from pywinauto import Application, findwindows
import argparse
import sys
import json


def print_json_and_flush(data):
    """输出JSON并强制刷新缓冲区"""
    print(json.dumps(data, ensure_ascii=True))

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='UI自动化工具')
    parser.add_argument('--app', required=True, help='应用窗口名称')
    parser.add_argument('--control', help='控件名称')
    parser.add_argument('--type', help='控件类型')
    parser.add_argument('--check', action='store_true', help='输出窗口控件树结构')
    parser.add_argument('--click', action='store_true', help='是否执行点击操作')
    parser.add_argument('--dump-file', help='将窗口树结构保存到指定文件')

    args = parser.parse_args()

    # 参数验证
    if not args.check and not (args.control and args.type):
        print_json_and_flush({"success": False, "error": "必须指定 --check 或者同时指定 --control 和 --type"})
        sys.exit(0)
    try:
        # 查找包含指定应用名称的窗口
        app_pattern = f".*{args.app}.*"
        windows = findwindows.find_windows(title_re=app_pattern)

        if not windows:
            print_json_and_flush({"success": False, "error": f"未找到包含 '{args.app}' 的窗口"})
            sys.exit(0)

        for window_handle in windows:
            try:
                app = Application(backend="uia").connect(handle=window_handle)
                window = app.window(handle=window_handle)

                # 如果是检查模式，输出窗口树结构
                if args.check:
                    window_title = window.window_text()
                    window_index = windows.index(window_handle) + 1
                    print(f"\n=== 窗口 {window_index}: {window_title} (句柄: {window_handle}) ===")

                    # 检查是否需要输出到文件
                    dump_file = getattr(args, 'dump_file', None)
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

                        print(f"窗口 {window_index} 的树结构已保存到: {dump_file}")
                    else:
                        # 输出到控制台
                        window.dump_tree(depth=None, filename=None)

                    # 继续处理下一个窗口，不要break
                    continue

                # 查找指定的控件
                text = window.child_window(title=args.control, control_type=args.type)

                if not text.exists():
                    continue

                try:
                    rect = text.rectangle()
                    center_x = (rect.left + rect.right) // 2
                    center_y = (rect.top + rect.bottom) // 2

                    # 准备输出结果
                    result = {
                        "success": True,
                        "control_title": args.control,
                        "control_type": args.type,
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
                    if args.click:
                        text.click_input(coords=(center_x - rect.left, center_y - rect.top))
                        result["clicked"] = True

                    # 输出结果
                    print_json_and_flush(result)

                except Exception as coord_error:
                    error_result = {
                        "success": False,
                        "error": str(coord_error),
                        "control_title": args.control,
                        "control_type": args.type
                    }

                    print_json_and_flush(error_result)

                break

            except Exception as e:
                continue

        # 如果是check模式，输出总结信息
        if args.check:
            dump_file = getattr(args, 'dump_file', None)
            result = {
                "success": True,
                "action": "check_windows",
                "app_name": args.app,
                "windows_found": len(windows),
                "dump_file": dump_file if dump_file else None
            }
            print_json_and_flush(result)

    except Exception as e:
        print_json_and_flush({"success": False, "error": f"查找{args.app}窗口时发生错误: {str(e)}"})

if __name__ == "__main__":
    main()
