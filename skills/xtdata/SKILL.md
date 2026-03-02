---
name: xtdata
description: xtquant-rpyc 行情数据命令行工具，获取股票列表、K线、实时行情等
---

# xtdata - 行情数据工具

## ⚠️ 重要约束

**必须使用 `xtdata` 命令行工具，禁止直接调用 Python xtquant 库**

| ✅ 正确做法 | ❌ 错误做法 |
|------------|------------|
| `xtdata get_full_tick --stock-list "..."` | `from xtquant import xtdata` |
| `xtdata get_market_data_ex --stock-list "..."` | `xtdata.get_market_data(...)` |

**原因**：
- xtquant 只能在 Windows 上运行
- 本地环境（macOS/Linux）无法直接调用 xtquant
- 必须通过 xtquant-rpyc 的命令行工具远程调用

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
| xtquant-rpyc 服务端 | 必需运行 | 在 Windows 上启动远程服务 |

**本 skill 假设**：
- Windows 上已配置好 xtquant 环境（含 miniQMT）
- xtquant-rpyc 服务端已启动并可访问
- 客户端环境变量已正确配置

## 客户端配置

- 已安装 xtquant-rpyc：`pip install xtquant-rpyc`
- 已配置环境变量（推荐）：
  ```bash
  export XTQUANT_REMOTE_HOST="192.168.1.100"
  export XTQUANT_CLIENT_SECRET="your-secret"
  ```

## 命令格式

```bash
xtdata [全局参数] <command> [API参数]
```

**参数规则**：全局参数在 command 之前，API 参数在 command 之后

## 全局参数

| 参数 | 环境变量 | 说明 |
|------|----------|------|
| `--host` | XTQUANT_REMOTE_HOST | 服务端地址 |
| `--port` | XTQUANT_REMOTE_PORT | 服务端端口 |
| `--secret` | XTQUANT_CLIENT_SECRET | 认证密钥 |
| `--client-id` | XTQUANT_CLIENT_ID | 客户端标识 |
| `--limit`, `-n` | - | 列表输出限制（默认50） |
| `--verbose`, `-v` | - | 显示详细日志 |

## 常用命令

### 获取股票列表
```bash
xtdata get_stock_list_in_sector --sector-name "沪深A股"
xtdata -n 100 get_stock_list_in_sector --sector-name "沪深300"
```

### 获取板块列表
```bash
xtdata get_sector_list
```

### 获取K线数据
```bash
# 日K线
xtdata get_market_data_ex --stock-list "['000001.SZ']" --period "1d" --start-time "20250101"

# 5分钟K线
xtdata get_market_data_ex --stock-list "['000001.SZ','600000.SH']" --period "5m" --start-time "20250101"
```

### 获取实时行情
```bash
xtdata get_full_tick --stock-list "['000001.SZ','600000.SH']"
```

### 下载历史数据

**单只股票下载**：
```bash
# download_history_data - 参数: stock_code, period, start_time, end_time
xtdata download_history_data --stock-code "000001.SZ" --period "1d"
xtdata download_history_data --stock-code "000001.SZ" --period "1d" --start-time "20250101" --end-time "20250228"
```

**批量下载**：
```bash
# download_history_data2 - 参数: stock_list, period, start_time, end_time
xtdata download_history_data2 --stock-list "['000001.SZ','600000.SH']" --period "1d"
xtdata download_history_data2 --stock-list "['000001.SZ','600000.SH']" --period "5m" --start-time "20250101"
```

**两个命令区别**：
| 命令 | 参数 | 说明 |
|------|------|------|
| `download_history_data` | `--stock-code` | 单只股票 |
| `download_history_data2` | `--stock-list` | 批量下载（推荐） |

## 数据准备提示

**查询市场数据前，应确保数据已下载**：

- 如果是首次查询某只股票的数据，或数据可能不是最新的，应先执行下载命令
- 下载命令会更新本地缓存，确保查询返回最新数据

**推荐流程**：
```
1. 先下载: xtdata download_history_data2 --stock-list "['000001.SZ']" --period "1d"
2. 再查询: xtdata get_market_data_ex --stock-list "['000001.SZ']" --period "1d" --start-time "20250101"
```

**示例**：
```
用户: 获取平安银行的日K线数据

AI: 首次查询需要先下载数据...
[执行] xtdata download_history_data2 --stock-list "['000001.SZ']" --period "1d"

AI: 数据下载完成，现在获取K线数据...
[执行] xtdata get_market_data_ex --stock-list "['000001.SZ']" --period "1d" --start-time "20250101"
```

## 限制

- **不支持 subscribe 开头的命令**（需要回调）
- **不支持 callback 参数**（需要 Python API）

## 参数格式

- 列表参数：`"['item1','item2']"` (Python 列表格式)
- 日期格式：`YYYYMMDD` 或 `YYYY-MM-DD`
