"""
XtQuant Share (xqshare) Integration Tests

These tests require a running server and are marked with @pytest.mark.integration.
Run with: pytest -m integration
"""

import pytest
import time
import sys
sys.path.insert(0, '.')


@pytest.mark.integration
class TestIntegration:
    """集成测试 - 需要运行服务端"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """设置测试环境"""
        self.host = "localhost"
        self.port = 18812
        self.client_secret = "test-secret"

    def test_connection(self):
        """测试基本连接"""
        from xqshare import XtQuantRemote

        with XtQuantRemote(
            host=self.host,
            port=self.port,
            client_secret=self.client_secret,
            auto_reconnect=False
        ) as client:
            assert client.is_connected()

    def test_ping(self):
        """测试心跳"""
        from xqshare import XtQuantRemote

        with XtQuantRemote(
            host=self.host,
            port=self.port,
            client_secret=self.client_secret
        ) as client:
            result = client.xtdata.get_stock_list_in_sector("沪深A股")
            assert result is not None

    def test_service_status(self):
        """测试服务状态"""
        from xqshare import XtQuantRemote

        with XtQuantRemote(
            host=self.host,
            port=self.port,
            client_secret=self.client_secret
        ) as client:
            status = client.get_service_status()
            assert "uptime" in status
            assert "active_tokens" in status


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])