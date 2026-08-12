"""
Test fixtures derived from the four worked examples in the NSVB GTR.

Each example exercises a different combination of NSVB code paths:

- Tree 1 (Douglas-fir, Example 1): live, no cull, intact top.
  Uses SPCD/DIVISION-level S1a coefficients.

- Tree 2 (Red maple, Example 2): live, cull=3%, intact top.
  Falls back to species-level (SPCD/"") coefficients (no division-specific row).

- Tree 3 (Tanoak, Example 3): dead (DECAYCD=2), cull=10%, broken top (AH<h_m).
  Falls back to Jenkins-group (S1b) coefficients; uses S11 default crown ratio.

- Tree 4 (White oak, Example 4): live, cull=2%, broken top (AH>h_m).
  Uses SPCD/DIVISION-level coefficients; user-supplied CR (30%).

Expected values are taken directly from the GTR text. Tests compare with
``np.testing.assert_allclose(rtol=1e-6)`` to tolerate the GTR's rounding.
``None`` means the example does not exercise (or does not print) that quantity:
parametrized scalar tests should skip, and vectorized tests should index past
None entries (the equation still runs on the full input vector).

Naming conventions for ExpectedValues fields:
    v_*       volume (ft^3)
    w_*       weight / biomass (lb)
    *_ib      inside-bark wood
    *_bk      bark only
    *_ob      outside-bark (wood + bark)
    *_gross   no cull / broken-top / dead reductions applied
    *_sound   with cull / broken-top deductions (volume basis)
    *_red     reduced weight (with cull / dead density / broken-top)

Ratio fields follow GTR notation:
    r_1   R at h=1 ft (stump)
    r_m   R at intact merchantable height h_m
    r_s   R at intact sawlog height h_s
    r_b   R at AH (actual height of broken-top tree)

This file represents GROUND TRUTH from the GTR text. Every value here is
what the publication says the answer is. When the function output does not
match a ground-truth value within the test tolerance, that is a real signal
about either (a) a bug in our implementation, or (b) a known precision
limitation in the GTR's own supplementary CSV / iterative solver. Either
way, tolerance handling lives in ``test_examples.py``, not here.
"""

from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass(frozen=True)
class ExpectedValues:
    """Per-tree GTR-published expected values for every NSVB quantity."""

    # --- Total stem volumes (gross) ---
    v_tot_ib_gross: Optional[float] = None
    v_tot_bk_gross: Optional[float] = None
    v_tot_ob_gross: Optional[float] = None

    # --- Heights from iterative solver ---
    h_m: Optional[float] = None
    h_s: Optional[float] = None

    # --- Stem-profile ratios ---
    r_1: Optional[float] = None
    r_m: Optional[float] = None
    r_s: Optional[float] = None
    r_b: Optional[float] = None

    # --- Merchantable stem volumes (gross) ---
    v_mer_ib_gross: Optional[float] = None
    v_mer_bk_gross: Optional[float] = None
    v_mer_ob_gross: Optional[float] = None

    # --- Sawlog stem volumes (gross) ---
    v_saw_ib_gross: Optional[float] = None
    v_saw_bk_gross: Optional[float] = None
    v_saw_ob_gross: Optional[float] = None

    # --- Stump volumes (gross) ---
    v_stump_ib_gross: Optional[float] = None
    v_stump_bk_gross: Optional[float] = None
    v_stump_ob_gross: Optional[float] = None

    # --- Top volumes (gross) ---
    v_top_ib_gross: Optional[float] = None
    v_top_bk_gross: Optional[float] = None
    v_top_ob_gross: Optional[float] = None

    # --- Missing-top volumes (broken-top trees only) ---
    v_miss_ib_gross: Optional[float] = None
    v_miss_bk_gross: Optional[float] = None
    v_miss_ob_gross: Optional[float] = None

    # --- Total stem volumes (sound: cull + broken-top deductions) ---
    v_tot_ib_sound: Optional[float] = None
    v_tot_bk_sound: Optional[float] = None
    v_tot_ob_sound: Optional[float] = None

    # --- Sound merchantable / stump / top volumes ---
    v_mer_ib_sound: Optional[float] = None
    v_mer_bk_sound: Optional[float] = None
    v_mer_ob_sound: Optional[float] = None
    v_stump_ib_sound: Optional[float] = None
    v_stump_ob_sound: Optional[float] = None
    v_top_ib_sound: Optional[float] = None
    v_top_bk_sound: Optional[float] = None
    v_top_ob_sound: Optional[float] = None

    # --- Stem wood / bark / branch / foliage weights ---
    w_tot_ib: Optional[float] = None
    w_tot_ib_red: Optional[float] = None
    w_tot_bk: Optional[float] = None
    w_tot_bk_red: Optional[float] = None
    w_tot_ob_red: Optional[float] = None
    w_branch: Optional[float] = None
    w_branch_red: Optional[float] = None
    w_foliage: Optional[float] = None
    w_foliage_red: Optional[float] = None

    # --- Broken-top branch / foliage intermediates ---
    crh: Optional[float] = None          # crown ratio standardized to H
    branch_rem: Optional[float] = None
    foliage_rem: Optional[float] = None

    # --- AGB harmonization ---
    agb_predicted: Optional[float] = None
    agb_component_red: Optional[float] = None
    agb_reduce: Optional[float] = None
    agb_predicted_red: Optional[float] = None
    agb_diff: Optional[float] = None
    wood_harmonized: Optional[float] = None
    bark_harmonized: Optional[float] = None
    branch_harmonized: Optional[float] = None

    # --- Adjusted densities ---
    wdsg_adj: Optional[float] = None
    bksg_adj: Optional[float] = None

    # --- Merchantable / stump weights derived from adjusted densities ---
    w_mer_ib: Optional[float] = None
    w_mer_bk: Optional[float] = None
    w_mer_ob: Optional[float] = None
    w_stump_ib: Optional[float] = None
    w_stump_bk: Optional[float] = None
    w_stump_ob: Optional[float] = None

    # --- Tree-top biomass and carbon ---
    drybio_top: Optional[float] = None
    c: Optional[float] = None


