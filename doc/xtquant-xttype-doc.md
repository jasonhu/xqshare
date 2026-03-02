# XtQuant xttype 模块接口文档

> 生成时间: 2026-03-02
> 基于源码: `/opt/homebrew/Caskroom/miniconda/base/envs/dev/lib/python3.13/site-packages/xtquant/xttype.py`

---

## 目录

- [账号类型](#账号类型)
- [数据结构](#数据结构)
- [信用交易数据结构](#信用交易数据结构)
- [回报数据结构](#回报数据结构)

---

## 账号类型

### StockAccount

证券账号类。

```python
from xtquant.xttype import StockAccount

# 普通股票账号
account = StockAccount("8888888888", "STOCK")

# 信用账号
credit_account = StockAccount("8888888888", "CREDIT")
```

**构造参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| account_id | str | 资金账号（必须为字符串） |
| account_type | str | 账号类型，默认 'STOCK' |

**支持的账号类型:**
| 类型 | 说明 |
|------|------|
| STOCK | 股票账号 |
| CREDIT | 信用账号 |
| FUTURE | 期货账号 |
| FUTURE_OPTION | 期货期权账号 |
| STOCK_OPTION | 股票期权账号 |
| HUGANGTONG | 沪港通账号 |
| SHENGANGTONG | 深港通账号 |
| NEW3BOARD | 全国股转账号 |

**属性:**
| 属性 | 类型 | 说明 |
|------|------|------|
| account_id | str | 资金账号 |
| account_type | int | 账号类型（数值） |

---

## 数据结构

### XtAsset

资产结构。

```python
# 通过查询获取
asset = trader.query_stock_asset(account)
print(f"可用: {asset.cash}")
print(f"总资产: {asset.total_asset}")
```

**属性:**
| 属性 | 类型 | 说明 |
|------|------|------|
| account_type | int | 账号类型 |
| account_id | str | 资金账号 |
| cash | float | 可用资金 |
| frozen_cash | float | 冻结资金 |
| market_value | float | 持仓市值 |
| total_asset | float | 总资产 |
| fetch_balance | float | 可取资金 |

---

### XtOrder

委托结构。

```python
# 通过查询获取
orders = trader.query_stock_orders(account)
for order in orders:
    print(f"委托号: {order.order_id}")
    print(f"股票: {order.stock_code}")
    print(f"状态: {order.order_status}")
```

**属性:**
| 属性 | 类型 | 说明 |
|------|------|------|
| account_type | int | 账号类型 |
| account_id | str | 资金账号 |
| stock_code | str | 证券代码，如 "600000.SH" |
| order_id | int | 委托编号 |
| order_sysid | str | 柜台编号 |
| order_time | str | 报单时间 |
| order_type | int | 委托类型，23=买，24=卖 |
| order_volume | int | 委托数量（股/张） |
| price_type | int | 报价类型 |
| price | float | 报价价格 |
| traded_volume | int | 成交数量（股/张） |
| traded_price | float | 成交均价 |
| order_status | int | 委托状态 |
| status_msg | str | 委托状态描述（含废单原因） |
| strategy_name | str | 策略名称 |
| order_remark | str | 委托备注 |
| direction | int | 多空方向（股票不需要） |
| offset_flag | int | 交易操作 |
| secu_account | str | 股东代码 |
| instrument_name | str | 证券名称 |

---

### XtTrade

成交结构。

```python
# 通过查询获取
trades = trader.query_stock_trades(account)
for trade in trades:
    print(f"成交号: {trade.traded_id}")
    print(f"价格: {trade.traded_price}")
    print(f"数量: {trade.traded_volume}")
```

**属性:**
| 属性 | 类型 | 说明 |
|------|------|------|
| account_type | int | 账号类型 |
| account_id | str | 资金账号 |
| stock_code | str | 证券代码 |
| order_type | int | 委托类型 |
| traded_id | str | 成交编号 |
| traded_time | str | 成交时间 |
| traded_price | float | 成交价格 |
| traded_volume | int | 成交数量（股/张） |
| traded_amount | float | 成交金额 |
| order_id | int | 委托编号 |
| order_sysid | str | 柜台编号 |
| strategy_name | str | 策略名称 |
| order_remark | str | 委托备注 |
| direction | int | 多空方向 |
| offset_flag | int | 交易操作 |
| commission | float | 手续费 |
| secu_account | str | 股东代码 |
| instrument_name | str | 证券名称 |

---

### XtPosition

持仓结构。

```python
# 通过查询获取
positions = trader.query_stock_positions(account)
for pos in positions:
    print(f"股票: {pos.stock_code}")
    print(f"持仓: {pos.volume}")
    print(f"可用: {pos.can_use_volume}")
    print(f"成本: {pos.avg_price}")
```

**属性:**
| 属性 | 类型 | 说明 |
|------|------|------|
| account_type | int | 账号类型 |
| account_id | str | 资金账号 |
| stock_code | str | 证券代码 |
| volume | int | 持仓数量（股/张） |
| can_use_volume | int | 可用数量（股/张） |
| open_price | float | 开仓价 |
| market_value | float | 市值 |
| frozen_volume | int | 冻结数量 |
| on_road_volume | int | 在途股份 |
| yesterday_volume | int | 昨夜拥股 |
| avg_price | float | 成本价 |
| direction | int | 多空方向 |
| last_price | float | 当前价 |
| profit_rate | float | 盈亏比例 |
| secu_account | str | 股东代码 |
| instrument_name | str | 证券名称 |

---

## 信用交易数据结构

### XtCreditOrder

信用委托结构。

**属性:** 继承自 XtOrder，额外包含：

| 属性 | 类型 | 说明 |
|------|------|------|
| contract_no | str | 两融合同编号 |
| stock_code1 | str | 关联证券代码 |

---

### XtCreditDeal

信用成交结构。

**属性:**
| 属性 | 类型 | 说明 |
|------|------|------|
| account_type | int | 账号类型 |
| account_id | str | 资金账号 |
| stock_code | str | 证券代码 |
| traded_id | str | 成交编号 |
| traded_time | str | 成交时间 |
| traded_price | float | 成交价格 |
| traded_volume | int | 成交数量 |
| order_id | int | 委托编号 |
| contract_no | str | 两融合同编号 |
| stock_code1 | str | 关联证券代码 |

---

## 回报数据结构

### XtOrderError

委托失败结构。

```python
def on_order_error(self, order_error):
    print(f"委托失败: {order_error.order_id}")
    print(f"错误码: {order_error.error_id}")
    print(f"错误信息: {order_error.error_msg}")
```

**属性:**
| 属性 | 类型 | 说明 |
|------|------|------|
| account_type | int | 账号类型 |
| account_id | str | 资金账号 |
| order_id | int | 订单编号 |
| error_id | int | 报单失败错误码 |
| error_msg | str | 报单失败具体信息 |
| strategy_name | str | 策略名称 |
| order_remark | str | 委托备注 |

---

### XtCancelError

撤单失败结构。

```python
def on_cancel_error(self, cancel_error):
    print(f"撤单失败: {cancel_error.order_id}")
    print(f"错误信息: {cancel_error.error_msg}")
```

**属性:**
| 属性 | 类型 | 说明 |
|------|------|------|
| account_type | int | 账号类型 |
| account_id | str | 资金账号 |
| order_id | int | 订单编号 |
| market | int | 交易市场，0=上海，1=深圳 |
| order_sysid | str | 柜台委托编号 |
| error_id | int | 撤单失败错误码 |
| error_msg | str | 撤单失败具体信息 |

---

### XtOrderResponse

异步下单回报结构。

```python
def on_order_stock_async_response(self, response):
    print(f"下单回报: {response.order_id}")
    print(f"错误信息: {response.error_msg}")
```

**属性:**
| 属性 | 类型 | 说明 |
|------|------|------|
| account_type | int | 账号类型 |
| account_id | str | 资金账号 |
| order_id | int | 订单编号 |
| strategy_name | str | 策略名称 |
| order_remark | str | 委托备注 |
| error_msg | str | 错误信息 |
| seq | int | 下单请求序号 |

---

### XtCancelOrderResponse

异步撤单回报结构。

```python
def on_cancel_order_stock_async_response(self, response):
    print(f"撤单结果: {response.cancel_result}")
```

**属性:**
| 属性 | 类型 | 说明 |
|------|------|------|
| account_type | int | 账号类型 |
| account_id | str | 资金账号 |
| cancel_result | int | 撤单结果，0=成功 |
| order_id | int | 订单编号 |
| order_sysid | str | 柜台委托编号 |
| seq | int | 撤单请求序号 |
| error_msg | str | 撤单反馈信息 |

---

### XtAccountStatus

账号状态结构。

```python
def on_account_status(self, status):
    print(f"账号: {status.account_id}")
    print(f"状态: {status.status}")
```

**属性:**
| 属性 | 类型 | 说明 |
|------|------|------|
| account_type | int | 账号类型 |
| account_id | str | 资金账号 |
| status | int | 账号状态 |

**账号状态值:**
| 值 | 常量 | 说明 |
|----|------|------|
| -1 | ACCOUNT_STATUS_INVALID | 无效 |
| 0 | ACCOUNT_STATUS_OK | 正常 |
| 1 | ACCOUNT_STATUS_WAITING_LOGIN | 连接中 |
| 2 | ACCOUNT_STATUSING | 登录中 |
| 3 | ACCOUNT_STATUS_FAIL | 失败 |
| 4 | ACCOUNT_STATUS_INITING | 初始化中 |
| 5 | ACCOUNT_STATUS_CORRECTING | 数据刷新校正中 |
| 6 | ACCOUNT_STATUS_CLOSED | 收盘后 |

---

### XtSmtAppointmentResponse

约券异步接口回报结构。

**属性:**
| 属性 | 类型 | 说明 |
|------|------|------|
| seq | int | 异步请求序号 |
| success | bool | 申请是否成功 |
| msg | str | 反馈信息 |
| apply_id | str | 资券申请编号 |

---

### XtBankTransferResponse

银证转账异步回报结构。

**属性:**
| 属性 | 类型 | 说明 |
|------|------|------|
| seq | int | 异步请求序号 |
| success | bool | 是否成功 |
| msg | str | 反馈信息 |

---

## 使用示例

### 创建账号

```python
from xtquant.xttype import StockAccount

# 普通股票账号
stock_account = StockAccount("1234567890", "STOCK")

# 信用账号
credit_account = StockAccount("1234567890", "CREDIT")

# 期货账号
future_account = StockAccount("1234567890", "FUTURE")
```

### 解析资产数据

```python
asset = trader.query_stock_asset(account)

print(f"=== 资产信息 ===")
print(f"资金账号: {asset.account_id}")
print(f"可用资金: {asset.cash:.2f}")
print(f"冻结资金: {asset.frozen_cash:.2f}")
print(f"持仓市值: {asset.market_value:.2f}")
print(f"总资产: {asset.total_asset:.2f}")
print(f"可取资金: {asset.fetch_balance:.2f}")
```

### 解析持仓数据

```python
positions = trader.query_stock_positions(account)

print("=== 持仓信息 ===")
for pos in positions:
    profit = (pos.last_price - pos.avg_price) * pos.volume
    print(f"{pos.stock_code} {pos.instrument_name}")
    print(f"  持仓: {pos.volume}股, 可用: {pos.can_use_volume}股")
    print(f"  成本: {pos.avg_price:.3f}, 现价: {pos.last_price:.3f}")
    print(f"  市值: {pos.market_value:.2f}, 盈亏: {profit:.2f}")
```

### 解析委托数据

```python
orders = trader.query_stock_orders(account)

print("=== 当日委托 ===")
for order in orders:
    direction = "买入" if order.order_type == 23 else "卖出"
    status = order.status_msg or f"状态码:{order.order_status}"
    print(f"[{order.order_id}] {order.stock_code} {direction} {order.order_volume}股")
    print(f"  委托价: {order.price}, 成交: {order.traded_volume}股@{order.traded_price}")
    print(f"  状态: {status}")
```

### 解析成交数据

```python
trades = trader.query_stock_trades(account)

print("=== 当日成交 ===")
for trade in trades:
    direction = "买入" if trade.order_type == 23 else "卖出"
    print(f"[{trade.traded_id}] {trade.stock_code} {direction}")
    print(f"  {trade.traded_volume}股 @ {trade.traded_price}")
    print(f"  成交额: {trade.traded_amount:.2f}, 手续费: {trade.commission:.2f}")
```
