from nt import write
from paddleocr import PaddleOCR

import numpy as np
from typing import Union, List
import os
import threading

# 加载环境变量
from dotenv import load_dotenv, find_dotenv,dotenv_values, set_key
import os
load_dotenv(find_dotenv())
import time

from assets.data import IceOre_data
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

# 自动挖冰矿监控的停止事件
AUTO_ICE_MONITOR_STOP_EVENT = threading.Event()

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

def CompressedArea_Change():
    """
    ### 压缩交互区修改函数 ###
    参数：
        无
    返回：
        True: 成功
        False: 失败
    ################
    """
    try:
        scale = tools.get_mouse_position_ratio()
        tools.write_to_env("压缩交互区", scale)
        print("压缩交互区写入完成")
        return True
    except:
        print("压缩交互区修改函数执行失败")
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
        
        # 创建矿石价格字典（从 IceOre_data.data_isk）
        # 格式: {矿石名称: 价格}
        ore_price_dict = {}
        for ore_item in IceOre_data.data_isk:
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
        
        # 从 IceOre_data.data_isk 中提取所有矿石名称（除了表头）
        ore_names = []
        for ore_item in IceOre_data.data_isk:
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

def AutomaticIce_Mining():
    """
    ### 自动冰矿挖掘函数 ###
    自动锁定冰矿矿石，并进行挖掘
    返回：
    True: 成功
    False: 失败
    ################
    """
    IceLock()
    time.sleep(2)
    if IceOreLocked_State():
        print("矿石已锁定")
        第一采集器位置 = eval(os.getenv('第一采集器位置'))
        第二采集器位置 = eval(os.getenv('第二采集器位置'))
        time.sleep(0.2)
        tools.random_click_in_circle(center = 第一采集器位置)
        time.sleep(0.2)
        tools.random_click_in_circle(center = 第二采集器位置)
        return True
    else:
        print("矿石未锁定")
        print("再次尝试锁定矿石")
        IceLock()
        if IceOreLocked_State():
            print("矿石已锁定")
            第一采集器位置 = eval(os.getenv('第一采集器位置'))
            第二采集器位置 = eval(os.getenv('第二采集器位置'))
            time.sleep(0.2)
            tools.random_click_in_circle(center = 第一采集器位置)
            time.sleep(0.2)
            tools.random_click_in_circle(center = 第二采集器位置)
            return True
        else:
            print("矿石锁定失败，可能不在采集器范围内")
            print("请尝试人工介入")
            return False

def WarehouseSpace_Monitor():
    """
    ### 矿仓剩余空间监控函数 ###
    监控矿仓的剩余空间，若检测到仓库已满或是剩余空间<20%，则返回True，反之则False
    返回：
    True: 仓库已满或剩余空间 < 20%
    False: 剩余空间 >= 20%
    ################
    """
    try:
        # 从环境变量读取监控区域
        矿仓剩余空间监控区 = eval(os.getenv('矿仓剩余空间监控区'))
        
        # 执行OCR识别
        main.Imageecognition(region=矿仓剩余空间监控区, verbose=False)
        
        # 查找 assets/tmp 目录中的 JSON 文件并处理
        tmp_path = "./assets/tmp"
        json_file = None
        if os.path.exists(tmp_path):
            for filename in os.listdir(tmp_path):
                if filename.endswith('.json'):
                    json_file = os.path.join(tmp_path, filename)
                    break
        
        if not json_file:
            if 调试模式 == 1:
                print("调试: 未找到JSON文件")
            return False
        
        # 解析矿仓剩余空间信息
        result = tools.parse_warehouse_space_json(json_file)
        
        if result is None:
            if 调试模式 == 1:
                print("调试: 无法解析矿仓剩余空间信息")
            return False
        
        used_space, total_space = result
        
        # 计算剩余空间和百分比
        remaining_space = total_space - used_space
        remaining_percentage = (remaining_space / total_space * 100) if total_space > 0 else 0
        
        if 调试模式 == 1:
            print(f"调试: 已用空间: {used_space}m³, 总空间: {total_space}m³")
            print(f"调试: 剩余空间: {remaining_space}m³, 剩余百分比: {remaining_percentage:.2f}%")
        
        # 检查是否已满或剩余空间 < 20%
        is_full = (used_space >= total_space) or (remaining_percentage < 20.0)
        
        if is_full:
            print(f"警告: 矿仓已满或剩余空间不足 ({remaining_percentage:.2f}%)")
        else:
            print(f"矿仓剩余空间: {remaining_space:.1f}m³ ({remaining_percentage:.2f}%)")
        
        return is_full
        
    except Exception as e:
        if 调试模式 == 1:
            print(f"调试: WarehouseSpace_Monitor() 执行失败: {str(e)}")
        return False

