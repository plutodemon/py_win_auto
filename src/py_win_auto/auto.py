from pywinauto import Application, findwindows
import argparse
import sys
import json
import time
import pyautogui


def print_json_and_flush(data):
    """输出JSON并强制刷新缓冲区"""
    print(json.dumps(data, ensure_ascii=True))


def find_and_wait_for_windows(app_name, check_interval=1, wait_after_found=13, timeout=None):
    """查找窗口，如果没有找到则等待程序启动
    
    Args:
        app_name (str): 应用程序窗口名称
        check_interval (int): 检查间隔时间（秒）
        wait_after_found (int): 找到程序后的等待时间（秒）
        timeout (int): 超时时间（秒），None表示无限等待
    
    Returns:
        list: 找到的窗口句柄列表，超时时返回None
    """

    app_pattern = f".*{app_name}.*"
    start_time = time.time()

    while True:
        windows = findwindows.find_windows(title_re=app_pattern)
        if windows:
            # 找到程序后等待指定时间
            time.sleep(wait_after_found)
            return windows

        # 检查是否超时
        if timeout is not None:
            elapsed_time = time.time() - start_time
            if elapsed_time >= timeout:
                return None

        # 等待指定间隔后再次检查
        time.sleep(check_interval)


def process_check_mode(window, window_handle, windows, dump_file):
    """处理检查模式，输出窗口树结构
    
    Args:
        window: 窗口对象
        window_handle: 窗口句柄
        windows: 窗口句柄列表
        dump_file: 输出文件路径
    """
    window_title = window.window_text()
    window_index = windows.index(window_handle) + 1

    if dump_file:
        # 输出到文件，处理编码问题
        from io import StringIO

        # 捕获dump_tree的输出
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        window.dump_tree(depth=None, filename=None)
        sys.stdout = old_stdout
        tree_content = captured_output.getvalue()

        # 追加模式写入文件，使用UTF-8编码
        mode = 'w' if window_index == 1 else 'a'
        with open(dump_file, mode, encoding='utf-8') as f:
            f.write(f"=== 窗口 {window_index}: {window_title} (句柄: {window_handle}) ===\n")
            f.write(tree_content)
            f.write("\n" + "=" * 80 + "\n\n")
    else:
        # 输出到控制台
        window.dump_tree(depth=None, filename=None)


def process_control_operation(window, control_name, control_type, should_click):
    """处理控件操作
    
    Args:
        window: 窗口对象
        control_name (str): 控件名称
        control_type (str): 控件类型
        should_click (bool): 是否执行点击操作
    
    Returns:
        tuple: (操作是否成功, 结果数据)
    """
    # 查找指定的控件
    text = window.child_window(title=control_name, control_type=control_type)

    if not text.exists():
        return False, None

    try:
        rect = text.rectangle()
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2

        # 准备输出结果
        result = {
            "success": True,
            "control_title": control_name,
            "control_type": control_type,
            "position": {
                "left": rect.left,
                "top": rect.top,
                "right": rect.right,
                "bottom": rect.bottom
            },
            "center": {
                "x": center_x,
                "y": center_y
            },
            "clicked": False
        }

        # 根据参数决定是否执行点击
        if should_click:
            click_success = False
            click_error_msg = None
            
            # 使用pyautogui进行绝对坐标点击
            try:
                # 禁用pyautogui的安全检查，防止鼠标移动导致异常
                original_failsafe = pyautogui.FAILSAFE
                pyautogui.FAILSAFE = False
                
                # 设置点击延迟，避免过快操作
                pyautogui.PAUSE = 0.1
                
                # 使用绝对坐标点击，不受用户鼠标移动影响
                pyautogui.click(center_x, center_y, duration=0.1)
                click_success = True
                
                # 恢复原始设置
                pyautogui.FAILSAFE = original_failsafe
                
            except Exception as e:
                click_error_msg = f"pyautogui点击失败: {str(e)}"
            
            # 设置点击结果
            result["clicked"] = click_success
            if not click_success and click_error_msg:
                result["click_error"] = click_error_msg

        return True, result

    except Exception as coord_error:
        error_result = {
            "success": False,
            "error": str(coord_error),
            "control_title": control_name,
            "control_type": control_type
        }
        return True, error_result


def execute_main_loop(args):
    """执行主循环逻辑
    
    Args:
        args: 命令行参数对象
    """
    # 查找和等待窗口
    check_interval = getattr(args, 'check_interval', 1)
    wait_after_found = getattr(args, 'wait_after_found', 13)
    timeout = getattr(args, 'timeout', None)
    windows = find_and_wait_for_windows(args.app, check_interval, wait_after_found, timeout)
    
    # 检查是否超时
    if windows is None:
        print_json_and_flush({"success": False, "error": f"等待程序 {args.app} 启动超时（{timeout}秒）"})
        sys.exit(1)

    # 处理找到的窗口
    for window_handle in windows:
        try:
            app = Application(backend="uia").connect(handle=window_handle)
            window = app.window(handle=window_handle)

            # 如果是检查模式，输出窗口树结构
            if args.check:
                dump_file = getattr(args, 'dump_file', None)
                process_check_mode(window, window_handle, windows, dump_file)
                # 继续处理下一个窗口，不要break
                continue

            # 处理控件操作
            success, result = process_control_operation(window, args.control, args.type, args.click)
            if success:
                if result:
                    print_json_and_flush(result)
                break

        except Exception as e:
            continue

    # 如果是check模式，输出总结信息并标记操作完成
    dump_file = getattr(args, 'dump_file', None)
    if args.check and dump_file:
        result = {
            "success": True,
            "action": "check_windows",
            "app_name": args.app,
            "windows_found": len(windows),
            "dump_file": dump_file if dump_file else None
        }
        print_json_and_flush(result)


def main():
    """主函数，负责参数解析和程序入口"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='UI自动化工具')
    parser.add_argument('--app', required=True, help='应用窗口名称')
    parser.add_argument('--control', help='控件名称')
    parser.add_argument('--type', help='控件类型')
    parser.add_argument('--check', action='store_true', help='输出窗口控件树结构')
    parser.add_argument('--click', action='store_true', help='是否执行点击操作')
    parser.add_argument('--dump-file', help='将窗口树结构保存到指定文件')
    parser.add_argument('--check-interval', type=int, default=1, help='检查程序是否启动的间隔时间（秒），默认1秒')
    parser.add_argument('--wait-after-found', type=int, default=13, help='找到程序后的等待时间（秒），默认13秒')
    parser.add_argument('--timeout', type=int, help='等待程序启动的超时时间（秒），不指定则无限等待')

    args = parser.parse_args()

    # 参数验证
    if not args.check and not (args.control and args.type):
        print_json_and_flush({"success": False, "error": "必须指定 --check 或者同时指定 --control 和 --type"})
        sys.exit(0)

    try:
        # 执行主循环逻辑
        execute_main_loop(args)
    except Exception as e:
        print_json_and_flush({"success": False, "error": f"查找{args.app}窗口时发生错误: {str(e)}"})


if __name__ == "__main__":
    main()
