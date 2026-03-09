"""
XtQuant Share (xqshare) Server Tests
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time
import os

# Import the server module
import sys
sys.path.insert(0, '.')


# Initialize logging before importing server
from xqshare.server import _init_logging
_init_logging("WARNING")  # Quiet logs for tests

from xqshare.server import (
    XtQuantService,
    CallbackManager,
    AuthError,
    _summarize_result,
    create_ssl_context,
)


class TestSummarizeResult:
    """测试返回值摘要函数"""
    
    def test_none(self):
        assert _summarize_result(None) == "None"
    
    def test_int(self):
        assert _summarize_result(42) == "42"
    
    def test_float(self):
        assert _summarize_result(3.14) == "3.14"
    
    def test_bool(self):
        assert _summarize_result(True) == "True"
    
    def test_string_short(self):
        assert _summarize_result("hello") == "hello"
    
    def test_string_long(self):
        long_str = "x" * 300
        result = _summarize_result(long_str)
        assert len(result) <= 203  # max_len + "..."
    
    def test_list(self):
        assert _summarize_result([1, 2, 3]) == "list[len=3]"
    
    def test_dict(self):
        result = _summarize_result({"a": 1, "b": 2})
        assert "dict" in result
        assert "a" in result or "b" in result


class TestCallbackManager:
    """测试回调管理器"""
    
    def test_register(self):
        manager = CallbackManager()
        callback = Mock()
        
        manager.register("test_id", callback, "client1")
        
        assert "test_id" in manager._callbacks
        assert manager._callbacks["test_id"]["client_info"] == "client1"
    
    def test_unregister(self):
        manager = CallbackManager()
        callback = Mock()
        manager.register("test_id", callback, "client1")
        
        manager.unregister("test_id")
        
        assert "test_id" not in manager._callbacks
    
    def test_invoke_success(self):
        manager = CallbackManager()
        callback = Mock(return_value="result")
        manager.register("test_id", callback, "client1")
        
        # invoke returns True on success
        result = manager.invoke("test_id", "arg1", "arg2")
        
        assert result is True
        callback.assert_called_once_with("arg1", "arg2")
    
    def test_invoke_nonexistent(self):
        manager = CallbackManager()
        result = manager.invoke("nonexistent")
        
        assert result is False
    
    def test_invoke_exception(self):
        manager = CallbackManager()
        callback = Mock(side_effect=Exception("test error"))
        manager.register("test_id", callback, "client1")
        
        # Should return False and unregister on exception
        result = manager.invoke("test_id")
        
        assert result is False
        assert "test_id" not in manager._callbacks
    
    def test_list_callbacks(self):
        manager = CallbackManager()
        manager.register("id1", Mock(), "client1")
        manager.register("id2", Mock(), "client2")
        
        callbacks = manager.list_callbacks()
        
        assert len(callbacks) == 2
        assert "id1" in callbacks
        assert "id2" in callbacks
    
    def test_clear_client_callbacks(self):
        manager = CallbackManager()
        manager.register("id1", Mock(), "client1")
        manager.register("id2", Mock(), "client1")
        manager.register("id3", Mock(), "client2")
        
        manager.clear_client_callbacks("client1")
        
        assert "id1" not in manager._callbacks
        assert "id2" not in manager._callbacks
        assert "id3" in manager._callbacks


class TestXtQuantService:
    """测试服务类"""
    
    def test_generate_token(self):
        service = XtQuantService()
        service._conn = Mock()
        service._conn.peer = "192.168.1.100:12345"
        
        token = service._generate_token("test_client")
        
        parts = token.split(":")
        assert len(parts) == 3
        assert parts[0] == "test_client"
    
    def test_verify_token_valid(self):
        service = XtQuantService()
        service._conn = Mock()
        service._conn.peer = "192.168.1.100:12345"
        
        token = service._generate_token("test_client")
        
        assert service._verify_token(token) is True
    
    def test_verify_token_invalid_format(self):
        service = XtQuantService()
        
        assert service._verify_token("invalid") is False
        assert service._verify_token("a:b:c:d") is False
    
    def test_verify_token_expired(self):
        service = XtQuantService()
        
        # Create an expired token (timestamp in the past)
        old_timestamp = str(int(time.time()) - 7200)  # 2 hours ago
        import hmac
        import hashlib
        message = f"test_client:{old_timestamp}".encode()
        signature = hmac.new(service.AUTH_KEY.encode(), message, hashlib.sha256).hexdigest()
        expired_token = f"test_client:{old_timestamp}:{signature}"
        
        assert service._verify_token(expired_token) is False
    
    def test_on_connect(self):
        service = XtQuantService()
        mock_conn = Mock()
        mock_conn.peer = "192.168.1.100:12345"
        
        service.on_connect(mock_conn)
        
        assert service._authenticated is False
        assert service._token is None
    
    def test_on_disconnect(self):
        service = XtQuantService()
        service._conn = Mock()
        service._conn.peer = "192.168.1.100:12345"
        service._client_info = "test_client@192.168.1.100:12345"
        service._token = "test_token"
        service._tokens = {"test_token": {"client_id": "test_client"}}
        
        service.on_disconnect(service._conn)
        
        assert "test_token" not in service._tokens


class TestSSLContext:
    """测试 SSL 上下文创建"""
    
    def test_create_ssl_context_no_files(self):
        ctx = create_ssl_context(None, None)
        assert ctx is None
    
    @patch('xqshare.server.ssl.SSLContext')
    def test_create_ssl_context_with_files(self, mock_ssl_context):
        mock_ctx = Mock()
        mock_ssl_context.return_value = mock_ctx
        
        # This will fail without actual files, but we can test the logic
        # In real tests, we'd need to create temporary cert files
        pass


class TestAuthService:
    """测试认证服务"""
    
    @patch.dict(os.environ, {"XQSHARE_CLIENT_SECRET": "test-secret"})
    def test_authenticate_success(self):
        service = XtQuantService()
        service._conn = Mock()
        service._conn.peer = "192.168.1.100:12345"
        
        token = service.exposed_authenticate("test_client", "test-secret")
        
        assert token is not None
        assert service._authenticated is True
    
    @patch.dict(os.environ, {"XQSHARE_CLIENT_SECRET": "test-secret"})
    def test_authenticate_failure(self):
        service = XtQuantService()
        service._conn = Mock()
        service._conn.peer = "192.168.1.100:12345"
        
        with pytest.raises(AuthError):
            service.exposed_authenticate("test_client", "wrong-secret")
    
    @patch.dict(os.environ, {
        "XQSHARE_CLIENT_app1": "secret-app1",
        "XQSHARE_CLIENT_app2": "secret-app2"
    })
    def test_multi_client_auth(self):
        service = XtQuantService()
        service._conn = Mock()
        service._conn.peer = "192.168.1.100:12345"
        
        # App1 with correct secret
        token1 = service.exposed_authenticate("app1", "secret-app1")
        assert token1 is not None
        
        # App2 with correct secret
        token2 = service.exposed_authenticate("app2", "secret-app2")
        assert token2 is not None
        
        # App1 with wrong secret
        with pytest.raises(AuthError):
            service.exposed_authenticate("app1", "secret-app2")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])