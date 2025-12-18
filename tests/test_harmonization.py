"""
Tests for component harmonization (GTR-WO-104 Steps 11-12).

Component harmonization ensures that stem wood + bark + branches = total AGB.
"""

import numpy as np
import pytest

from nsvb.estimators import (
    total_inside_bark_wood_volume,
    total_stem_wood_dry_weight,
    total_stem_bark_weight,
    total_branch_weight,
    total_aboveground_biomass,
    harmonize_components,
)

from .gtr_values import Example1, Example2, Example4


class TestHarmonizationExample1:
    """
    Tests for component harmonization using Example 1 from GTR.

    Example 1: Douglas-fir (SPCD=202), D=20.0", H=110', Division=240, no cull

    From GTR pages 10-11:
    - Wtotib = 2483.739897283610 lb
    - Wtotbk = 361.782496100100 lb
    - Wbranch = 277.487756904646 lb
    - AGBPredicted = 3154.5539926725 lb

    After harmonization:
    - WoodHarmonized = 2508.826815376370 lb
    - BarkHarmonized = 365.436666110811 lb
    - BranchHarmonized = 280.290511185328 lb
    """

    def test_component_weights_before_harmonization(self):
        """Verify component weight predictions match GTR Example 1."""
        # Stem wood weight
        w_wood = total_stem_wood_dry_weight(
            spcd=Example1.SPCD, dia=Example1.DIA, ht=Example1.HT, division=Example1.DIVISION
        )
        assert pytest.approx(w_wood, rel=1e-4) == Example1.W_TOTIB_GTR

        # Stem bark weight
        w_bark = total_stem_bark_weight(
            spcd=Example1.SPCD, dia=Example1.DIA, ht=Example1.HT, division=Example1.DIVISION
        )
        assert pytest.approx(w_bark, rel=1e-4) == Example1.W_TOTBK_GTR

        # Branch weight
        w_branch = total_branch_weight(
            spcd=Example1.SPCD, dia=Example1.DIA, ht=Example1.HT, division=Example1.DIVISION
        )
        assert pytest.approx(w_branch, rel=1e-4) == Example1.W_BRANCH_GTR

        # Predicted AGB
        agb_pred = total_aboveground_biomass(
            spcd=Example1.SPCD, dia=Example1.DIA, ht=Example1.HT, division=Example1.DIVISION
        )
        assert pytest.approx(agb_pred, rel=1e-4) == Example1.AGB_PREDICTED_GTR

    def test_harmonize_components(self):
        """
        Test component harmonization per GTR Steps 11-12.

        GTR Example 1 calculations (pages 10-11):
        AGBComponentred = 2483.739897283610 + 361.782496100100 + 277.487756904646
                        = 3123.010150288360

        AGBReduce = 3123.010150288360 / 3123.010150288360 = 1.0 (no cull/broken top)

        AGBPredictedred = 3154.5539926725 × 1.0 = 3154.5539926725

        WoodHarmonized = 3154.5539926725 × (2483.739897283610 / 3123.010150288360)
                       = 2508.826815376370

        BarkHarmonized = 3154.5539926725 × (361.782496100100 / 3123.010150288360)
                       = 365.436666110811

        BranchHarmonized = 3154.5539926725 × (277.487756904646 / 3123.010150288360)
                        = 280.290511185328
        """
        result = harmonize_components(
            spcd=Example1.SPCD,
            dia=Example1.DIA,
            ht=Example1.HT,
            division=Example1.DIVISION,
        )

        # Check harmonized values match GTR Example 1
        assert pytest.approx(result["wood"], rel=1e-4) == Example1.WOOD_HARMONIZED_GTR
        assert pytest.approx(result["bark"], rel=1e-4) == Example1.BARK_HARMONIZED_GTR
        assert pytest.approx(result["branch"], rel=1e-4) == Example1.BRANCH_HARMONIZED_GTR
        assert pytest.approx(result["agb"], rel=1e-4) == Example1.AGB_PREDICTED_GTR

    def test_harmonized_components_sum_to_agb(self):
        """
        Verify that harmonized components sum to predicted AGB.

        This is the key property of harmonization (GTR Step 12).
        """
        result = harmonize_components(
            spcd=Example1.SPCD,
            dia=Example1.DIA,
            ht=Example1.HT,
            division=Example1.DIVISION,
        )

        component_sum = result["wood"] + result["bark"] + result["branch"]
        assert pytest.approx(component_sum, rel=1e-6) == result["agb"]


