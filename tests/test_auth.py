"""
XtQuant Share (xqshare) Auth Module Tests
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch

from xqshare.auth import (
    Permission,
    AccountLevel,
    LEVEL_PERMISSIONS,
    API_PERMISSIONS,
    MINUTE_PERIODS,
    DAILY_PERIODS,
    TICK_PERIODS,
    PermissionError,
    ClientConfig,
    PermissionChecker,
    get_permission_checker,
    reset_permission_checker,
)


class TestPermissionEnums:
    """测试权限枚举"""

    def test_permission_values(self):
        """测试权限枚举值"""
        assert Permission.BASIC.value == "basic"
        assert Permission.DAILY.value == "daily"
        assert Permission.MINUTE.value == "minute"
        assert Permission.TICK.value == "tick"
        assert Permission.TRADE.value == "trade"
        assert Permission.CALLBACK.value == "callback"

    def test_account_level_values(self):
        """测试账号等级枚举值"""
        assert AccountLevel.FREE.value == "free"
        assert AccountLevel.PLUS.value == "plus"
        assert AccountLevel.STANDARD.value == "standard"
        assert AccountLevel.PREMIUM.value == "premium"
        assert AccountLevel.ENTERPRISE.value == "enterprise"


class TestLevelPermissions:
    """测试账号等级权限映射"""

    def test_free_permissions(self):
        """测试免费用户权限"""
        perms = LEVEL_PERMISSIONS[AccountLevel.FREE]
        assert Permission.BASIC in perms
        assert Permission.DAILY in perms
        assert Permission.MINUTE not in perms
        assert Permission.TICK not in perms
        assert Permission.TRADE not in perms
        assert Permission.CALLBACK not in perms

    def test_plus_permissions(self):
        """测试进阶用户权限"""
        perms = LEVEL_PERMISSIONS[AccountLevel.PLUS]
        assert Permission.BASIC in perms
        assert Permission.DAILY in perms
        assert Permission.MINUTE in perms
        assert Permission.TICK not in perms
        assert Permission.TRADE not in perms
        assert Permission.CALLBACK not in perms

    def test_standard_permissions(self):
        """测试标准用户权限"""
        perms = LEVEL_PERMISSIONS[AccountLevel.STANDARD]
        assert Permission.BASIC in perms
        assert Permission.DAILY in perms
        assert Permission.MINUTE in perms
        assert Permission.TICK in perms
        assert Permission.CALLBACK in perms
        assert Permission.TRADE not in perms

    def test_premium_permissions(self):
        """测试高级用户权限"""
        perms = LEVEL_PERMISSIONS[AccountLevel.PREMIUM]
        assert Permission.BASIC in perms
        assert Permission.DAILY in perms
        assert Permission.MINUTE in perms
        assert Permission.TICK in perms
        assert Permission.CALLBACK in perms
        assert Permission.TRADE in perms

    def test_enterprise_permissions(self):
        """测试企业用户权限"""
        perms = LEVEL_PERMISSIONS[AccountLevel.ENTERPRISE]
        assert Permission.BASIC in perms
        assert Permission.DAILY in perms
        assert Permission.MINUTE in perms
        assert Permission.TICK in perms
        assert Permission.CALLBACK in perms
        assert Permission.TRADE in perms


class TestPeriodSets:
    """测试周期集合"""

    def test_minute_periods(self):
        """测试分钟线周期"""
        assert "5m" in MINUTE_PERIODS
        assert "15m" in MINUTE_PERIODS
        assert "30m" in MINUTE_PERIODS
        assert "1h" in MINUTE_PERIODS
        assert "1m" not in MINUTE_PERIODS  # 1m 属于 tick 权限

    def test_daily_periods(self):
        """测试日线周期"""
        assert "1d" in DAILY_PERIODS
        assert "1w" in DAILY_PERIODS
        assert "1mon" in DAILY_PERIODS
        assert "1q" in DAILY_PERIODS
        assert "1hy" in DAILY_PERIODS
        assert "1y" in DAILY_PERIODS

    def test_tick_periods(self):
        """测试 tick 周期"""
        assert "tick" in TICK_PERIODS
        assert "1m" in TICK_PERIODS  # 1m 属于 tick 权限


class TestClientConfig:
    """测试客户端配置"""

    def test_from_dict_default(self):
        """测试默认配置"""
        config = ClientConfig.from_dict({})
        assert config.secret == ""
        assert config.level == AccountLevel.FREE

    def test_from_dict_with_values(self):
        """测试带值的配置"""
        config = ClientConfig.from_dict({
            "secret": "my-secret",
            "level": "plus"
        })
        assert config.secret == "my-secret"
        assert config.level == AccountLevel.PLUS

    def test_from_dict_invalid_level(self):
        """测试无效等级"""
        config = ClientConfig.from_dict({
            "secret": "my-secret",
            "level": "invalid"
        })
        assert config.level == AccountLevel.FREE

    def test_from_dict_level_case_insensitive(self):
        """测试等级大小写不敏感"""
        config = ClientConfig.from_dict({"level": "PREMIUM"})
        assert config.level == AccountLevel.PREMIUM


class TestPermissionError:
    """测试权限错误"""

    def test_error_message(self):
        """测试错误消息"""
        error = PermissionError(Permission.TICK, "get_full_tick", AccountLevel.FREE)
        assert "get_full_tick" in str(error)
        assert "tick" in str(error)
        assert "free" in str(error)
        assert error.permission == Permission.TICK
        assert error.method == "get_full_tick"
        assert error.level == AccountLevel.FREE


class TestPermissionChecker:
    """测试权限检查器"""

    def test_init_default_path(self):
        """测试默认路径初始化"""
        checker = PermissionChecker()
        assert checker.config_path.endswith("clients.yaml")

    def test_init_custom_path(self):
        """测试自定义路径初始化"""
        checker = PermissionChecker("/custom/path/config.yaml")
        assert checker.config_path == "/custom/path/config.yaml"

    def test_load_config_file_not_exists(self):
        """测试配置文件不存在"""
        checker = PermissionChecker("/nonexistent/path/config.yaml")
        assert checker._clients == {}

    def test_load_config_from_file(self):
        """测试从文件加载配置"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
