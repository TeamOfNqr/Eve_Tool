import pygetwindow as gw

def get_eve_windows_info():
    """
    获取所有标题包含“星战前夜”的窗口名称、唯一ID、是否前台
    
    返回:
        List[List[str, int or None, bool]]: 每个元素为 [窗口标题, hWnd句柄, 是否激活]
    """
    windows_info = []
    try:
        # 获取所有包含“星战前夜”的窗口对象
        eve_windows = gw.getWindowsWithTitle('星战前夜')
        
        for win in eve_windows:
            title = win.title
            is_active = win.isActive
            
            # 尝试获取 hWnd（新版 pygetwindow 使用 _hWnd 作为内部属性）
            hwnd = getattr(win, '_hWnd', None)  # 安全获取，不存在则为 None
            
            windows_info.append([title, hwnd, is_active])
            
    except Exception as e:
        print(f"获取 EVE 窗口时出错: {e}")
    
    return windows_info

print(get_eve_windows_info())