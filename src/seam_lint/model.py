"""Data model for compositions, diagnostics, and recommendations."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ToolSpec:
    name: str
    internal_state: tuple[str, ...]
    observable_schema: tuple[str, ...]

    @property
    def projected_away(self) -> tuple[str, ...]:
        return tuple(d for d in self.internal_state
                     if d not in self.observable_schema)


@dataclass(frozen=True)
class SemanticDimension:
    name: str
    from_field: str | None = None
    to_field: str | None = None


@dataclass(frozen=True)
class Edge:
    from_tool: str
    to_tool: str
    dimensions: tuple[SemanticDimension, ...]


@dataclass(frozen=True)
class Composition:
    name: str
    tools: list[ToolSpec]
    edges: list[Edge]


@dataclass(frozen=True)
class BlindSpot:
    dimension: str
    edge: str
    from_field: str
    to_field: str
    from_hidden: bool
    to_hidden: bool


@dataclass(frozen=True)
class Bridge:
    field: str
    add_to: list[str] = field(default_factory=list)
    eliminates: str = ""


@dataclass
class Diagnostic:
    name: str
    n_tools: int
    n_edges: int
    betti_1: int
    dim_c0_obs: int
    dim_c0_full: int
    dim_c1: int
    rank_obs: int
    rank_full: int
    h1_obs: int
    h1_full: int
    coherence_fee: int
    blind_spots: list[BlindSpot]
    bridges: list[Bridge]
    h1_after_bridge: int
    n_unbridged: int = 0
