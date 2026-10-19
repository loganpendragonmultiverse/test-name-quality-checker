# Testing

Use an isolated Python environment and install `python -m pip install -e ".[dev]"`.
Run `ruff format --check .`, `ruff check .`, `pytest`, and `python -m build`.
The repository CI matrix covers Python 3.10 and 3.14 on Linux, Windows, and macOS.
New regressions live alongside the existing core/CLI tests.

Repeated class, helper, and nested container regressions require no class-scope duplicates, while module and suite scopes still flag the repeated short names.

## 1.2.1 regression acceptance — 2026-10-19

Check ignored candidates versus included read attempts, retaining malformed-source attempts in the count. Exercise ordinary/new report creation, existing and dangling-symlink collisions, and a destination created immediately before exclusive open. Confirm source and competing-file bytes remain unchanged. Verify literal Markdown filenames and parser diagnostics. Run real small/large closed-pipe subprocesses and normal/in-memory/partial-write stdout cases. Confirm AST scanning does not import or execute project code and preserve all duplicate-scope, identity and suggestion regressions. Build wheel/sdist and inspect the four handoff documents, license and example bytes. Symlink tests may be skipped only on platforms that do not allow their creation; the Linux gate must execute them.

Verify that a recognized report symlink is refused before any output open, even when exclusive open would follow a dangling link on Windows. Retain both real symlink cases and the ordinary racing-file regression; do not add skips or weaken the 90% floor. The check/open pair is not an atomic hostile-filesystem boundary.
