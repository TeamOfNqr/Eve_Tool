from time import sleep
import os
from dotenv import load_dotenv, find_dotenv,dotenv_values, set_key
import re

# 导入自定义函数
import screen_information_judgment


def ShowArea(areaname = None):
    '''
    显示区域
    '''
    area = eval(os.getenv(areaname))  # 转换为元组
    screen_information_judgment.highlight_region_on_screen(rect = area, duration=2000)


ShowArea(areaname = "overview_area")