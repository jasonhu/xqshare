#!/usr/bin/env python3
"""
订阅全市场实时行情推送示例

通过 subscribe_whole_quote(['SH', 'SZ']) 订阅沪深全市场全推行情，
回调中维护本地快照表，主循环周期性输出吞吐统计和涨幅榜。

使用示例:
    # 订阅60秒（默认）
    python examples/subscribe_whole_market.py --host 192.168.1.100

    # 持续订阅，每5秒输出一次统计（Ctrl+C 停止）
    python examples/subscribe_whole_market.py --host 192.168.1.100 --duration 0 --interval 5

说明:
    交易时段全推数据量很大（每3秒数千只股票更新），回调函数只做数据落库，
    统计与打印在主循环中执行，避免阻塞回调线程。
"""

import argparse
import time
import signal
import threading
from xqshare import XtQuantRemote

# 全局状态
running = True
snapshot = {}          # 全市场本地快照表 {code: tick_data}
update_count = 0       # 累计收到的更新条数
batch_count = 0        # 累计收到的推送批次数
lock = threading.Lock()


def signal_handler(signum, frame):
    """信号处理器 - 优雅退出"""
    global running
    running = False
    print("\n\n正在停止订阅...")


def on_quote(datas: dict):
    """
    全推行情回调函数

    subscribe_whole_quote 回调格式: {stock1: data1, stock2: data2, ...}
    只包含有行情更新的股票（增量推送）。

    注意: 回调在 BgServingThread 中执行，这里只做落库，不做重计算/打印。
    """
    global update_count, batch_count
    if not running or not datas:
        return
    with lock:
        snapshot.update(datas)
        update_count += len(datas)
        batch_count += 1


def is_a_share(code: str) -> bool:
    """判断是否沪深 A 股（过滤掉指数、基金、债券、可转债等）"""
    if code.endswith('.SH'):
        return code.startswith(('600', '601', '603', '605', '688'))
    if code.endswith('.SZ'):
        return code.startswith(('000', '001', '002', '003', '300', '301'))
    return False


def print_stats(interval: float, last_count: int, elapsed: float):
    """输出吞吐统计 + 当前涨幅榜 TOP 5"""
    with lock:
        total = update_count
        batches = batch_count
        # 复制一份用于计算涨跌幅（避免长时间持锁）
        snap = dict(snapshot)

    delta = total - last_count
    print(f"\n[{time.strftime('%H:%M:%S')}] "
          f"快照表: {len(snap)} 只 | "
          f"本周期更新: {delta} 条 ({delta / interval:.0f} 条/秒) | "
          f"累计: {total} 条 / {batches} 批次 | "
          f"已运行: {elapsed:.0f}s")

    # 涨幅榜 TOP 5（仅 A 股，剔除停牌/无数据）
    rows = []
    for code, tick in snap.items():
        if not is_a_share(code):
            continue
        last_price = tick.get('lastPrice', 0) or 0
        last_close = tick.get('lastClose', 0) or 0
        if last_close <= 0 or last_price <= 0:
            continue
        rows.append((code, last_price, (last_price - last_close) / last_close))

    rows.sort(key=lambda r: r[2], reverse=True)
    print(f"  {'涨幅榜 TOP 5':^60}")
    for code, price, ratio in rows[:5]:
        print(f"    {code:<10} 最新价: {price:>10.3f}   涨跌幅: +{ratio * 100:.2f}%")

    return total


def main():
    parser = argparse.ArgumentParser(
        description="订阅全市场实时行情推送",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
说明:
  --duration 0  表示持续订阅，按 Ctrl+C 停止
  --duration N  表示订阅 N 秒后自动停止

  交易所快照 3 秒刷新一次，盘中每批次推送数千只股票的增量更新。
        """
    )
    parser.add_argument("--host", help="服务端地址 (默认: 环境变量 XQSHARE_REMOTE_HOST 或 localhost)")
    parser.add_argument("--port", type=int, help="服务端端口 (默认: 环境变量 XQSHARE_REMOTE_PORT 或 18812)")
    parser.add_argument("--secret", help="认证密钥 (默认: 环境变量 XQSHARE_CLIENT_SECRET)")
    parser.add_argument("--duration", type=int, default=60,
                        help="订阅时长（秒），0表示持续订阅 (默认: 60)")
    parser.add_argument("--interval", type=float, default=5,
                        help="统计输出间隔（秒）(默认: 5)")

    args = parser.parse_args()

    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 连接服务端（支持环境变量）
    print(f"正在连接 {args.host or '环境变量配置'}:{args.port or '环境变量配置'}...")
    xt = XtQuantRemote(
        host=args.host,
        port=args.port,
        client_secret=args.secret
    )

    try:
        # 订阅沪深全市场全推行情
        print("正在订阅沪深全市场全推行情 ['SH', 'SZ']...")
        seq = xt.xtdata.subscribe_whole_quote(['SH', 'SZ'], callback=on_quote)
        print(f"已订阅 (seq={seq})")
        print(f"统计输出间隔: {args.interval}s，"
              f"{'持续订阅中，按 Ctrl+C 停止' if args.duration == 0 else f'{args.duration}秒后自动停止'}")

        # 主循环：周期性输出统计
        start_time = time.time()
        last_count = 0
        last_print = start_time
        while running:
            time.sleep(0.5)
            now = time.time()
            if args.duration > 0 and now - start_time >= args.duration:
                break
            if now - last_print >= args.interval:
                last_count = print_stats(args.interval, last_count, now - start_time)
                last_print = now

        # 汇总
        print(f"\n{'='*70}")
        print(f"订阅结束 | 快照表共 {len(snapshot)} 只标的 | "
              f"累计接收 {update_count} 条更新 / {batch_count} 批次")

        # 取消订阅
        print("正在取消订阅...")
        xt.xtdata.unsubscribe_quote(seq)
        print(f"已取消 (seq={seq})")

    finally:
        xt.close()
        print("连接已关闭")


if __name__ == "__main__":
    main()
