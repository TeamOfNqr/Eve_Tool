import pygetwindow as gw
import pyautogui
import time

def get_eve_windows_info():
    """
    获取所有标题包含“星战前夜”的窗口名称、唯一ID、是否前台
    
    返回:
        List[List[str, int or None, bool]]: 每个元素为 [窗口标题, hWnd句柄, 是否激活]
    """
    windows_info = []
    try:
        # 获取所有包含“星战前夜”的窗口对象
        eve_windows = gw.getWindowsWithTitle('星战前夜：晨曦 [Serenity]')
        
        for win in eve_windows:
            title = win.title
            is_active = win.isActive
            
            # 尝试获取 hWnd（新版 pygetwindow 使用 _hWnd 作为内部属性）
            hwnd = getattr(win, '_hWnd', None)  # 安全获取，不存在则为 None
            
            windows_info.append([title, hwnd, is_active])
            
    except Exception as e:
        print(f"获取 EVE 窗口时出错: {e}")
    
    return windows_info

def get_eve_usernames():
    """
    自动获取所有“星战前夜：晨曦 [Serenity]”窗口的用户名。
    
    返回:
        List[str]: 用户名列表（按窗口顺序）
    """
    usernames = []
    try:
        eve_windows = gw.getWindowsWithTitle('星战前夜：晨曦 [Serenity]')
        for win in eve_windows:
            title = win.title
            # 按 " - " 分割，取最后一部分作为用户名
            if ' - ' in title:
                username = title.split(' - ', 1)[1]
                usernames.append(username)
            else:
                # 如果格式不符，可选择跳过或记录警告
                print(f"警告：窗口标题格式异常，无法提取用户名: {title}")
    except Exception as e:
        print(f"获取 EVE 用户名时出错: {e}")
    return usernames

import pygetwindow as gw

def get_eve_hwnd_by_username(username):
    """
    根据用户名查找对应的 EVE 窗口句柄（hWnd）。
    
    参数:
        username (str): EVE 账号的用户名，例如 'nqr-lty'
    
    返回:
        int or None: 如果找到匹配窗口，返回 hWnd；否则返回 None
    """
    try:
        # 拼接完整标题
        expected_title = f"星战前夜：晨曦 [Serenity] - {username}"
        
        # 获取所有完全匹配该标题的窗口（getWindowsWithTitle 支持模糊匹配，但精确标题可避免误匹配）
        windows = gw.getWindowsWithTitle(expected_title)
        
        # 由于标题唯一，通常只返回一个窗口
        for win in windows:
            if win.title == expected_title:  # 确保完全匹配
                hwnd = getattr(win, '_hWnd', None)
                return hwnd
        
        # 未找到
        return None
        
    except Exception as e:
        print(f"根据用户名 '{username}' 查找窗口句柄时出错: {e}")
        return None

# print(get_eve_windows_info())
# print(get_eve_usernames())
# print(get_eve_hwnd_by_username('nqr-lty'))

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

    return (positioning)



