# Changelog

## 0.6.0

### Added
- **Witness kernel** (`witness.py`): deterministic measurement → receipt pipeline with three-layer separation (measurement / binding / judgment)
- **Constitutional objects**: `Disposition` enum (5 levels), `BridgePatch` (frozen, Seam Patch v0.1), `WitnessReceipt` (content-addressable, tamper-evident)
- **`seam-lint serve`** — MCP stdio server exposing 2 tools + 1 resource:
  - `seam_lint.witness`: composition YAML → WitnessReceipt (atomic measure-bind-judge)
  - `seam_lint.bridge`: composition YAML → patched composition + receipt + before/after metrics
  - `seam_lint.taxonomy` resource: convention taxonomy for agent inspection
- **`seam-lint bridge`** — auto-generate bridged composition YAML or Seam Patches from diagnosed composition
- **`seam-lint witness`** — diagnose and emit WitnessReceipt as JSON
- **`Diagnostic.content_hash()`** — deterministic SHA-256 of measurement content (excludes timestamps)
- **`load_composition(text=)`** — parser accepts string input for MCP server use
- **Policy profile**: `witness()` and `_resolve_disposition()` accept named `policy_profile` parameter (default: `witness.default.v1`), recorded in receipt and receipt hash
- **Seam Patch v0.1**: `BridgePatch.to_seam_patch()` — explicitly typed patch format, not RFC 6902
- **Typed error vocabulary**: `WitnessErrorCode` enum (4 codes), `WitnessError` exception
- **Anti-reflexivity enforcement**: AST-level test proves `diagnostic.py` has zero imports from `witness.py` (Law 1); bounded recursion via `depth` parameter with `MAX_DEPTH=10` (Law 7)
- **Three-hash boundary**: `composition_hash` (what was proposed), `diagnostic_hash` (what was measured), `receipt_hash` (what was witnessed) — tested for independence
- 33 new tests (233 total)

### Fixed
- **Bridge generation bug**: when `from_field != to_field` and both sides hidden, destination tool received wrong field. Now generates separate Bridge per side with correct field.

### Changed
- `to_json_patch()` renamed to `to_seam_patch()` with `seam_patch_version: "0.1.0"` field
- `receipt_hash` docstring documents timestamp inclusion semantics (unique event identity vs deduplication via `diagnostic_hash`)
- Bridge response includes `original_composition_hash` for traceability

## 0.5.0

### Added
- **Three-tier confidence: "unknown" tier now live** — single description-keyword-only or weak schema signals (enum partial overlap, integer type inference) now correctly produce `unknown` instead of the dead-branch `inferred`
- **0-100 range disambiguation** — fields with `minimum: 0, maximum: 100` now check field name and description for rate/percent indicators before choosing `rate_scale` vs `score_range`
- **Domain-aware prioritization** — `classify_tool_rich()` accepts `domain_hint` (e.g. `"financial"`, `"ml"`) to boost domain-relevant dimensions from `unknown` → `inferred`
- **`_normalize_enum_value()` helper** — single source of truth for enum normalization (lowercase, strip hyphens/underscores), replacing duplicated inline logic
- **Real MCP validation suite** — 5 realistic tool definitions (Stripe, GitHub, Datadog, Slack, ML) with per-tool coverage assertions
- **End-to-end coverage test** — real MCP JSON → generate manifests → validate → assert ≥6/10 dimensions detected
- **Domain map API** — `_get_domain_map()` loads taxonomy `domains` metadata (previously defined but unused)
- 16 new tests covering unknown tier, range disambiguation, domain boosting, normalization, real-tool coverage, and E2E pipeline (178 total)

### Changed
- `_merge_signals()` accepts `domain_hint` parameter for confidence boosting
- `classify_tool_rich()` accepts `domain_hint` parameter (backward-compatible, defaults to `None`)
- Description-only signals now produce `unknown` confidence (was incorrectly `inferred`)

### Fixed
- Dead `else` branch in `_merge_signals()` — the "unknown" confidence tier was unreachable (all paths produced "inferred")
- Field name propagation for description hits in `_merge_signals()` — description hits now inherit field names from co-occurring name/schema hits
- Circular import between `classifier.py` and `mcp.py` now documented with inline comment
- False positive: `format: "uri"` / `"email"` / `"uri-reference"` no longer mapped to `encoding` dimension — these are string formats, not encoding conventions
- False positive: `count` removed from `id_offset` field name patterns — count is a quantity, not an index
- Text formatter now explains fee-vs-blind-spots divergence when fee = 0 but blind spots exist

## 0.4.0

### Added
- **Multi-signal convention inference**: classifier now uses three independent signal sources instead of field-name regex alone
  - Signal 1: Field name pattern matching (existing, now taxonomy-compiled)
  - Signal 2: Description keyword matching — detects conventions from tool/field descriptions (e.g. "amounts in cents", "ISO-8601 timestamps")
  - Signal 3: JSON Schema structural signals — `format`, `type`+range, `enum`, `pattern` metadata
- **Nested property extraction**: recursive extraction of fields from nested JSON Schema objects with dot-path naming (e.g. `invoice.total_amount`), depth limit 3
- **Taxonomy as single source of truth**: `field_patterns` from `taxonomy.yaml` now compile into classifier regex at load time; `known_values` drive enum matching
- **Three-tier confidence model**: `declared` (2+ independent signals agree), `inferred` (1 strong signal), `unknown` (weak/ambiguous) — replaces the binary high/medium system
- `FieldInfo` dataclass for rich field metadata (type, format, enum, min/max, pattern, description)
- `classify_tool_rich()` high-level API for full multi-signal classification of MCP tool definitions
- `classify_description()` for extracting dimension signals from tool descriptions
- `classify_schema_signal()` for extracting dimension signals from JSON Schema metadata
- `description_keywords` per dimension in taxonomy (v0.2)
- Currency codes (USD, EUR, GBP, JPY, CNY, BTC) added to `amount_unit` known_values
- `extract_field_infos()` public API for rich field extraction from tool schemas
- Manifest generation now uses multi-signal classifier with `sources` metadata in output
- 41 new tests covering all signal types, confidence tiers, and round-trip validation (162 total)

### Changed
- Confidence values in generated manifests are now directly `declared`/`inferred`/`unknown` — the `_CONFIDENCE_MAP` translation layer is removed
- `infer_from_manifest()` output now includes signal sources in review comments
- Taxonomy version bumped to 0.2

### Fixed
- Version string tests now use `__version__` import instead of hardcoded values

## 0.3.0

### Added
- `seam-lint manifest --publish` — anchor manifest commitment hash to Bitcoin timechain via OpenTimestamps
- `seam-lint manifest --verify` — verify OTS proof on a published manifest
- `seam-lint manifest --verify --upgrade` — upgrade pending proofs to confirmed after Bitcoin block inclusion
- Optional `[ots]` extra: `pip install seam-lint[ots]` (base install stays single-dependency)
- Commitment hash excludes OTS fields for deterministic verification after publish
- 11 new OTS tests (mocked calendars, no network required)

## 0.2.0

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
