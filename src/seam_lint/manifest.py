"""Seam Manifest operations: generate, validate, load taxonomy."""

from __future__ import annotations

import importlib.resources
import json
from pathlib import Path
from typing import Any

import yaml

from seam_lint.infer.classifier import classify_fields
from seam_lint.infer.mcp import _extract_tool_fields


def load_taxonomy() -> dict[str, Any]:
    """Load the built-in convention taxonomy."""
    pkg = importlib.resources.files("seam_lint")
    taxonomy_file = pkg / "taxonomy.yaml"
    return yaml.safe_load(taxonomy_file.read_text(encoding="utf-8"))


def validate_manifest(path: Path) -> list[str]:
    """Validate a manifest YAML against the spec.  Returns a list of issues (empty = valid)."""
    issues: list[str] = []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        return [f"YAML parse error: {e}"]

    if not isinstance(data, dict):
        return ["Manifest must be a YAML mapping"]

    if data.get("seam_manifest") != "0.1":
        issues.append(
            f"seam_manifest must be '0.1', got '{data.get('seam_manifest')}'"
        )

    tool = data.get("tool")
    if not isinstance(tool, dict):
        issues.append("Missing or invalid 'tool' section")
    elif not tool.get("name"):
        issues.append("tool.name is required and must be non-empty")

    conventions = data.get("conventions")
    if not isinstance(conventions, dict):
        issues.append("Missing or invalid 'conventions' section")
    else:
        taxonomy = load_taxonomy()
        known_dims = set(taxonomy.get("dimensions", {}).keys())

        for dim_name, decl in conventions.items():
            if not isinstance(decl, dict):
                issues.append(f"Convention '{dim_name}' must be a mapping")
                continue

            confidence = decl.get("confidence")
            if confidence not in ("declared", "inferred", "unknown"):
                issues.append(
                    f"Convention '{dim_name}': confidence must be "
                    f"'declared', 'inferred', or 'unknown', got '{confidence}'"
                )

            value = decl.get("value")
            if value is not None and (not isinstance(value, str) or not value):
                issues.append(
                    f"Convention '{dim_name}': value must be a non-empty string"
                )

            if dim_name not in known_dims:
                issues.append(
                    f"Info: '{dim_name}' is not in the standard taxonomy "
                    f"(custom dimensions are allowed)"
                )

    return issues


def generate_manifest_from_tools(
    tools_list: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Generate manifest dicts from a list of MCP tool definitions."""
    manifests: list[dict[str, Any]] = []
    for tool in tools_list:
        name = tool.get("name", "unknown_tool")
        fields = _extract_tool_fields(tool)
        inferred = classify_fields(fields)

        # Map classifier's internal grades to manifest spec vocabulary
        _CONFIDENCE_MAP = {"high": "inferred", "medium": "inferred"}
        conventions: dict[str, Any] = {}
        for dim in inferred:
            conventions[dim.dimension] = {
                "confidence": _CONFIDENCE_MAP.get(dim.confidence, dim.confidence),
            }

        manifest: dict[str, Any] = {
            "seam_manifest": "0.1",
            "tool": {
                "name": name,
            },
            "conventions": conventions,
        }
        desc = tool.get("description")
        if desc:
            manifest["tool"]["description"] = desc

        manifests.append(manifest)
    return manifests


def generate_manifest_from_json(path: Path) -> list[dict[str, Any]]:
    """Generate manifest dicts from an MCP manifest JSON file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        tools_list = data
    elif isinstance(data, dict) and "tools" in data:
        tools_list = data["tools"]
    else:
        raise ValueError(f"Expected 'tools' array or plain array in {path}")
    return generate_manifest_from_tools(tools_list)
