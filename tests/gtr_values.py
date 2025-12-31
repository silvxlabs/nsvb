"""
GTR-WO-104 expected values for NSVB tests.

This file contains all expected values from the GTR worked examples as a single
source of truth. All values are taken directly from the GTR-WO-104 document.

Reference: GTR-WO-104 "National-Scale Volume and Biomass (NSVB) Framework"
"""

# =============================================================================
# EXAMPLE 1: Douglas-fir (SPCD=202), D=20.0", H=110', Division=240
# GTR pages 10-12
# =============================================================================


class Example1:
    """GTR Example 1 expected values."""

    # Tree parameters
    SPCD = 202
    DIA = 20.0
    HT = 110.0
    DIVISION = "240"
    CULL = 0.0

    # Volume calculations (GTR page 10)
    V_TOTIB_GROSS_GTR = 88.452275544288
    V_TOTBK_GROSS_GTR = 13.191436232306

    # Weight calculations (GTR page 11)
    W_TOTIB_GTR = 2483.739897283610
    W_TOTBK_GTR = 361.782496100100
    W_BRANCH_GTR = 277.487756904646
    AGB_PREDICTED_GTR = 3154.5539926725
    W_FOLIAGE_GTR = 83.634788855934

    # Volume ratios (GTR page 12)
    R1_GTR = 0.024198309503
    RM_GTR = 0.993406175350
    RS_GTR = 0.960553392655

    # Heights (GTR page 12)
    HM_GTR = 98.28126765402
    HS_GTR = 83.785181046

    # Harmonized values (GTR pages 10-11)
    WOOD_HARMONIZED_GTR = 2508.826815376370
    BARK_HARMONIZED_GTR = 365.436666110811
    BRANCH_HARMONIZED_GTR = 280.290511185328

    # Component volumes (GTR page 12)
    V_STUMP_IB_GTR = 2.140395539869
    V_STUMP_OB_GTR = 2.459605996608
    V_MER_IB_GTR = 85.728641209612
    V_MER_OB_GTR = 98.513884967785
    V_MER_BK_GTR = 12.785243758174
    V_SAW_IB_GTR = 82.822737822255
    V_SAW_OB_GTR = 95.174606192451
    V_TOP_IB_GTR = 0.583238794807
    V_TOP_OB_GTR = 0.670220812201


# =============================================================================
# EXAMPLE 2: Red Maple (SPCD=316), D=11.1", H=38', Division=M210, CULL=3%
# GTR pages 14-15
# =============================================================================


class Example2:
    """GTR Example 2 expected values."""

    # Tree parameters
    SPCD = 316
    DIA = 11.1
    HT = 38.0
    DIVISION = "M210"
    CULL = 3.0

    # Volume calculations (GTR page 14)
    V_TOTIB_GROSS_GTR = 9.427112777611
    V_TOTBK_GROSS_GTR = 2.155106401987

    # Weight calculations (GTR page 14)
    W_TOTIB_NO_CULL_GTR = 288.243400288234
    W_TOTIBRED_GTR = 284.265641364256
    W_TOTBK_GTR = 52.945466015848
    W_BRANCH_GTR = 135.001927997271
    AGB_PREDICTED_GTR = 532.584798820042
    W_FOLIAGE_GTR = 22.807960563788

    # Volume ratios (GTR page 14)
    R1_GTR = 0.091117585499
    RM_GTR = 0.970485778632
    HM_GTR = 28.047839250135
    HS_GTR = 9.98078332380462

    # Harmonized values (GTR pages 14-15)
    AGB_COMPONENT_RED_GTR = 472.213035377375
    AGB_REDUCE_GTR = 0.991646711840
    AGB_PREDICTED_RED_GTR = 528.135964525863

    WOOD_HARMONIZED_GTR = 317.930462388645
    BARK_HARMONIZED_GTR = 59.215656211618
    BRANCH_HARMONIZED_GTR = 150.989845925600

    # Carbon (GTR page 15)
    CARBON_FRACTION = 0.48573333329999996
    CARBON_GTR = 256.533242502186  # 528.135964525863 × 0.485733333333


# =============================================================================
# EXAMPLE 3: Dead Tanoak (SPCD=631), D=11.3", H=28', AH=21', DECAYCD=2
# GTR pages 16-20
# =============================================================================


class Example3:
    """GTR Example 3 expected values (dead tree with broken top)."""

    # Tree parameters
    SPCD = 631
    DIA = 11.3
    HT = 28.0
    AH = 21.0
    DIVISION = "M240"
    PROVINCE = "M242"
    CULL = 10.0
    DECAYCD = 2
    CR = 0.378  # Crown ratio from Table S11 for M242 hardwood

    # Decay proportions from GTR Table 1 (hardwood DECAYCD=2)
    DENS_PROP = 0.80
    BARK_PROP = 0.8
    BRANCH_PROP = 0.5

    # Volume calculations (GTR pages 16-18)
    V_TOTIB_GROSS_GTR = 7.283117547652
    V_TOTBK_GROSS_GTR = 1.907136145131

    # Volume ratio at actual height (GTR page 18)
    RM_AT_AH_GTR = 0.968066877159

    # Broken top volume (GTR page 18)
    # VtotibBT = Rm × VtotibGross = 7.050544971441 (geometric volume)
    V_TOTIB_BT_GTR = 7.050544971441

    # Weight calculations before reductions (GTR page 18)
    W_TOTIB_GTR = 263.590590284621

    # Reduced weights (GTR page 19)
    W_TOTIBRED_GTR = 204.13865566837

    # Bark weight (GTR page 19)
    W_TOTBK_GTR = 46.816664266025
    W_TOTBKRED_GTR = 29.005863664008

    # Branch weight (GTR page 20)
    W_BRANCH_GTR = 226.788002348975
    BRANCH_REM_GTR = 0.338624338624
    W_BRANCHRED_GTR = 30.718374921312

    # Total AGB (GTR page 20)
    AGB_PREDICTED_GTR = 492.621457718427

    # Volume ratio calculations (GTR page 18)
    R1_GTR = 0.124985332188
    HM_GTR = 21.790361419761


