"""
Tests for the NSVB estimators against the four worked GTR examples.

Every NSVB step shown in the GTR examples gets its own ``Test...`` class
with two tests:

  * a parametrized scalar test that calls the estimator with Python floats /
    ints / strs once per tree (skipped when that example doesn't print the
    quantity), and
  * a vectorized test that passes parallel numpy arrays for all 4 trees in
    one call and asserts only against the indices the GTR exercises.

Both tests use ``np.testing.assert_allclose(rtol=1e-6)`` -- tight enough to
catch real bugs, loose enough to tolerate the GTR's 12-decimal rounding and
ordinary floating-point reassociation.

Tests targeting estimators that are still stubs (``NotImplementedError``)
fail today and serve as the working spec for the rest of the
implementation. Once a stub is replaced with a real implementation, the
test should pass without modification.
"""

import numpy as np
import pytest

from nsvb.estimators import (
    # implemented
    total_aboveground_biomass,
    total_bark_wood_volume,
    total_branch_weight,
    total_foliage_dry_weight,
    total_inside_bark_wood_volume,
    total_outside_bark_volume,
    total_stem_bark_weight,
    total_stem_wood_dry_weight,
    # stubs -- step 4
    merchantable_height,
    sawlog_height,
    # stubs -- step 5
    broken_top_volume_ratio,
    merchantable_volume_ratio,
    sawlog_volume_ratio,
    stump_volume_ratio,
    # stubs -- step 6 (gross)
    merchantable_bark_volume,
    merchantable_inside_bark_volume,
    merchantable_outside_bark_volume,
    missing_bark_volume,
    missing_inside_bark_volume,
    missing_outside_bark_volume,
    sawlog_bark_volume,
    sawlog_inside_bark_volume,
    sawlog_outside_bark_volume,
    stump_bark_volume,
    stump_inside_bark_volume,
    stump_outside_bark_volume,
    top_bark_volume,
    top_inside_bark_volume,
    top_outside_bark_volume,
    # stubs -- step 6 (sound)
    merchantable_bark_volume_sound,
    merchantable_inside_bark_volume_sound,
    merchantable_outside_bark_volume_sound,
    stump_inside_bark_volume_sound,
    stump_outside_bark_volume_sound,
    top_bark_volume_sound,
    top_inside_bark_volume_sound,
    top_outside_bark_volume_sound,
    total_bark_volume_sound,
    total_inside_bark_wood_volume_sound,
    total_outside_bark_volume_sound,
    # stubs -- step 7-9 reduced
    total_stem_wood_dry_weight_reduced,
    total_stem_bark_weight_reduced,
    total_stem_outside_bark_weight_reduced,
    branch_remainder,
    crown_ratio_at_h,
    foliage_remainder,
    total_branch_weight_reduced,
    # stubs -- step 11-12 harmonization
    agb_component_reduced,
    agb_difference,
    agb_predicted_reduced,
    agb_reduce_factor,
    harmonized_bark,
    harmonized_branch,
    harmonized_wood,
    # stubs -- step 13 adjusted densities
    adjusted_bark_density,
    adjusted_wood_density,
    # stubs -- step 14 merchantable / stump weights
    merchantable_bark_weight,
    merchantable_outside_bark_weight,
    merchantable_wood_weight,
    stump_bark_weight,
    stump_outside_bark_weight,
    stump_wood_weight,
    # stubs -- step 15 reduced
    total_foliage_dry_weight_reduced,
    # stubs -- step 16-17
    carbon_content,
    drybio_top,
)

from tests.fixtures import CRH, INPUTS, TREES, expected_array, tree_crh

RTOL = 1e-6
TREE_IDS = [f"tree{t.id}" for t in TREES]

