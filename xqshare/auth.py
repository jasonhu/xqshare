"""
xqshare 权限模块

实现多级账号权限控制，支持免费到企业级的 5 级账号体系。
"""

import os
import yaml
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Permission(Enum):
    """权限枚举"""
    BASIC = "basic"        # 基础信息
    DAILY = "daily"        # 日线数据
    MINUTE = "minute"      # 分钟线数据
    TICK = "tick"          # 实时行情
    TRADE = "trade"        # 交易功能
    CALLBACK = "callback"  # 回调功能


class AccountLevel(Enum):
    """账号等级枚举"""
    FREE = "free"
    PLUS = "plus"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


# 账号等级对应的权限组合
LEVEL_PERMISSIONS: Dict[AccountLevel, Set[Permission]] = {
    AccountLevel.FREE: {Permission.BASIC, Permission.DAILY},
    AccountLevel.PLUS: {Permission.BASIC, Permission.DAILY, Permission.MINUTE},
    AccountLevel.STANDARD: {Permission.BASIC, Permission.DAILY, Permission.MINUTE, Permission.TICK, Permission.CALLBACK},
    AccountLevel.PREMIUM: {Permission.BASIC, Permission.DAILY, Permission.MINUTE, Permission.TICK, Permission.TRADE, Permission.CALLBACK},
    AccountLevel.ENTERPRISE: {Permission.BASIC, Permission.DAILY, Permission.MINUTE, Permission.TICK, Permission.TRADE, Permission.CALLBACK},
}

# API 与权限的映射关系
# 格式: "module.method": Permission 或 "method": Permission
API_PERMISSIONS: Dict[str, Permission] = {
    # ==================== basic 权限 ====================
    "xtdata.get_stock_list_in_sector": Permission.BASIC,
    "xtdata.get_index_list": Permission.BASIC,
    "xtdata.get_instrument_detail": Permission.BASIC,
    "xtdata.get_divid_factors": Permission.BASIC,
    "xtdata.get_sector_list": Permission.BASIC,
    "get_all_stocks": Permission.BASIC,
    "get_index_list": Permission.BASIC,

    # ==================== daily 权限 ====================
    # get_market_data 和 get_market_data_ex 的 period 参数决定权限
    # 这里设置基础权限，实际检查时会根据 period 参数动态判断
    "xtdata.get_market_data": Permission.DAILY,
    "xtdata.get_market_data_ex": Permission.DAILY,
    "xtdata.get_full_kline": Permission.DAILY,
    "xtdata.download_history_data": Permission.DAILY,
    "xtdata.download_history_data2": Permission.DAILY,
    "download_history_data2": Permission.DAILY,

    # ==================== minute 权限 ====================
    "xtdata.get_financial_data": Permission.MINUTE,
    "xtdata.download_financial_data": Permission.MINUTE,
    "xtdata.download_financial_data2": Permission.MINUTE,

    # ==================== tick 权限 ====================
    "xtdata.get_full_tick": Permission.TICK,
    "xtdata.subscribe_quote": Permission.TICK,

    # ==================== trade 权限 ====================
    "get_xttrader": Permission.TRADE,
    "create_trader": Permission.TRADE,

    # ==================== callback 权限 ====================
    # 订阅类 API（包含 callback 参数）
    "xtdata.subscribe_whole_quote": Permission.CALLBACK,
    "xtdata.subscribe_full_tick": Permission.CALLBACK,
    "xtdata.subscribe_quote": Permission.CALLBACK,
    # 异步测试回调
    "test_async_callback": Permission.CALLBACK,
}

# 分钟/小时线周期列表（不含1m，1m属于tick权限）
MINUTE_PERIODS = {"5m", "15m", "30m", "1h"}
# 日线及以上周期列表
DAILY_PERIODS = {"1d", "1w", "1mon", "1q", "1hy", "1y"}
# Tick 周期（包含分笔和1分钟线）
TICK_PERIODS = {"tick", "1m"}

# 默认客户端配置（当配置文件不存在时使用）
DEFAULT_CLIENT_ID = "client-standard"
DEFAULT_CLIENT_SECRET = "xqshare-default-secret"


