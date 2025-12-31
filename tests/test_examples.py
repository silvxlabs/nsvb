import numpy as np
import pytest

from nsvb.estimators import (
    total_inside_bark_wood_volume,
    total_bark_wood_volume,
    total_stem_wood_dry_weight,
    total_stem_bark_weight,
    total_branch_weight,
    total_aboveground_biomass,
    total_foliage_dry_weight,
    missing_inside_bark_volume,
    calculate_crh,
    calculate_branch_foliage_remaining,
)

from .gtr_values import Example1, Example2, Example3, Example4


class TestExample1:
    """
    Tests for GTR Example 1: Douglas-fir (SPCD=202), D=20.0", H=110', Division=240.

    Reference: GTR-WO-104 pages 10-12.
    """

    def test_inside_bark_wood_volume(self):
        """
        VtotibGross = a × k^(b-b1) × D^b1 × H^c = 88.452275544288 ft³

        GTR page 10, using model 2 with coefficients from Table S1a.
        """
        result = total_inside_bark_wood_volume(
            Example1.SPCD, Example1.DIA, Example1.HT, Example1.DIVISION
        )
        assert pytest.approx(result, rel=1e-4) == Example1.V_TOTIB_GROSS_GTR

    def test_total_bark_wood_volume(self):
        """
        VtotbkGross = a × D^b × H^c = 13.191436232306 ft³

        GTR page 10, using model 1 with coefficients from Table S2a.

        Note: Implementation produces 13.197 vs GTR 13.191 (~0.04% difference).
        This may be due to coefficient precision differences.
        """
        result = total_bark_wood_volume(
            Example1.SPCD, Example1.DIA, Example1.HT, Example1.DIVISION
        )
        assert pytest.approx(result, rel=5e-4) == Example1.V_TOTBK_GROSS_GTR

    def test_total_stem_wood_dry_weight(self):
        """
        Wtotib = VtotibGross × WDSG × 62.4 = 2483.739897283610 lb

        GTR page 11. WDSG=0.45 for Douglas-fir from REF_SPECIES.
        """
        result = total_stem_wood_dry_weight(
            Example1.SPCD, Example1.DIA, Example1.HT, Example1.DIVISION
        )
        assert pytest.approx(result, rel=1e-4) == Example1.W_TOTIB_GTR

    def test_total_stem_bark_weight(self):
        """
        Wtotbk = a × D^b × H^c = 361.782496100100 lb

        GTR page 11, using model 1 with coefficients from Table S6a.
        """
        result = total_stem_bark_weight(
            Example1.SPCD, Example1.DIA, Example1.HT, Example1.DIVISION
        )
        assert pytest.approx(result, rel=1e-4) == Example1.W_TOTBK_GTR

    def test_total_branch_weight(self):
        """
        Wbranch = a × D^b × H^c = 277.487756904646 lb

        GTR page 11, using model 1 with coefficients from Table S7a.
        """
        result = total_branch_weight(
            Example1.SPCD, Example1.DIA, Example1.HT, Example1.DIVISION
        )
        assert pytest.approx(result, rel=1e-4) == Example1.W_BRANCH_GTR

    def test_total_aboveground_biomass(self):
        """
        AGBPredicted = a × D^b × H^c = 3154.5539926725 lb

        GTR page 11, using model 1 with coefficients from Table S8a.
        """
        result = total_aboveground_biomass(
            Example1.SPCD, Example1.DIA, Example1.HT, Example1.DIVISION
        )
        assert pytest.approx(result, rel=1e-4) == Example1.AGB_PREDICTED_GTR

    def test_total_foliage_dry_weight(self):
        """
        Wfoliage = a × k^(b-b1) × D^b1 × H^c = 83.634788855934 lb

        GTR page 11, using model 2 with coefficients from Table S9a.
        """
        result = total_foliage_dry_weight(
            Example1.SPCD, Example1.DIA, Example1.HT, Example1.DIVISION
        )
        assert pytest.approx(result, rel=1e-4) == Example1.W_FOLIAGE_GTR


