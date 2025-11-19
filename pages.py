from functools import partial
import importlib
import io
import re
from contextlib import redirect_stdout
from pathlib import Path
from PyQt6.QtCore import QCoreApplication, QEvent
import time

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QGridLayout, QScrollArea, QListWidget, QListWidgetItem, QMainWindow, QCheckBox
)
from PyQt6.QtGui import QFont, QTextCursor, QColor, QMouseEvent
from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal

import os
import threading
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from assets.data import IceOre_data
from src import main
from src import tools
from src import window_status
from src import complex_events

# 从环境变量获取总览区域
调试模式 = int(eval(os.getenv('调试模式')))
锁定状态监控区 = eval(os.getenv('锁定状态监控区'))



class RealTimeTextStream(io.TextIOBase):
    """实时文本流，将输出实时写入 QTextEdit"""
    def __init__(self, text_edit, filter_func=None):
        self.text_edit = text_edit
        self.filter_func = filter_func
        self.buffer = ""
        
    def _should_filter_line(self, line):
        """检查单行是否应该被过滤"""
        if not self.filter_func:
            return False
        # 对于单行，直接检查是否包含需要过滤的内容
        return bool(re.search(r'(EveTool_Env|PS |python\.exe|\.py|& C:/)', line))
        
    def write(self, text):
        if text:
            self.buffer += text
            # 处理换行，实时更新
            while '\n' in self.buffer:
                line, self.buffer = self.buffer.split('\n', 1)
                if line.strip() and not self._should_filter_line(line):
                    # 追加文本并滚动到底部
                    self.text_edit.append(line)
                    cursor = self.text_edit.textCursor()
                    cursor.movePosition(QTextCursor.MoveOperation.End)
                    self.text_edit.setTextCursor(cursor)
                    # 处理事件队列，确保UI实时更新
                    QCoreApplication.processEvents()
        return len(text)
    
    def flush(self):
        # 处理剩余的缓冲区内容
        if self.buffer.strip() and not self._should_filter_line(self.buffer):
            self.text_edit.append(self.buffer)
            cursor = self.text_edit.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.text_edit.setTextCursor(cursor)
            QCoreApplication.processEvents()
        self.buffer = ""


class InfoPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #f8f9fa;")

        # 自动冰矿监控运行状态
        self.auto_ice_running = False
        # 多账号自动挖矿控制运行状态
        self.auto_multi_account_running = False

        # 主布局：水平布局，左侧70%控制台，右侧30%按钮区域
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # 构建左侧控制台区域（70%）
        self._build_console_panel()
        
        # 构建右侧按钮区域（30%）
        self._build_button_panel()

        # 添加到主布局，设置比例
        main_layout.addWidget(self.console_panel, stretch=7)  # 70%
        main_layout.addWidget(self.button_panel, stretch=3)   # 30%

    def _build_console_panel(self):
        """构建左侧控制台面板（70%）"""
        self.console_panel = QWidget()
        self.console_panel.setStyleSheet("background-color: transparent;")
        console_layout = QVBoxLayout()
        console_layout.setContentsMargins(0, 0, 0, 0)
        console_layout.setSpacing(8)
        self.console_panel.setLayout(console_layout)

        # 标题
        console_label = QLabel("控制台")
        console_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        console_label.setStyleSheet("color: #333; padding: 4px 0;")
        console_layout.addWidget(console_label)

        # 控制台容器
        console_container = QWidget()
        console_container.setStyleSheet(
            """
            background-color: #ffffff;
            border: 1px solid rgba(0, 0, 0, 35);
            border-radius: 8px;
            """
        )
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(12, 12, 12, 12)
        console_container.setLayout(container_layout)

        # 控制台文本显示区域
        self.console_display = QTextEdit()
        self.console_display.setReadOnly(True)
        self.console_display.setPlaceholderText("按钮触发的函数输出将显示在这里...")
        self.console_display.setStyleSheet(
            """
            QTextEdit {
                background-color: transparent;
                border: none;
                padding: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10pt;
            }
            """
        )
        container_layout.addWidget(self.console_display)
        console_layout.addWidget(console_container)

    def _build_button_panel(self):
        """构建右侧按钮面板（30%）"""
        self.button_panel = QWidget()
        self.button_panel.setStyleSheet("background-color: transparent;")
        button_layout = QVBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        self.button_panel.setLayout(button_layout)

        # 标题
        title = QLabel("操作按钮")
        title.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #333; padding: 8px; background-color: #ffffff; border-radius: 6px;")
        button_layout.addWidget(title)

        # 按钮样式
        button_style = """
            QPushButton {
                background-color: #f1f3f5;
                border: 1px solid rgba(0, 0, 0, 30);
                border-radius: 6px;
                padding: 6px 12px;
                color: #212529;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #e7eff9;
                border-color: rgba(0, 102, 204, 80);
            }
            QPushButton:pressed {
                background-color: #d9e5f5;
                border-color: rgba(0, 102, 204, 120);
            }
        """

        # 创建4个按钮
        self.button1 = QPushButton("开启单人自动冰矿采集")
        self.button1.setFixedHeight(36)
        self.button1.setStyleSheet(button_style)
        self.button1.clicked.connect(self.on_button1_clicked)
        button_layout.addWidget(self.button1)

        self.button2 = QPushButton("启动多账号自动挖矿控制")
        self.button2.setFixedHeight(36)
        self.button2.setStyleSheet(button_style)
        self.button2.clicked.connect(self.on_button2_clicked)
        button_layout.addWidget(self.button2)

        self.button3 = QPushButton("按钮3")
        self.button3.setFixedHeight(36)
        self.button3.setStyleSheet(button_style)
        self.button3.clicked.connect(self.on_button3_clicked)
        button_layout.addWidget(self.button3)

        self.button4 = QPushButton("按钮4")
        self.button4.setFixedHeight(36)
        self.button4.setStyleSheet(button_style)
        self.button4.clicked.connect(self.on_button4_clicked)
        button_layout.addWidget(self.button4)

        # 添加弹性空间，使按钮置顶
        button_layout.addStretch()

    def _update_console(self, button_name, func=None):
        """更新控制台显示的辅助方法"""
        try:
            # 清空控制台
            self.console_display.clear()
            
            # 添加按钮名称和时间戳
            import time
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            self.console_display.append(f"[{timestamp}] 执行: {button_name}")
            self.console_display.append("-" * 50)
            
            # 如果提供了函数，执行并实时捕获输出
            if func:
                try:
                    # 创建实时流
                    realtime_stream = RealTimeTextStream(self.console_display)
                    
                    with redirect_stdout(realtime_stream):
                        result = func()
                    
                    # 处理剩余的缓冲区
                    realtime_stream.flush()
                    
                    # 显示返回值
                    if result is not None:
                        self.console_display.append("-" * 50)
                        self.console_display.append(f"返回值: {result}")
                        cursor = self.console_display.textCursor()
                        cursor.movePosition(QTextCursor.MoveOperation.End)
                        self.console_display.setTextCursor(cursor)
                except Exception as e:
                    self.console_display.append(f"函数执行出错: {str(e)}")
                    cursor = self.console_display.textCursor()
                    cursor.movePosition(QTextCursor.MoveOperation.End)
                    self.console_display.setTextCursor(cursor)
            else:
                # 如果没有提供函数，显示提示信息
                self.console_display.append("该按钮暂无功能")
                cursor = self.console_display.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                self.console_display.setTextCursor(cursor)
        except Exception as e:
            error_msg = f"函数执行出错: {str(e)}"
            self.console_display.setPlainText(error_msg)

    def on_button1_clicked(self):
        """按钮1点击处理：触发自动冰矿挖掘监控"""
        # 如果当前未运行，则启动监控；否则发送停止指令
        if not self.auto_ice_running:
            # 启动
            self.auto_ice_running = True
            self.button1.setText("终止单人自动冰矿采集")

            # 在控制台显示启动信息
            try:
                self.console_display.clear()
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                self.console_display.append(f"[{timestamp}] 执行: 自动冰矿挖掘监控（已启动）")
                self.console_display.append("-" * 50)
                cursor = self.console_display.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                self.console_display.setTextCursor(cursor)
            except Exception:
                pass

            # 在后台线程中执行耗时/长期运行的自动挖矿监控，避免阻塞 UI，
            # 并通过 RealTimeTextStream 将 print 输出实时写入控制台
            def _worker():
                realtime_stream = RealTimeTextStream(self.console_display)
                try:
                    with redirect_stdout(realtime_stream):
                        complex_events.AutoIceMining_Monitor_Forone()
                    realtime_stream.flush()
                except Exception as e:
                    print(f"自动冰矿挖掘监控线程异常: {e}")
                finally:
                    # 监控结束后在主线程恢复按钮状态
                    def _reset():
                        self.auto_ice_running = False
                        self.button1.setText("开启单人自动冰矿采集")
                    QCoreApplication.postEvent(
                        self,
                        type("DummyEvent", (QEvent,), {})()  # 简单触发事件队列
                    )
                    QCoreApplication.instance().postEvent(
                        self,
                        type("DummyEvent", (QEvent,), {})()
                    )
                    # 为了简单起见，直接在后台线程更新标志，按钮文字依然在下次点击前可见
                    self.auto_ice_running = False
                    self.button1.setText("开启单人自动冰矿采集")

            threading.Thread(target=_worker, daemon=True).start()
        else:
            # 发送停止指令
            complex_events.Stop_AutoIceMining_Monitor_Forone()

            # 在控制台提示停止
            try:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                self.console_display.append(f"[{timestamp}] 已请求终止自动冰矿挖掘监控")
                self.console_display.append("-" * 50)
                cursor = self.console_display.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                self.console_display.setTextCursor(cursor)
            except Exception:
                pass

            # 立即恢复按钮文字，状态标记将在后台线程结束时再次重置
            self.auto_ice_running = False
            self.button1.setText("开启单人自动冰矿采集")

    def on_button2_clicked(self):
        """按钮2点击处理：触发多账号自动挖矿控制"""
        # 如果当前未运行，则启动监控；否则发送停止指令
        if not self.auto_multi_account_running:
            # 启动
            self.auto_multi_account_running = True
            self.button2.setText("停止多账号自动挖矿控制")

            # 在控制台显示启动信息
            try:
                self.console_display.clear()
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                self.console_display.append(f"[{timestamp}] 执行: 多账号自动挖矿控制（已启动）")
                self.console_display.append("-" * 50)
                cursor = self.console_display.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                self.console_display.setTextCursor(cursor)
            except Exception:
                pass

            # 在后台线程中执行耗时/长期运行的自动挖矿监控，避免阻塞 UI，
            # 并通过 RealTimeTextStream 将 print 输出实时写入控制台
            def _worker():
                realtime_stream = RealTimeTextStream(self.console_display)
                try:
                    with redirect_stdout(realtime_stream):
                        complex_events.AutoIceMining_Monitor_Forone_WithThrow()
                    realtime_stream.flush()
                except Exception as e:
                    print(f"多账号自动挖矿控制线程异常: {e}")
                finally:
                    # 监控结束后在主线程恢复按钮状态
                    def _reset():
                        self.auto_multi_account_running = False
                        self.button2.setText("启动多账号自动挖矿控制")
                    QCoreApplication.postEvent(
                        self,
                        type("DummyEvent", (QEvent,), {})()  # 简单触发事件队列
                    )
                    QCoreApplication.instance().postEvent(
                        self,
                        type("DummyEvent", (QEvent,), {})()
                    )
                    # 为了简单起见，直接在后台线程更新标志，按钮文字依然在下次点击前可见
                    self.auto_multi_account_running = False
                    self.button2.setText("启动多账号自动挖矿控制")

            threading.Thread(target=_worker, daemon=True).start()
        else:
            # 发送停止指令
            complex_events.Stop_AutoIceMining_Monitor_Forone()

            # 在控制台提示停止
            try:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                self.console_display.append(f"[{timestamp}] 已请求终止多账号自动挖矿控制")
                self.console_display.append("-" * 50)
                cursor = self.console_display.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                self.console_display.setTextCursor(cursor)
            except Exception:
                pass

            # 立即恢复按钮文字，状态标记将在后台线程结束时再次重置
            self.auto_multi_account_running = False
            self.button2.setText("启动多账号自动挖矿控制")

    def on_button3_clicked(self):
        """按钮3点击处理：暂无功能"""
        self._update_console("按钮3", None)

    def on_button4_clicked(self):
        """按钮4点击处理：暂无功能"""
        self._update_console("按钮4", None)


class MainPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #f8f9fa;")

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(16)
        
        # 窗口前置状态
        self.is_topmost = False

        self._build_left_panel()
        self._build_right_panel()
        
        # 启动定时器，每5秒执行一次 Info_Show
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_info_display)
        self.timer.start(5000)  # 5000毫秒 = 5秒
        # 立即执行一次
        self.update_info_display()

    def _build_left_panel(self):
        """构建左侧面板：两个信息显示栏"""
        left_panel = QWidget()
        left_panel.setStyleSheet("background-color: transparent;")
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)
        left_panel.setLayout(left_layout)

        # 大的信息显示栏（80%）
        large_info_label = QLabel("信息显示")
        large_info_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        large_info_label.setStyleSheet("color: #333; padding: 4px 0;")
        
        large_info_container = QWidget()
        large_info_container.setStyleSheet(
            """
            background-color: #ffffff;
            border: 1px solid rgba(0, 0, 0, 35);
            border-radius: 8px;
            """
        )
        large_info_layout = QVBoxLayout()
        large_info_layout.setContentsMargins(12, 12, 12, 12)
        large_info_container.setLayout(large_info_layout)

        self.large_info_display = QTextEdit()
        self.large_info_display.setReadOnly(True)
        self.large_info_display.setPlaceholderText("Info_Show() 的输出将每5秒更新一次...")
        self.large_info_display.setStyleSheet(
            """
            QTextEdit {
                background-color: transparent;
                border: none;
                padding: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10pt;
            }
            """
        )
        large_info_layout.addWidget(self.large_info_display)

        # 小的信息显示栏（20%）- 控制台
        console_label = QLabel("控制台")
        console_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        console_label.setStyleSheet("color: #333; padding: 4px 0;")

        console_container = QWidget()
        console_container.setStyleSheet(
            """
            background-color: #ffffff;
            border: 1px solid rgba(0, 0, 0, 35);
            border-radius: 8px;
            """
        )
        console_layout = QVBoxLayout()
        console_layout.setContentsMargins(12, 12, 12, 12)
        console_container.setLayout(console_layout)

        self.console_display = QTextEdit()
        self.console_display.setReadOnly(True)
        self.console_display.setPlaceholderText("按钮交互后的输出将显示在这里...")
        self.console_display.setStyleSheet(
            """
            QTextEdit {
                background-color: transparent;
                border: none;
                padding: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9pt;
            }
            """
        )
        console_layout.addWidget(self.console_display)

        # 添加到左侧布局，设置比例
        left_layout.addWidget(large_info_label)
        left_layout.addWidget(large_info_container, stretch=8)  # 80%
        left_layout.addWidget(console_label)
        left_layout.addWidget(console_container, stretch=2)  # 20%

        self.main_layout.addWidget(left_panel, stretch=1)

    def _build_right_panel(self):
        """构建右侧面板：14个按钮"""
        right_panel = QWidget()
        right_panel.setFixedWidth(200)
        right_panel.setStyleSheet("background-color: transparent;")
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        right_panel.setLayout(right_layout)

        # 标题
        title = QLabel("操作按钮")
        title.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #333; padding: 8px; background-color: #ffffff; border-radius: 6px;")
        right_layout.addWidget(title)

        # 按钮样式
        button_style = """
            QPushButton {
                background-color: #f1f3f5;
                border: 1px solid rgba(0, 0, 0, 30);
                border-radius: 6px;
                padding: 6px 12px;
                color: #212529;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #e7eff9;
                border-color: rgba(0, 102, 204, 80);
            }
            QPushButton:pressed {
                background-color: #d9e5f5;
                border-color: rgba(0, 102, 204, 120);
            }
        """

        # 创建按钮1
        self.button1 = QPushButton("更新总览区域")
        self.button1.setFixedHeight(36)
        self.button1.setStyleSheet(button_style)
        self.button1.clicked.connect(self.on_button1_clicked)
        right_layout.addWidget(self.button1)

        # 创建按钮2
        self.button2 = QPushButton("窗口前置/取消前置")
        self.button2.setFixedHeight(36)
        self.button2.setStyleSheet(button_style)
        self.button2.clicked.connect(self.on_button2_clicked)
        right_layout.addWidget(self.button2)

        # 创建按钮3
        self.button3 = QPushButton("更新第一采集器位置")
        self.button3.setFixedHeight(36)
        self.button3.setStyleSheet(button_style)
        self.button3.clicked.connect(self.on_button3_clicked)
        right_layout.addWidget(self.button3)

        # 创建按钮4
        self.button4 = QPushButton("更新第二采集器位置")
        self.button4.setFixedHeight(36)
        self.button4.setStyleSheet(button_style)
        self.button4.clicked.connect(self.on_button4_clicked)
        right_layout.addWidget(self.button4)

        # 创建按钮5
        self.button5 = QPushButton("更新锁定状态监控区")
        self.button5.setFixedHeight(36)
        self.button5.setStyleSheet(button_style)
        self.button5.clicked.connect(self.on_button5_clicked)
        right_layout.addWidget(self.button5)

        # 创建按钮6
        self.button6 = QPushButton("更新矿仓剩余空间监控区")
        self.button6.setFixedHeight(36)
        self.button6.setStyleSheet(button_style)
        self.button6.clicked.connect(self.on_button6_clicked)
        right_layout.addWidget(self.button6)

        # 创建按钮7
        self.button7 = QPushButton("更新压缩交互左上定位点")
        self.button7.setFixedHeight(36)
        self.button7.setStyleSheet(button_style)
        self.button7.clicked.connect(self.on_button7_clicked)
        right_layout.addWidget(self.button7)

        # 创建按钮8
        self.button8 = QPushButton("更新压缩交互右下定位点")
        self.button8.setFixedHeight(36)
        self.button8.setStyleSheet(button_style)
        self.button8.clicked.connect(self.on_button8_clicked)
        right_layout.addWidget(self.button8)

        # 创建按钮9
        self.button9 = QPushButton("更新压缩交互区")
        self.button9.setFixedHeight(36)
        self.button9.setStyleSheet(button_style)
        self.button9.clicked.connect(self.on_button9_clicked)
        right_layout.addWidget(self.button9)

        # 创建按钮10
        self.button10 = QPushButton("按钮10")
        self.button10.setFixedHeight(36)
        self.button10.setStyleSheet(button_style)
        self.button10.clicked.connect(self.on_button10_clicked)
        right_layout.addWidget(self.button10)

        # 创建按钮11
        self.button11 = QPushButton("按钮11")
        self.button11.setFixedHeight(36)
        self.button11.setStyleSheet(button_style)
        self.button11.clicked.connect(self.on_button11_clicked)
        right_layout.addWidget(self.button11)

        # 创建按钮12
        self.button12 = QPushButton("按钮12")
        self.button12.setFixedHeight(36)
        self.button12.setStyleSheet(button_style)
        self.button12.clicked.connect(self.on_button12_clicked)
        right_layout.addWidget(self.button12)

        # 创建按钮13
        self.button13 = QPushButton("按钮13")
        self.button13.setFixedHeight(36)
        self.button13.setStyleSheet(button_style)
        self.button13.clicked.connect(self.on_button13_clicked)
        right_layout.addWidget(self.button13)

        # 创建按钮14
        self.button14 = QPushButton("按钮14")
        self.button14.setFixedHeight(36)
        self.button14.setStyleSheet(button_style)
        self.button14.clicked.connect(self.on_button14_clicked)
        right_layout.addWidget(self.button14)

        right_layout.addStretch()  # 添加弹性空间
        self.main_layout.addWidget(right_panel)

    def update_info_display(self):
        """更新大的信息显示栏，执行 Info_Show() 并捕获输出"""
        try:
            # 捕获 print 输出
            f = io.StringIO()
            with redirect_stdout(f):
                complex_events.Info_Show()
            output = f.getvalue()
            
            # 过滤掉执行行
            lines = output.split('\n')
            filtered_lines = []
            for line in lines:
                # 过滤掉包含路径和执行命令的行
                if not re.search(r'(EveTool_Env|PS |python\.exe|\.py)', line):
                    filtered_lines.append(line)
            
            filtered_output = '\n'.join(filtered_lines)
            self.large_info_display.setPlainText(filtered_output)
            # 自动滚动到底部
            cursor = self.large_info_display.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.large_info_display.setTextCursor(cursor)
        except Exception as e:
            self.large_info_display.setPlainText(f"执行 Info_Show() 时出错：{str(e)}")

    def _update_console(self, button_name, func=None):
        """更新控制台显示的辅助方法"""
        try:
            # 清空控制台
            self.console_display.clear()
            
            # 如果提供了函数，执行并实时捕获输出
            if func:
                try:
                    # 创建实时流
                    realtime_stream = RealTimeTextStream(self.console_display)
                    
                    with redirect_stdout(realtime_stream):
                        result = func()
                    
                    # 处理剩余的缓冲区
                    realtime_stream.flush()
                    
                    # 显示返回值
                    if result is not None:
                        self.console_display.append(f"返回值: {result}")
                        cursor = self.console_display.textCursor()
                        cursor.movePosition(QTextCursor.MoveOperation.End)
                        self.console_display.setTextCursor(cursor)
                except Exception as e:
                    self.console_display.append(f"函数执行出错: {str(e)}")
        except Exception as e:
            error_msg = f"函数执行出错: {str(e)}"
            self.console_display.setPlainText(error_msg)

    def on_button1_clicked(self):
        """按钮1点击处理"""
        self._update_console("更新总览区域", complex_events.OverviewScale_Change)

    def toggle_window_topmost(self):
        """切换窗口前置状态"""
        main_window = self.window()
        if main_window:
            if self.is_topmost:
                # 恢复普通状态
                main_window.setWindowFlags(main_window.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
                self.is_topmost = False
                print("窗口已恢复普通状态")
            else:
                # 设置为前置
                main_window.setWindowFlags(main_window.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
                self.is_topmost = True
                print("窗口已设置为前置")
            # 重新显示窗口以应用更改
            main_window.show()
            return True
        else:
            print("无法获取主窗口")
            return False
    
    def on_button2_clicked(self):
        """按钮2点击处理"""
        self._update_console("窗口前置/取消前置", self.toggle_window_topmost)

    def on_button3_clicked(self):
        """按钮3点击处理"""
        # 包装为函数，以便实时捕获输出
        def update_first_collector():
            print("开始更新第一采集器位置...")
            position = tools.get_mouse_position_after_delay()
            result = tools.write_to_env(function_name="第一采集器位置", data=position)
            print(f"第一采集器位置已更新为: {position}")
            return result
        self._update_console("更新第一采集器位置", update_first_collector)

    def on_button4_clicked(self):
        """按钮4点击处理"""
        # 包装为函数，以便实时捕获输出
        def update_second_collector():
            print("开始更新第二采集器位置...")
            position = tools.get_mouse_position_after_delay()
            result = tools.write_to_env(function_name="第二采集器位置", data=position)
            print(f"第二采集器位置已更新为: {position}")
            return result
        self._update_console("更新第二采集器位置", update_second_collector)

    def on_button5_clicked(self):
        """按钮5点击处理"""
        # 包装为函数，以便实时捕获输出
        def update_lock_status_area():
            print("开始更新锁定状态监控区...")
            positioning = complex_events.list_positioning()
            result = tools.write_to_env(function_name="锁定状态监控区", data=positioning)
            print(f"\n锁定状态监控区已更新为: {positioning}")
            return result
        self._update_console("锁定状态监控区", update_lock_status_area)

    def on_button6_clicked(self):
        """按钮6点击处理"""
        # 在这里添加按钮6的具体处理逻辑
        # 包装为函数，以便实时捕获输出
        def update_lock_status_area():
            print("开始更新矿仓剩余空间监控区...")
            positioning = complex_events.list_positioning()
            result = tools.write_to_env(function_name="矿仓剩余空间监控区", data=positioning)
            print(f"\n锁定状态监控区已更新为: {positioning}")
            return result
        self._update_console("矿仓剩余空间", update_lock_status_area)

    def on_button7_clicked(self):
        """按钮7点击处理"""
        # 包装为函数，以便实时捕获输出
        def update_first_collector():
            print("开始更新压缩交互左上定位点...")
            position = tools.get_mouse_position_after_delay()
            result = tools.write_to_env(function_name="压缩交互左上定位点", data=position)
            print(f"压缩交互左上定位点已更新为: {position}")
            return result
        self._update_console("更新压缩交互左上定位点", update_first_collector)

    def on_button8_clicked(self):
        """按钮8点击处理"""
        # 在这里添加按钮8的具体处理逻辑
        # 包装为函数，以便实时捕获输出
        def update_first_collector():
            print("开始更新压缩交互右下定位点...")
            position = tools.get_mouse_position_after_delay()
            result = tools.write_to_env(function_name="压缩交互右下定位点", data=position)
            print(f"压缩交互右下定位点已更新为: {position}")
            return result
        self._update_console("更新压缩交互右下定位点", update_first_collector)

    def on_button9_clicked(self):
        """按钮9点击处理"""
        self._update_console("更新压缩交互区", complex_events.CompressedArea_Change)

    def on_button10_clicked(self):
        """按钮10点击处理"""
        # 在这里添加按钮10的具体处理逻辑
        self._update_console("按钮10")

    def on_button11_clicked(self):
        """按钮11点击处理"""
        # 在这里添加按钮11的具体处理逻辑
        self._update_console("按钮11")

    def on_button12_clicked(self):
        """按钮12点击处理"""
        # 在这里添加按钮12的具体处理逻辑
        self._update_console("按钮12")

    def on_button13_clicked(self):
        """按钮13点击处理"""
        # 在这里添加按钮13的具体处理逻辑
        self._update_console("按钮13")

    def on_button14_clicked(self):
        """按钮14点击处理"""
        # 在这里添加按钮14的具体处理逻辑
        self._update_console("按钮14")

    def _get_current_time(self):
        """获取当前时间字符串"""
        import time
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

    def _filter_execution_lines(self, text):
        """过滤掉执行行"""
        lines = text.split('\n')
        filtered_lines = []
        for line in lines:
            # 过滤掉包含路径和执行命令的行
            if not re.search(r'(EveTool_Env|PS |python\.exe|\.py|& C:/)', line):
                filtered_lines.append(line)
        return '\n'.join(filtered_lines)


class OreSelectionPage(QWidget):
    """矿石多选页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #f8f9fa;")
        self.ore_sources = self._load_ore_sources()
        self._build_ui()

    def _load_ore_sources(self):
        sources = []
        data_dir = Path(__file__).resolve().parent / "assets" / "data"
        if not data_dir.exists():
            return sources

        for file_path in sorted(data_dir.glob("*_data.py")):
            module_name = f"assets.data.{file_path.stem}"
            try:
                module = importlib.import_module(module_name)
            except Exception as exc:
                print(f"加载矿石数据模块 {module_name} 失败: {exc}")
                continue

            data_isk = getattr(module, "data_isk", [])
            if len(data_isk) <= 1:
                continue

            rows_info = []
            try:
                lines = file_path.read_text(encoding='utf-8').splitlines()
            except Exception as e:
                print(f"读取文件 {file_path} 失败: {e}")
                continue

            # 精确查找 data_isk 起始行
            data_isk_start = None
            for i, line in enumerate(lines):
                if re.search(r'data_isk\s*=\s*\[', line):
                    data_isk_start = i
                    break
            if data_isk_start is None:
                continue

            # 重构解析逻辑
            current_line = data_isk_start + 1  # 从下一行开始
            data_index = 1  # 跳过表头(data_isk[0])
            
            while current_line < len(lines) and data_index < len(data_isk):
                stripped_line = lines[current_line].strip()
                
                # 检查数据块结束
                if stripped_line.startswith(']'):
                    break
                
                # 跳过空行、注释和表头行
                if (not stripped_line or 
                    stripped_line.startswith('#') or 
                    "'core-name'" in stripped_line or 
                    '"core-name"' in stripped_line):
                    current_line += 1
                    continue
                
                # 处理有效数据行
                row = data_isk[data_index]
                if isinstance(row, list) and len(row) >= 6:
                    # 验证行中是否包含布尔值
                    if self._contains_bool_value(lines[current_line]):
                        rows_info.append({
                            "row": row,
                            "file_path": file_path,
                            "line_number": current_line,
                            "original_line": lines[current_line]
                        })
                    else:
                        print(f"警告: 文件 {file_path.name} 第 {current_line+1} 行不包含有效布尔值")
                
                data_index += 1
                current_line += 1

            if not rows_info:
                continue

            sources.append({
                "title": getattr(module, "Name", file_path.stem.replace("_", " ")),
                "rows_info": rows_info,
            })

        return sources
    
    def _contains_bool_value(self, line):
        """检查行中是否包含独立的True/False值"""
        return bool(re.search(r'\b(True|False)\b', line))

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("矿石选择")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #1976d2; padding: 4px 0;")
        layout.addWidget(title)

        subtitle = QLabel("勾选需要的矿石，将直接修改文件中的布尔值字段。点击分类标题可折叠/展开列表。")
        subtitle.setStyleSheet("color: #666; font-size: 10pt; padding: 2px 0 8px 0;")
        layout.addWidget(subtitle)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none;")

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(16)

        if self.ore_sources:
            for source in self.ore_sources:
                container_layout.addWidget(self._create_section(source))
        else:
            empty_label = QLabel("未找到任何矿石数据，请检查 assets/data 目录。")
            empty_label.setStyleSheet("color: #999; font-style: italic;")
            container_layout.addWidget(empty_label)

        container_layout.addStretch()
        scroll_area.setWidget(container)
        layout.addWidget(scroll_area)

    def _create_section(self, source):
        section = QWidget()
        section.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
            }
        """)
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(0)

        # 创建可点击的标题
        header = ClickableHeaderLabel(source["title"])
        section_layout.addWidget(header)

        list_container = QWidget()
        list_container.setStyleSheet("""
            QWidget {
                background-color: #fafafa;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }
        """)
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(16, 12, 16, 12)
        list_layout.setSpacing(8)

        # 保存该section下的所有checkbox
        checkboxes = []
        for info in source["rows_info"]:
            row = info["row"]
            if len(row) < 6:
                continue
            checkbox = OreCheckBox(row[0], info)
            checkbox.setToolTip(f"isk/m³: {row[4]}")
            checkbox.setChecked(bool(row[5]))
            checkbox.stateChanged.connect(self._on_checkbox_toggled)
            list_layout.addWidget(checkbox)
            checkboxes.append(checkbox)

        # 连接header点击事件，实现折叠/展开功能
        def on_header_clicked():
            # 切换展开/收起状态
            header.toggle()
            # 根据展开状态显示/隐藏列表容器
            list_container.setVisible(header.is_expanded)
        
        header.clicked.connect(on_header_clicked)

        # 默认收起状态：隐藏列表容器
        list_container.setVisible(False)
        section_layout.addWidget(list_container)
        return section

    def _find_bool_position(self, line):
        """动态定位行中最后一个独立的True/False位置"""
        # 从后往前搜索，找到最后一个独立的True/False
        matches = list(re.finditer(r'\b(True|False)\b', line))
        if not matches:
            return None
        
        # 取最后一个匹配（最靠近行尾的布尔值）
        last_match = matches[-1]
        return {
            "start": last_match.start(),
            "end": last_match.end(),
            "value": last_match.group(1)
        }

    def _on_checkbox_toggled(self, state):
        checkbox = self.sender()
        if not isinstance(checkbox, OreCheckBox):
            return
            
        info = checkbox.row_info
        file_path = info["file_path"]
        line_number = info["line_number"]
        # PyQt6中stateChanged信号传递的state: 0=Unchecked, 2=Checked
        # 可以直接比较枚举值或整数
        new_value = (state == Qt.CheckState.Checked or state == 2)
        new_value_str = "True" if new_value else "False"

        original_line = None
        try:
            # 重新读取文件获取最新内容
            lines = file_path.read_text(encoding='utf-8').splitlines()
            if line_number >= len(lines):
                raise IndexError(f"行号 {line_number} 超出文件范围 (共 {len(lines)} 行)")

            original_line = lines[line_number]
            
            # 动态定位当前布尔值位置
            bool_pos = self._find_bool_position(original_line)
            if not bool_pos:
                raise ValueError(f"无法在行中定位布尔值: {original_line}")
            
            # 直接执行替换，不检查值是否变化
            # 因为用户明确进行了操作，应该信任用户意图
            
            # 精准替换
            new_line = (
                original_line[:bool_pos["start"]] + 
                new_value_str + 
                original_line[bool_pos["end"]:]
            )
            
            # 验证替换是否成功（新行应该包含目标布尔值）
            if new_value_str not in new_line:
                raise ValueError(f"替换后未找到目标布尔值 {new_value_str}")
            
            lines[line_number] = new_line
            
            # 写入文件
            file_path.write_text('\n'.join(lines), encoding='utf-8')
            
            # 验证文件写入是否成功
            verify_lines = file_path.read_text(encoding='utf-8').splitlines()
            if line_number < len(verify_lines):
                verify_line = verify_lines[line_number]
                if new_value_str not in verify_line:
                    raise ValueError(f"文件写入验证失败: 第 {line_number+1} 行未包含 {new_value_str}")
            
            # 更新内存数据
            info["row"][5] = new_value
            
            # 调试输出
            print(f"✓ 成功修改 {file_path.name} 第 {line_number+1} 行: {bool_pos['value']} -> {new_value_str}")
            
        except Exception as e:
            print(f"✗ 修改文件 {file_path.name} 第 {line_number+1} 行失败: {str(e)}")
            # 尝试强力替换（最后手段）
            if original_line is not None:
                try:
                    lines = file_path.read_text(encoding='utf-8').splitlines()
                    if line_number < len(lines):
                        current_line = lines[line_number]
                        # 使用正则表达式替换最后一个独立的True/False
                        # 匹配独立的True或False（不在引号内）
                        pattern = r'\b(True|False)\b'
                        matches = list(re.finditer(pattern, current_line))
                        if matches:
                            # 替换最后一个匹配
                            last_match = matches[-1]
                            new_line = (
                                current_line[:last_match.start()] + 
                                new_value_str + 
                                current_line[last_match.end():]
                            )
                            lines[line_number] = new_line
                            file_path.write_text('\n'.join(lines), encoding='utf-8')
                            info["row"][5] = new_value
                            print(f"✓ 强力替换成功: {file_path.name} 第 {line_number+1} 行: {last_match.group(1)} -> {new_value_str}")
                        else:
                            print(f"✗ 强力替换失败: 未找到可替换的布尔值")
                except Exception as e2:
                    print(f"✗ 强力替换也失败: {str(e2)}")


class ClickableHeaderLabel(QWidget):
    """可点击的标题标签，支持展开/收起状态"""
    clicked = pyqtSignal()
    
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.is_expanded = False  # 默认收起状态
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(36)
        
        # 创建水平布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)
        
        # 箭头标签 - 使用更美观的图标
        self.arrow_label = QLabel("▶")
        self.arrow_label.setFont(QFont("Microsoft YaHei", 11))
        self.arrow_label.setStyleSheet("""
            color: #2196f3;
            font-weight: bold;
        """)
        self.arrow_label.setFixedWidth(20)
        self.arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.arrow_label)
        
        # 文本标签
        self.text_label = QLabel(text)
        self.text_label.setFont(QFont("Microsoft YaHei", 13, QFont.Weight.Bold))
        self.text_label.setStyleSheet("color: #1976d2;")
        layout.addWidget(self.text_label)
        
        layout.addStretch()
        
        # 设置整体样式
        self._update_style()
    
    def _update_style(self):
        """更新样式"""
        # 移除背景色和边框，只保留悬停效果
        self.setStyleSheet("""
            ClickableHeaderLabel {
                background-color: transparent;
                border: none;
            }
            ClickableHeaderLabel:hover {
                background-color: transparent;
            }
        """)
    
    def set_expanded(self, expanded):
        """设置展开/收起状态"""
        self.is_expanded = expanded
        # 使用更美观的箭头符号
        self.arrow_label.setText("▼" if expanded else "▶")
        self._update_style()
    
    def toggle(self):
        """切换展开/收起状态"""
        self.set_expanded(not self.is_expanded)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class OreCheckBox(QCheckBox):
    def __init__(self, text, row_info, parent=None):
        super().__init__(text, parent)
        self.row_info = row_info
        self.setStyleSheet("""
            QCheckBox {
                spacing: 12px;
                font-size: 10pt;
                color: #424242;
                padding: 4px 0px;
            }
            QCheckBox:hover {
                color: #1976d2;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 4px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #bdbdbd;
                background: #ffffff;
            }
            QCheckBox::indicator:unchecked:hover {
                border: 2px solid #2196f3;
                background: #e3f2fd;
            }
            QCheckBox::indicator:checked {
                background: #2196f3;
                border: 2px solid #1976d2;
                image: url(:/qt-project.org/styles/commonstyle/images/checkBoxChecked.png);
            }
            QCheckBox::indicator:checked:hover {
                background: #1976d2;
                border: 2px solid #1565c0;
            }
        """)


