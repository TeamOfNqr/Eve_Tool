import os
import sys
# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv, find_dotenv,dotenv_values, set_key
load_dotenv(find_dotenv())

from src import ore_data
from src import main
from src import tools
from src import window_status
from src import complex_events

# 从环境变量获取总览区域
调试模式 = int(eval(os.getenv('调试模式')))
锁定状态监控区 = eval(os.getenv('锁定状态监控区'))


# from paddleocr import TextDetection
# model = TextDetection(model_name="PP-OCRv5_server_det")
# output = model.predict("image.png", batch_size=1)
# for res in output:
#     res.print()
#     res.save_to_img(save_path="./output/")
#     res.save_to_json(save_path="./output/res.json")

# from paddleocr import TextRecognition

# model = TextRecognition()
# output = model.predict(input="general_ocr_rec_001.png")
# for res in output:
#     res.print()
#     res.save_to_img(save_path="./output/")
#     res.save_to_json(save_path="./output/res.json")   


from paddleocr import PaddleOCR

ocr = PaddleOCR(
    use_doc_orientation_classify=False, 
    use_doc_unwarping=False, 
    use_textline_orientation=False) # 文本检测+文本识别
# ocr = PaddleOCR(use_doc_orientation_classify=True, use_doc_unwarping=True) # 文本图像预处理+文本检测+方向分类+文本识别
# ocr = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False) # 文本检测+文本行方向分类+文本识别
ocr = PaddleOCR(
    text_detection_model_name="PP-OCRv5_mobile_det",
    text_recognition_model_name="PP-OCRv5_mobile_rec",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False) # 更换 PP-OCRv5_mobile 模型

screenshot_ = tools.area_screenshot(region = 锁定状态监控区)
result = ocr.predict(screenshot_)
for res in result:
    res.print()
    res.save_to_img("test/output")
    res.save_to_json("test/output")