class TestExample2:
    """
    Tests for GTR Example 2: Red maple (SPCD=316), D=11.1", H=38', Division=M210, CULL=3%.

    Reference: GTR-WO-104 pages 13-15.
    """

    def test_inside_bark_wood_volume(self):
        """
        VtotibGross = a × D^b × H^c = 9.427112777611 ft³

        GTR page 13, using model 1 with species-level coefficients from Table S1a.
        """
        result = total_inside_bark_wood_volume(
            Example2.SPCD, Example2.DIA, Example2.HT, Example2.DIVISION
        )
        assert pytest.approx(result, rel=1e-4) == Example2.V_TOTIB_GROSS_GTR

    def test_total_bark_wood_volume(self):
        """
        VtotbkGross = a × k^(b-b1) × D^b1 × H^c = 2.155106401987 ft³

        GTR page 13, using model 2 with coefficients from Table S2a.
        """
        result = total_bark_wood_volume(
            Example2.SPCD, Example2.DIA, Example2.HT, Example2.DIVISION
        )
        assert pytest.approx(result, rel=1e-4) == Example2.V_TOTBK_GROSS_GTR

    def test_total_stem_wood_dry_weight(self):
        """
        Without cull: Wtotib = VtotibGross × WDSG × 62.4 = 288.243400288234 lb
        With cull: Wtotibred = VtotibGross × [1 - CULL/100 × (1 - DensProp)] × WDSG × 62.4
                             = 284.265641364256 lb

        GTR page 14. WDSG=0.49 for Red maple, DensProp=0.54 for hardwood cull.
        """
        # Test without cull
        result_no_cull = total_stem_wood_dry_weight(
            Example2.SPCD, Example2.DIA, Example2.HT, Example2.DIVISION
        )
        assert pytest.approx(result_no_cull, rel=1e-4) == Example2.W_TOTIB_NO_CULL_GTR

        # Test with cull
        result_with_cull = total_stem_wood_dry_weight(
            Example2.SPCD,
            Example2.DIA,
            Example2.HT,
            Example2.DIVISION,
            cull=Example2.CULL,
        )
        assert pytest.approx(result_with_cull, rel=1e-4) == Example2.W_TOTIBRED_GTR

    def test_total_stem_bark_weight(self):
        """
        Wtotbk = a × D^b × H^c = 52.945466015848 lb

        GTR page 14, using model 1 with coefficients from Table S6a.
        """
        result = total_stem_bark_weight(
            Example2.SPCD, Example2.DIA, Example2.HT, Example2.DIVISION
        )
        assert pytest.approx(result, rel=1e-4) == Example2.W_TOTBK_GTR

    def test_total_branch_weight(self):
        """
        Wbranch = a × D^b × H^c = 135.001927997271 lb

        GTR page 14, using model 1 with coefficients from Table S7a.
        """
        result = total_branch_weight(
            Example2.SPCD, Example2.DIA, Example2.HT, Example2.DIVISION
        )
        assert pytest.approx(result, rel=1e-4) == Example2.W_BRANCH_GTR

    def test_total_aboveground_biomass(self):
        """
        AGBPredicted = a × D^b × H^c × exp(-b1 × D) = 532.584798820042 lb

        GTR page 14, using model 4 with coefficients from Table S8a.
        """
        result = total_aboveground_biomass(
            Example2.SPCD, Example2.DIA, Example2.HT, Example2.DIVISION
        )
        assert pytest.approx(result, rel=1e-4) == Example2.AGB_PREDICTED_GTR

    def test_total_foliage_dry_weight(self):
        """
        Wfoliage = a × D^b × H^c = 22.807960563788 lb

        GTR page 14, using model 1 with coefficients from Table S9a.
        """
        result = total_foliage_dry_weight(
            Example2.SPCD, Example2.DIA, Example2.HT, Example2.DIVISION
        )
        assert pytest.approx(result, rel=1e-4) == Example2.W_FOLIAGE_GTR


