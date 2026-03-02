# XtQuant RPyC 远程代理

完全透明的 xtquant 远程调用方案，让 macOS/Linux 可以像本地一样调用 Windows 上的 xtquant 库。

## 特性

- ✅ **完全透明** - 客户端用法与本地 xtquant 完全一致
- ✅ **认证加密** - 支持 HMAC token 认证，可选 SSL/TLS 加密
- ✅ **断线重连** - 自动检测断线并重连，指数退避策略
- ✅ **心跳保活** - 定期心跳检测，保持连接活跃
- ✅ **异步回调** - 支持行情订阅等回调场景
- ✅ **完整日志** - API调用日志，记录函数名、参数、耗时
- ✅ **零学习成本** - 无需记忆新 API

## 架构

```
┌─────────────────┐         ┌─────────────────┐
│  macOS/Linux    │  RPyC   │   Windows       │
│  (客户端)        │ ──────► │  (服务端)        │
│                 │  18812  │                 │
│  xt.xtdata.xxx  │ ◄────── │  xtquant 实际运行│
│  xt.xttrader.xxx│  加密    │                 │
│                 │  回调    │                 │
└─────────────────┘         └─────────────────┘
```

## 安装

### 从 PyPI 安装（推荐）

```bash
pip install xtquant-rpyc
```

### 从源码安装

```bash
git clone https://gitee.com/jdragonhu/xtquant-rpyc.git
cd xtquant-rpyc
pip install -e .
```

### 依赖

```bash
pip install rpyc
```

## 快速开始

### 1. Windows 服务端

```bash
# 基础启动
python -m xtquant_rpyc.server

# 自定义端口
python -m xtquant_rpyc.server --port 18813

# 启用 SSL
python -m xtquant_rpyc.server --ssl --cert server.crt --key server.key

# 调整日志级别
python -m xtquant_rpyc.server --log-level DEBUG
```

**环境变量配置（推荐）:**

服务端:
```bash
export XTQUANT_PORT="18812"              # 监听端口
export XTQUANT_LOG_DIR="logs"            # 日志目录
export XTQUANT_CLIENT_SECRET="default-secret"  # 默认认证密钥
# export XTQUANT_CLIENT_app1="xxx"   # 特定客户端密钥（可选）
```

客户端:
```bash
export XTQUANT_REMOTE_HOST="192.168.1.100"   # 服务端地址
export XTQUANT_REMOTE_PORT="18812"           # 服务端端口
export XTQUANT_CLIENT_SECRET="your-secret"   # 认证密钥
# export XTQUANT_CLIENT_ID="my-app"        # 客户端标识（可选）
```

交易功能（需要资金账号和QMT路径）:
```bash
export XTQUANT_ACCOUNT_ID="12345678"              # 资金账号
export XTQUANT_USERDATA_PATH="C:\\迅投QMT交易端\\userdata_mini"  # QMT路径
```### 2. macOS/Linux 客户端

```python
from xtquant_rpyc import XtQuantRemote

# 方式1：使用环境变量（推荐）
# 需要先设置环境变量：
#   export XTQUANT_REMOTE_HOST="192.168.1.100"
#   export XTQUANT_CLIENT_SECRET="your-secret"
xt = XtQuantRemote()  # 自动读取环境变量

# 方式2：显式参数（覆盖环境变量）
xt = XtQuantRemote(
    host="192.168.1.100",
    port=18812,
    client_secret="default-secret",
    auto_reconnect=True,
    log_level="DEBUG",
)

# ========== 使用方式与本地 xtquant 完全一致 ==========

# 获取股票列表
stocks = xt.xtdata.get_stock_list_in_sector("沪深A股")
print(f"股票数量: {len(stocks)}")

# 获取行情数据
df = xt.xtdata.get_market_data(
    ["000001.SZ", "600000.SH"],
    period="1d",
    start_time="20260101"
)
print(df)

# 获取实时 tick
ticks = xt.xtdata.get_full_tick(["000001.SZ"])

# 关闭连接
xt.close()
```

