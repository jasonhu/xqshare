#!/usr/bin/env python3
"""
订阅实时行情推送示例

展示如何通过 xtquant-rpyc 订阅股票实时行情推送。

使用示例:
    # 订阅60秒（默认）
    python examples/subscribe_quote.py --host 192.168.1.100 --codes "000001.SZ,600000.SH"

    # 订阅120秒
    python examples/subscribe_quote.py --host 192.168.1.100 --codes "000001.SZ" --duration 120

    # 持续订阅（Ctrl+C 停止）
    python examples/subscribe_quote.py --host 192.168.1.100 --codes "000001.SZ" --duration 0
"""

import argparse
import time
import signal
import sys
from datetime import datetime
from xtquant_rpyc import XtQuantRemote

# 全局变量用于优雅退出
running = True
subscriptions = []


def signal_handler(signum, frame):
    """信号处理器"""
    global running
    print("\n\n正在停止订阅...")
    running = False


def on_quote(stock_code: str, data: dict):
    """行情推送回调函数"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 提取关键数据
    last_price = data.get('lastPrice', 0) or 0
    chg_ratio = data.get('chgRatio', 0) or 0
    volume = data.get('volume', 0) or 0
    amount = data.get('amount', 0) or 0

    # 涨跌幅符号
    chg_sign = "+" if chg_ratio >= 0 else ""

    # 格式化输出
    print(f"[{timestamp}] {stock_code:12s} | "
          f"最新价: {last_price:8.3f} | "
          f"涨跌幅: {chg_sign}{chg_ratio * 100:6.2f}% | "
          f"成交量: {volume:>12,} | "
          f"成交额: {amount:>15,.0f}")


def main():
    parser = argparse.ArgumentParser(
        description="订阅股票实时行情推送",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
说明:
  --duration 0  表示持续订阅，按 Ctrl+C 停止
  --duration N  表示订阅 N 秒后自动停止

输出字段:
  最新价   - 当前最新成交价
  涨跌幅   - 相对昨收价的涨跌百分比
  成交量   - 当日累计成交量（股）
  成交额   - 当日累计成交金额（元）
        """
    )
    parser.add_argument("--host", required=True, help="服务端地址")
    parser.add_argument("--port", type=int, default=18812, help="服务端端口 (默认: 18812)")
    parser.add_argument("--secret", default="", help="认证密钥")
    parser.add_argument("--codes", required=True, help="股票代码，逗号分隔 (如: 000001.SZ,600000.SH)")
    parser.add_argument("--duration", type=int, default=60,
                        help="订阅时长（秒），0表示持续订阅 (默认: 60)")

    args = parser.parse_args()

    # 解析股票代码
    stock_codes = [code.strip() for code in args.codes.split(",")]

    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 连接服务端
    print(f"正在连接 {args.host}:{args.port}...")
    xt = XtQuantRemote(
        host=args.host,
        port=args.port,
        client_secret=args.secret
    )

    try:
        # 订阅行情
        print(f"正在订阅实时行情...")
        print(f"  股票代码: {', '.join(stock_codes)}")
        print(f"  订阅时长: {'持续' if args.duration == 0 else f'{args.duration}秒'}")
        print(f"\n{'='*80}")
        print(f"{'时间':^20} | {'股票代码':^12} | {'最新价':^10} | {'涨跌幅':^10} | {'成交量':^14} | {'成交额':^18}")
        print(f"{'='*80}")

        # 订阅每只股票
        for code in stock_codes:
            sub = xt.subscribe_quote(code, on_quote)
            subscriptions.append(sub)

        # 等待
        if args.duration == 0:
            # 持续订阅
            print("\n持续订阅中，按 Ctrl+C 停止...\n")
            while running:
                time.sleep(1)
        else:
            # 定时订阅
            print(f"\n订阅 {args.duration} 秒...\n")
            time.sleep(args.duration)

    finally:
        # 取消订阅
        for sub in subscriptions:
            try:
                sub.stop()
            except Exception:
                pass

        xt.close()
        print("\n\n订阅已停止，连接已关闭")


if __name__ == "__main__":
    main()