@dataclass(frozen=True)
class TestTree:
    """A worked example from the GTR, including inputs and expected outputs."""

    id: int
    description: str
    spcd: int
    dia: float
    ht: float
    division: str
    cull: float = 0.0
    ah: Optional[float] = None       # actual height; None = intact top
    cr: Optional[float] = None       # user crown ratio (decimal); None = S11 default
    decaycd: int = 0                 # 0 = live; 1-5 = dead
    province: Optional[str] = None   # required for S11 default crown ratio
    expected: ExpectedValues = field(default_factory=ExpectedValues)


# ---------------------------------------------------------------------------
# Tree 1 -- Example 1: live Douglas-fir, no cull, intact top
# ---------------------------------------------------------------------------
TREE_1 = TestTree(
    id=1,
    description="Live Douglas-fir, no cull, intact top (Example 1, GTR)",
    spcd=202,
    dia=20.0,
    ht=110.0,
    division="240",
    cull=0.0,
    decaycd=0,
    expected=ExpectedValues(
        v_tot_ib_gross=88.452275544288,
        v_tot_bk_gross=13.191436232306,
        v_tot_ob_gross=101.643711776594,
        h_m=98.28126765402,
        h_s=83.785181046,
        r_1=0.024198309503,
        r_m=0.993406175350,
        r_s=0.960553392655,
        v_mer_ib_gross=85.728641209612,
        v_mer_bk_gross=12.785243758174,
        v_mer_ob_gross=98.513884967785,
        v_saw_ib_gross=82.822737822255,
        v_saw_bk_gross=12.351868370196,
        v_saw_ob_gross=95.174606192451,
        v_stump_ib_gross=2.140395539869,
        v_stump_bk_gross=0.319210456739,
        v_stump_ob_gross=2.459605996608,
        v_top_ib_gross=0.583238794807,
        v_top_bk_gross=0.086982017394,
        v_top_ob_gross=0.670220812201,
        v_tot_ib_sound=88.452275544288,
        v_tot_ob_sound=101.643711776594,
        w_tot_ib=2483.739897283610,
        w_tot_ib_red=2483.739897283610,
        w_tot_bk=361.782496100100,
        w_branch=277.487756904646,
        w_foliage=83.634788855934,
        agb_predicted=3154.5539926725,
        agb_component_red=3123.010150288360,
        agb_reduce=1.000000000000,
        agb_predicted_red=3154.5539926725,
        agb_diff=31.543842384153,
        wood_harmonized=2508.826815376370,
        bark_harmonized=365.436666110811,
        branch_harmonized=280.290511185328,
        wdsg_adj=0.454545207473,
        bksg_adj=0.4439514186,
        w_mer_ib=2431.57468351127,
        w_mer_bk=354.184091263592,
        w_mer_ob=2785.75877477486,
        w_stump_ib=60.709367768006,
        w_stump_bk=8.842949550309,
        w_stump_ob=69.552317318315,
        drybio_top=299.242900579325,
        c=1626.474894645920,
    ),
)


