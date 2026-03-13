#!/usr/bin/env python3
"""
查询账户持仓示例

展示如何通过 xqshare 查询交易账户的持仓、委托、成交信息。

注意:
  - 需要先在 Windows 上安装并运行 QMT 交易客户端
  - 需要提供客户端的 userdata 路径

环境变量:
  XQSHARE_REMOTE_HOST     - 服务端地址
  XQSHARE_REMOTE_PORT     - 服务端端口
  XQSHARE_CLIENT_SECRET   - 认证密钥
  QMT_ACCOUNT_ID      - 资金账号
  QMT_USERDATA_PATH   - QMT客户端 userdata_mini 目录路径

使用示例:
    # 使用环境变量配置（推荐）
    export XQSHARE_REMOTE_HOST="192.168.1.100"
    export QMT_ACCOUNT_ID="12345678"
    export QMT_USERDATA_PATH="C:\\QMT\\userdata_mini"
    python examples/query_positions.py

    # 命令行参数（覆盖环境变量）
    python examples/query_positions.py --account-id "12345678" --path "C:\\QMT\\userdata_mini"

    # 查询信用账户持仓
    python examples/query_positions.py --account-type CREDIT
"""

import argparse
import os
import time
from xqshare import XtQuantRemote


# 账户类型映射
ACCOUNT_TYPES = {
    "STOCK": "股票",
    "CREDIT": "信用",
    "FUTURE": "期货",
    "HUGANGTONG": "沪港通",
    "SHENGANGTONG": "深港通",
}

# 委托类型映射
ORDER_TYPES = {
    23: "买入",
    24: "卖出",
}


def print_asset_info(asset):
    """输出账户资产信息"""
    if asset is None:
        return

    cash = getattr(asset, 'cash', 0) or 0
    frozen_cash = getattr(asset, 'frozen_cash', 0) or 0
    market_value = getattr(asset, 'market_value', 0) or 0
    total_asset = getattr(asset, 'total_asset', 0) or 0
    fetch_balance = getattr(asset, 'fetch_balance', 0) or 0

    print()
    print("=" * 80)
    print(f"{'账户资产':^78}")
    print("-" * 80)
    print(f"  可用资金: {cash:>12,.2f} 元    冻结资金: {frozen_cash:>12,.2f} 元")
    print(f"  持仓市值: {market_value:>12,.2f} 元    总资产:   {total_asset:>12,.2f} 元")
    print(f"  可取资金: {fetch_balance:>12,.2f} 元")
    print("=" * 80)


def print_positions_table(positions):
    """以表格方式输出持仓"""
    print()
    print("=" * 108)
    print(f"{'持仓记录':^106}")
    print("-" * 108)

    if not positions:
        print(f"{'无持仓数据':^106}")
        print("=" * 108)
        return

    # 表头
    print(f"{'序号':^4} | {'股票代码':^10} | {'名称':^6} | {'持仓':>8} | {'可用':>8} | {'成本':>8} | {'现价':>8} | {'市值':>12} | {'盈亏':>10} | {'盈亏%':>7}")
    print("-" * 108)

    total_market_value = 0.0
    total_profit = 0.0

    for i, pos in enumerate(positions, 1):
        stock_code = getattr(pos, 'stock_code', 'N/A')
        stock_name = getattr(pos, 'instrument_name', '') or ''
        volume = getattr(pos, 'volume', 0) or 0
        can_use = getattr(pos, 'can_use_volume', 0) or 0
        avg_price = getattr(pos, 'open_price', 0) or getattr(pos, 'avg_price', 0) or 0
        last_price = getattr(pos, 'last_price', 0) or 0
        market_value = round(float(getattr(pos, 'market_value', 0) or 0), 2)
        # 计算盈亏（XtPosition 没有 float_profit 字段）
        cost = volume * avg_price
        profit = round(market_value - cost, 2)
        profit_rate = getattr(pos, 'profit_rate', 0) or 0

        # 截断股票名称
        stock_name_display = stock_name[:4].ljust(4) if len(stock_name) >= 4 else stock_name.ljust(4)

        # 盈亏格式化（自动带正负号）
        profit_str = f"{profit:+,.0f}"
        rate_str = f"{profit_rate*100:+.1f}%"

        print(f"{i:^4} | {stock_code:^10} | {stock_name_display:4} | {volume:>8,} | {can_use:>8,} | {avg_price:>8.3f} | {last_price:>8.3f} | {market_value:>12,.0f} | {profit_str:>10} | {rate_str:>8}")

        total_market_value += market_value
        total_profit += profit

    print("-" * 108)

    # 汇总行
    total_profit_str = f"{total_profit:+,.0f}"
    print(f"{'合计':^4} | {'':^10} | {'':^6} | {'':>8} | {'':>8} | {'':>8} | {'':>8} | {total_market_value:>12,.0f} | {total_profit_str:>10} |")
    print("=" * 108)
    print(f"\n持仓: {len(positions)} 只 | 市值: {total_market_value:,.0f} 元 | 盈亏: {total_profit_str} 元")


