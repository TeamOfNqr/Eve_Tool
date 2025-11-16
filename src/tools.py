import tkinter as tk
from typing import Union, List, Tuple, Optional
import os
from pathlib import Path
import pyautogui
import time
import re
import random
import math
import tkinter as tk

# 加载环境变量
from dotenv import load_dotenv, find_dotenv,dotenv_values, set_key
import os
load_dotenv(find_dotenv())

from src import ore_data
from src import main
from src import window_status
# import main
# import ore_data
# import window_status

# 从环境变量获取总览区域
总览区域比例 = eval(os.getenv('总览区域比例'))

def highlight_region(
    coordinates: Union[List[List[int]], List[int]], 
    duration: int = 5000,
    border_width: int = 3,
    border_color: str = "red"
):
    """
    ### 在屏幕上高亮显示指定区域 ###
    参数：
    coordinates: 坐标格式
        - 多边形格式: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]] (4个点)
        - 矩形格式: [x_min, y_min, x_max, y_max] (4个数值)
    duration: 显示持续时间（毫秒），0表示永久显示直到关闭窗口
    border_width: 边框宽度（像素）
    border_color: 边框颜色
    返回：
    None
    ##############################
    """
    # 判断坐标格式并转换为矩形格式
    if isinstance(coordinates[0], list):
        # 多边形格式: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
        if len(coordinates) != 4:
            raise ValueError("多边形格式需要4个点")
        x_coords = [point[0] for point in coordinates]
        y_coords = [point[1] for point in coordinates]
        x_min = min(x_coords)
        y_min = min(y_coords)
        x_max = max(x_coords)
        y_max = max(y_coords)
    else:
        # 矩形格式: [x_min, y_min, x_max, y_max]
        if len(coordinates) != 4:
            raise ValueError("矩形格式需要4个数值")
        x_min, y_min, x_max, y_max = coordinates
    
    # 计算窗口尺寸和位置
    width = x_max - x_min
    height = y_max - y_min
    
    # 创建透明窗口
    root = tk.Tk()
    root.overrideredirect(True)  # 移除窗口边框
    root.attributes('-topmost', True)  # 置顶
    
    # 设置窗口位置和大小
    window_width = width + border_width * 2
    window_height = height + border_width * 2
    root.geometry(f"{window_width}x{window_height}+{x_min - border_width}+{y_min - border_width}")
    
    # 创建画布，使用特殊颜色作为透明色
    canvas = tk.Canvas(
        root, 
        width=window_width, 
        height=window_height,
        highlightthickness=0,
        bg='#000001'  # 使用特殊颜色作为透明色
    )
    canvas.pack()
    
    # 设置窗口透明（Windows特有）
    try:
        root.attributes('-transparentcolor', '#000001')
    except:
        # 如果不支持透明色，使用半透明
        root.attributes('-alpha', 0.5)
        canvas.config(bg='black')
    
    # 绘制红色边框矩形（只绘制边框，不填充）
    canvas.create_rectangle(
        border_width,
        border_width,
        width + border_width,
        height + border_width,
        outline=border_color,
        width=border_width,
        fill=''  # 不填充
    )
    
    # 添加键盘事件：按ESC键关闭窗口
    def close_window(event=None):
        root.destroy()
    
    root.bind('<Escape>', close_window)
    root.focus_set()  # 设置焦点以接收键盘事件
    
    # 如果设置了持续时间，自动关闭窗口
    if duration > 0:
        root.after(duration, root.destroy)
    
    # 运行窗口
    root.mainloop()

