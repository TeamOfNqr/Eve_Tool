from paddleocr import PaddleOCR

import pyautogui
import cv2
import numpy as np
from typing import Union, List

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
    for res in result:
        # 辅助函数：转换多边形坐标
        def transform_poly(poly_list):
            """转换多边形坐标列表"""
            if poly_list is None:
                return
            for poly in poly_list:
                for point in poly:
                    point[0] += x_min
                    point[1] += y_min
        
        # 辅助函数：转换矩形框坐标
        def transform_boxes(box_list):
            """转换矩形框坐标列表"""
            if box_list is None:
                return
            for box in box_list:
                box[0] += x_min  # x_min
                box[1] += y_min  # y_min
                box[2] += x_min  # x_max
                box[3] += y_min  # y_max
        
        # 尝试访问结果对象的属性并转换坐标
        # 优先使用属性访问，如果没有则尝试字典访问
        if hasattr(res, 'dt_polys'):
            transform_poly(getattr(res, 'dt_polys', None))
        elif hasattr(res, '__dict__') and 'dt_polys' in res.__dict__:
            transform_poly(res.__dict__['dt_polys'])
        
        if hasattr(res, 'rec_polys'):
            transform_poly(getattr(res, 'rec_polys', None))
        elif hasattr(res, '__dict__') and 'rec_polys' in res.__dict__:
            transform_poly(res.__dict__['rec_polys'])
        
        if hasattr(res, 'rec_boxes'):
            transform_boxes(getattr(res, 'rec_boxes', None))
        elif hasattr(res, '__dict__') and 'rec_boxes' in res.__dict__:
            transform_boxes(res.__dict__['rec_boxes'])
        
        # 保存结果（可选）
        res.print()
        res.save_to_img("./output")
        res.save_to_json("./output")
    
    return result

# Imageecognition(screenshot="image.png")

# Imageecognition_region 使用示例：
# 1. 使用图片路径和矩形区域进行识别
# result = Imageecognition_region(
#     screenshot="image.png",
#     region_box=[100, 100, 500, 300]  # [x_min, y_min, x_max, y_max]
# )

# 2. 使用numpy数组（截图）和矩形区域进行识别
# screenshot = Screenshot()
# result = Imageecognition_region(
#     screenshot=screenshot,
#     region_box=[152, 16, 358, 77]  # [x_min, y_min, x_max, y_max]
# )

# 3. 结合highlight_region使用，先高亮显示区域，再进行识别
# from src.tools import highlight_region
# region_box = [152, 16, 358, 77]  # 矩形格式
# highlight_region(region_box, duration=2000)  # 高亮显示2秒
# result = Imageecognition_region("image.png", region_box=region_box)



