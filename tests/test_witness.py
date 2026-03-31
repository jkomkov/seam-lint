"""Tests for witness kernel: constitutional objects, receipts, disposition."""

from __future__ import annotations

import json

import pytest

from seam_lint.model import (
    BlindSpot,
    Bridge,
    BridgePatch,
    Diagnostic,
    Disposition,
    WitnessReceipt,
)
from seam_lint.witness import (
    RECEIPT_VERSION,
    _diagnostic_to_patches,
    _resolve_disposition,
    composition_hash,
    witness,
)


# ── Fixtures ─────────────────────────────────────────────────────────


def _make_diagnostic(
    fee: int = 0,
    blind_spots: list[BlindSpot] | None = None,
    bridges: list[Bridge] | None = None,
    n_unbridged: int = 0,
) -> Diagnostic:
    return Diagnostic(
        name="test-composition",
        n_tools=3,
        n_edges=2,
        betti_1=0,
        dim_c0_obs=6,
        dim_c0_full=8,
        dim_c1=4,
        rank_obs=4,
        rank_full=4,
        h1_obs=0,
        h1_full=0,
        coherence_fee=fee,
        blind_spots=blind_spots or [],
        bridges=bridges or [],
        h1_after_bridge=0,
        n_unbridged=n_unbridged,
    )


SAMPLE_BLIND_SPOT = BlindSpot(
    dimension="amount_unit",
    edge="parser → settlement",
    from_field="amount_scale",
    to_field="amount_unit",
    from_hidden=True,
    to_hidden=False,
)

SAMPLE_BRIDGE = Bridge(
    field="amount_scale",
    add_to=["parser"],
    eliminates="amount_unit",
)


# ── Disposition ──────────────────────────────────────────────────────


class TestDisposition:
    def test_proceed_when_clean(self):
        diag = _make_diagnostic(fee=0, n_unbridged=0)
        assert _resolve_disposition(diag) == Disposition.PROCEED

    def test_proceed_with_receipt_when_fee_only(self):
        diag = _make_diagnostic(fee=2, n_unbridged=0)
        assert _resolve_disposition(diag) == Disposition.PROCEED_WITH_RECEIPT

    def test_proceed_with_bridge_when_unbridged_no_fee(self):
        diag = _make_diagnostic(
            fee=0,
            blind_spots=[SAMPLE_BLIND_SPOT],
            bridges=[SAMPLE_BRIDGE],
            n_unbridged=1,
        )
        assert _resolve_disposition(diag) == Disposition.PROCEED_WITH_BRIDGE

    def test_refuse_when_both_unbridged_and_fee(self):
        diag = _make_diagnostic(
            fee=1,
            blind_spots=[SAMPLE_BLIND_SPOT],
            bridges=[SAMPLE_BRIDGE],
            n_unbridged=1,
        )
        assert _resolve_disposition(diag) == Disposition.REFUSE_PENDING_DISCLOSURE

    def test_enum_values(self):
        assert Disposition.PROCEED.value == "proceed"
        assert Disposition.REFUSE_PENDING_HUMAN_REVIEW.value == "refuse_pending_human_review"


# ── BridgePatch ──────────────────────────────────────────────────────


class TestBridgePatch:
    def test_to_seam_patch(self):
        patch = BridgePatch(
            target_tool="parser",
            dimension="amount_unit",
            field="amount_scale",
            action="expose",
            eliminates_blind_spot="amount_unit",
            expected_fee_delta=0,
        )
        result = patch.to_seam_patch()
        assert result["seam_patch_version"] == "0.1.0"
        assert result["action"] == "expose"
        assert result["target_tool"] == "parser"
        assert result["field"] == "amount_scale"
        assert result["path"] == "/observable_schema/amount_scale"
        assert result["dimension"] == "amount_unit"

    def test_frozen(self):
        patch = BridgePatch(
            target_tool="a", dimension="b", field="c",
            action="expose", eliminates_blind_spot="d",
            expected_fee_delta=0,
        )
        with pytest.raises(AttributeError):
            patch.target_tool = "x"  # type: ignore


# ── WitnessReceipt ───────────────────────────────────────────────────


