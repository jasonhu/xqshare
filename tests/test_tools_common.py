"""
测试 xqshare.tools.common 模块的输出格式化功能
"""

import json
import pytest
import pandas as pd
from datetime import datetime
from io import StringIO
from unittest.mock import patch

from xqshare.tools.common import (
    _format_as_json,
    _format_as_text,
    _format_as_csv,
    format_output,
    _format_object_attrs,
    _is_remote_object,
)


class TestIsRemoteObject:
    """测试 _is_remote_object 函数"""

    def test_local_dataframe(self):
        """本地 DataFrame 应返回 False"""
        df = pd.DataFrame({"col1": [1, 2]})
        assert _is_remote_object(df) is False

    def test_local_object(self):
        """普通 Python 对象应返回 False"""
        class TestObj:
            pass
        obj = TestObj()
        assert _is_remote_object(obj) is False

    def test_primitive_types(self):
        """基本类型应返回 False"""
        assert _is_remote_object("string") is False
        assert _is_remote_object(123) is False
        assert _is_remote_object([1, 2, 3]) is False
        assert _is_remote_object({"key": "value"}) is False

    def test_mock_rpyc_object(self):
        """模拟 RPyC 远程对象应返回 True"""
        # 创建一个模拟的远程对象
        class MockNetref:
            pass

        # 模拟 RPyC netref 的模块名
        MockNetref.__module__ = 'rpyc.core.netref'
        mock_obj = MockNetref()
        assert _is_remote_object(mock_obj) is True

    def test_mock_netref_object(self):
        """模块名仅包含 netref 的对象应返回 True"""
        class MockNetref:
            pass

        MockNetref.__module__ = 'some.netref.module'
        mock_obj = MockNetref()
        assert _is_remote_object(mock_obj) is True


class TestFormatAsJson:
    """测试 _format_as_json 函数"""

    def test_none(self):
        """None 应返回 None"""
        assert _format_as_json(None) is None

    def test_primitive_types(self):
        """基本类型应原样返回"""
        assert _format_as_json("hello") == "hello"
        assert _format_as_json(123) == 123
        assert _format_as_json(3.14) == 3.14
        assert _format_as_json(True) is True
        assert _format_as_json(False) is False

    def test_list_and_tuple(self):
        """列表和元组应转换为数组，递归处理元素"""
        result = _format_as_json([1, "a", None])
        assert result == [1, "a", None]

        result = _format_as_json((1, 2, 3))
        assert result == [1, 2, 3]  # 元组转为列表

    def test_dict(self):
        """字典应递归处理值"""
        result = _format_as_json({"a": 1, "b": [2, 3]})
        assert result == {"a": 1, "b": [2, 3]}

    def test_dataframe(self):
        """DataFrame 应转换为 records 格式"""
        df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
        result = _format_as_json(df)
        assert result == [
            {"col1": 1, "col2": "a"},
            {"col1": 2, "col2": "b"},
        ]

    def test_datetime(self):
        """datetime 应转换为 ISO 格式字符串"""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = _format_as_json(dt)
        assert result == "2024-01-15T10:30:00"

    def test_object(self):
        """普通对象应转换为属性字典"""
        class TestObj:
            def __init__(self):
                self.name = "test"
                self.value = 42

        obj = TestObj()
        result = _format_as_json(obj)
        assert "name" in result
        assert result["name"] == "test"
        assert "value" in result
        assert result["value"] == 42

    def test_nested_structure(self):
        """嵌套结构应递归处理"""
        df = pd.DataFrame({"x": [1]})
        data = {
            "items": [1, 2, 3],
            "df": df,
            "nested": {"a": datetime(2024, 1, 1)},
        }
        result = _format_as_json(data)
        assert result["items"] == [1, 2, 3]
        assert result["df"] == [{"x": 1}]
        assert result["nested"]["a"] == "2024-01-01T00:00:00"


