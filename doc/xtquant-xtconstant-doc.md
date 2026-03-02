# XtQuant xtconstant 模块接口文档

> 生成时间: 2026-03-02
> 基于源码: `/opt/homebrew/Caskroom/miniconda/base/envs/dev/lib/python3.13/site-packages/xtquant/xtconstant.py`

---

## 目录

- [账号类型](#账号类型)
- [委托类型](#委托类型)
- [报价类型](#报价类型)
- [市场类型](#市场类型)
- [委托状态](#委托状态)
- [账号状态](#账号状态)

---

## 账号类型

```python
from xtquant import xtconstant

# 使用示例
account = StockAccount("8888888888", "STOCK")
# 或使用常量判断账号类型
if account.account_type == xtconstant.SECURITY_ACCOUNT:
    print("股票账号")
```

| 常量 | 值 | 说明 |
|------|-----|------|
| FUTURE_ACCOUNT | 1 | 期货账号 |
| SECURITY_ACCOUNT | 2 | 股票账号 |
| CREDIT_ACCOUNT | 3 | 信用账号 |
| FUTURE_OPTION_ACCOUNT | 5 | 期货期权账号 |
| STOCK_OPTION_ACCOUNT | 6 | 股票期权账号 |
| HUGANGTONG_ACCOUNT | 7 | 沪港通账号 |
| INCOME_SWAP_ACCOUNT | 8 | 美股收益互换 |
| NEW3BOARD_ACCOUNT | 10 | 全国股转账号 |
| SHENGANGTONG_ACCOUNT | 11 | 深港通账号 |
| AT_OFFSITEBANKING | 13 | 场外理财账户 |
| AT_OUTTER_FUTURE | 1001 | 期货外盘 |
| AT_IB | 1002 | IB |
| AT_NS_TRUSTBANK | 15001 | 场外托管 |
| AT_INTERBANK | 15002 | 银行间账号 |
| AT_BANK | 15003 | 银行账号 |
| AT_OTC | 15005 | 场外账号 |

---

## 委托类型

### 股票委托

```python
from xtquant import xtconstant

# 买入
order_id = trader.order_stock(
    account, "600000.SH",
    order_type=xtconstant.STOCK_BUY,
    order_volume=100,
    price_type=xtconstant.FIX_PRICE,
    price=10.5
)

# 卖出
order_id = trader.order_stock(
    account, "600000.SH",
    order_type=xtconstant.STOCK_SELL,
    order_volume=100,
    price_type=xtconstant.FIX_PRICE,
    price=10.5
)
```

| 常量 | 值 | 说明 |
|------|-----|------|
| STOCK_BUY | 23 | 股票买入 |
| STOCK_SELL | 24 | 股票卖出 |

### 信用交易委托

```python
# 融资买入
order_id = trader.order_stock(
    credit_account, "600000.SH",
    order_type=xtconstant.CREDIT_FIN_BUY,
    order_volume=100,
    price_type=xtconstant.FIX_PRICE,
    price=10.5
)

# 融券卖出
order_id = trader.order_stock(
    credit_account, "600000.SH",
    order_type=xtconstant.CREDIT_SLO_SELL,
    order_volume=100,
    price_type=xtconstant.FIX_PRICE,
    price=10.5
)
```

| 常量 | 值 | 说明 |
|------|-----|------|
| CREDIT_BUY | 23 | 担保品买入 |
| CREDIT_SELL | 24 | 担保品卖出 |
| CREDIT_FIN_BUY | 27 | 融资买入 |
| CREDIT_SLO_SELL | 28 | 融券卖出 |
| CREDIT_BUY_SECU_REPAY | 29 | 买券还券 |
| CREDIT_DIRECT_SECU_REPAY | 30 | 直接还券 |
| CREDIT_SELL_SECU_REPAY | 31 | 卖券还款 |
| CREDIT_DIRECT_CASH_REPAY | 32 | 直接还款 |

### 专项信用交易

| 常量 | 值 | 说明 |
|------|-----|------|
| CREDIT_FIN_BUY_SPECIAL | 40 | 专项融资买入 |
| CREDIT_SLO_SELL_SPECIAL | 41 | 专项融券卖出 |
| CREDIT_BUY_SECU_REPAY_SPECIAL | 42 | 专项买券还券 |
| CREDIT_DIRECT_SECU_REPAY_SPECIAL | 43 | 专项直接还券 |
| CREDIT_SELL_SECU_REPAY_SPECIAL | 44 | 专项卖券还款 |
| CREDIT_DIRECT_CASH_REPAY_SPECIAL | 45 | 专项直接还款 |

### 期货委托

```python
# 开多
order_id = trader.order_stock(
    future_account, "IF2401.CFFEX",
    order_type=xtconstant.FUTURE_OPEN_LONG,
    order_volume=1,
    price_type=xtconstant.FIX_PRICE,
    price=4000
)

# 平今多
order_id = trader.order_stock(
    future_account, "IF2401.CFFEX",
    order_type=xtconstant.FUTURE_CLOSE_LONG_TODAY,
    order_volume=1,
    price_type=xtconstant.FIX_PRICE,
    price=4000
)
```

#### 期货六键风格

| 常量 | 值 | 说明 |
|------|-----|------|
| FUTURE_OPEN_LONG | 0 | 开多 |
| FUTURE_CLOSE_LONG_HISTORY | 1 | 平昨多 |
| FUTURE_CLOSE_LONG_TODAY | 2 | 平今多 |
| FUTURE_OPEN_SHORT | 3 | 开空 |
| FUTURE_CLOSE_SHORT_HISTORY | 4 | 平昨空 |
| FUTURE_CLOSE_SHORT_TODAY | 5 | 平今空 |

#### 期货四键风格

| 常量 | 值 | 说明 |
|------|-----|------|
| FUTURE_CLOSE_LONG_TODAY_FIRST | 6 | 平多，优先平今 |
| FUTURE_CLOSE_LONG_HISTORY_FIRST | 7 | 平多，优先平昨 |
| FUTURE_CLOSE_SHORT_TODAY_FIRST | 8 | 平空，优先平今 |
| FUTURE_CLOSE_SHORT_HISTORY_FIRST | 9 | 平空，优先平昨 |

#### 期货两键风格

| 常量 | 值 | 说明 |
|------|-----|------|
| FUTURE_CLOSE_LONG_TODAY_HISTORY_THEN_OPEN_SHORT | 10 | 卖出，有多仓先平仓(优先平今)，余量开空 |
| FUTURE_CLOSE_LONG_HISTORY_TODAY_THEN_OPEN_SHORT | 11 | 卖出，有多仓先平仓(优先平昨)，余量开空 |
| FUTURE_CLOSE_SHORT_TODAY_HISTORY_THEN_OPEN_LONG | 12 | 买入，有空仓先平仓(优先平今)，余量开多 |
| FUTURE_CLOSE_SHORT_HISTORY_TODAY_THEN_OPEN_LONG | 13 | 买入，有空仓先平仓(优先平昨)，余量开多 |
| FUTURE_OPEN | 14 | 买入，不优先平仓 |
| FUTURE_CLOSE | 15 | 卖出，不优先平仓 |

### 股票期权委托

| 常量 | 值 | 说明 |
|------|-----|------|
| STOCK_OPTION_BUY_OPEN | 48 | 买入开仓 |
| STOCK_OPTION_SELL_CLOSE | 49 | 卖出平仓 |
| STOCK_OPTION_SELL_OPEN | 50 | 卖出开仓 |
| STOCK_OPTION_BUY_CLOSE | 51 | 买入平仓 |
| STOCK_OPTION_COVERED_OPEN | 52 | 备兑开仓 |
| STOCK_OPTION_COVERED_CLOSE | 53 | 备兑平仓 |
| STOCK_OPTION_CALL_EXERCISE | 54 | 认购行权 |
| STOCK_OPTION_PUT_EXERCISE | 55 | 认沽行权 |
| STOCK_OPTION_SECU_LOCK | 56 | 证券锁定 |
| STOCK_OPTION_SECU_UNLOCK | 57 | 证券解锁 |

### ETF申赎

| 常量 | 值 | 说明 |
|------|-----|------|
| ETF_PURCHASE | 134 | 申购 |
| ETF_REDEMPTION | 135 | 赎回 |

---

## 报价类型

```python
from xtquant import xtconstant

# 限价委托
order_id = trader.order_stock(
    account, "600000.SH",
    order_type=xtconstant.STOCK_BUY,
    order_volume=100,
    price_type=xtconstant.FIX_PRICE,  # 限价
    price=10.5
)

# 市价委托（最新价）
order_id = trader.order_stock(
    account, "600000.SH",
    order_type=xtconstant.STOCK_BUY,
    order_volume=100,
    price_type=xtconstant.LATEST_PRICE,  # 最新价
    price=0  # 市价时价格填0
)

# 对手方最优价
order_id = trader.order_stock(
    account, "600000.SH",
    order_type=xtconstant.STOCK_BUY,
    order_volume=100,
    price_type=xtconstant.MARKET_PEER_PRICE_FIRST,
    price=0
)
```

### 通用报价类型

| 常量 | 值 | 说明 |
|------|-----|------|
| LATEST_PRICE | 5 | 最新价 |
| FIX_PRICE | 11 | 限价/指定价 |

### 期货报价类型

| 常量 | 值 | 说明 | 适用交易所 |
|------|-----|------|------------|
| MARKET_BEST | 18 | 市价最优价 | 郑商所 |
| MARKET_CANCEL | 19 | 市价即成剩撤 | 大商所 |
| MARKET_CANCEL_ALL | 20 | 市价全额成交或撤 | 大商所 |
| MARKET_CANCEL_1 | 21 | 市价最优一档即成剩撤 | 中金所 |
| MARKET_CANCEL_5 | 22 | 市价最优五档即成剩撤 | 中金所 |
| MARKET_CONVERT_1 | 23 | 市价最优一档即成剩转 | 中金所 |
| MARKET_CONVERT_5 | 24 | 市价最优五档即成剩转 | 中金所 |

### 股票报价类型

| 常量 | 值 | 说明 | 适用交易所 |
|------|-----|------|------------|
| MARKET_SH_CONVERT_5_CANCEL | 42 | 最优五档即时成交剩余撤销 | 上交所/北交所 |
| MARKET_SH_CONVERT_5_LIMIT | 43 | 最优五档即时成交剩转限价 | 上交所/北交所 |
| MARKET_PEER_PRICE_FIRST | 44 | 对手方最优价格委托 | 上交所/深交所/北交所 |
| MARKET_MINE_PRICE_FIRST | 45 | 本方最优价格委托 | 上交所/深交所/北交所 |
| MARKET_SZ_INSTBUSI_RESTCANCEL | 46 | 即时成交剩余撤销委托 | 深交所 |
| MARKET_SZ_CONVERT_5_CANCEL | 47 | 最优五档即时成交剩余撤销 | 深交所 |
| MARKET_SZ_FULL_OR_CANCEL | 48 | 全额成交或撤销委托 | 深交所 |

---

## 市场类型

### 整数枚举

| 常量 | 值 | 说明 |
|------|-----|------|
| SH_MARKET | 0 | 上海市场 |
| SZ_MARKET | 1 | 深圳市场 |
| MARKET_ENUM_INDEX_FUTURE | 2 | 中金所 |
| MARKET_ENUM_SHANGHAI_FUTURE | 3 | 上期所 |
| MARKET_ENUM_DALIANG_FUTURE | 4 | 大商所 |
| MARKET_ENUM_ZHENGZHOU_FUTURE | 5 | 郑商所 |
| MARKET_ENUM_INTL_ENERGY_FUTURE | 6 | 能源中心 |
| MARKET_ENUM_SHANGHAI_STOCK_OPTION | 7 | 上海期权 |
| MARKET_ENUM_BEIJING | 70 | 北交所 |
| MARKET_ENUM_SHENZHEN_STOCK_OPTION | 67 | 深圳期权 |
| MARKET_ENUM_GUANGZHOU_FUTURE | 75 | 广期所 |

### 字符串常量

| 常量 | 值 | 说明 |
|------|-----|------|
| MARKET_SHANGHAI | 'SH' | 上交所 |
| MARKET_SHENZHEN | 'SZ' | 深交所 |
| MARKET_BEIJING | 'BJ' | 北交所 |
| MARKET_INDEX_FUTURE | 'IF' | 中金所 |
| MARKET_SHANGHAI_FUTURE | 'SF' | 上期所 |
| MARKET_DALIANG_FUTURE | 'DF' | 大商所 |
| MARKET_ZHENGZHOU_FUTURE | 'ZF' | 郑商所 |
| MARKET_INTL_ENERGY_FUTURE | 'INE' | 能源中心 |
| MARKET_GUANGZHOU_FUTURE | 'GF' | 广期所 |
| MARKET_SHANGHAI_STOCK_OPTION | 'SHO' | 上海期权 |
| MARKET_SHENZHEN_STOCK_OPTION | 'SZO' | 深圳期权 |

---

## 委托状态

```python
from xtquant import xtconstant

# 判断委托状态
if order.order_status == xtconstant.ORDER_SUCCEEDED:
    print("委托已全部成交")
elif order.order_status == xtconstant.ORDER_JUNK:
    print(f"废单: {order.status_msg}")
```

| 常量 | 值 | 说明 |
|------|-----|------|
| ORDER_UNREPORTED | 48 | 未报 |
| ORDER_WAIT_REPORTING | 49 | 待报 |
| ORDER_REPORTED | 50 | 已报 |
| ORDER_REPORTED_CANCEL | 51 | 已报待撤 |
| ORDER_PARTSUCC_CANCEL | 52 | 部成待撤 |
| ORDER_PART_CANCEL | 53 | 部撤 |
| ORDER_CANCELED | 54 | 已撤 |
| ORDER_PART_SUCC | 55 | 部成 |
| ORDER_SUCCEEDED | 56 | 已成 |
| ORDER_JUNK | 57 | 废单 |
| ORDER_UNKNOWN | 255 | 未知 |

---

## 账号状态

```python
from xtquant import xtconstant

def on_account_status(self, status):
    if status.status == xtconstant.ACCOUNT_STATUS_OK:
        print(f"账号 {status.account_id} 正常")
    elif status.status == xtconstant.ACCOUNT_STATUS_FAIL:
        print(f"账号 {status.account_id} 连接失败")
```

| 常量 | 值 | 说明 |
|------|-----|------|
| ACCOUNT_STATUS_INVALID | -1 | 无效 |
| ACCOUNT_STATUS_OK | 0 | 正常 |
| ACCOUNT_STATUS_WAITING_LOGIN | 1 | 连接中 |
| ACCOUNT_STATUSING | 2 | 登录中 |
| ACCOUNT_STATUS_FAIL | 3 | 失败 |
| ACCOUNT_STATUS_INITING | 4 | 初始化中 |
| ACCOUNT_STATUS_CORRECTING | 5 | 数据刷新校正中 |
| ACCOUNT_STATUS_CLOSED | 6 | 收盘后 |
| ACCOUNT_STATUS_ASSIS_FAIL | 7 | 穿透副链接断开 |
| ACCOUNT_STATUS_DISABLEBYSYS | 8 | 系统停用（密码错误超限） |
| ACCOUNT_STATUS_DISABLEBYUSER | 9 | 用户停用 |

---

## 快速参考

### 股票交易常用

```python
# 买入限价
order_type = xtconstant.STOCK_BUY      # 23
price_type = xtconstant.FIX_PRICE      # 11

# 卖出限价
order_type = xtconstant.STOCK_SELL     # 24
price_type = xtconstant.FIX_PRICE      # 11

# 市价买入
order_type = xtconstant.STOCK_BUY
price_type = xtconstant.LATEST_PRICE   # 5

# 对手方最优买入
order_type = xtconstant.STOCK_BUY
price_type = xtconstant.MARKET_PEER_PRICE_FIRST  # 44
```

### 信用交易常用

```python
# 融资买入
order_type = xtconstant.CREDIT_FIN_BUY  # 27

# 融券卖出
order_type = xtconstant.CREDIT_SLO_SELL  # 28

# 买券还券
order_type = xtconstant.CREDIT_BUY_SECU_REPAY  # 29

# 卖券还款
order_type = xtconstant.CREDIT_SELL_SECU_REPAY  # 31
```

### 期货交易常用

```python
# 开多
order_type = xtconstant.FUTURE_OPEN_LONG  # 0

# 开空
order_type = xtconstant.FUTURE_OPEN_SHORT  # 3

# 平今多
order_type = xtconstant.FUTURE_CLOSE_LONG_TODAY  # 2

# 平昨空
order_type = xtconstant.FUTURE_CLOSE_SHORT_HISTORY  # 4
```
