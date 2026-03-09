"""
命令行工具共享模块

提供连接管理、参数解析、输出格式化等共享功能。
"""

import os
import json
import ast
import argparse
from pprint import pprint
from contextlib import contextmanager

# 环境变量名
ENV_HOST = "XQSHARE_REMOTE_HOST"
ENV_PORT = "XQSHARE_REMOTE_PORT"
ENV_SECRET = "XQSHARE_CLIENT_SECRET"
ENV_CLIENT_ID = "XQSHARE_CLIENT_ID"


@contextmanager
def create_client(host=None, port=None, secret=None, client_id=None, quiet=True):
    """创建客户端连接

    Args:
        quiet: 是否禁用控制台日志（默认 True）
    """
    if quiet:
        # 在导入前设置静默模式
        from xqshare.client import set_quiet_mode
        set_quiet_mode(True)

    from xqshare import XtQuantRemote

    h = host or os.environ.get(ENV_HOST, "localhost")
    p = port or int(os.environ.get(ENV_PORT, "18812"))
    s = secret or os.environ.get(ENV_SECRET)
    cid = client_id or os.environ.get(ENV_CLIENT_ID, "client-standard")

    xt = XtQuantRemote(host=h, port=p, client_id=cid, client_secret=s)
    try:
        yield xt
    finally:
        xt.close()


def parse_kv_args(args_list):
    """解析 --key value 格式的参数"""
    params = {}
    i = 0
    while i < len(args_list):
        arg = args_list[i]
        if arg.startswith('--'):
            key = arg[2:]
            # 将连字符转换为下划线，匹配 Python 函数参数命名
            key = key.replace('-', '_')
            if i + 1 < len(args_list) and not args_list[i + 1].startswith('--'):
                params[key] = args_list[i + 1]
                i += 2
            else:
                params[key] = True
        else:
            i += 1
    return params


def preprocess_params(params):
    """预处理复杂参数（JSON/Python 字面量反序列化）"""
    for key, value in params.items():
        if not isinstance(value, str):
            continue

        # 尝试解析为 Python 字面量（列表、字典、数字等）
        if value.startswith('[') or value.startswith('{'):
            try:
                params[key] = ast.literal_eval(value)
                continue
            except (ValueError, SyntaxError):
                pass

        # 尝试解析为 JSON
        if value.startswith('{'):
            try:
                params[key] = json.loads(value)
            except json.JSONDecodeError:
                pass

    # StockAccount 参数特殊处理
    if 'account' in params and isinstance(params['account'], dict):
        try:
            from xtquant.xttype import StockAccount
            params['account'] = StockAccount(**params['account'])
        except Exception:
            pass

    return params


def format_output(result, limit=None):
    """根据返回类型自动格式化输出

    Args:
        result: API 返回结果
        limit: 列表/元组输出数量限制，None 表示不限制
    """
    import pandas as pd

    if result is None:
        print("None")
    elif isinstance(result, pd.DataFrame):
        # DataFrame 输出
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        print(result.to_string())
    elif isinstance(result, dict):
        # 检查是否是 {stock: DataFrame} 格式
        has_dataframe = any(isinstance(v, pd.DataFrame) for v in result.values())
        if has_dataframe:
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', None)
            for key, value in result.items():
                print(f"\n=== {key} ===")
                if isinstance(value, pd.DataFrame):
                    print(value.to_string())
                else:
                    pprint(value)
        else:
            pprint(result)
    elif isinstance(result, (list, tuple)):
        total = len(result)
        if limit is not None and total > limit:
            display_data = result[:limit]
            _print_list(display_data)
            print(f"\n# 共 {total} 条，已显示前 {limit} 条")
        else:
            _print_list(result)
            if total > 10:
                print(f"\n# 共 {total} 条")
    else:
        # 单个对象，尝试显示属性
        _print_object(result)


def _print_list(items):
    """打印列表，处理对象类型"""
    for i, item in enumerate(items, 1):
        if hasattr(item, '__dict__') or hasattr(item, '__slots__'):
            # 是一个对象，显示属性
            print(f"[{i}] {_format_object(item)}")
        else:
            print(f"[{i}] {item}")


def _print_object(obj):
    """打印单个对象"""
    if hasattr(obj, '__dict__') or hasattr(obj, '__slots__'):
        pprint(_format_object(obj))
    else:
        pprint(obj)


def _format_object(obj):
    """将对象转换为字典格式"""
    result = {}
    # 使用 dir() 遍历所有属性
    for attr in dir(obj):
        if attr.startswith('_'):
            continue
        try:
            value = getattr(obj, attr)
            # 排除方法和函数
            if callable(value):
                continue
            result[attr] = value
        except Exception:
            pass
    return result if result else str(obj)


def add_global_args(parser):
    """添加全局参数"""
    parser.add_argument("--host", help="服务端地址，可通过 XQSHARE_REMOTE_HOST 环境变量设置")
    parser.add_argument("--port", type=int, help="服务端端口，可通过 XQSHARE_REMOTE_PORT 环境变量设置")
    parser.add_argument("--secret", help="认证密钥，可通过 XQSHARE_CLIENT_SECRET 环境变量设置")
    parser.add_argument("--client-id", dest="client_id", help="客户端标识，可通过 XQSHARE_CLIENT_ID 环境变量设置")
    parser.add_argument("--limit", "-n", type=int, default=50, help="列表输出数量限制 (默认: 50，0 表示不限制)")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细日志")
    return parser


def add_trader_args(parser):
    """添加交易相关参数"""
    parser.add_argument("--userdata-path", help="QMT客户端 userdata_mini 目录路径 (环境变量: QMT_USERDATA_PATH)")
    parser.add_argument("--account-id", help="资金账号 (环境变量: QMT_ACCOUNT_ID)")
    parser.add_argument("--account-type", default="STOCK", choices=["STOCK", "CREDIT", "FUTURE", "HUGANGTONG", "SHENGANGTONG"],
                        help="账户类型 (默认: STOCK)")
    return parser


def create_trader(xt, userdata_path, account_id, account_type):
    """创建交易实例

    Args:
        xt: XtQuantRemote 实例
        userdata_path: userdata_mini 目录路径
        account_id: 资金账号
        account_type: 账户类型

    Returns:
        (trader, account) 元组
    """
    import time

    # 从环境变量获取默认值
    if not userdata_path:
        import os
        userdata_path = os.environ.get("QMT_USERDATA_PATH")
    if not account_id:
        import os
        account_id = os.environ.get("QMT_ACCOUNT_ID")

    if not userdata_path:
        raise ValueError("必须提供 userdata_path 参数或设置 QMT_USERDATA_PATH 环境变量")
    if not account_id:
        raise ValueError("必须提供 account_id 参数或设置 QMT_ACCOUNT_ID 环境变量")

    # 创建交易实例
    session_id = int(time.time())
    trader = xt.xttrader.XtQuantTrader(userdata_path, session_id)
    trader.start()

    # 创建账户对象
    account = xt.xttype.StockAccount(account_id, account_type)

    # 连接交易服务器
    result = trader.connect()
    if result != 0:
        error_codes = {
            -1: "交易服务器未连接",
            -2: "账号未登录",
            -3: "请求超时",
            -4: "资金账号不存在",
        }
        raise ConnectionError(f"连接失败: {error_codes.get(result, f'错误码 {result}')}")

    return trader, account