class PermissionError(Exception):
    """权限错误"""
    def __init__(self, permission: Permission, method: str, level: AccountLevel):
        self.permission = permission
        self.method = method
        self.level = level
        super().__init__(
            f"权限不足: 方法 '{method}' 需要 '{permission.value}' 权限，"
            f"当前账号等级 '{level.value}' 无此权限"
        )


@dataclass
class ClientConfig:
    """客户端配置"""
    secret: str
    level: AccountLevel = AccountLevel.FREE

    @classmethod
    def from_dict(cls, data: dict) -> "ClientConfig":
        """从字典创建配置"""
        level_str = data.get("level", "free")
        try:
            level = AccountLevel(level_str.lower())
        except ValueError:
            level = AccountLevel.FREE
        return cls(
            secret=data.get("secret", ""),
            level=level
        )


class PermissionChecker:
    """权限检查器"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化权限检查器

        Args:
            config_path: 配置文件路径，默认为 ./clients.yaml（当前工作目录）
        """
        if config_path is None:
            config_path = os.path.join(os.getcwd(), "clients.yaml")
        self.config_path = config_path
        self._clients: Dict[str, ClientConfig] = {}
        self._use_default_client = False  # 标记是否使用默认客户端
        # 配置文件热更新相关属性
        self._last_mtime: float = 0  # 文件最后修改时间
        self._last_check_time: float = 0  # 上次检查时间
        self._check_interval: int = 300  # 检查间隔 5 分钟
        self._load_config()

    def _load_config(self) -> None:
        """加载配置文件"""
        config_file = Path(self.config_path)

        if not config_file.exists():
            # 配置文件不存在，使用默认客户端
            self._create_default_client()
            return

        # 记录文件修改时间
        self._last_mtime = config_file.stat().st_mtime

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if data and "clients" in data:
                for client_id, client_data in data["clients"].items():
                    if isinstance(client_data, dict):
                        self._clients[client_id] = ClientConfig.from_dict(client_data)

            # 如果配置为空，使用默认客户端
            if not self._clients:
                self._create_default_client()
        except Exception as e:
            # 配置加载失败，使用默认客户端
            import logging
            logging.warning(f"加载客户端配置失败: {e}，使用默认客户端")
            self._create_default_client()

    def _create_default_client(self) -> None:
        """创建默认客户端配置"""
        self._use_default_client = True
        self._clients[DEFAULT_CLIENT_ID] = ClientConfig(
            secret=DEFAULT_CLIENT_SECRET,
            level=AccountLevel.STANDARD
        )
        import logging
        logging.info(f"使用默认客户端配置: {DEFAULT_CLIENT_ID} (level=standard)")

    def check_and_reload_if_changed(self) -> bool:
        """
        检查配置文件是否变更，如果变更则重新加载

        每 5 分钟检查一次文件修改时间，如果检测到变更则重新加载配置。

        Returns:
            bool: 是否重新加载了配置
        """
        import time
        current_time = time.time()

        # 检查间隔未到，跳过
        if current_time - self._last_check_time < self._check_interval:
            return False

        self._last_check_time = current_time

        config_file = Path(self.config_path)
        if not config_file.exists():
            return False

        try:
            current_mtime = config_file.stat().st_mtime
            if current_mtime != self._last_mtime:
                import logging
                logging.info(f"检测到配置文件变更，重新加载: {self.config_path}")
                # 重置状态
                self._clients = {}
                self._use_default_client = False
                # 重新加载
                self._load_config()
                return True
        except Exception as e:
            import logging
            logging.warning(f"检查配置文件变更失败: {e}")

        return False

    def get_client_config(self, client_id: str) -> Optional[ClientConfig]:
        """
        获取客户端配置

        优先级：
        1. 配置文件中的配置
        2. 环境变量中的配置

        Args:
            client_id: 客户端 ID

        Returns:
            客户端配置，如果未找到返回 None
        """
        # 优先使用配置文件
        if client_id in self._clients:
            return self._clients[client_id]

        # 尝试从环境变量获取
        secret = os.environ.get(f"XTQUANT_CLIENT_{client_id}")
        if secret:
            return ClientConfig(secret=secret, level=AccountLevel.FREE)

        return None

    def verify_secret(self, client_id: str, client_secret: str) -> tuple[bool, Optional[AccountLevel]]:
        """
        验证客户端密钥

        Args:
            client_id: 客户端 ID
            client_secret: 客户端密钥

        Returns:
            (验证结果, 账号等级)
        """
        config = self.get_client_config(client_id)

        if config is None:
            # 未在配置中找到
            if self._use_default_client:
                # 使用默认客户端模式，拒绝未知客户端
                return False, None
            # 非默认模式，尝试使用环境变量中的默认密钥
            default_secret = os.environ.get("XTQUANT_CLIENT_SECRET", "default-secret")
            if client_secret == default_secret:
                return True, AccountLevel.FREE
            return False, None

        if config.secret == client_secret:
            return True, config.level

        return False, None

    def has_permission(self, level: AccountLevel, permission: Permission) -> bool:
        """
        检查账号等级是否有指定权限

        Args:
            level: 账号等级
            permission: 需要的权限

        Returns:
            是否有权限
        """
        return permission in LEVEL_PERMISSIONS.get(level, set())

    def check_api_permission(
        self,
        level: AccountLevel,
        method: str,
        args: tuple = (),
        kwargs: dict = None
    ) -> Optional[PermissionError]:
        """
        检查 API 调用权限

        Args:
            level: 账号等级
            method: API 方法名（可以是 "module.method" 或 "method"）
            args: 位置参数
            kwargs: 关键字参数

        Returns:
            如果权限不足返回 PermissionError，否则返回 None
        """
        if kwargs is None:
            kwargs = {}

        # 获取需要的权限
        required_permission = self._get_required_permission(method, args, kwargs)

        if required_permission is None:
            # 未配置权限的方法
            # STANDARD 及以上级别允许，FREE/PLUS 级别拒绝
            if level in (AccountLevel.FREE, AccountLevel.PLUS):
                return PermissionError(Permission.BASIC, method, level)
            return None

        # 检查权限
        if not self.has_permission(level, required_permission):
            return PermissionError(required_permission, method, level)

        return None

    def _get_required_permission(
        self,
        method: str,
        args: tuple,
        kwargs: dict
    ) -> Optional[Permission]:
        """
        获取 API 调用需要的权限

        对于 get_market_data 和 get_market_data_ex，
        根据 period 参数动态判断权限
        """
        # 直接查找
        if method in API_PERMISSIONS:
            permission = API_PERMISSIONS[method]

            # 特殊处理：日线/分钟线/tick 数据根据 period 判断
            if method in ("xtdata.get_market_data", "xtdata.get_market_data_ex",
                         "xtdata.get_full_kline",
                         "xtdata.download_history_data", "xtdata.download_history_data2",
                         "download_history_data2"):
                period = self._extract_period(args, kwargs)
                if period in MINUTE_PERIODS:
                    return Permission.MINUTE
                elif period in TICK_PERIODS:
                    return Permission.TICK
                elif period in DAILY_PERIODS:
                    return Permission.DAILY
                # 其他周期默认为日线权限

            return permission

        return None

    def _extract_period(self, args: tuple, kwargs: dict) -> str:
        """
        从参数中提取 period 值

        Args:
            args: 位置参数
            kwargs: 关键字参数

        Returns:
            period 值，默认 "1d"
        """
        # 优先从 kwargs 获取
        if "period" in kwargs:
            return kwargs["period"]

        # 常见 API 的 period 参数位置：
        # get_market_data(stock_list, period='1d', ...)
        # download_history_data(stock_code, period='1d', ...)
        # download_history_data2(stock_list, period='1d', ...)

        # 对于大多数 API，period 是第二个位置参数（索引 1）
        if len(args) >= 2 and isinstance(args[1], str):
            return args[1]

        # download_history_data 的 period 是第一个位置参数（索引 0）之后的
        if len(args) >= 2 and isinstance(args[0], str) and isinstance(args[1], str):
            return args[1]

        return "1d"


# 全局权限检查器实例
_permission_checker: Optional[PermissionChecker] = None


def get_permission_checker(config_path: Optional[str] = None) -> PermissionChecker:
    """获取全局权限检查器实例"""
    global _permission_checker
    if _permission_checker is None or config_path is not None:
        _permission_checker = PermissionChecker(config_path)
    return _permission_checker


def reset_permission_checker():
    """重置权限检查器（主要用于测试）"""
    global _permission_checker
    _permission_checker = None