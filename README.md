# 极限量化 (xqshare)

完全透明的 XtQuant 远程调用方案，让 macOS/Linux 可以像本地一样调用 Windows 上的 xtquant 库。

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
pip install xqshare
```

### 从源码安装

```bash
# Gitee（国内推荐）
git clone https://gitee.com/jdragonhu/xqshare.git

# GitHub（备用）
git clone https://github.com/jasonhu/xqshare.git

cd xqshare
pip install -e .
```

### 依赖

```bash
pip install rpyc
```

## 快速启动

### 启动前准备

**服务端（Windows）：** Python 环境 | 启动 miniQMT 并登录 | `pip install xqshare pyyaml`

**客户端（macOS/Linux）：** Python 环境 | `pip install xqshare`

### 服务器 Windows 快速启动

```powershell
python -m xqshare.server
```

### 客户端快速测试

```bash
export XQSHARE_REMOTE_HOST="192.168.1.100"
xtdata get_stock_list_in_sector --sector-name "沪深A股" --limit 10
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
| `--host` | XQSHARE_REMOTE_HOST | 服务端地址 |
| `--port` | XQSHARE_REMOTE_PORT | 服务端端口 |
| `--secret` | XQSHARE_CLIENT_SECRET | 认证密钥 |
| `--client-id` | XQSHARE_CLIENT_ID | 客户端标识 |
| `--limit`, `-n` | - | 列表输出数量限制（默认50） |
| `--verbose`, `-v` | - | 显示详细日志 |

### 限制

- **不支持订阅功能**：以 `subscribe` 开头的命令（需要回调函数）
- **不支持回调参数**：`callback` 参数（需要使用 Python API）
- **交易工具限制**：不支持以 `register` 开头的命令

---

## 示例脚本

项目提供了示例脚本，位于 `examples/` 目录，方便快速测试。

**推荐：使用环境变量配置（避免敏感信息泄露）**
```bash
# 设置环境变量
export XQSHARE_REMOTE_HOST="192.168.1.100"
export XQSHARE_CLIENT_SECRET="your-secret"

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
export QMT_ACCOUNT_ID="12345678"
export QMT_USERDATA_PATH="C:\\QMT\\userdata_mini"

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

```python
from xqshare import XtQuantRemote, connect, disconnect, xtdata, xttrader, xttype

# 方式1：类实例（推荐）
with XtQuantRemote("192.168.1.100", client_secret="xxx") as xt:
    stocks = xt.xtdata.get_stock_list_in_sector("沪深A股")

# 方式2：全局便捷函数
connect(host="192.168.1.100", client_secret="xxx")
stocks = xtdata.get_stock_list_in_sector("沪深A股")
disconnect()
```

**核心属性/方法：**
- `xt.xtdata` - 行情数据模块
- `xt.xttype` - 类型定义模块（StockAccount 等）
- `xt.create_trader()` - 创建交易实例

详细 API 请查看 [xqshare/client.py](xqshare/client.py) 源码。

---

## 使用示例

```python
from xqshare import XtQuantRemote

with XtQuantRemote("192.168.1.100", client_secret="my-secret") as xt:
    # 获取股票列表
    stocks = xt.xtdata.get_stock_list_in_sector("沪深A股")
    print(f"股票数量: {len(stocks)}")

    # 获取K线数据
    df = xt.xtdata.get_market_data(
        stock_list=["000001.SZ", "600000.SH"],
        period="1d",
        start_time="20260101"
    )
    print(df)

    # 获取实时行情
    ticks = xt.xtdata.get_full_tick(["000001.SZ"])
    print(ticks)
```

### 交易功能

```python
from xqshare import XtQuantRemote

with XtQuantRemote("192.168.1.100", client_secret="my-secret") as xt:
    # 创建交易实例（已自动 start）
    # userdata_path 可通过环境变量 QMT_USERDATA_PATH 配置
    trader = xt.create_trader("C:\\QMT\\userdata_mini")

    # 创建账户对象
    account = xt.xttype.StockAccount("12345678", "STOCK")

    # 连接交易服务器
    trader.connect()

    # 查询持仓
    positions = trader.query_stock_positions(account)
    for pos in positions:
        print(f"股票: {pos.stock_code}, 持仓: {pos.volume}")
```

**更多示例请查看 [examples/](examples/) 目录：**

| 文件 | 功能 |
|------|------|
| `get_stock_list.py` | 获取股票列表 |
| `download_history_data2.py` | 下载历史数据 |
| `get_market_data_ex.py` | 获取K线数据 |
| `get_tick_data.py` | 获取实时行情 |
| `subscribe_quote.py` | 订阅行情推送 |
| `query_positions.py` | 查询账户持仓 |

### 账户类型

| account_type | 说明 |
|--------------|------|
| `STOCK` | 普通股票账户 |
| `CREDIT` | 信用账户（两融） |
| `FUTURE` | 期货账户 |
| `HUGANGTONG` | 沪港通 |
| `SHENGANGTONG` | 深港通 |

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
logs/client_20260228.log
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

服务端和客户端需要配置相同的密钥，详见上方"环境变量配置"。

### 多客户端认证

服务端为每个客户端配置独立密钥：
```bash
export XQSHARE_CLIENT_app1="secret-for-app1"
export XQSHARE_CLIENT_app2="secret-for-app2"
```

客户端：
```python
xt1 = XtQuantRemote(client_id="app1", client_secret="secret-for-app1")
xt2 = XtQuantRemote(client_id="app2", client_secret="secret-for-app2")
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
python -m xqshare.server --ssl --cert server.crt --key server.key
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
xqshare/
├── xqshare/                # 包目录
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
└── LICENSE                 # GPLv3 许可证
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
black xqshare/

# 检查代码
flake8 xqshare/
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
# ├── xqshare-1.0.0-py3-none-any.whl
# └── xqshare-1.0.0.tar.gz

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
pip install --index-url https://test.pypi.org/simple/ xqshare
```

### 发布后验证

```bash
# 从 PyPI 安装
pip install xqshare

# 验证安装
python -c "from xqshare import XtQuantRemote; print('OK')"
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
tail -f logs/client_*.log
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

## 更新历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.1.1 | 2026-03-18 | 新增 xtview 模块支持（视图控制、调度任务管理），兼容不同 xtquant 版本 |
| 1.1.0 | 2026-03-17 | 交易功能优化完善、`xqshare-server` 命令、`.env` 配置支持、远程对象传输性能优化 |
| 1.0.4 | 2026-03-09 | JSON 输出优化：远程 DataFrame 高效序列化、`--compact` 参数、全局参数位置灵活、嵌套结构支持 |
| 1.0.3 | 2026-03-09 | 统一环境变量命名：XQSHARE_ 前缀，QMT 客户端配置使用 QMT_ 前缀 |
| 1.0.2 | 2026-03-09 | 精简快速启动章节 |
| 1.0.1 | 2026-02-28 | 支持配置文件热更新、多级账号权限控制 |
| 1.0.0 | 2026-02-20 | 首次发布 |

---

## License

GNU General Public License v3.0