---

## 命令行工具

安装后提供两个命令行工具：`xtdata`（行情）和 `xttrader`（交易）。

### xtdata - 行情数据工具

```bash
# 查看帮助
xtdata --help

# 获取股票列表
xtdata get_stock_list_in_sector --sector-name "沪深A股"

# 限制输出数量
xtdata --limit 100 get_stock_list_in_sector --sector-name "沪深A股"

# 获取K线数据
xtdata get_market_data_ex --stock-list "['000001.SZ']" --period "1d" --start-time "20260101" --end-time "20260228"

# 获取实时行情
xtdata get_full_tick --stock-list "['000001.SZ', '600000.SH']"
```

### xttrader - 交易工具

```bash
# 查看帮助
xttrader --help

# 查询持仓（需要设置账号）
xttrader --account-id "12345678" query_stock_positions

# 查询资产
xttrader --account-id "12345678" query_stock_asset

# 下单（需要更多参数）
xttrader --account-id "12345678" order_stock --stock-code "000001.SZ" --order-type 23 --order-volume 100
```

### 全局参数

| 参数 | 环境变量 | 说明 |
|------|----------|------|
| `--host` | XTQUANT_REMOTE_HOST | 服务端地址 |
| `--port` | XTQUANT_REMOTE_PORT | 服务端端口 |
| `--secret` | XTQUANT_CLIENT_SECRET | 认证密钥 |
| `--client-id` | XTQUANT_CLIENT_ID | 客户端标识 |
| `--limit`, `-n` | - | 列表输出数量限制（默认50） |
| `--verbose`, `-v` | - | 显示详细日志 |

### 限制

- **不支持订阅功能**：以 `subscribe` 开头的命令（需要回调函数）
- **不支持回调参数**：`callback` 参数（需要使用 Python API）
- **交易工具限制**：不支持以 `register` 开头的命令

---

## 命令行示例

项目提供了命令行工具，位于 `examples/` 目录，方便快速测试。

**推荐：使用环境变量配置（避免敏感信息泄露）**
```bash
# 设置环境变量
export XTQUANT_REMOTE_HOST="192.168.1.100"
export XTQUANT_CLIENT_SECRET="your-secret"

# 获取股票列表
python examples/get_stock_list.py --sector "沪深300"

# 下载历史数据（首次使用需要先下载数据）
python examples/download_history_data2.py

# 获取K线数据（支持 1d/1m/5m/15m/30m/60m）
python examples/get_market_data_ex.py --codes "000001.SZ,600000.SH" --period 1d

# 获取实时行情（含五档盘口）
python examples/get_tick_data.py --codes "000001.SZ"

# 订阅行情推送（duration=0 持续订阅，Ctrl+C 停止）
python examples/subscribe_quote.py --codes "000001.SZ" --duration 60
```

**交易功能（需要额外配置）:**
```bash
# 设置交易相关环境变量
export XTQUANT_ACCOUNT_ID="12345678"
export XTQUANT_USERDATA_PATH="C:\\迅投QMT交易端\\userdata_mini"

# 查询持仓
python examples/query_positions.py
```

**备选：命令行参数（覆盖环境变量）:**
```bash
# 显式指定服务端地址
python examples/get_stock_list.py --host 192.168.1.100 --sector "沪深300"

# 显式指定认证密钥
python examples/get_tick_data.py --host 192.168.1.100 --secret "your-secret" --codes "000001.SZ"

# 查看帮助
python examples/get_stock_list.py --help
```

---

## API 文档

### 客户端类 `XtQuantRemote`

#### 构造函数

```python
XtQuantRemote(
    host="localhost",           # 服务端地址
    port=18812,                 # 服务端端口
    client_id="default",        # 客户端标识
    client_secret="",           # 认证密钥
    use_ssl=False,              # 启用 SSL
    ssl_verify=True,            # 验证 SSL 证书
    auto_reconnect=True,        # 自动重连
    max_retries=5,              # 最大重试次数
    heartbeat_interval=30,      # 心跳间隔(秒)
    log_level="INFO",           # 日志级别
    callback_port=0,            # 回调服务器端口(0=自动)
)
```

#### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `xtdata` | RemoteModule | xtquant.xtdata 模块代理 |
| `xttrader` | RemoteModule | xtquant.xttrader 模块代理 |
| `xttype` | RemoteModule | xtquant.xttype 模块代理（账户类型等） |

#### 方法

| 方法 | 说明 |
|------|------|
| `is_connected()` | 检查连接状态 |
| `reconnect()` | 手动重连 |
| `close()` | 关闭连接 |
| `get_service_status()` | 获取服务端状态 |
| `get_all_stocks()` | 获取沪深A股列表 |
| `get_index_list()` | 获取指数列表 |
| `create_trader()` | 创建交易实例 |
| `subscribe_quote(stock_code, callback)` | 订阅行情 |
| `unsubscribe_all()` | 取消所有订阅 |
| `get_market_data_batch(stock_list, ...)` | 批量获取行情 |
| `get_full_tick_batch(stock_list)` | 批量获取 tick |

### 全局便捷函数

```python
from xtquant_rpyc import connect, disconnect, get_client, xtdata, xttrader, xttype

# 方式1：使用环境变量（推荐）
# 需要先设置: export XTQUANT_REMOTE_HOST="192.168.1.100"
connect()

# 方式2：显式参数（覆盖环境变量）
# connect(host="192.168.1.100", client_secret="my-secret")

# 直接使用模块
stocks = xtdata.get_stock_list_in_sector("沪深A股")

# 创建账户对象
account = xttype.StockAccount("资金账号", "STOCK")

# 查询持仓
positions = xttrader.query_stock_positions(account)

# 获取客户端实例
client = get_client()

# 断开连接
disconnect()
```

### 异常类

| 异常 | 说明 |
|------|------|
| `ConnectionError` | 连接错误 |
| `AuthenticationError` | 认证错误 |
| `CallbackError` | 回调错误 |

---

## 使用示例

### 基础数据获取

```python
from xtquant_rpyc import XtQuantRemote

with XtQuantRemote("192.168.1.100", client_secret="my-secret") as xt:
    # 获取股票列表
    all_stocks = xt.xtdata.get_stock_list_in_sector("沪深A股")
    print(f"沪深A股数量: {len(all_stocks)}")
    
    # 获取指数成分股
    hs300 = xt.xtdata.get_stock_list_in_sector("沪深300")
    print(f"沪深300成分股: {len(hs300)}")
    
    # 获取板块列表
    sectors = xt.xtdata.get_sector_list()
    for sector in sectors[:5]:
        print(f"板块: {sector}")
```

### K线数据获取

```python
from xtquant_rpyc import XtQuantRemote
import pandas as pd

with XtQuantRemote("192.168.1.100", client_secret="my-secret") as xt:
    # 获取日K线
    df = xt.xtdata.get_market_data(
        stock_list=["000001.SZ", "600000.SH"],
        period="1d",
        start_time="20250101",
        end_time="20251231"
    )
    print(df)
    
    # 获取分钟K线
    df_1m = xt.xtdata.get_market_data(
        stock_list=["000001.SZ"],
        period="1m",
        start_time="20250228"
    )
    
    # 获取分笔数据
    ticks = xt.xtdata.get_full_tick(["000001.SZ", "600000.SH"])
    for code, tick in ticks.items():
        print(f"{code}: 最新价={tick.get('lastPrice')}, 成交量={tick.get('volume')}")
```

### 财务数据获取

```python
from xtquant_rpyc import XtQuantRemote

with XtQuantRemote("192.168.1.100", client_secret="my-secret") as xt:
    # 获取财务数据
    financial_data = xt.xtdata.get_financial_data(
        stock_list=["000001.SZ"],
        table_list=["Balance", "Income", "CashFlow"],
        start_time="20240101",
        end_time="20241231"
    )
    print(financial_data)
```

### 实时行情订阅

