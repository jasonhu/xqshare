"""
XtQuant RPyC Server - Run on Windows to provide xtquant proxy service
"""

import rpyc
from rpyc.utils.server import ThreadedServer
import hashlib
import hmac
import time
import os
import ssl
import logging
import functools
from datetime import datetime
from typing import Any, Dict

# Import xtquant (only available on Windows)
try:
    import xtquant.xtdata as xtdata
    import xtquant.xttrader as xttrader
    import xtquant.xttype as xttype
    from xtquant.xttrader import XtQuantTrader
    XTQUANT_AVAILABLE = True
except ImportError:
    XTQUANT_AVAILABLE = False
    xtdata = None
    xttrader = None
    xttype = None
    XtQuantTrader = None


# ==================== 日志配置 ====================

def setup_logging(log_dir: str = "logs", log_level: str = "INFO"):
    """配置日志系统"""
    os.makedirs(log_dir, exist_ok=True)
    
    formatter = logging.Formatter(
        fmt='%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    file_handler = logging.FileHandler(
        os.path.join(log_dir, f"xtquant_service_{datetime.now().strftime('%Y%m%d')}.log"),
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    
    api_handler = logging.FileHandler(
        os.path.join(log_dir, f"api_calls_{datetime.now().strftime('%Y%m%d')}.log"),
        encoding='utf-8'
    )
    api_handler.setFormatter(formatter)
    api_logger = logging.getLogger('api')
    api_logger.addHandler(api_handler)
    api_logger.setLevel(logging.DEBUG)
    
    return logging.getLogger(__name__)


logger = None
api_logger = None


def _init_logging(log_level="INFO"):
    global logger, api_logger
    logger = setup_logging(log_level=log_level)
    api_logger = logging.getLogger('api')


# ==================== 日志装饰器 ====================

def _log_call(name: str, client_info: str, func, *args, **kwargs):
    """通用的 API 调用日志记录函数"""
    try:
        args_str = str(args)[:200] if args else ""
        kwargs_str = str(kwargs)[:200] if kwargs else ""
    except:
        args_str = "<unserializable>"
        kwargs_str = ""

    api_logger.info(f"[CALL] {name} | client={client_info} | args={args_str} | kwargs={kwargs_str}")

    start_time = time.perf_counter()
    try:
        result = func(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        result_summary = _summarize_result(result)
        api_logger.info(f"[OK] {name} | elapsed={elapsed_ms:.2f}ms | result={result_summary}")
        return result
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        api_logger.error(f"[ERROR] {name} | elapsed={elapsed_ms:.2f}ms | error={type(e).__name__}: {str(e)[:200]}")
        raise


def log_api_call(func_name: str = None):
    """记录 API 调用的装饰器"""
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            name = func_name or func.__name__
            client_info = getattr(self, '_client_info', 'unknown')
            return _log_call(name, client_info, func, self, *args, **kwargs)
        return wrapper
    return decorator


def _summarize_result(result: Any, max_len: int = 200) -> str:
    """生成返回值摘要"""
    try:
        if result is None:
            return "None"
        elif isinstance(result, (int, float, bool, str)):
            s = str(result)
            return s if len(s) <= max_len else s[:max_len] + "..."
        elif isinstance(result, (list, tuple)):
            return f"{type(result).__name__}[len={len(result)}]"
        elif isinstance(result, dict):
            keys = list(result.keys())[:5]
            return f"dict{{{', '.join(map(str, keys))}{'...' if len(result) > 5 else ''}}}"
        elif hasattr(result, '__class__'):
            return f"<{result.__class__.__module__}.{result.__class__.__name__}>"
        else:
            return str(type(result))
    except:
        return "<unserializable>"


# ==================== 回调管理器 ====================

class CallbackManager:
    """管理客户端注册的回调函数"""
    
    def __init__(self):
        self._callbacks: Dict[str, Dict] = {}
    
    def register(self, callback_id: str, callback_ref, client_info: str = "unknown"):
        self._callbacks[callback_id] = {
            'ref': callback_ref,
            'client_info': client_info,
            'registered_at': time.time(),
            'call_count': 0
        }
        logger.info(f"[Callback] 注册回调: {callback_id} | client={client_info}")
    
    def unregister(self, callback_id: str):
        if callback_id in self._callbacks:
            del self._callbacks[callback_id]
        logger.info(f"[Callback] 注销回调: {callback_id}")
    
    def invoke(self, callback_id: str, *args, **kwargs):
        callback_info = self._callbacks.get(callback_id)
        if not callback_info:
            logger.warning(f"[Callback] 回调不存在: {callback_id}")
            return False
        
        callback_ref = callback_info['ref']
        callback_info['call_count'] += 1
        
        try:
            start_time = time.perf_counter()
            callback_ref(*args, **kwargs)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            api_logger.debug(f"[Callback] 调用成功: {callback_id} | elapsed={elapsed_ms:.2f}ms")
            return True
        except Exception as e:
            logger.error(f"[Callback] 调用失败: {callback_id} | error={e}")
            self.unregister(callback_id)
            return False
    
    def list_callbacks(self):
        return {
            cb_id: {
                'client': info['client_info'],
                'registered_at': info['registered_at'],
                'call_count': info['call_count']
            }
            for cb_id, info in self._callbacks.items()
        }
    
    def clear_client_callbacks(self, client_info: str):
        to_remove = [cb_id for cb_id, info in self._callbacks.items() if info['client_info'] == client_info]
        for cb_id in to_remove:
            del self._callbacks[cb_id]
        if to_remove:
            logger.info(f"[Callback] 清理客户端回调: {client_info} | count={len(to_remove)}")


callback_manager = CallbackManager()


# ==================== 异常定义 ====================

class AuthError(Exception):
    """认证错误"""
    pass


# ==================== 模块代理（带日志） ====================

class LoggingProxy:
    """通用代理：拦截模块/对象的方法调用并记录日志，支持递归包装返回对象"""

    def __init__(self, target, target_name: str, client_info_getter):
        object.__setattr__(self, '_target', target)
        object.__setattr__(self, '_target_name', target_name)
        object.__setattr__(self, '_get_client_info', client_info_getter)

    def __getattr__(self, name):
        target = object.__getattribute__(self, '_target')
        target_name = object.__getattribute__(self, '_target_name')
        get_client_info = object.__getattribute__(self, '_get_client_info')

        attr = getattr(target, name)

        # 如果是可调用对象，包装成带日志的版本
        if callable(attr):
            def wrapper(*args, **kwargs):
                full_name = f"{target_name}.{name}"
                result = _log_call(full_name, get_client_info(), attr, *args, **kwargs)
                # 如果返回的是复杂对象，递归包装
                if result is not None and hasattr(result, '__class__'):
                    if not isinstance(result, (int, float, str, bool, list, dict, tuple, type(None), bytes)):
                        if not result.__class__.__module__.startswith('builtins'):
                            return LoggingProxy(result, full_name, get_client_info)
                return result
            wrapper.__name__ = name
            return wrapper

        return attr

    def __setattr__(self, name, value):
        return setattr(object.__getattribute__(self, '_target'), name, value)

    def __dir__(self):
        return dir(object.__getattribute__(self, '_target'))

    def __repr__(self):
        return repr(object.__getattribute__(self, '_target'))

# 兼容别名
LoggingModuleProxy = LoggingProxy


# ==================== 服务类 ====================

class XtQuantService(rpyc.Service):
    """完全透明代理服务"""
    
    AUTH_KEY = os.environ.get("XTQUANT_AUTH_KEY", "your-secret-key-change-me")
    AUTH_TOKEN_EXPIRE = 3600
    
    _xtdata = xtdata
    _xttrader = xttrader
    _xttype = xttype
    _tokens = {}
    
    def on_connect(self, conn):
        self._conn = conn
        self._authenticated = False
        # 兼容不同版本 rpyc：尝试获取客户端地址
        try:
            # 新版本 rpyc
            if hasattr(conn, 'peer'):
                self._client_info = f"{conn.peer}"
            # 旧版本 rpyc：从 channel 获取
            elif hasattr(conn, '_channel') and hasattr(conn._channel, 'stream'):
                stream = conn._channel.stream
                if hasattr(stream, 'sock'):
                    peer = stream.sock.getpeername()
                    self._client_info = f"{peer[0]}:{peer[1]}"
                else:
                    self._client_info = "unknown"
            else:
                self._client_info = "unknown"
        except Exception:
            self._client_info = "unknown"
        self._token = None
        logger.info(f"[连接] 客户端接入: {self._client_info}")
    
    def on_disconnect(self, conn):
        client_info = getattr(self, '_client_info', 'unknown')
        logger.info(f"[断开] 客户端离开: {client_info}")
        if hasattr(self, '_token') and self._token and self._token in self._tokens:
            del self._tokens[self._token]
        callback_manager.clear_client_callbacks(client_info)
    
    def _generate_token(self, client_id):
        timestamp = str(int(time.time()))
        message = f"{client_id}:{timestamp}".encode()
        signature = hmac.new(self.AUTH_KEY.encode(), message, hashlib.sha256).hexdigest()
        return f"{client_id}:{timestamp}:{signature}"
    
    def _verify_token(self, token):
        try:
            parts = token.split(":")
            if len(parts) != 3:
                return False
            client_id, timestamp, signature = parts
            if int(time.time()) - int(timestamp) > self.AUTH_TOKEN_EXPIRE:
                return False
            message = f"{client_id}:{timestamp}".encode()
            expected_sig = hmac.new(self.AUTH_KEY.encode(), message, hashlib.sha256).hexdigest()
            return hmac.compare_digest(signature, expected_sig)
        except Exception:
            return False
    
    # ==================== 认证接口 ====================
    
    @log_api_call("authenticate")
    def exposed_authenticate(self, client_id, client_secret):
        expected_secret = os.environ.get(f"XTQUANT_CLIENT_{client_id}", "")
        if not expected_secret:
            expected_secret = os.environ.get("XTQUANT_CLIENT_SECRET", "default-secret")
        
        if client_secret != expected_secret:
            logger.warning(f"[认证失败] client_id={client_id}")
            raise AuthError("认证失败：无效的客户端凭证")
        
        token = self._generate_token(client_id)
        self._tokens[token] = {"client_id": client_id, "created_at": time.time()}
        self._authenticated = True
        self._token = token
        self._client_info = f"{client_id}@{self._conn.peer}"
        logger.info(f"[认证成功] client_id={client_id}")
        return token
    
    @log_api_call("heartbeat")
    def exposed_heartbeat(self, token=None):
        if token and token in self._tokens:
            self._tokens[token]["last_heartbeat"] = time.time()
        return "pong"
    
    # ==================== 模块代理接口 ====================

    @log_api_call("get_xtdata")
    def exposed_get_xtdata(self, token=None):
        if token and not self._verify_token(token):
            raise AuthError("未授权访问")
        return LoggingModuleProxy(self._xtdata, 'xtdata', lambda: self._client_info)

    @log_api_call("get_xttrader")
    def exposed_get_xttrader(self, token=None):
        if token and not self._verify_token(token):
            raise AuthError("未授权访问")
        return LoggingModuleProxy(self._xttrader, 'xttrader', lambda: self._client_info)

    @log_api_call("get_xttype")
    def exposed_get_xttype(self, token=None):
        if token and not self._verify_token(token):
            raise AuthError("未授权访问")
        return LoggingModuleProxy(self._xttype, 'xttype', lambda: self._client_info)

    @log_api_call("create_trader")
    def exposed_create_trader(self, token=None):
        if token and not self._verify_token(token):
            raise AuthError("未授权访问")
        if not XTQUANT_AVAILABLE:
            raise RuntimeError("xtquant 库未安装")
        return XtQuantTrader()
    
    # ==================== 辅助接口 ====================
    
    @log_api_call("get_all_stocks")
    def exposed_get_all_stocks(self, token=None):
        if token and not self._verify_token(token):
            raise AuthError("未授权访问")
        return self._xtdata.get_stock_list_in_sector("沪深A股")
    
    @log_api_call("get_index_list")
    def exposed_get_index_list(self, token=None):
        if token and not self._verify_token(token):
            raise AuthError("未授权访问")
        return self._xtdata.get_stock_list_in_sector("沪深指数")
    
    # ==================== 回调管理 ====================
    
    @log_api_call("register_callback")
    def exposed_register_callback(self, callback_id: str, callback_ref):
        callback_manager.register(callback_id, callback_ref, self._client_info)
        return True
    
    @log_api_call("unregister_callback")
    def exposed_unregister_callback(self, callback_id: str):
        callback_manager.unregister(callback_id)
        return True
    
    @log_api_call("list_callbacks")
    def exposed_list_callbacks(self, token=None):
        if token and not self._verify_token(token):
            raise AuthError("未授权访问")
        return callback_manager.list_callbacks()
    
    # ==================== 行情订阅 ====================
    
    @log_api_call("subscribe_quote")
    def exposed_subscribe_quote(self, stock_code: str, callback_id: str):
        def on_quote(data):
            callback_manager.invoke(callback_id, stock_code, data)
        return self._xtdata.subscribe_quote(stock_code, callback=on_quote)
    
    @log_api_call("unsubscribe_quote")
    def exposed_unsubscribe_quote(self, stock_code: str):
        return self._xtdata.unsubscribe_quote(stock_code)
    
    # ==================== 批量接口 ====================
    
    @log_api_call("get_market_data_batch")
    def exposed_get_market_data_batch(self, stock_list: list, period: str = "1d",
                                       start_time: str = "", end_time: str = ""):
        return self._xtdata.get_market_data(stock_list, period=period, start_time=start_time, end_time=end_time)
    
    @log_api_call("get_full_tick_batch")
    def exposed_get_full_tick_batch(self, stock_list: list):
        return self._xtdata.get_full_tick(stock_list)
    
    @log_api_call("download_history_data2")
    def exposed_download_history_data2(self, stock_list: list, period: str = "1d",
                                        start_time: str = "", end_time: str = "", incrementally: bool = None):
        """
        下载历史数据（服务端封装，避免回调传输问题）
        返回: {'finished': n, 'total': n, 'result': {...}}
        """
        status = {'finished': 0, 'total': 0, 'done': False, 'result': {}, 'message': ''}

        def on_progress(data):
            status['finished'] = data.get('finished', 0)
            status['total'] = data.get('total', 0)
            status['done'] = status['finished'] >= status['total']
            status['message'] = data.get('message', '')
            if 'result' in data:
                import datetime as dt
                from xtquant import xtbson as bson
                regino_result = bson.BSON.decode(data.get('result'))
                for stock, info in regino_result.items():
                    info['start_time'] = str(dt.datetime.fromtimestamp(info.get('start_time') / 1000))
                    info['end_time'] = str(dt.datetime.fromtimestamp(info.get('end_time') / 1000))
                    status['result'][stock] = info

        # 调用原始方法（incrementally 参数需要转换为 None 或 bool）
        inc = incrementally
        self._xtdata.download_history_data2(
            stock_list, period, start_time, end_time,
            callback=on_progress, incrementally=inc
        )

        return status

    @log_api_call("get_financial_data")
    def exposed_get_financial_data(self, stock_list: list, table_list: list = None,
                                   start_time: str = "", end_time: str = ""):
        return self._xtdata.get_financial_data(stock_list, table_list or [], start_time, end_time)
    
    # ==================== 服务状态 ====================
    
    @log_api_call("get_service_status")
    def exposed_get_service_status(self, token=None):
        if token and not self._verify_token(token):
            raise AuthError("未授权访问")
        return {
            "uptime": time.time() - getattr(self, '_start_time', time.time()),
            "active_tokens": len(self._tokens),
            "active_callbacks": len(callback_manager.list_callbacks()),
            "callbacks": callback_manager.list_callbacks()
        }
    
    @log_api_call("ping")
    def exposed_ping(self):
        return "pong"

    @log_api_call("test_async_callback")
    def exposed_test_async_callback(self, callback_func, delay: float = 2.0, count: int = 5):
        """
        测试 RPyC netref 异步回调机制
        :param callback_func: 客户端传递的回调函数（netref）
        :param delay: 每次回调间隔秒数
        :param count: 回调次数
        :return: 立即返回 "已启动"
        """
        import threading
        import time

        def async_call():
            for i in range(count):
                time.sleep(delay)
                try:
                    result = callback_func(f"异步回调 #{i+1}/{count}，时间: {time.strftime('%H:%M:%S')}")
                    api_logger.info(f"[异步回调] #{i+1} 执行成功，返回: {result}")
                except Exception as e:
                    api_logger.error(f"[异步回调] #{i+1} 执行失败: {e}")

        thread = threading.Thread(target=async_call, daemon=True)
        thread.start()
        return f"已启动异步回调，共 {count} 次，间隔 {delay} 秒"


# ==================== 服务启动 ====================

def create_ssl_context(certfile=None, keyfile=None):
    if not certfile or not keyfile:
        return None
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile, keyfile)
    return ctx


def start_server(host="0.0.0.0", port=18812, use_ssl=False, certfile=None, keyfile=None, log_level="INFO"):
    """启动服务"""
    
    if not XTQUANT_AVAILABLE:
        print("错误: xtquant 库未安装，请先安装 xtquant")
        return
    
    _init_logging(log_level)
    XtQuantService._start_time = time.time()
    
    print("=" * 70)
    print("  XtQuant RPyC 服务")
    print("=" * 70)
    print(f"  监听地址: {host}:{port}")
    print(f"  SSL 加密: {'启用' if use_ssl else '禁用'}")
    print(f"  日志级别: {log_level}")
    print("=" * 70)
    
    logger.info(f"服务启动 | host={host} | port={port} | ssl={use_ssl}")
    
    config = {
        'allow_public_attrs': True,
        'allow_pickle': True,
        'allow_getattr': True,
        'allow_setattr': True,
        'allow_delattr': True,
        'allow_all_attrs': True,
        'sync_request_timeout': 300,
    }
    
    ssl_context = None
    if use_ssl:
        ssl_context = create_ssl_context(certfile, keyfile)
        if ssl_context:
            logger.info("SSL 证书加载成功")
            print("  ✓ SSL 证书加载成功")
        else:
            logger.warning("SSL 证书加载失败")
            print("  ⚠ SSL 证书加载失败")
    
    # 构建 ThreadedServer 参数（兼容不同 rpyc 版本）
    server_kwargs = {
        'hostname': host,
        'port': port,
        'protocol_config': config,
    }
    
    # 尝试使用 ssl_context（新版本 rpyc）
    try:
        server = ThreadedServer(XtQuantService, ssl_context=ssl_context, **server_kwargs)
    except TypeError:
        # 旧版本 rpyc 不支持 ssl_context，使用其他方式
        if ssl_context:
            # 对于旧版本，通过 protocol_config 传递 SSL
            import socket
            import ssl as ssl_module
            
            # 创建 SSL 包装的 socket
            class SSLThreadedServer(ThreadedServer):
                def _accept_method(self, sock):
                    try:
                        return ssl_context.wrap_socket(sock, server_side=True)
                    except Exception as e:
                        logger.error(f"SSL 包装失败: {e}")
                        raise
            
            server = SSLThreadedServer(XtQuantService, **server_kwargs)
            logger.info("使用兼容模式启动 SSL")
        else:
            server = ThreadedServer(XtQuantService, **server_kwargs)
    
    print("\n  服务已启动，等待客户端连接...")
    print("  按 Ctrl+C 停止服务\n")
    
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("服务停止（用户中断）")
        print("\n  服务已停止")
        server.close()
    except Exception as e:
        logger.error(f"服务异常: {e}")
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="XtQuant RPyC 服务")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    parser.add_argument("--port", type=int, default=18812, help="监听端口")
    parser.add_argument("--ssl", action="store_true", help="启用 SSL 加密")
    parser.add_argument("--cert", help="SSL 证书文件")
    parser.add_argument("--key", help="SSL 私钥文件")
    parser.add_argument("--log-level", default="INFO", help="日志级别")
    
    args = parser.parse_args()
    
    start_server(
        host=args.host,
        port=args.port,
        use_ssl=args.ssl,
        certfile=args.cert,
        keyfile=args.key,
        log_level=args.log_level
    )