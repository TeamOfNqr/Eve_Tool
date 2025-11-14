import cv2
import numpy as np
import pyautogui
import os
from dotenv import load_dotenv, find_dotenv
import random
import pyautogui
import time

# 从 .env 文件加载环境变量
load_dotenv(find_dotenv())

def is_state_active(template_path, threshold= 0.8):
    """
    这是一段判断函数，通过对比关键截图模板与屏幕截图，给出相似率
    判断当前屏幕是否包含指定模板图像（即角色处于某状态）
    当前用于判断角色是否出站

    :param template_path: 模板图像路径（如 'dead_flag.png'）
    :param threshold: 匹配阈值，0.8 通常较可靠
    :return: 
        - 若 DEBUG=0 → bool (True/False)
        - 若 DEBUG=1 → list [bool, float] (匹配结果, 匹配率)
    """
    # 截图
    screenshot = pyautogui.screenshot()
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    # 获取脚本所在目录，拼接模板路径（确保路径正确）
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_template_path = os.path.join(project_root, template_path)

    # 读取模板
    template = cv2.imread(full_template_path, cv2.IMREAD_COLOR)
    if template is None:
        raise FileNotFoundError(f"模板文件未找到: {full_template_path}")

    # 模板匹配
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)

    matched = max_val >= threshold

    return [matched, max_val]

# print(is_state_active('assets/screenshot_comparison/mining_text_display.png',threshold=float(os.getenv('is_state_active_threshold'))))

def locate_template_on_screen(template_path, threshold=0.8):
    """
    在当前屏幕截图中定位模板图像的高相似区域。

    :param template_path: 模板图像路径（如 'assets/screenshot_comparison/leave_station_button.png'）
    :param threshold: 匹配阈值（0.0 ~ 1.0），低于此值则认为未找到
    :return: 
        - 若找到匹配区域：返回 (x, y, width, height) 的 tuple（左上角坐标 + 宽高）
        - 若未找到或模板无效：返回 None
    """

    # 截图并转换为 OpenCV 格式
    screenshot = pyautogui.screenshot()
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    # 构建模板完整路径
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_template_path = os.path.join(project_root, template_path)

    # 读取模板
    template = cv2.imread(full_template_path, cv2.IMREAD_COLOR)
    if template is None:
        raise FileNotFoundError(f"模板文件未找到: {full_template_path}")

    # 执行模板匹配
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # 判断是否达到阈值
    if max_val >= threshold:
        # max_loc 是匹配区域左上角坐标
        x, y = max_loc
        h, w = template.shape[:2]
        return (x, y, w, h)  # 返回 (x, y, width, height)
    else:
        return None

# 一段调试代码，实现输出查看
# print(locate_template_on_screen('assets/screenshot_comparison/mining_text_display.png',threshold=float(os.getenv('is_state_active_threshold'))))

###################################################################################################################

# 一个调试功能，实现对返回框线的绘制
import tkinter as tk

def highlight_region_on_screen(rect, duration=2000):
    """
    在屏幕上创建一个透明窗口，并用红色边框高亮指定矩形区域。

    :param rect: (x, y, width, height) 的 tuple，由 locate_template_on_screen 返回
    :param duration: 高亮窗口显示的毫秒数（默认 2000ms = 2秒），设为 None 则需手动关闭
    """
    if rect is None:
        return

    x, y, w, h = rect

    # 创建全屏透明窗口
    root = tk.Tk()
    root.overrideredirect(True)           # 无边框
    root.attributes('-topmost', True)     # 置顶
    root.attributes('-transparentcolor', 'white')  # 将白色设为透明色
    root.config(bg='white')

    # 设置窗口尺寸为整个屏幕
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f"{screen_width}x{screen_height}+0+0")

    # 创建 Canvas 用于绘图
    canvas = tk.Canvas(root, width=screen_width, height=screen_height, bg='white', highlightthickness=0)
    canvas.pack()

    # 绘制红色边框矩形（注意：Canvas 坐标是 (x1, y1, x2, y2)）
    canvas.create_rectangle(x, y, x + w, y + h, outline='red', width=3)

    # 自动关闭窗口（可选）
    if duration is not None:
        root.after(duration, root.destroy)

    # 启动窗口（非阻塞主逻辑需在主线程调用）
    root.mainloop()

# rect = locate_template_on_screen(r'assets\screenshot_comparison_4K_100\arm\ice_ore_collector_F2.png',
#                                  threshold=float(os.getenv('is_state_active_threshold', 0.7)))

# # 高亮显示 2 秒
# overview_area = eval(os.getenv('overview_area'))  # 转换为元组
# highlight_region_on_screen(rect = overview_area, duration=2000)