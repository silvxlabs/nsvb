"""
Tests for carbon calculations (GTR-WO-104 Step 13).

Carbon content = Biomass × Carbon fraction

For live trees: Carbon fraction from Table S10a (species-specific)
For dead trees: Carbon fraction from Table S10b based on decay class and wood type
"""

import numpy as np
import pytest

from nsvb.estimators import (
    total_aboveground_biomass,
    harmonize_components,
    get_carbon_fraction,
    calculate_carbon,
)

from .gtr_values import (
    Example1, Example2, Example4,
    CarbonFractionsLive,
)


class TestCarbonFractionLive:
    """
    Tests for live tree carbon fraction lookups from Table S10a.
    """

    def test_douglas_fir_carbon_fraction(self):
        """
        Douglas-fir (SPCD=202) carbon fraction.
        From Table S10a: fia.wood.c = 51.55958333%
        """
        result = get_carbon_fraction(spcd=Example1.SPCD)
        assert pytest.approx(result, rel=1e-6) == CarbonFractionsLive.SPCD_202

    def test_red_maple_carbon_fraction(self):
        """
        Red maple (SPCD=316) carbon fraction.
        From Table S10a: fia.wood.c = 48.57333333%
        """
        result = get_carbon_fraction(spcd=Example2.SPCD)
        assert pytest.approx(result, rel=1e-6) == CarbonFractionsLive.SPCD_316

    def test_tanoak_carbon_fraction(self):
        """
        Tanoak (SPCD=631) carbon fraction.
        From Table S10a: fia.wood.c = 47.27%
        """
        result = get_carbon_fraction(spcd=631)
        assert pytest.approx(result, rel=1e-6) == CarbonFractionsLive.SPCD_631


class TestCarbonFractionDead:
    """
    Tests for dead tree carbon fraction lookups from Table S10b.

    Table S10b values:
    Hardwood DECAYCD 1: 47.0% -> 0.47
    Hardwood DECAYCD 2: 47.3% -> 0.473
    Hardwood DECAYCD 3: 48.1% -> 0.481
    Hardwood DECAYCD 4: 48.0% -> 0.48
    Hardwood DECAYCD 5: 47.2% -> 0.472

    Softwood DECAYCD 1: 50.1% -> 0.501
    Softwood DECAYCD 2: 50.4% -> 0.504
    Softwood DECAYCD 3: 50.6% -> 0.506
    Softwood DECAYCD 4: 52.0% -> 0.52
    Softwood DECAYCD 5: 52.7% -> 0.527
    """

    def test_hardwood_decay_class_2(self):
        """Test hardwood dead tree DECAYCD=2 carbon fraction."""
        # SPCD=316 (Red maple) is hardwood, decay class 2
        result = get_carbon_fraction(spcd=316, decaycd=2)
        assert result == 0.473

    def test_softwood_decay_class_2(self):
        """Test softwood dead tree DECAYCD=2 carbon fraction."""
        # SPCD=202 (Douglas-fir) is softwood, decay class 2
        result = get_carbon_fraction(spcd=202, decaycd=2)
        assert result == 0.504

    def test_hardwood_decay_class_5(self):
        """Test hardwood dead tree DECAYCD=5 carbon fraction."""
        result = get_carbon_fraction(spcd=631, decaycd=5)
        assert pytest.approx(result, rel=1e-6) == 0.472

    def test_softwood_decay_class_5(self):
        """Test softwood dead tree DECAYCD=5 carbon fraction."""
        result = get_carbon_fraction(spcd=202, decaycd=5)
        assert result == 0.527


class TestCarbonExample1:
    """
    Tests for carbon calculations using Example 1 from GTR.

    Example 1: Douglas-fir (SPCD=202), D=20.0", H=110', Division=240
    AGBPredicted = 3154.5539926725 lb
    Carbon fraction from Table S10a = 0.5155958333

    Carbon = AGBPredicted × Carbon_fraction
           = 3154.5539926725 × 0.5155958333 = ~1626.47 lb
    """

    def test_agb_carbon(self):
        """
        Test carbon content calculation from total AGB.

        Carbon = AGB × Carbon_fraction
        """
        agb = total_aboveground_biomass(
            spcd=Example1.SPCD, dia=Example1.DIA, ht=Example1.HT, division=Example1.DIVISION
        )
        # Verify AGB matches GTR Example 1
        assert pytest.approx(agb, rel=1e-4) == Example1.AGB_PREDICTED_GTR

        result = calculate_carbon(
            spcd=Example1.SPCD, dia=Example1.DIA, ht=Example1.HT, division=Example1.DIVISION
        )
        # Carbon = AGB × Carbon_fraction from Table S10a
        expected = Example1.AGB_PREDICTED_GTR * CarbonFractionsLive.SPCD_202
        assert pytest.approx(result, rel=1e-4) == expected


