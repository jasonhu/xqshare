"""
xqshare 测试配置和 fixtures

由于本机是 Mac，xtquant 库不可用，需要 mock。
"""

import sys
import os
import pytest
import tempfile
from unittest.mock import MagicMock, patch


# ==================== Mock xtquant 模块 ====================

@pytest.fixture(scope="session", autouse=True)
def mock_xtquant():
    """
    Session 级别的 xtquant mock

    在所有测试开始前 mock xtquant 模块，避免导入错误。
    """
    # 创建 mock 模块
    mock_xtquant = MagicMock()
    mock_xtdata = MagicMock()
    mock_xttrader = MagicMock()
    mock_xttype = MagicMock()

    # 设置模块属性
    mock_xtquant.xtdata = mock_xtdata
    mock_xtquant.xttrader = mock_xttrader
    mock_xtquant.xttype = mock_xttype

    # Mock 常用函数返回值
    mock_xtdata.get_stock_list_in_sector.return_value = ["000001.SZ", "000002.SZ", "600000.SH"]
    mock_xtdata.get_index_list.return_value = ["000001.SH", "399001.SZ"]
    mock_xtdata.get_market_data.return_value = {"000001.SZ": {"open": 10.0, "close": 10.5}}
    mock_xtdata.get_market_data_ex.return_value = {"000001.SZ": {"open": 10.0, "close": 10.5}}
    mock_xtdata.get_full_tick.return_value = {"000001.SZ": {"lastPrice": 10.5}}
    mock_xtdata.get_instrument_detail.return_value = {"InstrumentName": "平安银行"}
    mock_xtdata.get_divid_factors.return_value = {}
    mock_xtdata.get_sector_list.return_value = ["沪深A股", "沪深指数"]
    mock_xtdata.get_full_kline.return_value = []
    mock_xtdata.download_history_data.return_value = None
    mock_xtdata.download_history_data2.return_value = None
    mock_xtdata.get_financial_data.return_value = {}
    mock_xtdata.download_financial_data.return_value = None
    mock_xtdata.download_financial_data2.return_value = None
    mock_xtdata.subscribe_whole_quote.return_value = None
    mock_xtdata.subscribe_full_tick.return_value = None
    mock_xtdata.subscribe_quote.return_value = None

    # Mock XtQuantTrader
    mock_trader_class = MagicMock()
    mock_xtquant.xttrader.XtQuantTrader = mock_trader_class

    # 注入到 sys.modules
    sys.modules['xtquant'] = mock_xtquant
    sys.modules['xtquant.xtdata'] = mock_xtdata
    sys.modules['xtquant.xttrader'] = mock_xttrader
    sys.modules['xtquant.xttype'] = mock_xttype

    yield {
        'xtquant': mock_xtquant,
        'xtdata': mock_xtdata,
        'xttrader': mock_xttrader,
        'xttype': mock_xttype,
    }

    # 清理
    for mod in ['xtquant', 'xtquant.xtdata', 'xtquant.xttrader', 'xtquant.xttype']:
        if mod in sys.modules:
            del sys.modules[mod]


# ==================== 权限测试 fixtures ====================

@pytest.fixture
def temp_config_file():
    """
    创建临时配置文件
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
clients:
  free-user:
    secret: "free-secret"
    level: free
  plus-user:
    secret: "plus-secret"
    level: plus
  standard-user:
    secret: "standard-secret"
    level: standard
  premium-user:
    secret: "premium-secret"
    level: premium
  enterprise-user:
    secret: "enterprise-secret"
    level: enterprise
""")
        f.flush()
        yield f.name

    # 清理
    os.unlink(f.name)


@pytest.fixture
def permission_checker(temp_config_file):
    """
    创建权限检查器实例
    """
    from xqshare.auth import PermissionChecker, reset_permission_checker
    reset_permission_checker()
    checker = PermissionChecker(temp_config_file)
    yield checker
    reset_permission_checker()


@pytest.fixture
def mock_service(permission_checker):
    """
    创建 mock 服务实例
    """
    from xqshare.server import XtQuantService
    from xqshare.auth import reset_permission_checker

    # 重置类级别的权限检查器
    XtQuantService._permission_checker = permission_checker

    # 创建服务实例
    service = XtQuantService()
    service._conn = MagicMock()
    service._conn.peer = "127.0.0.1:12345"
    service.on_connect(service._conn)

    yield service

    # 清理
    reset_permission_checker()
    XtQuantService._permission_checker = None


@pytest.fixture
def mock_xtdata():
    """
    创建 mock xtdata 对象
    """
    mock = MagicMock()
    mock.get_stock_list_in_sector.return_value = ["000001.SZ", "000002.SZ"]
    mock.get_market_data.return_value = {"000001.SZ": {"open": 10.0}}
    mock.get_full_tick.return_value = {"000001.SZ": {"lastPrice": 10.5}}
    return mock