# Some quantities cannot be reproduced from the published supplementary CSV
# to the same precision as the GTR text examples, for two documented
# reasons:
#   * Ten S2a/S6a/S7a rows are stored in Excel scientific notation truncating
#     ``a`` to 3 sig figs (e.g. ``3.19E-05`` vs the GTR text's
#     ``0.000031886237``). For S2a SPCD=202/DIV=240 this causes ~4e-4
#     relative drift in bark / outside-bark quantities for Tree 1.
#   * The GTR's iterative h_m / h_s values were under-converged by the
#     publication (residual ~3e-6 in eqn 7 at the printed values); our
#     brentq finds the true root, so we differ by ~1e-6 relative -- which
#     then propagates into the small ``v_top_*`` subcomponents.
# Both are publication-precision limits, not bugs. Affected test classes
# override ``rtol`` below with a comment citing the cause.
RTOL_PUB_BARK = 1e-3   # Tree 1 S2a coefficient truncation propagation
RTOL_PUB_ITER = 5e-6   # h_m/h_s under-convergence propagation
# v_top_*_sound for broken-top trees: the residual (R_b - R_m) is tiny
# (e.g. Tree 4: ~0.003), so the h_m drift amplifies into ~2e-5 relative.
RTOL_PUB_SOUND = 5e-5


def _check_scalar(tree, field_name, fn, *args, rtol=RTOL):
    """Run ``fn(*args)`` as scalars; assert against ``tree.expected.<field>``."""
    expected = getattr(tree.expected, field_name)
    if expected is None:
        pytest.skip(f"Tree {tree.id} does not exercise {field_name}")
    result = fn(*args)
    np.testing.assert_allclose(result, expected, rtol=rtol)


def _check_vector(field_name, fn, *args, rtol=RTOL):
    """Run ``fn(*args)`` on full input arrays; assert against masked expected."""
    result = fn(*args)
    expected, mask = expected_array(field_name)
    assert isinstance(result, np.ndarray), "vectorized call must return ndarray"
    assert result.shape == expected.shape, (
        f"shape mismatch: result={result.shape} expected={expected.shape}"
    )
    np.testing.assert_allclose(result[mask], expected[mask], rtol=rtol)


# Shortcut bundles -- the input combinations that recur across tests.
_TREE_DIA_HT_DIV = lambda t: (t.spcd, t.dia, t.ht, t.division)
_INPUT_DIA_HT_DIV = (INPUTS["spcd"], INPUTS["dia"], INPUTS["ht"], INPUTS["division"])
_TREE_FULL = lambda t: (
    t.spcd, t.dia, t.ht, t.division, t.cull, t.ah, t.decaycd, t.cr, t.province or "",
)
_INPUT_FULL = (
    INPUTS["spcd"], INPUTS["dia"], INPUTS["ht"], INPUTS["division"],
    INPUTS["cull"], INPUTS["ah"], INPUTS["decaycd"], INPUTS["cr"], INPUTS["province"],
)


# =============================================================================
# Step 1 -- total inside-bark wood volume (S1)
# =============================================================================
class TestTotalInsideBarkWoodVolume:
    field = "v_tot_ib_gross"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, total_inside_bark_wood_volume, *_TREE_DIA_HT_DIV(tree))

    def test_vector(self):
        _check_vector(self.field, total_inside_bark_wood_volume, *_INPUT_DIA_HT_DIV)


# =============================================================================
# Step 2 -- total bark volume (S2)
# =============================================================================
class TestTotalBarkWoodVolume:
    field = "v_tot_bk_gross"
    # Tree 1 (SPCD 202 / DIV 240): S2a stores a=3.19E-05 (3 sig figs); GTR
    # text used a=0.000031886237. Worst-case ~4e-4 relative.
    rtol = RTOL_PUB_BARK

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, total_bark_wood_volume, *_TREE_DIA_HT_DIV(tree), rtol=self.rtol)

    def test_vector(self):
        _check_vector(self.field, total_bark_wood_volume, *_INPUT_DIA_HT_DIV, rtol=self.rtol)


# =============================================================================
# Step 3 -- total outside-bark volume (S1 + S2)
# =============================================================================
class TestTotalOutsideBarkVolume:
    field = "v_tot_ob_gross"
    rtol = RTOL_PUB_BARK   # bark precision propagates via v_tot_ib + v_tot_bk

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, total_outside_bark_volume, *_TREE_DIA_HT_DIV(tree), rtol=self.rtol)

    def test_vector(self):
        _check_vector(self.field, total_outside_bark_volume, *_INPUT_DIA_HT_DIV, rtol=self.rtol)


