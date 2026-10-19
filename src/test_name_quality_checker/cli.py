from __future__ import annotations

import argparse
import io
import os
import sys
from pathlib import Path

from .core import render_json, render_markdown, scan


def _write_stdout(rendered: str) -> None:
    """Deliver bytes without retaining a failed buffered report for shutdown."""
    try:
        descriptor = sys.stdout.fileno()
    except (AttributeError, io.UnsupportedOperation):
        sys.stdout.write(rendered)
        sys.stdout.flush()
        return
    pending = memoryview(
        rendered.encode(sys.stdout.encoding or "utf-8", sys.stdout.errors or "strict")
    )
    while pending:
        written = os.write(descriptor, pending)
        if written <= 0:
            raise OSError("stdout accepted no report bytes")
        pending = pending[written:]
    sys.stdout.flush()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Review Python test names without changing source files."
    )
    parser.add_argument("root", type=Path, nargs="?", default=Path.cwd())
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fail-on-findings", action="store_true")
    parser.add_argument("--max-name-length", type=int, default=80)
    parser.add_argument(
        "--duplicate-scope",
        choices=("class", "module", "suite"),
        default="suite",
        help="compare names within a lexical container, file, or whole scan",
    )
    args = parser.parse_args(argv)
    try:
        report = scan(args.root, args.max_name_length, duplicate_scope=args.duplicate_scope)
        rendered = render_json(report) if args.format == "json" else render_markdown(report)
        if args.output:
            if args.output.is_symlink():
                raise ValueError(f"output must not be a symlink: {args.output}")
            with args.output.open("x", encoding="utf-8", newline="\n") as output:
                output.write(rendered)
        else:
            _write_stdout(rendered)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 1 if args.fail_on_findings and (report["finding_count"] or report["parse_errors"]) else 0