class StandaloneControlBar(QMainWindow):
    """独立控制栏窗口 - 永久前置的用户名列表"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 拖动相关变量
        self.drag_window_pos = None
        self.drag_mouse_pos = None
        
        self.setWindowTitle("独立控制栏")
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |  # 永久前置
            Qt.WindowType.FramelessWindowHint |   # 无边框
            Qt.WindowType.Tool                    # 工具窗口特性
        )
        
        # 读取透明度参数（默认为 0.9，即 90% 不透明度）
        # 确保重新加载 .env 文件以获取最新值
        load_dotenv(find_dotenv(), override=True)
        try:
            opacity_str = os.getenv('独立控制栏透明度', '0.9')
            if opacity_str:
                # 去除空格
                opacity_str = opacity_str.strip()
                
                # 支持百分比格式（如 "35%"）或小数格式（如 "0.35"）
                if opacity_str.endswith('%'):
                    # 百分比格式：35% -> 0.35
                    percentage_value = float(opacity_str[:-1])
                    self.opacity = percentage_value / 100.0
                else:
                    # 小数格式：直接转换为浮点数
                    self.opacity = float(opacity_str)
                
                # 确保透明度在 0.0 到 1.0 之间
                self.opacity = max(0.0, min(1.0, self.opacity))
                if 调试模式 == 1:
                    print(f"独立控制栏透明度已设置为: {self.opacity} ({self.opacity * 100:.0f}%)")
            else:
                self.opacity = 0.9
                print("未找到透明度参数，使用默认值 0.9 (90%)")
        except (ValueError, TypeError) as e:
            print(f"读取透明度参数时出错: {e}，使用默认值 0.9 (90%)")
            self.opacity = 0.9
        
        # 读取颜色参数
        self.bg_color = os.getenv('独立控制栏主背景色', '#e9ecef').strip()
        self.list_bg_color = os.getenv('独立控制栏列表背景色', 'rgba(255, 255, 255, 200)').strip()
        self.active_color = os.getenv('独立控制栏激活色', 'rgba(187, 222, 251, 200)').strip()
        self.normal_text_color = os.getenv('独立控制栏普通文字色', '#000000').strip()
        self.active_text_color = os.getenv('独立控制栏激活文字色', '#1976d2').strip()
        
        # 设置窗口透明度（需要在窗口标志设置之后）
        self.setWindowOpacity(self.opacity)
        
        # 创建主窗口部件
        central_widget = QWidget()
        # 设置主背景色
        central_widget.setStyleSheet(f"background-color: {self.bg_color};")
        self.setCentralWidget(central_widget)
        
        # 主布局：水平布局，左侧拖动区域 + 右侧列表
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 左侧拖动区域（空白区域，用于拖动窗口）
        self.drag_area = QWidget()
        self.drag_area.setFixedWidth(12)  # 12像素宽的拖动区域
        self.drag_area.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
        self.drag_area.mousePressEvent = self.drag_area_mousePressEvent
        self.drag_area.mouseMoveEvent = self.drag_area_mouseMoveEvent
        main_layout.addWidget(self.drag_area)
        
        # 右侧内容区域
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(2, 2, 2, 2)
        content_layout.setSpacing(0)
        
        # 用户名列表
        self.username_list = QListWidget()
        # 使用从 .env 读取的颜色参数构建样式
        list_style = f"""
            QListWidget {{
                background-color: {self.list_bg_color};
                border: none;
                border-radius: 4px;
                padding: 0px;
            }}
            QListWidget::item {{
                padding: 6px 12px 6px 16px;
                border-radius: 2px;
                margin: 0px;
                min-height: 28px;
                text-align: left;
                color: {self.normal_text_color};
            }}
            QListWidget::item:hover {{
                background-color: {self.active_color};
            }}
            QListWidget::item:selected {{
                background-color: {self.active_color};
                color: {self.active_text_color};
            }}
        """
        self.username_list.setStyleSheet(list_style)
        self.username_list.setFont(QFont("Microsoft YaHei", 9))
        self.username_list.itemClicked.connect(self.on_username_clicked)
        # 禁用滚动条，确保所有内容都显示
        self.username_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.username_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content_layout.addWidget(self.username_list)
        
        # 内容区域容器
        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        main_layout.addWidget(content_widget)
        
        # 设置固定宽度（拖动区域12px + 列表区域320px = 332px）
        self.setFixedWidth(332)
        
        # 刷新列表
        self.refresh_username_list()
    
    def drag_area_mousePressEvent(self, event: QMouseEvent):
        """拖动区域的鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 记录窗口位置和鼠标位置
            self.drag_window_pos = self.frameGeometry().topLeft()
            self.drag_mouse_pos = event.globalPosition().toPoint()
    
    def drag_area_mouseMoveEvent(self, event: QMouseEvent):
        """拖动区域的鼠标移动事件"""
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, 'drag_window_pos'):
            # 计算鼠标移动距离
            delta = event.globalPosition().toPoint() - self.drag_mouse_pos
            # 移动窗口
            self.move(self.drag_window_pos + delta)
    
    def refresh_username_list(self):
        """刷新用户名列表"""
        self.username_list.clear()
        
        # 获取用户名列表
        usernames = window_status.get_eve_usernames()
        
        # 添加用户名到列表
        for username in usernames:
            # 创建列表项，用户名靠左显示，右侧留空
            item = QListWidgetItem(f"  {username}")  # 左侧添加空格，确保靠左
            # 将用户名存储在 item 的 data 中，以便后续使用
            item.setData(Qt.ItemDataRole.UserRole, username)
            # 设置对齐方式：文字靠左，右侧留空
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            item.setFont(QFont("Microsoft YaHei", 9))
            self.username_list.addItem(item)
        
        # 根据列表项数量调整窗口高度
        if usernames:
            # 计算每个列表项的实际高度
            # min-height: 28px + 上下padding各6px = 40px 每个列表项
            item_min_height = 28
            item_padding = 6 * 2  # 上下padding总和
            actual_item_height = item_min_height + item_padding  # 40px
            
            # 布局边距：上下各2px
            layout_margins = 4  # 上下边距总和
            
            # 计算总高度：列表项总高度 + 布局边距
            total_height = len(usernames) * actual_item_height + layout_margins
            
            # 设置固定高度，确保所有内容都能显示
            self.setFixedHeight(total_height)
            
            # 确保列表控件能正确显示所有项（减去布局边距）
            list_height = total_height - layout_margins
            self.username_list.setFixedHeight(list_height)
        else:
            # 如果没有窗口，设置最小高度
            self.setFixedHeight(50)
            self.username_list.setFixedHeight(46)
    
    def on_username_clicked(self, item):
        """处理用户名点击事件"""
        username = item.data(Qt.ItemDataRole.UserRole)
        
        if username:
            # 根据用户名获取窗口句柄
            hwnd = window_status.get_eve_hwnd_by_username(username)
            
            if hwnd is not None:
                # 前置窗口
                window_status.bring_window_to_front(hwnd)
            else:
                print(f"警告: 无法找到用户名为 '{username}' 的窗口句柄。")
                # 刷新列表，可能窗口已关闭
                QTimer.singleShot(300, self.refresh_username_list)


class WindowsControlPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #e9ecef;")
        
        # 独立控制栏窗口引用
        self.standalone_bar = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 标题
        title = QLabel("▶ 窗口控制")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #333; padding: 10px;")
        layout.addWidget(title)
        
        # 刷新按钮和窗口数量信息区域
        button_layout = QHBoxLayout()
        self.refresh_button = QPushButton("刷新窗口列表")
        self.refresh_button.setFixedHeight(40)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
            QPushButton:pressed {
                background-color: #1565c0;
            }
        """)
        self.refresh_button.clicked.connect(self.refresh_window_list)
        button_layout.addWidget(self.refresh_button)
        
        # 独立控制栏按钮
        self.standalone_bar_button = QPushButton("启动独立控制栏")
        self.standalone_bar_button.setFixedHeight(40)
        self.standalone_bar_button.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.standalone_bar_button.clicked.connect(self.toggle_standalone_bar)
        button_layout.addWidget(self.standalone_bar_button)
        
        button_layout.addStretch()
        
        # 窗口数量信息标签
        self.window_count_label = QLabel("当前: 0 个窗口")
        self.window_count_label.setFont(QFont("Microsoft YaHei", 10))
        self.window_count_label.setStyleSheet("""
            color: #666;
            padding: 8px 16px;
            background-color: white;
            border: 1px solid rgba(0, 0, 0, 20);
            border-radius: 6px;
        """)
        button_layout.addWidget(self.window_count_label)
        layout.addLayout(button_layout)
        
        # 窗口列表
        list_label = QLabel("EVE 窗口列表（点击列表项可前置对应窗口）")
        list_label.setFont(QFont("Microsoft YaHei", 11))
        list_label.setStyleSheet("color: #555; padding: 4px 0;")
        layout.addWidget(list_label)
        
        self.window_list = QListWidget()
        self.window_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid rgba(0, 0, 0, 35);
                border-radius: 8px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
            }
            QListWidget::item:selected {
                background-color: #bbdefb;
                color: #1976d2;
            }
        """)
        self.window_list.setFont(QFont("Microsoft YaHei", 10))
        self.window_list.itemClicked.connect(self.on_window_item_clicked)
        layout.addWidget(self.window_list)
        
        # 初始化时加载窗口列表
        self.refresh_window_list()
    
    def refresh_window_list(self):
        """刷新窗口列表"""
        # 清空当前列表
        self.window_list.clear()
        
        # 获取窗口信息
        windows_info = window_status.get_eve_windows_info()
        
        # 添加窗口到列表
        for window_data in windows_info:
            title, hwnd, is_active = window_data
            
            # 创建列表项
            item = QListWidgetItem(title)
            
            # 将 hwnd 存储在 item 的 data 中
            if hwnd is not None:
                item.setData(Qt.ItemDataRole.UserRole, hwnd)
            
            # 如果窗口是激活状态，可以添加特殊标记
            if is_active:
                item.setText(f"● {title}")
                item.setForeground(QColor(25, 118, 210))  # 蓝色，表示激活状态
            
            # 设置字体
            item.setFont(QFont("Microsoft YaHei", 10))
            
            self.window_list.addItem(item)
        
        # 更新窗口数量信息标签
        count = len(windows_info)
        self.window_count_label.setText(f"当前: {count} 个窗口")
    
    def on_window_item_clicked(self, item):
        """处理列表项点击事件"""
        # 获取存储的 hwnd
        hwnd = item.data(Qt.ItemDataRole.UserRole)
        
        if hwnd is not None:
            # 前置窗口
            success = window_status.bring_window_to_front(hwnd)
            if success:
                # 刷新列表以更新激活状态
                QTimer.singleShot(300, self.refresh_window_list)  # 延迟300ms刷新，确保窗口状态已更新
            else:
                # 如果前置失败，可能是窗口已关闭，刷新列表
                QTimer.singleShot(300, self.refresh_window_list)
        else:
            print(f"警告: 窗口 '{item.text()}' 的句柄无效，无法前置。")
    
    def toggle_standalone_bar(self):
        """切换独立控制栏的显示/隐藏"""
        if self.standalone_bar is None or not self.standalone_bar.isVisible():
            # 创建并显示独立控制栏
            self.standalone_bar = StandaloneControlBar()
            self.standalone_bar.show()
            self.standalone_bar_button.setText("关闭独立控制栏")
            
            # 设置窗口位置（可以放在屏幕右上角）
            screen = self.standalone_bar.screen().availableGeometry()
            self.standalone_bar.move(screen.width() - self.standalone_bar.width() - 20, 20)
        else:
            # 关闭独立控制栏
            self.standalone_bar.close()
            self.standalone_bar = None
            self.standalone_bar_button.setText("启动独立控制栏")
    
    def close_standalone_bar(self):
        """关闭独立控制栏（供外部调用）"""
        if self.standalone_bar is not None:
            self.standalone_bar.close()
            self.standalone_bar = None
            if hasattr(self, 'standalone_bar_button'):
                self.standalone_bar_button.setText("启动独立控制栏")


class AboutPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #e9ecef;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)
        
        # 创建滚动区域和文本编辑器来显示Markdown内容
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: white;
                border: 1px solid rgba(0, 0, 0, 35);
                border-radius: 8px;
            }
        """)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        self.about_text = QTextEdit()
        self.about_text.setReadOnly(True)
        self.about_text.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                border: none;
                font-family: 'Microsoft YaHei', 'SimHei', sans-serif;
                font-size: 11pt;
            }
        """)
        
        # 读取并显示about.md文件
        self.load_about_content()
        
        content_layout.addWidget(self.about_text)
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
    
    def load_about_content(self):
        """加载about.md文件内容"""
        try:
            # 获取about.md文件的路径
            # pages.py在根目录，所以只需要一次dirname
            current_dir = os.path.dirname(os.path.abspath(__file__))
            about_file = os.path.join(current_dir, 'src', 'about.md')
            
            # 如果上面的路径不存在，尝试其他可能的路径
            if not os.path.exists(about_file):
                # 尝试相对于当前工作目录
                about_file = os.path.join('src', 'about.md')
            
            if os.path.exists(about_file):
                with open(about_file, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()
                # 使用setMarkdown方法渲染Markdown内容
                self.about_text.setMarkdown(markdown_content)
            else:
                # 显示调试信息
                debug_info = f"未找到 about.md 文件\n"
                debug_info += f"尝试的路径1: {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'about.md')}\n"
                debug_info += f"尝试的路径2: {os.path.join('src', 'about.md')}\n"
                debug_info += f"当前工作目录: {os.getcwd()}\n"
                debug_info += f"pages.py位置: {os.path.abspath(__file__)}"
                self.about_text.setPlainText(debug_info)
        except Exception as e:
            self.about_text.setPlainText(f"加载 about.md 文件时出错: {str(e)}\n\n错误详情: {type(e).__name__}")
