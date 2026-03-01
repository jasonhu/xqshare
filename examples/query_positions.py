#!/usr/bin/env python3
"""
查询账户持仓示例

展示如何通过 xtquant-rpyc 查询交易账户的持仓信息。

使用示例:
    # 查询普通股票账户持仓
    python examples/query_positions.py --host 192.168.1.100 --account-id "12345678"

    # 查询信用账户持仓
    python examples/query_positions.py --host 192.168.1.100 --account-id "12345678" --account-type CREDIT

    # 查询期货账户持仓
    python examples/query_positions.py --host 192.168.1.100 --account-id "12345678" --account-type FUTURE
"""

import argparse
from xtquant_rpyc import XtQuantRemote


# 账户类型映射
ACCOUNT_TYPES = {
    "STOCK": "普通股票账户",
    "CREDIT": "信用账户（两融）",
    "FUTURE": "期货账户",
    "HUGANGTONG": "沪港通",
    "SHENGANGTONG": "深港通",
}


def format_position(pos, index: int) -> str:
    """格式化持仓信息"""
    lines = [f"\n{'='*60}"]
    lines.append(f"持仓 {index}")
    lines.append(f"{'='*60}")

    # 股票信息
    lines.append(f"股票代码: {getattr(pos, 'stock_code', 'N/A')}")

    # 持仓数量
    volume = getattr(pos, 'volume', 0) or 0
    can_use = getattr(pos, 'can_use_volume', 0) or 0
    lines.append(f"持仓数量: {volume:,} 股")
    lines.append(f"可用数量: {can_use:,} 股")

    # 价格信息
    avg_price = getattr(pos, 'avg_price', 0) or 0
    market_value = getattr(pos, 'market_value', 0) or 0
    lines.append(f"成本价: {avg_price:.3f} 元")
    lines.append(f"市值: {market_value:,.2f} 元")

    # 盈亏信息
    profit = getattr(pos, 'float_profit', 0) or 0
    profit_rate = getattr(pos, 'profit_rate', 0) or 0
    profit_sign = "+" if profit >= 0 else ""
    lines.append(f"浮动盈亏: {profit_sign}{profit:,.2f} 元")
    lines.append(f"盈亏比例: {profit_sign}{profit_rate * 100:.2f}%")

    # 冻结信息
    frozen = getattr(pos, 'frozen_volume', 0) or 0
    if frozen > 0:
        lines.append(f"冻结数量: {frozen:,} 股")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="查询账户持仓信息",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
账户类型 (account-type):
  STOCK       - 普通股票账户
  CREDIT      - 信用账户（两融）
  FUTURE      - 期货账户
  HUGANGTONG  - 沪港通
  SHENGANGTONG - 深港通

注意:
  - 资金账号需要与服务端配置的券商账户一致
  - 交易功能需要在 Windows 服务端正确配置券商接口
        """
    )
    parser.add_argument("--host", required=True, help="服务端地址")
    parser.add_argument("--port", type=int, default=18812, help="服务端端口 (默认: 18812)")
    parser.add_argument("--secret", default="", help="认证密钥")
    parser.add_argument("--account-id", required=True, help="资金账号")
    parser.add_argument("--account-type", default="STOCK",
                        choices=list(ACCOUNT_TYPES.keys()),
                        help=f"账户类型 (默认: STOCK)")

    args = parser.parse_args()

    # 连接服务端
    print(f"正在连接 {args.host}:{args.port}...")
    xt = XtQuantRemote(
        host=args.host,
        port=args.port,
        client_secret=args.secret
    )

    try:
        # 创建账户对象
        account = xt.xttype.StockAccount(args.account_id, args.account_type)

        print(f"\n正在查询持仓...")
        print(f"  资金账号: {args.account_id}")
        print(f"  账户类型: {ACCOUNT_TYPES.get(args.account_type, args.account_type)}")

        # 查询持仓
        positions = xt.xttrader.query_stock_positions(account)

        # 输出结果
        if positions:
            total_market_value = 0
            total_profit = 0

            for i, pos in enumerate(positions, 1):
                print(format_position(pos, i))
                total_market_value += getattr(pos, 'market_value', 0) or 0
                total_profit += getattr(pos, 'float_profit', 0) or 0

            # 汇总信息
            profit_sign = "+" if total_profit >= 0 else ""
            print(f"\n{'='*60}")
            print(f"持仓汇总")
            print(f"{'='*60}")
            print(f"持仓数量: {len(positions)} 只")
            print(f"总市值: {total_market_value:,.2f} 元")
            print(f"总浮动盈亏: {profit_sign}{total_profit:,.2f} 元")
        else:
            print(f"\n{'='*60}")
            print("当前账户无持仓")
            print(f"{'='*60}")

    except Exception as e:
        error_msg = str(e)
        if "connect" in error_msg.lower() or "连接" in error_msg:
            print(f"\n交易账户连接失败，请检查:")
            print(f"  1. 资金账号是否正确")
            print(f"  2. 服务端是否已配置券商接口")
            print(f"  3. 券商客户端是否已登录")
        raise

    finally:
        xt.close()
        print("\n连接已关闭")


if __name__ == "__main__":
    main()
