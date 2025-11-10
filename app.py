import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

# 修复 Windows 上 DPI 访问权限警告：强制使用 system DPI aware 模式
os.environ.setdefault("QT_QPA_PLATFORM", "windows:dpiawareness=1")

from pages import MainPage, InfoPage, AboutPage, DebugPage

# 自定义函数导入
from src import screen_information_judgment
sys.path.append(r'src')

class NavigationItem(QFrame):
    """极致紧凑型导航项"""
    clicked = pyqtSignal(int)

    def __init__(self, text, index, parent=None):
        super().__init__(parent)
        self.index = index
        self.text = text
        self.selected = False
        self.init_ui()

    def init_ui(self):
        self.setFixedHeight(40)
        # 保证水平填充、垂直不扩展（避免布局把多余空间分摊到每个条目之间）
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # 关键：设置样式时，用 padding 控制内容位置，避免 margin 引入外部空白
        self.setStyleSheet("""
            NavigationItem {
                background-color: white;
                border-radius: 6px;
                margin: 0;           /* 说明：Qt 样式不参与布局空隙，这里保持为 0 */
                padding: 0 12px 0 12px; /* 内边距统一 */
                border: none;
            }
            NavigationItem:hover {
                background-color: #f5f7fa;
            }
            NavigationItem[selected="true"] {
                background-color: #e3f2fd;
                border-left: 4px solid #2196f3;
                padding: 0 12px 0 8px; /* 左侧减少4px，让蓝色竖条“顶”出来 */
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 关键：移除布局内边距
        layout.setSpacing(0)  # 无间距

        self.label = QLabel(self.text)
        self.label.setFont(QFont("Microsoft YaHei", 10))
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.label)

        self.mousePressEvent = self.on_click

    def on_click(self, event):
        self.clicked.emit(self.index)

    def set_selected(self, selected):
        self.selected = selected
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EVE_TOOLS")
        self.resize(1000, 700)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)

        # ========== 左侧导航栏 ========== #
        nav_container = QWidget()
        nav_layout = QVBoxLayout()
        nav_container.setLayout(nav_layout)
        nav_container.setFixedWidth(200)
        nav_container.setStyleSheet("background-color: #f8f9fa;")

        # 标题
        title_label = QLabel("导航菜单")
        title_label.setFont(QFont("Microsoft YaHei", 13, QFont.Weight.Bold))
        title_label.setStyleSheet("padding: 12px 16px; color: #333;")
        nav_layout.addWidget(title_label)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #ddd; height: 1px;")
        nav_layout.addWidget(line)

        # 导航内容容器（无任何内边距）
        nav_content = QWidget()
        nav_content_layout = QVBoxLayout()
        nav_content.setLayout(nav_content_layout)
        nav_content_layout.setContentsMargins(0, 0, 0, 0)  # 关键：彻底移除内边距
        # 将条目间距压缩到 0，彻底去除“空挡”
        nav_content_layout.setSpacing(0)

        # 导航项
        nav_items = ["主控制台", "信息栏", "关于", "调试页面"]
        self.nav_items = []
        for i, text in enumerate(nav_items):
            item = NavigationItem(text, i)
            item.clicked.connect(self.switch_page)
            self.nav_items.append(item)
            nav_content_layout.addWidget(item)
        # 关键：在列表底部添加一个可伸缩空白，把所有多余空间压到最下面，
        # 防止 QVBoxLayout 在每个条目之间平均分配空隙。
        nav_content_layout.addStretch(1)

        # 滚动区（保持透明）
        scroll_area = QScrollArea()
        scroll_area.setWidget(nav_content)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("border: none; background-color: transparent;")

        nav_layout.addWidget(scroll_area)

        # ========== 右侧内容区 ========== #
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background-color: white;")

        # 创建页面（从 pages.py 加载独立配置）
        pages = [
            MainPage(),
            InfoPage(),
            AboutPage(),
            DebugPage(),
        ]

        for page in pages:
            self.stacked_widget.addWidget(page)

        # 默认选中第一个
        self.nav_items[0].set_selected(True)
        self.stacked_widget.setCurrentIndex(0)

        # 添加到主布局
        main_layout.addWidget(nav_container)
        main_layout.addWidget(self.stacked_widget)


    def switch_page(self, index):
        for i, item in enumerate(self.nav_items):
            item.set_selected(i == index)
        self.stacked_widget.setCurrentIndex(index)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())