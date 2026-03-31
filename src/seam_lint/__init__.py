"""seam-lint: Coherence fee diagnostic for agent tool compositions."""

__version__ = "0.5.0"

from seam_lint.model import (
    BlindSpot,
    Bridge,
    Composition,
    Diagnostic,
    Edge,
    SemanticDimension,
    ToolSpec,
)
from seam_lint.diagnostic import diagnose
from seam_lint.parser import load_composition
from seam_lint.guard import SeamGuard, SeamCheckError
from seam_lint.infer.classifier import FieldInfo, InferredDimension

__all__ = [
    "__version__",
    "BlindSpot",
    "Bridge",
    "Composition",
    "Diagnostic",
    "Edge",
    "FieldInfo",
    "InferredDimension",
    "SeamCheckError",
    "SeamGuard",
    "SemanticDimension",
    "ToolSpec",
    "diagnose",
    "load_composition",
]
