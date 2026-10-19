import html
import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from test_name_quality_checker import cli
from test_name_quality_checker.core import render_markdown, scan


def populate(root):
    source = root / "test_sample.py"
    source.write_text("def test_basic():\n    subject()\n", encoding="utf-8")
    return source


def test_ignored_candidates_do_not_inflate_read_attempts(tmp_path):
    source = populate(tmp_path)
    for ignored in (".git", ".venv", "build", "dist"):
        folder = tmp_path / ignored
        folder.mkdir()
        (folder / "test_ignored.py").write_text("not Python!", encoding="utf-8")
    (tmp_path / "test_broken.py").write_text("def test_broken(:", encoding="utf-8")
    before = source.read_bytes()
    report = scan(tmp_path)
    assert report["files_scanned"] == 2
    assert report["tests_found"] == 1
    assert len(report["parse_errors"]) == 1
    assert report["parse_errors"][0]["file"] == "test_broken.py"
    assert source.read_bytes() == before


def test_scan_counts_an_included_read_failure(tmp_path, monkeypatch):
    source = populate(tmp_path)
    original = Path.read_text

    def fail_read(path, *args, **kwargs):
        if path == source:
            raise OSError("read denied")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fail_read)
    report = scan(tmp_path)
    assert report["files_scanned"] == 1
    assert report["tests_found"] == 0
    assert "read denied" in report["parse_errors"][0]["error"]


def test_scan_never_imports_or_executes_source(tmp_path):
    marker = tmp_path / "executed"
    source = tmp_path / "test_side_effect.py"
    source.write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n"
        "raise RuntimeError('must never execute')\n"
        "async def test_basic():\n    await client.fetch()\n",
        encoding="utf-8",
    )
    report = scan(tmp_path)
    assert report["tests_found"] == 1
    assert report["findings"][0]["suggestion"] == "test_fetch_describes_expected_behavior"
    assert not marker.exists()


def test_new_report_is_complete_and_does_not_change_source(tmp_path):
    source = populate(tmp_path)
    before = source.read_bytes()
    output = tmp_path / "report.json"
    assert cli.main([str(tmp_path), "--format", "json", "--output", str(output)]) == 0
    assert json.loads(output.read_text(encoding="utf-8")) == scan(tmp_path)
    assert source.read_bytes() == before


def test_existing_destination_and_missing_parent_fail_cleanly(tmp_path, capsys):
    populate(tmp_path)
    output = tmp_path / "report.md"
    output.write_bytes(b"competing file")
    assert cli.main([str(tmp_path), "--output", str(output)]) == 2
    assert output.read_bytes() == b"competing file"
    assert "error:" in capsys.readouterr().err
    assert cli.main([str(tmp_path), "--output", str(tmp_path / "missing" / "report.md")]) == 2
    assert not (tmp_path / "missing").exists()


@pytest.mark.parametrize("dangling", [False, True])
def test_report_symlinks_preserve_target_and_link(tmp_path, dangling):
    populate(tmp_path)
    target = tmp_path / "target.md"
    if not dangling:
        target.write_bytes(b"target sentinel")
    output = tmp_path / "report.md"
    try:
        output.symlink_to(target)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")
    assert cli.main([str(tmp_path), "--output", str(output)]) == 2
    assert output.is_symlink()
    assert target.exists() is not dangling
    if not dangling:
        assert target.read_bytes() == b"target sentinel"


def test_racing_destination_is_not_overwritten(tmp_path, monkeypatch):
    source = populate(tmp_path)
    before = source.read_bytes()
    output = tmp_path / "report.json"
    original = Path.open
    modes = []

    def create_before_open(path, mode="r", *args, **kwargs):
        if path == output and mode == "x":
            modes.append(mode)
            with original(path, "w", encoding="utf-8") as stream:
                stream.write("racing sentinel")
        return original(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", create_before_open)
    assert cli.main([str(tmp_path), "--output", str(output)]) == 2
    assert modes == ["x"]
    assert output.read_text(encoding="utf-8") == "racing sentinel"
    assert source.read_bytes() == before


def test_markdown_paths_and_parser_messages_are_literal(tmp_path):
    name = "test_" + chr(96) + "[link](target)&.py"
    (tmp_path / name).write_text("def test_basic(): pass\n", encoding="utf-8")
    report = scan(tmp_path)
    message = "<script>alert(1)</script>\n![image](remote)" + chr(96)
    report["parse_errors"].append({"file": name, "error": message})
    rendered = render_markdown(report)
    assert name not in rendered
    assert "<script>" not in rendered
    assert "![image](remote)" not in rendered
    assert "&#96;" in rendered
    assert html.unescape(rendered).count(name) == 2
    assert message in html.unescape(rendered)


@pytest.mark.parametrize("count", [1, 600])
def test_real_closed_stdout_exits_two_without_shutdown_traceback(tmp_path, count):
    source = tmp_path / "test_many.py"
    source.write_text(
        "".join(f"def test_{number}(): pass\n" for number in range(count)),
        encoding="utf-8",
    )
    before = source.read_bytes()
    read_fd, write_fd = os.pipe()
    os.close(read_fd)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "test_name_quality_checker", str(tmp_path), "--format", "json"],
            check=False,
            stdout=write_fd,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
        )
    finally:
        os.close(write_fd)
    assert result.returncode == 2
    assert "error:" in result.stderr
    assert "Traceback" not in result.stderr
    assert "Exception ignored" not in result.stderr
    assert source.read_bytes() == before


def test_normal_and_in_memory_stdout_are_complete(tmp_path, capsys, monkeypatch):
    populate(tmp_path)
    expected = scan(tmp_path)
    assert cli.main([str(tmp_path), "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out) == expected
    stream = io.StringIO()
    monkeypatch.setattr(sys, "stdout", stream)
    assert cli.main([str(tmp_path), "--format", "json"]) == 0
    assert json.loads(stream.getvalue()) == expected


def test_partial_descriptor_writes_deliver_complete_utf8(monkeypatch):
    class Stream:
        encoding = "utf-8"
        errors = "strict"

        def fileno(self):
            return 123

        def flush(self):
            pass

    received = bytearray()

    def partial_write(fd, data):
        assert fd == 123
        chunk = bytes(data[:2])
        received.extend(chunk)
        return len(chunk)

    monkeypatch.setattr(sys, "stdout", Stream())
    monkeypatch.setattr(cli.os, "write", partial_write)
    cli._write_stdout("Unicode αβ report\n")
    assert received.decode("utf-8") == "Unicode αβ report\n"


def test_zero_descriptor_write_is_a_cli_error(tmp_path, monkeypatch, capsys):
    populate(tmp_path)

    class Stream(io.StringIO):
        def fileno(self):
            return 123

    monkeypatch.setattr(sys, "stdout", Stream())
    monkeypatch.setattr(cli.os, "write", lambda fd, data: 0)
    assert cli.main([str(tmp_path)]) == 2
    assert "stdout accepted no report bytes" in capsys.readouterr().err


def test_in_memory_flush_failure_is_a_cli_error(tmp_path, monkeypatch, capsys):
    populate(tmp_path)

    class Stream(io.StringIO):
        def flush(self):
            raise OSError("flush failed")

    monkeypatch.setattr(sys, "stdout", Stream())
    assert cli.main([str(tmp_path)]) == 2
    assert "flush failed" in capsys.readouterr().err
