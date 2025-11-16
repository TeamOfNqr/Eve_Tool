from nt import write
from paddleocr import PaddleOCR

import numpy as np
from typing import Union, List
import os

# 加载环境变量
from dotenv import load_dotenv, find_dotenv,dotenv_values, set_key
import os
load_dotenv(find_dotenv())
import time

from src import ore_data
from src import main
from src import tools
from src import window_status
# import main
# import tools
# import ore_data
# import window_status
import pyautogui

# 从环境变量获取总览区域
总览区域比例 = eval(os.getenv('总览区域比例'))
矿头挖掘距离 = int(eval(os.getenv('矿头挖掘距离')))
调试模式 = int(eval(os.getenv('调试模式')))
锁定状态监控区 = eval(os.getenv('锁定状态监控区'))

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

def IceLock():
    """
    ### 冰矿锁定函数 ###
    从OCR识别的表格数据中找到最贵的且距离小于矿头挖掘距离的矿石，
    然后点击矿石并锁定目标
    返回：
    True: 成功
    False: 失败
    ################
    """
    try:
        # 执行OCR识别（不显示详细输出）
        main.Imageecognition_right_third(总览区域比例, verbose=False)
        
        # 查找 assets/tmp 目录中的 JSON 文件并处理
        tmp_path = "./assets/tmp"
        json_file = None
        if os.path.exists(tmp_path):
            for filename in os.listdir(tmp_path):
                if filename.endswith('.json'):
                    json_file = os.path.join(tmp_path, filename)
                    break
        
        if not json_file:
            return False
        
        # 解析OCR表格数据
        table_data = tools.parse_ocr_table_json(json_file)
        if not table_data:
            return False
        
        # 调试：显示所有解析到的表格数据
        if 调试模式 == 1 :
            print(f"调试: 共解析到 {len(table_data)} 行数据")
            for i, row in enumerate(table_data[:10]):  # 只显示前10行
                print(f"调试: 第{i+1}行: 距离={row[0] if len(row) > 0 else 'N/A'}, 名字={row[1] if len(row) > 1 else 'N/A'}, 类型={row[2] if len(row) > 2 else 'N/A'}")
        
        # 创建矿石价格字典（从ore_data.IceMineral_Isk）
        # 格式: {矿石名称: 价格}
        ore_price_dict = {}
        for ore_item in ore_data.IceMineral_Isk:
            if len(ore_item) >= 5 and ore_item[0] != 'core-name':  # 跳过表头
                ore_name = ore_item[0]  # 矿石名称
                try:
                    ore_price = int(ore_item[4])  # 矿石价格（isk/m^3）
                    ore_price_dict[ore_name] = ore_price
                except (ValueError, IndexError):
                    continue
        
        # 从上往下遍历表格数据，找到所有符合条件的矿石
        valid_ores = []
        
        for i, row in enumerate(table_data):
            if len(row) < 4:
                continue
            
            distance_str = row[0]  # 距离列
            ore_type = row[2]      # 类型列（矿石名称）
            position_str = row[3]  # 位置列
            
            # 跳过无效数据
            if distance_str == "-" or ore_type == "-" or position_str == "-":
                continue
            
            # 解析距离
            distance_km = tools.parse_distance_to_km(distance_str)
            
            # 调试信息：显示所有距离解析结果
            if 调试模式 == 1 :
                print(f"调试: 距离字符串='{distance_str}', 解析后={distance_km}km, 矿头挖掘距离={矿头挖掘距离}km")
                
            
            # 检查矿石类型是否在价格字典中，支持多种匹配方式
            matched_ore_name = None
            matched_price = None
            
            # 1. 首先尝试完全匹配
            if ore_type in ore_price_dict:
                matched_ore_name = ore_type
                matched_price = ore_price_dict[ore_type]
                if 调试模式 == 1 :
                    print(f"调试: 完全匹配到矿石: {ore_type} -> {matched_ore_name}")
            else:
                # 2. 尝试提取括号内的内容（例如"小行星(白釉冰)" -> "白釉冰"）
                import re
                match = re.search(r'\(([^)]+)\)', ore_type)
                if match:
                    extracted_name = match.group(1)
                    if extracted_name in ore_price_dict:
                        matched_ore_name = extracted_name
                        matched_price = ore_price_dict[extracted_name]
                        if 调试模式 == 1 :
                            print(f"调试: 括号匹配到矿石: {ore_type} -> {matched_ore_name}")
                
                # 3. 如果还没有匹配，尝试部分匹配（例如"高密度白釉冰"包含"白釉冰"）
                # 优先匹配更长的名称（更精确的匹配）
                if matched_ore_name is None:
                    # 按名称长度排序，优先匹配更长的名称
                    sorted_ore_names = sorted(ore_price_dict.keys(), key=len, reverse=True)
                    for ore_name in sorted_ore_names:
                        # 检查矿石名称是否包含在类型中，或者类型是否包含矿石名称
                        if ore_name in ore_type or ore_type in ore_name:
                            matched_ore_name = ore_name
                            matched_price = ore_price_dict[ore_name]
                            print(f"调试: 部分匹配到矿石: {ore_type} -> {matched_ore_name}")
                            break
            
            # 如果没有匹配到任何矿石，跳过这一行
            if matched_ore_name is None or matched_price is None:
                if 调试模式 == 1 :
                    print(f"调试: 未匹配到矿石类型: {ore_type}，跳过")
                continue
            
            # 添加到有效矿石列表
            valid_ores.append({
                'row': row,
                'name': matched_ore_name,
                'price': matched_price,
                'distance': distance_str,
                'index': i
            })
        
        # 如果没有找到合适的矿石
        if not valid_ores:
            return False
        
        # 按价格从高到低排序，找到最贵的矿石
        valid_ores.sort(key=lambda x: x['price'], reverse=True)
        
        # 去重：只保留不同名称的矿石（保留价格最高的）
        unique_ores = {}
        for ore in valid_ores:
            ore_name = ore['name']
            if ore_name not in unique_ores or ore['price'] > unique_ores[ore_name]['price']:
                unique_ores[ore_name] = ore
        
        unique_ores_list = list(unique_ores.values())
        unique_ores_list.sort(key=lambda x: x['price'], reverse=True)
        
        # 显示找到的矿石
        print(f"找到 {len(unique_ores_list)} 个不同的矿石:")
        for idx, ore in enumerate(unique_ores_list, 1):
            print(f"  {idx}. {ore['name']}, 价格: {ore['price']}, 距离: {ore['distance']}")
        
        # 锁定所有找到的矿石
        locked_count = 0
        for idx, ore in enumerate(unique_ores_list, 1):
            print(f"\n开始锁定第 {idx} 个矿石: {ore['name']}")
            
            # 解析位置信息（字符串格式的列表转换为列表）
            position_str = ore['row'][3]
            try:
                # 将字符串 "[x_min, y_min, x_max, y_max]" 转换为列表
                import ast
                position = ast.literal_eval(position_str)
                if not isinstance(position, list) or len(position) != 4:
                    continue
            except Exception as e:
                continue
            
            # 点击矿石（右键，button_type=1）
            print(f"点击矿石位置: {position}")
            if not tools.random_click_in_inscribed_circle(
                position, 
                3, 
                1, 
                position_ratio=总览区域比例
            ):
                continue
            
            # 等待一小段时间，让菜单弹出
            time.sleep(0.5)
            
            # 锁定目标（左键，button_type=0）
            # 刷新OCR识别并查找"锁定目标"按钮（因为点击矿石后可能弹出菜单）
            lock_position = tools.find_keyword_position("锁定目标", refresh=True, verbose=False)
            if lock_position is None:
                continue
            
            print(f"点击锁定目标位置: {lock_position}")
            if not tools.random_click_in_inscribed_circle(
                lock_position,
                3,
                0,
                position_ratio=总览区域比例
            ):
                continue
            
            locked_count += 1
            print(f"成功锁定第 {idx} 个目标: {ore['name']}")
        
        if locked_count > 0:
            print(f"\n成功锁定所有 {locked_count} 个目标")
            return True
        else:
            return False
        
    except Exception as e:
        return False