def print_orders_table(orders):
    """以表格方式输出委托单"""
    print()
    print("=" * 130)
    print(f"{'委托记录':^128}")
    print("-" * 130)

    if not orders:
        print(f"{'无委托数据':^128}")
        print("=" * 130)
        return

    # 表头
    print(f"{'序号':^4} | {'委托编号':^12} | {'股票代码':^10} | {'方向':^4} | {'委托价':>8} | {'委托量':>8} | {'成交价':>8} | {'成交量':>8} | {'状态':^16} | {'委托时间':^12}")
    print("-" * 130)

    for i, order in enumerate(orders, 1):
        order_id = getattr(order, 'order_id', 'N/A')
        stock_code = getattr(order, 'stock_code', 'N/A')
        order_type = getattr(order, 'order_type', 0)
        price = getattr(order, 'price', 0) or 0
        order_volume = getattr(order, 'order_volume', 0) or 0
        traded_price = getattr(order, 'traded_price', 0) or 0
        traded_volume = getattr(order, 'traded_volume', 0) or 0
        status_msg = getattr(order, 'status_msg', '') or str(getattr(order, 'order_status', '?'))
        order_time = getattr(order, 'order_time', '')

        direction = ORDER_TYPES.get(order_type, f"类型{order_type}")
        status_display = status_msg[:14] if len(status_msg) > 14 else status_msg

        print(f"{i:^4} | {str(order_id):^12} | {stock_code:^10} | {direction:^4} | {price:>8.3f} | {order_volume:>8,} | {traded_price:>8.3f} | {traded_volume:>8,} | {status_display:^16} | {order_time:^12}")

    print("=" * 130)
    print(f"委托: {len(orders)} 笔")


def print_trades_table(trades):
    """以表格方式输出成交单"""
    print()
    print("=" * 110)
    print(f"{'成交记录':^108}")
    print("-" * 110)

    if not trades:
        print(f"{'无成交数据':^108}")
        print("=" * 110)
        return

    # 表头
    print(f"{'序号':^4} | {'成交编号':^12} | {'股票代码':^10} | {'方向':^4} | {'成交价':>8} | {'成交量':>8} | {'成交金额':>12} | {'成交时间':^14}")
    print("-" * 110)

    total_amount = 0.0

    for i, trade in enumerate(trades, 1):
        traded_id = getattr(trade, 'traded_id', 'N/A')
        stock_code = getattr(trade, 'stock_code', 'N/A')
        order_type = getattr(trade, 'order_type', 0)
        traded_price = getattr(trade, 'traded_price', 0) or 0
        traded_volume = getattr(trade, 'traded_volume', 0) or 0
        traded_amount = getattr(trade, 'traded_amount', 0) or 0
        traded_time = getattr(trade, 'traded_time', '')

        direction = ORDER_TYPES.get(order_type, f"类型{order_type}")
        total_amount += traded_amount

        print(f"{i:^4} | {str(traded_id):^12} | {stock_code:^10} | {direction:^4} | {traded_price:>8.3f} | {traded_volume:>8,} | {traded_amount:>12,.2f} | {traded_time:^14}")

    print("-" * 110)
    print(f"{'合计':^4} | {'':^12} | {'':^10} | {'':^4} | {'':>8} | {'':>8} | {total_amount:>12,.2f} |")
    print("=" * 110)
    print(f"成交: {len(trades)} 笔 | 总金额: {total_amount:,.2f} 元")


