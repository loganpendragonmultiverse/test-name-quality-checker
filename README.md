# Test Name Quality Checker

[![CI](https://github.com/loganpendragonmultiverse/test-name-quality-checker/actions/workflows/ci.yml/badge.svg)](https://github.com/loganpendragonmultiverse/test-name-quality-checker/actions/workflows/ci.yml)

Test Name Quality Checker scans Python test functions and methods, flags vague or duplicated names, and proposes behavior-oriented naming templates based on the first called subject it can identify.

## Three-minute start

```bash
python -m pip install .
test-name-check .
test-name-check . --fail-on-findings
test-name-check . --max-name-length 80
```

The scanner uses Python's AST and never imports or executes the tested project. Version 1.1 adds configurable overlong-name findings plus per-file test/finding summaries. Markdown and JSON reports include file and line evidence, reasons, suggestions, and parse errors. The optional failure flag supports gradual CI adoption.

Suggestions are mechanical prompts, not authoritative names. They cannot infer business intent or expected behavior and should be rewritten by a maintainer. Version 1 targets Python test functions only. Requires Python 3.10 or newer.

Part of the [Logan Pendragon Forge open-source collection](https://www.loganpendragonforge.com/open-source/). Licensed under the [MIT License](LICENSE).
