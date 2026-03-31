# Changelog

## 0.2.0 (unreleased)

### Added
- `seam-lint manifest` — generate and validate Seam Manifest files from MCP tool definitions
- `seam-lint manifest --from-json` — generate from MCP manifest JSON
- `seam-lint manifest --from-server` — generate from live MCP server
- `seam-lint manifest --validate` — validate existing manifest YAML
- `seam-lint manifest --examples` — generate example manifests to see the format
- `seam-lint scan` — scan live MCP server(s) via stdio and diagnose
- `seam-lint init` — interactive wizard to generate a composition YAML
- `seam-lint diagnose --brief` — one-line-per-file summary output
- `SeamGuard` Python API for programmatic composition analysis
- Convention taxonomy (10 dimensions) with field-pattern inference
- Auto-validation after manifest generation
- "Now what?" guidance in `check` output on failure
- Quickstart guide when running bare `seam-lint` with no subcommand
- SARIF output format for GitHub Code Scanning integration

### Fixed
- Confidence mapping: classifier internal grades (`high`/`medium`) now correctly map to manifest spec vocabulary (`declared`/`inferred`/`unknown`)
- `_examples_dir()` portability for installed packages

## 0.1.0

### Added
- `seam-lint diagnose` — full sheaf cohomology diagnostic with blind spot detection
- `seam-lint check` — CI/CD gate with configurable thresholds
- `seam-lint infer` — infer proto-composition from MCP manifest JSON
- Text, JSON, and SARIF output formats
- Exact rational arithmetic (no floating-point) via Python `Fraction`
- 9 bundled example compositions (financial, code review, ETL, RAG, auth, MCP)
- 107 tests, single dependency (PyYAML)