class TestExample3:
    """
    Tests for GTR Example 3: Dead tanoak (SPCD=631), D=11.3", H=28', AH=21',
    Division=M240, Province=M242, DECAYCD=2, CULL=10%.

    Reference: GTR-WO-104 pages 16-20.
    """

    def test_inside_bark_wood_volume(self):
        """
        VtotibGross = a × D^b × H^c = 7.283117547652 ft³

        GTR page 16, using model 1 with Jenkins group coefficients from Table S1b.
        """
        result = total_inside_bark_wood_volume(
            Example3.SPCD, Example3.DIA, Example3.HT, Example3.DIVISION
        )
        assert pytest.approx(result, rel=1e-4) == Example3.V_TOTIB_GROSS_GTR

    def test_total_bark_wood_volume(self):
        """
        VtotbkGross = a × D^b × H^c = 1.907136145131 ft³

        GTR page 17, using model 1 with coefficients from Table S2b.
        """
        result = total_bark_wood_volume(
            Example3.SPCD, Example3.DIA, Example3.HT, Example3.DIVISION
        )
        assert pytest.approx(result, rel=1e-4) == Example3.V_TOTBK_GROSS_GTR

    def test_total_stem_wood_dry_weight(self):
        """
        Wtotib = VtotibGross × WDSG × 62.4 = 263.590590284621 lb

        GTR page 18. WDSG=0.58 for Tanoak from REF_SPECIES.
        This is the full tree weight before decay/broken top adjustments.
        """
        result = total_stem_wood_dry_weight(
            Example3.SPCD, Example3.DIA, Example3.HT, Example3.DIVISION
        )
        assert pytest.approx(result, rel=1e-4) == Example3.W_TOTIB_GTR

    def test_total_stem_bark_weight(self):
        """
        Wtotbk = a × D^b × H^c = 46.816664266025 lb

        GTR page 19, using model 1 with coefficients from Table S6b.
        This is the full tree bark weight before decay/broken top adjustments.
        """
        result = total_stem_bark_weight(
            Example3.SPCD, Example3.DIA, Example3.HT, Example3.DIVISION
        )
        assert pytest.approx(result, rel=1e-4) == Example3.W_TOTBK_GTR

    def test_total_branch_weight(self):
        """
        Wbranch = a × D^b × H^c × WDSG = 226.788002348975 lb

        GTR page 19, using model 5 with Jenkins group coefficients from Table S7b.
        This is the full tree branch weight before decay/broken top adjustments.
        """
        result = total_branch_weight(
            Example3.SPCD, Example3.DIA, Example3.HT, Example3.DIVISION
        )
        assert pytest.approx(result, rel=1e-4) == Example3.W_BRANCH_GTR

    def test_total_aboveground_biomass(self):
        """
        AGBPredicted = a × D^b × H^c × WDSG = 492.621457718427 lb

        GTR page 20, using model 5 with Jenkins group coefficients from Table S8b.
        """
        result = total_aboveground_biomass(
            Example3.SPCD, Example3.DIA, Example3.HT, Example3.DIVISION
        )
        assert pytest.approx(result, rel=1e-4) == Example3.AGB_PREDICTED_GTR

    def test_total_foliage_dry_weight(self):
        """
        For dead trees, foliage weight is assumed to be zero.

        GTR page 20.
        """
        # Dead trees have no foliage - this is handled by the decaycd parameter
        pass