def AutoIceMining_Monitor_Forone():
    """
    ### 自动挖冰矿以及监控函数 ###
    自动执行冰矿挖掘并监控矿仓状态（支持外部停止）
    返回：
    True: 成功或正常停止
    False: 失败或需要人工介入
    ################
    """
    # 每次调用前清除停止标志
    AUTO_ICE_MONITOR_STOP_EVENT.clear()
    try:
        # 步骤1: 检查是否已经锁定到冰矿
        if IceOreLocked_State():
            # 已锁定，进入步骤2
            print("检测到已锁定冰矿，检查挖掘状态...")
            # 步骤2: 检查采集器是否正在挖掘
            if IceMining_Status():
                # 正在挖掘，直接进入步骤4
                print("采集器正在挖掘，开始监控矿仓状态...")
            else:
                # 未在挖掘，执行自动挖掘
                print("采集器未在挖掘，执行自动挖掘...")
                if not tools.CollectorClick():
                    print("矿石锁定失败或不在挖掘范围，请人工调整")
                    return False
        else:
            # 未锁定，直接跳到步骤3
            print("未检测到已锁定冰矿，执行自动挖掘...")
            # 步骤3: 执行自动挖掘
            if not AutomaticIce_Mining():
                print("矿石锁定失败或不在挖掘范围，请人工调整")
                return False
        
        # 步骤4: 每5秒监控一次矿仓状态
        print("开始监控矿仓状态...")
        while not AUTO_ICE_MONITOR_STOP_EVENT.is_set():
            if WarehouseSpace_Monitor():
                # 矿仓已满，执行压缩操作
                print("检测到矿仓已满，执行压缩操作...")
                if not tools.Compress_Interaction():
                    print("矿石压缩失败，请人工介入")
                    return False
                
                # 等待压缩操作完成，给系统一些时间更新状态
                time.sleep(2)
                
                # 再次检测矿仓空间
                print("压缩后重新检测矿仓空间...")
                if WarehouseSpace_Monitor():
                    # 压缩后依旧满，说明压缩操作虽然执行了但没有成功释放空间
                    print("矿仓矿石压缩失败，请人工介入")
                    return False
                else:
                    # 压缩成功，空间已释放，继续监控
                    print("压缩成功，矿仓空间已释放，继续监控...")
            else:
                # WarehouseSpace_Monitor() 内部已经打印了矿仓剩余空间
                pass

            # 循环间隔，如果收到停止信号则提前结束
            for _ in range(5):
                if AUTO_ICE_MONITOR_STOP_EVENT.is_set():
                    break
                time.sleep(1)

        print("收到停止指令，自动挖冰矿监控结束")
        return True
            
    except KeyboardInterrupt:
        print("监控已中断")
        return False
    except Exception as e:
        if 调试模式 == 1:
            print(f"调试: AutoIceMining_Monitor() 执行失败: {str(e)}")
        print("自动挖冰矿监控函数执行失败")
        return False

