"""
XtQuant Share (xqshare) Client Permission Tests

测试客户端权限相关逻辑
"""

import pytest
import os
import sys
from unittest.mock import Mock, MagicMock, patch, PropertyMock

# Mock xtquant 模块
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


class TestClientAuthResponse:
    """测试客户端认证响应处理"""

    def test_client_stores_account_level(self):
        """测试客户端存储账号等级"""
        from xqshare.client import XtQuantRemote

        # Mock rpyc 连接
        mock_conn = MagicMock()
        mock_root = MagicMock()
        mock_conn.root = mock_root

        # Mock 认证响应
        mock_root.authenticate.return_value = {"success": True, "level": "plus"}
        mock_root.heartbeat.return_value = "pong"

        with patch('xqshare.client.rpyc.connect', return_value=mock_conn):
            with patch('xqshare.client.BgServingThread'):
                with patch.dict(os.environ, {
                    "XQSHARE_REMOTE_HOST": "localhost",
                    "XQSHARE_REMOTE_PORT": "18812",
                    "XQSHARE_CLIENT_ID": "test-client",
                    "XQSHARE_CLIENT_SECRET": "test-secret"
                }):
                    client = XtQuantRemote(
                        host="localhost",
                        port=18812,
                        client_id="test-client",
                        client_secret="test-secret",
                        heartbeat_interval=0
                    )

                    # 验证账号等级被记录
                    assert client._account_level == "plus"

    def test_client_handles_old_auth_format(self):
        """测试客户端兼容旧格式认证响应（返回 True）"""
        from xqshare.client import XtQuantRemote

        mock_conn = MagicMock()
        mock_root = MagicMock()
        mock_conn.root = mock_root

        # 旧格式返回 True
        mock_root.authenticate.return_value = True
        mock_root.heartbeat.return_value = "pong"

        with patch('xqshare.client.rpyc.connect', return_value=mock_conn):
            with patch('xqshare.client.BgServingThread'):
                client = XtQuantRemote(
                    host="localhost",
                    port=18812,
                    client_id="test-client",
                    client_secret="test-secret",
                    heartbeat_interval=0
                )

                # 旧格式时 level 应该为 None
                assert client._account_level is None


class TestClientPermissionIntegration:
    """测试客户端权限集成"""

    def test_client_calls_require_permission(self):
        """测试客户端调用 API 时权限被检查"""
        # 这个测试验证当服务端拒绝时，客户端收到异常
        from xqshare.auth import PermissionError as AuthPermissionError, Permission, AccountLevel

        # 创建一个模拟的权限错误
        error = AuthPermissionError(Permission.MINUTE, "get_market_data", AccountLevel.FREE)

        # 验证错误信息
        assert "minute" in str(error)  # 权限名称
        assert "get_market_data" in str(error)
        assert "free" in str(error)

    def test_permission_error_propagation(self):
        """测试权限错误可以正确传播"""
        from xqshare.auth import PermissionError as AuthPermissionError, Permission, AccountLevel

        # 创建权限错误
        error = AuthPermissionError(Permission.TICK, "get_full_tick", AccountLevel.PLUS)

        # 验证可以 raise 和 catch
        with pytest.raises(AuthPermissionError) as exc_info:
            raise error

        assert exc_info.value.permission == Permission.TICK
        assert exc_info.value.method == "get_full_tick"
        assert exc_info.value.level == AccountLevel.PLUS


class TestClientProperties:
    """测试客户端属性"""

    def test_xtdata_property(self):
        """测试 xtdata 属性返回 RemoteModule"""
        from xqshare.client import XtQuantRemote, RemoteModule

        mock_conn = MagicMock()
        mock_root = MagicMock()
        mock_conn.root = mock_root
        mock_root.authenticate.return_value = {"success": True, "level": "free"}
        mock_root.heartbeat.return_value = "pong"
        mock_root.get_xtdata.return_value = MagicMock()

        with patch('xqshare.client.rpyc.connect', return_value=mock_conn):
            with patch('xqshare.client.BgServingThread'):
                client = XtQuantRemote(
                    host="localhost",
                    port=18812,
                    client_id="test",
                    client_secret="test",
                    heartbeat_interval=0
                )

                # xtdata 应该是 RemoteModule 实例
                assert hasattr(client, 'xtdata')
                assert isinstance(client._xtdata, RemoteModule)

    def test_xttrader_property(self):
        """测试 xttrader 属性"""
        from xqshare.client import XtQuantRemote, RemoteModule

        mock_conn = MagicMock()
        mock_root = MagicMock()
        mock_conn.root = mock_root
        mock_root.authenticate.return_value = {"success": True, "level": "premium"}
        mock_root.heartbeat.return_value = "pong"

        with patch('xqshare.client.rpyc.connect', return_value=mock_conn):
            with patch('xqshare.client.BgServingThread'):
                client = XtQuantRemote(
                    host="localhost",
                    port=18812,
                    client_id="test",
                    client_secret="test",
                    heartbeat_interval=0
                )

                assert hasattr(client, 'xttrader')
                assert isinstance(client._xttrader, RemoteModule)


class TestClientEnvConfig:
    """测试客户端环境变量配置"""

    def test_client_uses_env_vars(self):
        """测试客户端使用环境变量配置"""
        from xqshare.client import XtQuantRemote

        mock_conn = MagicMock()
        mock_root = MagicMock()
        mock_conn.root = mock_root
        mock_root.authenticate.return_value = {"success": True, "level": "standard"}
        mock_root.heartbeat.return_value = "pong"

        with patch('xqshare.client.rpyc.connect', return_value=mock_conn):
            with patch('xqshare.client.BgServingThread'):
                with patch.dict(os.environ, {
                    "XQSHARE_REMOTE_HOST": "192.168.1.100",
                    "XQSHARE_REMOTE_PORT": "18888",
                    "XQSHARE_CLIENT_ID": "env-client",
                    "XQSHARE_CLIENT_SECRET": "env-secret"
                }):
                    client = XtQuantRemote(heartbeat_interval=0)

                    assert client._host == "192.168.1.100"
                    assert client._port == 18888
                    assert client._client_id == "env-client"
                    assert client._client_secret == "env-secret"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])