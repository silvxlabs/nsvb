"""
Tests for dead tree calculations (GTR-WO-104 DECAYCD adjustments).

Dead trees have wood density reductions and bark/branch structural losses
based on decay class (DECAYCD) as specified in Table 1 of the GTR.
"""

import numpy as np
import pytest

from nsvb.estimators import (
    total_inside_bark_wood_volume,
    total_stem_wood_dry_weight,
    total_stem_bark_weight,
    total_branch_weight,
    total_aboveground_biomass,
    get_decay_proportions,
    harmonize_components,
)

from .gtr_values import Example3, DecayProportions


class TestDecayProportions:
    """
    Tests for decay proportion lookups from GTR Table 1.

    Table 1 values:
    Hardwood DECAYCD 1: DensProp=0.99, BarkProp=1.0, BranchProp=1.0
    Hardwood DECAYCD 2: DensProp=0.80, BarkProp=0.8, BranchProp=0.5
    Hardwood DECAYCD 3: DensProp=0.54, BarkProp=0.5, BranchProp=0.1
    Hardwood DECAYCD 4: DensProp=0.43, BarkProp=0.2, BranchProp=0
    Hardwood DECAYCD 5: DensProp=0.43, BarkProp=0, BranchProp=0

    Softwood DECAYCD 1: DensProp=0.97, BarkProp=1.0, BranchProp=1.0
    Softwood DECAYCD 2: DensProp=1.00, BarkProp=0.8, BranchProp=0.5
    Softwood DECAYCD 3: DensProp=0.92, BarkProp=0.5, BranchProp=0.1
    Softwood DECAYCD 4: DensProp=0.55, BarkProp=0.2, BranchProp=0
    Softwood DECAYCD 5: DensProp=0.55, BarkProp=0, BranchProp=0
    """

    def test_hardwood_decay_class_1(self):
        """Test hardwood DECAYCD=1 proportions."""
        props = get_decay_proportions(spcd=316, decaycd=1)  # Red maple (hardwood)
        assert props["dens_prop"] == DecayProportions.HARDWOOD[1]["dens_prop"]
        assert props["bark_prop"] == DecayProportions.HARDWOOD[1]["bark_prop"]
        assert props["branch_prop"] == DecayProportions.HARDWOOD[1]["branch_prop"]

    def test_hardwood_decay_class_2(self):
        """Test hardwood DECAYCD=2 proportions."""
        props = get_decay_proportions(spcd=316, decaycd=2)
        assert props["dens_prop"] == DecayProportions.HARDWOOD[2]["dens_prop"]
        assert props["bark_prop"] == DecayProportions.HARDWOOD[2]["bark_prop"]
        assert props["branch_prop"] == DecayProportions.HARDWOOD[2]["branch_prop"]

    def test_hardwood_decay_class_3(self):
        """Test hardwood DECAYCD=3 proportions."""
        props = get_decay_proportions(spcd=316, decaycd=3)
        assert props["dens_prop"] == DecayProportions.HARDWOOD[3]["dens_prop"]
        assert props["bark_prop"] == DecayProportions.HARDWOOD[3]["bark_prop"]
        assert props["branch_prop"] == DecayProportions.HARDWOOD[3]["branch_prop"]

    def test_hardwood_decay_class_4(self):
        """Test hardwood DECAYCD=4 proportions."""
        props = get_decay_proportions(spcd=316, decaycd=4)
        assert props["dens_prop"] == DecayProportions.HARDWOOD[4]["dens_prop"]
        assert props["bark_prop"] == DecayProportions.HARDWOOD[4]["bark_prop"]
        assert props["branch_prop"] == DecayProportions.HARDWOOD[4]["branch_prop"]

    def test_hardwood_decay_class_5(self):
        """Test hardwood DECAYCD=5 proportions."""
        props = get_decay_proportions(spcd=316, decaycd=5)
        assert props["dens_prop"] == DecayProportions.HARDWOOD[5]["dens_prop"]
        assert props["bark_prop"] == DecayProportions.HARDWOOD[5]["bark_prop"]
        assert props["branch_prop"] == DecayProportions.HARDWOOD[5]["branch_prop"]

    def test_softwood_decay_class_1(self):
        """Test softwood DECAYCD=1 proportions."""
        props = get_decay_proportions(spcd=202, decaycd=1)  # Douglas-fir (softwood)
        assert props["dens_prop"] == DecayProportions.SOFTWOOD[1]["dens_prop"]
        assert props["bark_prop"] == DecayProportions.SOFTWOOD[1]["bark_prop"]
        assert props["branch_prop"] == DecayProportions.SOFTWOOD[1]["branch_prop"]

    def test_softwood_decay_class_2(self):
        """Test softwood DECAYCD=2 proportions."""
        props = get_decay_proportions(spcd=202, decaycd=2)
        assert props["dens_prop"] == DecayProportions.SOFTWOOD[2]["dens_prop"]
        assert props["bark_prop"] == DecayProportions.SOFTWOOD[2]["bark_prop"]
        assert props["branch_prop"] == DecayProportions.SOFTWOOD[2]["branch_prop"]

    def test_softwood_decay_class_3(self):
        """Test softwood DECAYCD=3 proportions."""
        props = get_decay_proportions(spcd=202, decaycd=3)
        assert props["dens_prop"] == DecayProportions.SOFTWOOD[3]["dens_prop"]
        assert props["bark_prop"] == DecayProportions.SOFTWOOD[3]["bark_prop"]
        assert props["branch_prop"] == DecayProportions.SOFTWOOD[3]["branch_prop"]

    def test_softwood_decay_class_4(self):
        """Test softwood DECAYCD=4 proportions."""
        props = get_decay_proportions(spcd=202, decaycd=4)
        assert props["dens_prop"] == DecayProportions.SOFTWOOD[4]["dens_prop"]
        assert props["bark_prop"] == DecayProportions.SOFTWOOD[4]["bark_prop"]
        assert props["branch_prop"] == DecayProportions.SOFTWOOD[4]["branch_prop"]

    def test_softwood_decay_class_5(self):
        """Test softwood DECAYCD=5 proportions."""
        props = get_decay_proportions(spcd=202, decaycd=5)
        assert props["dens_prop"] == DecayProportions.SOFTWOOD[5]["dens_prop"]
        assert props["bark_prop"] == DecayProportions.SOFTWOOD[5]["bark_prop"]
        assert props["branch_prop"] == DecayProportions.SOFTWOOD[5]["branch_prop"]


