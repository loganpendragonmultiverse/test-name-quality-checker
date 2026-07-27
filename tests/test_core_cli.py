import json

import pytest

from test_name_quality_checker.cli import main
from test_name_quality_checker.core import render_markdown, scan


def test_scan_finds_vague_and_duplicate_names(tmp_path):
    (tmp_path / "test_one.py").write_text(
        "def test_basic():\n    parse_record()\n", encoding="utf-8"
    )
    (tmp_path / "test_two.py").write_text(
        "async def test_basic():\n    await load_record()\n", encoding="utf-8"
    )
    report = scan(tmp_path)
    assert report["finding_count"] == 2
    assert report["findings"][0]["reasons"] == ["vague", "duplicate"]
    assert report["findings"][0]["suggestion"] == "test_parse_record_describes_expected_behavior"
    assert "Consider" in render_markdown(report)


def test_parse_error_and_validation(tmp_path):
    (tmp_path / "broken_test.py").write_text("def test_broken(:", encoding="utf-8")
    report = scan(tmp_path)
    assert len(report["parse_errors"]) == 1
    assert "Parse errors" in render_markdown(report)
    with pytest.raises(ValueError, match="directory"):
        scan(tmp_path / "missing")


def test_cli_json_fail_mode_and_safe_output(tmp_path, capsys):
    (tmp_path / "test_sample.py").write_text("def test_1():\n    run()\n", encoding="utf-8")
    assert main([str(tmp_path), "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["finding_count"] == 1
    assert main([str(tmp_path), "--fail-on-findings"]) == 1
    output = tmp_path / "report.md"
    output.write_text("keep", encoding="utf-8")
    assert main([str(tmp_path), "--output", str(output)]) == 2


def test_subject_from_method_and_fallback(tmp_path):
    (tmp_path / "test_methods.py").write_text(
        "def test_works():\n    client.fetch()\n\ndef test_case():\n    value = 1\n",
        encoding="utf-8",
    )
    report = scan(tmp_path)
    assert report["findings"][0]["subject"] == "fetch"
    assert report["findings"][1]["subject"] == "test_methods"