def AutoIceMining_Monitor_Forone_WithThrow():
    """
    ### 自动挖冰矿以及监控函数（带抛出功能） ###
    自动执行冰矿挖掘并监控矿仓状态（支持外部停止）
    与 AutoIceMining_Monitor_Forone() 的区别：
    当出现矿石仓满后，执行完压缩操作之后额外执行一步 tools.Throw_Ore_To_Fleet_Hangar()
    返回：
    True: 成功或正常停止
    False: 失败或需要人工介入
    ################
    """
    # 每次调用前清除停止标志
    AUTO_ICE_MONITOR_STOP_EVENT.clear()
    try:
        # 步骤1: 检查是否已经锁定到冰矿
        if IceOreLocked_State():
            # 已锁定，进入步骤2
            print("检测到已锁定冰矿，检查挖掘状态...")
            # 步骤2: 检查采集器是否正在挖掘
            if IceMining_Status():
                # 正在挖掘，直接进入步骤4
                print("采集器正在挖掘，开始监控矿仓状态...")
            else:
                # 未在挖掘，执行自动挖掘
                print("采集器未在挖掘，执行自动挖掘...")
                if not tools.CollectorClick():
                    print("矿石锁定失败或不在挖掘范围，请人工调整")
                    return False
        else:
            # 未锁定，直接跳到步骤3
            print("未检测到已锁定冰矿，执行自动挖掘...")
            # 步骤3: 执行自动挖掘
            if not AutomaticIce_Mining():
                print("矿石锁定失败或不在挖掘范围，请人工调整")
                return False
        
        # 步骤4: 每5秒监控一次矿仓状态
        print("开始监控矿仓状态...")
        while not AUTO_ICE_MONITOR_STOP_EVENT.is_set():
            if WarehouseSpace_Monitor():
                # 矿仓已满，执行压缩操作
                print("检测到矿仓已满，执行压缩操作...")
                tools.Compress_Interaction()  # 无论压缩是否成功都继续
                
                # 等待压缩操作完成，给系统一些时间更新状态
                time.sleep(2)
                
                # 立即执行抛出矿石至舰队机库（无论压缩是否成功）
                print("执行抛出矿石至舰队机库...")
                if not tools.Throw_Ore_To_Fleet_Hangar():
                    print("抛出矿石至舰队机库失败，请人工介入")
                    return False
                print("抛出矿石至舰队机库成功")
                
                # 等待抛出操作完成，给系统一些时间更新状态
                time.sleep(1)
                
                # 检测矿仓空间，如果依旧为满则提示
                print("抛出后重新检测矿仓空间...")
                if WarehouseSpace_Monitor():
                    print("矿石压缩抛出失败，请尝试人工介入")
                    return False
                else:
                    print("矿仓空间已释放，继续监控...")
            else:
                # WarehouseSpace_Monitor() 内部已经打印了矿仓剩余空间
                pass

            # 循环间隔，如果收到停止信号则提前结束
            for _ in range(5):
                if AUTO_ICE_MONITOR_STOP_EVENT.is_set():
                    break
                time.sleep(1)

        print("收到停止指令，自动挖冰矿监控结束")
        return True
            
    except KeyboardInterrupt:
        print("监控已中断")
        return False
    except Exception as e:
        if 调试模式 == 1:
            print(f"调试: AutoIceMining_Monitor_Forone_WithThrow() 执行失败: {str(e)}")
        print("自动挖冰矿监控函数执行失败")
        return False

def Stop_AutoIceMining_Monitor_Forone():
    """
    ### 停止自动挖冰矿监控 ###
    通过设置停止事件请求 AutoIceMining_Monitor_Forone() 结束循环
    """
    AUTO_ICE_MONITOR_STOP_EVENT.set()

