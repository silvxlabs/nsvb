"""
Tests for volume ratio calculations (Equation 6) and height-to-diameter solver (Equation 7).

These tests are based on the GTR-WO-104 examples.
"""

import numpy as np
import pytest

from nsvb.estimators import (
    volume_ratio,
    height_to_diameter,
    merchantable_height,
    sawlog_height,
    stump_volume,
    merchantable_volume,
    sawlog_volume,
    top_volume,
)

from .gtr_values import Example1, Example2, Example3, Example4


class TestVolumeRatioExample1:
    """
    Tests for volume ratio calculations using Example 1 from GTR.

    Example 1: Douglas-fir (SPCD=202), D=20.0", H=110', Division=240
    """

    def test_volume_ratio_stump(self):
        """
        R1 = [1 – (1 – h1/H)^α]^β
        R1 = [1 – (1 – 1/110)^2.220714200464]^0.952218706779
        = 0.024198309503

        Using inside-bark ratio coefficients (S5a).
        """
        result = volume_ratio(
            spcd=Example1.SPCD,
            h=1.0,
            ht=Example1.HT,
            division=Example1.DIVISION,
            bark="ib",
        )
        assert pytest.approx(result, rel=1e-6) == Example1.R1_GTR

    def test_volume_ratio_merchantable(self):
        """
        Rm = [1 – (1 – hm/H)^α]^β
        Rm = [1 – (1 – 98.28126765402/110)^2.220714200464]^0.952218706779
        = 0.993406175350
        """
        result = volume_ratio(
            spcd=Example1.SPCD,
            h=Example1.HM_GTR,
            ht=Example1.HT,
            division=Example1.DIVISION,
            bark="ib",
        )
        assert pytest.approx(result, rel=1e-6) == Example1.RM_GTR

    def test_volume_ratio_sawlog(self):
        """
        Rs = [1 – (1 – hs/H)^α]^β
        Rs = [1 – (1 – 83.785181046/110)^2.220714200464]^0.952218706779
        = 0.960553392655
        """
        result = volume_ratio(
            spcd=Example1.SPCD,
            h=Example1.HS_GTR,
            ht=Example1.HT,
            division=Example1.DIVISION,
            bark="ib",
        )
        assert pytest.approx(result, rel=1e-6) == Example1.RS_GTR


class TestHeightToDiameterExample1:
    """
    Tests for height-to-diameter solver using Example 1 from GTR.

    Example 1: Douglas-fir (SPCD=202), D=20.0", H=110', Division=240
    """

    def test_merchantable_height(self):
        """
        For the merchantable height to a 4.0-inch top (hm):
        Iterative minimization results in hm = 98.28126765402
        """
        result = merchantable_height(
            spcd=Example1.SPCD,
            dia=Example1.DIA,
            ht=Example1.HT,
            division=Example1.DIVISION,
        )
        assert pytest.approx(result, rel=1e-4) == Example1.HM_GTR

    def test_sawlog_height(self):
        """
        For the sawlog height to a 7.0-inch top:
        Iterative minimization results in hs = 83.785181046
        """
        result = sawlog_height(
            spcd=Example1.SPCD,
            dia=Example1.DIA,
            ht=Example1.HT,
            division=Example1.DIVISION,
        )
        assert pytest.approx(result, rel=1e-4) == Example1.HS_GTR

    def test_height_to_4inch_diameter(self):
        """
        Generic height_to_diameter function for 4.0" top.
        """
        result = height_to_diameter(
            spcd=Example1.SPCD,
            dia=Example1.DIA,
            ht=Example1.HT,
            target_dia=4.0,
            division=Example1.DIVISION,
        )
        assert pytest.approx(result, rel=1e-4) == Example1.HM_GTR

    def test_height_to_7inch_diameter(self):
        """
        Generic height_to_diameter function for 7.0" top.
        """
        result = height_to_diameter(
            spcd=Example1.SPCD,
            dia=Example1.DIA,
            ht=Example1.HT,
            target_dia=7.0,
            division=Example1.DIVISION,
        )
        assert pytest.approx(result, rel=1e-4) == Example1.HS_GTR


