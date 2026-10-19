# Development contract

Review Python test names through read-only AST parsing without importing or executing project code.

Version 1.1 adds configurable length diagnostics and per-file summaries. Suggestions remain mechanical prompts, not inferred business intent.

Every feature release must update tests, version metadata, changelog, README claims, repository metadata, release assets, and the Forge catalog together.

## 1.2.0 - 2026-10-16

Report qualified names and source identities for synchronous, async, and nested test definitions. Add class, module, and suite duplicate scopes, keeping suite scope as the default.

See README.md for interface details and TESTING.md for the verification gate.

## 1.2.1 — 2026-10-19

Scan totals count included file read attempts, including parse errors, and exclude ignored candidate paths. Reports refuse pre-existing report symlinks, including dangling links, before exclusive file creation. Failed terminal writes return status 2 with a diagnostic. Markdown keeps authored filenames and parser messages literal. AST discovery, source identities, duplicate scopes and mechanical suggestions are unchanged.

Keep output creation exclusive and stdout failures inside the CLI error boundary. Package the four handoff documents, license and existing example with both distributions. Preserve the non-executing AST contract and existing lexical-container identities.

Reject a pre-existing output symlink immediately before exclusive open. Keep ordinary file-race protection; do not claim that the check/open pair atomically blocks hostile leaf-link or parent-directory replacement.
