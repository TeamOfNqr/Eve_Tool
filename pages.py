from functools import partial

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QGridLayout
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt


class MainPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #ffffff;")

        layout = QVBoxLayout(self)
        title = QLabel("主控制台")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #333; padding: 20px;")
        layout.addWidget(title)


class InfoPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #f8f9fa;")

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(20)

        self._build_title()
        self._build_info_pairs()
        self._build_basic_info_section()

    def _build_title(self):
        title = QLabel("信息栏")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "color: #333; padding: 16px 20px; background-color: #ffffff; border-radius: 8px;"
        )
        self.main_layout.addWidget(title)

    def _build_info_pairs(self):
        pair_container = QWidget()
        pair_container.setStyleSheet("background-color: transparent;")
        pair_layout = QGridLayout()
        pair_layout.setContentsMargins(0, 0, 0, 0)
        pair_layout.setHorizontalSpacing(20)
        pair_layout.setVerticalSpacing(18)
        pair_container.setLayout(pair_layout)

        self.info_buttons = []
        self.info_outputs = []

        pair_configs = [
            ("刷新状态", "状态详情将在此显示……"),
            ("加载日志", "日志内容将在此显示……"),
            ("同步数据", "数据同步结果将在此显示……"),
            ("导出报告", "报告生成信息将在此显示……"),
        ]

        for index, (btn_text, placeholder) in enumerate(pair_configs):
            row_widget, button, text_edit = self._create_info_pair(btn_text, placeholder)
            grid_row = index // 2
            grid_col = index % 2
            pair_layout.addWidget(row_widget, grid_row, grid_col)

            button.clicked.connect(partial(self.on_info_button_clicked, index))
            self.info_buttons.append(button)
            self.info_outputs.append(text_edit)

        self.main_layout.addWidget(pair_container)

    def _create_info_pair(self, button_text, placeholder):
        pair_widget = QWidget()
        pair_widget.setStyleSheet(
            """
            background-color: rgba(255, 255, 255, 0.92);
            border-radius: 10px;
            padding: 16px;
            """
        )
        pair_layout = QHBoxLayout()
        pair_layout.setContentsMargins(0, 0, 0, 0)
        pair_layout.setSpacing(12)
        pair_widget.setLayout(pair_layout)

        button = QPushButton(button_text)
        button.setFixedHeight(36)
        button.setStyleSheet(
            """
            QPushButton {
                background-color: #f1f3f5;
                border: 1px solid rgba(0, 0, 0, 30);
                border-radius: 6px;
                padding: 6px 12px;
                color: #212529;
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
        )

        text_container = QWidget()
        text_container.setStyleSheet(
            """
            background-color: #ffffff;
            border: 1px solid rgba(0, 0, 0, 35);
            border-radius: 8px;
            padding: 6px;
            """
        )
        text_container_layout = QVBoxLayout()
        text_container_layout.setContentsMargins(0, 0, 0, 0)
        text_container_layout.setSpacing(0)
        text_container.setLayout(text_container_layout)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setFixedHeight(80)
        text_edit.setPlaceholderText(placeholder)
        text_edit.setStyleSheet(
            """
            QTextEdit {
                background-color: transparent;
                border: none;
                padding: 6px;
            }
            """
        )
        text_container_layout.addWidget(text_edit)

        pair_layout.addWidget(button)
        pair_layout.addWidget(text_container)

        return pair_widget, button, text_edit

    def _build_basic_info_section(self):
        info_container = QWidget()
        info_container.setStyleSheet(
            """
            background-color: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(0, 0, 0, 35);
            border-radius: 12px;
            """
        )
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(20, 22, 20, 20)
        info_layout.setSpacing(14)
        info_container.setLayout(info_layout)

        info_label = QLabel("基础信息")
        info_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        info_label.setStyleSheet(
            """
            color: #495057;
            background-color: transparent;
            padding: 4px 6px;
            """
        )

        self.info_summary = QTextEdit()
        self.info_summary.setReadOnly(True)
        self.info_summary.setPlaceholderText("核心信息将在此显示，可根据实际业务进行填充。")
        self.info_summary.setStyleSheet(
            """
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid rgba(0, 0, 0, 25);
                border-radius: 8px;
                padding: 12px;
            }
            """
        )
        self.info_summary.setMinimumHeight(220)

        info_layout.addWidget(info_label)
        info_layout.addWidget(self.info_summary)

        self.main_layout.addWidget(info_container)

    def on_info_button_clicked(self, index):
        self.info_outputs[index].setPlainText(
            f"已触发操作：{self.info_buttons[index].text()}。\n请在此接入实际处理逻辑。"
        )


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