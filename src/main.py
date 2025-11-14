from paddleocr import PaddleOCR

import pyautogui
import cv2
import numpy as np
from typing import Union, List
import os

# 加载环境变量
from dotenv import load_dotenv, find_dotenv,dotenv_values, set_key
import os
load_dotenv(find_dotenv())

from src import ore_data
import shutil

# 从环境变量获取总览区域
overview_area = eval(os.getenv('总览区域'))
总览区域比例 = eval(os.getenv('总览区域比例'))

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

def Imageecognition(screenshot = Screenshot()):
    """
    ### 图像识别函数 ###
    参数：
    screenshot: 截图
    返回：
    result: 识别结果
    ################
    """
    ocr = PaddleOCR(
    use_doc_orientation_classify=False, 
    use_doc_unwarping=False, 
    use_textline_orientation=False) # 文本检测+文本识别
    # ocr = PaddleOCR(use_doc_orientation_classify=True, use_doc_unwarping=True) # 文本图像预处理+文本检测+方向分类+文本识别
    # ocr = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False) # 文本检测+文本行方向分类+文本识别
    # ocr = PaddleOCR(
    #     text_detection_model_name="PP-OCRv5_mobile_det",
    #     text_recognition_model_name="PP-OCRv5_mobile_rec",
    #     use_doc_orientation_classify=False,
    #     use_doc_unwarping=False,
    #     use_textline_orientation=False) # 更换 PP-OCRv5_mobile 模型
    result = ocr.predict(screenshot)
    # 清空 tmp 文件夹并保存结果
    clear_tmp_folder()
    for res in result:
        res.print()
        res.save_to_img("./assets/tmp")
        res.save_to_json("./assets/tmp")

    return result

def Imageecognition_right_third(position_ratio: List[float] = None):
    """
    ### 对鼠标右上区域进行图像识别 ###
    参数：
    position_ratio: 鼠标位置比例 [x比例, y比例] (0.0到1.0之间)
                    例如：[0.33, 0.5] 表示鼠标在屏幕右侧1/3的上半边
                    如果为None，则使用默认值 [2/3, 0]（屏幕右侧1/3区域）
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
    
    # 初始化OCR
    ocr = PaddleOCR(
        use_doc_orientation_classify=False, 
        use_doc_unwarping=False, 
        use_textline_orientation=False
    )
    
    # 对截图进行OCR识别
    result = ocr.predict(screenshot)
    
    # 将坐标转换回原图坐标系（加上偏移量）
    offset_x = left
    offset_y = top
    
    # 清空 tmp 文件夹
    clear_tmp_folder()
    
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
        res.print()
        res.save_to_img("./assets/tmp")
        res.save_to_json("./assets/tmp")
    
    return result