# =============================================================================
# Step 4 -- merchantable & sawlog heights (S3 + S4, inverted iteratively)
# =============================================================================
class TestMerchantableHeight:
    field = "h_m"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, merchantable_height, *_TREE_DIA_HT_DIV(tree))

    def test_vector(self):
        _check_vector(self.field, merchantable_height, *_INPUT_DIA_HT_DIV)


class TestSawlogHeight:
    field = "h_s"
    # GTR's printed h_s values are under-converged iterates (residual ~3e-6
    # in eqn 7 at GTR's printed values); brentq finds the true root.
    rtol = RTOL_PUB_ITER

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, sawlog_height, *_TREE_DIA_HT_DIV(tree), rtol=self.rtol)

    def test_vector(self):
        _check_vector(self.field, sawlog_height, *_INPUT_DIA_HT_DIV, rtol=self.rtol)


# =============================================================================
# Step 5 -- stem-profile volume ratios (S5)
# =============================================================================
class TestStumpVolumeRatio:
    field = "r_1"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, stump_volume_ratio, *_TREE_DIA_HT_DIV(tree))

    def test_vector(self):
        _check_vector(self.field, stump_volume_ratio, *_INPUT_DIA_HT_DIV)


class TestMerchantableVolumeRatio:
    field = "r_m"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, merchantable_volume_ratio, *_TREE_DIA_HT_DIV(tree))

    def test_vector(self):
        _check_vector(self.field, merchantable_volume_ratio, *_INPUT_DIA_HT_DIV)


class TestSawlogVolumeRatio:
    field = "r_s"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, sawlog_volume_ratio, *_TREE_DIA_HT_DIV(tree))

    def test_vector(self):
        _check_vector(self.field, sawlog_volume_ratio, *_INPUT_DIA_HT_DIV)


class TestBrokenTopVolumeRatio:
    """R_b -- evaluated at AH for broken-top trees."""
    field = "r_b"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(
            tree, self.field, broken_top_volume_ratio,
            tree.spcd, tree.dia, tree.ht, tree.division, tree.ah,
        )

    def test_vector(self):
        _check_vector(
            self.field, broken_top_volume_ratio,
            INPUTS["spcd"], INPUTS["dia"], INPUTS["ht"], INPUTS["division"], INPUTS["ah"],
        )


# =============================================================================
# Step 6 -- subcomponent volumes (gross)
# =============================================================================
class TestMerchantableInsideBarkVolume:
    field = "v_mer_ib_gross"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, merchantable_inside_bark_volume, *_TREE_DIA_HT_DIV(tree))

    def test_vector(self):
        _check_vector(self.field, merchantable_inside_bark_volume, *_INPUT_DIA_HT_DIV)


class TestMerchantableBarkVolume:
    field = "v_mer_bk_gross"
    rtol = RTOL_PUB_BARK   # Tree 1 S2a precision propagates through v_tot_bk

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, merchantable_bark_volume, *_TREE_DIA_HT_DIV(tree), rtol=self.rtol)

    def test_vector(self):
        _check_vector(self.field, merchantable_bark_volume, *_INPUT_DIA_HT_DIV, rtol=self.rtol)


class TestMerchantableOutsideBarkVolume:
    field = "v_mer_ob_gross"
    rtol = RTOL_PUB_BARK   # Tree 1 S2a precision propagates through v_tot_ob

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, merchantable_outside_bark_volume, *_TREE_DIA_HT_DIV(tree), rtol=self.rtol)

    def test_vector(self):
        _check_vector(self.field, merchantable_outside_bark_volume, *_INPUT_DIA_HT_DIV, rtol=self.rtol)


class TestSawlogInsideBarkVolume:
    field = "v_saw_ib_gross"
    rtol = RTOL_PUB_ITER   # h_s drift propagates to small v_saw_ib (Tree 2)

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, sawlog_inside_bark_volume, *_TREE_DIA_HT_DIV(tree), rtol=self.rtol)

    def test_vector(self):
        _check_vector(self.field, sawlog_inside_bark_volume, *_INPUT_DIA_HT_DIV, rtol=self.rtol)


