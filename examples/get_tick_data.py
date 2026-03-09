#!/usr/bin/env python3
"""
获取实时行情示例

展示如何通过 xqshare 获取股票的实时tick数据。

使用示例:
    # 获取单只股票实时行情
    python examples/get_tick_data.py --host 192.168.1.100 --codes "000001.SZ"

    # 获取多只股票实时行情
    python examples/get_tick_data.py --host 192.168.1.100 --codes "000001.SZ,600000.SH,000002.SZ"
"""

import argparse
import os
from xqshare import XtQuantRemote


def format_tick_info(code: str, tick: dict) -> str:
    """格式化tick数据为可读字符串"""
    from datetime import datetime

    lines = [f"\n{'='*60}"]
    lines.append(f"股票代码: {code}")
    lines.append(f"{'='*60}")

    # 时间信息
    timetag = tick.get('timetag', 0) or tick.get('time', 0)
    if timetag:
        try:
            dt = datetime.fromtimestamp(timetag / 1000)
            lines.append(f"更新时间: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        except:
            lines.append(f"时间戳: {timetag}")

    # 价格信息（需要手动计算涨跌）
    last_price = tick.get('lastPrice', 0) or 0
    last_close = tick.get('lastClose', 0) or 0

    lines.append(f"\n【价格】")
    lines.append(f"  最新价: {last_price:.3f}")
    lines.append(f"  昨收价: {last_close:.3f}")
    lines.append(f"  今开盘: {tick.get('open', 0) or 0:.3f}")
    lines.append(f"  最高价: {tick.get('high', 0) or 0:.3f}")
    lines.append(f"  最低价: {tick.get('low', 0) or 0:.3f}")

    # 涨跌（手动计算）
    lines.append(f"\n【涨跌】")
    if last_close > 0:
        chg = last_price - last_close
        chg_ratio = chg / last_close
        chg_sign = "+" if chg >= 0 else ""
        lines.append(f"  涨跌额: {chg_sign}{chg:.3f}")
        lines.append(f"  涨跌幅: {chg_sign}{chg_ratio * 100:.2f}%")
    else:
        lines.append(f"  涨跌额: -")
        lines.append(f"  涨跌幅: -")

    # 成交信息
    # volume: 成交总量（手）
    # pvolume: 原始成交总量（股）= volume * 100
    # amount: 成交额
    lines.append(f"\n【成交】")
    volume = tick.get('volume', 0) or 0  # 手
    amount = tick.get('amount', 0) or 0
    pvolume = tick.get('pvolume', 0) or 0  # 股
    lines.append(f"  成交量: {pvolume:,} 股 ({volume:,} 手)")
    lines.append(f"  成交额: {amount:,.2f} 元")

    # 五档行情
    lines.append(f"\n【五档】")
    bid_prices = tick.get('bidPrice', []) or []
    bid_volumes = tick.get('bidVol', []) or []
    ask_prices = tick.get('askPrice', []) or []
    ask_volumes = tick.get('askVol', []) or []

    lines.append(f"  档位    买量      买价      卖价      卖量")
    lines.append("  " + "-" * 48)
    for i in range(5):
        bid_p = f"{bid_prices[i]:.3f}" if i < len(bid_prices) and bid_prices[i] else "-"
        bid_v = f"{int(bid_volumes[i]):,}" if i < len(bid_volumes) and bid_volumes[i] else "-"
        ask_p = f"{ask_prices[i]:.3f}" if i < len(ask_prices) and ask_prices[i] else "-"
        ask_v = f"{int(ask_volumes[i]):,}" if i < len(ask_volumes) and ask_volumes[i] else "-"
        lines.append(f"   {i+1}     {bid_v:>8}  {bid_p:>8}  {ask_p:>8}  {ask_v:>8}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="获取股票实时tick数据",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
输出说明:
  最新价   - 当前最新成交价
  涨跌额   - 相对昨收价的涨跌金额
  涨跌幅   - 相对昨收价的涨跌百分比
  成交量   - 当日累计成交量（股）
  成交额   - 当日累计成交金额（元）
  五档行情 - 买卖盘口五档委托价格和数量
        """
    )
    parser.add_argument("--host", help="服务端地址 (默认: 环境变量 XQSHARE_REMOTE_HOST 或 localhost)")
    parser.add_argument("--port", type=int, help="服务端端口 (默认: 环境变量 XQSHARE_REMOTE_PORT 或 18812)")
    parser.add_argument("--secret", help="认证密钥 (默认: 环境变量 XQSHARE_CLIENT_SECRET)")
    parser.add_argument("--codes", required=True, help="股票代码，逗号分隔 (如: 000001.SZ,600000.SH)")

    args = parser.parse_args()

    # 解析股票代码
    stock_codes = [code.strip() for code in args.codes.split(",")]

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
        # 获取tick数据
        print(f"正在获取实时行情...")
        print(f"  股票代码: {', '.join(stock_codes)}")

        ticks = xt.xtdata.get_full_tick(stock_codes)

        # 输出结果
        if ticks:
            for code, tick in ticks.items():
                print(format_tick_info(code, tick))
        else:
            print("\n未获取到数据，请检查股票代码是否正确")

    finally:
        xt.close()
        print("\n连接已关闭")


if __name__ == "__main__":
    main()