def get_region_by_clicks(
    prompt_text: str = "请点击两次鼠标选择区域\n第一次点击：左上角\n第二次点击：右下角\n按ESC取消"
) -> Optional[List[int]]:
    """
    ### 通过两次鼠标点击获取矩形区域坐标 ###
    参数：
    prompt_text: 提示文本
    返回：
    [x_min, y_min, x_max, y_max] 或 None（如果取消）
    ##############################
    """
    clicks = []
    result = None
    preview_rect = None
    
    def on_click(event):
        nonlocal clicks, result, preview_rect
        clicks.append((event.x_root, event.y_root))
        
        if len(clicks) == 1:
            # 第一次点击，显示提示
            prompt_label.config(text=f"第一次点击: ({event.x_root}, {event.y_root})\n请点击第二次（右下角）")
        elif len(clicks) == 2:
            # 第二次点击，计算矩形坐标
            x1, y1 = clicks[0]
            x2, y2 = clicks[1]
            x_min = min(x1, x2)
            y_min = min(y1, y2)
            x_max = max(x1, x2)
            y_max = max(y1, y2)
            result = [x_min, y_min, x_max, y_max]
            
            # 清除之前的预览矩形
            if preview_rect:
                canvas.delete(preview_rect)
            
            # 绘制最终选择的矩形
            canvas.create_rectangle(
                x_min, y_min, x_max, y_max,
                outline='yellow',
                width=3,
                fill='',
                tags='final_rect'
            )
            
            prompt_label.config(text=f"区域已选择: {result}\n窗口将自动关闭")
            # 延迟关闭窗口，让用户看到结果
            root.after(1500, root.destroy)
    
    def on_motion(event):
        """鼠标移动时显示预览矩形"""
        nonlocal preview_rect
        if len(clicks) == 1:
            # 清除之前的预览矩形
            if preview_rect:
                canvas.delete(preview_rect)
            
            # 绘制预览矩形
            x1, y1 = clicks[0]
            x2, y2 = event.x_root, event.y_root
            x_min = min(x1, x2)
            y_min = min(y1, y2)
            x_max = max(x1, x2)
            y_max = max(y1, y2)
            
            preview_rect = canvas.create_rectangle(
                x_min, y_min, x_max, y_max,
                outline='cyan',
                width=2,
                fill='',
                dash=(5, 5),
                tags='preview_rect'
            )
    
    def on_escape(event):
        """按ESC取消"""
        nonlocal result
        result = None
        root.destroy()
    
    # 创建全屏透明窗口
    root = tk.Tk()
    
    # 获取屏幕尺寸（需要在设置窗口属性前获取）
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    # 设置窗口属性
    root.overrideredirect(True)  # 移除窗口边框
    root.attributes('-topmost', True)  # 置顶
    root.attributes('-alpha', 0.3)  # 半透明
    
    # 手动设置全屏大小（不能使用-fullscreen，因为overrideredirect已设置）
    root.geometry(f"{screen_width}x{screen_height}+0+0")
    
    # 创建画布覆盖整个屏幕
    canvas = tk.Canvas(
        root,
        width=screen_width,
        height=screen_height,
        highlightthickness=0,
        bg='black'
    )
    canvas.pack()
    
    # 绑定鼠标事件
    canvas.bind('<Button-1>', on_click)
    canvas.bind('<Motion>', on_motion)
    root.bind('<Escape>', on_escape)
    root.focus_set()
    
    # 创建提示标签
    prompt_label = tk.Label(
        root,
        text=prompt_text,
        font=('Arial', 16, 'bold'),
        bg='black',
        fg='yellow',
        justify='left'
    )
    prompt_label.place(relx=0.5, rely=0.1, anchor='center')
    
    # 运行窗口
    root.mainloop()
    
    return result

def write_to_env(
    function_name: str,
    data: Union[str, int, float, bool, List, None],
    env_file_path: str = ".env"
):
    """
    ### 将数据写入.env文件中对应函数名的键 ###
    参数：
    function_name: 函数名（将转换为大写并添加下划线，如 "get_region" -> "GET_REGION"）
    data: 要写入的数据（字符串、数字、布尔值、列表或None）
        - 保持数据原格式，不做任何转换
    env_file_path: .env文件路径（默认为".env"）
    返回：
    None
    异常：
    ValueError: 如果.env文件中不存在对应的函数键，或参数无效
    IOError/OSError: 如果文件读写失败
    ##############################
    """
    # 参数验证
    if not function_name or not isinstance(function_name, str):
        raise ValueError("function_name 必须是非空字符串")
    
    if not env_file_path or not isinstance(env_file_path, str):
        raise ValueError("env_file_path 必须是非空字符串")
    
    # 处理数据格式：保持原格式，只做必要的字符串转换
    if data is None:
        data_str = ""
    elif isinstance(data, (list, tuple)):
        # 列表或元组保持列表格式
        data_str = str(list(data))  # [1, 2, 3]
    else:
        # 数字、字符串、布尔值等直接转换为字符串，保持原格式
        data_str = str(data)
    
    # 获取.env文件路径
    env_path = Path(env_file_path)
    
    # 读取现有的.env文件内容
    env_lines = []
    key_found = False
    matched_key = None
    
    try:
        if env_path.exists():
            # 检查文件是否为目录
            if env_path.is_dir():
                raise ValueError(f"路径 '{env_file_path}' 是一个目录，不是文件")
            
            # 读取文件内容
            with open(env_path, 'r', encoding='utf-8') as f:
                env_lines = f.readlines()
    except PermissionError:
        raise PermissionError(f"没有权限读取文件: {env_file_path}")
    except Exception as e:
        raise IOError(f"读取文件失败: {env_file_path}, 错误: {str(e)}")
    
    # 查找并更新对应的键
    updated_lines = []
    for line in env_lines:
        # 去除行尾换行符
        stripped_line = line.rstrip('\n\r')
        
        # 跳过空行和注释行
        if not stripped_line or stripped_line.strip().startswith('#'):
            updated_lines.append(line)
            continue
        
        # 解析键值对
        if '=' in stripped_line:
            key, _ = stripped_line.split('=', 1)
            key = key.strip()
            
            # 跳过空键
            if not key:
                updated_lines.append(line)
                continue
            
            # 检查是否匹配（大小写不敏感，支持点号替换为下划线）
            key_normalized = key.replace('.', '_').upper()
            function_normalized = function_name.replace('.', '_').upper()
            
            # 匹配：键名（忽略大小写和点号/下划线）与函数名匹配
            if key_normalized == function_normalized:
                # 找到匹配的键，更新值
                updated_lines.append(f"{key}={data_str}\n")
                key_found = True
                matched_key = key
            else:
                # 保持原行不变
                updated_lines.append(line)
        else:
            # 保持原行不变
            updated_lines.append(line)
    
    # 如果没有找到对应的键，抛出异常
    if not key_found:
        available_keys = []
        for line in env_lines:
            stripped_line = line.strip()
            if '=' in stripped_line and not stripped_line.startswith('#'):
                key = stripped_line.split('=', 1)[0].strip()
                if key:
                    available_keys.append(key)
        
        function_normalized = function_name.replace('.', '_').upper()
        error_msg = f"在.env文件中未找到函数 '{function_name}' 对应的键"
        if not env_path.exists():
            error_msg += f"\n文件不存在: {env_file_path}"
        else:
            error_msg += f"\n期望的键格式（忽略大小写和点号/下划线）: {function_normalized}"
            if available_keys:
                error_msg += f"\n.env文件中可用的键: {', '.join(available_keys)}"
            else:
                error_msg += "\n.env文件中没有任何键"
        
        raise ValueError(error_msg)
    
    # 写回.env文件
    temp_path = None
    try:
        # 确保目录存在（如果父目录不是根目录）
        if env_path.parent != env_path:
            try:
                env_path.parent.mkdir(parents=True, exist_ok=True)
            except (OSError, PermissionError) as e:
                raise PermissionError(f"无法创建目录: {env_path.parent}, 错误: {str(e)}")
        
        # 写入文件（使用临时文件确保原子性写入）
        temp_path = env_path.with_suffix(env_path.suffix + '.tmp')
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.writelines(updated_lines)
        
        # 原子性替换原文件
        if env_path.exists():
            env_path.unlink()
        temp_path.replace(env_path)
        
    except PermissionError as e:
        # 清理临时文件
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except:
                pass
        raise
    except Exception as e:
        # 清理临时文件
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except:
                pass
        raise IOError(f"写入文件失败: {env_file_path}, 错误: {str(e)}")

