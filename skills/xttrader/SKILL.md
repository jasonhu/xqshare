---
name: xttrader
description: xqshare 交易命令行工具，查询持仓、资产、下单、撤单等
---

# xttrader - 交易工具

## ⚠️ 重要约束

**必须使用 `xttrader` 命令行工具，禁止直接调用 Python xtquant 库**

| ✅ 正确做法 | ❌ 错误做法 |
|------------|------------|
| `xttrader query_stock_positions` | `from xtquant import xttrader` |
| `xttrader order_stock --stock-code "..."` | `trader.order_stock(...)` |

**原因**：
- xtquant 只能在 Windows 上运行
- 本地环境（macOS/Linux）无法直接调用 xtquant
- 必须通过 xqshare 的命令行工具远程调用

## 使用场景

当用户需要：
- 查询账户持仓
- 查询账户资产
- 股票下单/撤单
- 查询订单状态

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
  export QMT_ACCOUNT_ID="你的资金账号"
  export QMT_USERDATA_PATH="C:\\QMT\\userdata_mini"
  ```

## 命令格式

```bash
xttrader [全局参数] <command> [API参数]
```

**参数规则**：全局参数在 command 之前，API 参数在 command 之后

## 全局参数

| 参数 | 环境变量 | 说明 |
|------|----------|------|
| `--host` | XQSHARE_REMOTE_HOST | 服务端地址 |
| `--port` | XQSHARE_REMOTE_PORT | 服务端端口 |
| `--secret` | XQSHARE_CLIENT_SECRET | 认证密钥 |
| `--account-id` | QMT_ACCOUNT_ID | 资金账号 |
| `--account-type` | - | 账户类型（默认 STOCK） |
| `--userdata-path` | QMT_USERDATA_PATH | QMT userdata_mini 路径 |

## 账户类型

| 类型 | 说明 |
|------|------|
| STOCK | 普通股票账户 |
| CREDIT | 信用账户（两融） |
| FUTURE | 期货账户 |
| HUGANGTONG | 沪港通 |
| SHENGANGTONG | 深港通 |

## 常用命令

### 查询持仓
```bash
xttrader query_stock_positions
xttrader --account-id "12345678" query_stock_positions
```

### 查询资产
```bash
xttrader query_stock_asset
```

### 查询订单
```bash
# 查询所有订单
xttrader query_stock_orders

# 仅查询可撤订单
xttrader query_stock_orders --cancelable-only true
```

### 查询成交
```bash
xttrader query_stock_trades
```

### 下单
```bash
# order_type: 23=买入, 24=卖出
# price_type: 11=限价, 12=市价
xttrader order_stock --stock-code "000001.SZ" --order-type 23 --order-volume 100 --price-type 11 --price 10.0
```

### 撤单
```bash
# 按订单ID撤单
xttrader cancel_order_stock --order-id "订单ID"

# 按柜台编号撤单
xttrader cancel_order_stock_sysid --market "SH" --sysid "柜台合同编号"
```

## ⚠️ 安全提示

**高风险命令需要用户二次确认后才能执行**：

| 命令 | 风险等级 | 说明 |
|------|----------|------|
| `order_stock` | 🔴 高 | 下单（买入/卖出） |
| `cancel_order_stock` | 🔴 高 | 撤单 |
| `cancel_order_stock_sysid` | 🔴 高 | 撤单（按柜台编号） |

**执行流程**：
1. 先向用户展示将要执行的完整命令
2. 明确说明操作内容和风险
3. 等待用户明确确认（如 "确认"、"执行"、"yes"）
4. 用户确认后再执行命令

**示例**：
```
AI: 即将执行下单操作：
    命令: xttrader order_stock --stock-code "000001.SZ" --order-type 23 --order-volume 100 --price-type 11 --price 10.0
    操作: 买入 平安银行(000001.SZ) 100股，限价 10.0 元
    预估金额: 1000 元

    请确认是否执行？(确认/取消)

用户: 确认

AI: [执行命令]
```

## 限制

- **不支持 subscribe/register 开头的命令**（需要回调）
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
- 金额相关计算务必二次核对

## 参数格式

- **股票代码**：带交易所后缀，如 `"000001.SZ"`, `"600000.SH"`
- **订单类型**：`23`=买入, `24`=卖出
- **报价类型**：`11`=限价, `12`=市价
