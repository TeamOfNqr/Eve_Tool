from nt import write
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
import time

from src import tools

# 从环境变量获取总览区域
置顶显示 = eval(os.getenv('置顶显示'))


def Info_Show():
    """
    ### 控制台信息显示函数 ###
    参数：
        无
    返回：
        True: 成功
        False: 失败
    ################
    """
    info = []
    try:
        print("#"*20)

        # 读取并打印 .env 文件内容
        env_path = find_dotenv()
        if env_path and os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                env_content = f.read()
                print(env_content)
                print(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))) 
        else:
            print(".env 文件未找到")
        print("#"*20)
        return True
    except:
        print("总览信息显示函数执行失败")
        return False

def OverviewScale_Change():
    """
    ### 总览比例修改函数 ###
    参数：
        无
    返回：
        True: 成功
        False: 失败
    ################
    """
    try:
        scale = tools.get_mouse_position_ratio()
        tools.write_to_env("总览区域比例", scale)
        print("总览区域比例写入完成")
        return True
    except:
        print("总览比例修改函数执行失败")
        return False

