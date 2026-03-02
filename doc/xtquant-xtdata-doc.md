# XtQuant xtdata 模块接口文档

> 生成时间: 2026-03-02
> 基于源码: `/opt/homebrew/Caskroom/miniconda/base/envs/dev/lib/python3.13/site-packages/xtquant/xtdata.py`

---

## 目录

- [连接管理](#连接管理)
- [行情订阅](#行情订阅)
- [历史行情数据](#历史行情数据)
- [实时行情数据](#实时行情数据)
- [财务数据](#财务数据)
- [板块管理](#板块管理)
- [合约信息](#合约信息)
- [交易日历](#交易日历)
- [期权相关](#期权相关)
- [数据下载](#数据下载)
- [策略/模型](#策略模型)
- [工具函数](#工具函数)
- [数据周期](#数据周期)
- [数据字段](#数据字段)

---

## 连接管理

### connect(ip='', port=None, remember_if_success=True)

连接到 xtquant 服务。

**参数:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| ip | str | '' | 服务器IP地址 |
| port | int/tuple | None | 端口号或端口范围 |
| remember_if_success | bool | True | 是否记住连接参数 |

**返回:** client 对象

**异常:** 连接失败时抛出异常

```python
# 连接本地服务
client = xtdata.connect()

# 连接远程服务
client = xtdata.connect('192.168.1.100', 58610)
```

---

### reconnect(ip='', port=None, remember_if_success=True)

重新连接服务。

**参数:** 同 `connect()`

---

### disconnect()

断开与服务端的连接。

```python
xtdata.disconnect()
```

---

### get_client()

获取当前连接的客户端对象，如果未连接则自动重连。

**返回:** client 对象

---

### get_data_dir()

获取数据目录路径。

**返回:** str - 数据目录路径

---

## 行情订阅

### subscribe_quote(stock_code, period='1d', start_time='', end_time='', count=0, callback=None)

订阅单只股票行情数据。

**参数:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| stock_code | str | - | 股票代码，如 "000001.SZ" |
| period | str | '1d' | 周期：tick/1m/5m/1d 等 |
| start_time | str/datetime | '' | 开始时间，如 "20240101" |
| end_time | str/datetime | '' | 结束时间 |
| count | int | 0 | 数据数量，-1为全部 |
| callback | function | None | 回调函数 |

**回调函数格式:**
```python
def on_subscribe(datas):
    # datas: {stock: [data1, data2, ...]}
    pass
```

**返回:** int - 订阅序号

```python
def on_data(datas):
    print(datas)

seq = xtdata.subscribe_quote("000001.SZ", "1m", callback=on_data)
```

---

### subscribe_quote2(stock_code, period='1d', start_time='', end_time='', count=0, dividend_type=None, callback=None)

订阅行情数据（支持复权）。

**参数:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| dividend_type | str | None | 除权类型：none/front/back/front_ratio/back_ratio |

其他参数同 `subscribe_quote()`

---

### subscribe_whole_quote(code_list, callback=None)

订阅全推行情数据。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| code_list | list | 市场列表 ['SH', 'SZ'] 或股票列表 ['600000.SH'] |
| callback | function | 回调函数 |

**返回:** int - 订阅序号

```python
def on_data(datas):
    # datas: {stock1: data1, stock2: data2, ...}
    print(datas)

# 订阅整个市场
seq = xtdata.subscribe_whole_quote(['SH', 'SZ'], on_data)

# 订阅指定股票
seq = xtdata.subscribe_whole_quote(['600000.SH', '000001.SZ'], on_data)
```

**返回数据字段:**
| 字段 | 说明 |
|------|------|
| time | 时间戳 |
| lastPrice | 最新价 |
| open | 开盘价 |
| high | 最高价 |
| low | 最低价 |
| lastClose | 前收盘价 |
| amount | 成交额 |
| volume | 成交量 |
| askPrice | 卖价档位 [1-5] |
| bidPrice | 买价档位 [1-5] |
| askVol | 卖量档位 [1-5] |
| bidVol | 买量档位 [1-5] |

---

### subscribe_l2thousand(stock_code, gear_num=None, callback=None)

订阅千档盘口。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| stock_code | str | 股票代码 |
| gear_num | int | 档位数，None 表示全部 |
| callback | function | 回调函数 |

**返回:** int - 订阅号

```python
def on_data(data):
    print(data)
seq = xtdata.subscribe_l2thousand('000001.SZ', gear_num=10, callback=on_data)
```

---

### subscribe_l2thousand_queue(stock_code, callback=None, gear_num=None, price=None)

订阅千档盘口队列。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| stock_code | str | 股票代码 |
| callback | function | 回调函数 |
| gear_num | int | 档位数 |
| price | float/list/tuple | 价格档位：单个价格/多个价格/价格范围 |

```python
# 订阅买卖2档
seq = xtdata.subscribe_l2thousand_queue('000001.SZ', callback=on_data, gear_num=2)

# 订阅指定价格范围
seq = xtdata.subscribe_l2thousand_queue('000001.SZ', callback=on_data, price=(11.3, 11.4))
```

---

### unsubscribe_quote(seq)

取消订阅。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| seq | int | 订阅接口返回的订阅号 |

```python
xtdata.unsubscribe_quote(seq)
```

---

### run()

阻塞当前线程，持续接收行情回调。

```python
xtdata.subscribe_quote("000001.SZ", "1m", callback=on_data)
xtdata.run()  # 阻塞接收回调
```

---

## 历史行情数据

### get_market_data(field_list=[], stock_list=[], period='1d', start_time='', end_time='', count=-1, dividend_type='none', fill_data=True)

获取历史行情数据。

**参数:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| field_list | list | [] | 字段列表，[]为全部字段 |
| stock_list | list | [] | 股票代码列表 |
| period | str | '1d' | 周期 |
| start_time | str | '' | 开始时间 "20200101" |
| end_time | str | '' | 结束时间 "20201231" |
| count | int | -1 | 数量，-1全部，n从结束时间向前数n个 |
| dividend_type | str | 'none' | 除权类型 |
| fill_data | bool | True | 是否填充缺失数据 |

**返回:**
- period 为 'tick' 时: `{stock: np.ndarray}`
- 其他周期: `{field: pd.DataFrame}` - index 为股票代码，columns 为时间

```python
data = xtdata.get_market_data(
    field_list=['open', 'high', 'low', 'close', 'volume'],
    stock_list=['000001.SZ', '600000.SH'],
    period='1d',
    start_time='20240101',
    end_time='20240131'
)
print(data['close'])
```

---

### get_market_data_ex(field_list=[], stock_list=[], period='1d', start_time='', end_time='', count=-1, dividend_type='none', fill_data=True)

获取历史行情数据（扩展版）。

**返回:** `{stock: pd.DataFrame}` - 每只股票一个 DataFrame，index 为时间

```python
data = xtdata.get_market_data_ex(
    field_list=[],
    stock_list=['000001.SZ'],
    period='1d',
    start_time='20240101',
    end_time='20240131'
)
print(data['000001.SZ'])
```

---

### get_local_data(field_list=[], stock_list=[], period='1d', start_time='', end_time='', count=-1, dividend_type='none', fill_data=True, data_dir=None)

从本地文件获取历史数据（不请求服务器）。

**参数:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| data_dir | str | None | 数据目录，None 使用默认目录 |

其他参数同 `get_market_data_ex()`

---

### get_market_data3(...)

`get_market_data_ex()` 的别名，参数相同。

---

## 实时行情数据

### get_full_tick(code_list)

获取最新 tick 数据。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| code_list | list | 股票代码列表 |

**返回:** dict - `{stock: {tick_data}}`

```python
ticks = xtdata.get_full_tick(['000001.SZ', '600000.SH'])
print(ticks['000001.SZ'])
```

---

### get_l2_quote(field_list=[], stock_code='', start_time='', end_time='', count=-1)

获取 Level2 实时行情快照。

**返回:** np.ndarray

---

### get_l2_order(field_list=[], stock_code='', start_time='', end_time='', count=-1)

获取 Level2 逐笔委托数据。

**返回:** np.ndarray

---

### get_l2_transaction(field_list=[], stock_code='', start_time='', end_time='', count=-1)

获取 Level2 逐笔成交数据。

**返回:** np.ndarray

---

### get_l2thousand_queue(stock_code, gear_num=None, price=None)

获取千档盘口队列数据。

**返回:** dict

---

### get_transactioncount(code_list)

获取大单统计数据。

**返回:** dict

---

### get_fullspeed_orderbook(code_list)

获取全速盘口数据。

**返回:** dict

---

### get_full_kline(field_list=[], stock_list=[], period='1m', start_time='', end_time='', count=1, dividend_type='none', fill_data=True)

K线全推获取最新交易日数据。

**返回:** `{field: pd.DataFrame}`

---

## 财务数据

### get_financial_data(stock_list, table_list=[], start_time='', end_time='', report_type='report_time')

获取财务数据。

**参数:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| stock_list | list | - | 股票代码列表 |
| table_list | list | [] | 报表名称列表 |
| start_time | str | '' | 开始时间 |
| end_time | str | '' | 结束时间 |
| report_type | str | 'report_time' | 时段筛选：announce_time/report_time |

**可选报表:**
| 表名 | 说明 |
|------|------|
| Balance | 资产负债表 |
| Income | 利润表 |
| CashFlow | 现金流量表 |
| Capital | 股本结构 |
| HolderNum | 股东人数 |
| Top10Holder | 十大股东 |
| Top10FlowHolder | 十大流通股东 |
| PershareIndex | 每股指标 |

**返回:** `{stock: {table: pd.DataFrame}}`

```python
data = xtdata.get_financial_data(
    stock_list=['000001.SZ'],
    table_list=['Balance', 'Income'],
    start_time='20230101',
    end_time='20231231'
)
print(data['000001.SZ']['Balance'])
```

---

### download_financial_data(stock_list, table_list=[], start_time='', end_time='', incrementally=None)

下载财务数据到本地。

---

### download_financial_data2(stock_list, table_list=[], start_time='', end_time='', callback=None)

下载财务数据（带回调）。

---

## 板块管理

### get_sector_list()

获取板块列表。

**返回:** list[str] - 板块名称列表

```python
sectors = xtdata.get_sector_list()
print(sectors)  # ['沪深A股', '上证A股', '深证A股', ...]
```

---

### get_sector_info(sector_name='')

获取板块信息。

**参数:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| sector_name | str | '' | 板块名称，空则获取所有 |

**返回:** pd.DataFrame - 包含 sector 和 category 列

---

### get_stock_list_in_sector(sector_name, real_timetag=-1)

获取板块成分股。

**参数:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| sector_name | str | - | 板块名称 |
| real_timetag | str/int | -1 | 时间戳或日期字符串，-1为最新 |

**返回:** list[str] - 股票代码列表

```python
# 获取最新成分股
stocks = xtdata.get_stock_list_in_sector('沪深A股')

# 获取历史成分股
stocks = xtdata.get_stock_list_in_sector('沪深A股', '20230101')
```

---

### get_index_weight(index_code)

获取指数权重。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| index_code | str | 指数代码 |

**返回:** dict - `{stock: weight}`

```python
weights = xtdata.get_index_weight('000300.SH')
```

---

### create_sector_folder(parent_node, folder_name, overwrite=True)

创建板块目录节点。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| parent_node | str | 父节点，''为'我的'目录 |
| folder_name | str | 目录名称 |
| overwrite | bool | True跳过，False自动编号 |

---

### create_sector(parent_node, sector_name, overwrite=True)

创建板块。

---

### add_sector(sector_name, stock_list)

增加自定义板块。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| sector_name | str | 板块名称 |
| stock_list | list | 股票代码列表 |

```python
xtdata.add_sector('我的自选', ['000001.SZ', '600000.SH'])
```

---

### remove_stock_from_sector(sector_name, stock_list)

从板块中移除股票。

---

### remove_sector(sector_name)

删除自定义板块。

---

### reset_sector(sector_name, stock_list)

重置板块成分股。

---

### download_sector_data()

下载行业板块数据。

---

## 合约信息

### get_instrument_detail(stock_code, iscomplete=False)

获取合约信息。

**参数:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| stock_code | str | - | 股票代码 |
| iscomplete | bool | False | 是否返回完整信息 |

**返回:** dict

**主要字段:**
| 字段 | 类型 | 说明 |
|------|------|------|
| ExchangeID | str | 市场代码 |
| InstrumentID | str | 合约代码 |
| InstrumentName | str | 合约名称 |
| ProductID | str | 品种ID |
| ProductName | str | 品种名称 |
| CreateDate | str | 上市日期 |
| ExpireDate | str | 到期日 |
| PreClose | float | 前收盘价 |
| UpStopPrice | float | 涨停价 |
| DownStopPrice | float | 跌停价 |
| FloatVolume | float | 流通股本 |
| TotalVolume | float | 总股本 |
| PriceTick | float | 最小变价单位 |
| VolumeMultiple | int | 合约乘数 |
| MainContract | int | 主力合约标记 |
| IsTrading | bool | 是否可交易 |

```python
info = xtdata.get_instrument_detail('000001.SZ')
print(info['InstrumentName'])
```

---

### get_instrument_detail_list(stock_list, iscomplete=False)

批量获取合约信息。

**返回:** `{stock: info_dict}`

---

### get_instrument_type(stock_code, variety_list=None)

判断证券类型。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| stock_code | str | 股票代码 |
| variety_list | list | 品种列表，None返回全部 |

**返回:** dict - `{类型名: 是否属于该类型}`

---

### get_markets()

获取所有可选市场。

**返回:** dict - `{市场代码: 市场名称}`

```python
markets = xtdata.get_markets()
# {'SH': '上交所', 'SZ': '深交所', 'BJ': '北交所', ...}
```

---

### get_wp_market_list()

获取外盘市场列表。

---

### get_ipo_info(start_time='', end_time='')

获取IPO信息。

**返回字段:**
| 字段 | 说明 |
|------|------|
| securityCode | 证券代码 |
| codeName | 代码简称 |
| publishPrice | 发行价格 |
| startDate | 申购开始日期 |
| listedDate | 上市日期 |
| lwr | 中签率 |

---

## 交易日历

### get_trading_dates(market, start_time='', end_time='', count=-1)

获取交易日列表。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| market | str | 市场代码：SH/SZ/IF/DF/SF/ZF 等 |
| start_time | str | 开始时间 |
| end_time | str | 结束时间 |
| count | int | 数量，-1为全部 |

**返回:** list[int] - 毫秒时间戳列表

```python
dates = xtdata.get_trading_dates('SH', '20240101', '20240131')
```

---

### get_trading_calendar(market, start_time='', end_time='')

获取交易日历（包含未来交易日）。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| market | str | 市场，仅支持 SH/SZ |
| start_time | str | 开始时间 |
| end_time | str | 结束时间 |

**返回:** list[str] - 日期字符串列表

---

### get_holidays()

获取节假日列表。

**返回:** list[str] - 日期字符串列表

```python
holidays = xtdata.get_holidays()
```

---

### get_divid_factors(stock_code, start_time='', end_time='')

获取除权除息因子。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| stock_code | str | 股票代码 |
| start_time | str | 开始时间 |
| end_time | str | 结束时间 |

**返回:** pd.DataFrame

```python
factors = xtdata.get_divid_factors('000001.SZ', '20200101', '20241231')
```

---

## 期权相关

### get_option_detail_data(optioncode)

获取期权合约详情。

**返回:** dict

**主要字段:**
| 字段 | 说明 |
|------|------|
| optType | 期权类型：CALL/PUT |
| OptExercisePrice | 行权价 |
| OptUndlCode | 标的代码 |
| EndDelivDate | 到期日 |

---

### get_option_undl_data(undl_code_ref)

获取标的对应的所有期权列表。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| undl_code_ref | str | 标的代码，空则返回全部 |

**返回:** list 或 dict

---

### get_option_list(undl_code, dedate, opttype='', isavailavle=False)

获取指定日期可交易的期权列表。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| undl_code | str | 标的代码 |
| dedate | str | 日期 |
| opttype | str | 期权类型：C/CALL/P/PUT |
| isavailavle | bool | 是否只返回可交易的 |

**返回:** list[str]

---

### get_his_option_list(undl_code, dedate)

获取历史上某日的期权信息列表。

**返回:** pd.DataFrame

---

### get_his_option_list_batch(undl_code, start_time='', end_time='')

批量获取历史期权信息。

**返回:** `{date: pd.DataFrame}`

---

## 数据下载

### download_history_data(stock_code, period, start_time='', end_time='', incrementally=None)

下载历史数据。

**参数:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| stock_code | str | - | 品种代码 |
| period | str | - | 数据周期 |
| start_time | str | '' | 开始时间 |
| end_time | str | '' | 结束时间 |
| incrementally | bool | None | 是否增量下载，None根据start_time判断 |

```python
# 下载全部历史数据
xtdata.download_history_data('000001.SZ', '1d')

# 下载指定时间段
xtdata.download_history_data('000001.SZ', '1d', '20230101', '20231231')
```

---

### download_history_data2(stock_list, period, start_time='', end_time='', callback=None, incrementally=None)

批量下载历史数据（支持回调）。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| stock_list | list | 股票代码列表 |
| callback | function | 进度回调函数 |

**回调格式:**
```python
def on_progress(data):
    # data: {'finished': n, 'total': m}
    print(f"{data['finished']}/{data['total']}")
```

---

### download_index_weight()

下载指数权重数据。

---

### download_history_contracts(incrementally=True)

下载过期合约数据。

---

### download_holiday_data(incrementally=True)

下载节假日数据。

---

### download_etf_info()

下载 ETF 申赎信息。

---

### download_cb_data()

下载可转债数据。

---

### download_his_st_data()

下载历史 ST 数据。

---

## 策略/模型

### subscribe_formula(formula_name, stock_code, period, start_time='', end_time='', count=-1, dividend_type=None, extend_param={}, callback=None)

订阅策略模型。

**返回:** int - 模型ID (request_id)

---

### get_formula_result(request_id, start_time='', end_time='', count=-1, timeout_second=-1)

获取模型结果。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| request_id | int | 模型ID |
| timeout_second | int | 等待时间，-1无限，0立即返回 |

**返回:** dict

---

### call_formula(formula_name, stock_code, period, start_time='', end_time='', count=-1, dividend_type=None, extend_param={})

同步调用策略模型。

**返回:** dict

---

### bind_formula(request_id, callback=None)

绑定模型回调。

---

### unsubscribe_formula(request_id)

取消订阅模型。

---

### create_formula(formula_name, formula_content, formula_params={})

创建策略。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| formula_name | str | 策略名称 |
| formula_content | str | 策略内容 |
| formula_params | dict | 策略参数 |

---

### import_formula(formula_name, file_path)

导入策略文件（.rzrk）。

---

### del_formula(formula_name)

删除策略。

---

### get_formulas()

查询所有策略。

---

## 工具函数

### get_main_contract(code_market, start_time='', end_time='')

获取主力合约。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| code_market | str | 主力连续合约代码，如 "IF00.IF" |
| start_time | str | 开始时间 |
| end_time | str | 结束时间 |

**返回:**
- 无时间参数: str - 当前主力合约
- 有 start_time: str - 指定日期主力合约
- 有 start_time 和 end_time: pd.Series - 时间序列

```python
# 当前主力
code = xtdata.get_main_contract("IF00.IF")

# 历史主力序列
series = xtdata.get_main_contract("IF00.IF", "20230101", "20240101")
```

---

### get_sec_main_contract(code_market, start_time='', end_time='')

获取次主力合约。参数同 `get_main_contract()`。

---

### get_cb_info(stockcode)

获取可转债信息。

**返回:** dict

---

### get_etf_info()

获取 ETF 申赎信息。

**返回:** dict

---

### get_his_st_data(stock_code)

获取历史 ST 状态数据。

**返回:** dict - `{status: [[start, end], ...]}`

---

### timetag_to_datetime(timetag, format)

将毫秒时间戳转换为日期时间字符串。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| timetag | int | 毫秒时间戳 |
| format | str | 时间格式，如 "%Y%m%d" |

**返回:** str

```python
date_str = xtdata.timetag_to_datetime(1704067200000, '%Y%m%d')
```

---

### datetime_to_timetag(datetime, format='%Y%m%d%H%M%S')

将日期时间字符串转换为毫秒时间戳。

**返回:** int

---

### read_feather(file_path)

读取 feather 格式文件。

**返回:** (param_dict, pd.DataFrame)

---

### write_feather(dest_path, param, df)

写入 feather 格式文件。

---

## 数据周期

### K线周期

| 周期 | 说明 |
|------|------|
| tick | 分笔数据 |
| 1m | 1分钟K线 |
| 5m | 5分钟K线 |
| 15m | 15分钟K线 |
| 30m | 30分钟K线 |
| 60m/1h | 60分钟K线 |
| 1d | 日K线 |
| 1w | 周K线 |
| 1mon | 月K线 |

### Level2 周期

| 周期 | 说明 |
|------|------|
| l2quote | Level2行情快照 |
| l2quoteaux | Level2行情快照补充 |
| l2order | Level2逐笔委托 |
| l2transaction | Level2逐笔成交 |
| l2transactioncount | Level2大单统计 |
| l2orderqueue | Level2委买委卖队列 |

### 特殊周期

| 周期 | 说明 |
|------|------|
| transactioncount1m | Level1逐笔成交统计1分钟 |
| transactioncount1d | Level1逐笔成交统计日线 |
| warehousereceipt | 期货仓单 |
| futureholderrank | 期货席位 |
| interactiveqa | 互动问答 |

---

## 数据字段

### K线字段

| 字段 | 说明 |
|------|------|
| time | 时间戳 |
| open | 开盘价 |
| high | 最高价 |
| low | 最低价 |
| close | 收盘价 |
| volume | 成交量 |
| amount | 成交额 |
| settle | 今结算（期货） |
| openInterest | 持仓量（期货） |

### 分笔字段

| 字段 | 说明 |
|------|------|
| time | 时间戳 |
| lastPrice | 最新价 |
| open | 开盘价 |
| high | 最高价 |
| low | 最低价 |
| lastClose | 前收盘价 |
| amount | 成交总额 |
| volume | 成交总量 |
| pvolume | 原始成交总量 |
| stockStatus | 证券状态 |
| openInt | 持仓量 |
| lastSettlementPrice | 前结算 |
| askPrice1-5 | 卖一价~卖五价 |
| bidPrice1-5 | 买一价~买五价 |
| askVol1-5 | 卖一量~卖五量 |
| bidVol1-5 | 买一量~买五量 |

---

## 除权类型

| 类型 | 说明 |
|------|------|
| none | 不复权 |
| front | 前复权 |
| back | 后复权 |
| front_ratio | 等比前复权 |
| back_ratio | 等比后复权 |

---

## 市场代码

| 代码 | 市场 |
|------|------|
| SH | 上交所 |
| SZ | 深交所 |
| BJ | 北交所 |
| HK | 港交所 |
| HGT | 沪港通 |
| SGT | 深港通 |
| IF | 中金所 |
| SF/SHFE | 上期所 |
| DF/DCE | 大商所 |
| ZF/CZCE | 郑商所 |
| GF/GFEX | 广期所 |
| INE | 能源交易所 |
| SHO | 上证期权 |
| SZO | 深证期权 |

---

## 简写函数

xtdata 提供了以下简写别名：

| 简写 | 原函数 |
|------|--------|
| gmd | get_market_data |
| gmd2 | get_market_data_ex |
| gmd3 | get_market_data3 |
| gld | get_local_data |
| t2d | timetag_to_datetime |
| gsl | get_stock_list_in_sector |

```python
# 使用简写
data = xtdata.gmd([], ['000001.SZ'], '1d')
stocks = xtdata.gsl('沪深A股')
```
