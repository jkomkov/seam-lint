"""Heuristic dimension classifier.

Maps field names to semantic convention dimensions using pattern matching.
No LLM, no API key, deterministic.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

DIMENSION_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("date_format", re.compile(
        r"(^|_)(time|date|timestamp|datetime|created_at|updated_at|"
        r"expires?_at|deadline|scheduled|start_time|end_time|"
        r"birth_?date|due_date)($|_)", re.IGNORECASE
    )),
    ("rate_scale", re.compile(
        r"(^|_)(rate|percent|percentage|ratio|probability|"
        r"confidence|likelihood|fraction|proportion|"
        r"interest_rate|tax_rate|growth_rate)($|_)", re.IGNORECASE
    )),
    ("amount_unit", re.compile(
        r"(^|_)(amount|price|cost|fee|total|subtotal|balance|"
        r"salary|revenue|profit|budget|payment|charge|"
        r"discount|tax|tip|wage)($|_|s$)", re.IGNORECASE
    )),
    ("score_range", re.compile(
        r"(^|_)(score|rating|priority|rank|grade|level|"
        r"quality|severity|weight|importance)($|_)", re.IGNORECASE
    )),
    ("id_offset", re.compile(
        r"(^|_)(id|index|offset|position|ordinal|sequence|"
        r"serial|number|num|count|page)($|_)", re.IGNORECASE
    )),
    ("precision", re.compile(
        r"(^|_)(precision|decimals|decimal_places|dp|"
        r"significant_digits|rounding|accuracy)($|_)", re.IGNORECASE
    )),
    ("encoding", re.compile(
        r"(^|_)(encoding|charset|character_set|locale|"
        r"text_encoding|content_encoding)($|_)", re.IGNORECASE
    )),
    ("timezone", re.compile(
        r"(^|_)(tz|timezone|time_?zone|utc_offset)($|_)", re.IGNORECASE
    )),
    ("null_handling", re.compile(
        r"(^|_)(null_handling|null_strategy|missing_value|"
        r"na_value|nan_handling|default_missing)($|_)", re.IGNORECASE
    )),
    ("line_ending", re.compile(
        r"(^|_)(line_ending|newline|eol|crlf|lf_mode)($|_)", re.IGNORECASE
    )),
]


@dataclass(frozen=True)
class InferredDimension:
    field_name: str
    dimension: str
    confidence: str  # "high", "medium"


def classify_field(name: str) -> InferredDimension | None:
    """Classify a single field name into a semantic dimension, or None."""
    for dim_name, pattern in DIMENSION_PATTERNS:
        if pattern.search(name):
            return InferredDimension(
                field_name=name,
                dimension=dim_name,
                confidence="high" if "_" in name else "medium",
            )
    return None


def classify_fields(fields: list[str]) -> list[InferredDimension]:
    """Classify a list of field names, returning only those that match."""
    results = []
    for f in fields:
        inferred = classify_field(f)
        if inferred is not None:
            results.append(inferred)
    return results
