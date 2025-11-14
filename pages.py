from functools import partial
import sys
import io
import re
from contextlib import redirect_stdout
from PyQt6.QtCore import QCoreApplication


from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QGridLayout, QScrollArea
)
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtCore import Qt, QTimer

from src import complex_events


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
        self.setStyleSheet("background-color: #ffffff;")

        layout = QVBoxLayout(self)
        title = QLabel("主控制台")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #333; padding: 20px;")
        layout.addWidget(title)


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
        self.button3 = QPushButton("按钮3")
        self.button3.setFixedHeight(36)
        self.button3.setStyleSheet(button_style)
        self.button3.clicked.connect(self.on_button3_clicked)
        right_layout.addWidget(self.button3)

        # 创建按钮4
        self.button4 = QPushButton("按钮4")
        self.button4.setFixedHeight(36)
        self.button4.setStyleSheet(button_style)
        self.button4.clicked.connect(self.on_button4_clicked)
        right_layout.addWidget(self.button4)

        # 创建按钮5
        self.button5 = QPushButton("按钮5")
        self.button5.setFixedHeight(36)
        self.button5.setStyleSheet(button_style)
        self.button5.clicked.connect(self.on_button5_clicked)
        right_layout.addWidget(self.button5)

        # 创建按钮6
        self.button6 = QPushButton("按钮6")
        self.button6.setFixedHeight(36)
        self.button6.setStyleSheet(button_style)
        self.button6.clicked.connect(self.on_button6_clicked)
        right_layout.addWidget(self.button6)

        # 创建按钮7
        self.button7 = QPushButton("按钮7")
        self.button7.setFixedHeight(36)
        self.button7.setStyleSheet(button_style)
        self.button7.clicked.connect(self.on_button7_clicked)
        right_layout.addWidget(self.button7)

        # 创建按钮8
        self.button8 = QPushButton("按钮8")
        self.button8.setFixedHeight(36)
        self.button8.setStyleSheet(button_style)
        self.button8.clicked.connect(self.on_button8_clicked)
        right_layout.addWidget(self.button8)

        # 创建按钮9
        self.button9 = QPushButton("按钮9")
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
        # 在这里添加按钮3的具体处理逻辑
        self._update_console("按钮3")

    def on_button4_clicked(self):
        """按钮4点击处理"""
        # 在这里添加按钮4的具体处理逻辑
        self._update_console("按钮4")

    def on_button5_clicked(self):
        """按钮5点击处理"""
        # 在这里添加按钮5的具体处理逻辑
        self._update_console("按钮5")

    def on_button6_clicked(self):
        """按钮6点击处理"""
        # 在这里添加按钮6的具体处理逻辑
        self._update_console("按钮6")

    def on_button7_clicked(self):
        """按钮7点击处理"""
        # 在这里添加按钮7的具体处理逻辑
        self._update_console("按钮7")

    def on_button8_clicked(self):
        """按钮8点击处理"""
        # 在这里添加按钮8的具体处理逻辑
        self._update_console("按钮8")

    def on_button9_clicked(self):
        """按钮9点击处理"""
        # 在这里添加按钮9的具体处理逻辑
        self._update_console("按钮9")

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


class AboutPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #e9ecef;")

        layout = QVBoxLayout(self)
        title = QLabel("▶ 关于")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #333; padding: 20px;")
        layout.addWidget(title)


class DebugPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #dee2e6;")

        layout = QVBoxLayout(self)

        # 标题
        title = QLabel("▶ 调试页面")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #333; padding: 16px 20px;")
        layout.addWidget(title)

        # 第一行：按钮一 + 文本框一
        row1 = QHBoxLayout()
        btn1 = QPushButton("运行函数一")
        btn1.setFixedHeight(36)
        self.output1 = QTextEdit()
        self.output1.setReadOnly(True)
        self.output1.setPlaceholderText("函数一输出将显示在此处...")
        self.output1.setFixedHeight(80)
        row1.addWidget(btn1)
        row1.addWidget(self.output1)
        layout.addLayout(row1)

        # 第二行：按钮二 + 文本框二
        row2 = QHBoxLayout()
        btn2 = QPushButton("运行函数二")
        btn2.setFixedHeight(36)
        self.output2 = QTextEdit()
        self.output2.setReadOnly(True)
        self.output2.setPlaceholderText("函数二输出将显示在此处...")
        self.output2.setFixedHeight(80)
        row2.addWidget(btn2)
        row2.addWidget(self.output2)
        layout.addLayout(row2)

        # 第三行：按钮三 + 文本框三
        row3 = QHBoxLayout()
        btn3 = QPushButton("运行函数三")
        btn3.setFixedHeight(36)
        self.output3 = QTextEdit()
        self.output3.setReadOnly(True)
        self.output3.setPlaceholderText("函数三输出将显示在此处...")
        self.output3.setFixedHeight(80)
        row3.addWidget(btn3)
        row3.addWidget(self.output3)
        layout.addLayout(row3)

        # 第四行：按钮四 + 文本框四
        row4 = QHBoxLayout()
        btn4 = QPushButton("运行函数四")
        btn4.setFixedHeight(36)
        self.output4 = QTextEdit()
        self.output4.setReadOnly(True)
        self.output4.setPlaceholderText("函数四输出将显示在此处...")
        self.output4.setFixedHeight(80)
        row4.addWidget(btn4)
        row4.addWidget(self.output4)
        layout.addLayout(row4)

        # 第五行：按钮五 + 文本框五
        row5 = QHBoxLayout()
        btn5 = QPushButton("运行函数五")
        btn5.setFixedHeight(36)
        self.output5 = QTextEdit()
        self.output5.setReadOnly(True)
        self.output5.setPlaceholderText("函数五输出将显示在此处...")
        self.output5.setFixedHeight(80)
        row5.addWidget(btn5)
        row5.addWidget(self.output5)
        layout.addLayout(row5)

        # 信号连接
        btn1.clicked.connect(self.on_btn1_clicked)
        btn2.clicked.connect(self.on_btn2_clicked)
        btn3.clicked.connect(self.on_btn3_clicked)
        btn4.clicked.connect(self.on_btn4_clicked)
        btn5.clicked.connect(self.on_btn5_clicked)

    # 示例函数与槽，可替换为实际业务逻辑
    def on_btn1_clicked(self):
        try:
            result = self.debug_func_one()
        except Exception as e:
            result = f"执行函数一发生错误：{e}"
        self.output1.setPlainText(str(result))

    def on_btn2_clicked(self):
        try:
            result = self.debug_func_two()
        except Exception as e:
            result = f"执行函数二发生错误：{e}"
        self.output2.setPlainText(str(result))

    def on_btn3_clicked(self):
        try:
            result = self.debug_func_three()
        except Exception as e:
            result = f"执行函数三发生错误：{e}"
        self.output3.setPlainText(str(result))

    def on_btn4_clicked(self):
        try:
            result = self.debug_func_four()
        except Exception as e:
            result = f"执行函数四发生错误：{e}"
        self.output4.setPlainText(str(result))

    def on_btn5_clicked(self):
        try:
            result = self.debug_func_five()
        except Exception as e:
            result = f"执行函数五发生错误：{e}"
        self.output5.setPlainText(str(result))

    def debug_func_one(self):
        return "函数一已执行：这是示例输出。"

    def debug_func_two(self):
        return "函数二已执行：这是另一个示例输出。"

    def debug_func_three(self):
        return "函数三已执行：占位示例输出。"

    def debug_func_four(self):
        return "函数四已执行：占位示例输出。"

    def debug_func_five(self):
        return "函数五已执行：占位示例输出。"