def get_mouse_position_ratio() -> List[float]:
    """
    ### 获取鼠标位置相对于屏幕的比例 ###
    返回：
    [x比例, y比例] - 鼠标位置相对于屏幕的比例（0.0到1.0之间）
    例如：如果鼠标在屏幕右侧1/3的上半边，返回[0.33, 0.5]
    ##############################
    """
    print("3S后将记录位置")
    time.sleep(3)

    # 获取鼠标当前位置
    mouse_x, mouse_y = pyautogui.position()
    
    # 获取屏幕尺寸
    screen_width, screen_height = pyautogui.size()
    
    # 计算比例
    x_ratio = mouse_x / screen_width
    y_ratio = mouse_y / screen_height
    
    # 返回比例列表，保留两位小数
    return [round(x_ratio, 2), round(y_ratio, 2)]

def get_mouse_position_after_delay() -> List[int]:
    """
    ### 3秒后记录鼠标位置并返回绝对坐标 ###
    返回：
    [x, y] - 鼠标位置的绝对坐标（像素）
    例如：如果鼠标在屏幕(1920, 1080)位置，返回[1920, 1080]
    ##############################
    """
    print("3秒后将记录鼠标位置")
    time.sleep(3)

    # 获取鼠标当前位置
    mouse_x, mouse_y = pyautogui.position()
    
    # 返回绝对坐标列表
    return [mouse_x, mouse_y]

