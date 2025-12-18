"""
Pytest fixtures for NSVB test suite.

These fixtures provide tree parameters from GTR-WO-104 examples to reduce
duplication across test files.
"""

import numpy as np
import pytest


# =============================================================================
# Example 1: Douglas-fir (Live, No Cull)
# =============================================================================
@pytest.fixture
def example1_params():
    """
    GTR Example 1: Douglas-fir tree parameters.

    From GTR-WO-104 page 10:
    Douglas-fir (Pseudotsuga menziesii; SPCD = 202) tree having D = 20.0 inches
    and H = 110 feet with no cull growing in the Marine Division (DIVISION = 240).
    """
    return {
        "spcd": 202,
        "dia": 20.0,
        "ht": 110.0,
        "division": "240",
        "cull": 0.0,
    }


# =============================================================================
# Example 2: Red Maple (Live, With Cull)
# =============================================================================
@pytest.fixture
def example2_params():
    """
    GTR Example 2: Red maple tree parameters.

    From GTR-WO-104 page 14:
    Red maple (Acer rubrum; SPCD = 316) tree with D = 11.1 inches, H = 38 feet,
    and CULL = 3 percent growing in the Warm Continental Mountains (DIVISION = M210).
    """
    return {
        "spcd": 316,
        "dia": 11.1,
        "ht": 38.0,
        "division": "M210",
        "cull": 3.0,
    }


# =============================================================================
# Example 3: Tanoak (Dead, With Broken Top)
# =============================================================================
@pytest.fixture
def example3_params():
    """
    GTR Example 3: Dead tanoak tree parameters.

    From GTR-WO-104 page 16:
    Dead (DECAYCD = 2) tanoak (Notholithocarpus densiflorus; SPCD = 631) tree
    having D = 11.3 inches, H = 28 feet, and a broken top (actual height AH = 21 feet)
    with CULL = 10 percent growing in the Marine Mountains (DIVISION = M240,
    PROVINCE = M242).
    """
    return {
        "spcd": 631,
        "dia": 11.3,
        "ht": 28.0,
        "ah": 21.0,
        "division": "M240",
        "province": "M242",
        "cull": 10.0,
        "decaycd": 2,
    }


# =============================================================================
# Example 4: White Oak (Live, With Broken Top and Crown Ratio)
# =============================================================================
@pytest.fixture
def example4_params():
    """
    GTR Example 4: White oak tree parameters.

    From GTR-WO-104 page 21:
    Live white oak (Quercus alba; SPCD = 802) tree having D = 18.1 inches,
    H = 65 feet, a broken top (actual height (AH) = 59 feet), CULL = 2 percent,
    and a crown ratio of 30 percent (CR = 30) growing in the Hot Continental
    Mountains (DIVISION = M220).
    """
    return {
        "spcd": 802,
        "dia": 18.1,
        "ht": 65.0,
        "ah": 59.0,
        "division": "M220",
        "cull": 2.0,
        "cr": 30.0,
    }


# =============================================================================
# Vectorized Fixtures (All 4 Examples)
# =============================================================================
@pytest.fixture
def all_examples_params():
    """
    All four GTR examples as numpy arrays for vectorized testing.

    Note: ah, cr, and decaycd are not included as they don't apply to all examples.
    """
    return {
        "spcd": np.array([202, 316, 631, 802]),
        "dia": np.array([20.0, 11.1, 11.3, 18.1]),
        "ht": np.array([110.0, 38.0, 28.0, 65.0]),
        "division": np.array(["240", "M210", "M240", "M220"]),
        "cull": np.array([0.0, 3.0, 10.0, 2.0]),
    }


@pytest.fixture
def live_examples_params():
    """
    Examples 1, 2, and 4 (live trees) as numpy arrays.

    Example 3 is a dead tree and excluded.
    """
    return {
        "spcd": np.array([202, 316, 802]),
        "dia": np.array([20.0, 11.1, 18.1]),
        "ht": np.array([110.0, 38.0, 65.0]),
        "division": np.array(["240", "M210", "M220"]),
        "cull": np.array([0.0, 3.0, 2.0]),
    }


# =============================================================================
# Decay Proportion Fixtures
# =============================================================================
@pytest.fixture
def hardwood_decay_proportions():
    """
    GTR Table 1: Hardwood decay proportions by decay class.

    From GTR-WO-104 Table 1 (page 17).
    """
    return {
        1: {"dens_prop": 0.99, "bark_prop": 1.0, "branch_prop": 1.0},
        2: {"dens_prop": 0.80, "bark_prop": 0.8, "branch_prop": 0.5},
        3: {"dens_prop": 0.54, "bark_prop": 0.5, "branch_prop": 0.1},
        4: {"dens_prop": 0.43, "bark_prop": 0.2, "branch_prop": 0.0},
        5: {"dens_prop": 0.43, "bark_prop": 0.0, "branch_prop": 0.0},
    }


@pytest.fixture
def softwood_decay_proportions():
    """
    GTR Table 1: Softwood decay proportions by decay class.

    From GTR-WO-104 Table 1 (page 17).
    """
    return {
        1: {"dens_prop": 0.97, "bark_prop": 1.0, "branch_prop": 1.0},
        2: {"dens_prop": 1.00, "bark_prop": 0.8, "branch_prop": 0.5},
        3: {"dens_prop": 0.92, "bark_prop": 0.5, "branch_prop": 0.1},
        4: {"dens_prop": 0.55, "bark_prop": 0.2, "branch_prop": 0.0},
        5: {"dens_prop": 0.55, "bark_prop": 0.0, "branch_prop": 0.0},
    }


# =============================================================================
# Carbon Fraction Fixtures
# =============================================================================
@pytest.fixture
def dead_carbon_fractions():
    """
    GTR Table S10b: Dead tree carbon fractions.

    From GTR-WO-104 Table S10b.
    """
    return {
        "hardwood": {1: 0.47, 2: 0.473, 3: 0.481, 4: 0.48, 5: 0.472},
        "softwood": {1: 0.501, 2: 0.504, 3: 0.506, 4: 0.52, 5: 0.527},
    }
