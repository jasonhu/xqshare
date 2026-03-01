#!/usr/bin/env python3
"""
下载历史数据示例

展示如何通过 xtquant-rpyc 下载股票历史数据到服务端本地。
下载数据后，get_market_data 等函数才能获取到数据。

使用示例:
    # 下载默认股票的日K线（000001.SZ, 600000.SH）
    python examples/download_history_data.py --host 192.168.1.100

    # 下载指定股票
    python examples/download_history_data.py --host 192.168.1.100 --codes "000001.SZ,600000.SH"

    # 下载指定日期范围的数据
    python examples/download_history_data.py --host 192.168.1.100 --codes "000001.SZ" --start 20250101 --end 20260228

    # 下载1分钟K线
    python examples/download_history_data.py --host 192.168.1.100 --codes "000001.SZ" --period 1m
"""

import argparse
from datetime import datetime, timedelta
from xtquant_rpyc import XtQuantRemote


# 默认股票代码
DEFAULT_CODES = ["000001.SZ", "600000.SH"]


def main():
    parser = argparse.ArgumentParser(
        description="下载股票历史数据到服务端本地",
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

说明:
  下载数据是异步的，调用后立即返回。
  数据会下载到服务端的本地存储，供后续 get_market_data 等函数使用。
        """
    )
    parser.add_argument("--host", required=True, help="服务端地址")
    parser.add_argument("--port", type=int, default=18812, help="服务端端口 (默认: 18812)")
    parser.add_argument("--secret", default="", help="认证密钥")
    parser.add_argument("--codes", default=",".join(DEFAULT_CODES),
                        help=f"股票代码，逗号分隔 (默认: {','.join(DEFAULT_CODES)})")
    parser.add_argument("--period", default="1d", choices=["1d", "1m", "5m", "15m", "30m", "60m"],
                        help="K线周期 (默认: 1d)")
    parser.add_argument("--start", help="开始日期 YYYYMMDD (默认: 近1年)")
    parser.add_argument("--end", help="结束日期 YYYYMMDD (默认: 今天)")

    args = parser.parse_args()

    # 解析股票代码
    stock_codes = [code.strip() for code in args.codes.split(",")]

    # 设置默认日期
    if not args.end:
        args.end = datetime.now().strftime("%Y%m%d")
    if not args.start:
        start_date = datetime.now() - timedelta(days=365)
        args.start = start_date.strftime("%Y%m%d")

    # 连接服务端
    print(f"正在连接 {args.host}:{args.port}...")
    xt = XtQuantRemote(
        host=args.host,
        port=args.port,
        client_secret=args.secret
    )

    try:
        # 下载数据
        print(f"正在下载历史数据...")
        print(f"  股票代码: {', '.join(stock_codes)}")
        print(f"  K线周期: {args.period}")
        print(f"  日期范围: {args.start} ~ {args.end}")
        print()

        # 定义进度回调
        def on_progress(data):
            finished = data.get('finished', 0)
            total = data.get('total', 0)
            if total > 0:
                percent = finished / total * 100
                print(f"\r  下载进度: {finished}/{total} ({percent:.1f}%)", end="", flush=True)

        # download_history_data2 是同步阻塞的，会等待下载完成
        result = xt.xtdata.download_history_data2(
            stock_list=stock_codes,
            period=args.period,
            start_time=args.start,
            end_time=args.end,
            callback=on_progress
        )

        print()  # 换行

        # 显示下载结果
        # 返回值说明：
        #   - 空字典 {}：下载成功（可能是增量下载，无新数据）
        #   - {stock: {start_time, end_time}}：全量下载成功，包含时间范围
        #   - 异常：下载失败
        print(f"\n下载完成！")
        if result:
            print(f"{'='*60}")
            print("下载详情：")
            for stock_code, info in result.items():
                start_time = info.get('start_time', 'N/A')
                end_time = info.get('end_time', 'N/A')
                print(f"  {stock_code}: {start_time} ~ {end_time}")
            print(f"{'='*60}")
        else:
            print("  返回值为空（增量下载或数据已存在，数据已保存到服务端本地）")

        print()
        print("验证数据:")
        print(f"  python examples/get_market_data_ex.py --host {args.host} --codes \"{args.codes}\" --period {args.period}")

    finally:
        xt.close()
        print("\n连接已关闭")


if __name__ == "__main__":
    main()