class TestHarmonizationExample2:
    """
    Tests for component harmonization using Example 2 from GTR.

    Example 2: Red maple (SPCD=316), D=11.1", H=38', Division=M210, CULL=3%

    From GTR pages 14-15:
    - Wtotibred = 284.265641364256 lb (reduced for cull)
    - Wtotbkred = 52.945466015848 lb
    - Wbranchred = 135.001927997271 lb
    - AGBPredicted = 532.584798820042 lb

    AGBComponentred = 472.213035377375 lb
    AGBReduce = 0.991646711840
    AGBPredictedred = 528.135964525863 lb

    After harmonization:
    - WoodHarmonized = 317.930462388645 lb
    - BarkHarmonized = 59.215656211618 lb
    - BranchHarmonized = 150.989845925600 lb
    """

    def test_harmonize_components_with_cull(self):
        """
        Test component harmonization with cull deduction.

        GTR Example 2 (pages 14-15).
        """
        result = harmonize_components(
            spcd=Example2.SPCD,
            dia=Example2.DIA,
            ht=Example2.HT,
            division=Example2.DIVISION,
            cull=Example2.CULL,
        )

        # Check harmonized values match GTR Example 2
        assert pytest.approx(result["wood"], rel=1e-4) == Example2.WOOD_HARMONIZED_GTR
        assert pytest.approx(result["bark"], rel=1e-4) == Example2.BARK_HARMONIZED_GTR
        assert pytest.approx(result["branch"], rel=1e-4) == Example2.BRANCH_HARMONIZED_GTR
        assert pytest.approx(result["agb"], rel=1e-4) == Example2.AGB_PREDICTED_RED_GTR

    def test_harmonized_components_sum_to_reduced_agb(self):
        """
        Verify harmonized components sum to reduced AGB.
        """
        result = harmonize_components(
            spcd=Example2.SPCD,
            dia=Example2.DIA,
            ht=Example2.HT,
            division=Example2.DIVISION,
            cull=Example2.CULL,
        )

        component_sum = result["wood"] + result["bark"] + result["branch"]
        assert pytest.approx(component_sum, rel=1e-6) == result["agb"]


class TestHarmonizationExample4:
    """
    Tests for component harmonization using Example 4 from GTR.

    Example 4: White oak (SPCD=802), D=18.1", H=65', AH=59', Division=M220, CULL=2%

    This tests harmonization with cull (no broken top in harmonization).
    """

    def test_component_weights_before_harmonization(self):
        """Verify component weight predictions for Example 4."""
        # Stem wood weight
        w_wood = total_stem_wood_dry_weight(
            spcd=Example4.SPCD, dia=Example4.DIA, ht=Example4.HT, division=Example4.DIVISION
        )
        # GTR page 21: Wtotib = 1582.882064271140
        assert pytest.approx(w_wood, rel=1e-4) == Example4.W_TOTIB_GTR

        # Stem bark weight
        w_bark = total_stem_bark_weight(
            spcd=Example4.SPCD, dia=Example4.DIA, ht=Example4.HT, division=Example4.DIVISION
        )
        # GTR page 22: Wtotbk = 237.154413924445
        assert pytest.approx(w_bark, rel=1e-4) == Example4.W_TOTBK_GTR

        # Branch weight
        w_branch = total_branch_weight(
            spcd=Example4.SPCD, dia=Example4.DIA, ht=Example4.HT, division=Example4.DIVISION
        )
        # GTR page 22: Wbranch = 770.251512414918
        assert pytest.approx(w_branch, rel=1e-4) == Example4.W_BRANCH_GTR

    def test_harmonize_components_with_cull(self):
        """
        Test component harmonization with cull deduction.

        Note: Example 4 has a broken top but the harmonization calculation
        in the GTR doesn't include broken top adjustments in the base case.
        """
        result = harmonize_components(
            spcd=Example4.SPCD,
            dia=Example4.DIA,
            ht=Example4.HT,
            division=Example4.DIVISION,
            cull=Example4.CULL,
        )

        # Check that components sum to AGB
        component_sum = result["wood"] + result["bark"] + result["branch"]
        assert pytest.approx(component_sum, rel=1e-6) == result["agb"]

        # Verify AGB is reduced from no-cull prediction
        agb_no_cull = total_aboveground_biomass(
            spcd=Example4.SPCD, dia=Example4.DIA, ht=Example4.HT, division=Example4.DIVISION
        )
        assert result["agb"] < agb_no_cull

    def test_harmonized_components_sum_to_reduced_agb(self):
        """
        Verify harmonized components sum to reduced AGB.
        """
        result = harmonize_components(
            spcd=Example4.SPCD,
            dia=Example4.DIA,
            ht=Example4.HT,
            division=Example4.DIVISION,
            cull=Example4.CULL,
        )

        component_sum = result["wood"] + result["bark"] + result["branch"]
        assert pytest.approx(component_sum, rel=1e-6) == result["agb"]


class TestHarmonizationVectorized:
    """
    Tests for vectorized component harmonization.
    """

    def test_harmonize_components_vectorized(self):
        """
        Test that harmonize_components works with array inputs.
        """
        spcd = np.array([Example1.SPCD, Example2.SPCD])
        dia = np.array([Example1.DIA, Example2.DIA])
        ht = np.array([Example1.HT, Example2.HT])
        division = np.array([Example1.DIVISION, Example2.DIVISION])
        cull = np.array([Example1.CULL, Example2.CULL])

        result = harmonize_components(
            spcd=spcd,
            dia=dia,
            ht=ht,
            division=division,
            cull=cull,
        )

        # Check array results
        assert isinstance(result["wood"], np.ndarray)
        assert len(result["wood"]) == 2

        # Example 1 values (no cull)
        assert pytest.approx(result["wood"][0], rel=1e-4) == Example1.WOOD_HARMONIZED_GTR
        assert pytest.approx(result["bark"][0], rel=1e-4) == Example1.BARK_HARMONIZED_GTR
        assert pytest.approx(result["branch"][0], rel=1e-4) == Example1.BRANCH_HARMONIZED_GTR

        # Example 2 values (with cull)
        assert pytest.approx(result["wood"][1], rel=1e-4) == Example2.WOOD_HARMONIZED_GTR
        assert pytest.approx(result["bark"][1], rel=1e-4) == Example2.BARK_HARMONIZED_GTR
        assert pytest.approx(result["branch"][1], rel=1e-4) == Example2.BRANCH_HARMONIZED_GTR
