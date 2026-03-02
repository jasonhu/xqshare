#!/usr/bin/env python3
"""
测试 RPyC netref 异步回调机制

验证客户端函数作为 netref 传递给服务端后，服务端能否异步回调。
"""

import argparse
import time
import rpyc


def main():
    parser = argparse.ArgumentParser(description="测试 RPyC 异步回调")
    parser.add_argument("--host", help="服务端地址 (默认: 环境变量 XTQUANT_REMOTE_HOST 或 localhost)")
    parser.add_argument("--port", type=int, help="服务端端口 (默认: 环境变量 XTQUANT_REMOTE_PORT 或 18812)")
    parser.add_argument("--delay", type=float, default=2.0, help="回调间隔秒数")
    parser.add_argument("--count", type=int, default=5, help="回调次数")

    args = parser.parse_args()

    # 定义回调函数
    def my_callback(message: str) -> str:
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        return "OK"

    config = {
        'allow_public_attrs': True,
        'allow_pickle': True,
        'allow_getattr': True,
        'allow_setattr': True,
        'allow_delattr': True,
        'allow_all_attrs': True,
        'sync_request_timeout': 300,
    }

    # 支持环境变量
    host = args.host  # None 时使用 localhost
    port = args.port or 18812  # None 时使用默认端口
    print(f"正在连接 {host or 'localhost'}:{port}...")
    conn = rpyc.connect(host or 'localhost', port, config=config)

    # 启动后台线程自动处理传入消息（回调）
    from rpyc.utils.helpers import BgServingThread
    bg_thread = BgServingThread(conn)
    print("已启动后台消息处理线程\n")

    try:
        print(f"发起异步回调测试...")
        print(f"  间隔: {args.delay} 秒")
        print(f"  次数: {args.count} 次")
        print(f"\n等待回调中...\n")

        # 直接调用服务端方法，传递回调函数
        result = conn.root.test_async_callback(my_callback, args.delay, args.count)
        print(f"服务端返回: {result}\n")

        # 等待所有回调执行完成 - 现在可以简单 sleep 了
        wait_time = args.delay * args.count + 2
        print(f"等待 {wait_time} 秒观察回调...\n")
        time.sleep(wait_time)

        print("\n测试完成！")

    finally:
        bg_thread.stop()
        conn.close()
        print("连接已关闭")


if __name__ == "__main__":
    main()
