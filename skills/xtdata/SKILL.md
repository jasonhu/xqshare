---
name: xtdata
description: xqshare 行情数据命令行工具，获取股票列表、K线、实时行情等
---

# xtdata - 行情数据工具

## ⚠️ 重要约束

**必须使用 `xtdata` 命令行工具，禁止直接调用 Python xtquant 库**

| ✅ 正确做法 | ❌ 错误做法 |
|------------|------------|
| `xtdata get_full_tick --code-list "..."` | `from xtquant import xtdata` |
| `xtdata get_market_data_ex --stock-list "..."` | `xtdata.get_market_data(...)` |

**原因**：
- xtquant 只能在 Windows 上运行
- 本地环境（macOS/Linux）无法直接调用 xtquant
- 必须通过 xqshare 的命令行工具远程调用

## 使用场景

当用户需要：
- 获取股票列表（沪深A股、板块成分股等）
- 获取K线数据（日线、分钟线）
- 获取实时行情/五档盘口
- 下载历史数据
- 查询板块信息

## 前置条件（用户自行配置）

**⚠️ 以下环境需用户自行配置，本 skill 不提供配置指导**

| 组件 | 要求 | 说明 |
|------|------|------|
| Windows 服务器 | 必需 | xtquant 只能运行在 Windows |
| xqshare 服务端 | 必需运行 | 在 Windows 上启动远程服务 |

**本 skill 假设**：
- Windows 上已配置好 xtquant 环境（含 miniQMT）
- xqshare 服务端已启动并可访问
- 客户端环境变量已正确配置

## 客户端配置

- 已安装 xqshare：`pip install xqshare`
- 已配置环境变量（推荐）：
  ```bash
  export XQSHARE_REMOTE_HOST="192.168.1.100"
  export XQSHARE_CLIENT_SECRET="your-secret"
  ```

## 命令格式

```bash
xtdata [全局参数] <command> [API参数]
```

**参数规则**：全局参数在 command 之前，API 参数在 command 之后

## 全局参数

| 参数 | 环境变量 | 说明 |
|------|----------|------|
| `--host` | XQSHARE_REMOTE_HOST | 服务端地址 |
| `--port` | XQSHARE_REMOTE_PORT | 服务端端口 |
| `--secret` | XQSHARE_CLIENT_SECRET | 认证密钥 |
| `--client-id` | XQSHARE_CLIENT_ID | 客户端标识 |
| `--format`, `-f` | XQSHARE_FORMAT | 输出格式: text/json/csv (默认: text) |
| `--compact` | - | 紧凑模式输出 (仅对 json 格式有效) |
| `--limit`, `-n` | - | 列表输出限制（默认50，0表示不限制） |
| `--output`, `-o` | - | 输出文件路径 |
| `--verbose`, `-v` | - | 显示详细日志 |

**参数位置**：全局参数可放在 command 之前或之后，例如：
```bash
# 两种写法都有效
xtdata --format json --compact get_stock_list_in_sector --sector-name "沪深A股"
xtdata get_stock_list_in_sector --sector-name "沪深A股" --format json --compact
```

## 常用命令

### 获取板块列表
```bash
xtdata get_sector_list
```

### 获取股票列表
```bash
# text 格式（默认）
xtdata get_stock_list_in_sector --sector-name "沪深A股"

# json 格式
xtdata -f json get_stock_list_in_sector --sector-name "沪深A股"

# 紧凑 json 输出
xtdata -f json --compact get_stock_list_in_sector --sector-name "沪深A股"

# 限制输出数量
xtdata -n 100 get_stock_list_in_sector --sector-name "沪深300"
```

### 获取股票详情
```bash
# 获取股票基础信息
xtdata get_instrument_detail --stock-code "000001.SZ"

# 获取分红除权因子
xtdata get_divid_factors --stock-code "000001.SZ" --start-time "20240101" --end-time "20260101"
```

### 获取K线数据

**get_market_data** - 返回 `{字段: DataFrame}` 结构（按字段组织）：
```bash
# 多只股票日K线
xtdata get_market_data --stock-list "[\"000001.SZ\",\"600000.SH\"]" --period "1d" --start-time "20260101" --end-time "20260309"

# json 格式输出
xtdata -f json --compact get_market_data --stock-list "[\"000001.SZ\"]" --period "1d" --start-time "20260101"
```

**get_market_data_ex** - 返回 `{股票: DataFrame}` 结构（按股票组织，推荐）：
```bash
# 单只股票
xtdata get_market_data_ex --stock-list "[\"000001.SZ\"]" --period "1d" --start-time "20260101" --end-time "20260309"

# 多只股票
xtdata get_market_data_ex --stock-list "[\"000001.SZ\",\"600000.SH\",\"000002.SZ\"]" --period "1d" --start-time "20260101"

# 5分钟K线
xtdata get_market_data_ex --stock-list "[\"000001.SZ\"]" --period "5m" --start-time "20260301" --end-time "20260309"

# 使用 count 参数（获取最近N条）
xtdata get_market_data_ex --stock-list "[\"000001.SZ\"]" --period "1d" --count 10

# 前复权
xtdata get_market_data_ex --stock-list "[\"000001.SZ\"]" --period "1d" --start-time "20260101" --dividend-type "front"
```

