#!/usr/bin/env python3
"""
获取全市场实时行情快照示例

通过 get_full_tick(['SH', 'SZ']) 一次性拉取沪深全市场最新 tick 快照，
过滤出沪深 A 股，计算涨跌幅并排序输出。

使用示例:
    # 涨幅榜前 20（默认）
    python examples/get_market_snapshot.py --host 192.168.1.100

    # 跌幅榜前 20
    python examples/get_market_snapshot.py --host 192.168.1.100 --sort asc

    # 输出前 50 条
    python examples/get_market_snapshot.py --host 192.168.1.100 --top 50

    # 不过滤，输出全部标的（含指数、基金、债券等）
    python examples/get_market_snapshot.py --host 192.168.1.100 --all
"""

import argparse
from xqshare import XtQuantRemote


def is_a_share(code: str) -> bool:
    """判断是否沪深 A 股（过滤掉指数、基金、债券、可转债等）"""
    if code.endswith('.SH'):
        return code.startswith(('600', '601', '603', '605', '688'))
    if code.endswith('.SZ'):
        return code.startswith(('000', '001', '002', '003', '300', '301'))
    return False


def main():
    parser = argparse.ArgumentParser(
        description="获取全市场实时行情快照",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
说明:
  get_full_tick 传入市场代码 ['SH', 'SZ'] 即可获取全市场快照，无需预先订阅。
  交易所快照 3 秒刷新一次，重复调用间隔建议不小于 3 秒。

输出字段:
  最新价   - 当前最新成交价
  涨跌幅   - 相对昨收价的涨跌百分比（get_full_tick 不直接返回，需自行计算）
  成交量   - 当日累计成交量（股，pvolume 字段）
  成交额   - 当日累计成交金额（元）
        """
    )
    parser.add_argument("--host", help="服务端地址 (默认: 环境变量 XQSHARE_REMOTE_HOST 或 localhost)")
    parser.add_argument("--port", type=int, help="服务端端口 (默认: 环境变量 XQSHARE_REMOTE_PORT 或 18812)")
    parser.add_argument("--secret", help="认证密钥 (默认: 环境变量 XQSHARE_CLIENT_SECRET)")
    parser.add_argument("--top", type=int, default=20, help="输出条数 (默认: 20)")
    parser.add_argument("--sort", choices=['desc', 'asc'], default='desc',
                        help="按涨跌幅排序：desc=涨幅榜（默认），asc=跌幅榜")
    parser.add_argument("--all", action="store_true",
                        help="不过滤，输出全部标的（默认只保留沪深 A 股）")

    args = parser.parse_args()

    # 连接服务端（支持环境变量）
    print(f"正在连接 {args.host or '环境变量配置'}:{args.port or '环境变量配置'}...")
    xt = XtQuantRemote(
        host=args.host,
        port=args.port,
        client_secret=args.secret
    )

    try:
        # 一次性拉取沪深全市场快照
        print("正在获取全市场行情快照...")
        snapshot = xt.xtdata.get_full_tick(['SH', 'SZ'])

        if not snapshot:
            print("\n未获取到数据。若反复为空，请确认:")
            print("  1. QMT/miniQMT 已启动并登录")
            print("  2. 可先调用 subscribe_whole_quote(['SH','SZ']) 建立全推后再试")
            return

        print(f"共获取 {len(snapshot)} 只标的")

        # 过滤 + 计算涨跌幅
        rows = []
        for code, tick in snapshot.items():
            if not args.all and not is_a_share(code):
                continue

            last_price = tick.get('lastPrice', 0) or 0
            last_close = tick.get('lastClose', 0) or 0

            # 剔除停牌/无数据（昨收或最新价为 0）
            if last_close <= 0 or last_price <= 0:
                continue

            chg_ratio = (last_price - last_close) / last_close
            rows.append({
                'code': code,
                'last_price': last_price,
                'chg_ratio': chg_ratio,
                'pvolume': tick.get('pvolume', 0) or 0,
                'amount': tick.get('amount', 0) or 0,
            })

        # 排序并取前 N
        rows.sort(key=lambda r: r['chg_ratio'], reverse=(args.sort == 'desc'))
        rows = rows[:args.top]

        # 输出
        scope = "全部标的" if args.all else "沪深A股"
        title = "涨幅榜" if args.sort == 'desc' else "跌幅榜"
        print(f"\n{'='*78}")
        print(f"{scope} {title} TOP {args.top}")
        print(f"{'='*78}")
        print(f"{'排名':>4} | {'股票代码':<10} | {'最新价':>10} | {'涨跌幅':>9} | {'成交量(股)':>14} | {'成交额(元)':>16}")
        print(f"{'-'*78}")

        for i, r in enumerate(rows, 1):
            chg_sign = "+" if r['chg_ratio'] >= 0 else ""
            print(f"{i:>4} | {r['code']:<10} | {r['last_price']:>10.3f} | "
                  f"{chg_sign}{r['chg_ratio'] * 100:>7.2f}% | "
                  f"{r['pvolume']:>14,} | {r['amount']:>16,.0f}")

    finally:
        xt.close()
        print("\n连接已关闭")


if __name__ == "__main__":
    main()
