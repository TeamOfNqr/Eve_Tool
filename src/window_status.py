import pygetwindow as gw
import time

try:
    import win32gui
    import win32con
    import win32process
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

def get_eve_window_by_username(username):
    """
    根据用户名查找对应的 EVE 窗口对象（pygetwindow Window 对象）。
    
    参数:
        username (str): EVE 账号的用户名，例如 'nqr-lty'
    
    返回:
        pygetwindow.Window or None: 如果找到匹配窗口，返回 Window 对象；否则返回 None
    """
    try:
        # 拼接完整标题
        expected_title = f"星战前夜：晨曦 [Serenity] - {username}"
        
        # 获取所有完全匹配该标题的窗口
        windows = gw.getWindowsWithTitle(expected_title)
        
        # 由于标题唯一，通常只返回一个窗口
        for win in windows:
            if win.title == expected_title:  # 确保完全匹配
                return win
        
        # 未找到
        return None
        
    except Exception as e:
        print(f"根据用户名 '{username}' 查找窗口对象时出错: {e}")
        return None

def bring_window_to_front(hwnd):
    """
    将指定窗口移动到最前面（临时前置，不是永久置顶）。
    使用多种方法确保窗口被置于最前，同时保持窗口位置和大小不变。
    
    参数:
        hwnd (int): 窗口句柄（hWnd）
    
    返回:
        bool: 如果成功前置窗口返回 True，否则返回 False
    """
    if hwnd is None:
        print("错误: 窗口句柄为 None，无法前置窗口。")
        return False
    
    if not WIN32_AVAILABLE:
        print("错误: win32gui 未安装，无法前置窗口。")
        return False
    
    try:
        # 检查窗口是否存在
        if not win32gui.IsWindow(hwnd):
            print(f"错误: 窗口句柄 {hwnd} 无效或窗口已关闭。")
            return False
        
        # 保存窗口的当前位置和大小，确保不会改变
        rect = win32gui.GetWindowRect(hwnd)
        x, y, right, bottom = rect
        width = right - x
        height = bottom - y
        
        # 方法1: 如果窗口最小化，先恢复
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            time.sleep(0.1)
        
        # 方法2: 确保窗口可见
        if not win32gui.IsWindowVisible(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        
        # 方法3: 使用 SetWindowPos 将窗口置于最前（HWND_TOP 是临时置顶，不是永久）
        # 这是最可靠的方法，使用保存的位置和大小确保窗口位置不变
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOP,  # 置于最前（临时，不是永久置顶）
            x, y, width, height,  # 使用原始位置和大小
            win32con.SWP_SHOWWINDOW | win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
        )
        
        # 方法4: 再次调用 SetWindowPos，确保窗口在最前（有时需要调用两次）
        time.sleep(0.05)
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOP,
            x, y, width, height,
            win32con.SWP_SHOWWINDOW | win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
        )
        
        # 方法5: 尝试使用 SetForegroundWindow（可能因为安全限制失败，但不影响其他方法）
        try:
            # 获取当前前台窗口的线程ID
            foreground_hwnd = win32gui.GetForegroundWindow()
            if foreground_hwnd:
                foreground_thread_id = win32gui.GetWindowThreadProcessId(foreground_hwnd)[0]
                current_thread_id = win32gui.GetCurrentThreadId()
                
                # 如果线程不同，尝试附加线程输入
                if foreground_thread_id != current_thread_id:
                    try:
                        win32process.AttachThreadInput(current_thread_id, foreground_thread_id, True)
                        win32gui.SetForegroundWindow(hwnd)
                        win32process.AttachThreadInput(current_thread_id, foreground_thread_id, False)
                    except Exception:
                        # 如果附加失败，直接尝试设置前台窗口
                        win32gui.SetForegroundWindow(hwnd)
                else:
                    win32gui.SetForegroundWindow(hwnd)
        except Exception:
            # SetForegroundWindow 可能失败，但不影响其他方法
            pass
        
        # 方法6: 最后再次确保窗口位置和大小没有改变
        current_rect = win32gui.GetWindowRect(hwnd)
        current_x, current_y, current_right, current_bottom = current_rect
        current_width = current_right - current_x
        current_height = current_bottom - current_y
        
        # 如果位置或大小改变了，恢复原位置和大小
        if current_x != x or current_y != y or current_width != width or current_height != height:
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_TOP,
                x, y, width, height,
                win32con.SWP_SHOWWINDOW | win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
            )
        
        # 验证窗口是否可见且不在最小化状态
        if win32gui.IsWindowVisible(hwnd) and not win32gui.IsIconic(hwnd):
            return True
        else:
            return False
        
    except Exception as e:
        print(f"前置窗口时出错: {e}")
        return False

def minimize_all_eve_windows():
    """
    将所有EVE窗口最小化到任务栏。
    
    返回:
        int: 成功最小化的窗口数量
    """
    if not WIN32_AVAILABLE:
        print("错误: win32gui 未安装，无法最小化窗口。")
        return 0
    
    minimized_count = 0
    try:
        # 获取所有EVE窗口
        eve_windows = gw.getWindowsWithTitle('星战前夜：晨曦 [Serenity]')
        
        for win in eve_windows:
            try:
                hwnd = getattr(win, '_hWnd', None)
                if hwnd is None:
                    continue
                
                # 检查窗口是否存在且未最小化
                if win32gui.IsWindow(hwnd) and not win32gui.IsIconic(hwnd):
                    # 最小化窗口
                    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                    minimized_count += 1
            except Exception as e:
                # 最小化窗口时出错，继续处理下一个窗口
                continue
        
        if minimized_count > 0:
            print(f"已最小化 {minimized_count} 个EVE窗口到任务栏")
        
        return minimized_count
        
    except Exception as e:
        print(f"最小化所有EVE窗口时出错: {e}")
        return 0