# ---------------------------------------------------------------------------
# Tree 2 -- Example 2: live red maple, cull=3%, intact top
# ---------------------------------------------------------------------------
TREE_2 = TestTree(
    id=2,
    description="Live red maple, cull=3%, intact top (Example 2, GTR)",
    spcd=316,
    dia=11.1,
    ht=38.0,
    division="M210",
    cull=3.0,
    decaycd=0,
    expected=ExpectedValues(
        v_tot_ib_gross=9.427112777611,
        v_tot_bk_gross=2.155106401987,
        v_tot_ob_gross=11.582219179599,
        h_m=28.047839250135,
        h_s=9.98078332380462,
        r_1=0.091117585499,
        r_m=0.970485778632,
        r_s=0.580175217851,
        v_mer_ib_gross=8.289903129704,
        v_mer_bk_gross=1.895132022724,
        v_mer_ob_gross=10.185035152427,
        v_saw_ib_gross=4.610401454934,
        v_saw_bk_gross=1.053971234423,
        v_saw_ob_gross=5.664372689357,
        v_stump_ib_gross=0.858975754526,
        v_stump_bk_gross=0.196368091843,
        v_stump_ob_gross=1.055343846369,
        v_top_ib_gross=0.278233893382,
        v_top_bk_gross=0.06360628742,
        v_top_ob_gross=0.341840180802,
        v_tot_ib_sound=9.144299394283,
        v_tot_ob_sound=11.299405796270,
        w_tot_ib=288.243400288234,
        w_tot_ib_red=284.265641364256,
        w_tot_bk=52.945466015848,
        w_tot_bk_red=52.945466015848,
        w_tot_ob_red=337.211107380104,
        w_branch=135.001927997271,
        w_branch_red=135.001927997271,
        w_foliage=22.807960563788,
        agb_predicted=532.584798820042,
        agb_component_red=472.213035377375,
        agb_reduce=0.991646711840,
        agb_predicted_red=528.135964525863,
        agb_diff=55.922929148488,
        wood_harmonized=317.930462388645,
        bark_harmonized=59.215656211618,
        branch_harmonized=150.989845925600,
        wdsg_adj=0.540466586276,
        bksg_adj=0.440335033421,
        w_mer_ib=279.577936252521,
        w_mer_bk=52.072364607955,
        w_mer_ob=331.650300860476,
        w_stump_ib=28.969056089533,
        w_stump_bk=5.395587617753,
        w_stump_ob=34.364643707286,
        drybio_top=162.121019958101,
        c=256.533242502186,
    ),
)