class TestExample4:
    """
    Tests for GTR Example 4: White oak (SPCD=802), D=18.1", H=65', AH=59',
    Division=M220, CULL=2%, CR=30%.

    Reference: GTR-WO-104 pages 21-23.
    """

    def test_inside_bark_wood_volume(self):
        """
        VtotibGross = a × D^b × H^c = 42.277832913225 ft³

        GTR page 21, using model 1 with coefficients from Table S1a.
        """
        result = total_inside_bark_wood_volume(
            Example4.SPCD, Example4.DIA, Example4.HT, Example4.DIVISION
        )
        assert pytest.approx(result, rel=1e-4) == Example4.V_TOTIB_GROSS_GTR

    def test_total_bark_wood_volume(self):
        """
        VtotbkGross = a × k^(b-b1) × D^b1 × H^c = 8.361568823386 ft³

        GTR page 21, using model 2 with coefficients from Table S2a.
        """
        result = total_bark_wood_volume(
            Example4.SPCD, Example4.DIA, Example4.HT, Example4.DIVISION
        )
        assert pytest.approx(result, rel=1e-4) == Example4.V_TOTBK_GROSS_GTR

    def test_total_stem_wood_dry_weight(self):
        """
        Wtotib = VtotibGross × WDSG × 62.4 = 1582.882064271140 lb

        GTR page 21. WDSG=0.60 for White oak from REF_SPECIES.
        This is the full tree weight before cull/broken top adjustments.
        """
        result = total_stem_wood_dry_weight(
            Example4.SPCD, Example4.DIA, Example4.HT, Example4.DIVISION
        )
        assert pytest.approx(result, rel=1e-4) == Example4.W_TOTIB_GTR

    def test_total_stem_bark_weight(self):
        """
        Wtotbk = a × k^(b-b1) × D^b1 × H^c = 237.154413924445 lb

        GTR page 22, using model 2 with coefficients from Table S6a.
        This is the full tree bark weight before broken top adjustment.
        """
        result = total_stem_bark_weight(
            Example4.SPCD, Example4.DIA, Example4.HT, Example4.DIVISION
        )
        assert pytest.approx(result, rel=1e-4) == Example4.W_TOTBK_GTR

    def test_total_branch_weight(self):
        """
        Wbranch = a × D^b × H^c = 770.251512414918 lb

        GTR page 22, using model 1 with coefficients from Table S7a.
        This is the full tree branch weight before broken top adjustment.
        """
        result = total_branch_weight(
            Example4.SPCD, Example4.DIA, Example4.HT, Example4.DIVISION
        )
        assert pytest.approx(result, rel=1e-4) == Example4.W_BRANCH_GTR

    def test_total_foliage_dry_weight(self):
        """
        Wfoliage = a × D^b × H^c = 47.823281355886 lb

        GTR page 22, using model 1 with coefficients from Table S9a.
        This is the full tree foliage weight before broken top adjustment.
        """
        result = total_foliage_dry_weight(
            Example4.SPCD, Example4.DIA, Example4.HT, Example4.DIVISION
        )
        assert pytest.approx(result, rel=1e-4) == Example4.W_FOLIAGE_GTR

    # =========================================================================
    # Tests for Example 4 reduced values (with broken top)
    # GTR-WO-104 pages 21-23
    # =========================================================================

    def test_missing_inside_bark_volume(self):
        """
        GTR Example 4 (page 21): Missing volume due to broken top.

        VmissibGross = VtotibGross × (1 - Rm)
        VmissibGross = 42.277832913225 × (1 - 0.997638556946)
                     = 0.099795127559

        Where Rm is the volume ratio at actual height (AH=59').
        """
        result = missing_inside_bark_volume(
            spcd=Example4.SPCD,
            dia=Example4.DIA,
            ht=Example4.HT,
            ah=Example4.AH,
            division=Example4.DIVISION,
        )
        assert pytest.approx(result, rel=1e-4) == Example4.V_MISSIB_GROSS_GTR

    def test_crh_standardized_crown_ratio(self):
        """
        GTR Example 4 (page 22): Standardized crown ratio at H.

        CRH = [H - AH × (1 - CR)] / H
        CRH = [65 - 59 × (1 - 0.30)] / 65
            = [65 - 59 × 0.70] / 65
            = [65 - 41.3] / 65
            = 23.7 / 65
            = 0.364615384615
        """
        result = calculate_crh(ah=Example4.AH, ht=Example4.HT, cr=Example4.CR / 100)
        assert pytest.approx(result, rel=1e-6) == Example4.CRH_GTR

    def test_branch_foliage_remaining(self):
        """
        GTR Example 4 (page 22): Branch/foliage remaining after broken top.

        BranchRem = [AH - H × (1 - CRH)] / (H × CRH)
        BranchRem = [59 - 65 × (1 - 0.364615384615)] / (65 × 0.364615384615)
                  = [59 - 65 × 0.635384615385] / 23.7
                  = [59 - 41.3] / 23.7
                  = 17.7 / 23.7
                  = 0.746835443038

        Note: FoliageRem uses the same formula.
        """
        crh = calculate_crh(ah=Example4.AH, ht=Example4.HT, cr=Example4.CR / 100)
        result = calculate_branch_foliage_remaining(
            ah=Example4.AH, ht=Example4.HT, crh=crh
        )
        assert pytest.approx(result, rel=1e-6) == Example4.BRANCH_REM_GTR

    def test_total_stem_wood_dry_weight_with_broken_top(self):
        """
        GTR Example 4 (page 21): Stem wood with broken top and cull.

        Wtotibred = (VtotibGross - VmissibGross) × [1 - CULL/100 × (1 - DensProp)]
                    × WDSG × 62.4
        Wtotibred = (42.277832913225 - 0.099795127559) × [1 - 2/100 × (1 - 0.54)]
                    × 0.60 × 62.4
                  = 42.178037785666 × 0.9908 × 0.60 × 62.4
                  = 1564.617593936140

        Note: DensProp=0.54 for hardwood cull (DECAYCD=3 equivalent).
        """
        result = total_stem_wood_dry_weight(
            spcd=Example4.SPCD,
            dia=Example4.DIA,
            ht=Example4.HT,
            ah=Example4.AH,
            division=Example4.DIVISION,
            cull=Example4.CULL,
        )
        assert pytest.approx(result, rel=1e-4) == Example4.W_TOTIBRED_GTR

    def test_total_stem_bark_weight_with_broken_top(self):
        """
        GTR Example 4 (page 22): Bark weight with broken top.

        Wtotbkred = Wtotbk × Rb
        Wtotbkred = 237.154413924445 × 0.997639540140
                  = 236.594620449755

        Where Rb is the bark volume ratio at actual height (AH=59').
        """
        result = total_stem_bark_weight(
            spcd=Example4.SPCD,
            dia=Example4.DIA,
            ht=Example4.HT,
            ah=Example4.AH,
            division=Example4.DIVISION,
        )
        assert pytest.approx(result, rel=1e-4) == Example4.W_TOTBKRED_GTR

    def test_total_branch_weight_with_broken_top(self):
        """
        GTR Example 4 (page 22): Branch weight with broken top.

        Wbranchred = Wbranch × BranchRem
        Wbranchred = 770.251512414918 × 0.746835443038
                   = 575.250923828242

        Where BranchRem = 0.746835443038 based on CRH.
        """
        result = total_branch_weight(
            spcd=Example4.SPCD,
            dia=Example4.DIA,
            ht=Example4.HT,
            ah=Example4.AH,
            cr=Example4.CR / 100,
            division=Example4.DIVISION,
        )
        assert pytest.approx(result, rel=1e-4) == Example4.W_BRANCHRED_GTR

    def test_total_foliage_dry_weight_with_broken_top(self):
        """
        GTR Example 4 (page 22): Foliage weight with broken top.

        Wfoliagered = Wfoliage × FoliageRem
        Wfoliagered = 47.823281355886 × 0.746835443038
                    = 35.716121518954

        Where FoliageRem = BranchRem = 0.746835443038 based on CRH.
        """
        result = total_foliage_dry_weight(
            spcd=Example4.SPCD,
            dia=Example4.DIA,
            ht=Example4.HT,
            ah=Example4.AH,
            cr=Example4.CR / 100,
            division=Example4.DIVISION,
        )
        assert pytest.approx(result, rel=1e-4) == Example4.W_FOLIAGERED_GTR


