from paddleocr import PaddleOCR

import pyautogui
import cv2
import numpy as np
from typing import Union, List
import os
import logging
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO


# 加载环境变量
from dotenv import load_dotenv, find_dotenv,dotenv_values, set_key
load_dotenv(find_dotenv())

import shutil

# 设置 PaddleOCR 的日志级别为 ERROR，抑制 INFO 和 WARNING 输出
logging.getLogger('ppocr').setLevel(logging.ERROR)
logging.getLogger('paddleocr').setLevel(logging.ERROR)
logging.getLogger('paddlex').setLevel(logging.ERROR)


from src import ore_data
from src import tools
from src import window_status
# import tools
# import ore_data
# import window_status

# 从环境变量获取总览区域
overview_area = eval(os.getenv('总览区域'))
总览区域比例 = eval(os.getenv('总览区域比例'))
锁定状态监控区 = eval(os.getenv('锁定状态监控区'))

def clear_tmp_folder():
    """
    ### 清空 assets/tmp 文件夹内容 ###
    """
    tmp_path = "./assets/tmp"
    if os.path.exists(tmp_path):
        for filename in os.listdir(tmp_path):
            file_path = os.path.join(tmp_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"删除文件/文件夹时出错 {file_path}: {e}")

def Screenshot(region=None):
    """
    ### 截图函数 ###
    参数：
    region: 截图区域 (left, top, width, height)
    返回：
    screenshot: 截图
    ################
    """
    screenshot = pyautogui.screenshot(region=region)
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    return screenshot

def Imageecognition(region = None,verbose: bool = True):
    """
    ### 对锁定状态监控区进行图像识别 ###
    参数：
    region: 截图区域 (left, top, width, height)
    verbose: 是否打印OCR识别结果，默认为True
    返回：
    result: 识别结果（坐标已转换回原图坐标系）
    ################
    """
    
    # 验证区域格式
    if not isinstance(region, (list, tuple)) or len(region) != 4:
        raise ValueError("锁定状态监控区必须是包含4个元素的列表或元组: (x1, y1, width, height)")
    
    left, top, width, height = region
    
    # 截取锁定状态监控区
    screenshot = Screenshot(region=region)
    
    # 初始化OCR（抑制输出）
    # 使用 StringIO 来捕获并丢弃 PaddleOCR 的输出
    null_stream = StringIO()
    with redirect_stdout(null_stream), redirect_stderr(null_stream):
        ocr = PaddleOCR(
            use_doc_orientation_classify=False, 
            use_doc_unwarping=False, 
            use_textline_orientation=False
        )
        # 对截图进行OCR识别
        result = ocr.predict(screenshot)
        ocr = PaddleOCR(
            text_detection_model_name="PP-OCRv5_mobile_det",
            text_recognition_model_name="PP-OCRv5_mobile_rec",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False)
    # 将坐标转换回原图坐标系（加上偏移量）
    offset_x = left
    offset_y = top
    
    # 清空 tmp 文件夹
    clear_tmp_folder()
    
    # 创建新的 null_stream 用于保存文件时抑制输出
    null_stream_save = StringIO()
    
    for res in result:
        # 辅助函数：转换多边形坐标
        def transform_poly(poly_list):
            """转换多边形坐标列表"""
            if poly_list is None:
                return
            for i, poly in enumerate(poly_list):
                if poly is None:
                    continue
                new_poly = []
                for point in poly:
                    if isinstance(point, (list, tuple)) and len(point) >= 2:
                        new_poly.append([point[0] + offset_x, point[1] + offset_y])
                    else:
                        new_poly.append(point)
                poly_list[i] = new_poly
        
        # 辅助函数：转换矩形框坐标
        def transform_boxes(box_list):
            """转换矩形框坐标列表"""
            if box_list is None:
                return
            for i, box in enumerate(box_list):
                if box is None:
                    continue
                if isinstance(box, (list, tuple)) and len(box) >= 4:
                    box_list[i] = [
                        box[0] + offset_x,  # x_min
                        box[1] + offset_y,  # y_min
                        box[2] + offset_x,  # x_max
                        box[3] + offset_y   # y_max
                    ]
        
        # 转换坐标
        converted_keys = set()
        
        if hasattr(res, '__dict__'):
            res_dict = res.__dict__
            
            if 'dt_polys' in res_dict and res_dict['dt_polys'] is not None and 'dt_polys' not in converted_keys:
                transform_poly(res_dict['dt_polys'])
                converted_keys.add('dt_polys')
            
            if 'rec_polys' in res_dict and res_dict['rec_polys'] is not None and 'rec_polys' not in converted_keys:
                transform_poly(res_dict['rec_polys'])
                converted_keys.add('rec_polys')
            
            if 'rec_boxes' in res_dict and res_dict['rec_boxes'] is not None and 'rec_boxes' not in converted_keys:
                transform_boxes(res_dict['rec_boxes'])
                converted_keys.add('rec_boxes')
        
        # 如果__dict__中没有，尝试直接属性访问
        if 'dt_polys' not in converted_keys and hasattr(res, 'dt_polys'):
            dt_polys = getattr(res, 'dt_polys', None)
            if dt_polys is not None:
                transform_poly(dt_polys)
                try:
                    setattr(res, 'dt_polys', dt_polys)
                except:
                    pass
        
        if 'rec_polys' not in converted_keys and hasattr(res, 'rec_polys'):
            rec_polys = getattr(res, 'rec_polys', None)
            if rec_polys is not None:
                transform_poly(rec_polys)
                try:
                    setattr(res, 'rec_polys', rec_polys)
                except:
                    pass
        
        if 'rec_boxes' not in converted_keys and hasattr(res, 'rec_boxes'):
            rec_boxes = getattr(res, 'rec_boxes', None)
            if rec_boxes is not None:
                transform_boxes(rec_boxes)
                try:
                    setattr(res, 'rec_boxes', rec_boxes)
                except:
                    pass
        
        # 保存结果
        if verbose:
            res.print()
        # 抑制保存文件时的输出
        with redirect_stdout(null_stream_save), redirect_stderr(null_stream_save):
            res.save_to_img("./assets/tmp")
            res.save_to_json("./assets/tmp")
    
    return result

