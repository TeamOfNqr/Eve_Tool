import random
import time
import easyocr
import pyautogui
import cv2
import numpy as np
import time
import os
from dotenv import load_dotenv, find_dotenv
from screen_information_judgment import locate_template_on_screen

# 自定义函数导入
import sys
sys.path.append(r'src')
import window_status

# 鼠标模拟点击函数

def click_random_point_in_ellipse(bounding_box, delay=0.2, debug=False, click_button=0):
    '''
    在给定 bounding_box 定义的椭圆区域内随机选择一点进行鼠标点击。
    可接受 locate_template_on_screen() 等函数返回的 (x, y, w, h) 格式。

    :param bounding_box: (x, y, w, h) 元组，定义外接矩形
    :param delay: 点击前的延迟时间（秒）
    :param debug: 是否打印调试信息
    :param click_button: 0 表示左键点击，1 表示右键点击
    '''
    if bounding_box is None:
        if debug:
            print("❌ 未找到目标区域，跳过点击")
        return

    x, y, w, h = bounding_box
    if w <= 0 or h <= 0:
        if debug:
            print("⚠️ 无效的区域尺寸")
        return

    cx, cy = x + w / 2, y + h / 2
    a, b = w / 2, h / 2

    # 生成椭圆内随机点
    for _ in range(100):  # 最多重试100次
        rx = random.uniform(-a, a)
        ry = random.uniform(-b, b)
        if (rx / a) ** 2 + (ry / b) ** 2 <= 1:
            click_x = int(cx + rx)
            click_y = int(cy + ry)

            # 确定按钮类型
            button_type = 'left' if click_button == 0 else 'right'

            if debug:
                print(f"🖱️ 尝试{button_type}键点击: ({click_x}, {click_y})")

            time.sleep(delay)
            pyautogui.moveTo(click_x, click_y)  # 可选：便于观察
            pyautogui.click(click_x, click_y, button=button_type)
            return

    if debug:
        print("⚠️ 未能在椭圆内生成有效点击点")

# ===========================================================================================================
# 调试

# bbox = locate_template_on_screen(
#     r'assets\screenshot_comparison_4K_100\arm\ice_ore_collector_F1.png',
#     threshold=float(os.getenv('is_state_active_threshold', 0.8))
# )

# # ✅ 示例1：左键点击（默认行为）
# # click_random_point_in_ellipse(bbox, click_button=0, debug=True)

# # ✅ 示例2：右键点击
# click_random_point_in_ellipse(bbox, click_button=1, debug=True)

# ===========================================================================================================

# 加载环境变量
load_dotenv(find_dotenv())

# 从环境变量获取总览区域
overview_area = eval(os.getenv('overview_area'))  # 转换为元组
list_of_text_confidence = eval(os.getenv('list_of_text_confidence'))

# 初始化 OCR 阅读器，支持简体中文和英文
reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)

def click_on_text_in_region(target_text, region=None, confidence_threshold=list_of_text_confidence, click_button=0, offset_range=3):
    """
    在指定屏幕区域内查找目标文字，并在其位置点击（带随机微偏移，模拟真人）。
    
    :param target_text: 要查找的文字，例如 "小行星带"
    :param region: 截图区域 (left, top, width, height)
    :param confidence_threshold: OCR置信度阈值
    :param click_button: 0=左键, 1=右键
    :param offset_range: 随机偏移的最大像素值（默认±3）
    """
    print(f"正在查找文字: '{target_text}'")

    # 1. 截图
    if region:
        screenshot = pyautogui.screenshot(region=region)
    else:
        screenshot = pyautogui.screenshot()

    # 2. 转换为OpenCV格式 (BGR)
    screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    # 3. 使用 EasyOCR 识别文字
    results = reader.readtext(screenshot_cv)

    # 4. 遍历所有识别结果
    for (bbox, text, prob) in results:
        if prob < confidence_threshold:
            continue

        if target_text in text:
            # 计算文本框中心点
            x_coords = [point[0] for point in bbox]
            y_coords = [point[1] for point in bbox]
            center_x = int((min(x_coords) + max(x_coords)) / 2)
            center_y = int((min(y_coords) + max(y_coords)) / 2)

            # 加上区域偏移（如果指定了 region）
            if region:
                center_x += region[0]
                center_y += region[1]

            # 👇 添加微小随机偏移（模拟真人点击）
            offset_x = random.randint(-offset_range, offset_range)
            offset_y = random.randint(-offset_range, offset_range)
            click_x = center_x + offset_x
            click_y = center_y + offset_y

            # 确定按钮类型
            button_type = 'left' if click_button == 0 else 'right'
            print(f"✅ 找到文字 '{text}'，置信度 {prob:.2f}，{button_type}键点击位置 ({click_x}, {click_y}) "
                  f"[偏移: ({offset_x}, {offset_y})]")

            # 移动并点击
            pyautogui.moveTo(click_x, click_y, duration=0.2 + random.uniform(0, 0.1))  # 移动时间也加点随机
            time.sleep(0.1 + random.uniform(0, 0.1))
            pyautogui.click(button=button_type)

            return True

    print(f"❌ 未找到包含 '{target_text}' 的文字")
    return False

# ===========================================================================================================
# 调试 

# target = "小行星带"
# click_on_text_in_region(
#     target_text=target,
#     region=overview_area,
#     click_button=1,      # 1 = 右键
#     offset_range=3       # ±3 像素偏移（可根据需要调整为 2~5）
# )

# ===========================================================================================================