#!/usr/bin/env python3
"""
查询账户持仓示例

展示如何通过 xtquant-rpyc 查询交易账户的持仓信息。

注意:
  - 需要先在 Windows 上安装并运行迅投极速交易客户端
  - 需要提供客户端的 userdata 路径

环境变量:
  XTQUANT_REMOTE_HOST     - 服务端地址
  XTQUANT_REMOTE_PORT     - 服务端端口
  XTQUANT_CLIENT_SECRET   - 认证密钥
  XTQUANT_ACCOUNT_ID      - 资金账号
  XTQUANT_USERDATA_PATH   - 迅投QMT客户端 userdata_mini 目录路径

使用示例:
    # 使用环境变量配置（推荐）
    export XTQUANT_REMOTE_HOST="192.168.1.100"
    export XTQUANT_ACCOUNT_ID="12345678"
    export XTQUANT_USERDATA_PATH="C:\\迅投QMT交易端\\userdata_mini"
    python examples/query_positions.py

    # 命令行参数（覆盖环境变量）
    python examples/query_positions.py --account-id "12345678" --path "C:\\迅投QMT交易端\\userdata_mini"

    # 查询信用账户持仓
    python examples/query_positions.py --account-type CREDIT
"""

import argparse
import os
import time
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
  - path 参数是迅投QMT客户端的 userdata_mini 目录路径
  - 资金账号需要与服务端配置的券商账户一致
  - 交易功能需要在 Windows 服务端正确配置券商接口
        """
    )
    parser.add_argument("--host", help="服务端地址 (默认: 环境变量 XTQUANT_REMOTE_HOST 或 localhost)")
    parser.add_argument("--port", type=int, help="服务端端口 (默认: 环境变量 XTQUANT_REMOTE_PORT 或 18812)")
    parser.add_argument("--secret", help="认证密钥 (默认: 环境变量 XTQUANT_CLIENT_SECRET)")
    parser.add_argument("--account-id", help="资金账号 (默认: 环境变量 XTQUANT_ACCOUNT_ID)")
    parser.add_argument("--account-type", default="STOCK",
                        choices=list(ACCOUNT_TYPES.keys()),
                        help=f"账户类型 (默认: STOCK)")
    parser.add_argument("--path", help="迅投QMT客户端 userdata_mini 目录路径 (默认: 环境变量 XTQUANT_USERDATA_PATH)")

    args = parser.parse_args()

    # 从环境变量读取私密配置
    account_id = args.account_id or os.environ.get("XTQUANT_ACCOUNT_ID")
    userdata_path = args.path or os.environ.get("XTQUANT_USERDATA_PATH")

    if not account_id:
        print("错误: 必须提供资金账号")
        print("  方式1: 设置环境变量 XTQUANT_ACCOUNT_ID")
        print("  方式2: 使用 --account-id 参数")
        return

    if not userdata_path:
        print("错误: 必须提供 userdata_mini 目录路径")
        print("  方式1: 设置环境变量 XTQUANT_USERDATA_PATH")
        print("  方式2: 使用 --path 参数")
        print("  示例: --path \"C:\\\\迅投QMT交易端\\\\userdata_mini\"")
        return

    # 连接服务端（支持环境变量）
    trader = None
    host = args.host  # None 时 XtQuantRemote 会自动读取环境变量
    port = args.port  # None 时 XtQuantRemote 会自动读取环境变量
    print(f"正在连接 {host or '环境变量配置'}:{port or '环境变量配置'}...")
    xt = XtQuantRemote(
        host=host,
        port=port,
        client_secret=args.secret  # None 时自动读取环境变量
    )

    try:
        # 创建交易实例（使用时间戳生成唯一 session_id）
        session_id = int(time.time())
        print(f"正在创建交易实例...")
        print(f"  路径: {userdata_path}")
        print(f"  会话ID: {session_id}")
        trader = xt.xttrader.XtQuantTrader(userdata_path, session_id)

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

        print(f"\n正在查询持仓...")
        print(f"  资金账号: {account_id}")
        print(f"  账户类型: {ACCOUNT_TYPES.get(args.account_type, args.account_type)}")

        # 查询持仓
        positions = trader.query_stock_positions(account)

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
        if trader:
            try:
                trader.stop()
            except:
                pass
        xt.close()
        print("\n连接已关闭")


if __name__ == "__main__":
    main()