def main():
    parser = argparse.ArgumentParser(
        description="查询账户持仓、委托、成交信息",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
账户类型 (account-type):
  STOCK       - 普通股票账户
  CREDIT      - 信用账户（两融）
  FUTURE      - 期货账户
  HUGANGTONG  - 沪港通
  SHENGANGTONG - 深港通

注意:
  - path 参数是 QMT 客户端的 userdata_mini 目录路径
  - 资金账号需要与服务端配置的券商账户一致
  - 交易功能需要在 Windows 服务端正确配置券商接口
        """
    )
    parser.add_argument("--host", help="服务端地址 (默认: 环境变量 XQSHARE_REMOTE_HOST 或 localhost)")
    parser.add_argument("--port", type=int, help="服务端端口 (默认: 环境变量 XQSHARE_REMOTE_PORT 或 18812)")
    parser.add_argument("--secret", help="认证密钥 (默认: 环境变量 XQSHARE_CLIENT_SECRET)")
    parser.add_argument("--account-id", help="资金账号 (默认: 环境变量 QMT_ACCOUNT_ID)")
    parser.add_argument("--account-type", default="STOCK",
                        choices=list(ACCOUNT_TYPES.keys()),
                        help=f"账户类型 (默认: STOCK)")
    parser.add_argument("--path", help="QMT客户端 userdata_mini 目录路径 (默认: 环境变量 QMT_USERDATA_PATH)")

    args = parser.parse_args()

    # 从环境变量读取私密配置
    account_id = args.account_id or os.environ.get("QMT_ACCOUNT_ID")
    userdata_path = args.path or os.environ.get("QMT_USERDATA_PATH")

    if not account_id:
        print("错误: 必须提供资金账号")
        print("  方式1: 设置环境变量 QMT_ACCOUNT_ID")
        print("  方式2: 使用 --account-id 参数")
        return

    if not userdata_path:
        print("错误: 必须提供 userdata_mini 目录路径")
        print("  方式1: 设置环境变量 QMT_USERDATA_PATH")
        print("  方式2: 使用 --path 参数")
        print("  示例: --path \"C:\\\\QMT\\\\userdata_mini\"")
        return

    # 连接服务端（支持环境变量）
    trader = None
    host_display = args.host or os.environ.get("XQSHARE_REMOTE_HOST", "localhost")
    port_display = args.port or int(os.environ.get("XQSHARE_REMOTE_PORT", "18812"))
    print(f"正在连接 {host_display}:{port_display}...")
    xt = XtQuantRemote(
        host=args.host,
        port=args.port,
        client_secret=args.secret
    )

    try:
        # 创建交易实例
        print(f"正在创建交易实例...")
        print(f"  路径: {userdata_path}")
        trader = xt.create_trader(userdata_path)

        # 启动交易线程
        print(f"正在启动交易线程...")
        trader.start()

        # 创建账户对象
        account = xt.xttype.StockAccount(account_id, args.account_type)

        # 连接交易服务器
        print(f"正在连接交易服务器...")
        connect_result = trader.connect()
        if connect_result != 0:
            error_codes = {
                -1: "交易服务器未连接",
                -2: "账号未登录",
                -3: "请求超时",
                -4: "资金账号不存在",
            }
            print(f"连接失败: {error_codes.get(connect_result, f'错误码 {connect_result}')}")
            return

        print(f"\n正在查询账户信息...")
        print(f"  资金账号: {account_id}")
        print(f"  账户类型: {ACCOUNT_TYPES.get(args.account_type, args.account_type)}")

        # 查询资产
        asset = trader.query_stock_asset(account)

        # 查询持仓
        positions = trader.query_stock_positions(account)

        # 查询委托
        orders = trader.query_stock_orders(account)

        # 查询成交
        trades = trader.query_stock_trades(account)

        # 输出资产信息
        print_asset_info(asset)

        # 以表格方式输出持仓
        print_positions_table(positions)

        # 以表格方式输出委托
        print_orders_table(orders)

        # 以表格方式输出成交
        print_trades_table(trades)

    except Exception as e:
        error_msg = str(e)
        if "connect" in error_msg.lower() or "连接" in error_msg:
            print(f"\n交易账户连接失败，请检查:")
            print(f"  1. 资金账号是否正确")
            print(f"  2. 服务端是否已配置券商接口")
            print(f"  3. 券商客户端是否已登录")
        raise

    finally:
        if trader:
            try:
                trader.stop()
            except:
                pass
        xt.close()
        print("\n连接已关闭")


if __name__ == "__main__":
    main()
