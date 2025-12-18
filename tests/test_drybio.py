"""
Tests for DRYBIO calculations (GTR-WO-104 Step 14).

DRYBIO calculations partition stem wood biomass into components:
- DRYBIO_STUMP: Biomass from ground to 1-foot stump height
- DRYBIO_BOLE: Biomass from 1-foot stump to 4-inch top diameter
- DRYBIO_TOP: Biomass from 4-inch top to tip of tree
- DRYBIO_SAPLING: Total stem biomass for saplings (D < 5 inches)
- DRYBIO_WDLD_SPP: Total AGB for woodland species
"""

import numpy as np
import pytest

from nsvb.estimators import (
    total_stem_wood_dry_weight,
    volume_ratio,
    merchantable_height,
    drybio_stump,
    drybio_bole,
    drybio_top,
    drybio_sapling,
    drybio_wdld_spp,
    total_aboveground_biomass,
)

from .gtr_values import Example1, Example2, Example3, Example4


class TestDrybioExample1:
    """
    Tests for DRYBIO calculations using Example 1 from GTR.

    Example 1: Douglas-fir (SPCD=202), D=20.0", H=110', Division=240
    Wtotib = 2483.739897283610 lb (total stem wood dry weight)

    Volume ratios from test_volume_ratio.py:
    - R1 (at 1') = 0.024198309503
    - Rm (at 98.28') = 0.993412209437

    Expected DRYBIO components:
    - DRYBIO_STUMP = R1 × Wtotib = 0.024198309503 × 2483.739897 = 60.11 lb
    - DRYBIO_BOLE = (Rm - R1) × Wtotib = 0.969213899934 × 2483.739897 = 2407.24 lb
    - DRYBIO_TOP = (1 - Rm) × Wtotib = 0.006587790563 × 2483.739897 = 16.36 lb
    """

    def test_drybio_stump(self):
        """
        DRYBIO_STUMP = R1 × Wstemwd

        R1 = 0.024198309503
        Wstemwd = 2483.739897283610 lb
        Expected = 60.11 lb
        """
        result = drybio_stump(
            spcd=Example1.SPCD, dia=Example1.DIA, ht=Example1.HT, division=Example1.DIVISION
        )
        # R1 × Wstemwd
        expected = Example1.R1_GTR * Example1.W_TOTIB_GTR
        assert pytest.approx(result, rel=1e-4) == expected

    def test_drybio_bole(self):
        """
        DRYBIO_BOLE = (Rm - R1) × Wstemwd

        Rm = 0.993412209437
        R1 = 0.024198309503
        Wstemwd = 2483.739897283610 lb
        """
        result = drybio_bole(
            spcd=Example1.SPCD, dia=Example1.DIA, ht=Example1.HT, division=Example1.DIVISION
        )
        # (Rm - R1) × Wstemwd
        expected = (Example1.RM_GTR - Example1.R1_GTR) * Example1.W_TOTIB_GTR
        assert pytest.approx(result, rel=1e-4) == expected

    def test_drybio_top(self):
        """
        DRYBIO_TOP = (1 - Rm) × Wstemwd

        Rm = volume ratio at merchantable height
        Wstemwd = 2483.739897283610 lb
        """
        result = drybio_top(
            spcd=Example1.SPCD, dia=Example1.DIA, ht=Example1.HT, division=Example1.DIVISION
        )
        # Calculate using actual Rm
        hm = merchantable_height(Example1.SPCD, Example1.DIA, Example1.HT, Example1.DIVISION)
        rm = volume_ratio(Example1.SPCD, hm, Example1.HT, Example1.DIVISION, bark="ib")
        expected = (1 - rm) * Example1.W_TOTIB_GTR
        assert pytest.approx(result, rel=1e-4) == expected

    def test_components_sum_to_total(self):
        """
        DRYBIO_STUMP + DRYBIO_BOLE + DRYBIO_TOP should equal total stem weight.
        """
        stump = drybio_stump(
            spcd=Example1.SPCD, dia=Example1.DIA, ht=Example1.HT, division=Example1.DIVISION
        )
        bole = drybio_bole(
            spcd=Example1.SPCD, dia=Example1.DIA, ht=Example1.HT, division=Example1.DIVISION
        )
        top = drybio_top(
            spcd=Example1.SPCD, dia=Example1.DIA, ht=Example1.HT, division=Example1.DIVISION
        )
        total = total_stem_wood_dry_weight(
            spcd=Example1.SPCD, dia=Example1.DIA, ht=Example1.HT, division=Example1.DIVISION
        )

        assert pytest.approx(stump + bole + top, rel=1e-6) == total