class TestStemComponentVolumesExample1:
    """
    Tests for stem component volume calculations using Example 1 from GTR.

    Example 1: Douglas-fir (SPCD=202), D=20.0", H=110', Division=240
    """

    def test_stump_inside_bark_volume(self):
        """
        VstumpibGross = R1 × VtotibGross
        VstumpibGross = 0.024198309503 × 88.452275544288
        = 2.140395539869
        """
        result = stump_volume(
            spcd=Example1.SPCD,
            dia=Example1.DIA,
            ht=Example1.HT,
            division=Example1.DIVISION,
            bark="ib",
        )
        assert pytest.approx(result, rel=1e-4) == Example1.V_STUMP_IB_GTR

    def test_stump_outside_bark_volume(self):
        """
        VstumpobGross = R1 × VtotobGross
        VstumpobGross = 0.024198309503 × 101.643711776594
        = 2.459605996608
        """
        result = stump_volume(
            spcd=Example1.SPCD,
            dia=Example1.DIA,
            ht=Example1.HT,
            division=Example1.DIVISION,
            bark="ob",
        )
        assert pytest.approx(result, rel=1e-4) == Example1.V_STUMP_OB_GTR

    def test_merchantable_inside_bark_volume(self):
        """
        VmeribGross = (Rm × VtotibGross) – (R1 × VtotibGross)
        VmeribGross = (0.993406175350 × 88.452275544288)
        – (0.024198309503 × 88.452275544288)
        = 85.728641209612
        """
        result = merchantable_volume(
            spcd=Example1.SPCD,
            dia=Example1.DIA,
            ht=Example1.HT,
            division=Example1.DIVISION,
            bark="ib",
        )
        assert pytest.approx(result, rel=1e-4) == Example1.V_MER_IB_GTR

    def test_merchantable_outside_bark_volume(self):
        """
        VmerobGross = (Rm × VtotobGross) – (R1 × VtotobGross)
        VmerobGross = (0.993406175350 × 101.643711776594)
        – (0.024198309503 × 101.643711776594)
        = 98.513884967785
        """
        result = merchantable_volume(
            spcd=Example1.SPCD,
            dia=Example1.DIA,
            ht=Example1.HT,
            division=Example1.DIVISION,
            bark="ob",
        )
        assert pytest.approx(result, rel=1e-4) == Example1.V_MER_OB_GTR

    def test_merchantable_bark_volume(self):
        """
        VmerbkGross = VmerobGross – VmeribGross
        VmerbkGross = 98.513884967785 – 85.728641209612
        = 12.785243758174

        Note: Using slightly looser tolerance (5e-4) because this is a compound
        calculation (ob - ib) that accumulates error from both component calculations.
        """
        result = merchantable_volume(
            spcd=Example1.SPCD,
            dia=Example1.DIA,
            ht=Example1.HT,
            division=Example1.DIVISION,
            bark="bk",
        )
        assert pytest.approx(result, rel=5e-4) == Example1.V_MER_BK_GTR

    def test_sawlog_inside_bark_volume(self):
        """
        VsawibGross = (Rs × VtotibGross) – (R1 × VtotibGross)
        VsawibGross = (0.960553392655 × 88.452275544288)
        – (0.024198309503 × 88.452275544288)
        = 82.822737822255
        """
        result = sawlog_volume(
            spcd=Example1.SPCD,
            dia=Example1.DIA,
            ht=Example1.HT,
            division=Example1.DIVISION,
            bark="ib",
        )
        assert pytest.approx(result, rel=1e-4) == Example1.V_SAW_IB_GTR

    def test_sawlog_outside_bark_volume(self):
        """
        VsawobGross = (Rs × VtotobGross) – (R1 × VtotobGross)
        VsawobGross = (0.960553392655 × 101.643711776594)
        – (0.024198309503 × 101.643711776594)
        = 95.174606192451
        """
        result = sawlog_volume(
            spcd=Example1.SPCD,
            dia=Example1.DIA,
            ht=Example1.HT,
            division=Example1.DIVISION,
            bark="ob",
        )
        assert pytest.approx(result, rel=1e-4) == Example1.V_SAW_OB_GTR

    def test_top_inside_bark_volume(self):
        """
        VtopibGross = VtotibGross – VmeribGross – VstumpibGross
        VtopibGross = 88.452275544288 – 85.728641209612 – 2.140395539869
        = 0.583238794807
        """
        result = top_volume(
            spcd=Example1.SPCD,
            dia=Example1.DIA,
            ht=Example1.HT,
            division=Example1.DIVISION,
            bark="ib",
        )
        assert pytest.approx(result, rel=1e-4) == Example1.V_TOP_IB_GTR

    def test_top_outside_bark_volume(self):
        """
        VtopobGross = VtotobGross – VmerobGross – VstumpobGross
        VtopobGross = 101.643711776594 – 98.513884967785 – 2.459605996608
        = 0.670220812201
        """
        result = top_volume(
            spcd=Example1.SPCD,
            dia=Example1.DIA,
            ht=Example1.HT,
            division=Example1.DIVISION,
            bark="ob",
        )
        assert pytest.approx(result, rel=1e-4) == Example1.V_TOP_OB_GTR


