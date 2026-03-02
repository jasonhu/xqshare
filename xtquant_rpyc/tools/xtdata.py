#!/usr/bin/env python3
"""
xtdata - 行情数据命令行工具

动态映射到 xtdata API 函数。

参数规则:
    - 工具参数（--host, --port, --limit 等）必须放在 command 之前
    - API 函数参数放在 command 之后

使用示例:
    # 工具参数在 command 之前
    xtdata --limit 100 get_stock_list_in_sector --sector-name "沪深A股"
    xtdata --host 192.168.1.100 get_full_tick --codes "000001.SZ"

    # 使用环境变量配置连接，只传 API 参数
    xtdata get_market_data_ex --codes "000001.SZ" --period 1d
"""

import sys
import argparse
from .common import (
    create_client, parse_kv_args, preprocess_params,
    format_output, add_global_args
)


def main():
    parser = argparse.ArgumentParser(
        prog="xtdata",
        description="xtquant 行情数据命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
参数规则:
  工具参数 (--host, --port, --limit 等) 必须放在 command 之前
  API 函数参数放在 command 之后

示例:
  xtdata --limit 100 get_stock_list_in_sector --sector-name "沪深A股"
  xtdata --host 192.168.1.100 get_full_tick --codes "000001.SZ"
        """
    )
    add_global_args(parser)
    parser.add_argument("command", help="API函数名")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="函数参数 (--key value)")

    args = parser.parse_args()

    # 拒绝订阅相关命令
    if args.command.startswith('subscribe'):
        print(f"错误: 命令行工具不支持订阅功能 '{args.command}'", file=sys.stderr)
        print("提示: 订阅功能需要回调函数支持，请使用 Python API 或 examples 脚本", file=sys.stderr)
        sys.exit(1)

    with create_client(args.host, args.port, args.secret, args.client_id, quiet=not args.verbose) as xt:
        func = getattr(xt.xtdata, args.command, None)
        if func is None:
            print(f"错误: 未知命令 '{args.command}'", file=sys.stderr)
            sys.exit(1)

        params = parse_kv_args(args.args)
        params = preprocess_params(params)

        # 检查 callback 参数
        if 'callback' in params:
            print("错误: 命令行工具不支持回调参数 'callback'", file=sys.stderr)
            print("提示: 回调功能需要使用 Python API 或 examples 脚本", file=sys.stderr)
            sys.exit(1)

        result = func(**params)
        limit = None if args.limit == 0 else args.limit
        format_output(result, limit)


if __name__ == "__main__":
    main()