```python
from xtquant_rpyc import XtQuantRemote
import time

def on_quote(stock_code: str, data: dict):
    """行情推送回调"""
    print(f"[{stock_code}] 最新价: {data.get('lastPrice')} | "
          f"成交量: {data.get('volume')} | "
          f"涨跌幅: {data.get('chgRatio', 0) * 100:.2f}%")

with XtQuantRemote("192.168.1.100", client_secret="my-secret") as xt:
    # 订阅多只股票
    stocks = ["000001.SZ", "600000.SH", "000002.SZ"]
    
    subscriptions = []
    for stock in stocks:
        sub = xt.subscribe_quote(stock, on_quote)
        subscriptions.append(sub)
    
    print("已订阅行情，按 Ctrl+C 停止...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    
    # 停止订阅
    for sub in subscriptions:
        sub.stop()
```

### 使用上下文管理器订阅

```python
from xtquant_rpyc import XtQuantRemote
import time

with XtQuantRemote("192.168.1.100", client_secret="my-secret") as xt:
    # 使用上下文管理器自动管理订阅
    with xt.subscribe_quote("000001.SZ", lambda c, d: print(f"{c}: {d.get('lastPrice')}")):
        print("订阅中，60秒后自动取消...")
        time.sleep(60)
    # 自动取消订阅
```

### 交易示例

#### 查询账户持仓

```python
from xtquant_rpyc import XtQuantRemote

with XtQuantRemote("192.168.1.100", client_secret="my-secret") as xt:
    # 创建账户对象（通过 xttype 代理）
    # account_type: STOCK(股票), CREDIT(信用), FUTURE(期货) 等
    account = xt.xttype.StockAccount("你的资金账号", "STOCK")

    # 查询持仓
    positions = xt.xttrader.query_stock_positions(account)

    # 遍历持仓
    for pos in positions:
        print(f"股票: {pos.stock_code}")
        print(f"  持仓数量: {pos.volume}")
        print(f"  可用数量: {pos.can_use_volume}")
        print(f"  成本价: {pos.avg_price}")
        print(f"  市值: {pos.market_value}")
        print(f"  盈亏比例: {pos.profit_rate * 100:.2f}%")
        print("---")
```

#### 账户类型说明

| account_type | 说明 |
|--------------|------|
| `STOCK` | 普通股票账户 |
| `CREDIT` | 信用账户（两融） |
| `FUTURE` | 期货账户 |
| `HUGANGTONG` | 沪港通 |
| `SHENGANGTONG` | 深港通 |

#### 完整交易流程

```python
from xtquant_rpyc import XtQuantRemote

with XtQuantRemote("192.168.1.100", client_secret="my-secret") as xt:
    # 创建账户对象
    account = xt.xttype.StockAccount("资金账号", "STOCK")

    # 创建交易实例
    trader = xt.create_trader()

    # 连接交易账户（根据券商配置）
    # trader.connect(account_id, account_key, server_ip)

    # 查询资产
    # asset = trader.query_stock_asset(account)

    # 查询持仓
    positions = xt.xttrader.query_stock_positions(account)

    # 下单买入
    # order_id = xt.xttrader.order_stock(
    #     account=account,
    #     stock_code="000001.SZ",
    #     order_type=23,       # 23=买入, 24=卖出
    #     order_volume=100,    # 股票以"股"为单位
    #     price_type=11,       # 11=限价, 12=市价
    #     price=10.0,
    #     strategy_name="my_strategy",
    #     order_remark="test_order"
    # )

    # 查询订单
    # orders = xt.xttrader.query_stock_orders(account)

    # 撤单
    # xt.xttrader.cancel_order(account, order_id)
```

### 批量数据获取

```python
from xtquant_rpyc import XtQuantRemote

with XtQuantRemote("192.168.1.100", client_secret="my-secret") as xt:
    # 批量获取行情（一次网络请求）
    stock_list = xt.get_all_stocks()[:100]  # 取前100只
    
    data = xt.get_market_data_batch(
        stock_list=stock_list,
        period="1d",
        start_time="20250101"
    )
    print(f"获取数据: {len(data)} 条")
    
    # 批量获取 tick
    ticks = xt.get_full_tick_batch(stock_list[:50])
    print(f"获取 tick: {len(ticks)} 只股票")
```

