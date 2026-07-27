from __future__ import annotations

import ast
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

VAGUE = re.compile(
    r"^test(?:_\d+|_(?:basic|simple|works|working|function|method|happy_path|case|thing))?$",
    re.IGNORECASE,
)


def _called_subject(node: ast.AST, fallback: str) -> str:
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            function = child.func
            if isinstance(function, ast.Name) and function.id not in {"print"}:
                return re.sub(r"\W+", "_", function.id).strip("_").casefold()
            if isinstance(function, ast.Attribute):
                return re.sub(r"\W+", "_", function.attr).strip("_").casefold()
    return re.sub(r"\W+", "_", fallback).strip("_").casefold()


def scan(root: Path, max_name_length: int = 80) -> dict[str, Any]:
    if not root.is_dir():
        raise ValueError("root must be a directory")
    if max_name_length < 20:
        raise ValueError("max-name-length must be at least 20")
    tests = []
    parse_errors = []
    paths = sorted({*root.rglob("test_*.py"), *root.rglob("*_test.py")})
    for path in paths:
        if any(part in {".git", ".venv", "build", "dist"} for part in path.parts):
            continue
        relative = path.relative_to(root).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        except (OSError, UnicodeError, SyntaxError) as exc:
            parse_errors.append({"file": relative, "error": str(exc)})
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith(
                "test"
            ):
                tests.append(
                    {
                        "file": relative,
                        "line": node.lineno,
                        "name": node.name,
                        "subject": _called_subject(node, path.stem),
                    }
                )
    by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for test in tests:
        by_name[test["name"]].append(test)
    findings = []
    for test in tests:
        reasons = []
        if VAGUE.fullmatch(test["name"]):
            reasons.append("vague")
        if len(by_name[test["name"]]) > 1:
            reasons.append("duplicate")
        if len(str(test["name"])) > max_name_length:
            reasons.append("overlong")
        if reasons:
            findings.append(
                {
                    **test,
                    "reasons": reasons,
                    "suggestion": f"test_{test['subject']}_describes_expected_behavior",
                }
            )
    file_summary: dict[str, dict[str, int]] = {}
    for test in tests:
        file_summary.setdefault(str(test["file"]), {"tests": 0, "findings": 0})["tests"] += 1
    for finding in findings:
        file_summary[str(finding["file"])]["findings"] += 1
    return {
        "version": 1,
        "max_name_length": max_name_length,
        "files_scanned": len(paths),
        "tests_found": len(tests),
        "finding_count": len(findings),
        "findings": findings,
        "files": file_summary,
        "parse_errors": parse_errors,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Test Name Quality Report",
        "",
        f"**{report['tests_found']} tests · {report['finding_count']} findings · {len(report['parse_errors'])} parse errors**",
        "",
    ]
    for finding in report["findings"]:
        lines.extend(
            [
                f"- `{finding['file']}:{finding['line']}` — `{finding['name']}` ({', '.join(finding['reasons'])})",
                f"  - Consider: `{finding['suggestion']}`",
            ]
        )
    if report["parse_errors"]:
        lines.extend(["", "## Parse errors", ""])
        lines.extend(f"- `{item['file']}` — {item['error']}" for item in report["parse_errors"])
    return "\n".join(lines).rstrip() + "\n"


def render_json(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, ensure_ascii=False) + "\n"
