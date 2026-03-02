"""
XtQuant RPyC Client - Transparent remote proxy for xtquant
"""

import os
import rpyc
import time
import threading
import ssl
import logging
from typing import Any, Callable, Dict, List
from datetime import datetime


# ==================== 日志配置 ====================

def setup_logging(log_level: str = "INFO", quiet: bool = False):
    """配置客户端日志

    Args:
        log_level: 日志级别
        quiet: 是否静默模式（不输出控制台日志）
    """
    log_dir = os.path.expanduser("~/.xtquant/logs")
    os.makedirs(log_dir, exist_ok=True)

    formatter = logging.Formatter(
        fmt='%(asctime)s.%(msecs)03d | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    root_logger = logging.getLogger('xtquant_client')
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # 静默模式下不添加控制台 handler
    if not quiet:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        root_logger.addHandler(console_handler)

    file_handler = logging.FileHandler(
        os.path.join(log_dir, f"client_{datetime.now().strftime('%Y%m%d')}.log"),
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)

    return root_logger


_logger = None
_quiet_mode = False


def set_quiet_mode(quiet: bool = True):
    """设置静默模式"""
    global _quiet_mode
    _quiet_mode = quiet


def get_logger():
    global _logger
    if _logger is None:
        _logger = setup_logging(quiet=_quiet_mode)
    return _logger


# ==================== 异常定义 ====================

class ConnectionError(Exception):
    """连接错误"""
    pass


class AuthenticationError(Exception):
    """认证错误"""
    pass


class CallbackError(Exception):
    """回调错误"""
    pass


# ==================== 重连策略 ====================

class ReconnectPolicy:
    """重连策略"""
    
    def __init__(self, max_retries=5, base_delay=1, max_delay=30, backoff_factor=2):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
    
    def get_delay(self, retry_count):
        delay = self.base_delay * (self.backoff_factor ** retry_count)
        return min(delay, self.max_delay)


# ==================== 后台服务线程 ====================

from rpyc.utils.helpers import BgServingThread


# ==================== 远程模块代理 ====================

class RemoteModule:
    """远程模块代理 - 完全透明的动态代理"""
    
    def __init__(self, client, module_name):
        self._client = client
        self._module_name = module_name
        self._module = None
        self._logger = get_logger()
    
    def _ensure_module(self):
        if self._module is None:
            self._client._ensure_connected()
            try:
                method = getattr(self._client._conn.root, f'get_{self._module_name}')
                self._module = method()
            except Exception as e:
                self._module = None
                raise
        return self._module
    
    def __getattr__(self, name):
        module = self._ensure_module()
        try:
            attr = getattr(module, name)
            if callable(attr):
                return self._wrap_call(attr, name)
            return attr
        except Exception as e:
            if self._client._should_reconnect(e):
                self._module = None
                module = self._ensure_module()
                attr = getattr(module, name)
                if callable(attr):
                    return self._wrap_call(attr, name)
                return attr
            raise
    
    def _wrap_call(self, func, func_name: str):
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            args_str = self._summarize_args(args, kwargs)
            self._logger.debug(f"[CALL] {self._module_name}.{func_name}({args_str})")

            try:
                result = func(*args, **kwargs)
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                result_summary = self._summarize_result(result)
                self._logger.info(f"[OK] {self._module_name}.{func_name} | {elapsed_ms:.2f}ms | {result_summary}")
                return result
            except Exception as e:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                self._logger.error(f"[ERROR] {self._module_name}.{func_name} | {elapsed_ms:.2f}ms | {type(e).__name__}: {e}")
                raise

        # 手动设置属性，避免 Python 3.13 functools.wraps 的 __annotations__ 兼容性问题
        wrapper.__name__ = func_name
        wrapper.__qualname__ = f"{self._module_name}.{func_name}"
        return wrapper
    
    def _summarize_args(self, args, kwargs, max_len: int = 100) -> str:
        parts = []
        if args:
            for arg in args[:3]:
                try:
                    s = str(arg)[:30]
                    parts.append(s)
                except:
                    parts.append("?")
            if len(args) > 3:
                parts.append(f"...+{len(args)-3}")
        if kwargs:
            for k, v in list(kwargs.items())[:2]:
                try:
                    s = f"{k}={str(v)[:20]}"
                    parts.append(s)
                except:
                    parts.append(f"{k}=?")
            if len(kwargs) > 2:
                parts.append(f"...+{len(kwargs)-2}")
        return ", ".join(parts)[:max_len]
    
    def _summarize_result(self, result, max_len: int = 100) -> str:
        try:
            if result is None:
                return "None"
            elif isinstance(result, (int, float, bool)):
                return str(result)
            elif isinstance(result, str):
                return result[:max_len] if len(result) > max_len else result
            elif isinstance(result, (list, tuple)):
                return f"{type(result).__name__}[len={len(result)}]"
            elif isinstance(result, dict):
                return f"dict[{len(result)} keys]"
            else:
                return f"<{type(result).__name__}>"
        except:
            return "?"
    
    def __dir__(self):
        module = self._ensure_module()
        return dir(module)


# ==================== 主客户端类 ====================

class XtQuantRemote:
    """
    远程 xtquant 完全透明代理
    
    功能：
    - 自动认证
    - 断线自动重连
    - SSL 加密（可选）
    - 异步回调支持
    - API调用日志
    
    使用示例:
        xt = XtQuantRemote("192.168.1.100")
        stocks = xt.xtdata.get_stock_list_in_sector("沪深A股")
        xt.close()
        
        with XtQuantRemote("192.168.1.100") as xt:
            df = xt.xtdata.get_market_data(["000001.SZ"])
    """
    
    def __init__(
        self,
        host=None,
        port=None,
        client_id=None,
        client_secret=None,
        use_ssl=False,
        ssl_verify=True,
        auto_reconnect=True,
        max_retries=5,
        heartbeat_interval=30,
        log_level="INFO",
    ):
        # 支持环境变量：显式参数 > 环境变量 > 默认值
        if host is None:
            host = os.environ.get("XTQUANT_REMOTE_HOST", "localhost")
        if port is None:
            port = int(os.environ.get("XTQUANT_REMOTE_PORT", "18812"))
        if client_id is None:
            client_id = os.environ.get("XTQUANT_CLIENT_ID", "default")
        if client_secret is None:
            client_secret = os.environ.get("XTQUANT_CLIENT_SECRET", "default-secret")

        self._host = host
        self._port = port
        self._client_id = client_id
        self._client_secret = client_secret
        self._use_ssl = use_ssl
        self._ssl_verify = ssl_verify
        self._auto_reconnect = auto_reconnect
        self._reconnect_policy = ReconnectPolicy(max_retries=max_retries)
        self._heartbeat_interval = heartbeat_interval
        self._log_level = log_level

        self._conn = None
        self._authenticated = False
        self._connected = False
        self._reconnecting = False
        self._heartbeat_thread = None
        self._stop_heartbeat = threading.Event()
        self._bg_thread = None  # BgServingThread for async callbacks

        self._xtdata = RemoteModule(self, 'xtdata')
        self._xttrader = RemoteModule(self, 'xttrader')
        self._xttype = RemoteModule(self, 'xttype')
        self._logger = get_logger()

        self._connect()
    
    def _should_reconnect(self, error):
        if not self._auto_reconnect:
            return False
        error_str = str(error).lower()
        hints = ['connection', 'closed', 'reset', 'broken', 'timeout', 'refused', 'eof', 'socket']
        return any(h in error_str for h in hints)
    
    def _create_ssl_context(self):
        if not self._use_ssl:
            return None
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        if self._ssl_verify:
            ctx.verify_mode = ssl.CERT_REQUIRED
            ctx.check_hostname = True
        else:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        return ctx
    
    def _connect(self):
        config = {
            'allow_public_attrs': True,
            'allow_pickle': True,
            'allow_getattr': True,
            'allow_setattr': True,
            'allow_delattr': True,
            'allow_all_attrs': True,
            'sync_request_timeout': 300,
        }
        
        ssl_context = self._create_ssl_context()
        
        try:
            # 尝试新版本 rpyc API
            try:
                self._conn = rpyc.connect(self._host, self._port, config=config, ssl_context=ssl_context)
            except TypeError:
                # 旧版本 rpyc 不支持 ssl_context 参数
                if ssl_context and self._use_ssl:
                    # 使用 SSL 包装 socket
                    import socket
                    sock = socket.create_connection((self._host, self._port))
                    sock = ssl_context.wrap_socket(sock, server_hostname=self._host)
                    self._conn = rpyc.connect_stream(sock, config=config)
                else:
                    self._conn = rpyc.connect(self._host, self._port, config=config)
            
            self._connected = True

            # 启动后台服务线程处理异步回调
            self._bg_thread = BgServingThread(self._conn)
            self._logger.debug("后台服务线程已启动")

            if self._client_secret:
                self._conn.root.authenticate(self._client_id, self._client_secret)
                self._logger.info(f"认证成功: client_id={self._client_id}")

            if self._heartbeat_interval > 0:
                self._start_heartbeat()
            
            self._logger.info(f"连接成功: {self._host}:{self._port}")
        except Exception as e:
            self._connected = False
            raise ConnectionError(f"连接失败: {e}")
    
    def _ensure_connected(self):
        if self._connected and self._conn:
            return
        if not self._auto_reconnect:
            raise ConnectionError("连接已断开，自动重连已禁用")
        self._reconnect()
    
    def _reconnect(self):
        if self._reconnecting:
            for _ in range(10):
                time.sleep(0.5)
                if self._connected:
                    return
            raise ConnectionError("重连超时")
        
        self._reconnecting = True
        retry_count = 0
        
        try:
            while retry_count < self._reconnect_policy.max_retries:
                try:
                    self._logger.info(f"重连中... 第 {retry_count + 1} 次尝试")
                    
                    if self._conn:
                        try:
                            self._conn.close()
                        except:
                            pass
                    
                    self._conn = None
                    self._connected = False
                    self._token = None
                    self._connect()
                    
                    for sub in self._subscriptions:
                        if sub._active:
                            try:
                                sub.start()
                            except:
                                pass
                    
                    self._logger.info("重连成功")
                    return
                except Exception as e:
                    retry_count += 1
                    delay = self._reconnect_policy.get_delay(retry_count - 1)
                    self._logger.warning(f"重连失败: {e}，{delay}秒后重试...")
                    time.sleep(delay)
            
            raise ConnectionError(f"重连失败，已尝试 {retry_count} 次")
        finally:
            self._reconnecting = False
    
    def _start_heartbeat(self):
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            return
        self._stop_heartbeat.clear()
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()
    
    def _heartbeat_loop(self):
        while not self._stop_heartbeat.is_set():
            try:
                if self._connected and self._conn:
                    try:
                        self._conn.root.heartbeat()
                    except Exception as e:
                        if self._auto_reconnect:
                            self._logger.warning(f"心跳失败: {e}，尝试重连...")
                            try:
                                self._reconnect()
                            except:
                                pass
            except Exception:
                pass
            self._stop_heartbeat.wait(self._heartbeat_interval)

    def _stop_heartbeat_thread(self):
        self._stop_heartbeat.set()
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=2)

    # ==================== 公共接口 ====================

    @property
    def xtdata(self):
        return self._xtdata

    @property
    def xttrader(self):
        return self._xttrader

    @property
    def xttype(self):
        return self._xttype

    def create_trader(self):
        self._ensure_connected()
        return self._conn.root.create_trader()

    def get_all_stocks(self):
        self._ensure_connected()
        return self._conn.root.get_all_stocks()
    
    def get_index_list(self):
        self._ensure_connected()
        return self._conn.root.get_index_list()

    def download_history_data2(self, stock_list: list, period: str = "1d",
                                start_time: str = "", end_time: str = "", incrementally: bool = None):
        """
        下载历史数据（服务端封装版本，返回完整状态）

        返回: {'finished': n, 'total': n, 'done': bool, 'message': str, 'result': {}}
        """
        self._ensure_connected()
        return self._conn.root.download_history_data2(stock_list, period, start_time, end_time, incrementally)

    def is_connected(self):
        return self._connected

    def get_service_status(self):
        self._ensure_connected()
        return self._conn.root.get_service_status()
    
    def reconnect(self):
        self._reconnect()
    
    def close(self):
        self._stop_heartbeat_thread()
        if self._bg_thread:
            self._bg_thread.stop()
            self._bg_thread = None
        self._connected = False
        if self._conn:
            try:
                self._conn.close()
            except:
                pass
        self._conn = None
        self._logger.info("连接已关闭")
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
    
    def __repr__(self):
        status = "已连接" if self._connected else "已断开"
        ssl_status = "SSL" if self._use_ssl else "明文"
        return f"<XtQuantRemote {self._host}:{self._port} [{status}] [{ssl_status}]>"


