from time import sleep
import os
from dotenv import load_dotenv, find_dotenv,dotenv_values, set_key
import re

# 导入自定义函数
import mouse_keyboard
import screen_information_judgment
import window_status
import ore_data

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


def update_env_region(name: str):
    '''
    通用区域参数更新函数
    通过交互式方式获取屏幕区域参数，并更新项目根目录下 .env 文件中指定的键。
    
    参数:
        name (str): 要更新的 .env 键名，如 "overview_area"
    '''
    # 获取当前脚本所在目录 (假设此脚本位于 src/)
    current_file_path = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file_path)
    project_root = os.path.dirname(current_dir)  # 项目根目录为 src 的父目录
    env_path = os.path.join(project_root, ".env")

    # 检查 .env 文件是否存在
    if not os.path.isfile(env_path):
        print("❌ 未找到 .env 文件")
        return

    try:
        # 获取新的区域参数（应为四元组 tuple）
        new_region = window_status.list_positioning()
        print(f"✅ 已获取新区域参数: {new_region}")

        # 验证返回值是否为有效四元组
        if not isinstance(new_region, tuple) or len(new_region) != 4:
            print("❌ 获取的区域参数格式无效，应为四元组 (x, y, width, height)")
            return

        # 转为字符串形式（不加引号，便于后续 eval）
        region_str = str(new_region)

        # 安全写入 .env 文件，不加引号
        set_key(
            dotenv_path=env_path,
            key_to_set=name,
            value_to_set=region_str,
            quote_mode="never"
        )

        print(f"✅ .env 文件已成功更新：{name} = {region_str}")

        # 可选：可视化反馈（仅当模块可用且键为区域类参数时才合理）
        # 此处保留原逻辑，但需确保 name 对应的值是区域参数
        try:
            # 注意：此处需确保环境变量已重新加载，或直接使用 region_str
            # 为避免依赖 os.getenv（可能未刷新），直接使用 new_region
            screen_information_judgment.highlight_region_on_screen(rect=new_region, duration=2000)
        except Exception as vis_error:
            print(f"⚠️ 可视化高亮失败（不影响写入）: {vis_error}")

    except AttributeError as ae:
        print(f"❌ 依赖错误：{ae}。请确保 window_status 和 list_positioning() 已正确定义。")
    except Exception as e:
        print(f"❌ 更新 .env 文件时发生错误: {e}")


# update_env_region(name = "overview_area")

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

def Replace_MiningHead(Collector = "C",text = "None"):
    '''
    更换矿头
    1. 右键需要更换矿头
    2. 左键选择需要的矿头
    '''

    CollectorA = eval(os.getenv('CollectorA'))
    CollectorB = eval(os.getenv('CollectorB'))
    arm_area = eval(os.getenv('arm_area'))

    if my_screen_resolution == (3840,2160) and game_scaling == 100:
        if Collector == "A" and CollectorA is not None:
            mouse_keyboard.random_click_in_circle(CollectorA, button=1,radius = 2)
        elif Collector == "B":
            mouse_keyboard.random_click_in_circle(CollectorB, button=1,radius = 2)
        else:
            print("❌ 无效的矿头位置")
            return True
    else:
        print("❌ 不支持的屏幕分辨率或游戏缩放")
        return False


    if my_screen_resolution == (3840,2160) and game_scaling == 100:
        bbox = screen_information_judgment.locate_template_on_screen(
            r'assets\screenshot_comparison_4K_100\arm\ammunition\crystal\PolymerCrystal_B.png',
            threshold=0.8
            )
        mouse_keyboard.click_random_point_in_ellipse(bbox, click_button=0, debug=True)


    # mouse_keyboard.click_on_text_in_region(
    #     target_text=text,
    #     region=arm_area,
    #     click_button=0,
    #     offset_range=3
    # )

# update_env_from_mouse("CollectorB")
# Replace_MiningHead(Collector = "A",text = "聚合小行星采集晶体B型")

def LockedOre_Image(Ore_Name: str):
    '''
    锁定矿石图像
    1. 找到需要锁定的矿石图像
    2. 左键点击锁定
    '''
    # for ore in ore_data.IceMineral:
    #     if ore[0] == Ore_Name:
    #         # 获取对应的截图文件名
    #         image_filename = ore[1]
    #         # 拼装完整路径
    #         image_path = r'assets\screenshot_comparison_4K_100/information_bar/ora/ice/' + image_filename
    #         # 进行图像识别
    #         bbox = screen_information_judgment.locate_template_on_screen(
    #             image_path,
    #             threshold=0.8
    #         )
    #         # 点击识别到的位置
    #         mouse_keyboard.click_random_point_in_ellipse(bbox, click_button=1, debug=True)
    #         # 找到并处理后退出循环
    #         break

    mouse_keyboard.click_on_text_in_region(
        target_text = Ore_Name, 
        click_button=1,
        region=overview_area,
        confidence_threshold=0.3,
    )
    sleep(0.5)
    mouse_keyboard.click_on_text_in_region(
        target_text = "目标", 
        click_button=0,
        region=overview_area,
        confidence_threshold=0.3,
    )
    

LockedOre_Image(Ore_Name = "朴白釉冰")