def Write_MousePlace():
    print("3s后记录一号采集器位置")
    time.sleep(3)
    mouseplace = tools.get_mouse_position_after_delay()
    tools.write_to_env("一号采集器位置", mouseplace)
    print("3s后记录二号采集器位置")
    time.sleep(3)
    mouseplace = tools.get_mouse_position_after_delay()
    tools.write_to_env("二号采集器位置", mouseplace)

def list_positioning():
    """
    通过延时记录鼠标位置定位信息窗口的区域参数

    返回:
        tuple: 包含 (x1, y1, width, height) 的元组，用于定位窗口区域
    """
    print("请将鼠标移动到列表左上角，3秒后记录...")
    time.sleep(3)
    x1, y1 = pyautogui.position()
    print(f"左上角坐标: ({x1}, {y1})")

    print("请将鼠标移动到列表右下角，3秒后记录...")
    time.sleep(3)
    x2, y2 = pyautogui.position()
    print(f"右下角坐标: ({x2}, {y2})")

    width = x2 - x1
    height = y2 - y1

    positioning = (x1, y1, width, height)

    print(f"\n✅ 最终区域参数: region = ({x1}, {y1}, {width}, {height})")

    tools.highlight_region_on_screen(rect=(x1, y1, width, height))

    return positioning

