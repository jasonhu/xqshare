#!/usr/bin/env python3
"""
获取实时行情示例

展示如何通过 xtquant-rpyc 获取股票的实时tick数据。

使用示例:
    # 获取单只股票实时行情
    python examples/get_tick_data.py --host 192.168.1.100 --codes "000001.SZ"

    # 获取多只股票实时行情
    python examples/get_tick_data.py --host 192.168.1.100 --codes "000001.SZ,600000.SH,000002.SZ"
"""

import argparse
from xtquant_rpyc import XtQuantRemote


def format_tick_info(code: str, tick: dict) -> str:
    """格式化tick数据为可读字符串"""
    lines = [f"\n{'='*60}"]
    lines.append(f"股票代码: {code}")
    lines.append(f"{'='*60}")

    # 时间信息
    timetag = tick.get('timetag', 0)
    if timetag:
        from datetime import datetime
        try:
            dt = datetime.fromtimestamp(timetag / 1000)
            lines.append(f"时间戳: {dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} ({timetag})")
        except:
            lines.append(f"时间戳: {timetag}")

    # 价格信息
    lines.append(f"\n【价格信息】")
    if tick.get('lastPrice'):
        lines.append(f"  最新价: {tick.get('lastPrice', 0):.3f}")
    if tick.get('lastClose'):
        lines.append(f"  昨收价: {tick.get('lastClose', 0):.3f}")
    if tick.get('open'):
        lines.append(f"  开盘价: {tick.get('open', 0):.3f}")
    if tick.get('high'):
        lines.append(f"  最高价: {tick.get('high', 0):.3f}")
    if tick.get('low'):
        lines.append(f"  最低价: {tick.get('low', 0):.3f}")

    # 涨跌信息
    lines.append(f"\n【涨跌信息】")
    chg = tick.get('chg', 0) or 0
    chg_ratio = tick.get('chgRatio', 0) or 0
    chg_sign = "+" if chg >= 0 else ""
    lines.append(f"  涨跌额: {chg_sign}{chg:.3f}")
    lines.append(f"  涨跌幅: {chg_sign}{chg_ratio * 100:.2f}%")

    # 成交信息
    lines.append(f"\n【成交信息】")
    volume = tick.get('volume', 0) or 0
    amount = tick.get('amount', 0) or 0
    pvolume = tick.get('pvolume', 0) or 0
    lines.append(f"  成交量: {volume:,} 股")
    lines.append(f"  成交额: {amount:,.2f} 元")
    lines.append(f"  成交笔数: {pvolume:,}")

    # 状态信息
    lines.append(f"\n【状态信息】")
    stock_status = tick.get('stockStatus', 0)
    open_int = tick.get('openInt', 0)
    lines.append(f"  股票状态: {stock_status}")
    lines.append(f"  持仓量: {open_int}")

    # 结算价（期货）
    settlement = tick.get('settlementPrice', 0)
    last_settlement = tick.get('lastSettlementPrice', 0)
    if settlement:
        lines.append(f"  结算价: {settlement:.3f}")
    if last_settlement:
        lines.append(f"  昨结算: {last_settlement:.3f}")

    # 五档行情
    lines.append(f"\n【五档行情】")
    # 五档数据是数组格式: [档位1, 档位2, 档位3, 档位4, 档位5]
    bid_prices = tick.get('bidPrice', []) or []
    bid_volumes = tick.get('bidVol', []) or []
    ask_prices = tick.get('askPrice', []) or []
    ask_volumes = tick.get('askVol', []) or []

    lines.append(f"  {'档位':^4} {'买入量':^10} {'买入价':^10} {'卖出价':^10} {'卖出量':^10}")
    lines.append("  " + "-" * 52)
    for i in range(5):
        bid_p = f"{bid_prices[i]:.3f}" if i < len(bid_prices) and bid_prices[i] else "-"
        bid_v = f"{int(bid_volumes[i]):,}" if i < len(bid_volumes) and bid_volumes[i] else "-"
        ask_p = f"{ask_prices[i]:.3f}" if i < len(ask_prices) and ask_prices[i] else "-"
        ask_v = f"{int(ask_volumes[i]):,}" if i < len(ask_volumes) and ask_volumes[i] else "-"
        lines.append(f"  {i+1:^4} {bid_v:^10} {bid_p:^10} {ask_p:^10} {ask_v:^10}")

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
    parser.add_argument("--host", required=True, help="服务端地址")
    parser.add_argument("--port", type=int, default=18812, help="服务端端口 (默认: 18812)")
    parser.add_argument("--secret", default="", help="认证密钥")
    parser.add_argument("--codes", required=True, help="股票代码，逗号分隔 (如: 000001.SZ,600000.SH)")

    args = parser.parse_args()

    # 解析股票代码
    stock_codes = [code.strip() for code in args.codes.split(",")]

    # 连接服务端
    print(f"正在连接 {args.host}:{args.port}...")
    xt = XtQuantRemote(
        host=args.host,
        port=args.port,
        client_secret=args.secret
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