class TestSawlogBarkVolume:
    field = "v_saw_bk_gross"
    rtol = RTOL_PUB_BARK   # Tree 1 S2a propagation dominates

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, sawlog_bark_volume, *_TREE_DIA_HT_DIV(tree), rtol=self.rtol)

    def test_vector(self):
        _check_vector(self.field, sawlog_bark_volume, *_INPUT_DIA_HT_DIV, rtol=self.rtol)


class TestSawlogOutsideBarkVolume:
    field = "v_saw_ob_gross"
    rtol = RTOL_PUB_BARK   # Tree 1 S2a + Tree 2 h_s propagation

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, sawlog_outside_bark_volume, *_TREE_DIA_HT_DIV(tree), rtol=self.rtol)

    def test_vector(self):
        _check_vector(self.field, sawlog_outside_bark_volume, *_INPUT_DIA_HT_DIV, rtol=self.rtol)


class TestStumpInsideBarkVolume:
    field = "v_stump_ib_gross"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, stump_inside_bark_volume, *_TREE_DIA_HT_DIV(tree))

    def test_vector(self):
        _check_vector(self.field, stump_inside_bark_volume, *_INPUT_DIA_HT_DIV)


class TestStumpBarkVolume:
    field = "v_stump_bk_gross"
    rtol = RTOL_PUB_BARK   # Tree 1 S2a propagation

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, stump_bark_volume, *_TREE_DIA_HT_DIV(tree), rtol=self.rtol)

    def test_vector(self):
        _check_vector(self.field, stump_bark_volume, *_INPUT_DIA_HT_DIV, rtol=self.rtol)


class TestStumpOutsideBarkVolume:
    field = "v_stump_ob_gross"
    rtol = RTOL_PUB_BARK   # Tree 1 S2a propagation

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, stump_outside_bark_volume, *_TREE_DIA_HT_DIV(tree), rtol=self.rtol)

    def test_vector(self):
        _check_vector(self.field, stump_outside_bark_volume, *_INPUT_DIA_HT_DIV, rtol=self.rtol)


class TestTopInsideBarkVolume:
    field = "v_top_ib_gross"
    # v_top_ib = v_tot_ib * (1 - r_m). Small h_m drift amplifies into the
    # small top-volume residual (Trees 1, 2 ~2e-6 relative).
    rtol = RTOL_PUB_ITER

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, top_inside_bark_volume, *_TREE_DIA_HT_DIV(tree), rtol=self.rtol)

    def test_vector(self):
        _check_vector(self.field, top_inside_bark_volume, *_INPUT_DIA_HT_DIV, rtol=self.rtol)


class TestTopBarkVolume:
    field = "v_top_bk_gross"
    rtol = RTOL_PUB_BARK   # Tree 1 S2a propagation dominates h_m drift

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, top_bark_volume, *_TREE_DIA_HT_DIV(tree), rtol=self.rtol)

    def test_vector(self):
        _check_vector(self.field, top_bark_volume, *_INPUT_DIA_HT_DIV, rtol=self.rtol)


class TestTopOutsideBarkVolume:
    field = "v_top_ob_gross"
    rtol = RTOL_PUB_BARK   # Tree 1 S2a propagation via v_tot_ob

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, top_outside_bark_volume, *_TREE_DIA_HT_DIV(tree), rtol=self.rtol)

    def test_vector(self):
        _check_vector(self.field, top_outside_bark_volume, *_INPUT_DIA_HT_DIV, rtol=self.rtol)


# =============================================================================
# Step 6 -- missing-top volumes (broken-top trees only)
# =============================================================================
class TestMissingInsideBarkVolume:
    field = "v_miss_ib_gross"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(
            tree, self.field, missing_inside_bark_volume,
            tree.spcd, tree.dia, tree.ht, tree.division, tree.ah,
        )

    def test_vector(self):
        _check_vector(
            self.field, missing_inside_bark_volume,
            INPUTS["spcd"], INPUTS["dia"], INPUTS["ht"], INPUTS["division"], INPUTS["ah"],
        )