def AutoIceMining_MultiWindow_Cycle():
    """
    ### 多窗口自动挖冰矿循环函数 ###
    自动在多个EVE窗口之间切换，对每个窗口执行挖冰矿监控操作
    
    流程：
    1. 初始化排除账号列表
    2. 对当前EVE页面进行AutoIceMining_Monitor_Forone_WithThrow()操作
       - 如果检测到矿仓未满则进行下一步
       - 如果检测到矿仓为满，则执行压缩和抛出并再次确认矿仓空间已释放，矿仓未满后进行下一步
    3. 自动切换目标游戏窗口（排除排除账号列表中的用户名，单次循环中不重复）
    4. 切换之后等待1s执行第二步
    
    返回：
    True: 成功
    False: 失败
    ################
    """
    try:
        # 1. 初始化排除账号列表（保留原始值，支持字符串和整数）
        排除账号_env = os.getenv('排除账号')
        排除账号_原始 = []  # 保留原始值（字符串）
        排除账号_整数 = []  # 保留整数值
        if 排除账号_env:
            try:
                排除账号 = eval(排除账号_env)
                # 确保排除账号是列表格式
                if not isinstance(排除账号, (list, tuple)):
                    排除账号 = [排除账号] if 排除账号 else []
                # 分别保存字符串和整数值
                for acc in 排除账号:
                    # 保存原始值（转换为字符串）
                    排除账号_原始.append(str(acc))
                    # 尝试转换为整数并保存
                    try:
                        排除账号_整数.append(int(acc))
                    except (ValueError, TypeError):
                        # 如果无法转换为整数，只保留字符串值
                        pass
            except Exception as e:
                print(f"警告: 解析排除账号环境变量时出错: {e}，使用空列表")
        
        if 调试模式 == 1:
            print(f"调试: 排除账号原始列表 = {排除账号_原始}")
            print(f"调试: 排除账号整数列表 = {排除账号_整数}")
        
        # 获取所有EVE窗口用户名
        all_usernames = window_status.get_eve_usernames()
        if not all_usernames:
            print("未找到任何EVE窗口")
            return False
        
        # 过滤掉排除账号列表中的用户名
        # 支持字符串匹配和整数匹配
        available_usernames = []
        for username in all_usernames:
            should_exclude = False
            
            # 方法1: 直接字符串匹配
            if username in 排除账号_原始:
                should_exclude = True
            else:
                # 方法2: 尝试将用户名转换为整数进行匹配
                try:
                    username_int = int(username)
                    if username_int in 排除账号_整数:
                        should_exclude = True
                except ValueError:
                    # 如果用户名不是数字，只检查字符串匹配（已在上面检查）
                    pass
            
            # 如果不在排除列表中，则添加到可用列表
            if not should_exclude:
                available_usernames.append(username)
        
        if not available_usernames:
            print("所有窗口都在排除账号列表中，没有可用的窗口")
            return False
        
        if 调试模式 == 1:
            print(f"调试: 可用用户名列表 = {available_usernames}")
        
        # 持续循环处理所有窗口（处理完所有窗口后重新开始）
        print("开始多窗口循环处理，按 Ctrl+C 可中断...")
        cycle_count = 0
        
        while True:
            cycle_count += 1
            print(f"\n{'='*50}")
            print(f"开始第 {cycle_count} 轮循环")
            print(f"{'='*50}")
            
            # 初始化：将所有窗口最小化到任务栏
            print("初始化：将所有EVE窗口最小化到任务栏...")
            window_status.minimize_all_eve_windows()
            time.sleep(0.5)  # 等待最小化完成
            
            # 每轮循环开始时重新获取窗口列表，确保使用最新的窗口信息
            all_usernames = window_status.get_eve_usernames()
            if not all_usernames:
                print("未找到任何EVE窗口，等待 5 秒后重试...")
                time.sleep(5)
                continue
            
            # 重新过滤掉排除账号列表中的用户名
            available_usernames = []
            for username in all_usernames:
                should_exclude = False
                
                # 方法1: 直接字符串匹配
                if username in 排除账号_原始:
                    should_exclude = True
                else:
                    # 方法2: 尝试将用户名转换为整数进行匹配
                    try:
                        username_int = int(username)
                        if username_int in 排除账号_整数:
                            should_exclude = True
                    except ValueError:
                        # 如果用户名不是数字，只检查字符串匹配（已在上面检查）
                        pass
                
                # 如果不在排除列表中，则添加到可用列表
                if not should_exclude:
                    available_usernames.append(username)
            
            if not available_usernames:
                print("所有窗口都在排除账号列表中，等待 5 秒后重试...")
                time.sleep(5)
                continue
            
            if 调试模式 == 1:
                print(f"调试: 当前可用用户名列表 = {available_usernames}")
            
            # 记录已切换的窗口，确保单次循环中不重复
            已切换窗口 = []
            
            # 循环处理每个窗口
            while len(已切换窗口) < len(available_usernames):
                # 选择下一个未处理的窗口
                for username in available_usernames:
                    if username not in 已切换窗口:
                        current_username = username
                        break
                else:
                    # 所有窗口都已处理，跳出内层循环，重新开始新一轮
                    break
                
                print(f"\n切换到窗口: {current_username}")
                
                # 切换到目标窗口
                hwnd = window_status.get_eve_hwnd_by_username(current_username)
                if hwnd is None:
                    print(f"无法找到窗口 {current_username} 的句柄，跳过")
                    已切换窗口.append(current_username)
                    continue
                
                if not window_status.bring_window_to_front(hwnd):
                    print(f"无法前置窗口 {current_username}，跳过")
                    已切换窗口.append(current_username)
                    continue
                
                # 等待窗口切换完成
                time.sleep(1)
                
                # 2. 检查矿仓状态并执行相应操作
                print(f"检查窗口 {current_username} 的矿仓状态...")
                
                # 先检查矿仓是否满
                if WarehouseSpace_Monitor():
                    # 矿仓已满，执行压缩和抛出
                    print("检测到矿仓已满，执行压缩操作...")
                    if not tools.Compress_Interaction():
                        print("压缩操作失败，跳过此窗口")
                        已切换窗口.append(current_username)
                        continue
                    
                    # 等待压缩操作完成
                    time.sleep(2)
                    
                    # 执行抛出矿石至舰队机库
                    print("执行抛出矿石至舰队机库...")
                    if not tools.Throw_Ore_To_Fleet_Hangar():
                        print("抛出操作失败，跳过此窗口")
                        已切换窗口.append(current_username)
                        continue
                    
                    # 等待抛出操作完成
                    time.sleep(1)
                    
                    # 再次确认矿仓空间已释放
                    print("确认矿仓空间是否已释放...")
                    if WarehouseSpace_Monitor():
                        print("矿仓空间仍未释放，跳过此窗口")
                        已切换窗口.append(current_username)
                        continue
                    else:
                        print("矿仓空间已释放，继续执行监控...")
                else:
                    print("矿仓未满，直接执行监控...")
                
                # 执行AutoIceMining_Monitor_Forone_WithThrow()操作
                # 注意：这个函数内部有循环监控，但我们可以通过停止事件来控制
                print(f"开始对窗口 {current_username} 执行自动挖冰矿监控...")
                
                # 由于AutoIceMining_Monitor_Forone_WithThrow()是一个长时间运行的监控函数，
                # 我们需要在切换到下一个窗口前停止它
                # 但根据需求，这里应该是执行一次检查和处理，然后切换到下一个窗口
                # 所以我们可以只执行一次检查，而不是运行完整的监控循环
                
                # 执行一次自动挖冰矿操作（如果未锁定则锁定并开始挖掘）
                if IceOreLocked_State():
                    # 已锁定，检查挖掘状态
                    if IceMining_Status():
                        print("采集器正在挖掘")
                    else:
                        print("采集器未在挖掘，执行自动挖掘...")
                        if not tools.CollectorClick():
                            print("自动挖掘失败，跳过此窗口")
                            已切换窗口.append(current_username)
                            continue
                else:
                    # 未锁定，执行自动挖掘
                    print("未检测到已锁定冰矿，执行自动挖掘...")
                    if not AutomaticIce_Mining():
                        print("自动挖掘失败，跳过此窗口")
                        已切换窗口.append(current_username)
                        continue
                
                # 标记当前窗口已处理
                已切换窗口.append(current_username)
                print(f"窗口 {current_username} 处理完成")
                
                # 等待一段时间再切换到下一个窗口
                time.sleep(1)
            
            # 所有窗口处理完成，等待一段时间后重新开始下一轮循环
            print(f"\n第 {cycle_count} 轮循环完成，所有窗口已处理")
            print("等待 5 秒后开始下一轮循环...")
            time.sleep(5)
        
    except KeyboardInterrupt:
        print("多窗口循环已中断")
        return False
    except Exception as e:
        if 调试模式 == 1:
            print(f"调试: AutoIceMining_MultiWindow_Cycle() 执行失败: {str(e)}")
        print(f"多窗口自动挖冰矿循环函数执行失败: {str(e)}")
        return False

