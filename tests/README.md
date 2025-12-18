# NSVB Test Suite

This directory contains the test suite for the NSVB (National-Scale Volume and Biomass) package. All tests are based on the GTR-WO-104 document examples and expected values.

## Test Files

### Core Test Files

- **`test_examples.py`** - Integration tests for all 4 GTR examples
  - `TestExample1`: Douglas-fir (live, no cull)
  - `TestExample2`: Red maple (live, with cull)
  - `TestExample3`: Tanoak (dead, broken top, decay)
  - `TestExample4`: White oak (live, broken top, cull, crown ratio)
  - `TestVectorized`: Array input tests combining all examples

### Feature-Specific Test Files

- **`test_volume_ratio.py`** - Volume ratio (Equation 6) and height-to-diameter (Equation 7)
  - Stump/merchantable/sawlog volume ratios
  - Height calculations for different top diameters
  - Stem component volumes (stump, merchantable, sawlog, top)

- **`test_carbon.py`** - Carbon calculations (Step 13)
  - Live tree carbon fractions (Table S10a)
  - Dead tree carbon fractions (Table S10b)
  - Carbon content calculations

- **`test_harmonization.py`** - Component harmonization (Steps 11-12)
  - Wood/bark/branch weight predictions
  - Harmonization to ensure components sum to AGB
  - Cull deduction handling

- **`test_dead_tree.py`** - Dead tree calculations
  - Decay proportions (Table 1)
  - Density reductions for dead wood
  - Bark and branch structural losses
  - Broken top adjustments for dead trees

- **`test_drybio.py`** - DRYBIO calculations (Step 14)
  - DRYBIO_STUMP, DRYBIO_BOLE, DRYBIO_TOP
  - DRYBIO_SAPLING, DRYBIO_WDLD_SPP
  - Broken top handling

- **`test_sound_volume.py`** - Sound volume calculations (Step 6)
  - Cull deductions
  - Sound merchantable and sawlog volumes

### Support Files

- **`conftest.py`** - Pytest fixtures for example tree parameters
  - `example1_params` through `example4_params`: Individual example fixtures
  - `all_examples_params`: Vectorized fixture with all 4 examples
  - `live_examples_params`: Vectorized fixture for live trees only
  - Decay proportion fixtures
  - Carbon fraction fixtures

- **`gtr_values.py`** - All expected values from GTR-WO-104
  - `Example1`, `Example2`, `Example3`, `Example4`: GTR expected values
  - `CarbonFractionsLive`, `CarbonFractionsDead`: Table S10 values
  - `DecayProportions`: Table 1 values
  - `WoodSpecificGravity`: REF_SPECIES values

## GTR Examples Reference

### Example 1: Douglas-fir (SPCD=202)
- D=20.0", H=110', Division=240
- Live tree with no cull
- Tests: Volume, weight, harmonization

### Example 2: Red maple (SPCD=316)
- D=11.1", H=38', Division=M210, CULL=3%
- Live tree with cull deduction
- Tests: Volume, weight, cull adjustments, harmonization

### Example 3: Tanoak (SPCD=631)
- D=11.3", H=28', AH=21', Division=M240, DECAYCD=2, CULL=10%
- Dead tree with broken top and decay
- Tests: Decay proportions, broken top adjustments, dead tree weights

### Example 4: White oak (SPCD=802)
- D=18.1", H=65', AH=59', Division=M220, CULL=2%, CR=30%
- Live tree with broken top and crown ratio
- Tests: CRH calculation, BranchRem, reduced weights

## Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_examples.py

# Run specific test class
uv run pytest tests/test_examples.py::TestExample4

# Run specific test
uv run pytest tests/test_examples.py::TestExample4::test_missing_inside_bark_volume
```
