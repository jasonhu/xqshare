#!/usr/bin/env python3
"""
xttrader - 交易命令行工具

支持 XtQuantTrader 的交易操作。

参数规则:
    - 工具参数（--host, --port, --account-id 等）必须放在 command 之前
    - API 函数参数放在 command 之后
    - account 参数会自动补充，无需手动传递

使用示例:
    # 查询持仓
    xttrader --account-id "12345678" --userdata-path "C:\\\\迅投QMT\\\\userdata_mini" query_stock_positions

    # 查询资产
    xttrader --account-id "12345678" query_stock_asset

    # 下单
    xttrader --account-id "12345678" order_stock --stock-code "000001.SZ" --order-type 23 --order-volume 100
"""

import sys
import argparse
from .common import (
    create_client, parse_kv_args, preprocess_params,
    format_output, add_global_args, add_trader_args, create_trader
)


def main():
    parser = argparse.ArgumentParser(
        prog="xttrader",
        description="xtquant 交易命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
参数规则:
  工具参数 (--host, --port, --account-id 等) 必须放在 command 之前
  API 函数参数放在 command 之后
  account 参数会自动补充，无需手动传递

常用命令:
  query_stock_positions  - 查询持仓
  query_stock_asset      - 查询资产
  order_stock            - 下单
  order_cancel           - 撤单

示例:
  xttrader --account-id "12345678" query_stock_positions
  xttrader --account-id "12345678" order_stock --stock-code "000001.SZ" --order-type 23 --order-volume 100
        """
    )
    add_global_args(parser)
    add_trader_args(parser)
    parser.add_argument("command", help="API函数名")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="函数参数 (--key value)")

    args = parser.parse_args()

    with create_client(args.host, args.port, args.secret, args.client_id, quiet=not args.verbose) as xt:
        try:
            trader, account = create_trader(xt, args.userdata_path, args.account_id, args.account_type)
        except Exception as e:
            print(f"错误: {e}", file=sys.stderr)
            sys.exit(1)

        try:
            func = getattr(trader, args.command, None)
            if func is None:
                print(f"错误: 未知命令 '{args.command}'", file=sys.stderr)
                sys.exit(1)

            params = parse_kv_args(args.args)
            params = preprocess_params(params)

            # 自动添加 account 参数
            params['account'] = account

            result = func(**params)
            limit = None if args.limit == 0 else args.limit
            format_output(result, limit)
        finally:
            trader.stop()


if __name__ == "__main__":
    main()