clients:
  app1:
    secret: "secret-app1"
    level: plus
  app2:
    secret: "secret-app2"
    level: premium
""")
            f.flush()
            checker = PermissionChecker(f.name)

            assert "app1" in checker._clients
            assert "app2" in checker._clients
            assert checker._clients["app1"].level == AccountLevel.PLUS
            assert checker._clients["app2"].level == AccountLevel.PREMIUM

    def test_verify_secret_from_config(self):
        """测试从配置验证密钥"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
clients:
  app1:
    secret: "secret-app1"
    level: standard
""")
            f.flush()
            checker = PermissionChecker(f.name)

            valid, level = checker.verify_secret("app1", "secret-app1")
            assert valid is True
            assert level == AccountLevel.STANDARD

            valid, level = checker.verify_secret("app1", "wrong-secret")
            assert valid is False
            assert level is None

    def test_verify_secret_from_env(self):
        """测试从环境变量验证密钥"""
        with patch.dict(os.environ, {"XTQUANT_CLIENT_app1": "env-secret"}):
            checker = PermissionChecker("/nonexistent/path/config.yaml")

            valid, level = checker.verify_secret("app1", "env-secret")
            assert valid is True
            assert level == AccountLevel.FREE

    def test_verify_secret_default(self):
        """测试默认密钥验证"""
        with patch.dict(os.environ, {"XTQUANT_CLIENT_SECRET": "default-secret"}):
            checker = PermissionChecker("/nonexistent/path/config.yaml")

            valid, level = checker.verify_secret("unknown", "default-secret")
            assert valid is True
            assert level == AccountLevel.FREE

    def test_has_permission(self):
        """测试权限检查"""
        checker = PermissionChecker()

        # FREE 用户
        assert checker.has_permission(AccountLevel.FREE, Permission.BASIC) is True
        assert checker.has_permission(AccountLevel.FREE, Permission.DAILY) is True
        assert checker.has_permission(AccountLevel.FREE, Permission.MINUTE) is False
        assert checker.has_permission(AccountLevel.FREE, Permission.TICK) is False
        assert checker.has_permission(AccountLevel.FREE, Permission.TRADE) is False

        # PLUS 用户
        assert checker.has_permission(AccountLevel.PLUS, Permission.MINUTE) is True
        assert checker.has_permission(AccountLevel.PLUS, Permission.TICK) is False

        # STANDARD 用户
        assert checker.has_permission(AccountLevel.STANDARD, Permission.TICK) is True
        assert checker.has_permission(AccountLevel.STANDARD, Permission.TRADE) is False

        # PREMIUM 用户
        assert checker.has_permission(AccountLevel.PREMIUM, Permission.TRADE) is True


class TestAPIDynamicPermission:
    """测试 API 动态权限检测"""

    def setup_method(self):
        """每个测试前重置权限检查器"""
        reset_permission_checker()
        self.checker = PermissionChecker()

    def test_basic_api_permission(self):
        """测试 basic 权限 API"""
        # FREE 用户可以调用
        error = self.checker.check_api_permission(
            AccountLevel.FREE, "xtdata.get_stock_list_in_sector"
        )
        assert error is None

        # 所有等级都可以调用
        error = self.checker.check_api_permission(
            AccountLevel.FREE, "xtdata.get_sector_list"
        )
        assert error is None

    def test_daily_permission_with_period_1d(self):
        """测试日线权限 (period=1d)"""
        # FREE 用户可以调用
        error = self.checker.check_api_permission(
            AccountLevel.FREE, "xtdata.get_market_data",
            args=(["000001.SZ"], "1d")
        )
        assert error is None

        # period 通过 kwargs 传递
        error = self.checker.check_api_permission(
            AccountLevel.FREE, "xtdata.get_market_data_ex",
            kwargs={"period": "1d"}
        )
        assert error is None

    def test_minute_permission_with_period_5m(self):
        """测试分钟线权限 (period=5m)"""
        # FREE 用户不能调用
        error = self.checker.check_api_permission(
            AccountLevel.FREE, "xtdata.get_market_data",
            args=(["000001.SZ"], "5m")
        )
        assert error is not None
        assert error.permission == Permission.MINUTE

        # PLUS 用户可以调用
        error = self.checker.check_api_permission(
            AccountLevel.PLUS, "xtdata.get_market_data",
            args=(["000001.SZ"], "5m")
        )
        assert error is None

    def test_tick_permission_with_period_tick(self):
        """测试 tick 权限 (period=tick)"""
        # PLUS 用户不能调用
        error = self.checker.check_api_permission(
            AccountLevel.PLUS, "xtdata.get_market_data",
            args=(["000001.SZ"], "tick")
        )
        assert error is not None
        assert error.permission == Permission.TICK

        # STANDARD 用户可以调用
        error = self.checker.check_api_permission(
            AccountLevel.STANDARD, "xtdata.get_market_data",
            args=(["000001.SZ"], "tick")
        )
        assert error is None

    def test_tick_permission_with_period_1m(self):
        """测试 tick 权限 (period=1m)"""
        # PLUS 用户不能调用 (1m 属于 tick 权限)
        error = self.checker.check_api_permission(
            AccountLevel.PLUS, "xtdata.get_market_data",
            args=(["000001.SZ"], "1m")
        )
        assert error is not None
        assert error.permission == Permission.TICK

        # STANDARD 用户可以调用
        error = self.checker.check_api_permission(
            AccountLevel.STANDARD, "xtdata.get_market_data",
            args=(["000001.SZ"], "1m")
        )
        assert error is None

    def test_get_full_kline_permission(self):
        """测试 get_full_kline 权限"""
        # 日线 - FREE 用户可以
        error = self.checker.check_api_permission(
            AccountLevel.FREE, "xtdata.get_full_kline",
            args=(["000001.SZ"], "1d")
        )
        assert error is None

        # 分钟线 - FREE 用户不能
        error = self.checker.check_api_permission(
            AccountLevel.FREE, "xtdata.get_full_kline",
            args=(["000001.SZ"], "5m")
        )
        assert error is not None
        assert error.permission == Permission.MINUTE

        # tick - PLUS 用户不能
        error = self.checker.check_api_permission(
            AccountLevel.PLUS, "xtdata.get_full_kline",
            args=(["000001.SZ"], "tick")
        )
        assert error is not None
        assert error.permission == Permission.TICK

    def test_download_history_data2_permission(self):
        """测试 download_history_data2 权限"""
        # 日线 - FREE 用户可以
        error = self.checker.check_api_permission(
            AccountLevel.FREE, "download_history_data2",
            args=(["000001.SZ"], "1d")
        )
        assert error is None

        # 分钟线 - FREE 用户不能
        error = self.checker.check_api_permission(
            AccountLevel.FREE, "download_history_data2",
            args=(["000001.SZ"], "15m")
        )
        assert error is not None

    def test_financial_data_permission(self):
        """测试财务数据权限"""
        # 财务数据需要 minute 权限
        error = self.checker.check_api_permission(
            AccountLevel.FREE, "xtdata.get_financial_data"
        )
        assert error is not None
        assert error.permission == Permission.MINUTE

        # PLUS 用户可以
        error = self.checker.check_api_permission(
            AccountLevel.PLUS, "xtdata.get_financial_data"
        )
        assert error is None

    def test_trade_permission(self):
        """测试交易权限"""
        # STANDARD 用户不能交易
        error = self.checker.check_api_permission(
            AccountLevel.STANDARD, "get_xttrader"
        )
        assert error is not None
        assert error.permission == Permission.TRADE

        # PREMIUM 用户可以
        error = self.checker.check_api_permission(
            AccountLevel.PREMIUM, "get_xttrader"
        )
        assert error is None

    def test_callback_permission(self):
        """测试回调权限"""
        # PLUS 用户不能使用回调
        error = self.checker.check_api_permission(
            AccountLevel.PLUS, "xtdata.subscribe_whole_quote"
        )
        assert error is not None
        assert error.permission == Permission.CALLBACK

        # STANDARD 用户可以
        error = self.checker.check_api_permission(
            AccountLevel.STANDARD, "xtdata.subscribe_whole_quote"
        )
        assert error is None

    def test_unknown_api_free_denied(self):
        """测试未配置的 API - FREE 用户被拒绝"""
        error = self.checker.check_api_permission(
            AccountLevel.FREE, "xtdata.some_unknown_api"
        )
        assert error is not None
        assert error.permission == Permission.BASIC

    def test_unknown_api_plus_denied(self):
        """测试未配置的 API - PLUS 用户被拒绝"""
        error = self.checker.check_api_permission(
            AccountLevel.PLUS, "xtdata.some_unknown_api"
        )
        assert error is not None
        assert error.permission == Permission.BASIC

    def test_unknown_api_standard_allowed(self):
        """测试未配置的 API - STANDARD 用户允许"""
        error = self.checker.check_api_permission(
            AccountLevel.STANDARD, "xtdata.some_unknown_api"
        )
        assert error is None

    def test_unknown_api_premium_allowed(self):
        """测试未配置的 API - PREMIUM 用户允许"""
        error = self.checker.check_api_permission(
            AccountLevel.PREMIUM, "xtdata.some_unknown_api"
        )
        assert error is None

    def test_period_extraction_from_kwargs(self):
        """测试从 kwargs 提取 period"""
        error = self.checker.check_api_permission(
            AccountLevel.FREE, "xtdata.get_market_data",
            kwargs={"period": "1h"}
        )
        # FREE 用户没有 minute 权限，1h 属于 minute
        assert error is not None

    def test_period_default_1d(self):
        """测试 period 默认为 1d"""
        # 没有 period 参数时默认 1d
        error = self.checker.check_api_permission(
            AccountLevel.FREE, "xtdata.get_market_data",
            args=(["000001.SZ"],)
        )
        assert error is None


class TestGlobalPermissionChecker:
    """测试全局权限检查器"""

    def setup_method(self):
        """每个测试前重置"""
        reset_permission_checker()

    def test_get_permission_checker_singleton(self):
        """测试单例模式"""
        checker1 = get_permission_checker()
        checker2 = get_permission_checker()
        assert checker1 is checker2

    def test_get_permission_checker_with_path(self):
        """测试带路径获取"""
        checker = get_permission_checker("/custom/path.yaml")
        assert checker.config_path == "/custom/path.yaml"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])