class TestCarbonExample2:
    """
    Tests for carbon calculations using Example 2 from GTR.

    Example 2: Red maple (SPCD=316), D=11.1", H=38', Division=M210, CULL=3%
    AGBPredictedred = 528.135964525863 lb (reduced for cull)
    Carbon fraction from Table S10a = 0.48573333329999996

    Carbon = AGBPredictedred × Carbon_fraction
           = 528.135964525863 × 0.48573333 = ~256.53 lb
    """

    def test_agb_carbon_with_cull(self):
        """
        Test carbon content with cull deduction.

        Uses harmonized/reduced AGB from harmonize_components.
        """
        result = calculate_carbon(
            spcd=Example2.SPCD,
            dia=Example2.DIA,
            ht=Example2.HT,
            division=Example2.DIVISION,
            cull=Example2.CULL,
        )
        # Carbon = AGBPredictedred × Carbon_fraction from Table S10a
        expected = Example2.AGB_PREDICTED_RED_GTR * CarbonFractionsLive.SPCD_316
        assert pytest.approx(result, rel=1e-4) == expected


class TestCarbonExample4:
    """
    Tests for carbon calculations using Example 4 from GTR.

    Example 4: White oak (SPCD=802), D=18.1", H=65', AH=59', Division=M220, CULL=2%

    White oak carbon fraction from Table S10a = 0.49570000000000003
    """

    def test_carbon_fraction(self):
        """Test white oak carbon fraction from Table S10a."""
        result = get_carbon_fraction(spcd=Example4.SPCD)
        assert pytest.approx(result, rel=1e-6) == CarbonFractionsLive.SPCD_802

    def test_agb_carbon_with_cull(self):
        """
        Test carbon content with cull deduction (no broken top adjustment).

        Uses harmonized AGB with cull deduction but without broken top.
        """
        result = calculate_carbon(
            spcd=Example4.SPCD,
            dia=Example4.DIA,
            ht=Example4.HT,
            division=Example4.DIVISION,
            cull=Example4.CULL,
        )
        # Get harmonized AGB with cull
        harm = harmonize_components(
            spcd=Example4.SPCD,
            dia=Example4.DIA,
            ht=Example4.HT,
            division=Example4.DIVISION,
            cull=Example4.CULL,
        )
        expected = harm["agb"] * CarbonFractionsLive.SPCD_802
        assert pytest.approx(result, rel=1e-4) == expected


class TestCarbonVectorized:
    """
    Tests for vectorized carbon calculations.
    """

    def test_carbon_vectorized(self):
        """Test that calculate_carbon works with array inputs."""
        spcd = np.array([Example1.SPCD, Example2.SPCD])
        dia = np.array([Example1.DIA, Example2.DIA])
        ht = np.array([Example1.HT, Example2.HT])
        division = np.array([Example1.DIVISION, Example2.DIVISION])
        cull = np.array([Example1.CULL, Example2.CULL])

        result = calculate_carbon(
            spcd=spcd, dia=dia, ht=ht, division=division, cull=cull
        )

        assert isinstance(result, np.ndarray)
        assert len(result) == 2

        # Example 1: Carbon = AGB × Carbon_fraction from Table S10a
        assert pytest.approx(result[0], rel=1e-4) == Example1.AGB_PREDICTED_GTR * CarbonFractionsLive.SPCD_202

        # Example 2: Carbon = AGBred × Carbon_fraction from Table S10a
        assert pytest.approx(result[1], rel=1e-4) == Example2.AGB_PREDICTED_RED_GTR * CarbonFractionsLive.SPCD_316

    def test_carbon_fraction_vectorized(self):
        """Test that get_carbon_fraction works with array inputs."""
        spcd = np.array([Example1.SPCD, Example2.SPCD, 631])
        result = get_carbon_fraction(spcd=spcd)

        assert isinstance(result, np.ndarray)
        assert len(result) == 3
        assert pytest.approx(result[0], rel=1e-6) == CarbonFractionsLive.SPCD_202  # Douglas-fir
        assert pytest.approx(result[1], rel=1e-6) == CarbonFractionsLive.SPCD_316  # Red maple
        assert pytest.approx(result[2], rel=1e-6) == CarbonFractionsLive.SPCD_631  # Tanoak