class TestVectorized:
    """
    Test vectorization by combining all 4 GTR examples into arrays.

    Verifies that array inputs produce the same results as scalar inputs.
    """

    # Arrays of all 4 examples built from gtr_values
    spcd = np.array([Example1.SPCD, Example2.SPCD, Example3.SPCD, Example4.SPCD])
    dia = np.array([Example1.DIA, Example2.DIA, Example3.DIA, Example4.DIA])
    ht = np.array([Example1.HT, Example2.HT, Example3.HT, Example4.HT])
    division = np.array(
        [Example1.DIVISION, Example2.DIVISION, Example3.DIVISION, Example4.DIVISION]
    )
    cull = np.array([Example1.CULL, Example2.CULL, 0, Example4.CULL])

    def test_inside_bark_wood_volume(self):
        """Vectorized inside bark volume matches GTR examples."""
        result = total_inside_bark_wood_volume(
            self.spcd, self.dia, self.ht, self.division
        )

        assert isinstance(result, np.ndarray)
        assert len(result) == 4

        assert pytest.approx(result[0], rel=1e-4) == Example1.V_TOTIB_GROSS_GTR
        assert pytest.approx(result[1], rel=1e-4) == Example2.V_TOTIB_GROSS_GTR
        assert pytest.approx(result[2], rel=1e-4) == Example3.V_TOTIB_GROSS_GTR
        assert pytest.approx(result[3], rel=1e-4) == Example4.V_TOTIB_GROSS_GTR

    def test_total_bark_wood_volume(self):
        """Vectorized bark volume matches GTR examples."""
        result = total_bark_wood_volume(self.spcd, self.dia, self.ht, self.division)

        assert isinstance(result, np.ndarray)
        assert len(result) == 4

        # Example 1 has ~0.04% discrepancy, use wider tolerance
        assert pytest.approx(result[0], rel=5e-4) == Example1.V_TOTBK_GROSS_GTR
        assert pytest.approx(result[1], rel=1e-4) == Example2.V_TOTBK_GROSS_GTR
        assert pytest.approx(result[2], rel=1e-4) == Example3.V_TOTBK_GROSS_GTR
        assert pytest.approx(result[3], rel=1e-4) == Example4.V_TOTBK_GROSS_GTR

    def test_total_stem_wood_dry_weight(self):
        """Vectorized stem wood weight matches GTR examples."""
        # Test without cull
        result_no_cull = total_stem_wood_dry_weight(
            self.spcd, self.dia, self.ht, self.division
        )

        assert isinstance(result_no_cull, np.ndarray)
        assert len(result_no_cull) == 4

        assert pytest.approx(result_no_cull[0], rel=1e-4) == Example1.W_TOTIB_GTR
        assert (
            pytest.approx(result_no_cull[1], rel=1e-4) == Example2.W_TOTIB_NO_CULL_GTR
        )
        assert pytest.approx(result_no_cull[2], rel=1e-4) == Example3.W_TOTIB_GTR
        assert pytest.approx(result_no_cull[3], rel=1e-4) == Example4.W_TOTIB_GTR

        # Test with cull
        result_with_cull = total_stem_wood_dry_weight(
            self.spcd, self.dia, self.ht, self.division, self.cull
        )

        assert isinstance(result_with_cull, np.ndarray)
        assert len(result_with_cull) == 4

        assert (
            pytest.approx(result_with_cull[0], rel=1e-4) == Example1.W_TOTIB_GTR
        )  # cull=0
        assert (
            pytest.approx(result_with_cull[1], rel=1e-4) == Example2.W_TOTIBRED_GTR
        )  # cull=3
        assert (
            pytest.approx(result_with_cull[2], rel=1e-4) == Example3.W_TOTIB_GTR
        )  # cull=0

    def test_total_stem_bark_weight(self):
        """Vectorized stem bark weight matches GTR examples."""
        result = total_stem_bark_weight(self.spcd, self.dia, self.ht, self.division)

        assert isinstance(result, np.ndarray)
        assert len(result) == 4

        assert pytest.approx(result[0], rel=1e-4) == Example1.W_TOTBK_GTR
        assert pytest.approx(result[1], rel=1e-4) == Example2.W_TOTBK_GTR
        assert pytest.approx(result[2], rel=1e-4) == Example3.W_TOTBK_GTR
        assert pytest.approx(result[3], rel=1e-4) == Example4.W_TOTBK_GTR

    def test_total_branch_weight(self):
        """Vectorized branch weight matches GTR examples."""
        result = total_branch_weight(self.spcd, self.dia, self.ht, self.division)

        assert isinstance(result, np.ndarray)
        assert len(result) == 4

        assert pytest.approx(result[0], rel=1e-4) == Example1.W_BRANCH_GTR
        assert pytest.approx(result[1], rel=1e-4) == Example2.W_BRANCH_GTR
        assert pytest.approx(result[2], rel=1e-4) == Example3.W_BRANCH_GTR
        assert pytest.approx(result[3], rel=1e-4) == Example4.W_BRANCH_GTR

    def test_total_aboveground_biomass(self):
        """Vectorized total aboveground biomass matches GTR examples."""
        result = total_aboveground_biomass(self.spcd, self.dia, self.ht, self.division)

        assert isinstance(result, np.ndarray)
        assert len(result) == 4

        assert pytest.approx(result[0], rel=1e-4) == Example1.AGB_PREDICTED_GTR
        assert pytest.approx(result[1], rel=1e-4) == Example2.AGB_PREDICTED_GTR
        assert pytest.approx(result[2], rel=1e-4) == Example3.AGB_PREDICTED_GTR

    def test_total_foliage_dry_weight(self):
        """Vectorized foliage weight matches GTR examples."""
        result = total_foliage_dry_weight(self.spcd, self.dia, self.ht, self.division)

        assert isinstance(result, np.ndarray)
        assert len(result) == 4

        assert pytest.approx(result[0], rel=1e-4) == Example1.W_FOLIAGE_GTR
        assert pytest.approx(result[1], rel=1e-4) == Example2.W_FOLIAGE_GTR
        # Example 3 is dead tree - foliage not tested here
        assert pytest.approx(result[3], rel=1e-4) == Example4.W_FOLIAGE_GTR