class TestMissingBarkVolume:
    field = "v_miss_bk_gross"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(
            tree, self.field, missing_bark_volume,
            tree.spcd, tree.dia, tree.ht, tree.division, tree.ah,
        )

    def test_vector(self):
        _check_vector(
            self.field, missing_bark_volume,
            INPUTS["spcd"], INPUTS["dia"], INPUTS["ht"], INPUTS["division"], INPUTS["ah"],
        )


class TestMissingOutsideBarkVolume:
    field = "v_miss_ob_gross"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(
            tree, self.field, missing_outside_bark_volume,
            tree.spcd, tree.dia, tree.ht, tree.division, tree.ah,
        )

    def test_vector(self):
        _check_vector(
            self.field, missing_outside_bark_volume,
            INPUTS["spcd"], INPUTS["dia"], INPUTS["ht"], INPUTS["division"], INPUTS["ah"],
        )


# =============================================================================
# Step 6 -- sound volumes (cull + broken-top deductions)
# =============================================================================
_SOUND_TREE_ARGS = lambda t: (t.spcd, t.dia, t.ht, t.division, t.cull, t.ah, t.decaycd)
_SOUND_INPUT_ARGS = (
    INPUTS["spcd"], INPUTS["dia"], INPUTS["ht"], INPUTS["division"],
    INPUTS["cull"], INPUTS["ah"], INPUTS["decaycd"],
)


class TestTotalInsideBarkVolumeSound:
    field = "v_tot_ib_sound"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, total_inside_bark_wood_volume_sound, *_SOUND_TREE_ARGS(tree))

    def test_vector(self):
        _check_vector(self.field, total_inside_bark_wood_volume_sound, *_SOUND_INPUT_ARGS)


class TestTotalBarkVolumeSound:
    field = "v_tot_bk_sound"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, total_bark_volume_sound, *_SOUND_TREE_ARGS(tree))

    def test_vector(self):
        _check_vector(self.field, total_bark_volume_sound, *_SOUND_INPUT_ARGS)


class TestTotalOutsideBarkVolumeSound:
    field = "v_tot_ob_sound"
    rtol = RTOL_PUB_BARK   # Tree 1 S2a propagation via v_tot_ob

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, total_outside_bark_volume_sound, *_SOUND_TREE_ARGS(tree), rtol=self.rtol)

    def test_vector(self):
        _check_vector(self.field, total_outside_bark_volume_sound, *_SOUND_INPUT_ARGS, rtol=self.rtol)


class TestMerchantableInsideBarkVolumeSound:
    field = "v_mer_ib_sound"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, merchantable_inside_bark_volume_sound, *_SOUND_TREE_ARGS(tree))

    def test_vector(self):
        _check_vector(self.field, merchantable_inside_bark_volume_sound, *_SOUND_INPUT_ARGS)


class TestMerchantableBarkVolumeSound:
    field = "v_mer_bk_sound"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, merchantable_bark_volume_sound, *_SOUND_TREE_ARGS(tree))

    def test_vector(self):
        _check_vector(self.field, merchantable_bark_volume_sound, *_SOUND_INPUT_ARGS)


class TestMerchantableOutsideBarkVolumeSound:
    field = "v_mer_ob_sound"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, merchantable_outside_bark_volume_sound, *_SOUND_TREE_ARGS(tree))

    def test_vector(self):
        _check_vector(self.field, merchantable_outside_bark_volume_sound, *_SOUND_INPUT_ARGS)


class TestStumpInsideBarkVolumeSound:
    field = "v_stump_ib_sound"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, stump_inside_bark_volume_sound, *_SOUND_TREE_ARGS(tree))

    def test_vector(self):
        _check_vector(self.field, stump_inside_bark_volume_sound, *_SOUND_INPUT_ARGS)


class TestStumpOutsideBarkVolumeSound:
    field = "v_stump_ob_sound"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, stump_outside_bark_volume_sound, *_SOUND_TREE_ARGS(tree))

    def test_vector(self):
        _check_vector(self.field, stump_outside_bark_volume_sound, *_SOUND_INPUT_ARGS)


class TestTopInsideBarkVolumeSound:
    field = "v_top_ib_sound"
    rtol = RTOL_PUB_SOUND   # Tree 4: small (R_b - R_m) amplifies h_m drift

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, top_inside_bark_volume_sound, *_SOUND_TREE_ARGS(tree), rtol=self.rtol)

    def test_vector(self):
        _check_vector(self.field, top_inside_bark_volume_sound, *_SOUND_INPUT_ARGS, rtol=self.rtol)