# ==================== 全局便捷函数 ====================

_global_client = None

def connect(host=None, port=None, **kwargs):
    """创建全局连接

    支持环境变量配置：
    - XTQUANT_REMOTE_HOST: 服务端地址
    - XTQUANT_REMOTE_PORT: 服务端端口
    - XTQUANT_CLIENT_ID: 客户端标识
    - XTQUANT_CLIENT_SECRET: 客户端密钥

    优先级：显式参数 > 环境变量 > 默认值
    """
    global _global_client
    if host is None:
        host = os.environ.get("XTQUANT_REMOTE_HOST", "localhost")
    if port is None:
        port = int(os.environ.get("XTQUANT_REMOTE_PORT", "18812"))
    _global_client = XtQuantRemote(host, port, **kwargs)
    return _global_client

def disconnect():
    """断开全局连接"""
    global _global_client
    if _global_client:
        _global_client.close()
        _global_client = None

def get_client():
    """获取全局客户端"""
    return _global_client


class _ModuleProxy:
    def __init__(self, name):
        self._name = name
    
    def __getattr__(self, attr):
        if _global_client is None:
            raise RuntimeError("请先调用 connect() 建立连接")
        return getattr(getattr(_global_client, self._name), attr)


xtdata = _ModuleProxy('xtdata')
xttrader = _ModuleProxy('xttrader')
xttype = _ModuleProxy('xttype')