# =============================================================================
# EXAMPLE 4: White Oak (SPCD=802), D=18.1", H=65', AH=59', CR=30%, CULL=2%
# GTR pages 21-23
# =============================================================================


class Example4:
    """GTR Example 4 expected values (live tree with broken top)."""

    # Tree parameters
    SPCD = 802
    DIA = 18.1
    HT = 65.0
    AH = 59.0
    DIVISION = "M220"
    CULL = 2.0
    CR = 30.0  # Observed crown ratio as percentage

    # Volume calculations (GTR page 21)
    V_TOTIB_GROSS_GTR = 42.277832913225
    V_TOTBK_GROSS_GTR = 8.361568823386

    # Missing volume due to broken top (GTR page 21)
    V_MISSIB_GROSS_GTR = 0.099795127559

    # Weight calculations (GTR page 21)
    W_TOTIB_GTR = 1582.882064271140
    W_TOTIBRED_GTR = 1564.617593936140

    # Bark weight (GTR page 22)
    W_TOTBK_GTR = 237.154413924445

    # Volume ratio at AH for bark (GTR page 22)
    RB_AT_AH_GTR = 0.997639540140
    W_TOTBKRED_GTR = 236.594620449755

    # Crown ratio and branch calculations (GTR page 22)
    CRH_GTR = 0.364615384615  # Standardized crown ratio at H
    BRANCH_REM_GTR = 0.746835443038
    FOLIAGE_REM_GTR = 0.746835443038  # Same as BranchRem

    # Branch weight (GTR page 22)
    W_BRANCH_GTR = 770.251512414918
    W_BRANCHRED_GTR = 575.250923828242

    # Foliage weight (GTR page 22)
    W_FOLIAGE_GTR = 47.823281355886
    W_FOLIAGERED_GTR = 35.716121518954


# =============================================================================
# CARBON FRACTIONS (Table S10a - Live Trees)
# =============================================================================


class CarbonFractionsLive:
    """Carbon fractions for live trees from Table S10a."""

    SPCD_202 = 0.5155958333  # Douglas-fir
    SPCD_316 = 0.48573333329999996  # Red maple
    SPCD_631 = 0.4727  # Tanoak
    SPCD_802 = 0.49570000000000003  # White oak


# =============================================================================
# CARBON FRACTIONS (Table S10b - Dead Trees)
# =============================================================================


class CarbonFractionsDead:
    """Carbon fractions for dead trees from Table S10b."""

    HARDWOOD = {
        1: 0.47,
        2: 0.473,
        3: 0.481,
        4: 0.48,
        5: 0.472,
    }

    SOFTWOOD = {
        1: 0.501,
        2: 0.504,
        3: 0.506,
        4: 0.52,
        5: 0.527,
    }


# =============================================================================
# DECAY PROPORTIONS (Table 1)
# =============================================================================


class DecayProportions:
    """Decay proportions from GTR Table 1."""

    HARDWOOD = {
        1: {"dens_prop": 0.99, "bark_prop": 1.0, "branch_prop": 1.0},
        2: {"dens_prop": 0.80, "bark_prop": 0.8, "branch_prop": 0.5},
        3: {"dens_prop": 0.54, "bark_prop": 0.5, "branch_prop": 0.1},
        4: {"dens_prop": 0.43, "bark_prop": 0.2, "branch_prop": 0.0},
        5: {"dens_prop": 0.43, "bark_prop": 0.0, "branch_prop": 0.0},
    }

    SOFTWOOD = {
        1: {"dens_prop": 0.97, "bark_prop": 1.0, "branch_prop": 1.0},
        2: {"dens_prop": 1.00, "bark_prop": 0.8, "branch_prop": 0.5},
        3: {"dens_prop": 0.92, "bark_prop": 0.5, "branch_prop": 0.1},
        4: {"dens_prop": 0.55, "bark_prop": 0.2, "branch_prop": 0.0},
        5: {"dens_prop": 0.55, "bark_prop": 0.0, "branch_prop": 0.0},
    }

    # Live tree cull density proportions (DECAYCD=3 equivalents)
    LIVE_CULL_HARDWOOD = 0.54
    LIVE_CULL_SOFTWOOD = 0.92


# =============================================================================
# WOOD SPECIFIC GRAVITY (from REF_SPECIES)
# =============================================================================


class WoodSpecificGravity:
    """Wood specific gravity values from FIADB REF_SPECIES."""

    SPCD_202 = 0.45  # Douglas-fir
    SPCD_316 = 0.49  # Red maple
    SPCD_631 = 0.58  # Tanoak
    SPCD_802 = 0.60  # White oak
