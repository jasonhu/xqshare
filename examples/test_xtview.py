"""
xtview 模块测试示例

测试 xtview 模块的基本功能：
1. 连接状态检查
2. 调度任务查询
3. UI 面板控制（可选）
"""

from xqshare import connect, disconnect


def test_xtview_connection():
    """测试 xtview 连接"""
    print("=" * 50)
    print("测试 1: xtview 模块连接")
    print("=" * 50)

    xt = connect()
    print(f"连接状态: {xt.is_connected()}")

    # 访问 xtview 代理对象（此时还未真正调用服务端）
    print(f"xtview 代理对象: {xt.xtview}")
    print("✓ xtview 代理对象获取成功\n")

    return xt


def test_query_schedule(xt):
    """测试查询调度任务"""
    print("=" * 50)
    print("测试 2: 查询调度任务")
    print("=" * 50)

    try:
        tasks = xt.xtview.query_schedule_task()
        print(f"当前调度任务数量: {len(tasks) if tasks else 0}")
        if tasks:
            for i, task in enumerate(tasks, 1):
                print(f"  任务 {i}: {task}")
        else:
            print("  暂无调度任务")
        print("✓ 查询调度任务成功\n")
        return True
    except Exception as e:
        print(f"✗ 查询失败: {e}\n")
        return False


def test_get_client(xt):
    """测试获取客户端连接"""
    print("=" * 50)
    print("测试 3: 获取 xtview 客户端")
    print("=" * 50)

    try:
        client = xt.xtview.get_client()
        print(f"客户端对象: {client}")
        is_connected = client.is_connected() if hasattr(client, 'is_connected') else "unknown"
        print(f"连接状态: {is_connected}")
        print("✓ 获取客户端成功\n")
        return True
    except Exception as e:
        print(f"✗ 获取客户端失败: {e}\n")
        return False


def test_ui_panel(xt):
    """测试 UI 面板控制（可选）"""
    print("=" * 50)
    print("测试 4: UI 面板控制（需要 QMT 客户端运行）")
    print("=" * 50)

    try:
        # 创建一个简单的 UI 面板
        # 注意：这需要 QMT 客户端正在运行
        from xqshare.client import XtQuantRemote

        # UIPanel 参数：code, period, figures, startX, startY, width, height
        panel = xt.xtview.UIPanel(
            code='600000.SH',
            period='1d',
            figures=[{'ma': {'n1': 5, 'n2': 10}}],
            startX=-1,
            startY=-1,
            width=-1,
            height=-1
        )
        print(f"UIPanel 对象: code={panel.code}, period={panel.period}")

        # 应用 UI 控制
        xt.xtview.apply_ui_panel_control([panel])
        print("✓ UI 面板控制成功\n")
        return True
    except Exception as e:
        print(f"✗ UI 面板控制失败: {e}")
        print("  （可能 QMT 客户端未运行或不支持此功能）\n")
        return False


def main():
    print("\n" + "=" * 50)
    print("  xtview 模块功能测试")
    print("=" * 50 + "\n")

    xt = None
    try:
        xt = test_xtview_connection()
        test_query_schedule(xt)
        test_get_client(xt)
        test_ui_panel(xt)

    except Exception as e:
        print(f"\n✗ 测试异常: {e}")
    finally:
        if xt:
            disconnect()
            print("连接已关闭")

    print("\n" + "=" * 50)
    print("  测试完成")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