class TestDrybioExample2:
    """
    Tests for DRYBIO with cull deduction using Example 2.

    Example 2: Red maple (SPCD=316), D=11.1", H=38', Division=M210, CULL=3%
    Wtotibred = 284.265641364256 lb (with cull)
    """

    def test_drybio_stump_with_cull(self):
        """DRYBIO_STUMP with cull deduction."""
        result = drybio_stump(
            spcd=Example2.SPCD,
            dia=Example2.DIA,
            ht=Example2.HT,
            division=Example2.DIVISION,
            cull=Example2.CULL,
        )
        # Should use reduced stem weight
        w_stem = total_stem_wood_dry_weight(
            spcd=Example2.SPCD,
            dia=Example2.DIA,
            ht=Example2.HT,
            division=Example2.DIVISION,
            cull=Example2.CULL,
        )
        r1 = volume_ratio(Example2.SPCD, 1.0, Example2.HT, Example2.DIVISION, bark="ib")
        expected = r1 * w_stem
        assert pytest.approx(result, rel=1e-6) == expected

    def test_components_sum_with_cull(self):
        """Components should sum to total reduced stem weight."""
        stump = drybio_stump(
            spcd=Example2.SPCD,
            dia=Example2.DIA,
            ht=Example2.HT,
            division=Example2.DIVISION,
            cull=Example2.CULL,
        )
        bole = drybio_bole(
            spcd=Example2.SPCD,
            dia=Example2.DIA,
            ht=Example2.HT,
            division=Example2.DIVISION,
            cull=Example2.CULL,
        )
        top = drybio_top(
            spcd=Example2.SPCD,
            dia=Example2.DIA,
            ht=Example2.HT,
            division=Example2.DIVISION,
            cull=Example2.CULL,
        )
        total = total_stem_wood_dry_weight(
            spcd=Example2.SPCD,
            dia=Example2.DIA,
            ht=Example2.HT,
            division=Example2.DIVISION,
            cull=Example2.CULL,
        )

        assert pytest.approx(stump + bole + top, rel=1e-6) == total


class TestDrybioExample3:
    """
    Tests for DRYBIO with dead tree (decay) using Example 3.

    Example 3: Dead tanoak (SPCD=631), D=11.3", H=28', Division=M240, DECAYCD=2
    """

    def test_drybio_stump_dead_tree(self):
        """DRYBIO_STUMP for dead tree with decay reduction."""
        result = drybio_stump(
            spcd=Example3.SPCD,
            dia=Example3.DIA,
            ht=Example3.HT,
            division=Example3.DIVISION,
            decaycd=Example3.DECAYCD,
        )
        # Should use decay-reduced stem weight
        w_stem = total_stem_wood_dry_weight(
            spcd=Example3.SPCD,
            dia=Example3.DIA,
            ht=Example3.HT,
            division=Example3.DIVISION,
            decaycd=Example3.DECAYCD,
        )
        r1 = volume_ratio(Example3.SPCD, 1.0, Example3.HT, Example3.DIVISION, bark="ib")
        expected = r1 * w_stem
        assert pytest.approx(result, rel=1e-6) == expected

    def test_components_sum_dead_tree(self):
        """Components should sum to total decay-reduced stem weight."""
        stump = drybio_stump(
            spcd=Example3.SPCD,
            dia=Example3.DIA,
            ht=Example3.HT,
            division=Example3.DIVISION,
            decaycd=Example3.DECAYCD,
        )
        bole = drybio_bole(
            spcd=Example3.SPCD,
            dia=Example3.DIA,
            ht=Example3.HT,
            division=Example3.DIVISION,
            decaycd=Example3.DECAYCD,
        )
        top = drybio_top(
            spcd=Example3.SPCD,
            dia=Example3.DIA,
            ht=Example3.HT,
            division=Example3.DIVISION,
            decaycd=Example3.DECAYCD,
        )
        total = total_stem_wood_dry_weight(
            spcd=Example3.SPCD,
            dia=Example3.DIA,
            ht=Example3.HT,
            division=Example3.DIVISION,
            decaycd=Example3.DECAYCD,
        )

        assert pytest.approx(stump + bole + top, rel=1e-6) == total