class TestDeadTreeExample3:
    """
    Tests for dead tree calculations using Example 3 from GTR.

    Example 3: Dead tanoak (SPCD=631), D=11.3", H=28', AH=21', Division=M240
    DECAYCD=2, CULL=10%

    From GTR pages 16-21:
    - VtotibGross = 7.283117547652 (full tree volume)
    - VtotibBT = 5.638614085234 (broken top volume, AH=21')
    - Wtotib = 263.590590284621 lb (before decay reduction, full tree)
    - Wtotibred = 204.13865566837 lb (with DECAYCD=2 reduction and broken top)
    - DensProp for hardwood DECAYCD=2 = 0.80
    """

    def test_volume_gross(self):
        """
        VtotibGross = 7.283117547652 ft³ (full tree, no broken top)

        From GTR Example 3 (page 16).
        """
        result = total_inside_bark_wood_volume(
            spcd=Example3.SPCD, dia=Example3.DIA, ht=Example3.HT, division=Example3.DIVISION
        )
        assert pytest.approx(result, rel=1e-4) == Example3.V_TOTIB_GROSS_GTR

    def test_volume_with_broken_top(self):
        """
        Broken top volume using volume ratio at actual height (AH).

        From GTR Example 3 (page 18):
        Rm = [1 – (1 – AH/H)^α]^β
        Rm = [1 – (1 – 21/28)^2.353772358051]^0.831640004254 = 0.968066877159

        VtotibBT = Rm × VtotibGross = 0.968066877159 × 7.283117547652 = 7.050544971441

        Note: The GTR value 5.638614085234 from Example 3 is the "effective volume"
        for weight calculation after applying DensProp. Volume functions return
        actual geometric volume, not density-adjusted values.
        """
        result = total_inside_bark_wood_volume(
            spcd=Example3.SPCD,
            dia=Example3.DIA,
            ht=Example3.HT,
            ah=Example3.AH,
            division=Example3.DIVISION,
        )
        # Rm × VtotibGross = 0.968066877159 × 7.283117547652 = 7.050544971441
        assert pytest.approx(result, rel=1e-4) == Example3.V_TOTIB_BT_GTR

    def test_stem_wood_weight_before_decay(self):
        """
        Wtotib = VtotibGross × WDSG × 62.4
        Wtotib = 7.283117547652 × 0.58 × 62.4 = 263.590590284621

        From GTR Example 3 (page 19). This is the full tree weight before
        any decay or broken top adjustments.
        """
        # Calculate without decay reduction (live tree equivalent)
        v_gross = total_inside_bark_wood_volume(
            spcd=Example3.SPCD, dia=Example3.DIA, ht=Example3.HT, division=Example3.DIVISION
        )
        wdsg = 0.58  # From REF_SPECIES for SPCD=631
        w_totib = v_gross * wdsg * 62.4
        assert pytest.approx(w_totib, rel=1e-4) == Example3.W_TOTIB_GTR

    def test_stem_wood_weight_with_decay_and_broken_top(self):
        """
        GTR Example 3 (page 19): Dead tree stem wood weight with broken top.

        Wtotibred = 204.13865566837 lb

        This calculation includes:
        - Broken top at AH=21' (reduces volume from 7.283 to 5.639 ft³)
        - DECAYCD=2 (hardwood DensProp=0.80)
        - CULL=10% (not applied separately for dead trees per GTR page 19)

        The reduced weight accounts for both the broken top volume reduction
        and the decay-based density reduction.
        """
        result = total_stem_wood_dry_weight(
            spcd=Example3.SPCD,
            dia=Example3.DIA,
            ht=Example3.HT,
            ah=Example3.AH,
            division=Example3.DIVISION,
            cull=Example3.CULL,
            decaycd=Example3.DECAYCD,
        )
        # GTR Example 3 expected value (page 19)
        assert pytest.approx(result, rel=1e-4) == Example3.W_TOTIBRED_GTR

    def test_stem_bark_weight_with_decay(self):
        """
        Dead tree bark weight with decay reduction (no broken top).

        GTR-WO-104 Example 3 (page 22-23):
        Wtotbkred = Wtotbk × DensProp × BarkProp

        GTR Table 1: Hardwood DECAYCD=2
        - DensProp = 0.8
        - BarkProp = 0.8

        Live bark weight = 46.81666440280295 lb
        Dead bark weight = 46.81666440280295 × 0.8 × 0.8 = 29.962665217793894 lb
        """
        result = total_stem_bark_weight(
            spcd=Example3.SPCD,
            dia=Example3.DIA,
            ht=Example3.HT,
            division=Example3.DIVISION,
            decaycd=Example3.DECAYCD,
        )
        # Live weight × DensProp × BarkProp
        expected = Example3.W_TOTBK_GTR * Example3.DENS_PROP * Example3.BARK_PROP
        assert pytest.approx(result, rel=1e-4) == expected

    def test_stem_bark_weight_with_decay_and_broken_top(self):
        """
        GTR Example 3 (page 19): Dead tree bark weight with broken top.

        Wtotbkred = Wtotbk × Rm × DensProp × BarkProp
        Wtotbkred = 46.816664266025 × 0.968066877159 × 0.8 × 0.8
                  = 29.005863664008

        This calculation includes:
        - Broken top at AH=21' (Rm = 0.968066877159)
        - DECAYCD=2 (hardwood DensProp=0.80, BarkProp=0.8)
        """
        result = total_stem_bark_weight(
            spcd=Example3.SPCD,
            dia=Example3.DIA,
            ht=Example3.HT,
            ah=Example3.AH,
            division=Example3.DIVISION,
            decaycd=Example3.DECAYCD,
        )
        # GTR Example 3 expected value (page 19)
        assert pytest.approx(result, rel=1e-4) == Example3.W_TOTBKRED_GTR

    def test_branch_weight_with_decay(self):
        """
        Dead tree branch weight with decay reduction (no broken top).

        GTR-WO-104 Example 3 (page 22-23):
        Wbranchred = Wbranch × DensProp × BranchProp

        GTR Table 1: Hardwood DECAYCD=2
        - DensProp = 0.8
        - BranchProp = 0.5

        Live branch weight = 226.78800239146196 lb
        Dead branch weight = 226.78800239146196 × 0.8 × 0.5 = 90.71520095658479 lb
        """
        result = total_branch_weight(
            spcd=Example3.SPCD,
            dia=Example3.DIA,
            ht=Example3.HT,
            division=Example3.DIVISION,
            decaycd=Example3.DECAYCD,
        )
        # Live weight × DensProp × BranchProp
        expected = Example3.W_BRANCH_GTR * Example3.DENS_PROP * Example3.BRANCH_PROP
        assert pytest.approx(result, rel=1e-4) == expected

    def test_branch_weight_with_decay_and_broken_top(self):
        """
        GTR Example 3 (page 20): Dead tree branch weight with broken top.

        Wbranchred = Wbranch × DensProp × BranchProp × BranchRem
        Wbranchred = 226.788002348975 × 0.8 × 0.5 × 0.338624338624
                   = 30.718374921312

        This calculation includes:
        - Broken top at AH=21' with CR=0.378 from Table S11
        - BranchRem = [AH - H × (1 - CR)] / (H × CR)
                    = [21 - 28 × (1 - 0.378)] / (28 × 0.378)
                    = 0.338624338624
        - DECAYCD=2 (hardwood DensProp=0.80, BranchProp=0.5)

        Note: For dead trees, CR is looked up from Table S11 automatically
        when cr parameter is not provided. The division should be the
        ecoprovince (M242) for Table S11 lookup.
        """
        # For dead trees, we don't pass cr - the function looks it up
        # from Table S11. However, we need to use the province (M242)
        # not the division (M240) for the lookup.
        result = total_branch_weight(
            spcd=Example3.SPCD,
            dia=Example3.DIA,
            ht=Example3.HT,
            ah=Example3.AH,
            division=Example3.PROVINCE,  # Use province for Table S11 lookup
            decaycd=Example3.DECAYCD,
        )
        # GTR Example 3 expected value (page 20)
        assert pytest.approx(result, rel=1e-4) == Example3.W_BRANCHRED_GTR

    def test_branch_weight_decay_class_5(self):
        """
        Dead tree branch weight with DECAYCD=5 (no branches remaining).

        GTR Table 1: Hardwood DECAYCD=5 BranchProp = 0
        """
        result = total_branch_weight(
            spcd=Example3.SPCD,
            dia=Example3.DIA,
            ht=Example3.HT,
            division=Example3.DIVISION,
            decaycd=5,
        )
        assert result == 0.0

    def test_harmonize_components_dead_tree(self):
        """
        Test component harmonization for dead trees.

        Harmonization ensures wood + bark + branch = AGB after applying
        decay proportions (DensProp, BarkProp, BranchProp).
        """
        result = harmonize_components(
            spcd=Example3.SPCD,
            dia=Example3.DIA,
            ht=Example3.HT,
            division=Example3.DIVISION,
            decaycd=Example3.DECAYCD,
        )

        # Verify harmonized components sum to AGB
        component_sum = result["wood"] + result["bark"] + result["branch"]
        assert pytest.approx(component_sum, rel=1e-6) == result["agb"]

        # AGB should be reduced from live tree value
        live_agb = total_aboveground_biomass(
            spcd=Example3.SPCD, dia=Example3.DIA, ht=Example3.HT, division=Example3.DIVISION
        )
        assert result["agb"] < live_agb

    def test_harmonize_components_decay_class_5(self):
        """
        Test harmonization with DECAYCD=5 (no bark or branches).

        GTR Table 1: Hardwood DECAYCD=5: BarkProp=0, BranchProp=0
        Only wood remains, so bark and branch harmonized weights should be 0.
        """
        result = harmonize_components(
            spcd=Example3.SPCD,
            dia=Example3.DIA,
            ht=Example3.HT,
            division=Example3.DIVISION,
            decaycd=5,
        )

        # With BarkProp=0 and BranchProp=0, only wood remains
        assert result["bark"] == 0.0
        assert result["branch"] == 0.0

        # All AGB is in wood
        assert pytest.approx(result["wood"], rel=1e-6) == result["agb"]


