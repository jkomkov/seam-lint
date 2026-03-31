"""Witness kernel: deterministic measurement → receipt pipeline.

Layer A (measurement): Diagnostic — already exists in diagnostic.py
Layer B (binding):     WitnessReceipt — produced here
Layer C (judgment):    Disposition — resolved here from policy

The kernel is intentionally small and stateless. Given a Diagnostic
and a composition hash, it produces a WitnessReceipt with content-
addressable hashes. No network, no side effects, no policy opinions
beyond the disposition thresholds.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from seam_lint import __version__
from seam_lint.model import (
    BridgePatch,
    Diagnostic,
    Disposition,
    WitnessReceipt,
)

RECEIPT_VERSION = "0.1.0"
DEFAULT_POLICY = "witness.default.v1"


def _resolve_disposition(
    diag: Diagnostic,
    policy_profile: str = DEFAULT_POLICY,
) -> Disposition:
    """Map measurement to judgment under a named policy.

    The policy_profile parameter names which rule set produced this
    disposition. Currently only ``witness.default.v1`` is implemented.
    The parameter exists so that receipts record which policy was applied,
    preventing the kernel from becoming a stealth judge.
    """
    # witness.default.v1: the only built-in profile
    if diag.n_unbridged > 0 and diag.coherence_fee > 0:
        return Disposition.REFUSE_PENDING_DISCLOSURE
    if diag.n_unbridged > 0:
        return Disposition.PROCEED_WITH_BRIDGE
    if diag.coherence_fee > 0:
        return Disposition.PROCEED_WITH_RECEIPT
    return Disposition.PROCEED


def _diagnostic_to_patches(diag: Diagnostic) -> tuple[BridgePatch, ...]:
    """Convert Bridge recommendations to machine-actionable BridgePatch objects."""
    patches: list[BridgePatch] = []
    for br in diag.bridges:
        for tool in br.add_to:
            patches.append(
                BridgePatch(
                    target_tool=tool,
                    dimension=br.eliminates,
                    field=br.field,
                    action="expose",
                    eliminates_blind_spot=br.eliminates,
                    expected_fee_delta=0,  # per-patch delta requires re-diagnosis
                )
            )
    return tuple(patches)


def witness(
    diag: Diagnostic,
    composition_hash: str,
    unknown_dimensions: int = 0,
    policy_profile: str = DEFAULT_POLICY,
) -> WitnessReceipt:
    """Produce a WitnessReceipt from a Diagnostic.

    This is the core witness function. It is deterministic given the
    same inputs (except timestamp). Everything an agent needs to decide
    whether to proceed is in the receipt.

    ``policy_profile`` names the disposition rule set. Recorded in the
    receipt so consumers know which judgment logic was applied.
    """
    patches = _diagnostic_to_patches(diag)
    disposition = _resolve_disposition(diag, policy_profile)

    return WitnessReceipt(
        receipt_version=RECEIPT_VERSION,
        kernel_version=__version__,
        composition_hash=composition_hash,
        diagnostic_hash=diag.content_hash(),
        policy_profile=policy_profile,
        fee=diag.coherence_fee,
        blind_spots_count=len(diag.blind_spots),
        bridges_required=diag.n_unbridged,
        unknown_dimensions=unknown_dimensions,
        disposition=disposition,
        timestamp=datetime.now(timezone.utc).isoformat(),
        patches=patches,
    )


def composition_hash(yaml_bytes: bytes) -> str:
    """SHA-256 of raw composition YAML bytes."""
    return hashlib.sha256(yaml_bytes).hexdigest()
