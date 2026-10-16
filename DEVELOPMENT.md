# Development contract

Review Python test names through read-only AST parsing without importing or executing project code.

Version 1.1 adds configurable length diagnostics and per-file summaries. Suggestions remain mechanical prompts, not inferred business intent.

Every feature release must update tests, version metadata, changelog, README claims, repository metadata, release assets, and the Forge catalog together.

## 1.2.0 - 2026-10-16

Report qualified names and source identities for synchronous, async, and nested test definitions. Add class, module, and suite duplicate scopes, keeping suite scope as the default.

See README.md for interface details and TESTING.md for the verification gate.