class TestTopBarkVolumeSound:
    field = "v_top_bk_sound"
    rtol = RTOL_PUB_SOUND   # Tree 4: small (R_b - R_m) amplifies h_m drift

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, top_bark_volume_sound, *_SOUND_TREE_ARGS(tree), rtol=self.rtol)

    def test_vector(self):
        _check_vector(self.field, top_bark_volume_sound, *_SOUND_INPUT_ARGS, rtol=self.rtol)


class TestTopOutsideBarkVolumeSound:
    field = "v_top_ob_sound"
    rtol = RTOL_PUB_SOUND   # same amplification as IB / BK counterparts

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, top_outside_bark_volume_sound, *_SOUND_TREE_ARGS(tree), rtol=self.rtol)

    def test_vector(self):
        _check_vector(self.field, top_outside_bark_volume_sound, *_SOUND_INPUT_ARGS, rtol=self.rtol)


# =============================================================================
# Step 7 -- total stem wood dry weight (Wtotib + Wtotibred)
# =============================================================================
class TestTotalStemWoodDryWeight:
    """Wtotib -- gross stem wood weight (no reductions)."""
    field = "w_tot_ib"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, total_stem_wood_dry_weight, *_TREE_DIA_HT_DIV(tree))

    def test_vector(self):
        _check_vector(self.field, total_stem_wood_dry_weight, *_INPUT_DIA_HT_DIV)


class TestTotalStemWoodDryWeightReduced:
    """Wtotibred -- with cull / dead density / broken-top reductions."""
    field = "w_tot_ib_red"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(
            tree, self.field, total_stem_wood_dry_weight_reduced,
            tree.spcd, tree.dia, tree.ht, tree.division, tree.cull, tree.ah, tree.decaycd,
        )

    def test_vector(self):
        _check_vector(
            self.field, total_stem_wood_dry_weight_reduced,
            INPUTS["spcd"], INPUTS["dia"], INPUTS["ht"], INPUTS["division"],
            INPUTS["cull"], INPUTS["ah"], INPUTS["decaycd"],
        )


# =============================================================================
# Step 8 -- total stem bark weight (Wtotbk + Wtotbkred + Wtotobred)
# =============================================================================
class TestTotalStemBarkWeight:
    field = "w_tot_bk"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, total_stem_bark_weight, *_TREE_DIA_HT_DIV(tree))

    def test_vector(self):
        _check_vector(self.field, total_stem_bark_weight, *_INPUT_DIA_HT_DIV)


class TestTotalStemBarkWeightReduced:
    field = "w_tot_bk_red"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(
            tree, self.field, total_stem_bark_weight_reduced,
            tree.spcd, tree.dia, tree.ht, tree.division, tree.ah, tree.decaycd,
        )

    def test_vector(self):
        _check_vector(
            self.field, total_stem_bark_weight_reduced,
            INPUTS["spcd"], INPUTS["dia"], INPUTS["ht"], INPUTS["division"],
            INPUTS["ah"], INPUTS["decaycd"],
        )


class TestTotalStemOutsideBarkWeightReduced:
    field = "w_tot_ob_red"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(
            tree, self.field, total_stem_outside_bark_weight_reduced,
            tree.spcd, tree.dia, tree.ht, tree.division, tree.cull, tree.ah, tree.decaycd,
        )

    def test_vector(self):
        _check_vector(
            self.field, total_stem_outside_bark_weight_reduced,
            INPUTS["spcd"], INPUTS["dia"], INPUTS["ht"], INPUTS["division"],
            INPUTS["cull"], INPUTS["ah"], INPUTS["decaycd"],
        )


# =============================================================================
# Step 9 -- total branch weight (Wbranch + Wbranchred + intermediates)
# =============================================================================
class TestTotalBranchWeight:
    field = "w_branch"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, total_branch_weight, *_TREE_DIA_HT_DIV(tree))

    def test_vector(self):
        _check_vector(self.field, total_branch_weight, *_INPUT_DIA_HT_DIV)


