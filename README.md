# seam-lint

Static analysis for agent tool compositions. Finds semantic blind spots that bilateral verification cannot reach and recommends bridge annotations to eliminate them.

**Zero heavy dependencies.** Only requires PyYAML. No numpy, no scipy, no LLM calls. Installs in under a second.

## Install

```bash
pip install seam-lint
```

## Quick start

Run the built-in examples to see output immediately:

```bash
seam-lint diagnose --examples
```

Diagnose your own composition:

```bash
seam-lint diagnose my_pipeline.yaml
```

## Library API (v0.2)

`SeamGuard` is the primary programmatic interface. Use it to embed coherence analysis in any Python application, agent framework, or CI pipeline.

```python
from seam_lint import SeamGuard, SeamCheckError

# Path A: From raw tool definitions (the framework integration path)
guard = SeamGuard.from_tools({
    "invoice_parser": {
        "fields": ["total_amount", "due_date", "line_items", "currency"],
        "conventions": {"amount_unit": "dollars", "date_format": "ISO-8601"},
    },
    "settlement_engine": {
        "fields": ["amount", "settlement_date", "ledger_entry"],
        "conventions": {"amount_unit": "cents"},
    },
}, edges=[("invoice_parser", "settlement_engine")])

# Path B: From MCP manifest JSON
guard = SeamGuard.from_mcp_manifest("manifest.json")

# Path C: From YAML composition (the v0.1 path)
guard = SeamGuard.from_composition("pipeline.yaml")

# Path D: From a live MCP server via stdio
guard = SeamGuard.from_mcp_server("python my_server.py")

# Diagnose
diag = guard.diagnose()
diag.coherence_fee         # int
diag.blind_spots           # list[BlindSpot]
diag.bridges               # list[Bridge]

# Check (raises SeamCheckError if thresholds exceeded)
guard.check(max_blind_spots=0, max_unbridged=0)

# Export
guard.to_yaml("pipeline.yaml")   # save for CI
guard.to_json()                   # JSON string with version + hash
guard.to_sarif()                  # SARIF string
```

### Framework integration example

A LangChain integration becomes:

```python
from seam_lint import SeamGuard

class SeamCoherenceCallback(BaseCallbackHandler):
    def on_chain_start(self, serialized, inputs, **kwargs):
        tools = extract_tools_from_chain(serialized)
        guard = SeamGuard.from_tools(tools)
        diag = guard.diagnose()
        if diag.coherence_fee > 0:
            warnings.warn(f"Composition has {len(diag.blind_spots)} blind spots")
```

## What it does

When tools in a pipeline share implicit conventions (date formats, unit scales, encoding schemes), some of those conventions may be invisible to bilateral verification -- each pair of tools looks correct in isolation, but the pipeline as a whole can silently produce wrong results.

seam-lint computes the **coherence fee**: the number of independent semantic dimensions that fall through the cracks of pairwise checks. For each blind spot, it recommends a **bridge** -- a specific field to expose in the tool's observable schema.

```
  Financial Analysis Pipeline
  ═══════════════════════════

  Topology: 3 tools, 3 edges, beta_1 = 1

  Blind spots (2):
    [1] day_conv_match (data_provider -> financial_analysis)
        day_convention hidden on both sides
    [2] metric_type_match (financial_analysis -> portfolio_verification)
        risk_metric hidden on both sides

  Recommended bridges:
    [1] Add 'day_convention' to F(data_provider) and F(financial_analysis)
    [2] Add 'risk_metric' to F(financial_analysis) and F(portfolio_verification)

  After bridging: fee = 0
```

## Composition format

Compositions are YAML files that describe your tool pipeline. See [`composition-schema.json`](composition-schema.json) for the full schema.

```yaml
name: My Pipeline

tools:
  tool_a:
    internal_state: [field_x, field_y, hidden_z]
    observable_schema: [field_x, field_y]

  tool_b:
    internal_state: [field_x, hidden_z]
    observable_schema: [field_x]

edges:
  - from: tool_a
    to: tool_b
    dimensions:
      - name: x_match
        from_field: field_x
        to_field: field_x
      - name: z_match
        from_field: hidden_z
        to_field: hidden_z
```

- **`internal_state`**: All semantic dimensions the tool operates on internally (the full stalk S(v)).
- **`observable_schema`**: Dimensions visible in the tool's API (the observable sub-sheaf F(v)). Must be a subset of `internal_state`.
- **`edges`**: Bilateral interfaces between tools. Each dimension names a shared convention.

