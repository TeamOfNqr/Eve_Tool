from time import sleep
import os
from dotenv import load_dotenv, find_dotenv,dotenv_values, set_key
import re

# 导入自定义函数
import mouse_keyboard
import screen_information_judgment
import window_status


# 加载环境变量
load_dotenv(find_dotenv())

# 从环境变量获取总览区域
overview_area = eval(os.getenv('overview_area'))
list_of_text_confidence = eval(os.getenv('list_of_text_confidence'))
my_screen_resolution = eval(os.getenv('my_screen_resolution'))
game_scaling = eval(os.getenv('game_scaling'))

def Goto_OrdinaryMineralBelt():
    '''
    前往小行星矿带
    1. 找到目标小行星带，右键列表
    2.  前往目标小行星带，左键跃迁
    '''
    mouse_keyboard.click_on_text_in_region(
        target_text="小行星带",
        region=overview_area,
        click_button=1,
        offset_range=3
    )
    sleep(1)

    if my_screen_resolution == (3840,2160) and game_scaling == 100:
        bbox = screen_information_judgment.locate_template_on_screen(
            r'assets\screenshot_comparison_4K_100\information_bar\leap_indicator.png',
            threshold=float(os.getenv('is_state_active_threshold', 0.8))
            )
        mouse_keyboard.click_random_point_in_ellipse(bbox, click_button=0, debug=True)
    else:
        bbox = screen_information_judgment.locate_template_on_screen(
            r'assets\screenshot_comparison_4K_100\information_bar\leap_indicator.png',
            threshold=float(os.getenv('is_state_active_threshold', 0.8))
            )
        mouse_keyboard.click_random_point_in_ellipse(bbox, click_button=0, debug=True)

def Docking_StarCity():
    '''
    停靠星城
    1. 找到目标星城，右键列表
    2.  前往目标星城，左键跃迁
    '''
    mouse_keyboard.click_on_text_in_region(
        target_text="星城",
        region=overview_area,
        click_button=1,
        offset_range=3
    )
    sleep(1)
    if my_screen_resolution == (3840,2160) and game_scaling == 100:
        bbox = screen_information_judgment.locate_template_on_screen(
            r'assets\screenshot_comparison_4K_100\information_bar\StarCity.png',
            threshold=float(os.getenv('is_state_active_threshold', 0.8))
            )
        mouse_keyboard.click_random_point_in_ellipse(bbox, click_button=0, debug=True)
    else:
        bbox = screen_information_judgment.locate_template_on_screen(
            r'assets\screenshot_comparison_4K_100\information_bar\StarCity.png',
            threshold=float(os.getenv('is_state_active_threshold', 0.8))
            )
        mouse_keyboard.click_random_point_in_ellipse(bbox, click_button=0, debug=True)


def OverviewArea_Modified():
    '''
    总览区域修改
    通过交互式方式重新定位总览区域，并更新项目根目录下的 .env 文件中的 overview_area。
    若 .env 文件不存在，则提示“未找到”并退出。
    '''
    # 获取当前脚本所在的绝对路径 (complex_events.py)
    current_file_path = os.path.abspath(__file__)
    
    # 获取当前脚本所在目录 (src/)
    current_dir = os.path.dirname(current_file_path)
    
    # 假设项目根目录是当前目录的上一级 (即 src 的父目录)
    project_root = os.path.dirname(current_dir)
    
    # 构造 .env 文件在项目根目录下的完整路径
    env_path = os.path.join(project_root, ".env")

    # 检查 .env 文件是否存在
    if not os.path.isfile(env_path):
        print("❌ 未找到 .env 文件")
        return

    try:
        # 获取新的区域参数（应为 tuple）
        new_region = window_status.list_positioning()
        print(f"✅ 已获取新区域参数: {new_region}")

        # 验证返回值是否为 tuple 且包含4个元素
        if not isinstance(new_region, tuple) or len(new_region) != 4:
            print("❌ 获取的区域参数格式无效，应为四元组 (x, y, width, height)")
            return

        # 转为字符串（不加引号，避免读取时需二次解析）
        region_str = str(new_region)

        # 安全写入 .env 文件（不加引号）
        set_key(
            dotenv_path=env_path,
            key_to_set="overview_area",
            value_to_set=region_str,
            quote_mode="never"
        )

        print(f"✅ .env 文件已成功更新：overview_area = {region_str}")
        overview_area = eval(os.getenv('overview_area'))  # 转换为元组
        screen_information_judgment.highlight_region_on_screen(rect = overview_area, duration=2000)

    except AttributeError:
        print("❌ 错误：window_status 或 list_positioning() 未定义，请检查依赖。")
    except Exception as e:
        print(f"❌ 更新 .env 文件时发生错误: {e}")


def update_env_from_mouse(name):
    """
    使用当前鼠标位置更新 .env 文件中指定参数的值。
    
    参数:
        name (str): .env 文件中要更新的键名（如 "cursor_pos"）
    """
    # 获取当前脚本所在目录和项目根目录
    current_file_path = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file_path)
    project_root = os.path.dirname(current_dir)
    env_path = os.path.join(project_root, ".env")

    # 检查 .env 文件是否存在
    if not os.path.isfile(env_path):
        print("❌ 未找到 .env 文件")
        return

    # 读取 .env 中所有键，检查 name 是否存在
    env_vars = dotenv_values(env_path)
    if name not in env_vars:
        print(f"❌ .env 文件中不存在参数: {name}")
        return

    # 获取鼠标位置（假设返回 [x, y]）
    try:
        pos = mouse_keyboard.get_mouse_position()
        if not (isinstance(pos, (list, tuple)) and len(pos) == 2):
            print("❌ 鼠标位置格式无效")
            return
        x, y = pos
    except Exception as e:
        print(f"❌ 获取鼠标位置失败: {e}")
        return

    # 构造元组字符串，不加引号（如 (123, 456)）
    pos_str = f"({int(x)}, {int(y)})"

    # 更新 .env 文件
    try:
        set_key(
            dotenv_path=env_path,
            key_to_set=name,
            value_to_set=pos_str,
            quote_mode="never"
        )
        print(f"✅ 已更新 {name} = {pos_str}")
    except Exception as e:
        print(f"❌ 写入 .env 文件失败: {e}")