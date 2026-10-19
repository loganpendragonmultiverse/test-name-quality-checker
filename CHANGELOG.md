# Changelog

## 1.2.1 - 2026-10-19

- Refuse pre-existing report symlinks before exclusive open, including dangling Windows links.

- Count only included scan attempts, retaining parse-error attempts.
- Create report files exclusively and return actionable output/closed-pipe errors without replacing existing destinations.
- Render authored paths and parser diagnostics as literal Markdown text.
- Include handoff documents, license and the existing example in wheel and source packages.

## 1.2.0 - 2026-10-16

- Distinguish repeated same-name lexical container definitions in class scope using source locations.

- Report qualified names and source identities for synchronous, async, and nested test definitions.
- Add class, module, and suite duplicate scopes, keeping suite scope as the default.

## 1.1.0 - 2026-07-27

- Added configurable overlong-name findings and a CLI name-length limit.
- Added per-file test and finding summaries.

## 1.0.0 - 2026-07-26

- Added non-executing Python AST test discovery.
- Added vague-name, duplicate-name, and parse-error findings.
- Added behavior-oriented suggestion templates and optional CI failure mode.