def IceMining_Status():
    """
    锁定状态监控区状态判断函数
    返回：
    True: 采集器正在挖掘
    False: 采集器未在挖掘
    ################
    """
    # 使用 main.Screenshot() 获取已转换为 numpy 数组的截图
    area = main.Screenshot(region=锁定状态监控区)
    result = main.is_state_active(template_path="assets/image/IceMining.png", screenshot_=area)
    print(result)

    if result[0]:
        print("采集器正在挖掘")
        return True
    else:
        print("采集器未在挖掘")
        return False

def IceOreLocked_State():
    """
    ### 冰矿锁定状态检查函数 ###
    检查锁定状态监控区是否包含冰矿矿石
    返回：
    True: 包含冰矿矿石
    False: 不包含冰矿矿石或识别失败
    ################
    """
    try:
        # 执行OCR识别
        main.Imageecognition(region=锁定状态监控区, verbose=False)
        
        # 查找 assets/tmp 目录中的 JSON 文件并处理
        tmp_path = "./assets/tmp"
        json_file = None
        if os.path.exists(tmp_path):
            for filename in os.listdir(tmp_path):
                if filename.endswith('.json'):
                    json_file = os.path.join(tmp_path, filename)
                    break
        
        if not json_file:
            return False
        
        # 读取JSON文件
        import json
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 获取识别文本
        rec_texts = data.get('rec_texts', [])
        if not rec_texts:
            return False
        
        # 从 ore_data.IceMineral_Isk 中提取所有矿石名称（除了表头）
        ore_names = []
        for ore_item in ore_data.IceMineral_Isk:
            if len(ore_item) > 0 and ore_item[0] != 'core-name':  # 跳过表头
                ore_name = ore_item[0]  # 矿石名称
                ore_names.append(ore_name)
        
        # 检查 rec_texts 中是否包含任何矿石名称
        # 将所有文本合并为一个字符串进行检查
        all_text = ' '.join([str(text) for text in rec_texts if text])
        
        # 检查是否包含任何矿石名称
        for ore_name in ore_names:
            if ore_name in all_text:
                if 调试模式 == 1:
                    print(f"调试: 在锁定状态监控区找到矿石: {ore_name}")
                return True
        
        # 如果完全匹配没有找到，尝试部分匹配（参考 IceLock() 的匹配逻辑）
        for text in rec_texts:
            if not text or not isinstance(text, str):
                continue
            
            text_str = str(text).strip()
            
            # 1. 首先尝试完全匹配
            if text_str in ore_names:
                if 调试模式 == 1:
                    print(f"调试: 完全匹配到矿石: {text_str}")
                return True
            
            # 2. 尝试提取括号内的内容（例如"小行星(白釉冰)" -> "白釉冰"）
            import re
            match = re.search(r'\(([^)]+)\)', text_str)
            if match:
                extracted_name = match.group(1)
                if extracted_name in ore_names:
                    if 调试模式 == 1:
                        print(f"调试: 括号匹配到矿石: {text_str} -> {extracted_name}")
                    return True
            
            # 3. 尝试部分匹配（例如"高密度白釉冰"包含"白釉冰"）
            # 按名称长度排序，优先匹配更长的名称
            sorted_ore_names = sorted(ore_names, key=len, reverse=True)
            for ore_name in sorted_ore_names:
                # 检查矿石名称是否包含在文本中，或者文本是否包含矿石名称
                if ore_name in text_str or text_str in ore_name:
                    if 调试模式 == 1:
                        print(f"调试: 部分匹配到矿石: {text_str} -> {ore_name}")
                    return True
        
        if 调试模式 == 1:
            print("调试: 未在锁定状态监控区找到任何冰矿矿石")
        return False
        
    except Exception as e:
        if 调试模式 == 1:
            print(f"调试: IceOreLocked_State() 执行失败: {str(e)}")
        return False