### 多客户端场景

```python
from xtquant_rpyc import XtQuantRemote

# 配置服务端环境变量:
# export XTQUANT_CLIENT_app1="secret-app1"
# export XTQUANT_CLIENT_app2="secret-app2"

# 不同应用使用不同客户端ID和密钥
client1 = XtQuantRemote(
    host="192.168.1.100",
    client_id="app1",
    client_secret="secret-app1"
)

client2 = XtQuantRemote(
    host="192.168.1.100",
    client_id="app2",
    client_secret="secret-app2"
)

# 各自独立操作
stocks1 = client1.xtdata.get_stock_list_in_sector("沪深A股")
stocks2 = client2.xtdata.get_stock_list_in_sector("创业板")

client1.close()
client2.close()
```

---

## 异步回调（行情订阅）

支持服务端主动推送数据到客户端，适用于实时行情订阅场景。

### 服务端日志（自动记录）

```
2026-02-28 23:45:12.345 | INFO     | api | [CALL] get_market_data | client=my-app@192.168.1.50 | args=(['000001.SZ', '600000.SH'],) | kwargs={'period': '1d'}
2026-02-28 23:45:12.456 | INFO     | api | [OK] get_market_data | elapsed=111.23ms | result=DataFrame[shape=(100, 6)]
2026-02-28 23:45:15.123 | INFO     | api | [CALL] get_full_tick | client=my-app@192.168.1.50 | args=(['000001.SZ'],) | kwargs={}
2026-02-28 23:45:15.145 | INFO     | api | [OK] get_full_tick | elapsed=22.11ms | result=dict{000001.SZ}
```

### 客户端使用回调

```python
from xtquant_rpyc import XtQuantRemote

# 连接
xt = XtQuantRemote("192.168.1.100", client_secret="my-secret")

# 定义回调函数
def on_quote(stock_code, data):
    """行情推送回调"""
    print(f"行情推送: {stock_code}")
    print(f"  最新价: {data.get('lastPrice')}")
    print(f"  成交量: {data.get('volume')}")

# 订阅行情
subscription = xt.subscribe_quote("000001.SZ", on_quote)

print("已订阅，等待行情推送...")
try:
    # 主线程可以做其他事情
    import time
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass

# 停止订阅
subscription.stop()
xt.close()
```

### 使用上下文管理器

```python
from xtquant_rpyc import XtQuantRemote

with XtQuantRemote("192.168.1.100") as xt:
    # 订阅行情
    with xt.subscribe_quote("000001.SZ", lambda code, data: print(f"{code}: {data}")):
        import time
        time.sleep(60)  # 运行1分钟
    # 自动取消订阅
# 自动关闭连接
```

---

## 日志系统

### 服务端日志

**日志文件位置：**
```
logs/
├── xtquant_service_20260228.log    # 主日志
└── api_calls_20260228.log          # API调用日志（单独文件）
```

**日志格式：**
```
时间戳 | 级别 | 模块 | 消息
2026-02-28 23:45:12.345 | INFO | api | [CALL] get_market_data | ...
```

**API调用日志记录内容：**
- 函数名称
- 客户端信息（client_id + IP）
- 调用参数（截断摘要）
- 执行耗时（毫秒）
- 返回值摘要

**日志示例：**
```
2026-02-28 23:45:12.345 | INFO     | api | [CALL] get_market_data | client=my-app@192.168.1.50 | args=(['000001.SZ'],) | kwargs={'period': '1d', 'start_time': '20260101'}
2026-02-28 23:45:12.456 | INFO     | api | [OK] get_market_data | elapsed=111.23ms | result=DataFrame[shape=(100, 6)]

2026-02-28 23:45:15.123 | INFO     | api | [CALL] get_full_tick | client=my-app@192.168.1.50 | args=(['000001.SZ'],) | kwargs={}
2026-02-28 23:45:15.145 | INFO     | api | [OK] get_full_tick | elapsed=22.11ms | result=dict{000001.SZ}

2026-02-28 23:45:20.000 | ERROR    | api | [ERROR] get_market_data | elapsed=5000.00ms | error=TimeoutError: Connection timed out
```

