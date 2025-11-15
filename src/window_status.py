import pygetwindow as gw
try:
    import win32gui
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("警告: win32gui 未安装，窗口前置功能将不可用。请使用 'pip install pywin32' 安装。")


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

def bring_window_to_front(hwnd):
    """
    将指定窗口前置到最前面（临时前置，不是永久置顶）。
    
    参数:
        hwnd (int): 窗口句柄（hWnd）
    
    返回:
        bool: 如果成功前置窗口返回 True，否则返回 False
    """
    if not WIN32_AVAILABLE:
        print("错误: win32gui 未安装，无法前置窗口。")
        return False
    
    if hwnd is None:
        print("错误: 窗口句柄为 None，无法前置窗口。")
        return False
    
    try:
        # 检查窗口是否存在
        if not win32gui.IsWindow(hwnd):
            print(f"错误: 窗口句柄 {hwnd} 无效或窗口已关闭。")
            return False
        
        # 如果窗口最小化，先恢复
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        
        # 将窗口置于前台
        win32gui.SetForegroundWindow(hwnd)
        
        # 确保窗口可见（如果被其他窗口遮挡）
        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        
        return True
        
    except Exception as e:
        print(f"前置窗口时出错: {e}")
        return False


