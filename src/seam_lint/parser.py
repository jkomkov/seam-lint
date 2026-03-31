"""YAML composition parser with inline schema validation."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from seam_lint.model import Composition, Edge, SemanticDimension, ToolSpec

try:
    import yaml
except ImportError:
    print("seam-lint requires PyYAML: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


class CompositionError(Exception):
    """Raised when a composition file fails validation."""


def _require_key(data: dict[str, Any], key: str, context: str) -> Any:
    if key not in data:
        raise CompositionError(f"Missing required field '{key}' in {context}")
    return data[key]


def _require_type(value: Any, expected: type, field: str, context: str) -> None:
    if not isinstance(value, expected):
        raise CompositionError(
            f"Field '{field}' in {context} must be {expected.__name__}, "
            f"got {type(value).__name__}"
        )


def _validate_tool(name: str, spec: Any) -> ToolSpec:
    _require_type(spec, dict, name, "tools")
    internal = _require_key(spec, "internal_state", f"tool '{name}'")
    _require_type(internal, list, "internal_state", f"tool '{name}'")
    if not internal:
        raise CompositionError(
            f"Tool '{name}' must have at least one internal_state dimension"
        )
    for i, dim in enumerate(internal):
        _require_type(dim, str, f"internal_state[{i}]", f"tool '{name}'")

    observable = _require_key(spec, "observable_schema", f"tool '{name}'")
    _require_type(observable, list, "observable_schema", f"tool '{name}'")
    for i, dim in enumerate(observable):
        _require_type(dim, str, f"observable_schema[{i}]", f"tool '{name}'")

    obs_tuple = tuple(observable)
    int_tuple = tuple(internal)
    for field in obs_tuple:
        if field not in int_tuple:
            raise CompositionError(
                f"Tool '{name}': observable_schema field '{field}' "
                f"is not in internal_state"
            )

    return ToolSpec(name=name, internal_state=int_tuple, observable_schema=obs_tuple)


def _validate_edge(edge_data: Any, index: int, tool_names: set[str]) -> Edge:
    context = f"edge[{index}]"
    _require_type(edge_data, dict, f"edges[{index}]", "edges")
    from_tool = _require_key(edge_data, "from", context)
    _require_type(from_tool, str, "from", context)
    to_tool = _require_key(edge_data, "to", context)
    _require_type(to_tool, str, "to", context)

    if from_tool not in tool_names:
        raise CompositionError(
            f"{context}: 'from' references unknown tool '{from_tool}'"
        )
    if to_tool not in tool_names:
        raise CompositionError(
            f"{context}: 'to' references unknown tool '{to_tool}'"
        )

    dims_data = _require_key(edge_data, "dimensions", context)
    _require_type(dims_data, list, "dimensions", context)
    if not dims_data:
        raise CompositionError(f"{context} must have at least one dimension")

    dims: list[SemanticDimension] = []
    for j, d in enumerate(dims_data):
        dim_ctx = f"{context}.dimensions[{j}]"
        _require_type(d, dict, f"dimensions[{j}]", context)
        name = _require_key(d, "name", dim_ctx)
        _require_type(name, str, "name", dim_ctx)
        dims.append(
            SemanticDimension(
                name=name,
                from_field=d.get("from_field"),
                to_field=d.get("to_field"),
            )
        )

    return Edge(from_tool=from_tool, to_tool=to_tool, dimensions=tuple(dims))


def load_composition(path: Path) -> Composition:
    """Load and validate a YAML composition file.

    Raises CompositionError with actionable messages on validation failure.
    """
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise CompositionError(f"Invalid YAML in {path}: {e}") from e

    if not isinstance(data, dict):
        raise CompositionError(f"{path}: expected a YAML mapping at top level")

    name = data.get("name", path.stem)
    _require_type(name, str, "name", str(path))

    tools_data = _require_key(data, "tools", str(path))
    _require_type(tools_data, dict, "tools", str(path))
    if not tools_data:
        raise CompositionError(f"{path}: 'tools' must contain at least one tool")

    tools = [_validate_tool(tname, tspec) for tname, tspec in tools_data.items()]
    tool_names = {t.name for t in tools}

    edges_data = _require_key(data, "edges", str(path))
    _require_type(edges_data, list, "edges", str(path))
    edges = [_validate_edge(e, i, tool_names) for i, e in enumerate(edges_data)]

    return Composition(name=name, tools=tools, edges=edges)