class TestCrownRatioAtH:
    field = "crh"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, crown_ratio_at_h, tree.ht, tree.ah, tree.cr)

    def test_vector(self):
        _check_vector(self.field, crown_ratio_at_h, INPUTS["ht"], INPUTS["ah"], INPUTS["cr"])


class TestBranchRemainder:
    """branch_remainder is the pure formula; the H-standardized CRH must be
    resolved by the caller (here via :func:`tree_crh`)."""
    field = "branch_rem"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, branch_remainder, tree.ht, tree.ah, tree_crh(tree))

    def test_vector(self):
        _check_vector(self.field, branch_remainder, INPUTS["ht"], INPUTS["ah"], CRH)


class TestFoliageRemainder:
    field = "foliage_rem"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, foliage_remainder, tree.ht, tree.ah, tree_crh(tree))

    def test_vector(self):
        _check_vector(self.field, foliage_remainder, INPUTS["ht"], INPUTS["ah"], CRH)


class TestTotalBranchWeightReduced:
    field = "w_branch_red"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(
            tree, self.field, total_branch_weight_reduced,
            tree.spcd, tree.dia, tree.ht, tree.division,
            tree.ah, tree.decaycd, tree.cr, tree.province or "",
        )

    def test_vector(self):
        _check_vector(
            self.field, total_branch_weight_reduced,
            INPUTS["spcd"], INPUTS["dia"], INPUTS["ht"], INPUTS["division"],
            INPUTS["ah"], INPUTS["decaycd"], INPUTS["cr"], INPUTS["province"],
        )


# =============================================================================
# Step 10 -- total aboveground biomass (S8, predicted)
# =============================================================================
class TestTotalAbovegroundBiomass:
    field = "agb_predicted"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, total_aboveground_biomass, *_TREE_DIA_HT_DIV(tree))

    def test_vector(self):
        _check_vector(self.field, total_aboveground_biomass, *_INPUT_DIA_HT_DIV)


# =============================================================================
# Step 11 -- AGB harmonization scalars
# =============================================================================
class TestAGBComponentReduced:
    field = "agb_component_red"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, agb_component_reduced, *_TREE_FULL(tree))

    def test_vector(self):
        _check_vector(self.field, agb_component_reduced, *_INPUT_FULL)


class TestAGBReduceFactor:
    field = "agb_reduce"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, agb_reduce_factor, *_TREE_FULL(tree))

    def test_vector(self):
        _check_vector(self.field, agb_reduce_factor, *_INPUT_FULL)


class TestAGBPredictedReduced:
    field = "agb_predicted_red"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, agb_predicted_reduced, *_TREE_FULL(tree))

    def test_vector(self):
        _check_vector(self.field, agb_predicted_reduced, *_INPUT_FULL)


class TestAGBDifference:
    field = "agb_diff"
    # AGBDiff = AGBPredictedred - AGBComponentred -- small difference of
    # two large nearly-equal numbers. For Tree 1 (~31 ft of difference on
    # ~3154 lb totals), rtol=1e-6 in the inputs becomes ~1e-5 in the diff.
    rtol = 5e-5

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, agb_difference, *_TREE_FULL(tree), rtol=self.rtol)

    def test_vector(self):
        _check_vector(self.field, agb_difference, *_INPUT_FULL, rtol=self.rtol)


# =============================================================================
# Step 12 -- harmonized components
# =============================================================================
class TestHarmonizedWood:
    field = "wood_harmonized"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, harmonized_wood, *_TREE_FULL(tree))

    def test_vector(self):
        _check_vector(self.field, harmonized_wood, *_INPUT_FULL)


class TestHarmonizedBark:
    field = "bark_harmonized"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, harmonized_bark, *_TREE_FULL(tree))

    def test_vector(self):
        _check_vector(self.field, harmonized_bark, *_INPUT_FULL)


class TestHarmonizedBranch:
    field = "branch_harmonized"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, harmonized_branch, *_TREE_FULL(tree))

    def test_vector(self):
        _check_vector(self.field, harmonized_branch, *_INPUT_FULL)


