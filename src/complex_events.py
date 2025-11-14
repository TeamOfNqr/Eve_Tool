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

import tools

# 从环境变量获取总览区域
总览区域 = eval(os.getenv('总览区域'))
总览区域比例 = eval(os.getenv('总览区域比例'))
矿头挖掘距离 = eval(os.getenv('矿头挖掘距离'))

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
        return True
    except:
        print("总览比例修改函数执行失败")
        return False

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
    info.append("总览区域："+str(总览区域比例))
    info.append("矿头挖掘距离："+str(矿头挖掘距离))
    try:
        print("#"*20)
        for i in info:
            print(i)
        print(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))) 
        print("#"*20)
        return True
    except:
        print("总览信息显示函数执行失败")
        return False