# ---------------------------------------------------------------------------
# Tree 3 -- Example 3: dead tanoak (DECAYCD=2), cull=10%, broken top (AH<h_m)
# ---------------------------------------------------------------------------
TREE_3 = TestTree(
    id=3,
    description="Dead tanoak (DECAYCD=2), cull=10%, broken top AH=21 < h_m (Example 3, GTR)",
    spcd=631,
    dia=11.3,
    ht=28.0,
    division="M240",
    cull=10.0,
    ah=21.0,
    cr=None,                # use S11 default
    decaycd=2,
    province="M242",
    expected=ExpectedValues(
        v_tot_ib_gross=7.283117547652,
        v_tot_bk_gross=1.907136145131,
        v_tot_ob_gross=9.190253692783,
        h_m=21.790361419761,
        h_s=8.10427459853,
        r_1=0.124985332188,
        r_m=0.975933190572,
        r_s=0.610622756652,
        r_b=0.968066877159,   # R at AH=21 (called "R_m" in GTR text for sound calc)
        v_mer_ib_gross=6.197553279533,
        v_mer_bk_gross=1.622873418346,
        v_mer_ob_gross=7.820426697879,
        v_saw_ib_gross=3.536954447910,
        v_saw_bk_gross=0.926176685624,
        v_saw_ob_gross=4.463131133534,
        v_stump_ib_gross=0.910282866061,
        v_stump_bk_gross=0.238364044628,
        v_stump_ob_gross=1.148646910689,
        # AH < h_m so no top volume present (top is below merchantable cutoff)
        v_top_ib_sound=0.0,
        v_top_bk_sound=0.0,
        v_top_ob_sound=0.0,
        v_mer_ib_sound=5.526235794852,
        v_mer_bk_sound=1.607871287707,
        v_mer_ob_sound=7.134107082559,
        v_stump_ib_sound=0.819254579455,
        v_stump_ob_sound=1.057618624083,
        v_tot_ib_sound=6.345490374317,
        v_tot_bk_sound=1.846235332335,
        v_tot_ob_sound=8.191725706642,
        w_tot_ib=263.590590284621,
        w_tot_ib_red=204.13865566837,
        w_tot_bk=46.816664266025,
        w_tot_bk_red=29.005863664008,
        w_branch=226.788002348975,
        branch_rem=0.338624338624,
        w_branch_red=30.718374921312,
        agb_predicted=492.621457718427,
        agb_component_red=263.862894253690,
        agb_reduce=0.491186195084,
        agb_predicted_red=241.968859433448,
        agb_diff=-21.894034820242,
        wood_harmonized=187.200242072923,
        bark_harmonized=26.599100898644,
        branch_harmonized=28.169516461881,
        # w_foliage left as None: the GTR's "Wfoliage = 0 for dead trees"
        # is a special-case override, not a model output. The override is
        # asserted via w_foliage_red below.
        w_foliage_red=0.0,
        wdsg_adj=0.425499580359,
        bksg_adj=0.230884782206,
        w_mer_ib=163.031163476092,
        w_mer_bk=23.164939953637,
        w_mer_ob=186.196103429729,
        w_stump_ib=24.169078597057,
        w_stump_bk=3.434160945052,
        w_stump_ob=27.603239542109,
        drybio_top=28.169516461610,
        c=114.451270512021,
    ),
)


# ---------------------------------------------------------------------------
# Tree 4 -- Example 4: live white oak, cull=2%, broken top (AH>h_m), CR=30%
# ---------------------------------------------------------------------------
TREE_4 = TestTree(
    id=4,
    description="Live white oak, cull=2%, broken top AH=59 > h_m, CR=30% (Example 4, GTR)",
    spcd=802,
    dia=18.1,
    ht=65.0,
    division="M220",
    cull=2.0,
    ah=59.0,
    cr=0.30,
    decaycd=0,
    expected=ExpectedValues(
        v_tot_ib_gross=42.277832913225,
        v_tot_bk_gross=8.361568823386,
        v_tot_ob_gross=50.639401736611,
        h_m=56.72042843,
        h_s=39.214128405,
        r_1=0.062976290396,
        r_m=0.994774693648,
        r_s=0.913186793241,
        r_b=0.997639540140,
        v_mer_ib_gross=39.394417201498,
        v_mer_bk_gross=7.791296478313,
        v_mer_ob_gross=47.185713679811,
        v_saw_ib_gross=35.945057580350,
        v_saw_bk_gross=7.109093633904,
        v_saw_ob_gross=43.054151214254,
        v_stump_ib_gross=2.662501082857,
        v_stump_bk_gross=0.526580586388,
        v_stump_ob_gross=3.189081669245,
        v_top_ib_gross=0.220914628870,
        v_top_bk_gross=0.043691758685,
        v_top_ob_gross=0.264606387555,
        v_miss_ib_gross=0.099795127559,
        v_miss_bk_gross=0.019737147575,
        v_miss_ob_gross=0.119532275134,
        v_top_ib_sound=0.118698955228,
        v_top_bk_sound=0.023954611111,
        v_top_ob_sound=0.142653566339,
        v_mer_ib_sound=38.606528857468,
        v_stump_ib_sound=2.609251061200,
        v_tot_ib_sound=41.334478873896,
        v_tot_bk_sound=8.341831675811,
        v_tot_ob_sound=49.676310549707,
        w_tot_ib=1582.882064271140,
        w_tot_ib_red=1564.617593936140,
        w_tot_bk=237.154413924445,
        w_tot_bk_red=236.594620449755,
        w_branch=770.251512414918,
        crh=0.364615384615,
        branch_rem=0.746835443038,
        w_branch_red=575.250923828242,
        agb_predicted=2285.319903933610,
        agb_component_red=2376.463138214140,
        agb_reduce=0.917451320791,
        agb_predicted_red=2096.669764293850,
        agb_diff=-279.793373920290,
        wood_harmonized=1380.407021315430,
        bark_harmonized=208.739104392067,
        branch_harmonized=507.523638586351,
        w_foliage=47.823281355886,
        foliage_rem=0.746835443038,
        w_foliage_red=35.716121518954,
        wdsg_adj=0.524488775540,
        bksg_adj=0.401012401713,
        w_mer_ib=1289.304409606240,
        w_mer_bk=194.962966425323,
        w_mer_ob=1484.267376031560,
        w_stump_ib=87.138600608067,
        w_stump_bk=13.176717568116,
        w_stump_ob=100.315318176183,
        drybio_top=512.087070086107,
        c=1039.319202160460,
    ),
)


