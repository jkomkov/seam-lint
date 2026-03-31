"""seam-lint: Coherence fee diagnostic for agent tool compositions."""

__version__ = "0.6.0"

from seam_lint.model import (
    BlindSpot,
    Bridge,
    BridgePatch,
    Composition,
    DEFAULT_POLICY_PROFILE,
    Diagnostic,
    Disposition,
    Edge,
    PolicyProfile,
    SemanticDimension,
    ToolSpec,
    WitnessError,
    WitnessErrorCode,
    WitnessReceipt,
)
from seam_lint.diagnostic import diagnose
from seam_lint.parser import load_composition
from seam_lint.guard import SeamGuard, SeamCheckError
from seam_lint.witness import witness
from seam_lint.infer.classifier import FieldInfo, InferredDimension

__all__ = [
    "__version__",
    "BlindSpot",
    "Bridge",
    "BridgePatch",
    "Composition",
    "DEFAULT_POLICY_PROFILE",
    "Diagnostic",
    "Disposition",
    "Edge",
    "FieldInfo",
    "InferredDimension",
    "PolicyProfile",
    "SeamCheckError",
    "SeamGuard",
    "SemanticDimension",
    "ToolSpec",
    "WitnessError",
    "WitnessErrorCode",
    "WitnessReceipt",
    "diagnose",
    "load_composition",
    "witness",
]
