#!/usr/bin/env python3
"""
下载历史数据示例 (服务端封装版本)

使用服务端封装的 download_history_data2 方法，避免回调传输问题。
返回完整的下载状态和结果。

使用示例:
    # 下载默认股票的日K线
    python examples/download_history_data2.py --host 127.0.0.1

    # 下载指定股票
    python examples/download_history_data2.py --host 127.0.0.1 --codes "000001.SZ,600000.SH"

    # 下载指定日期范围
    python examples/download_history_data2.py --host 127.0.0.1 --codes "000001.SZ" --start 20250101
"""

import argparse
import os
from datetime import datetime, timedelta
from xqshare import XtQuantRemote


# 默认股票代码
DEFAULT_CODES = ["000001.SZ", "600000.SH"]


def main():
    parser = argparse.ArgumentParser(
        description="下载股票历史数据（服务端封装版本）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
K线周期 (period):
  1d   - 日K线
  1m   - 1分钟K线
  5m   - 5分钟K线
  15m  - 15分钟K线
  30m  - 30分钟K线
  60m  - 60分钟K线

返回值说明:
  {
    'finished': n,    # 已完成数量
    'total': n,       # 总数量
    'done': bool,     # 是否完成
    'message': str,   # 消息
    'result': {stock: {start_time, end_time}}  # 下载详情
  }
        """
    )
    parser.add_argument("--host", help="服务端地址 (默认: 环境变量 XTQUANT_REMOTE_HOST 或 localhost)")
    parser.add_argument("--port", type=int, help="服务端端口 (默认: 环境变量 XTQUANT_REMOTE_PORT 或 18812)")
    parser.add_argument("--secret", help="认证密钥 (默认: 环境变量 XTQUANT_CLIENT_SECRET)")
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
        # 下载数据
        print(f"正在下载历史数据...")
        print(f"  股票代码: {', '.join(stock_codes)}")
        print(f"  K线周期: {args.period}")
        print(f"  日期范围: {args.start} ~ {args.end}")
        print()

        # 使用服务端封装的方法，直接返回状态和结果
        result = xt.download_history_data2(
            stock_list=stock_codes,
            period=args.period,
            start_time=args.start,
            end_time=args.end
        )

        # 解析结果
        finished = result.get('finished', 0)
        total = result.get('total', 0)
        done = result.get('done', False)
        message = result.get('message', '')
        detail = result.get('result', {})

        # 显示进度
        if total > 0:
            percent = finished / total * 100
            print(f"  下载进度: {finished}/{total} ({percent:.1f}%)")

        # 显示状态
        if done:
            print(f"\n✓ 下载完成！")
            if message:
                print(f"  消息: {message}")
        else:
            print(f"\n⚠ 下载可能未完成")

        # 显示详情
        if detail:
            print(f"{'='*60}")
            print("下载详情：")
            for stock_code, info in detail.items():
                start = info.get('start_time', 'N/A')
                end = info.get('end_time', 'N/A')
                print(f"  {stock_code}: {start} ~ {end}")
            print(f"{'='*60}")

        print()
        print("验证数据:")
        print(f"  python examples/get_market_data_ex.py --host {args.host} --codes \"{args.codes}\" --period {args.period}")

    finally:
        xt.close()
        print("\n连接已关闭")


if __name__ == "__main__":
    main()
