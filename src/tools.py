import tkinter as tk
from typing import Union, List, Tuple, Optional
import os
from pathlib import Path

# 加载环境变量
from dotenv import load_dotenv, find_dotenv,dotenv_values, set_key
import os
load_dotenv(find_dotenv())

# 从环境变量获取总览区域
overview_area = eval(os.getenv('总览区域'))

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


# highlight_region(overview_area, duration=3000)
