# XtQuant xttrader 模块接口文档

> 生成时间: 2026-03-02
> 基于源码: `/opt/homebrew/Caskroom/miniconda/base/envs/dev/lib/python3.13/site-packages/xtquant/xttrader.py`

---

## 目录

- [交易类 XtQuantTrader](#交易类-xtquanttrader)
- [回调类 XtQuantTraderCallback](#回调类-xtquanttradercallback)
- [使用示例](#使用示例)

---

## 交易类 XtQuantTrader

### 构造函数

```python
XtQuantTrader(path, session, callback=None)
```

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| path | str | mini版迅投极速交易客户端 userdata 文件夹路径 |
| session | int | 当前任务执行所属的会话ID |
| callback | XtQuantTraderCallback | 回调方法 |

---

### 生命周期管理

#### start()

启动交易客户端。

```python
trader.start()
```

---

#### stop()

停止交易客户端。

```python
trader.stop()
```

---

#### connect()

建立连接。

**返回:** int - 0 表示成功

```python
result = trader.connect()
```

---

#### register_callback(callback)

注册回调对象。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| callback | XtQuantTraderCallback | 回调对象 |

---

#### run_forever()

阻塞运行。

---

#### sleep(time)

异步睡眠。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| time | float | 睡眠时间（秒） |

---

#### set_timeout(timeout=0)

设置超时时间。

---

### 订阅管理

#### subscribe(account)

订阅账号。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| account | StockAccount | 证券账号 |

**返回:** 订阅结果

```python
account = StockAccount("8888888888", "STOCK")
trader.subscribe(account)
```

---

#### unsubscribe(account)

取消订阅账号。

---

### 下单接口

#### order_stock(account, stock_code, order_type, order_volume, price_type, price, strategy_name='', order_remark='')

同步下单。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| account | StockAccount | 证券账号 |
| stock_code | str | 证券代码，如 "600000.SH" |
| order_type | int | 委托类型：23=买，24=卖 |
| order_volume | int | 委托数量（股/张） |
| price_type | int | 报价类型 |
| price | float | 报价价格 |
| strategy_name | str | 策略名称 |
| order_remark | str | 委托备注 |

**返回:** int - 订单ID，-1 表示失败

```python
order_id = trader.order_stock(
    account, "600000.SH",
    order_type=23,  # 买入
    order_volume=100,
    price_type=11,  # 限价
    price=10.5,
    strategy_name="my_strategy",
    order_remark="test_order"
)
```

---

#### order_stock_async(account, stock_code, order_type, order_volume, price_type, price, strategy_name='', order_remark='')

异步下单。

**返回:** int - 下单请求序号，-1 表示失败

回调通过 `on_order_stock_async_response` 接收。

---

### 撤单接口

#### cancel_order_stock(account, order_id)

同步撤单（按订单ID）。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| account | StockAccount | 证券账号 |
| order_id | int | 委托编号 |

**返回:** int - 0=成功，-1=失败

```python
result = trader.cancel_order_stock(account, order_id)
```

---

#### cancel_order_stock_async(account, order_id)

异步撤单（按订单ID）。

**返回:** int - 撤单请求序号

---

#### cancel_order_stock_sysid(account, market, sysid)

同步撤单（按柜台编号）。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| account | StockAccount | 证券账号 |
| market | int/str | 交易市场：0=上海，1=深圳，或 "SH"/"SZ" |
| sysid | str | 柜台合同编号 |

**返回:** int - 0=成功，-1=失败

---

#### cancel_order_stock_sysid_async(account, market, sysid)

异步撤单（按柜台编号）。

---

### 查询接口 - 账号

#### query_account_infos()

查询账号列表。

**返回:** list - 账号信息列表

---

#### query_account_infos_async(callback)

异步查询账号列表。

---

#### query_account_status()

查询账号状态。

**返回:** list - 账号状态列表

---

#### query_account_status_async(callback)

异步查询账号状态。

---

### 查询接口 - 资产

#### query_stock_asset(account)

查询资产。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| account | StockAccount | 证券账号 |

**返回:** XtAsset - 资产对象

```python
asset = trader.query_stock_asset(account)
print(f"可用资金: {asset.cash}")
print(f"总资产: {asset.total_asset}")
```

---

#### query_stock_asset_async(account, callback)

异步查询资产。

---

### 查询接口 - 委托

#### query_stock_order(account, order_id)

查询单个委托。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| account | StockAccount | 证券账号 |
| order_id | int | 订单编号 |

**返回:** XtOrder - 委托对象

---

#### query_stock_orders(account, cancelable_only=False)

查询所有委托。

**参数:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| account | StockAccount | - | 证券账号 |
| cancelable_only | bool | False | 仅查询可撤委托 |

**返回:** list[XtOrder] - 委托对象列表

```python
orders = trader.query_stock_orders(account)
for order in orders:
    print(f"委托号: {order.order_id}, 状态: {order.order_status}")
```

---

#### query_stock_orders_async(account, callback, cancelable_only=False)

异步查询所有委托。

---

### 查询接口 - 成交

#### query_stock_trades(account)

查询所有成交。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| account | StockAccount | 证券账号 |

**返回:** list[XtTrade] - 成交对象列表

```python
trades = trader.query_stock_trades(account)
for trade in trades:
    print(f"成交号: {trade.traded_id}, 价格: {trade.traded_price}")
```

---

#### query_stock_trades_async(account, callback)

异步查询所有成交。

---

### 查询接口 - 持仓

#### query_stock_position(account, stock_code)

查询单个持仓。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| account | StockAccount | 证券账号 |
| stock_code | str | 证券代码 |

**返回:** XtPosition - 持仓对象

---

#### query_stock_positions(account)

查询所有持仓。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| account | StockAccount | 证券账号 |

**返回:** list[XtPosition] - 持仓对象列表

```python
positions = trader.query_stock_positions(account)
for pos in positions:
    print(f"股票: {pos.stock_code}, 数量: {pos.volume}, 成本: {pos.avg_price}")
```

---

#### query_stock_positions_async(account, callback)

异步查询所有持仓。

---

### 查询接口 - 信用交易

#### query_credit_detail(account)

查询信用账户详情。

**返回:** dict

---

#### query_credit_detail_async(account, callback)

异步查询信用账户详情。

---

#### query_stk_compacts(account)

查询负债合约。

**返回:** list

---

#### query_stk_compacts_async(account, callback)

异步查询负债合约。

---

#### query_credit_subjects(account)

查询融资融券标的。

**返回:** list

---

#### query_credit_subjects_async(account, callback)

异步查询融资融券标的。

---

#### query_credit_slo_code(account)

查询可融券数据。

**返回:** list

---

#### query_credit_slo_code_async(account, callback)

异步查询可融券数据。

---

#### query_credit_assure(account)

查询标的担保品。

**返回:** list

---

#### query_credit_assure_async(account, callback)

异步查询标的担保品。

---

### 查询接口 - 新股申购

#### query_new_purchase_limit(account)

查询新股申购额度。

**返回:** dict

---

#### query_new_purchase_limit_async(account, callback)

异步查询新股申购额度。

---

## 回调类 XtQuantTraderCallback

继承此类实现回调方法。

```python
class MyCallback(XtQuantTraderCallback):
    def on_connected(self):
        print("连接成功")

    def on_disconnected(self):
        print("连接断开")

    def on_stock_order(self, order):
        print(f"委托回报: {order.order_id}")
```

---

### 回调方法

#### on_connected()

连接成功推送。

---

#### on_disconnected()

连接断开推送。

---

#### on_account_status(status)

账号状态变化推送。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| status | XtAccountStatus | 账号状态对象 |

---

#### on_stock_asset(asset)

资产变化推送。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| asset | XtAsset | 资产对象 |

---

#### on_stock_order(order)

委托变化推送。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| order | XtOrder | 委托对象 |

---

#### on_stock_trade(trade)

成交变化推送。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| trade | XtTrade | 成交对象 |

---

#### on_stock_position(position)

持仓变化推送。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| position | XtPosition | 持仓对象 |

---

#### on_order_error(order_error)

委托失败推送。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| order_error | XtOrderError | 委托失败对象 |

---

#### on_cancel_error(cancel_error)

撤单失败推送。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| cancel_error | XtCancelError | 撤单失败对象 |

---

#### on_order_stock_async_response(response)

异步下单回报。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| response | XtOrderResponse | 下单回报对象 |

---

#### on_cancel_order_stock_async_response(response)

异步撤单回报。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| response | XtCancelOrderResponse | 撤单回报对象 |

---

#### on_smt_appointment_async_response(response)

约券异步接口回报。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| response | XtSmtAppointmentResponse | 约券回报对象 |

---

#### on_bank_transfer_async_response(response)

银证转账异步回报。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| response | XtBankTransferResponse | 转账回报对象 |

---

## 使用示例

### 完整交易流程

```python
from xtquant import xttrader
from xtquant.xttype import StockAccount
from xtquant import xtconstant

# 1. 创建回调类
class MyCallback(xttrader.XtQuantTraderCallback):
    def on_connected(self):
        print("连接成功")

    def on_disconnected(self):
        print("连接断开")

    def on_stock_order(self, order):
        print(f"委托回报: {order.stock_code} {order.order_volume}股 "
              f"状态:{order.order_status}")

    def on_stock_trade(self, trade):
        print(f"成交回报: {trade.stock_code} {trade.traded_volume}股 "
              f"价格:{trade.traded_price}")

    def on_order_error(self, order_error):
        print(f"委托失败: {order_error.error_msg}")

# 2. 初始化交易对象
path = "C:/国金证券QMT交易端/userdata_mini"
session_id = 123456
trader = xttrader.XtQuantTrader(path, session_id, MyCallback())

# 3. 启动并连接
trader.start()
trader.connect()

# 4. 订阅账号
account = StockAccount("8888888888", "STOCK")
trader.subscribe(account)

# 5. 查询资产
asset = trader.query_stock_asset(account)
print(f"可用: {asset.cash}, 总资产: {asset.total_asset}")

# 6. 查询持仓
positions = trader.query_stock_positions(account)
for pos in positions:
    print(f"{pos.stock_code}: {pos.volume}股, 成本{pos.avg_price}")

# 7. 下单
order_id = trader.order_stock(
    account, "600000.SH",
    order_type=xtconstant.STOCK_BUY,
    order_volume=100,
    price_type=xtconstant.FIX_PRICE,
    price=10.5
)
print(f"委托号: {order_id}")

# 8. 撤单（如需要）
if order_id > 0:
    trader.cancel_order_stock(account, order_id)

# 9. 停止
trader.stop()
```

### 异步交易示例

```python
# 异步下单
seq = trader.order_stock_async(
    account, "000001.SZ",
    order_type=xtconstant.STOCK_BUY,
    order_volume=100,
    price_type=xtconstant.LATEST_PRICE,
    price=0
)
print(f"下单请求序号: {seq}")

# 回调在 on_order_stock_async_response 中接收
```

### 信用交易示例

```python
# 使用信用账号
credit_account = StockAccount("8888888888", "CREDIT")

# 融资买入
order_id = trader.order_stock(
    credit_account, "600000.SH",
    order_type=xtconstant.CREDIT_FIN_BUY,
    order_volume=100,
    price_type=xtconstant.FIX_PRICE,
    price=10.5
)

# 查询信用详情
detail = trader.query_credit_detail(credit_account)
```
