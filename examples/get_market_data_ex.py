#!/usr/bin/env python3
"""
获取K线数据示例 (使用 get_market_data_ex)

展示如何通过 xtquant-rpyc 获取股票的K线行情数据。
get_market_data_ex 返回格式更直观：{stock: DataFrame}，DataFrame 的 index 为时间。

使用示例:
    # 获取日K线（默认近30天）
    python examples/get_market_data_ex.py --host 192.168.1.100 --codes "000001.SZ,600000.SH"

    # 获取指定日期范围的日K线
    python examples/get_market_data_ex.py --host 192.168.1.100 --codes "000001.SZ" --start 20260101 --end 20260228

    # 获取1分钟K线
    python examples/get_market_data_ex.py --host 192.168.1.100 --codes "000001.SZ" --period 1m
"""

import argparse
from datetime import datetime, timedelta
from xtquant_rpyc import XtQuantRemote


def main():
    parser = argparse.ArgumentParser(
        description="获取股票K线行情数据 (get_market_data_ex)",
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

返回格式: {stock: DataFrame}
  DataFrame.index = 时间
  DataFrame.columns = open, high, low, close, volume, amount 等
        """
    )
    parser.add_argument("--host", required=True, help="服务端地址")
    parser.add_argument("--port", type=int, default=18812, help="服务端端口 (默认: 18812)")
    parser.add_argument("--secret", default="", help="认证密钥")
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

    # 连接服务端
    print(f"正在连接 {args.host}:{args.port}...")
    xt = XtQuantRemote(
        host=args.host,
        port=args.port,
        client_secret=args.secret
    )

    try:
        # 获取K线数据
        print(f"正在获取K线数据...")
        print(f"  股票代码: {', '.join(stock_codes)}")
        print(f"  K线周期: {args.period}")
        print(f"  日期范围: {args.start} ~ {args.end}")

        # get_market_data_ex 返回 {stock: DataFrame}
        # DataFrame 的 index 是时间，columns 是字段
        data = xt.xtdata.get_market_data_ex(
            stock_list=stock_codes,
            period=args.period,
            start_time=args.start,
            end_time=args.end
        )

        # 输出结果
        print(f"\n{'='*60}")
        if data is not None and len(data) > 0:
            print(f"获取到 {len(data)} 只股票的数据")
            print(f"{'='*60}")

            for stock_code, df in data.items():
                if df is not None and len(df) > 0:
                    print(f"\n股票: {stock_code}")
                    print(f"  数据条数: {len(df)}")
                    print(f"  时间范围: {df.index[0]} ~ {df.index[-1]}")
                    print(f"  数据字段: {', '.join(df.columns.tolist())}")

                    # 显示前5条数据
                    print(f"\n  数据预览 (前5条):")
                    print(df.head(5).to_string())
                else:
                    print(f"\n股票: {stock_code} - 无数据")
        else:
            print("未获取到数据，请检查股票代码和日期范围")

    finally:
        xt.close()
        print("\n连接已关闭")


if __name__ == "__main__":
    main()