### 客户端日志

**日志文件位置：**
```
~/.xtquant/logs/client_20260228.log
```

**客户端也会记录调用：**
```python
# 设置日志级别
xt = XtQuantRemote("192.168.1.100", log_level="DEBUG")
```

客户端日志示例：
```
2026-02-28 23:50:01.123 | INFO  | [OK] xtdata.get_market_data | 111.23ms | DataFrame[shape=(100, 6)]
2026-02-28 23:50:02.456 | INFO  | [OK] xtdata.get_full_tick | 22.11ms | dict[1 keys]
2026-02-28 23:50:05.000 | ERROR | [ERROR] xtdata.get_market_data | 5000.00ms | TimeoutError: Connection timed out
```

---

## 配置选项

### 客户端参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| host | 服务端地址 | localhost |
| port | 服务端端口 | 18812 |
| client_id | 客户端标识 | default |
| client_secret | 认证密钥 | 空 |
| use_ssl | 启用 SSL | False |
| ssl_verify | 验证 SSL 证书 | True |
| auto_reconnect | 自动重连 | True |
| max_retries | 最大重试次数 | 5 |
| heartbeat_interval | 心跳间隔(秒) | 30 |
| log_level | 日志级别 | INFO |
| callback_port | 回调服务器端口 | 0(自动) |

### 服务端参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| --host | 监听地址 | 0.0.0.0 |
| --port | 监听端口 | 18812 |
| --ssl | 启用 SSL | False |
| --cert | SSL 证书文件 | - |
| --key | SSL 私钥文件 | - |
| --log-level | 日志级别 | INFO |

---

## 认证机制

### 基础认证

服务端：
```bash
export XTQUANT_CLIENT_SECRET="my-shared-secret"
python -m xtquant_rpyc.server
```

客户端：
```python
xt = XtQuantRemote(host="...", client_secret="my-shared-secret")
```

### 多客户端认证

服务端为每个客户端配置独立密钥：
```bash
export XTQUANT_CLIENT_app1="secret-for-app1"
export XTQUANT_CLIENT_app2="secret-for-app2"
```

客户端：
```python
xt1 = XtQuantRemote(host="...", client_id="app1", client_secret="secret-for-app1")
xt2 = XtQuantRemote(host="...", client_id="app2", client_secret="secret-for-app2")
```

---

## SSL 加密

### 生成自签名证书

```bash
openssl genrsa -out server.key 2048
openssl req -new -x509 -days 365 -key server.key -out server.crt
```

### 启动服务端

```bash
python -m xtquant_rpyc.server --ssl --cert server.crt --key server.key
```

### 客户端连接

```python
xt = XtQuantRemote(
    host="192.168.1.100",
    use_ssl=True,
    ssl_verify=False  # 自签名证书需禁用验证
)
```

---

## 断线重连

自动检测连接断开并重连：
- **检测机制**：心跳超时、调用异常
- **重连策略**：指数退避（1s → 2s → 4s → 8s → 16s...）
- **最大重试**：默认 5 次
- **自动恢复订阅**：重连后自动重新订阅行情

```python
xt = XtQuantRemote(
    host="192.168.1.100",
    auto_reconnect=True,
    max_retries=10,
    heartbeat_interval=15,
)
```

---

## 项目结构

