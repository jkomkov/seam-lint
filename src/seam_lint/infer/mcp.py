"""Infer a proto-composition YAML from an MCP manifest JSON.

Reads the `tools` array from an MCP server's `list_tools` response and
produces a YAML composition with inferred semantic dimensions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from seam_lint.infer.classifier import InferredDimension, classify_fields


def _extract_fields_from_schema(schema: dict[str, Any]) -> list[str]:
    """Extract field names from a JSON Schema object (properties)."""
    if not isinstance(schema, dict):
        return []
    props = schema.get("properties", {})
    if isinstance(props, dict):
        return list(props.keys())
    return []


def _extract_tool_fields(tool: dict[str, Any]) -> list[str]:
    """Extract all field names from a tool's input/output schemas."""
    fields: list[str] = []
    input_schema = tool.get("inputSchema", {})
    fields.extend(_extract_fields_from_schema(input_schema))
    output_schema = tool.get("outputSchema", {})
    fields.extend(_extract_fields_from_schema(output_schema))
    return list(dict.fromkeys(fields))  # deduplicate preserving order


def _find_shared_dimensions(
    tools_dims: dict[str, list[InferredDimension]],
) -> list[dict[str, Any]]:
    """Find edges: tools sharing inferred dimensions of the same type."""
    dim_to_tools: dict[str, list[tuple[str, str]]] = {}
    for tool_name, dims in tools_dims.items():
        for d in dims:
            dim_to_tools.setdefault(d.dimension, []).append(
                (tool_name, d.field_name)
            )

    edges: list[dict[str, Any]] = []
    tool_names = list(tools_dims.keys())
    for i, t1 in enumerate(tool_names):
        for t2 in tool_names[i + 1:]:
            shared: list[dict[str, str]] = []
            dims_1 = {d.dimension: d for d in tools_dims[t1]}
            dims_2 = {d.dimension: d for d in tools_dims[t2]}
            for dim_name in dims_1:
                if dim_name in dims_2:
                    shared.append({
                        "name": f"{dim_name}_match",
                        "from_field": dims_1[dim_name].field_name,
                        "to_field": dims_2[dim_name].field_name,
                    })
            if shared:
                edges.append({
                    "from": t1,
                    "to": t2,
                    "dimensions": shared,
                })
    return edges


def infer_from_manifest(manifest_path: Path) -> str:
    """Read an MCP manifest JSON and produce a proto-composition YAML."""
    data = json.loads(manifest_path.read_text())

    tools_list: list[dict[str, Any]]
    if isinstance(data, list):
        tools_list = data
    elif isinstance(data, dict) and "tools" in data:
        tools_list = data["tools"]
    else:
        raise ValueError(
            f"Expected a JSON object with a 'tools' array or a plain array "
            f"of tool objects in {manifest_path}"
        )

    composition: dict[str, Any] = {
        "name": f"inferred-from-{manifest_path.stem}",
        "tools": {},
        "edges": [],
    }

    tools_dims: dict[str, list[InferredDimension]] = {}

    for tool in tools_list:
        name = tool.get("name", "unknown_tool")
        safe_name = name.replace("-", "_").replace(" ", "_")
        fields = _extract_tool_fields(tool)
        inferred = classify_fields(fields)

        inferred_field_names = {d.field_name for d in inferred}
        observable = [f for f in fields if f not in inferred_field_names]

        composition["tools"][safe_name] = {
            "internal_state": fields if fields else ["_placeholder"],
            "observable_schema": observable if observable else fields[:1] if fields else ["_placeholder"],
        }
        tools_dims[safe_name] = inferred

    composition["edges"] = _find_shared_dimensions(tools_dims)

    lines: list[str] = []
    lines.append(f"# Proto-composition inferred from {manifest_path.name}")
    lines.append("# REVIEW all fields and edges before running seam-lint diagnose")
    lines.append("")
    lines.append(yaml.dump(composition, default_flow_style=False, sort_keys=False))

    for tool_name, dims in tools_dims.items():
        if dims:
            lines.append(f"# REVIEW: {tool_name} inferred dimensions:")
            for d in dims:
                lines.append(
                    f"#   {d.field_name} -> {d.dimension} "
                    f"(confidence: {d.confidence})"
                )
            lines.append("")

    return "\n".join(lines)