class TestDeadTreeVectorized:
    """
    Tests for vectorized dead tree calculations.

    Ensures that dead tree calculations (with decay reductions) work
    correctly with array inputs.
    """

    def test_stem_wood_weight_vectorized_decay(self):
        """
        Vectorized stem wood weight with decay classes.

        Tests array inputs with different decay classes produce correct
        density-reduced weights.
        """
        # Two dead trees: one tanoak (hardwood), one Douglas-fir (softwood)
        spcd = np.array([631, 202])
        dia = np.array([11.3, 15.0])
        ht = np.array([28.0, 80.0])
        division = np.array(["M240", "240"])
        decaycd = np.array([2, 3])  # Different decay classes

        result = total_stem_wood_dry_weight(
            spcd=spcd, dia=dia, ht=ht, division=division, decaycd=decaycd
        )

        assert isinstance(result, np.ndarray)
        assert len(result) == 2

        # Compare to scalar calculations
        scalar1 = total_stem_wood_dry_weight(
            spcd=631, dia=11.3, ht=28.0, division="M240", decaycd=2
        )
        scalar2 = total_stem_wood_dry_weight(
            spcd=202, dia=15.0, ht=80.0, division="240", decaycd=3
        )

        assert pytest.approx(result[0], rel=1e-6) == scalar1
        assert pytest.approx(result[1], rel=1e-6) == scalar2

    def test_stem_bark_weight_vectorized_decay(self):
        """
        Vectorized stem bark weight with decay classes.
        """
        spcd = np.array([631, 316, 202])
        dia = np.array([11.3, 12.0, 18.0])
        ht = np.array([28.0, 40.0, 90.0])
        division = np.array(["M240", "M210", "240"])
        decaycd = np.array([2, 4, 5])

        result = total_stem_bark_weight(
            spcd=spcd, dia=dia, ht=ht, division=division, decaycd=decaycd
        )

        assert isinstance(result, np.ndarray)
        assert len(result) == 3

        # DECAYCD=5 should have BarkProp=0, so bark weight should be 0
        assert result[2] == 0.0

    def test_branch_weight_vectorized_decay(self):
        """
        Vectorized branch weight with decay classes.
        """
        spcd = np.array([631, 316])
        dia = np.array([11.3, 12.0])
        ht = np.array([28.0, 40.0])
        division = np.array(["M240", "M210"])
        decaycd = np.array([2, 5])

        result = total_branch_weight(
            spcd=spcd, dia=dia, ht=ht, division=division, decaycd=decaycd
        )

        assert isinstance(result, np.ndarray)
        assert len(result) == 2

        # DECAYCD=5 should have BranchProp=0, so branch weight should be 0
        assert result[1] == 0.0

        # First should match scalar
        scalar = total_branch_weight(
            spcd=631, dia=11.3, ht=28.0, division="M240", decaycd=2
        )
        assert pytest.approx(result[0], rel=1e-6) == scalar

    def test_harmonize_components_vectorized_decay(self):
        """
        Vectorized harmonization with decay classes.
        """
        spcd = np.array([631, 316])
        dia = np.array([11.3, 12.0])
        ht = np.array([28.0, 40.0])
        division = np.array(["M240", "M210"])
        decaycd = np.array([2, 3])

        result = harmonize_components(
            spcd=spcd, dia=dia, ht=ht, division=division, decaycd=decaycd
        )

        assert isinstance(result["wood"], np.ndarray)
        assert len(result["wood"]) == 2

        # Verify components sum to AGB for each tree
        for i in range(2):
            component_sum = result["wood"][i] + result["bark"][i] + result["branch"][i]
            assert pytest.approx(component_sum, rel=1e-6) == result["agb"][i]

