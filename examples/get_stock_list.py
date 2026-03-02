#!/usr/bin/env python3
"""
获取股票列表示例

展示如何通过 xtquant-rpyc 获取指定板块的股票列表。

使用示例:
    # 获取沪深A股列表
    python examples/get_stock_list.py --host 192.168.1.100

    # 获取沪深300成分股
    python examples/get_stock_list.py --host 192.168.1.100 --sector "沪深300"

    # 使用认证密钥
    python examples/get_stock_list.py --host 192.168.1.100 --secret "your-secret"
"""

import argparse
import os
from xtquant_rpyc import XtQuantRemote


def main():
    parser = argparse.ArgumentParser(
        description="获取指定板块的股票列表",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
常用板块名称:
  沪深A股    - 所有A股股票
  沪深300    - 沪深300指数成分股
  中证500    - 中证500指数成分股
  创业板     - 创业板股票
  科创板     - 科创板股票
  上证A股    - 上海证券交易所A股
  深证A股    - 深圳证券交易所A股
  沪深指数   - 所有指数
        """
    )
    parser.add_argument("--host", help="服务端地址 (默认: 环境变量 XTQUANT_REMOTE_HOST 或 localhost)")
    parser.add_argument("--port", type=int, help="服务端端口 (默认: 环境变量 XTQUANT_REMOTE_PORT 或 18812)")
    parser.add_argument("--secret", help="认证密钥 (默认: 环境变量 XTQUANT_CLIENT_SECRET)")
    parser.add_argument("--sector", default="沪深A股", help="板块名称 (默认: 沪深A股)")

    args = parser.parse_args()

    # 连接服务端（支持环境变量）
    # 获取实际使用的值用于显示
    host_display = args.host or os.environ.get("XTQUANT_REMOTE_HOST", "localhost")
    port_display = args.port or int(os.environ.get("XTQUANT_REMOTE_PORT", "18812"))
    print(f"正在连接 {host_display}:{port_display}...")

    # 创建连接（参数为 None 时自动读取环境变量）
    xt = XtQuantRemote(
        host=args.host,
        port=args.port,
        client_secret=args.secret
    )

    try:
        # 获取股票列表
        print(f"正在获取板块 [{args.sector}] 的股票列表...")
        stocks = xt.xtdata.get_stock_list_in_sector(args.sector)

        # 输出结果
        print(f"\n{'='*50}")
        print(f"板块: {args.sector}")
        print(f"股票数量: {len(stocks)}")
        print(f"{'='*50}")

        # 显示前20只股票
        display_count = min(20, len(stocks))
        for i, code in enumerate(stocks[:display_count], 1):
            print(f"{i:3d}. {code}")

        if len(stocks) > display_count:
            print(f"... 还有 {len(stocks) - display_count} 只股票")

        print(f"\n总计: {len(stocks)} 只股票")

    finally:
        xt.close()
        print("\n连接已关闭")


if __name__ == "__main__":
    main()
