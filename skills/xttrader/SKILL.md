---
name: xttrader
description: 迅投QMT交易命令行工具，查询持仓、资产、下单、撤单等
---

# xttrader - 交易工具

## 使用场景

当用户需要：
- 查询账户持仓
- 查询账户资产
- 股票下单/撤单
- 查询订单状态

## 前置条件

- 已安装 xtquant-rpyc：`pip install xtquant-rpyc`
- 已配置环境变量：
  ```bash
  export XTQUANT_REMOTE_HOST="192.168.1.100"
  export XTQUANT_CLIENT_SECRET="your-secret"
  export XTQUANT_ACCOUNT_ID="你的资金账号"
  export XTQUANT_USERDATA_PATH="C:\\迅投QMT交易端\\userdata_mini"
  ```

## 命令格式

```bash
xttrader [全局参数] <command> [API参数]
```

**参数规则**：全局参数在 command 之前，API 参数在 command 之后

## 全局参数

| 参数 | 环境变量 | 说明 |
|------|----------|------|
| `--host` | XTQUANT_REMOTE_HOST | 服务端地址 |
| `--port` | XTQUANT_REMOTE_PORT | 服务端端口 |
| `--secret` | XTQUANT_CLIENT_SECRET | 认证密钥 |
| `--account-id` | XTQUANT_ACCOUNT_ID | 资金账号 |
| `--account-type` | - | 账户类型（默认 STOCK） |
| `--userdata-path` | XTQUANT_USERDATA_PATH | QMT userdata_mini 路径 |
| `--limit`, `-n` | - | 列表输出限制（默认50） |
| `--verbose`, `-v` | - | 显示详细日志 |

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

### 下单
```bash
# order_type: 23=买入, 24=卖出
# price_type: 11=限价, 12=市价
xttrader order_stock --stock-code "000001.SZ" --order-type 23 --order-volume 100 --price-type 11 --price 10.0
```

### 撤单
```bash
xttrader order_cancel --order-id "订单ID"
```

### 查询订单
```bash
xttrader query_stock_orders
```

## ⚠️ 安全提示

**高风险命令需要用户二次确认后才能执行**：

| 命令 | 风险等级 | 说明 |
|------|----------|------|
| `order_stock` | 🔴 高 | 下单（买入/卖出） |
| `order_cancel` | 🔴 高 | 撤单 |
| `order_cancel_all` | 🔴 高 | 全部撤单 |
| `credit_buy` | 🔴 高 | 融资买入 |
| `credit_sell` | 🔴 高 | 融券卖出 |
| `credit_repay` | 🔴 高 | 直接还款 |
| `credit_repay_stock` | 🔴 高 | 买券还券 |

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

## 注意事项

- account 参数会自动补充，无需手动传递
- 下单前确认账号已登录券商客户端
