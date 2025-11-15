from functools import partial
import io
import re
from contextlib import redirect_stdout
from PyQt6.QtCore import QCoreApplication


from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QGridLayout, QScrollArea, QListWidget, QListWidgetItem, QMainWindow
)
from PyQt6.QtGui import QFont, QTextCursor, QColor, QMouseEvent
from PyQt6.QtCore import Qt, QTimer, QPoint

import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from src import ore_data
from src import main
from src import tools
from src import window_status
from src import complex_events
# import main
# import tools
# import ore_data
# import window_status
# import complex_events

# 从环境变量获取总览区域
调试模式 = int(eval(os.getenv('调试模式')))

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


class DebugPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #e9ecef;")

        layout = QVBoxLayout(self)
        title = QLabel("▶ 关于")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #333; padding: 20px;")
        layout.addWidget(title)