class TestFormatAsText:
    """测试 _format_as_text 函数"""

    def test_none(self):
        """None 应输出 'None'"""
        result = _format_as_text(None)
        assert result == "None"

    def test_dataframe(self):
        """DataFrame 应格式化为表格字符串"""
        df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
        result = _format_as_text(df)
        assert "col1" in result
        assert "col2" in result
        assert "1" in result
        assert "2" in result

    def test_dict_with_dataframe(self):
        """带 DataFrame 的字典应分块格式化"""
        df = pd.DataFrame({"x": [1, 2]})
        data = {"table": df, "count": 2}
        result = _format_as_text(data)
        assert "=== table ===" in result
        assert "=== count ===" in result

    def test_plain_dict(self):
        """普通字典应使用 pformat 格式化"""
        data = {"a": 1, "b": [2, 3]}
        result = _format_as_text(data)
        assert "'a': 1" in result or "'a':1" in result

    def test_list_no_limit(self):
        """列表无限制时应输出全部元素"""
        items = ["a", "b", "c"]
        result = _format_as_text(items, limit=None)
        assert "[1] a" in result
        assert "[2] b" in result
        assert "[3] c" in result

    def test_list_with_limit(self):
        """列表限制时应截断并显示统计"""
        items = ["a", "b", "c", "d", "e"]
        result = _format_as_text(items, limit=3)
        assert "[1] a" in result
        assert "[2] b" in result
        assert "[3] c" in result
        assert "[4] d" not in result
        assert "共 5 条" in result
        assert "已显示前 3 条" in result

    def test_list_with_objects(self):
        """包含对象的列表应格式化对象属性"""
        class Item:
            def __init__(self, name):
                self.name = name

        items = [Item("first"), Item("second")]
        result = _format_as_text(items)
        assert "[1]" in result
        assert "[2]" in result
        # 对象属性应被格式化
        assert "name" in result

    def test_primitive(self):
        """基本类型应使用 pformat 格式化"""
        result = _format_as_text(42)
        assert "42" in result

        result = _format_as_text("hello")
        assert "hello" in result


class TestFormatAsCsv:
    """测试 _format_as_csv 函数"""

    def test_dataframe(self):
        """DataFrame 应格式化为 CSV 字符串"""
        df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
        result = _format_as_csv(df)
        assert "col1" in result
        assert "col2" in result
        assert "1,a" in result or "1" in result
        assert "2,b" in result or "2" in result

    def test_dict_with_dataframe(self):
        """带 DataFrame 的字典应分块格式化"""
        df = pd.DataFrame({"x": [1, 2]})
        data = {"table": df, "count": 2}
        result = _format_as_csv(data)
        assert "# table" in result
        assert "# count: 2" in result

    def test_dict_without_dataframe(self):
        """不含 DataFrame 的字典应使用 pformat 格式化"""
        data = {"a": 1, "b": [2, 3]}
        result = _format_as_csv(data)
        assert "a" in result or "1" in result

    def test_primitive(self):
        """基本类型应使用 pformat 格式化"""
        result = _format_as_csv(42)
        assert "42" in result

        result = _format_as_csv("hello")
        assert "hello" in result

    def test_none(self):
        """None 应输出 'None'"""
        result = _format_as_csv(None)
        assert "None" in result


class TestFormatOutput:
    """测试 format_output 主函数"""

    def test_json_format(self, capsys, tmp_path):
        """JSON 格式应正确输出到控制台"""
        data = {"items": [1, 2, 3]}
        format_output(data, output_format="json")
        captured = capsys.readouterr()
        # 验证输出是有效 JSON
        parsed = json.loads(captured.out)
        assert parsed == {"items": [1, 2, 3]}

    def test_json_format_compact(self, capsys, tmp_path):
        """JSON 紧凑模式应无缩进输出"""
        data = {"items": [1, 2, 3]}
        # 紧凑模式
        format_output(data, output_format="json", compact=True)
        captured = capsys.readouterr()
        # 紧凑模式应该没有换行
        assert "\n" not in captured.out.strip()
        # 验证输出是有效 JSON
        parsed = json.loads(captured.out)
        assert parsed == {"items": [1, 2, 3]}

    def test_json_format_pretty(self, capsys, tmp_path):
        """JSON pretty 模式应有缩进输出"""
        data = {"items": [1, 2, 3]}
        # pretty 模式（默认）
        format_output(data, output_format="json", compact=False)
        captured = capsys.readouterr()
        # pretty 模式应该有换行和缩进
        assert "\n" in captured.out
        assert "  " in captured.out  # 2 空格缩进

    def test_json_format_with_dataframe(self, capsys, tmp_path):
        """JSON 格式应将 DataFrame 转换为 records"""
        df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
        format_output(df, output_format="json")
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert parsed == [{"x": 1, "y": 3}, {"x": 2, "y": 4}]

    def test_csv_format_dataframe(self, capsys, tmp_path):
        """CSV 格式 DataFrame 应输出 CSV 字符串"""
        df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
        format_output(df, output_format="csv")
        captured = capsys.readouterr()
        assert "x,y" in captured.out
        assert "1,3" in captured.out
        assert "2,4" in captured.out

    def test_csv_format_dict_with_dataframe(self, capsys, tmp_path):
        """CSV 格式带 DataFrame 的字典应分块输出"""
        df = pd.DataFrame({"x": [1]})
        data = {"table": df, "count": 1}
        format_output(data, output_format="csv")
        captured = capsys.readouterr()
        assert "# table" in captured.out
        assert "# count: 1" in captured.out

    def test_text_format(self, capsys, tmp_path):
        """文本格式（默认）应使用 _format_as_text"""
        data = {"a": 1, "b": 2}
        format_output(data, output_format="text")
        captured = capsys.readouterr()
        assert "'a': 1" in captured.out or "'a':1" in captured.out

    def test_output_to_file(self, tmp_path):
        """输出到文件应正确写入"""
        output_file = tmp_path / "output.json"
        data = {"items": [1, 2, 3]}
        format_output(data, output=str(output_file), output_format="json")

        # 验证文件存在且内容正确
        assert output_file.exists()
        with open(output_file) as f:
            content = json.load(f)
        assert content == {"items": [1, 2, 3]}

    def test_output_creates_parent_dirs(self, tmp_path):
        """输出到文件应自动创建父目录"""
        output_file = tmp_path / "subdir" / "nested" / "output.json"
        data = {"test": "value"}
        format_output(data, output=str(output_file), output_format="json")

        # 验证文件存在
        assert output_file.exists()
        assert output_file.parent.is_dir()

    def test_output_with_limit(self, capsys, tmp_path):
        """列表限制应正确应用到输出"""
        items = list(range(10))
        format_output(items, limit=5, output_format="text")
        captured = capsys.readouterr()
        assert "共 10 条" in captured.out
        assert "已显示前 5 条" in captured.out