# =============================================================================
# Step 13 -- adjusted densities
# =============================================================================
class TestAdjustedWoodDensity:
    field = "wdsg_adj"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, adjusted_wood_density, *_TREE_FULL(tree))

    def test_vector(self):
        _check_vector(self.field, adjusted_wood_density, *_INPUT_FULL)


class TestAdjustedBarkDensity:
    field = "bksg_adj"
    # Tree 1: BKSGAdj = BarkHarmonized / V_tot_bk_basis / 62.4. The
    # denominator V_tot_bk_basis inherits the S2a coefficient precision drift
    # (~4e-4 relative) for SPCD 202 / DIV 240.
    rtol = RTOL_PUB_BARK

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, adjusted_bark_density, *_TREE_FULL(tree), rtol=self.rtol)

    def test_vector(self):
        _check_vector(self.field, adjusted_bark_density, *_INPUT_FULL, rtol=self.rtol)


# =============================================================================
# Step 14 -- merchantable & stump weights
# =============================================================================
class TestMerchantableWoodWeight:
    field = "w_mer_ib"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, merchantable_wood_weight, *_TREE_FULL(tree))

    def test_vector(self):
        _check_vector(self.field, merchantable_wood_weight, *_INPUT_FULL)


class TestMerchantableBarkWeight:
    field = "w_mer_bk"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, merchantable_bark_weight, *_TREE_FULL(tree))

    def test_vector(self):
        _check_vector(self.field, merchantable_bark_weight, *_INPUT_FULL)


class TestMerchantableOutsideBarkWeight:
    field = "w_mer_ob"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, merchantable_outside_bark_weight, *_TREE_FULL(tree))

    def test_vector(self):
        _check_vector(self.field, merchantable_outside_bark_weight, *_INPUT_FULL)


class TestStumpWoodWeight:
    field = "w_stump_ib"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, stump_wood_weight, *_TREE_FULL(tree))

    def test_vector(self):
        _check_vector(self.field, stump_wood_weight, *_INPUT_FULL)


class TestStumpBarkWeight:
    field = "w_stump_bk"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, stump_bark_weight, *_TREE_FULL(tree))

    def test_vector(self):
        _check_vector(self.field, stump_bark_weight, *_INPUT_FULL)


class TestStumpOutsideBarkWeight:
    field = "w_stump_ob"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, stump_outside_bark_weight, *_TREE_FULL(tree))

    def test_vector(self):
        _check_vector(self.field, stump_outside_bark_weight, *_INPUT_FULL)


# =============================================================================
# Step 15 -- foliage weight (Wfoliage + Wfoliagered)
# =============================================================================
class TestTotalFoliageDryWeight:
    field = "w_foliage"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, total_foliage_dry_weight, *_TREE_DIA_HT_DIV(tree))

    def test_vector(self):
        _check_vector(self.field, total_foliage_dry_weight, *_INPUT_DIA_HT_DIV)


class TestTotalFoliageDryWeightReduced:
    field = "w_foliage_red"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(
            tree, self.field, total_foliage_dry_weight_reduced,
            tree.spcd, tree.dia, tree.ht, tree.division,
            tree.ah, tree.decaycd, tree.cr, tree.province or "",
        )

    def test_vector(self):
        _check_vector(
            self.field, total_foliage_dry_weight_reduced,
            INPUTS["spcd"], INPUTS["dia"], INPUTS["ht"], INPUTS["division"],
            INPUTS["ah"], INPUTS["decaycd"], INPUTS["cr"], INPUTS["province"],
        )


# =============================================================================
# Step 16 -- DRYBIO_TOP
# =============================================================================
class TestDrybioTop:
    field = "drybio_top"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, drybio_top, *_TREE_FULL(tree))

    def test_vector(self):
        _check_vector(self.field, drybio_top, *_INPUT_FULL)


# =============================================================================
# Step 17 -- carbon content (S10)
# =============================================================================
class TestCarbonContent:
    field = "c"

    @pytest.mark.parametrize("tree", TREES, ids=TREE_IDS)
    def test_scalar(self, tree):
        _check_scalar(tree, self.field, carbon_content, *_TREE_FULL(tree))

    def test_vector(self):
        _check_vector(self.field, carbon_content, *_INPUT_FULL)