class TestVolumeRatioExample2:
    """
    Tests for volume ratio calculations using Example 2 from GTR.

    Example 2: Red maple (SPCD=316), D=11.1", H=38', Division=M210, CULL=3%
    """

    def test_volume_ratio_stump(self):
        """
        R1 = [1 – (1 – 1/38)^2.533953226865]^0.8781223155
        = 0.091117585499
        """
        result = volume_ratio(
            spcd=Example2.SPCD,
            h=1.0,
            ht=Example2.HT,
            division=Example2.DIVISION,
            bark="ib",
        )
        assert pytest.approx(result, rel=1e-5) == Example2.R1_GTR

    def test_volume_ratio_merchantable(self):
        """
        Rm = [1 – (1 – 28.047839250135/38)^2.533953226865]^0.8781223155
        = 0.970485778632
        """
        result = volume_ratio(
            spcd=Example2.SPCD,
            h=Example2.HM_GTR,
            ht=Example2.HT,
            division=Example2.DIVISION,
            bark="ib",
        )
        assert pytest.approx(result, rel=1e-5) == Example2.RM_GTR

    def test_merchantable_height(self):
        """
        Iterative minimization results in hm = 28.047839250135
        """
        result = merchantable_height(
            spcd=Example2.SPCD,
            dia=Example2.DIA,
            ht=Example2.HT,
            division=Example2.DIVISION,
        )
        assert pytest.approx(result, rel=1e-4) == Example2.HM_GTR

    def test_sawlog_height(self):
        """
        For hardwoods (SPCD>=300), sawlog top is 9.0".
        Iterative minimization results in hs = 9.98078332380462
        """
        result = sawlog_height(
            spcd=Example2.SPCD,
            dia=Example2.DIA,
            ht=Example2.HT,
            division=Example2.DIVISION,
        )
        assert pytest.approx(result, rel=1e-4) == Example2.HS_GTR


class TestVolumeRatioExample3:
    """
    Tests for volume ratio calculations using Example 3 from GTR.

    Example 3: Dead tanoak (SPCD=631), D=11.3", H=28', AH=21', Division=M240
    Uses Jenkins group coefficients (JENKINS_SPGRPCD=8).
    """

    def test_volume_ratio_stump_jenkins(self):
        """
        R1 = [1 – (1 – 1/28)^2.353772358051]^0.831640004254
        = 0.124985332188

        Uses Jenkins group coefficients (S5b) for tanoak.
        """
        result = volume_ratio(
            spcd=Example3.SPCD,
            h=1.0,
            ht=Example3.HT,
            division=Example3.DIVISION,
            bark="ib",
        )
        assert pytest.approx(result, rel=1e-5) == Example3.R1_GTR

    def test_merchantable_height_jenkins(self):
        """
        Iterative minimization results in hm = 21.790361419761
        """
        result = merchantable_height(
            spcd=Example3.SPCD,
            dia=Example3.DIA,
            ht=Example3.HT,
            division=Example3.DIVISION,
        )
        assert pytest.approx(result, rel=1e-4) == Example3.HM_GTR


class TestVolumeRatioExample4:
    """
    Tests for volume ratio calculations using Example 4 from GTR.

    Example 4: White oak (SPCD=802), D=18.1", H=65', AH=59', Division=M220
    """

    def test_volume_ratio_at_actual_height(self):
        """
        Volume ratio at actual height (AH=59').

        From GTR Example 4 (page 21):
        Rm = 1 - (1 - 59/65)^alpha)^beta = 0.997638556946
        """
        result = volume_ratio(
            spcd=Example4.SPCD,
            h=Example4.AH,
            ht=Example4.HT,
            division=Example4.DIVISION,
            bark="ib",
        )
        # GTR doesn't give the exact value, but VmissibGross = VtotibGross × (1 - Rm)
        # VmissibGross = 0.099795127559, VtotibGross = 42.277832913225
        # So Rm = 1 - 0.099795127559/42.277832913225 = 0.997638556946
        rm_expected = 1 - Example4.V_MISSIB_GROSS_GTR / Example4.V_TOTIB_GROSS_GTR
        assert pytest.approx(result, rel=1e-5) == rm_expected

    def test_merchantable_height(self):
        """
        Merchantable height for white oak (hardwood, 4" top).
        """
        result = merchantable_height(
            spcd=Example4.SPCD,
            dia=Example4.DIA,
            ht=Example4.HT,
            division=Example4.DIVISION,
        )
        # Should be between 1 and 65 feet
        assert 1.0 < result < Example4.HT

    def test_sawlog_height(self):
        """
        Sawlog height for white oak (hardwood, 9" top).
        """
        result = sawlog_height(
            spcd=Example4.SPCD,
            dia=Example4.DIA,
            ht=Example4.HT,
            division=Example4.DIVISION,
        )
        # Should be between 1 and merchantable height
        hm = merchantable_height(
            spcd=Example4.SPCD,
            dia=Example4.DIA,
            ht=Example4.HT,
            division=Example4.DIVISION,
        )
        assert 1.0 < result < hm


class TestVectorizedVolumeRatio:
    """
    Tests for vectorized volume ratio calculations.
    """

    def test_volume_ratio_vectorized(self):
        """
        Test that volume_ratio works with array inputs.
        """
        spcd = np.array([Example1.SPCD, Example2.SPCD, Example3.SPCD])
        h = np.array([1.0, 1.0, 1.0])
        ht = np.array([Example1.HT, Example2.HT, Example3.HT])
        division = np.array([Example1.DIVISION, Example2.DIVISION, Example3.DIVISION])

        result = volume_ratio(spcd=spcd, h=h, ht=ht, division=division, bark="ib")

        # Check that we get array back
        assert isinstance(result, np.ndarray)
        assert len(result) == 3

        # Check individual values
        assert pytest.approx(result[0], rel=1e-5) == Example1.R1_GTR
        assert pytest.approx(result[1], rel=1e-5) == Example2.R1_GTR
        assert pytest.approx(result[2], rel=1e-5) == Example3.R1_GTR
