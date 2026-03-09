#!/usr/bin/env python3
"""
获取K线数据示例

展示如何通过 xqshare 获取股票的K线行情数据。

使用示例:
    # 获取日K线（默认近30天）
    python examples/get_market_data.py --host 192.168.1.100 --codes "000001.SZ,600000.SH"

    # 获取指定日期范围的日K线
    python examples/get_market_data.py --host 192.168.1.100 --codes "000001.SZ" --start 20260101 --end 20260228

    # 获取1分钟K线
    python examples/get_market_data.py --host 192.168.1.100 --codes "000001.SZ" --period 1m

    # 获取5分钟K线
    python examples/get_market_data.py --host 192.168.1.100 --codes "000001.SZ" --period 5m
"""

import argparse
import os
from datetime import datetime, timedelta
from xqshare import XtQuantRemote


def main():
    parser = argparse.ArgumentParser(
        description="获取股票K线行情数据",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
K线周期 (period):
  1d   - 日K线
  1m   - 1分钟K线
  5m   - 5分钟K线
  15m  - 15分钟K线
  30m  - 30分钟K线
  60m  - 60分钟K线

日期格式: YYYYMMDD (如: 20260101)
        """
    )
    parser.add_argument("--host", help="服务端地址 (默认: 环境变量 XQSHARE_REMOTE_HOST 或 localhost)")
    parser.add_argument("--port", type=int, help="服务端端口 (默认: 环境变量 XQSHARE_REMOTE_PORT 或 18812)")
    parser.add_argument("--secret", help="认证密钥 (默认: 环境变量 XQSHARE_CLIENT_SECRET)")
    parser.add_argument("--codes", required=True, help="股票代码，逗号分隔 (如: 000001.SZ,600000.SH)")
    parser.add_argument("--period", default="1d", choices=["1d", "1m", "5m", "15m", "30m", "60m"],
                        help="K线周期 (默认: 1d)")
    parser.add_argument("--start", help="开始日期 YYYYMMDD (默认: 近30天)")
    parser.add_argument("--end", help="结束日期 YYYYMMDD (默认: 今天)")

    args = parser.parse_args()

    # 解析股票代码
    stock_codes = [code.strip() for code in args.codes.split(",")]

    # 设置默认日期
    if not args.end:
        args.end = datetime.now().strftime("%Y%m%d")
    if not args.start:
        start_date = datetime.now() - timedelta(days=30)
        args.start = start_date.strftime("%Y%m%d")

    # 连接服务端（支持环境变量）
    host = args.host  # None 时 XtQuantRemote 会自动读取环境变量
    port = args.port  # None 时 XtQuantRemote 会自动读取环境变量
    print(f"正在连接 {host or '环境变量配置'}:{port or '环境变量配置'}...")
    xt = XtQuantRemote(
        host=host,
        port=port,
        client_secret=args.secret  # None 时自动读取环境变量
    )

    try:
        # 获取K线数据
        print(f"正在获取K线数据...")
        print(f"  股票代码: {', '.join(stock_codes)}")
        print(f"  K线周期: {args.period}")
        print(f"  日期范围: {args.start} ~ {args.end}")

        data = xt.xtdata.get_market_data(
            stock_list=stock_codes,
            period=args.period,
            start_time=args.start,
            end_time=args.end
        )

        # 输出结果
        # get_market_data 返回 dict { field: DataFrame }
        # DataFrame 的 index 为 stock_list，columns 为 time_list
        print(f"\n{'='*60}")
        if data is not None and len(data) > 0:
            print(f"获取到 {len(data)} 个字段的数据")
            print(f"{'='*60}")

            # 获取时间范围（从第一个字段的 DataFrame）
            first_field = list(data.keys())[0]
            first_df = data[first_field]
            time_cols = first_df.columns.tolist()
            print(f"  时间范围: {time_cols[0]} ~ {time_cols[-1]}")
            print(f"  时间点数: {len(time_cols)}")
            print(f"  股票列表: {', '.join(first_df.index.tolist())}")
            print(f"  数据字段: {', '.join(data.keys())}")

            # 显示收盘价数据（前5个时间点）
            if 'close' in data:
                print(f"\n收盘价数据 (前5个时间点):")
                print(data['close'].iloc[:, :5].to_string())
            else:
                # 如果没有 close 字段，显示第一个字段
                print(f"\n{first_field} 数据 (前5个时间点):")
                print(first_df.iloc[:, :5].to_string())
        else:
            print("未获取到数据，请检查股票代码和日期范围")

    finally:
        xt.close()
        print("\n连接已关闭")


if __name__ == "__main__":
    main()
