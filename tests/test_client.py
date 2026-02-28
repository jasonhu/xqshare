"""
XtQuant RPyC Client Tests
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import threading
import time

# Import the client module
import sys
sys.path.insert(0, '.')
from xtquant_rpyc.client import (
    XtQuantRemote,
    ConnectionError,
    AuthenticationError,
    CallbackError,
    ReconnectPolicy,
    CallbackServer,
    RemoteModule,
)


class TestReconnectPolicy:
    """测试重连策略"""
    
    def test_base_delay(self):
        policy = ReconnectPolicy(max_retries=5, base_delay=1, backoff_factor=2)
        assert policy.get_delay(0) == 1
    
    def test_exponential_backoff(self):
        policy = ReconnectPolicy(max_retries=5, base_delay=1, backoff_factor=2)
        assert policy.get_delay(0) == 1
        assert policy.get_delay(1) == 2
        assert policy.get_delay(2) == 4
        assert policy.get_delay(3) == 8
    
    def test_max_delay(self):
        policy = ReconnectPolicy(max_retries=5, base_delay=1, max_delay=10, backoff_factor=2)
        assert policy.get_delay(10) == 10  # cap at max_delay


class TestCallbackServer:
    """测试回调服务器"""
    
    def test_register_callback(self):
        server = CallbackServer(port=0)
        callback = Mock()
        server.register("test_id", callback)
        assert "test_id" in server._callbacks
    
    def test_unregister_callback(self):
        server = CallbackServer(port=0)
        callback = Mock()
        server.register("test_id", callback)
        server.unregister("test_id")
        assert "test_id" not in server._callbacks
    
    def test_invoke_callback(self):
        server = CallbackServer(port=0)
        callback = Mock(return_value="result")
        server.register("test_id", callback)
        
        result = server._invoke_callback("test_id", "arg1", "arg2")
        callback.assert_called_once_with("arg1", "arg2")
        assert result == "result"
    
    def test_invoke_nonexistent_callback(self):
        server = CallbackServer(port=0)
        with pytest.raises(CallbackError):
            server._invoke_callback("nonexistent")


class TestRemoteModule:
    """测试远程模块代理"""
    
    def test_attribute_access(self):
        mock_client = Mock()
        mock_client._ensure_connected = Mock()
        mock_client._should_reconnect = Mock(return_value=False)
        mock_client._conn = Mock()
        mock_client._token = "test_token"
        
        # Mock the remote module
        mock_module = Mock()
        mock_module.test_func = Mock(return_value="test_result")
        mock_client._conn.root.get_xtdata = Mock(return_value=mock_module)
        
        remote = RemoteModule(mock_client, 'xtdata')
        result = remote.test_func()
        
        assert result == "test_result"
    
    def test_reconnect_on_error(self):
        mock_client = Mock()
        mock_client._ensure_connected = Mock()
        mock_client._should_reconnect = Mock(return_value=True)
        mock_client._conn = Mock()
        mock_client._token = "test_token"
        
        # First call fails, second succeeds
        mock_module = Mock()
        call_count = [0]
        
        def test_func():
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Connection reset")
            return "success"
        
        mock_module.test_func = test_func
        mock_client._conn.root.get_xtdata = Mock(return_value=mock_module)
        
        remote = RemoteModule(mock_client, 'xtdata')
        
        # Should trigger reconnect on first failure
        with pytest.raises(Exception):
            remote.test_func()


class TestXtQuantRemote:
    """测试主客户端类"""
    
    @patch('xtquant_rpyc.client.rpyc.connect')
    def test_connect_without_auth(self, mock_connect):
        mock_conn = Mock()
        mock_conn.root.ping = Mock(return_value="pong")
        mock_connect.return_value = mock_conn
        
        client = XtQuantRemote(host="localhost", port=18812, client_secret="", auto_reconnect=False)
        
        mock_connect.assert_called_once()
        assert client._connected is True
    
    @patch('xtquant_rpyc.client.rpyc.connect')
    def test_connect_with_auth(self, mock_connect):
        mock_conn = Mock()
        mock_conn.root.ping = Mock(return_value="pong")
        mock_conn.root.authenticate = Mock(return_value="test_token")
        mock_connect.return_value = mock_conn
        
        client = XtQuantRemote(
            host="localhost", 
            port=18812, 
            client_secret="my-secret",
            auto_reconnect=False
        )
        
        mock_conn.root.authenticate.assert_called_once()
        assert client._token == "test_token"
    
    @patch('xtquant_rpyc.client.rpyc.connect')
    def test_context_manager(self, mock_connect):
        mock_conn = Mock()
        mock_conn.root.ping = Mock(return_value="pong")
        mock_connect.return_value = mock_conn
        
        with XtQuantRemote(host="localhost", auto_reconnect=False) as client:
            assert client._connected is True
        
        assert client._connected is False
    
    @patch('xtquant_rpyc.client.rpyc.connect')
    def test_should_reconnect(self, mock_connect):
        mock_conn = Mock()
        mock_conn.root.ping = Mock(return_value="pong")
        mock_connect.return_value = mock_conn
        
        client = XtQuantRemote(host="localhost", auto_reconnect=True)
        
        # Connection errors should trigger reconnect
        assert client._should_reconnect(Exception("Connection reset")) is True
        assert client._should_reconnect(Exception("Socket closed")) is True
        assert client._should_reconnect(Exception("Timeout")) is True
        
        # Other errors should not
        assert client._should_reconnect(Exception("ValueError")) is False
        
        client.close()
    
    @patch('xtquant_rpyc.client.rpyc.connect')
    def test_is_connected(self, mock_connect):
        mock_conn = Mock()
        mock_conn.root.ping = Mock(return_value="pong")
        mock_connect.return_value = mock_conn
        
        client = XtQuantRemote(host="localhost", auto_reconnect=False)
        assert client.is_connected() is True
        
        client.close()
        assert client.is_connected() is False


class TestGlobalFunctions:
    """测试全局便捷函数"""
    
    @patch('xtquant_rpyc.client.rpyc.connect')
    def test_connect_disconnect(self, mock_connect):
        mock_conn = Mock()
        mock_conn.root.ping = Mock(return_value="pong")
        mock_connect.return_value = mock_conn
        
        from xtquant_rpyc.client import connect, disconnect, get_client
        
        client = connect(host="localhost", auto_reconnect=False)
        assert client is not None
        
        retrieved = get_client()
        assert retrieved is client
        
        disconnect()
        assert get_client() is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])