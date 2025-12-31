"""
Tests for sound volume calculations (GTR-WO-104 Step 6).

Sound volumes account for cull deductions in live trees and density
reductions in dead trees.
"""

import numpy as np
import pytest

from nsvb.estimators import (
    total_inside_bark_wood_volume,
    sound_inside_bark_volume,
    sound_merchantable_volume,
    sound_sawlog_volume,
    merchantable_volume,
    sawlog_volume,
)

from .gtr_values import Example1, Example2


class TestSoundVolumeExample2:
    """
    Tests for sound volume calculations using Example 2 from GTR.

    Example 2: Red maple (SPCD=316), D=11.1", H=38', Division=M210, CULL=3%

    From GTR page 13:
    VtotibSound = VtotibGross × (1 – CULL/100)
    """

    def test_sound_total_inside_bark_volume(self):
        """
        VtotibSound = VtotibGross × (1 – CULL/100)

        From GTR Example 2 (page 23):
        VtotibGross = 9.427112777611 (from test_examples.py)
        CULL = 3%

        VtotibSound = 9.427112777611 × (1 – 0.03) = 9.14430039428467

        Note: The GTR doesn't explicitly calculate VtotibSound, but the
        formula is given on page 13 (Step 6).
        """
        # First verify the gross volume matches GTR Example 2
        v_gross = total_inside_bark_wood_volume(
            spcd=Example2.SPCD,
            dia=Example2.DIA,
            ht=Example2.HT,
            division=Example2.DIVISION,
        )
        # GTR Example 2: VtotibGross
        assert pytest.approx(v_gross, rel=1e-4) == Example2.V_TOTIB_GROSS_GTR

        # Now test the sound volume
        result = sound_inside_bark_volume(
            spcd=Example2.SPCD,
            dia=Example2.DIA,
            ht=Example2.HT,
            division=Example2.DIVISION,
            cull=Example2.CULL,
        )

        # VtotibSound = VtotibGross × (1 – CULL/100)
        expected = Example2.V_TOTIB_GROSS_GTR * (1 - Example2.CULL / 100)
        assert pytest.approx(result, rel=1e-4) == expected

    def test_sound_volume_zero_cull(self):
        """
        When CULL=0, sound volume equals gross volume.
        """
        v_gross = total_inside_bark_wood_volume(
            spcd=Example2.SPCD,
            dia=Example2.DIA,
            ht=Example2.HT,
            division=Example2.DIVISION,
        )
        result = sound_inside_bark_volume(
            spcd=Example2.SPCD,
            dia=Example2.DIA,
            ht=Example2.HT,
            division=Example2.DIVISION,
            cull=0.0,
        )
        assert pytest.approx(result, rel=1e-6) == v_gross

    def test_sound_merchantable_volume(self):
        """
        VmeribSound = VmeribGross × (1 – CULL/100)
        """
        v_mer_gross = merchantable_volume(
            spcd=Example2.SPCD,
            dia=Example2.DIA,
            ht=Example2.HT,
            division=Example2.DIVISION,
            bark="ib",
        )
        result = sound_merchantable_volume(
            spcd=Example2.SPCD,
            dia=Example2.DIA,
            ht=Example2.HT,
            division=Example2.DIVISION,
            cull=Example2.CULL,
        )
        expected = v_mer_gross * (1 - Example2.CULL / 100)
        assert pytest.approx(result, rel=1e-4) == expected

    def test_sound_sawlog_volume(self):
        """
        VsawibSound = VsawibGross × (1 – CULL/100)
        """
        v_saw_gross = sawlog_volume(
            spcd=Example2.SPCD,
            dia=Example2.DIA,
            ht=Example2.HT,
            division=Example2.DIVISION,
            bark="ib",
        )
        result = sound_sawlog_volume(
            spcd=Example2.SPCD,
            dia=Example2.DIA,
            ht=Example2.HT,
            division=Example2.DIVISION,
            cull=Example2.CULL,
        )
        expected = v_saw_gross * (1 - Example2.CULL / 100)
        assert pytest.approx(result, rel=1e-4) == expected


class TestSoundVolumeVectorized:
    """
    Tests for vectorized sound volume calculations.
    """

    def test_sound_volume_vectorized(self):
        """
        Test that sound volume functions work with array inputs.
        """
        spcd = np.array([Example1.SPCD, Example2.SPCD])
        dia = np.array([Example1.DIA, Example2.DIA])
        ht = np.array([Example1.HT, Example2.HT])
        division = np.array([Example1.DIVISION, Example2.DIVISION])
        cull = np.array([Example1.CULL, Example2.CULL])

        result = sound_inside_bark_volume(
            spcd=spcd,
            dia=dia,
            ht=ht,
            division=division,
            cull=cull,
        )

        assert isinstance(result, np.ndarray)
        assert len(result) == 2

        # First tree has no cull, sound = gross
        v_gross_1 = total_inside_bark_wood_volume(
            spcd=Example1.SPCD,
            dia=Example1.DIA,
            ht=Example1.HT,
            division=Example1.DIVISION,
        )
        assert pytest.approx(result[0], rel=1e-4) == v_gross_1

        # Second tree has 3% cull
        v_gross_2 = total_inside_bark_wood_volume(
            spcd=Example2.SPCD,
            dia=Example2.DIA,
            ht=Example2.HT,
            division=Example2.DIVISION,
        )
        assert pytest.approx(result[1], rel=1e-4) == v_gross_2 * (
            1 - Example2.CULL / 100
        )


class TestSoundVolumeEdgeCases:
    """
    Tests for edge cases in sound volume calculations.
    """

    def test_sound_volume_100_percent_cull(self):
        """
        When CULL=100%, sound volume is zero.
        """
        result = sound_inside_bark_volume(
            spcd=Example1.SPCD,
            dia=Example1.DIA,
            ht=Example1.HT,
            division=Example1.DIVISION,
            cull=100.0,
        )
        assert result == 0.0

    def test_sound_volume_high_cull(self):
        """
        Test with a high cull percentage (50%).
        """
        v_gross = total_inside_bark_wood_volume(
            spcd=Example1.SPCD,
            dia=Example1.DIA,
            ht=Example1.HT,
            division=Example1.DIVISION,
        )
        result = sound_inside_bark_volume(
            spcd=Example1.SPCD,
            dia=Example1.DIA,
            ht=Example1.HT,
            division=Example1.DIVISION,
            cull=50.0,
        )
        assert pytest.approx(result, rel=1e-6) == v_gross * 0.5