def Imageecognition_right_third(position_ratio: List[float] = None, verbose: bool = True):
    """
    ### 对鼠标右上区域进行图像识别 ###
    参数：
    position_ratio: 鼠标位置比例 [x比例, y比例] (0.0到1.0之间)
                    例如：[0.33, 0.5] 表示鼠标在屏幕右侧1/3的上半边
                    如果为None，则使用默认值 [2/3, 0]（屏幕右侧1/3区域）
    verbose: 是否打印OCR识别结果，默认为True
    返回：
    result: 识别结果（坐标已转换回原图坐标系）
    ################
    """
    # 获取屏幕尺寸
    screen_width, screen_height = pyautogui.size()
    
    # 如果未提供比例参数，使用默认值（屏幕右侧1/3区域）
    if position_ratio is None:
        position_ratio = [0.75, 0.47]
    
    # 验证参数格式
    if not isinstance(position_ratio, (list, tuple)) or len(position_ratio) != 2:
        raise ValueError("position_ratio 必须是包含2个元素的列表或元组: [x比例, y比例]")
    
    x_ratio, y_ratio = position_ratio
    
    # 验证比例范围
    if not (0.0 <= x_ratio <= 1.0) or not (0.0 <= y_ratio <= 1.0):
        raise ValueError("比例值必须在0.0到1.0之间")
    
    # 根据比例计算鼠标位置
    mouse_x = int(screen_width * x_ratio)
    mouse_y = int(screen_height * y_ratio)
    
    # 计算从鼠标位置到屏幕右上角的区域
    # 从鼠标x位置开始，到右边界
    left = mouse_x
    top = 0  # 从屏幕顶部开始
    width = screen_width - left  # 从鼠标x位置到右边界
    height = mouse_y  # 从顶部到鼠标y位置（上半边）
    
    # 截取鼠标右上区域
    region = (left, top, width, height)
    screenshot = Screenshot(region=region)
    
    # 初始化OCR（抑制输出）
    # 使用 StringIO 来捕获并丢弃 PaddleOCR 的输出
    null_stream = StringIO()
    with redirect_stdout(null_stream), redirect_stderr(null_stream):
        ocr = PaddleOCR(
            use_doc_orientation_classify=False, 
            use_doc_unwarping=False, 
            use_textline_orientation=False
        )
        # 对截图进行OCR识别
        result = ocr.predict(screenshot)
        ocr = PaddleOCR(
            text_detection_model_name="PP-OCRv5_mobile_det",
            text_recognition_model_name="PP-OCRv5_mobile_rec",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False)
    # 将坐标转换回原图坐标系（加上偏移量）
    offset_x = left
    offset_y = top
    
    # 清空 tmp 文件夹
    clear_tmp_folder()
    
    # 创建新的 null_stream 用于保存文件时抑制输出
    null_stream_save = StringIO()
    
    for res in result:
        # 辅助函数：转换多边形坐标
        def transform_poly(poly_list):
            """转换多边形坐标列表"""
            if poly_list is None:
                return
            for i, poly in enumerate(poly_list):
                if poly is None:
                    continue
                new_poly = []
                for point in poly:
                    if isinstance(point, (list, tuple)) and len(point) >= 2:
                        new_poly.append([point[0] + offset_x, point[1] + offset_y])
                    else:
                        new_poly.append(point)
                poly_list[i] = new_poly
        
        # 辅助函数：转换矩形框坐标
        def transform_boxes(box_list):
            """转换矩形框坐标列表"""
            if box_list is None:
                return
            for i, box in enumerate(box_list):
                if box is None:
                    continue
                if isinstance(box, (list, tuple)) and len(box) >= 4:
                    box_list[i] = [
                        box[0] + offset_x,  # x_min
                        box[1] + offset_y,  # y_min
                        box[2] + offset_x,  # x_max
                        box[3] + offset_y   # y_max
                    ]
        
        # 转换坐标
        converted_keys = set()
        
        if hasattr(res, '__dict__'):
            res_dict = res.__dict__
            
            if 'dt_polys' in res_dict and res_dict['dt_polys'] is not None and 'dt_polys' not in converted_keys:
                transform_poly(res_dict['dt_polys'])
                converted_keys.add('dt_polys')
            
            if 'rec_polys' in res_dict and res_dict['rec_polys'] is not None and 'rec_polys' not in converted_keys:
                transform_poly(res_dict['rec_polys'])
                converted_keys.add('rec_polys')
            
            if 'rec_boxes' in res_dict and res_dict['rec_boxes'] is not None and 'rec_boxes' not in converted_keys:
                transform_boxes(res_dict['rec_boxes'])
                converted_keys.add('rec_boxes')
        
        # 如果__dict__中没有，尝试直接属性访问
        if 'dt_polys' not in converted_keys and hasattr(res, 'dt_polys'):
            dt_polys = getattr(res, 'dt_polys', None)
            if dt_polys is not None:
                transform_poly(dt_polys)
                try:
                    setattr(res, 'dt_polys', dt_polys)
                except:
                    pass
        
        if 'rec_polys' not in converted_keys and hasattr(res, 'rec_polys'):
            rec_polys = getattr(res, 'rec_polys', None)
            if rec_polys is not None:
                transform_poly(rec_polys)
                try:
                    setattr(res, 'rec_polys', rec_polys)
                except:
                    pass
        
        if 'rec_boxes' not in converted_keys and hasattr(res, 'rec_boxes'):
            rec_boxes = getattr(res, 'rec_boxes', None)
            if rec_boxes is not None:
                transform_boxes(rec_boxes)
                try:
                    setattr(res, 'rec_boxes', rec_boxes)
                except:
                    pass
        
        # 保存结果
        if verbose:
            res.print()
        # 抑制保存文件时的输出
        with redirect_stdout(null_stream_save), redirect_stderr(null_stream_save):
            res.save_to_img("./assets/tmp")
            res.save_to_json("./assets/tmp")
    
    return result

def is_state_active(template_path, screenshot_ ,threshold= 0.7):
    """
    这是一段判断函数，通过对比关键截图模板与屏幕截图，给出相似率
    判断当前屏幕是否包含指定模板图像（即角色处于某状态）
    当前用于判断角色是否出站

    :param template_path: 模板图像路径
    :param screenshot_: 对比图像
    :param threshold: 匹配阈值，0.8 通常较可靠
    :return: 
        - 若 DEBUG=0 → bool (True/False)
        - 若 DEBUG=1 → list [bool, float] (匹配结果, 匹配率)
    """
    screenshot = screenshot_

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

