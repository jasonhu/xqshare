"""
XtQuant Share (xqshare) Server Permission Tests

测试服务端权限检查逻辑
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, MagicMock, patch

# 确保在导入 server 之前 mock xtquant
import sys
from unittest.mock import MagicMock
mock_xtquant = MagicMock()
mock_xtdata = MagicMock()
mock_xttrader = MagicMock()
mock_xttype = MagicMock()
mock_xtquant.xtdata = mock_xtdata
mock_xtquant.xttrader = mock_xttrader
mock_xtquant.xttype = mock_xttype
sys.modules['xtquant'] = mock_xtquant
sys.modules['xtquant.xtdata'] = mock_xtdata
sys.modules['xtquant.xttrader'] = mock_xttrader
sys.modules['xtquant.xttype'] = mock_xttype

# 初始化日志
from xqshare.server import _init_logging
_init_logging("WARNING")

# 导入反序列化函数（服务端返回的是序列化数据，测试时需要反序列化）
from xqshare.client import _deserialize_from_transfer

from xqshare.server import (
    XtQuantService,
    LoggingProxy,
    AuthError,
)
from xqshare.auth import (
    Permission,
    AccountLevel,
    PermissionChecker,
    PermissionError as AuthPermissionError,
    reset_permission_checker,
)


class TestServiceAuthenticate:
    """测试服务端认证流程"""

    def setup_method(self):
        """每个测试前重置"""
        reset_permission_checker()
        XtQuantService._permission_checker = None

    def test_authenticate_free_user(self, mock_service):
        """测试 FREE 用户认证返回 free 等级"""
        result = mock_service.exposed_authenticate("free-user", "free-secret")

        assert result["success"] is True
        assert result["level"] == "free"
        assert mock_service._authenticated is True
        assert mock_service._account_level == AccountLevel.FREE

    def test_authenticate_plus_user(self, mock_service):
        """测试 PLUS 用户认证返回 plus 等级"""
        result = mock_service.exposed_authenticate("plus-user", "plus-secret")

        assert result["success"] is True
        assert result["level"] == "plus"
        assert mock_service._account_level == AccountLevel.PLUS

    def test_authenticate_standard_user(self, mock_service):
        """测试 STANDARD 用户认证返回 standard 等级"""
        result = mock_service.exposed_authenticate("standard-user", "standard-secret")

        assert result["success"] is True
        assert result["level"] == "standard"
        assert mock_service._account_level == AccountLevel.STANDARD

    def test_authenticate_premium_user(self, mock_service):
        """测试 PREMIUM 用户认证返回 premium 等级"""
        result = mock_service.exposed_authenticate("premium-user", "premium-secret")

        assert result["success"] is True
        assert result["level"] == "premium"
        assert mock_service._account_level == AccountLevel.PREMIUM

    def test_authenticate_enterprise_user(self, mock_service):
        """测试 ENTERPRISE 用户认证返回 enterprise 等级"""
        result = mock_service.exposed_authenticate("enterprise-user", "enterprise-secret")

        assert result["success"] is True
        assert result["level"] == "enterprise"
        assert mock_service._account_level == AccountLevel.ENTERPRISE

    def test_authenticate_invalid_secret(self, mock_service):
        """测试无效密钥抛出 AuthError"""
        with pytest.raises(AuthError) as exc_info:
            mock_service.exposed_authenticate("free-user", "wrong-secret")

        assert "无效的客户端凭证" in str(exc_info.value)

    def test_authenticate_unknown_user(self, mock_service):
        """测试未知用户认证失败"""
        with pytest.raises(AuthError):
            mock_service.exposed_authenticate("unknown-user", "any-secret")


class TestLoggingProxyPermission:
    """测试 LoggingProxy 权限检查"""

    def setup_method(self):
        """每个测试前重置"""
        reset_permission_checker()

    def _create_proxy(self, mock_target, level):
        """创建带权限检查的代理"""
        checker = PermissionChecker()
        return LoggingProxy(
            mock_target, 'xtdata',
            lambda: "test-client",
            checker,
            level
        )

    def test_free_user_basic_api(self):
        """测试 FREE 用户可调用 basic API"""
        mock_xtdata = MagicMock()
        mock_xtdata.get_stock_list_in_sector.return_value = ["000001.SZ"]

        proxy = self._create_proxy(mock_xtdata, AccountLevel.FREE)
        result = proxy.get_stock_list_in_sector("沪深A股")

        assert _deserialize_from_transfer(result) == ["000001.SZ"]
        mock_xtdata.get_stock_list_in_sector.assert_called_once_with("沪深A股")

    def test_free_user_daily_api(self):
        """测试 FREE 用户可调用 daily API (period=1d)"""
        mock_xtdata = MagicMock()
        mock_xtdata.get_market_data.return_value = {"000001.SZ": {}}

        proxy = self._create_proxy(mock_xtdata, AccountLevel.FREE)
        result = proxy.get_market_data(["000001.SZ"], "1d")

        assert _deserialize_from_transfer(result) == {"000001.SZ": {}}

    def test_free_user_minute_api_denied(self):
        """测试 FREE 用户调用 minute API 被拒绝"""
        mock_xtdata = MagicMock()

        proxy = self._create_proxy(mock_xtdata, AccountLevel.FREE)

        with pytest.raises(AuthPermissionError) as exc_info:
            proxy.get_market_data(["000001.SZ"], "5m")

        assert exc_info.value.permission == Permission.MINUTE
        mock_xtdata.get_market_data.assert_not_called()

    def test_plus_user_minute_api(self):
        """测试 PLUS 用户可调用 minute API"""
        mock_xtdata = MagicMock()
        mock_xtdata.get_market_data.return_value = {"000001.SZ": {}}

        proxy = self._create_proxy(mock_xtdata, AccountLevel.PLUS)
        result = proxy.get_market_data(["000001.SZ"], "5m")

        assert _deserialize_from_transfer(result) == {"000001.SZ": {}}

    def test_plus_user_tick_api_denied(self):
        """测试 PLUS 用户调用 tick API 被拒绝"""
        mock_xtdata = MagicMock()

        proxy = self._create_proxy(mock_xtdata, AccountLevel.PLUS)

        with pytest.raises(AuthPermissionError) as exc_info:
            proxy.get_market_data(["000001.SZ"], "tick")

        assert exc_info.value.permission == Permission.TICK

    def test_plus_user_1m_api_denied(self):
        """测试 PLUS 用户调用 1m API 被拒绝 (1m 属于 tick 权限)"""
        mock_xtdata = MagicMock()

        proxy = self._create_proxy(mock_xtdata, AccountLevel.PLUS)

        with pytest.raises(AuthPermissionError) as exc_info:
            proxy.get_market_data(["000001.SZ"], "1m")

        assert exc_info.value.permission == Permission.TICK

    def test_standard_user_tick_api(self):
        """测试 STANDARD 用户可调用 tick API"""
        mock_xtdata = MagicMock()
        mock_xtdata.get_market_data.return_value = {"000001.SZ": {}}

        proxy = self._create_proxy(mock_xtdata, AccountLevel.STANDARD)
        result = proxy.get_market_data(["000001.SZ"], "tick")

        assert _deserialize_from_transfer(result) == {"000001.SZ": {}}

    def test_standard_user_1m_api(self):
        """测试 STANDARD 用户可调用 1m API"""
        mock_xtdata = MagicMock()
        mock_xtdata.get_market_data.return_value = {"000001.SZ": {}}

        proxy = self._create_proxy(mock_xtdata, AccountLevel.STANDARD)
        result = proxy.get_market_data(["000001.SZ"], "1m")

        assert _deserialize_from_transfer(result) == {"000001.SZ": {}}

    def test_standard_user_get_full_tick(self):
        """测试 STANDARD 用户可调用 get_full_tick"""
        mock_xtdata = MagicMock()
        mock_xtdata.get_full_tick.return_value = {"000001.SZ": {"lastPrice": 10.5}}

        proxy = self._create_proxy(mock_xtdata, AccountLevel.STANDARD)
        result = proxy.get_full_tick(["000001.SZ"])

        assert _deserialize_from_transfer(result) == {"000001.SZ": {"lastPrice": 10.5}}

    def test_financial_data_permission(self):
        """测试财务数据权限 (minute 级别)"""
        mock_xtdata = MagicMock()
        mock_xtdata.get_financial_data.return_value = {}

        # FREE 用户不能调用
        proxy = self._create_proxy(mock_xtdata, AccountLevel.FREE)
        with pytest.raises(AuthPermissionError) as exc_info:
            proxy.get_financial_data("000001.SZ")
        assert exc_info.value.permission == Permission.MINUTE

        # PLUS 用户可以调用
        proxy = self._create_proxy(mock_xtdata, AccountLevel.PLUS)
        result = proxy.get_financial_data("000001.SZ")
        assert _deserialize_from_transfer(result) == {}

    def test_callback_permission(self):
        """测试回调权限"""
        mock_xtdata = MagicMock()
        mock_xtdata.subscribe_whole_quote.return_value = None

        # PLUS 用户不能调用
        proxy = self._create_proxy(mock_xtdata, AccountLevel.PLUS)
        with pytest.raises(AuthPermissionError) as exc_info:
            proxy.subscribe_whole_quote("000001.SZ", lambda x: None)
        assert exc_info.value.permission == Permission.CALLBACK

        # STANDARD 用户可以调用
        proxy = self._create_proxy(mock_xtdata, AccountLevel.STANDARD)
        result = proxy.subscribe_whole_quote("000001.SZ", lambda x: None)
        assert _deserialize_from_transfer(result) is None

    def test_get_full_kline_permission(self):
        """测试 get_full_kline 权限检测"""
        mock_xtdata = MagicMock()
        mock_xtdata.get_full_kline.return_value = []

        # FREE 用户可以调用日线
        proxy = self._create_proxy(mock_xtdata, AccountLevel.FREE)
        proxy.get_full_kline("000001.SZ", "1d")
        assert mock_xtdata.get_full_kline.called

        # FREE 用户不能调用分钟线
        mock_xtdata.reset_mock()
        with pytest.raises(AuthPermissionError):
            proxy.get_full_kline("000001.SZ", "5m")

        # PLUS 用户不能调用 tick
        proxy = self._create_proxy(mock_xtdata, AccountLevel.PLUS)
        with pytest.raises(AuthPermissionError):
            proxy.get_full_kline("000001.SZ", "tick")

        # STANDARD 用户可以调用 tick
        proxy = self._create_proxy(mock_xtdata, AccountLevel.STANDARD)
        proxy.get_full_kline("000001.SZ", "tick")
        assert mock_xtdata.get_full_kline.called


class TestServiceTradePermission:
    """测试 trade 相关权限"""

    def setup_method(self):
        """每个测试前重置"""
        reset_permission_checker()
        XtQuantService._permission_checker = None

    def test_get_xttrader_permission(self, mock_service):
        """测试 get_xttrader 权限检查"""
        # 先认证 STANDARD 用户
        mock_service.exposed_authenticate("standard-user", "standard-secret")

        # STANDARD 用户不能调用 get_xttrader
        with pytest.raises(AuthPermissionError) as exc_info:
            mock_service.exposed_get_xttrader()

        assert exc_info.value.permission == Permission.TRADE

    def test_get_xttrader_premium_user(self, mock_service):
        """测试 PREMIUM 用户可调用 get_xttrader"""
        # 先认证 PREMIUM 用户
        mock_service.exposed_authenticate("premium-user", "premium-secret")

        # PREMIUM 用户可以调用
        result = mock_service.exposed_get_xttrader()
        assert result is not None

    def test_create_trader_permission(self, mock_service):
        """测试 create_trader 权限检查"""
        # 先认证 STANDARD 用户
        mock_service.exposed_authenticate("standard-user", "standard-secret")

        # STANDARD 用户不能调用 create_trader
        with pytest.raises(AuthPermissionError) as exc_info:
            mock_service.exposed_create_trader()

        assert exc_info.value.permission == Permission.TRADE

    def test_create_trader_premium_user(self, mock_service):
        """测试 PREMIUM 用户可调用 create_trader"""
        # 先认证 PREMIUM 用户
        mock_service.exposed_authenticate("premium-user", "premium-secret")

        # PREMIUM 用户可以调用 (但会因为 mock 而失败，这里只测试权限)
        # 由于 XtQuantTrader 在 mock 环境下是 MagicMock，调用会成功
        try:
            result = mock_service.exposed_create_trader()
        except AuthPermissionError:
            pytest.fail("PREMIUM 用户应该可以调用 create_trader")


class TestPeriodDynamicPermission:
    """测试 period 参数动态权限检测"""

    def setup_method(self):
        """每个测试前重置"""
        reset_permission_checker()

    def _create_proxy(self, mock_target, level):
        """创建带权限检查的代理"""
        checker = PermissionChecker()
        return LoggingProxy(
            mock_target, 'xtdata',
            lambda: "test-client",
            checker,
            level
        )

    def test_period_1d_free_allowed(self):
        """测试 period=1d FREE 用户允许"""
        mock_xtdata = MagicMock()
        proxy = self._create_proxy(mock_xtdata, AccountLevel.FREE)

        proxy.get_market_data(["000001.SZ"], "1d")
        assert mock_xtdata.get_market_data.called

    def test_period_1w_free_allowed(self):
        """测试 period=1w FREE 用户允许"""
        mock_xtdata = MagicMock()
        proxy = self._create_proxy(mock_xtdata, AccountLevel.FREE)

        proxy.get_market_data(["000001.SZ"], "1w")
        assert mock_xtdata.get_market_data.called

    def test_period_5m_plus_allowed(self):
        """测试 period=5m PLUS 用户允许"""
        mock_xtdata = MagicMock()
        proxy = self._create_proxy(mock_xtdata, AccountLevel.PLUS)

        proxy.get_market_data(["000001.SZ"], "5m")
        assert mock_xtdata.get_market_data.called

    def test_period_1h_plus_allowed(self):
        """测试 period=1h PLUS 用户允许"""
        mock_xtdata = MagicMock()
        proxy = self._create_proxy(mock_xtdata, AccountLevel.PLUS)

        proxy.get_market_data(["000001.SZ"], "1h")
        assert mock_xtdata.get_market_data.called

    def test_period_tick_standard_allowed(self):
        """测试 period=tick STANDARD 用户允许"""
        mock_xtdata = MagicMock()
        proxy = self._create_proxy(mock_xtdata, AccountLevel.STANDARD)

        proxy.get_market_data(["000001.SZ"], "tick")
        assert mock_xtdata.get_market_data.called

    def test_period_1m_standard_allowed(self):
        """测试 period=1m STANDARD 用户允许"""
        mock_xtdata = MagicMock()
        proxy = self._create_proxy(mock_xtdata, AccountLevel.STANDARD)

        proxy.get_market_data(["000001.SZ"], "1m")
        assert mock_xtdata.get_market_data.called

    def test_period_via_kwargs(self):
        """测试 period 通过 kwargs 传递"""
        mock_xtdata = MagicMock()
        proxy = self._create_proxy(mock_xtdata, AccountLevel.PLUS)

        proxy.get_market_data_ex(stock_list=["000001.SZ"], period="15m")
        assert mock_xtdata.get_market_data_ex.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])