class TestFormatObjectAttrs:
    """测试 _format_object_attrs 函数"""

    def test_object_with_attributes(self):
        """对象属性应被提取为字典"""
        class TestObj:
            def __init__(self):
                self.name = "test"
                self.value = 42

        obj = TestObj()
        result = _format_object_attrs(obj)
        assert isinstance(result, dict)
        assert result["name"] == "test"
        assert result["value"] == 42

    def test_object_with_methods(self):
        """方法应被排除"""
        class TestObj:
            def __init__(self):
                self.value = 10

            def do_something(self):
                return "ignored"

        obj = TestObj()
        result = _format_object_attrs(obj)
        assert "value" in result
        assert "do_something" not in result

    def test_object_with_private_attrs(self):
        """私有属性（下划线开头）应被排除"""
        class TestObj:
            def __init__(self):
                self.public = "visible"
                self._private = "hidden"

        obj = TestObj()
        result = _format_object_attrs(obj)
        assert "public" in result
        assert "_private" not in result

    def test_empty_object(self):
        """无属性对象应返回 str 表示"""
        class EmptyObj:
            pass

        obj = EmptyObj()
        result = _format_object_attrs(obj)
        # 无公共非 callable 属性，返回 str(obj)
        assert isinstance(result, str)

    def test_object_with_exception_on_getattr(self):
        """getattr 抛出异常的属性应被忽略"""
        class ProblematicObj:
            @property
            def problematic(self):
                raise RuntimeError("Cannot access")

            def __init__(self):
                self.normal = "ok"

        obj = ProblematicObj()
        # 不应抛出异常
        result = _format_object_attrs(obj)
        assert "normal" in result
        assert "problematic" not in result


class TestFormatOutputIntegration:
    """集成测试：测试完整输出流程"""

    def test_dataframe_json_file_output(self, tmp_path):
        """DataFrame JSON 文件输出完整流程"""
        df = pd.DataFrame({
            "stock": ["000001.SZ", "000002.SZ"],
            "price": [10.5, 20.3],
        })
        output_file = tmp_path / "stocks.json"

        format_output(df, output=str(output_file), output_format="json")

        assert output_file.exists()
        with open(output_file) as f:
            data = json.load(f)
        assert len(data) == 2
        assert data[0]["stock"] == "000001.SZ"

    def test_csv_file_output(self, tmp_path):
        """CSV 文件输出完整流程"""
        df = pd.DataFrame({
            "date": ["2024-01-01", "2024-01-02"],
            "close": [100.0, 101.5],
        })
        output_file = tmp_path / "prices.csv"

        format_output(df, output=str(output_file), output_format="csv")

        assert output_file.exists()
        content = output_file.read_text()
        assert "date,close" in content
        assert "2024-01-01" in content

    def test_nested_dict_output(self, tmp_path):
        """嵌套字典输出"""
        data = {
            "metadata": {"count": 2, "date": "2024-01-15"},
            "records": [
                {"id": 1, "name": "first"},
                {"id": 2, "name": "second"},
            ],
        }
        output_file = tmp_path / "data.json"

        format_output(data, output=str(output_file), output_format="json")

        with open(output_file) as f:
            result = json.load(f)
        assert result["metadata"]["count"] == 2
        assert len(result["records"]) == 2