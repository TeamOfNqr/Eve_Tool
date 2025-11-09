from time import sleep
import os
from dotenv import load_dotenv, find_dotenv,dotenv_values, set_key
import re

# 导入自定义函数
import mouse_keyboard
import screen_information_judgment
import window_status


def Show_VerviewArea():
    '''
    显示总览区域
    '''
    overview_area = eval(os.getenv('overview_area'))  # 转换为元组
    screen_information_judgment.highlight_region_on_screen(rect = overview_area, duration=2000)