TREES = [TREE_1, TREE_2, TREE_3, TREE_4]


# ---------------------------------------------------------------------------
# Vectorized accessors
# ---------------------------------------------------------------------------
#
# The same TREES, but rearranged as parallel numpy arrays so a single function
# call can run all four trees at once. ``expected_array(name)`` returns
# ``(values, mask)`` where ``values`` has ``np.nan`` for any tree that does
# not exercise the quantity and ``mask`` is the boolean array of which indices
# should actually be asserted. Vectorized tests should still pass the FULL
# input array through the equation (so the vectorized code path itself is
# exercised on every tree), and then assert against ``values[mask]`` /
# ``result[mask]``.


def _nan_if_none(v):
    return np.nan if v is None else v


INPUTS = {
    "spcd": np.array([t.spcd for t in TREES], dtype=int),
    "dia": np.array([t.dia for t in TREES], dtype=float),
    "ht": np.array([t.ht for t in TREES], dtype=float),
    "division": np.array([t.division for t in TREES]),
    "cull": np.array([t.cull for t in TREES], dtype=float),
    "ah": np.array([_nan_if_none(t.ah) for t in TREES], dtype=float),
    "cr": np.array([_nan_if_none(t.cr) for t in TREES], dtype=float),
    "decaycd": np.array([t.decaycd for t in TREES], dtype=int),
    "province": np.array([t.province or "" for t in TREES]),
}


def tree_crh(tree):
    """Resolve the H-standardized crown ratio (CRH) for a tree.

    Returns ``np.nan`` for trees with no broken top. For broken-top trees:
      * if ``cr`` is user-supplied (measured at AH), standardize to H via
        ``[H - AH(1 - CR)] / H``.
      * otherwise look up the default from Table S11 by (province, hardwood).
    """
    if tree.ah is None:
        return float("nan")
    if tree.cr is not None:
        return (tree.ht - tree.ah * (1 - tree.cr)) / tree.ht
    if tree.province is not None:
        hwd = tree.spcd >= 300
        try:
            from nsvb.tables import CROWN_RATIO_DEFAULTS
            return CROWN_RATIO_DEFAULTS[(tree.province, hwd)]
        except KeyError:
            return float("nan")
    return float("nan")


CRH = np.array([tree_crh(t) for t in TREES], dtype=float)


def expected_array(field_name: str):
    """Return (values, mask) numpy arrays for an ExpectedValues field.

    ``values`` contains the expected value for every tree, with ``np.nan``
    where the example does not exercise (or print) that quantity.
    ``mask`` is True at indices where the assertion should be made.

    Usage in a vectorized test:

        result = some_estimator(INPUTS["spcd"], INPUTS["dia"], ...)
        expected, mask = expected_array("v_tot_ib_gross")
        np.testing.assert_allclose(result[mask], expected[mask], rtol=1e-6)
    """
    raw = [getattr(t.expected, field_name) for t in TREES]
    mask = np.array([v is not None for v in raw])
    values = np.array([np.nan if v is None else v for v in raw], dtype=float)
    return values, mask