class TestWitnessReceipt:
    def test_receipt_hash_deterministic(self):
        r1 = WitnessReceipt(
            receipt_version="0.1.0",
            kernel_version="0.5.0",
            composition_hash="abc123",
            diagnostic_hash="def456",
            policy_profile="witness.default.v1",
            fee=0,
            blind_spots_count=0,
            bridges_required=0,
            unknown_dimensions=0,
            disposition=Disposition.PROCEED,
            timestamp="2026-03-30T00:00:00+00:00",
        )
        r2 = WitnessReceipt(
            receipt_version="0.1.0",
            kernel_version="0.5.0",
            composition_hash="abc123",
            diagnostic_hash="def456",
            policy_profile="witness.default.v1",
            fee=0,
            blind_spots_count=0,
            bridges_required=0,
            unknown_dimensions=0,
            disposition=Disposition.PROCEED,
            timestamp="2026-03-30T00:00:00+00:00",
        )
        assert r1.receipt_hash == r2.receipt_hash

    def test_receipt_hash_changes_with_content(self):
        base = WitnessReceipt(
            receipt_version="0.1.0",
            kernel_version="0.5.0",
            composition_hash="abc123",
            diagnostic_hash="def456",
            policy_profile="witness.default.v1",
            fee=0,
            blind_spots_count=0,
            bridges_required=0,
            unknown_dimensions=0,
            disposition=Disposition.PROCEED,
            timestamp="2026-03-30T00:00:00+00:00",
        )
        modified = WitnessReceipt(
            receipt_version="0.1.0",
            kernel_version="0.5.0",
            composition_hash="abc123",
            diagnostic_hash="def456",
            policy_profile="witness.default.v1",
            fee=1,  # different fee
            blind_spots_count=0,
            bridges_required=0,
            unknown_dimensions=0,
            disposition=Disposition.PROCEED,
            timestamp="2026-03-30T00:00:00+00:00",
        )
        assert base.receipt_hash != modified.receipt_hash

    def test_anchor_ref_excluded_from_hash(self):
        r1 = WitnessReceipt(
            receipt_version="0.1.0",
            kernel_version="0.5.0",
            composition_hash="abc",
            diagnostic_hash="def",
            policy_profile="witness.default.v1",
            fee=0,
            blind_spots_count=0,
            bridges_required=0,
            unknown_dimensions=0,
            disposition=Disposition.PROCEED,
            timestamp="2026-03-30T00:00:00+00:00",
            anchor_ref=None,
        )
        r2 = WitnessReceipt(
            receipt_version="0.1.0",
            kernel_version="0.5.0",
            composition_hash="abc",
            diagnostic_hash="def",
            policy_profile="witness.default.v1",
            fee=0,
            blind_spots_count=0,
            bridges_required=0,
            unknown_dimensions=0,
            disposition=Disposition.PROCEED,
            timestamp="2026-03-30T00:00:00+00:00",
            anchor_ref="ots:abc123",
        )
        assert r1.receipt_hash == r2.receipt_hash

    def test_to_dict_includes_all_fields(self):
        receipt = WitnessReceipt(
            receipt_version="0.1.0",
            kernel_version="0.5.0",
            composition_hash="abc",
            diagnostic_hash="def",
            policy_profile="witness.default.v1",
            fee=0,
            blind_spots_count=0,
            bridges_required=0,
            unknown_dimensions=0,
            disposition=Disposition.PROCEED,
            timestamp="2026-03-30T00:00:00+00:00",
        )
        d = receipt.to_dict()
        assert d["receipt_version"] == "0.1.0"
        assert d["disposition"] == "proceed"
        assert "receipt_hash" in d
        assert d["patches"] == []

    def test_to_dict_is_json_serializable(self):
        receipt = WitnessReceipt(
            receipt_version="0.1.0",
            kernel_version="0.5.0",
            composition_hash="abc",
            diagnostic_hash="def",
            policy_profile="witness.default.v1",
            fee=0,
            blind_spots_count=0,
            bridges_required=0,
            unknown_dimensions=0,
            disposition=Disposition.PROCEED,
            timestamp="2026-03-30T00:00:00+00:00",
        )
        # Must not raise
        json.dumps(receipt.to_dict())


# ── Diagnostic.content_hash ──────────────────────────────────────────


class TestDiagnosticContentHash:
    def test_deterministic(self):
        d1 = _make_diagnostic(fee=0)
        d2 = _make_diagnostic(fee=0)
        assert d1.content_hash() == d2.content_hash()

    def test_changes_with_fee(self):
        d1 = _make_diagnostic(fee=0)
        d2 = _make_diagnostic(fee=1)
        assert d1.content_hash() != d2.content_hash()

    def test_includes_blind_spots(self):
        d1 = _make_diagnostic(fee=0)
        d2 = _make_diagnostic(fee=0, blind_spots=[SAMPLE_BLIND_SPOT])
        assert d1.content_hash() != d2.content_hash()


# ── witness() integration ────────────────────────────────────────────


class TestWitnessFunction:
    def test_clean_composition(self):
        diag = _make_diagnostic(fee=0)
        receipt = witness(diag, "comp_hash_abc")
        assert receipt.disposition == Disposition.PROCEED
        assert receipt.fee == 0
        assert receipt.blind_spots_count == 0
        assert receipt.patches == ()
        assert receipt.composition_hash == "comp_hash_abc"
        assert receipt.receipt_version == RECEIPT_VERSION

    def test_composition_with_blind_spots(self):
        diag = _make_diagnostic(
            fee=0,
            blind_spots=[SAMPLE_BLIND_SPOT],
            bridges=[SAMPLE_BRIDGE],
            n_unbridged=1,
        )
        receipt = witness(diag, "hash_xyz")
        assert receipt.disposition == Disposition.PROCEED_WITH_BRIDGE
        assert receipt.blind_spots_count == 1
        assert receipt.bridges_required == 1
        assert len(receipt.patches) == 1
        assert receipt.patches[0].target_tool == "parser"
        assert receipt.patches[0].field == "amount_scale"

    def test_receipt_hash_is_sha256(self):
        diag = _make_diagnostic(fee=0)
        receipt = witness(diag, "abc")
        assert len(receipt.receipt_hash) == 64  # SHA-256 hex

    def test_diagnostic_to_patches(self):
        diag = _make_diagnostic(
            bridges=[
                Bridge(field="f1", add_to=["tool_a", "tool_b"], eliminates="dim1"),
                Bridge(field="f2", add_to=["tool_c"], eliminates="dim2"),
            ]
        )
        patches = _diagnostic_to_patches(diag)
        assert len(patches) == 3  # 2 from first bridge + 1 from second
        assert patches[0].target_tool == "tool_a"
        assert patches[1].target_tool == "tool_b"
        assert patches[2].target_tool == "tool_c"


# ── composition_hash ─────────────────────────────────────────────────


class TestCompositionHash:
    def test_deterministic(self):
        data = b"name: test\ntools: {}"
        assert composition_hash(data) == composition_hash(data)

    def test_different_content(self):
        assert composition_hash(b"a") != composition_hash(b"b")

    def test_is_sha256(self):
        assert len(composition_hash(b"test")) == 64
