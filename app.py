import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton,
    QTextEdit, QVBoxLayout, QHBoxLayout
)
from PyQt5.QtCore import Qt
import os

# 自定义函数导入
import sys

from src import screen_information_judgment

sys.path.append(r'src')

#####################################################################################################################################################################

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # 设置窗口标题和大小
        self.setWindowTitle("EVE_TOOLS")
        self.resize(600, 400)

        # 创建按钮
        self.run_button = QPushButton("执行角色检测")
        self.run_button.clicked.connect(self.on_button_click)  # 绑定点击事件

        # 创建文本框（用于显示结果）
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)  # 设置为只读
        self.result_text.setPlaceholderText("检测结果将显示在此处...")

        # 布局
        layout = QVBoxLayout()
        layout.addWidget(self.run_button)
        layout.addWidget(self.result_text)
        self.setLayout(layout)

    def on_button_click(self):
        # 调用你的函数并获取结果
        result = screen_information_judgment.is_state_active('assets/screenshot_comparison/leave_station_button.png',threshold=float(os.getenv('is_state_active_threshold')))
        # 将结果写入文本框
        self.result_text.setPlainText(str(result))

#####################################################################################################################################################################

# 启动应用
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())