class TestDrybioBrokenTop:
    """
    Tests for DRYBIO with broken top (Example 4 scenario).

    Example 4: White oak (SPCD=802), D=18.1", H=65', AH=59', Division=M220
    """

    def test_drybio_bole_broken_top(self):
        """
        DRYBIO_BOLE with broken top should use min(ah, hm) as upper limit.

        If ah > hm, bole is same as full tree.
        If ah < hm, bole uses ah as upper limit.
        """
        hm = merchantable_height(Example4.SPCD, Example4.DIA, Example4.HT, Example4.DIVISION)

        result = drybio_bole(
            spcd=Example4.SPCD,
            dia=Example4.DIA,
            ht=Example4.HT,
            ah=Example4.AH,
            division=Example4.DIVISION,
        )

        # Get volume ratios
        r1 = volume_ratio(Example4.SPCD, 1.0, Example4.HT, Example4.DIVISION, bark="ib")

        # Use lesser of ah and hm
        h_upper = min(Example4.AH, hm)
        r_upper = volume_ratio(Example4.SPCD, h_upper, Example4.HT, Example4.DIVISION, bark="ib")

        w_stem = total_stem_wood_dry_weight(
            spcd=Example4.SPCD, dia=Example4.DIA, ht=Example4.HT, division=Example4.DIVISION
        )

        expected = (r_upper - r1) * w_stem
        assert pytest.approx(result, rel=1e-6) == expected

    def test_drybio_top_broken_above_merchantable(self):
        """
        If broken above merchantable height, top is partial.

        DRYBIO_TOP = (R(ah) - Rm) × Wstemwd
        """
        hm = merchantable_height(Example4.SPCD, Example4.DIA, Example4.HT, Example4.DIVISION)

        # This example has ah=59' which may be above or below hm depending on tree shape
        result = drybio_top(
            spcd=Example4.SPCD,
            dia=Example4.DIA,
            ht=Example4.HT,
            ah=Example4.AH,
            division=Example4.DIVISION,
        )

        if Example4.AH <= hm:
            # Broken below merchantable - no top
            assert result == 0.0
        else:
            # Broken above merchantable - partial top
            rm = volume_ratio(Example4.SPCD, hm, Example4.HT, Example4.DIVISION, bark="ib")
            r_ah = volume_ratio(Example4.SPCD, Example4.AH, Example4.HT, Example4.DIVISION, bark="ib")
            w_stem = total_stem_wood_dry_weight(
                spcd=Example4.SPCD, dia=Example4.DIA, ht=Example4.HT, division=Example4.DIVISION
            )
            expected = (r_ah - rm) * w_stem
            assert pytest.approx(result, rel=1e-6) == expected

    def test_drybio_top_broken_below_merchantable(self):
        """
        If broken below merchantable height, top biomass is 0.
        """
        # Use a very low ah that's definitely below merchantable height
        ah_low = 10.0  # 10 feet is typically below merchantable height

        result = drybio_top(
            spcd=Example4.SPCD,
            dia=Example4.DIA,
            ht=Example4.HT,
            ah=ah_low,
            division=Example4.DIVISION,
        )

        hm = merchantable_height(Example4.SPCD, Example4.DIA, Example4.HT, Example4.DIVISION)
        if ah_low <= hm:
            assert result == 0.0


