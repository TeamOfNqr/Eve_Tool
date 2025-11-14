from paddleocr import PaddleOCR

import pyautogui
import cv2
import numpy as np
from typing import Union, List
import json
import os
from pathlib import Path

# 加载环境变量
from dotenv import load_dotenv, find_dotenv,dotenv_values, set_key
import os
load_dotenv(find_dotenv())

# 从环境变量获取总览区域
overview_area = eval(os.getenv('总览区域'))


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
    for res in result:
        res.print()
        res.save_to_img("./output")
        res.save_to_json("./output")

    return result

def Imageecognition_region(
    screenshot: Union[str, np.ndarray],
    region_box: List[int],
    use_doc_orientation_classify: bool = False,
    use_doc_unwarping: bool = False,
    use_textline_orientation: bool = False
):
    """
    ### 对图片的指定区域进行图像识别 ###
    参数：
    screenshot: 截图（图片路径字符串或numpy数组）
    region_box: 识别区域的矩形坐标 [x_min, y_min, x_max, y_max] (4个数值)
    use_doc_orientation_classify: 是否使用文档方向分类
    use_doc_unwarping: 是否使用文档展开
    use_textline_orientation: 是否使用文本行方向检测
    返回：
    result: 识别结果（格式与Imageecognition相同，坐标已转换回原图坐标系）
    ################
    """
    # 验证矩形格式
    if len(region_box) != 4:
        raise ValueError("区域矩形格式需要4个数值: [x_min, y_min, x_max, y_max]")
    
    x_min, y_min, x_max, y_max = region_box
    
    # 验证坐标有效性
    if x_min >= x_max or y_min >= y_max:
        raise ValueError("无效的矩形坐标: x_min必须小于x_max, y_min必须小于y_max")
    
    # 读取图片
    if isinstance(screenshot, str):
        # 如果是字符串，当作文件路径读取
        img = cv2.imread(screenshot)
        if img is None:
            raise ValueError(f"无法读取图片: {screenshot}")
    else:
        # 如果是numpy数组，直接使用
        img = screenshot.copy()
    
    # 确保坐标在图片范围内
    x_min = max(0, int(x_min))
    y_min = max(0, int(y_min))
    x_max = min(img.shape[1], int(x_max))
    y_max = min(img.shape[0], int(y_max))
    
    # 裁剪图片区域
    cropped_img = img[y_min:y_max, x_min:x_max]
    
    if cropped_img.size == 0:
        raise ValueError("裁剪后的图片区域为空，请检查坐标是否正确")
    
    # 初始化OCR
    ocr = PaddleOCR(
        use_doc_orientation_classify=use_doc_orientation_classify,
        use_doc_unwarping=use_doc_unwarping,
        use_textline_orientation=use_textline_orientation
    )
    
    # 对裁剪后的区域进行OCR识别
    result = ocr.predict(cropped_img)
    
    # 将坐标转换回原图坐标系（加上偏移量）
    # 保存原始偏移量，用于坐标转换
    offset_x = x_min
    offset_y = y_min
    
    for res in result:
        # 辅助函数：转换多边形坐标（创建新列表，确保修改生效）
        def transform_poly(poly_list):
            """转换多边形坐标列表"""
            if poly_list is None:
                return
            for i, poly in enumerate(poly_list):
                if poly is None:
                    continue
                # 创建新的多边形列表
                new_poly = []
                for point in poly:
                    if isinstance(point, (list, tuple)) and len(point) >= 2:
                        new_poly.append([point[0] + offset_x, point[1] + offset_y])
                    else:
                        new_poly.append(point)
                poly_list[i] = new_poly
        
        # 辅助函数：转换矩形框坐标（创建新列表，确保修改生效）
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
        
        # 尝试访问结果对象的属性并转换坐标
        # 优先通过__dict__访问，因为这样可以确保修改生效
        converted_keys = set()  # 记录已转换的键，避免重复转换
        
        if hasattr(res, '__dict__'):
            res_dict = res.__dict__
            
            # 转换 dt_polys
            if 'dt_polys' in res_dict and res_dict['dt_polys'] is not None and 'dt_polys' not in converted_keys:
                transform_poly(res_dict['dt_polys'])
                converted_keys.add('dt_polys')
            
            # 转换 rec_polys
            if 'rec_polys' in res_dict and res_dict['rec_polys'] is not None and 'rec_polys' not in converted_keys:
                transform_poly(res_dict['rec_polys'])
                converted_keys.add('rec_polys')
            
            # 转换 rec_boxes
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
        
        # 保存结果（在坐标转换之后）
        res.print()
        res.save_to_img("./output")
        
        # 保存JSON文件路径，用于后续坐标转换
        # 获取保存的JSON文件路径（PaddleOCR通常使用时间戳命名）
        json_files_before = set(Path("./output").glob("*_res.json"))
        res.save_to_json("./output")
        json_files_after = set(Path("./output").glob("*_res.json"))
        new_json_files = json_files_after - json_files_before
        
        # 如果找到了新生成的JSON文件，确保坐标已转换
        for json_file in new_json_files:
            try:
                # 读取JSON文件
                with open(json_file, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                # 转换坐标
                coordinate_converted = False
                
                # 转换 dt_polys
                if 'dt_polys' in json_data and json_data['dt_polys']:
                    for poly in json_data['dt_polys']:
                        if poly:
                            for point in poly:
                                if isinstance(point, list) and len(point) >= 2:
                                    point[0] += offset_x
                                    point[1] += offset_y
                                    coordinate_converted = True
                
                # 转换 rec_polys
                if 'rec_polys' in json_data and json_data['rec_polys']:
                    for poly in json_data['rec_polys']:
                        if poly:
                            for point in poly:
                                if isinstance(point, list) and len(point) >= 2:
                                    point[0] += offset_x
                                    point[1] += offset_y
                                    coordinate_converted = True
                
                # 转换 rec_boxes
                if 'rec_boxes' in json_data and json_data['rec_boxes']:
                    for box in json_data['rec_boxes']:
                        if isinstance(box, list) and len(box) >= 4:
                            box[0] += offset_x  # x_min
                            box[1] += offset_y  # y_min
                            box[2] += offset_x  # x_max
                            box[3] += offset_y  # y_max
                            coordinate_converted = True
                
                # 如果坐标被转换了，重新保存JSON文件
                if coordinate_converted:
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, ensure_ascii=False, indent=4)
            except Exception as e:
                # 如果JSON转换失败，不影响主流程
                print(f"警告: 无法转换JSON文件 {json_file} 中的坐标: {e}")
    
    return result