### 获取实时行情（五档盘口）
```bash
# 单只股票
xtdata get_full_tick --code-list "[\"000001.SZ\"]"

# 多只股票
xtdata get_full_tick --code-list "[\"000001.SZ\",\"600000.SH\",\"000002.SZ\",\"600519.SH\"]"

# json 格式
xtdata -f json get_full_tick --code-list "[\"000001.SZ\",\"600000.SH\"]"
```

### 获取财务数据

**注意**：查询财务数据前，需先下载：
```bash
# 下载财务数据
xtdata download_financial_data2 --stock-list "[\"000001.SZ\"]" --table-list "[\"Balance\",\"Income\",\"CashFlow\"]"

# 查询财务数据
xtdata get_financial_data --stock-list "[\"000001.SZ\"]" --table-list "[\"Balance\",\"Income\"]"
```

### 下载历史数据

**单只股票下载**：
```bash
xtdata download_history_data --stock-code "000001.SZ" --period "1d" --start-time "20250101" --end-time "20260309"
```

**批量下载（推荐）**：
```bash
# 下载多只股票日K线
xtdata download_history_data2 --stock-list "[\"000001.SZ\",\"600000.SH\"]" --period "1d" --start-time "20250101" --end-time "20260309"

# 下载分钟线
xtdata download_history_data2 --stock-list "[\"000001.SZ\"]" --period "5m" --start-time "20250101"
```

**下载命令对比**：
| 命令 | 参数 | 说明 |
|------|------|------|
| `download_history_data` | `--stock-code` | 单只股票 |
| `download_history_data2` | `--stock-list` | 批量下载（推荐） |

## 数据准备提示

**⚠️ 重要：获取数据前必须先下载**

查询 K 线数据前，必须先下载对应股票的历史数据，否则会返回空数据或旧数据。

**基础下载周期**：

只有以下 3 个周期是基础数据，需要实际下载：
| 周期 | 说明 |
|------|------|
| `1m` | 1分钟线 |
| `5m` | 5分钟线 |
| `1d` | 日线 |

**派生周期**：其他周期（如 `15m`, `30m`, `60m`, `1w` 等）是基于基础周期计算得出，无需单独下载。

**下载与查询对应关系**：

| 数据类型 | 下载命令 | 查询命令 |
|----------|----------|----------|
| K线数据 | `download_history_data2` | `get_market_data_ex` |
| 财务数据 | `download_financial_data2` | `get_financial_data` |

**推荐流程**：
```
1. 下载基础数据: xtdata download_history_data2 --stock-list "[\"000001.SZ\"]" --period "1d"
2. 查询K线数据: xtdata get_market_data_ex --stock-list "[\"000001.SZ\"]" --period "1d" --start-time "20250101"
```

**示例**：
```
用户: 获取平安银行的日K线数据

AI: 首次查询需要先下载数据...
[执行] xtdata download_history_data2 --stock-list "[\"000001.SZ\"]" --period "1d"

AI: 数据下载完成，现在获取K线数据...
[执行] xtdata get_market_data_ex --stock-list "[\"000001.SZ\"]" --period "1d" --start-time "20250101"
```

## 限制

- **不支持 subscribe 开头的命令**（需要回调）
- **不支持 callback 参数**（需要 Python API）

## ⚠️ 数值处理注意事项

**科学计数法计算要特别仔细**：

| 科学计数法 | 实际值 | 常见错误 |
|------------|--------|----------|
| `1.23e8` | 123,000,000 (1.23亿) | ❌ 误认为 1230 万 |
| `1.23e9` | 1,230,000,000 (12.3亿) | ❌ 误认为 1.23 亿 |
| `5.67e6` | 5,670,000 (567万) | ❌ 误认为 56.7 万 |
| `3.14e10` | 31,400,000,000 (314亿) | ❌ 位数算错 |

**计算规则**：
- `e6` = 百万 (万 × 100)
- `e7` = 千万 (万 × 1000)
- `e8` = 亿
- `e9` = 十亿
- `e10` = 百亿

**处理建议**：
- 遇到科学计数法时，先转换为完整数字再解读
- 复述数值时，明确写出完整数字或使用"亿/万"单位

## 参数格式

- **列表参数**：使用 JSON 数组格式，如 `"[\"000001.SZ\",\"600000.SH\"]"`
- **日期格式**：`YYYYMMDD`（如 `20260101`）
- **周期参数**：`1d`(日线), `5m`(5分钟), `1m`(1分钟)

## 数据结构对比

| API | 返回结构 | 特点 |
|-----|----------|------|
| `get_market_data` | `{字段: DataFrame}` | 按字段组织，每字段一个 DataFrame（行=股票，列=日期） |
| `get_market_data_ex` | `{股票: DataFrame}` | 按股票组织，每股票一个 DataFrame（行=日期，列=字段），推荐 |