class TestDrybioSapling:
    """Tests for DRYBIO_SAPLING calculations."""

    def test_drybio_sapling_equals_total_stem(self):
        """DRYBIO_SAPLING should equal total stem wood weight."""
        # Use a sapling (D < 5 inches)
        spcd = 202
        dia = 3.5
        ht = 25.0
        division = "240"

        result = drybio_sapling(spcd=spcd, dia=dia, ht=ht, division=division)
        expected = total_stem_wood_dry_weight(
            spcd=spcd, dia=dia, ht=ht, division=division
        )

        assert pytest.approx(result, rel=1e-6) == expected


class TestDrybioWoodlandSpecies:
    """Tests for DRYBIO_WDLD_SPP calculations."""

    def test_drybio_wdld_spp_equals_agb(self):
        """DRYBIO_WDLD_SPP should equal total AGB from Table S8."""
        # Use a typical species (any species works for this test)
        spcd = 202
        dia = 10.0
        ht = 40.0
        division = "240"

        result = drybio_wdld_spp(spcd=spcd, dia=dia, ht=ht, division=division)
        expected = total_aboveground_biomass(
            spcd=spcd, dia=dia, ht=ht, division=division
        )

        assert pytest.approx(result, rel=1e-6) == expected


class TestDrybioVectorized:
    """Tests for vectorized DRYBIO calculations."""

    def test_drybio_stump_vectorized(self):
        """Test drybio_stump with array inputs."""
        spcd = np.array([Example1.SPCD, Example2.SPCD])
        dia = np.array([Example1.DIA, Example2.DIA])
        ht = np.array([Example1.HT, Example2.HT])
        division = np.array([Example1.DIVISION, Example2.DIVISION])

        result = drybio_stump(spcd=spcd, dia=dia, ht=ht, division=division)

        assert isinstance(result, np.ndarray)
        assert len(result) == 2

        # Compare to scalar calculations
        for i in range(2):
            scalar_result = drybio_stump(
                spcd=spcd[i], dia=dia[i], ht=ht[i], division=division[i]
            )
            assert pytest.approx(result[i], rel=1e-6) == scalar_result

    def test_drybio_bole_vectorized(self):
        """Test drybio_bole with array inputs."""
        spcd = np.array([Example1.SPCD, Example2.SPCD])
        dia = np.array([Example1.DIA, Example2.DIA])
        ht = np.array([Example1.HT, Example2.HT])
        division = np.array([Example1.DIVISION, Example2.DIVISION])

        result = drybio_bole(spcd=spcd, dia=dia, ht=ht, division=division)

        assert isinstance(result, np.ndarray)
        assert len(result) == 2

    def test_drybio_top_vectorized(self):
        """Test drybio_top with array inputs."""
        spcd = np.array([Example1.SPCD, Example2.SPCD])
        dia = np.array([Example1.DIA, Example2.DIA])
        ht = np.array([Example1.HT, Example2.HT])
        division = np.array([Example1.DIVISION, Example2.DIVISION])

        result = drybio_top(spcd=spcd, dia=dia, ht=ht, division=division)

        assert isinstance(result, np.ndarray)
        assert len(result) == 2

    def test_vectorized_components_sum_to_total(self):
        """Vectorized components should sum to total stem weight."""
        spcd = np.array([Example1.SPCD, Example2.SPCD, Example4.SPCD])
        dia = np.array([Example1.DIA, Example2.DIA, Example4.DIA])
        ht = np.array([Example1.HT, Example2.HT, Example4.HT])
        division = np.array([Example1.DIVISION, Example2.DIVISION, Example4.DIVISION])

        stump = drybio_stump(spcd=spcd, dia=dia, ht=ht, division=division)
        bole = drybio_bole(spcd=spcd, dia=dia, ht=ht, division=division)
        top = drybio_top(spcd=spcd, dia=dia, ht=ht, division=division)
        total = total_stem_wood_dry_weight(spcd=spcd, dia=dia, ht=ht, division=division)

        np.testing.assert_allclose(stump + bole + top, total, rtol=1e-6)
