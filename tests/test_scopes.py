import json

import pytest

from test_name_quality_checker.cli import main
from test_name_quality_checker.core import render_markdown, scan


def populate(root):
    (root / "test_one.py").write_text(
        "class TestFirst:\n"
        "    def test_saves_record(self): pass\n"
        "    async def test_saves_record(self): pass\n"
        "class TestSecond:\n"
        "    def test_saves_record(self): pass\n"
        "def test_saves_record(): pass\n"
        "def helper():\n"
        "    async def test_saves_record(): pass\n"
        "    async def test_saves_record(): pass\n",
        encoding="utf-8",
    )
    (root / "test_two.py").write_text("def test_saves_record(): pass\n", encoding="utf-8")


def test_suite_default_and_module_scope(tmp_path):
    populate(tmp_path)
    default = scan(tmp_path)
    assert default == scan(tmp_path, duplicate_scope="suite")
    assert default["tests_found"] == 7 and default["finding_count"] == 7
    module = scan(tmp_path, duplicate_scope="module")
    assert module["finding_count"] == 6
    assert all(x["file"] == "test_one.py" for x in module["findings"])


def test_class_scope_distinguishes_containers_and_real_duplicates(tmp_path):
    populate(tmp_path)
    report = scan(tmp_path, duplicate_scope="class")
    assert report["finding_count"] == 4
    assert [x["qualified_name"] for x in report["findings"]] == [
        "TestFirst.test_saves_record",
        "TestFirst.test_saves_record",
        "helper.test_saves_record",
        "helper.test_saves_record",
    ]
    assert len({x["identity"] for x in report["findings"]}) == 4
    assert "TestFirst.test_saves_record" in render_markdown(report)
    assert report == scan(tmp_path, duplicate_scope="class")


def test_scope_cli_and_invalid_api(tmp_path, capsys):
    populate(tmp_path)
    assert main([str(tmp_path), "--duplicate-scope", "class", "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["duplicate_scope"] == "class"
    with pytest.raises(ValueError, match="duplicate-scope"):
        scan(tmp_path, duplicate_scope="invalid")


def test_nested_classes_and_vague_names_still_reported(tmp_path):
    (tmp_path / "test_nested.py").write_text(
        "class Outer:\n"
        "    class Inner:\n"
        "        async def test_basic(self): pass\n"
        "def test_basic(): pass\n",
        encoding="utf-8",
    )
    report = scan(tmp_path, duplicate_scope="class")
    assert [x["reasons"] for x in report["findings"]] == [["vague"], ["vague"]]
    assert report["findings"][0]["qualified_name"] == "Outer.Inner.test_basic"


@pytest.mark.parametrize(
    "definition",
    [
        "class TestRepeated:\n    def test_saves_record(self): pass\n",
        "def helper():\n    async def test_saves_record(): pass\n",
        "class Outer:\n    class Inner:\n        def test_saves_record(self): pass\n",
    ],
)
def test_repeated_container_definitions_remain_distinct(tmp_path, definition):
    (tmp_path / "test_repeated.py").write_text(definition + "\n" + definition, encoding="utf-8")
    local = scan(tmp_path, duplicate_scope="class")
    assert local["tests_found"] == 2
    assert local["finding_count"] == 0
    for scope in ("module", "suite"):
        report = scan(tmp_path, duplicate_scope=scope)
        assert report["finding_count"] == 2
        assert all(f["reasons"] == ["duplicate"] for f in report["findings"])
        assert len({f["qualified_name"] for f in report["findings"]}) == 1
        assert len({f["container_id"] for f in report["findings"]}) == 2
