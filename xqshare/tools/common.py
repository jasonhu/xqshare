"""
命令行工具共享模块

提供连接管理、参数解析、输出格式化等共享功能。
"""

import os
import json
import ast
import argparse
from contextlib import contextmanager

# 环境变量名
ENV_HOST = "XQSHARE_REMOTE_HOST"
ENV_PORT = "XQSHARE_REMOTE_PORT"
ENV_SECRET = "XQSHARE_CLIENT_SECRET"
ENV_CLIENT_ID = "XQSHARE_CLIENT_ID"
ENV_FORMAT = "XQSHARE_FORMAT"


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


def _is_remote_object(obj):
    """判断是否为 RPyC 远程对象（netref）

    Args:
        obj: 待检测对象

    Returns:
        bool: 如果是远程对象返回 True
    """
    module = type(obj).__module__
    return 'rpyc' in module or 'netref' in module


def _format_as_json(result):
    """将结果转换为 JSON 可序列化格式"""
    import pandas as pd
    from datetime import datetime
    import io

    if result is None:
        return None
    elif isinstance(result, pd.DataFrame):
        if _is_remote_object(result):
            # 远程 DataFrame：用 to_csv 一次拉取，本地解析
            csv_str = result.to_csv(index=True)
            local_df = pd.read_csv(io.StringIO(csv_str), index_col=0)
            return local_df.to_dict(orient='records')
        else:
            # 本地 DataFrame：直接转换
            return result.to_dict(orient='records')
    elif isinstance(result, dict):
        return {k: _format_as_json(v) for k, v in result.items()}
    elif isinstance(result, (list, tuple)):
        return [_format_as_json(item) for item in result]
    elif hasattr(result, '__dict__'):
        return {attr: _format_as_json(getattr(result, attr))
                for attr in dir(result)
                if not attr.startswith('_') and not callable(getattr(result, attr))}
    elif isinstance(result, datetime):
        return result.isoformat()
    else:
        return result


def _format_as_text(result, limit=None):
    """将结果格式化为文本字符串"""
    import pandas as pd
    from pprint import pformat
    import io

    output = io.StringIO()

    if result is None:
        output.write("None")
    elif isinstance(result, pd.DataFrame):
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        output.write(result.to_string())
    elif isinstance(result, dict):
        has_dataframe = any(isinstance(v, pd.DataFrame) for v in result.values())
        if has_dataframe:
            for key, value in result.items():
                output.write(f"\n=== {key} ===\n")
                if isinstance(value, pd.DataFrame):
                    output.write(value.to_string())
                else:
                    output.write(pformat(value))
        else:
            output.write(pformat(result))
    elif isinstance(result, (list, tuple)):
        total = len(result)
        display = result[:limit] if limit and total > limit else result
        for i, item in enumerate(display, 1):
            if hasattr(item, '__dict__') or hasattr(item, '__slots__'):
                output.write(f"[{i}] {_format_object_attrs(item)}\n")
            else:
                output.write(f"[{i}] {item}\n")
        if limit and total > limit:
            output.write(f"\n# 共 {total} 条，已显示前 {limit} 条")
    else:
        output.write(pformat(result))

    return output.getvalue()


def _format_as_csv(result):
    """将结果格式化为 CSV 字符串

    Args:
        result: API 返回结果

    Returns:
        CSV 格式的字符串
    """
    import pandas as pd
    from pprint import pformat

    if isinstance(result, pd.DataFrame):
        return result.to_csv(index=True)
    elif isinstance(result, dict) and any(isinstance(v, pd.DataFrame) for v in result.values()):
        lines = []
        for key, value in result.items():
            if isinstance(value, pd.DataFrame):
                lines.append(f"# {key}")
                lines.append(value.to_csv(index=True))
            else:
                lines.append(f"# {key}: {value}")
        return "\n".join(lines) + "\n"
    else:
        return pformat(result) + "\n"


def format_output(result, limit=None, output=None, output_format='text'):
    """根据返回类型自动格式化输出

    Args:
        result: API 返回结果
        limit: 列表/元组输出数量限制，None 表示不限制
        output: 输出文件路径，None 表示输出到控制台
        output_format: 输出格式（text/json/csv），默认 text
    """
    from pathlib import Path

    if output_format == 'json':
        data = _format_as_json(result)
        content = json.dumps(data, ensure_ascii=False, indent=2)

    elif output_format == 'csv':
        content = _format_as_csv(result)

    else:
        content = _format_as_text(result, limit)

    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        with open(output, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"结果已保存到: {output}")
    else:
        print(content)


def _format_object_attrs(obj):
    """将对象属性提取为字典格式"""
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
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--format", "-f", dest="output_format", choices=["text", "json", "csv"],
                        help="输出格式 (环境变量: XQSHARE_FORMAT, 默认: text)")
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
