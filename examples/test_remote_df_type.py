#!/usr/bin/env python3
"""
测试远程 DataFrame 类型信息

检测 RPyC 远程返回的 DataFrame 对象的类型特征。
"""

import argparse
import pandas as pd
from xqshare import XtQuantRemote


def inspect_object(obj, name="obj"):
    """检查对象的类型信息"""
    print(f"\n{'='*60}")
    print(f"检查对象: {name}")
    print(f"{'='*60}")

    # 基本类型信息
    print(f"type(obj): {type(obj)}")
    print(f"type(obj).__name__: {type(obj).__name__}")
    print(f"type(obj).__module__: {type(obj).__module__}")
    print(f"type(obj).__class__: {type(obj).__class__}")
    print(f"type(obj).__class__.__name__: {type(obj).__class__.__name__}")

    # isinstance 检查
    print(f"\nisinstance(obj, pd.DataFrame): {isinstance(obj, pd.DataFrame)}")

    # 检查是否有 __class__ 属性
    if hasattr(obj, '__class__'):
        print(f"obj.__class__: {obj.__class__}")
        print(f"obj.__class__.__name__: {obj.__class__.__name__}")
        print(f"obj.__class__.__module__: {obj.__class__.__module__}")

    # 检查是否是远程代理的特征
    class_name = type(obj).__name__
    module_name = type(obj).__module__

    print(f"\n--- 远程对象检测 ---")
    print(f"类名是 'DataFrame': {class_name == 'DataFrame'}")
    print(f"模块包含 'rpyc': {'rpyc' in module_name}")
    print(f"模块包含 'netref': {'netref' in module_name}")
    print(f"模块以 'pandas' 开头: {module_name.startswith('pandas')}")
    print(f"模块以 'builtins' 开头: {module_name.startswith('builtins')}")

    # 如果是 DataFrame，检查一些方法
    if hasattr(obj, 'shape'):
        print(f"\n--- DataFrame 属性 ---")
        print(f"shape: {obj.shape}")

        # 测试 to_csv 是否触发远程调用
        print(f"\n测试 to_csv (应该是一次远程调用)...")
        csv_str = obj.to_csv(index=True)
        print(f"CSV 长度: {len(csv_str)} 字符")
        print(f"CSV 前 200 字符:\n{csv_str[:200]}...")


def main():
    parser = argparse.ArgumentParser(description="测试远程 DataFrame 类型")
    parser.add_argument("--host", help="服务端地址")
    parser.add_argument("--port", type=int, help="服务端端口")
    parser.add_argument("--secret", help="认证密钥")
    parser.add_argument("--code", default="000001.SZ", help="股票代码")

    args = parser.parse_args()

    # 连接服务端
    print(f"正在连接 {args.host or '环境变量配置'}:{args.port or '环境变量配置'}...")
    xt = XtQuantRemote(
        host=args.host,
        port=args.port,
        client_secret=args.secret
    )

    try:
        # 获取数据
        print(f"获取 {args.code} 的K线数据...")
        data = xt.xtdata.get_market_data_ex(
            stock_list=[args.code],
            period="1d",
            start_time="20260101",
            end_time="20260228"
        )

        if data and args.code in data:
            df = data[args.code]

            # 检查远程 DataFrame
            inspect_object(df, f"remote DataFrame ({args.code})")

            # 检查包含 DataFrame 的字典
            inspect_object(data, "dict containing remote DataFrame")

            # 对比本地 DataFrame
            print(f"\n{'='*60}")
            print("对比：创建本地 DataFrame")
            print(f"{'='*60}")
            local_df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
            inspect_object(local_df, "local DataFrame")

        else:
            print("未获取到数据")

    finally:
        xt.close()
        print("\n连接已关闭")


if __name__ == "__main__":
    main()