def parse_ocr_table_json(json_path: Union[str, Path, dict]) -> List[List[str]]:
    """
    ### 从OCR结果JSON文件中提取表格数据 ###
    参数：
    json_path: JSON文件路径或已加载的字典对象
    返回：
    List[List[str]]: 表格数据，每行是一个子列表，格式为 [距离, 名字, 类型, 位置]
    例如：
    [
        ["18km", "小行星(白釉冰)", "白釉冰", "[39, 130, 89, 151]"],
        ["60m", "小行星(白釉冰)", "白釉冰", "[100, 131, 208, 152]"],
        ["2.7 AU", "阿尔卡利1-矿钻集团精炼", "加达里食品处", "[299, 130, 350, 152]"],
        ...
    ]
    注意：
    - 距离列：保持原始格式，不做任何转换
    - 位置列：使用rec_boxes的值，格式为"[x_min, y_min, x_max, y_max]"
    ##############################
    """
    import json
    
    # 加载JSON数据
    if isinstance(json_path, dict):
        data = json_path
    else:
        json_path = Path(json_path)
        if not json_path.exists():
            raise FileNotFoundError(f"JSON文件不存在: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    
    # 获取识别文本和边界框
    rec_texts = data.get('rec_texts', [])
    rec_boxes = data.get('rec_boxes', [])
    
    if not rec_texts or not rec_boxes:
        raise ValueError("JSON文件中缺少rec_texts或rec_boxes字段")
    
    if len(rec_texts) != len(rec_boxes):
        raise ValueError(f"rec_texts和rec_boxes长度不匹配: {len(rec_texts)} vs {len(rec_boxes)}")
    
    # 处理分离的单位：将独立的"km"、"m"、"AU"与前一个文本合并
    distance_units = ["km", "m", "AU"]
    indices_to_remove = []
    
    for i in range(1, len(rec_texts)):
        text = rec_texts[i].strip()
        # 检查是否是独立的单位（不区分大小写）
        if text.lower() in [unit.lower() for unit in distance_units]:
            # 与前一个文本合并
            prev_text = rec_texts[i - 1].strip()
            # 检查条件：
            # 1. 上一个文本不是表头
            # 2. 上一个文本不以该单位结尾（避免重复合并）
            prev_text_lower = prev_text.lower()
            text_lower = text.lower()
            if (prev_text not in ["距离", "名字", "类型", "速度"] and 
                not prev_text_lower.endswith(text_lower)):
                rec_texts[i - 1] = prev_text + text
                # 更新边界框：合并后的框应该覆盖两个文本的区域
                prev_box = rec_boxes[i - 1]
                curr_box = rec_boxes[i]
                # 使用合并后的最小和最大坐标
                merged_box = [
                    min(prev_box[0], curr_box[0]),  # x_min
                    min(prev_box[1], curr_box[1]),  # y_min
                    max(prev_box[2], curr_box[2]),  # x_max
                    max(prev_box[3], curr_box[3])   # y_max
                ]
                rec_boxes[i - 1] = merged_box
                # 标记当前索引需要删除
                indices_to_remove.append(i)
    
    # 从后向前删除已合并的单位项（避免索引错乱）
    for idx in reversed(indices_to_remove):
        rec_texts.pop(idx)
        rec_boxes.pop(idx)
    
    # 消除距离单位值中的空格（如 "18 km" -> "18km"）
    for i, text in enumerate(rec_texts):
        if text and text.strip():
            # 使用正则表达式匹配：数字 + 空格 + 单位，替换为数字 + 单位
            # 匹配模式：数字（可能包含小数点和负号）+ 空格 + 单位（km/m/AU，不区分大小写）
            text_cleaned = re.sub(r'(\d+(?:\.\d+)?)\s+([kmau]+)', r'\1\2', text, flags=re.IGNORECASE)
            if text_cleaned != text:
                rec_texts[i] = text_cleaned
    
    # 先找到表头行的索引，用于排除表头中的距离单位
    header_texts = ["距离", "名字", "类型", "速度"]
    header_indices_for_distance = set()  # 表头的索引集合（用于排除）
    
    for i, text in enumerate(rec_texts):
        if text in header_texts:
            header_indices_for_distance.add(i)
    
    # 找到第一个包含距离单位的文本索引（km、m、au，不区分大小写）
    # 这将是数据行的起始点
    first_distance_index = None
    first_data_start_index = None  # 实际的数据起始索引
    distance_units = ['km', 'm', 'au']  # 支持的距离单位
    
    for i, text in enumerate(rec_texts):
        # 跳过表头行
        if i in header_indices_for_distance:
            continue
            
        if text and isinstance(text, str):
            text_lower = text.lower().strip()
            # 检查是否包含任何距离单位关键词
            # 同时确保不是表头中的单位（如"速度（m"中的"m"）
            for unit in distance_units:
                if unit in text_lower:
                    # 进一步检查：如果文本包含表头关键词，则跳过
                    is_header = any(header in text for header in header_texts)
                    if not is_header:
                        first_distance_index = i
                        # 如果文本就是单位本身（独立的单位，可能是因为识别问题导致的），从前一个文本开始
                        if text_lower == unit and i > 0:
                            # 从前一个文本开始（因为值和单位被分开了）
                            first_data_start_index = i - 1
                        else:
                            # 从当前包含单位的文本开始（例如"18km"、"7,371m"）
                            first_data_start_index = i
                        break
            if first_distance_index is not None:
                break
    
    if first_distance_index is None or first_data_start_index is None:
        raise ValueError("未找到包含距离单位的文本（km/m/au），无法确定数据行的起始位置")
    
    # 获取第一个距离文本的Y坐标，用于确定数据行的起始Y坐标
    # 使用实际数据起始索引的Y坐标
    first_data_box = rec_boxes[first_data_start_index]
    first_data_y_min = first_data_box[1]  # y_min
    first_data_y_max = first_data_box[3]  # y_max
    first_data_y_center = (first_data_y_min + first_data_y_max) / 2
    
    # 同时也获取第一个距离单位文本的Y坐标，取两者的最小值作为数据行的起始Y坐标
    # 这样可以确保包含第一个距离单位的行被包含进来
    first_distance_box = rec_boxes[first_distance_index]
    first_distance_y_min = first_distance_box[1]
    first_distance_y_max = first_distance_box[3]
    first_distance_y_center = (first_distance_y_min + first_distance_y_max) / 2
    
    # 使用更小的Y坐标（更靠上的位置）作为起始点，确保第一个数据行被包含
    # 同时考虑Y坐标容差，确保同一行的文本都被包含
    first_data_y_center = min(first_data_y_center, first_distance_y_center)
    # 使用y_min作为起始Y坐标，这样更宽松
    first_data_y_start = min(first_data_y_min, first_distance_y_min)
    
    # 找到表头行的索引和X坐标范围（仍然需要表头来确定列的范围）
    # header_texts 已经在上面定义过了，这里直接使用
    header_info = {}  # {text: (index, x_min, x_max)}
    header_indices = header_indices_for_distance.copy()  # 使用之前找到的表头索引
    
    for i, text in enumerate(rec_texts):
        if text in header_texts:
            x_min, y_min, x_max, y_max = rec_boxes[i]
            header_info[text] = (i, x_min, x_max)
            header_indices.add(i)
    
    # 根据表头确定列的X坐标范围（如果找不到足够的表头，尝试使用默认列范围）
    column_ranges = []
    if len(header_info) >= 3:
        # 按X坐标排序表头
        sorted_headers = sorted(header_info.items(), key=lambda x: x[1][1])  # 按x_min排序
        
        # 定义列的X坐标范围（使用表头的位置作为参考，并添加一些容差）
        for i, (text, (idx, x_min, x_max)) in enumerate(sorted_headers):
            if i == 0:
                # 第一列：从0到下一个表头的中间，但扩展一些范围
                next_x = sorted_headers[i+1][1][1] if i+1 < len(sorted_headers) else x_max + 200
                column_ranges.append((0, next_x - 10))  # 减去10作为容差
            elif i == len(sorted_headers) - 1:
                # 最后一列：从前一列的结束到无穷大
                prev_end = column_ranges[-1][1]
                column_ranges.append((prev_end, float('inf')))
            else:
                # 中间列：从前一列的结束到下一个表头的开始
                prev_end = column_ranges[-1][1]
                next_x = sorted_headers[i+1][1][1]
                column_ranges.append((prev_end, next_x - 10))  # 减去10作为容差
    else:
        # 如果找不到足够的表头，使用更宽松的列范围
        # 基于第一个数据文本的X坐标来估算列范围
        first_data_x_min = first_data_box[0]
        first_data_x_max = first_data_box[2]
        # 估算列宽度（假设每列大约200像素）
        estimated_col_width = 200
        column_ranges = [
            (0, first_data_x_max + estimated_col_width // 2),
            (first_data_x_max + estimated_col_width // 2, first_data_x_max + estimated_col_width * 2),
            (first_data_x_max + estimated_col_width * 2, first_data_x_max + estimated_col_width * 3),
            (first_data_x_max + estimated_col_width * 3, float('inf'))
        ]
    
    # 定义Y坐标容差（同一行的文本Y坐标应该相近）
    y_tolerance = 15
    
    # 将文本按行分组，从第一个km文本开始处理
    rows = {}  # {y_center: [(index, text, x_min, x_center), ...]}
    
    # 辅助函数：判断文本是否是距离（包含单位）
    def is_distance(text):
        if not text or not isinstance(text, str):
            return False
        text_lower = text.lower()
        return any(unit in text_lower for unit in ['km', 'm', 'au'])
    
    for i, (text, box) in enumerate(zip(rec_texts, rec_boxes)):
        # 跳过空文本
        if not text or not text.strip():
            continue
        
        # 跳过表头行
        if i in header_indices:
            continue
        
        x_min, y_min, x_max, y_max = box
        y_center = (y_min + y_max) / 2
        x_center = (x_min + x_max) / 2
        
        # 关键修改：只处理从第一个距离单位文本所在行或之后的数据
        # 使用y_min进行比较，这样更宽松，确保第一个数据行被包含
        # 如果当前文本的Y坐标明显在第一个数据行之上（超过容差），则跳过
        if y_min < first_data_y_start - y_tolerance:
            continue
        
        # 过滤掉明显不是数据的文本（如单个字符、符号等）
        if text.strip() in ["口", "。", "S", "2", "×", "广", ".", ""]:
            continue
        
        # 找到最接近的Y坐标行（如果已存在相近的行）
        matched_y = None
        for existing_y in rows.keys():
            if abs(y_center - existing_y) < y_tolerance:
                matched_y = existing_y
                break
        
        if matched_y is None:
            matched_y = y_center
        
        if matched_y not in rows:
            rows[matched_y] = []
        
        rows[matched_y].append((i, text, x_min, x_center))
    
    # 按Y坐标排序行
    sorted_rows = sorted(rows.items(), key=lambda x: x[0])
    
    # 构建表格数据
    table_data = []
    
    for y_center, items in sorted_rows:
        # 在同一行内，按X坐标排序
        items.sort(key=lambda x: x[3])  # 按x_center排序
        
        # 根据列的X坐标范围分配数据
        row_data = ["-", "-", "-", "-"]  # [距离, 名字, 类型, 位置]
        distance_idx = None  # 保存距离文本的索引，用于获取rec_boxes
        
        for idx, text, x_min, x_center in items:
            # 首先尝试根据X坐标确定列
            assigned = False
            for col_idx, (col_start, col_end) in enumerate(column_ranges):
                if col_start <= x_center < col_end:
                    if col_idx < len(row_data):
                        # 如果该列已有数据，可能是多个文本，尝试合并或选择最合适的
                        if row_data[col_idx] == "-":
                            row_data[col_idx] = text
                            if col_idx == 0 and is_distance(text):
                                distance_idx = idx
                        else:
                            # 如果已有数据，根据列类型选择更合适的文本
                            if col_idx == 0:  # 距离列
                                # 优先选择包含单位的文本
                                if is_distance(text) and not is_distance(row_data[col_idx]):
                                    row_data[col_idx] = text
                                    distance_idx = idx
                                elif len(text) > len(row_data[col_idx]):
                                    row_data[col_idx] = text
                                    if is_distance(text):
                                        distance_idx = idx
                            else:
                                # 其他列选择更长的文本
                                if len(text) > len(row_data[col_idx]):
                                    row_data[col_idx] = text
                        assigned = True
                    break
            
            # 如果根据X坐标没有分配，但文本看起来像距离，尝试分配到距离列
            if not assigned and is_distance(text) and row_data[0] == "-":
                row_data[0] = text
                distance_idx = idx
        
        # 设置位置列（使用距离文本对应的rec_boxes，如果没有距离则使用名字文本的rec_boxes）
        position_box = None
        if distance_idx is not None:
            position_box = rec_boxes[distance_idx]
        elif len(items) > 0:
            # 如果没有距离，使用第一个文本的rec_boxes
            first_idx = items[0][0]
            position_box = rec_boxes[first_idx]
        
        if position_box:
            row_data[3] = str(position_box)  # 位置列使用rec_boxes的值
        
        # 过滤掉明显不是数据行的内容（如窗口标题、标签等）
        skip_keywords = ["总览", "选中", "常用", "刷怪", "会战", "后勤", "无人机", "货柜", "任务", "建筑", "挖矿", "副刷怪", "跃迁"]
        
        # 检查是否包含需要跳过的关键词
        should_skip = False
        for col in row_data:
            if col != "-" and any(keyword in col for keyword in skip_keywords):
                should_skip = True
                break
        
        # 只有当至少有一列有数据且不包含跳过关键词时才添加这一行
        if not should_skip and any(col != "-" for col in row_data):
            # 确保距离列有数据，或者至少名字和类型列有数据
            if row_data[0] != "-" or (row_data[1] != "-" and row_data[2] != "-"):
                table_data.append(row_data)
    
    return table_data

def random_click_in_inscribed_circle(
    coordinates: Union[List[List[int]], List[int]],
    random_range: int,
    button_type: int,
    position_ratio: Optional[List[float]] = None
) -> bool:
    """
    ### 在框内生成内接圆/椭圆，并在圆心周围随机点击（已补偿剪裁偏移） ###
    参数：
    coordinates: 坐标格式
        - 多边形格式: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]] (4个点)
        - 矩形格式: [x_min, y_min, x_max, y_max] (4个数值)
    random_range: 在圆心周围随机点击的像素范围（半径）
    button_type: 点击类型，0=左键，1=右键
    position_ratio: 剪裁比例 [x比例, y比例]，默认为None（从.env中的"总览区域比例"读取）
    返回：
    True: 成功
    False: 失败
    注意：
    此函数会补偿Imageecognition_right_third()函数中的剪裁偏移
    ##############################
    """
    try:
        # 获取屏幕尺寸
        screen_width, screen_height = pyautogui.size()
        
        # 计算剪裁偏移量（与Imageecognition_right_third()中的计算方式一致）
        x_ratio, y_ratio = position_ratio
        offset_x = int(screen_width * x_ratio)  # left偏移量
        offset_y = 0  # top偏移量（始终为0）
        
        # 判断坐标格式并转换为矩形格式
        if isinstance(coordinates[0], list):
            # 多边形格式: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
            if len(coordinates) != 4:
                raise ValueError("多边形格式需要4个点")
            x_coords = [point[0] for point in coordinates]
            y_coords = [point[1] for point in coordinates]
            x_min = min(x_coords)
            y_min = min(y_coords)
            x_max = max(x_coords)
            y_max = max(y_coords)
        else:
            # 矩形格式: [x_min, y_min, x_max, y_max]
            if len(coordinates) != 4:
                raise ValueError("矩形格式需要4个数值")
            x_min, y_min, x_max, y_max = coordinates
        
        # 补偿剪裁偏移量：将剪裁后图像的坐标转换为原图坐标
        x_min = x_min + offset_x
        y_min = y_min + offset_y
        x_max = x_max + offset_x
        y_max = y_max + offset_y
        
        # 计算矩形的宽度和高度
        width = x_max - x_min
        height = y_max - y_min
        
        if width <= 0 or height <= 0:
            raise ValueError("无效的矩形尺寸")
        
        # 计算内接椭圆/圆的中心和半轴长
        center_x = (x_min + x_max) / 2
        center_y = (y_min + y_max) / 2
        
        # 使用椭圆（内接于矩形）
        # 椭圆的半轴长
        a = width / 2  # 水平半轴
        b = height / 2  # 垂直半轴
        
        # 在圆心周围 random_range 像素范围内生成随机点
        # 使用极坐标生成随机点，确保在圆心周围的圆内，同时也在椭圆内
        max_attempts = 100  # 最大尝试次数
        click_x, click_y = None, None
        
        for _ in range(max_attempts):
            # 生成随机角度和距离（在圆心周围 random_range 像素范围内）
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, random_range)
            
            # 转换为直角坐标（相对于圆心）
            offset_x_local = distance * math.cos(angle)
            offset_y_local = distance * math.sin(angle)
            
            # 计算实际点击坐标
            candidate_x = center_x + offset_x_local
            candidate_y = center_y + offset_y_local
            
            # 检查点是否在椭圆内
            # 椭圆方程: ((x-cx)/a)^2 + ((y-cy)/b)^2 <= 1
            normalized_x = (candidate_x - center_x) / a
            normalized_y = (candidate_y - center_y) / b
            if normalized_x ** 2 + normalized_y ** 2 <= 1:
                click_x = int(candidate_x)
                click_y = int(candidate_y)
                break
        
        # 如果无法生成有效点，使用圆心
        if click_x is None or click_y is None:
            click_x = int(center_x)
            click_y = int(center_y)
        
        # 移动鼠标到目标位置
        pyautogui.moveTo(click_x, click_y)
        
        # 等待0.2秒
        time.sleep(0.2)
        
        # 执行点击
        if button_type == 0:
            # 左键
            pyautogui.click(click_x, click_y)
        elif button_type == 1:
            # 右键
            pyautogui.rightClick(click_x, click_y)
        else:
            raise ValueError("button_type 必须是 0（左键）或 1（右键）")
        
        return True
    except Exception as e:
        print(f"随机点击函数执行失败: {str(e)}")
        return False

def find_keyword_position(name: Optional[str] = None, refresh: bool = False, verbose: bool = True) -> Optional[List[int]]:
    """
    ### 从tmp目录下的JSON文件中查找关键字对应的位置信息 ###
    参数：
    name: 关键字（字符串），默认为None
    refresh: 是否在查找前刷新OCR识别结果，默认为False
    verbose: 是否打印OCR识别结果和错误信息，默认为True
    返回：
    List[int]: 位置信息（rec_boxes的值），格式为 [x_min, y_min, x_max, y_max]
    如果未找到关键字，返回None
    异常：
    FileNotFoundError: 如果tmp目录下没有找到JSON文件
    ValueError: 如果name参数为None或空字符串
    ##############################
    """
    import json
    
    # 如果需要刷新OCR识别结果
    if refresh:
        main.Imageecognition_right_third(总览区域比例, verbose=verbose)
    
    # 参数验证
    if not name or not isinstance(name, str) or not name.strip():
        raise ValueError("name参数必须是非空字符串")
    
    # 查找tmp目录下的JSON文件
    tmp_path = Path("assets/tmp")
    if not tmp_path.exists():
        raise FileNotFoundError(f"tmp目录不存在: {tmp_path}")
    
    # 查找所有JSON文件，按修改时间排序（最新的在前）
    json_files = sorted(
        tmp_path.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    if not json_files:
        raise FileNotFoundError(f"tmp目录下没有找到JSON文件: {tmp_path}")
    
    # 遍历所有JSON文件，找到第一个匹配的
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 获取识别文本和边界框
            rec_texts = data.get('rec_texts', [])
            rec_boxes = data.get('rec_boxes', [])
            
            if not rec_texts or not rec_boxes:
                continue
            
            if len(rec_texts) != len(rec_boxes):
                continue
            
            # 在rec_texts中搜索关键字（不区分大小写，支持部分匹配）
            name_lower = name.lower().strip()
            for i, text in enumerate(rec_texts):
                if text and isinstance(text, str):
                    text_lower = text.lower().strip()
                    # 检查是否包含关键字（支持部分匹配）
                    if name_lower in text_lower:
                        # 返回对应的rec_boxes值
                        if i < len(rec_boxes):
                            return rec_boxes[i]
            
        except Exception as e:
            # 如果读取某个JSON文件失败，继续尝试下一个
            if verbose:
                print(f"读取JSON文件失败: {json_file}, 错误: {str(e)}")
            continue
    
    # 如果没有找到匹配的关键字，返回None
    return None

def parse_distance_to_km(distance_str: str) -> float:
    """
    ### 将距离字符串转换为千米 ###
    参数：
    distance_str: 距离字符串，例如 "18km", "60m", "2.7 AU", "6,873 m"
    返回：
    float: 距离（千米）
    ##############################
    """
    if not distance_str or distance_str == "-":
        return float('inf')  # 无效距离返回无穷大
    
    # 移除空格并转换为小写
    distance_str = distance_str.strip().lower()
    
    # 先移除数字中的逗号（千位分隔符），例如 "6,873" -> "6873", "1,234,567" -> "1234567"
    # 使用全局替换，移除所有逗号（但保留小数点）
    distance_str_cleaned = re.sub(r'(\d),(\d)', r'\1\2', distance_str)
    # 如果还有逗号，继续移除（处理多个逗号的情况）
    while ',' in distance_str_cleaned:
        distance_str_cleaned = re.sub(r'(\d),(\d)', r'\1\2', distance_str_cleaned)
    
    # 匹配数字和单位（使用search而不是match，因为可能有前缀）
    # 支持：数字（可能包含小数点）+ 可选空格 + 单位
    match = re.search(r'([\d.]+)\s*([kmau]+)', distance_str_cleaned)
    if not match:
        return float('inf')
    
    try:
        value = float(match.group(1))
        unit = match.group(2).strip()
        
        # 根据单位转换
        if unit == 'km':
            return value
        elif unit == 'm':
            return value / 1000.0  # 米转千米
        elif unit == 'au':
            return value * 149597870.7  # AU转千米（1 AU ≈ 149,597,870.7 km）
        else:
            # 如果单位不明确，尝试判断
            if 'km' in unit:
                return value
            elif 'm' in unit and 'km' not in unit:
                return value / 1000.0
            elif 'au' in unit:
                return value * 149597870.7
            else:
                return float('inf')
    except (ValueError, AttributeError):
        return float('inf')

def area_screenshot(region = None):
    """
    区域截图函数
    接收参数格式为(x1, y1, width, height)
    """
    if region:
        screenshot = pyautogui.screenshot(region=region)
    else:
        screenshot = pyautogui.screenshot()
    return screenshot

def highlight_region_on_screen(rect, duration=2000):
    """
    在屏幕上创建一个透明窗口，并用红色边框高亮指定矩形区域。

    :param rect: (x, y, width, height) 的 tuple，由 locate_template_on_screen 返回
    :param duration: 高亮窗口显示的毫秒数（默认 2000ms = 2秒），设为 None 则需手动关闭
    """
    if rect is None:
        return

    x, y, w, h = rect

    # 创建全屏透明窗口
    root = tk.Tk()
    root.overrideredirect(True)           # 无边框
    root.attributes('-topmost', True)     # 置顶
    root.attributes('-transparentcolor', 'white')  # 将白色设为透明色
    root.config(bg='white')

    # 设置窗口尺寸为整个屏幕
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f"{screen_width}x{screen_height}+0+0")

    # 创建 Canvas 用于绘图
    canvas = tk.Canvas(root, width=screen_width, height=screen_height, bg='white', highlightthickness=0)
    canvas.pack()

    # 绘制红色边框矩形（注意：Canvas 坐标是 (x1, y1, x2, y2)）
    canvas.create_rectangle(x, y, x + w, y + h, outline='red', width=3)

    # 自动关闭窗口（可选）
    if duration is not None:
        root.after(duration, root.destroy)

    # 启动窗口（非阻塞主逻辑需在主线程调用）
    root.mainloop()

def random_click_in_circle(center, button=0, radius=3, delay_before_click=0.3):
    """
    在指定坐标为中心、给定半径的圆形范围内随机点击。
    
    参数:
        center (list or tuple): [x, y] 基准坐标
        button (int): 0 表示左键，1 表示右键
        radius (int): 随机偏移的像素半径（默认 5）
        delay_before_click (float): 鼠标移动到目标位置后、点击前的等待时间（秒），默认 0.7
    """
    if not isinstance(center, (list, tuple)) or len(center) != 2:
        raise ValueError("center 必须是包含两个元素的列表或元组，如 [x, y]")
    
    x, y = center

    # 在圆形区域内生成均匀分布的随机点（使用极坐标）
    r = radius * math.sqrt(random.random())
    theta = random.uniform(0, 2 * math.pi)
    
    offset_x = int(r * math.cos(theta))
    offset_y = int(r * math.sin(theta))
    
    click_x = x + offset_x
    click_y = y + offset_y

    # 移动鼠标到目标位置（pyautogui.click 会自动移动，但显式移动便于控制）
    pyautogui.moveTo(click_x, click_y)

    # 等待指定时间后再点击
    time.sleep(delay_before_click)

    # 执行点击
    pyautogui.click(
        x=click_x,
        y=click_y,
        button='left' if button == 0 else 'right',
        clicks=1,
        interval=0.0
    )