```
xtquant-rpyc/
├── xtquant_rpyc/           # 包目录
│   ├── __init__.py         # 包入口
│   ├── client.py           # 客户端
│   ├── server.py           # 服务端
│   └── tools/              # 命令行工具
│       ├── __init__.py
│       ├── common.py       # 共享模块
│       ├── xtdata.py       # 行情命令行工具
│       └── xttrader.py     # 交易命令行工具
├── examples/               # 示例代码
│   ├── get_stock_list.py      # 获取股票列表
│   ├── download_history_data.py  # 下载历史数据（回调版本）
│   ├── download_history_data2.py # 下载历史数据（服务端封装版本）
│   ├── get_market_data.py     # 获取K线数据
│   ├── get_market_data_ex.py  # 获取K线数据（推荐，格式更直观）
│   ├── get_tick_data.py       # 获取实时行情
│   ├── subscribe_quote.py     # 订阅行情推送
│   └── query_positions.py     # 查询账户持仓
├── tests/                  # 测试目录
│   ├── __init__.py
│   ├── test_client.py      # 客户端测试
│   ├── test_server.py      # 服务端测试
│   └── test_integration.py # 集成测试
├── README.md               # 文档
├── pyproject.toml          # 包配置
├── pytest.ini              # 测试配置
└── LICENSE                 # MIT 许可证
```

---

## 开发

### 运行测试

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行单元测试
pytest tests/

# 运行集成测试（需要启动服务端）
pytest tests/ -m integration
```

### 代码风格

```bash
# 格式化代码
black xtquant_rpyc/

# 检查代码
flake8 xtquant_rpyc/
```

---

## 打包与发布

### 环境准备

```bash
# 安装打包和发布工具
pip install build twine
```

| 工具 | 用途 |
|------|------|
| `build` | 打包生成 `.whl` + `.tar.gz` |
| `twine` | 上传到 PyPI |

### 本地打包

```bash
# 清理旧的构建文件
rm -rf dist/ build/ *.egg-info

# 执行打包
python -m build

# 检查生成的包
ls -la dist/
# dist/
# ├── xtquant_rpyc-1.0.0-py3-none-any.whl
# └── xtquant_rpyc-1.0.0.tar.gz

# 验证包格式
twine check dist/*
```

### 发布到 PyPI

**前置条件：**
1. 注册 [PyPI 账号](https://pypi.org/account/register/)
2. 创建 API Token：Account settings → API tokens → Add API token
3. 保存 Token（格式：`pypi-xxxxxx...`，只显示一次！）

**执行发布：**

```bash
twine upload dist/*
```

**输入：**
- Username: `__token__`（字面意思，就是输入这个字符串）
- Password: 粘贴你的 API Token

### 测试发布（可选）

先在 [TestPyPI](https://test.pypi.org/) 测试：

```bash
# 发布到 TestPyPI
twine upload --repository testpypi dist/*

# 从 TestPyPI 安装测试
pip install --index-url https://test.pypi.org/simple/ xtquant-rpyc
```

### 发布后验证

```bash
# 从 PyPI 安装
pip install xtquant-rpyc

# 验证安装
python -c "from xtquant_rpyc import XtQuantRemote; print('OK')"
```

---

## 日志文件

```
服务端:
  logs/
  ├── xtquant_service_YYYYMMDD.log   # 主日志
  └── api_calls_YYYYMMDD.log         # API调用日志

客户端:
  ~/.xtquant/logs/client_YYYYMMDD.log
```

---

## 注意事项

1. **网络延迟**：远程调用有网络延迟，高频场景建议批量获取
2. **数据序列化**：复杂对象通过 pickle 序列化，确保两端 Python 版本兼容
3. **安全性**：生产环境建议启用 SSL + 强密码认证
4. **防火墙**：确保服务端端口（默认 18812）可访问
5. **日志清理**：定期清理日志文件，避免磁盘占用过大

---

## 故障排查

### 查看日志

```bash
# 服务端
tail -f logs/api_calls_*.log

# 客户端
tail -f ~/.xtquant/logs/client_*.log
```

### 连接失败

```bash
# 检查网络
ping 192.168.1.100
telnet 192.168.1.100 18812
```

### 查看服务状态

```python
# 客户端查询服务端状态
status = xt.get_service_status()
print(status)
# {'uptime': 3600, 'active_tokens': 2, 'active_callbacks': 5}
```

---

## License

MIT License