A dimension is a **blind spot** when `from_field` or `to_field` is in `internal_state` but not in `observable_schema` of the respective tool.

## Commands

### `seam-lint diagnose`

Diagnose compositions and report blind spots, bridges, and the coherence fee.

```bash
seam-lint diagnose pipeline.yaml                    # text output
seam-lint diagnose --format json pipeline.yaml      # JSON with version + SHA-256
seam-lint diagnose --format sarif pipeline.yaml     # SARIF for GitHub code scanning
seam-lint diagnose --examples                       # run on bundled examples
```

### `seam-lint check`

CI/CD gate. Exits with code 1 if any composition exceeds the specified thresholds.

```bash
seam-lint check pipeline.yaml                                   # default: --max-blind-spots 0 --max-unbridged 0
seam-lint check --max-blind-spots 2 compositions/               # allow up to 2 blind spots
seam-lint check --format sarif compositions/ > results.sarif    # SARIF for GitHub Actions
```

### `seam-lint scan`

Scan live MCP servers via stdio. Zero configuration — no YAML required.

```bash
seam-lint scan "python my_server.py"                             # single server
seam-lint scan "python server_a.py" "python server_b.py"         # multi-server composition
seam-lint scan "python server.py" -o pipeline.yaml               # save for CI
seam-lint scan "python server.py" --format json                  # JSON diagnostic
```

The scanner spawns each server as a subprocess, performs the MCP initialize handshake, queries `tools/list`, and auto-generates a composition using the heuristic dimension classifier. No MCP SDK dependency.

### `seam-lint manifest`

Generate or validate [Seam Manifest](seam-manifest-spec-v0.1.md) files.

```bash
seam-lint manifest --from-json tools.json -o manifest.yaml       # from MCP manifest JSON
seam-lint manifest --from-server "python server.py"              # from live MCP server
seam-lint manifest --validate manifest.yaml                      # validate against spec
```

### `seam-lint init`

Interactive wizard to generate a composition YAML.

```bash
seam-lint init
seam-lint init -o my_pipeline.yaml
```

### `seam-lint infer`

Infer a proto-composition from an MCP manifest JSON.

```bash
seam-lint infer manifest.json                # stdout
seam-lint infer manifest.json -o proto.yaml  # save to file
```

### `seam-lint --version`

Print the installed version.

## Seam Manifest Specification

The [Seam Manifest Spec v0.1](seam-manifest-spec-v0.1.md) defines a per-tool convention declaration format. Each manifest declares what semantic conventions a single tool assumes (e.g. "amounts are in dollars", "dates are ISO-8601").

See the [spec](seam-manifest-spec-v0.1.md), [JSON Schema](seam-manifest-schema.json), and the built-in [taxonomy](src/seam_lint/taxonomy.yaml) of 10 convention dimensions.

## CI integration

### GitHub Actions with SARIF

```yaml
name: seam-lint
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install seam-lint
      - run: seam-lint check --format sarif compositions/ > seam-lint.sarif
      - uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: seam-lint.sarif
```

This uploads results to GitHub's code scanning tab, where blind spots appear as annotations on pull requests.

### Simple pass/fail

```yaml
      - run: pip install seam-lint
      - run: seam-lint check compositions/
```

## Output formats

| Format | Flag | Use case |
|--------|------|----------|
| Text | `--format text` (default) | Developer terminal |
| JSON | `--format json` | Orchestrator integration, includes version + SHA-256 |
| SARIF | `--format sarif` | GitHub code scanning, VS Code SARIF viewer |

## How it works

seam-lint builds a discrete coboundary operator (delta-0) from C^0 (tool dimensions) to C^1 (edge dimensions) for both the observable sheaf F and the full sheaf S. The coherence fee is:

```
fee = H^1(F_obs) - H^1(F_full)
    = (dim C^1 - rank delta_obs) - (dim C^1 - rank delta_full)
    = rank delta_full - rank delta_obs
```

Each unit of fee corresponds to an independent semantic dimension that bilateral verification cannot detect. Bridging (exposing hidden fields in the observable schema) increases rank(delta_obs) until it matches rank(delta_full).

The rank computation uses exact arithmetic (Python's `fractions.Fraction` module) via Gaussian elimination -- no floating-point tolerance, no numpy dependency.

## License

MIT
