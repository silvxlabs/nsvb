import warnings
from typing import Union

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.optimize import brentq

from nsvb.models import MODEL_MAP
from nsvb.validation import validated
from nsvb.tables import (
    CARBON_FRACTION_DEAD,
    CARBON_FRACTION_LIVE,
    CARBON_FRACTION_LIVE_BY_JENKINS,
    CROWN_RATIO_DEFAULTS,
    ECO_DIV_PROV,
    HARDWOOD_SPCD_THRESHOLD,
    REF_SPECIES,
    lookup_spcd_coefs,
    resolve_stdorgcd,
    TABLES,
    WOOD_DENSITY_PROPORTIONS,
)

# Single definition, shared with the coefficient loader in tables.py so the
# two cannot drift. GTR p.8 keys the hardwood/softwood split off SPCD, not off
# REF_SPECIES.SFTWD_HRDWD -- see the note in tables.py.
_HARDWOOD_SPCD_THRESHOLD = HARDWOOD_SPCD_THRESHOLD

WEIGHT_CUBIC_FOOT_WATER = 62.4  # lb/ft^3

# pi / (4 * 144) -- area of a 1-inch-diameter circle, in ft^2. Appears in
# equation 7 (top-diameter solver) as the conversion between stem
# cross-sectional area at top height and the squared top diameter in inches.
_INCH2_TO_FT2 = 0.005454154


def _org_key(stdorgcd):
    """Stand-origin table key(s), shaped to broadcast alongside the other
    per-tree inputs. Scalars (including None) collapse to a single string;
    arrays are resolved element-wise so a vectorized call can mix origins."""
    if isinstance(stdorgcd, np.ndarray):
        return np.array(
            [resolve_stdorgcd(o) for o in stdorgcd.reshape(-1)]
        ).reshape(stdorgcd.shape)
    return resolve_stdorgcd(stdorgcd)


def _run_model_form(
    table_name: str,
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
    stdorgcd=None,
) -> Union[float, NDArray]:
    """
    Run the model form for the given table.
    Works with scalar or array inputs.

    Parameters:
        table_name (str): Table name.
        spcd (int): Species code.
        dia (float): Diameter of the tree.
        ht (float): Height of the tree.
        division (str, optional): Division code. Default is an empty string.

    Returns:
        float: Model form result.
    """
    # Scalar implementation
    def _scalar_lookup(spcd_val, dia_val, ht_val, div_val, org_val):
        try:
            data = lookup_spcd_coefs(
                TABLES[f"{table_name}a"], spcd_val, div_val, org_val
            )
        except KeyError:
            spgrp = int(REF_SPECIES[spcd_val]["JENKINS_SPGRPCD"])
            table_data = TABLES[f"{table_name}b"]
            data = table_data.get(spgrp)
            wdsg = float(REF_SPECIES[spcd_val]["WOOD_SPGR_GREENVOL_DRYWT"])
            data = data.copy()
            data["wdsg"] = wdsg
        model_function = MODEL_MAP[data["model"]]
        return model_function(dia_val, ht_val, **data)

    org = _org_key(stdorgcd)

    # Check if inputs are arrays
    is_array = (isinstance(spcd, np.ndarray) or isinstance(dia, np.ndarray)
                or isinstance(ht, np.ndarray) or isinstance(stdorgcd, np.ndarray))

    if is_array:
        # Vectorize the scalar function
        vectorized_fn = np.vectorize(_scalar_lookup)
        return vectorized_fn(spcd, dia, ht, division, org)
    else:
        # Use scalar path directly
        return _scalar_lookup(int(spcd), float(dia), float(ht), str(division), org)


@validated
def total_inside_bark_wood_volume(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
    *,
    stdorgcd=None,
) -> Union[float, NDArray]:
    """
    Predict gross total stem wood volume as a
    function of diameter at breast height (D) and
    total height (H). Use the appropriate model form
    and coefficients from table S1.

    Corresponds to step 1 of "Examples of Tree-Level Calculations" in the GTR.

    Parameters:
        spcd (int): FIA species code.
        dia (float): Diameter of the tree in inches (in).
        ht (float): Height of the tree in feet (ft).
        division (str, optional): Division code. Default is an empty string.

    Returns:
        float: Total inside bark wood volume.
    """
    return _run_model_form("s1", spcd, dia, ht, division, stdorgcd=stdorgcd)


@validated
def total_bark_wood_volume(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
    *,
    stdorgcd=None,
) -> Union[float, NDArray]:
    """
    Predict gross total stem bark volume as a function of D and H. Uses the
    appropriate model form and coefficients from table S2.

    Corresponds to step 2 of "Examples of Tree-Level Calculations" in the GTR.

    Parameters:
        spcd (int): FIA species code.
        dia (float): Diameter of the tree in inches (in).
        ht (float): Height of the tree in feet (ft).
        division (str, optional): Division code. Default is an empty string.

    Returns:
        float: Total stem bark volume in cubic feet (ft^3).
    """
    return _run_model_form("s2", spcd, dia, ht, division, stdorgcd=stdorgcd)


@validated
def total_outside_bark_volume(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
    *,
    stdorgcd=None,
) -> Union[float, NDArray]:
    """
    Obtain gross total stem outside-bark volume as
    the sum of wood and bark gross volumes.

    Corresponds to step 3 of "Examples of Tree-Level Calculations" in the GTR.

    Parameters:
        spcd (int): FIA species code.
        dia (float): Diameter of the tree in inches (in).
        ht (float): Height of the tree in feet (ft).
        division (str, optional): Division code. Default is an empty string.

    Returns:
        float: Total outside bark volume.
    """
    v_tot_ib = total_inside_bark_wood_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
    v_tot_bk = total_bark_wood_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
    return v_tot_ib + v_tot_bk


def _wdsg(spcd: Union[int, ArrayLike]) -> Union[float, NDArray]:
    """Wood specific gravity (green volume / dry weight) from FIADB
    REF_SPECIES, shape-preserving for scalar or array input."""
    spcd_arr = np.asarray(spcd)
    values = np.array([
        float(REF_SPECIES[int(s)]["WOOD_SPGR_GREENVOL_DRYWT"])
        for s in spcd_arr.reshape(-1)
    ])
    if spcd_arr.ndim == 0:
        return values.item()
    return values.reshape(spcd_arr.shape)


@validated
def total_stem_wood_dry_weight(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
    *,
    stdorgcd=None,
) -> Union[float, NDArray]:
    """
    Wtotib -- convert total stem wood GROSS volume to biomass weight using
    published wood density values (Miles and Smith 2009):

        Wtotib = VtotibGross * WDSG * 62.4

    Works with scalar or array inputs.

    Corresponds to step 7 of "Examples of Tree-Level Calculations" in the GTR.

    This is the gross quantity, with no deductions of any kind -- exactly as
    the GTR defines Wtotib (see Example 1). For cull, dead-tree density
    reduction or broken-top loss, use
    :func:`total_stem_wood_dry_weight_reduced`, which implements Wtotibred.

    (This function previously accepted a ``cull`` argument, which made it
    compute Wtotibred under the Wtotib name. It duplicated the reduced
    variant, and keyed its DensProp off REF_SPECIES.SFTWD_HRDWD rather than
    the GTR's SPCD>=300 rule, so the two disagreed by up to ~8 percent for the
    39 species where those classifications differ. The gross form is also what
    :func:`agb_reduce_factor` needs for its denominator.)

    Parameters:
        spcd (int): FIA species code.
        dia (float): Diameter of the tree in inches (in).
        ht (float): Height of the tree in feet (ft).
        division (str, optional): Division code. Default is an empty string.

    Returns:
        float: Total stem wood dry weight in pounds (lb).
    """
    return (
        total_inside_bark_wood_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
        * _wdsg(spcd)
        * WEIGHT_CUBIC_FOOT_WATER
    )


@validated
def total_stem_bark_weight(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
    *,
    stdorgcd=None,
) -> Union[float, NDArray]:
    """
    Wtotbk -- predict GROSS total stem bark biomass as a function of D and H,
    using the appropriate model form and coefficients from table S6.

    Corresponds to step 8 of "Examples of Tree-Level Calculations" in the GTR.

    The GTR's description of step 8 also covers reducing the prediction for
    missing bark due to a broken top or dead-tree structural loss. That
    reduction is NOT applied here -- this function returns the raw model
    prediction. Use :func:`total_stem_bark_weight_reduced` for Wtotbkred.

    Parameters:
        spcd (int): FIA species code.
        dia (float): Diameter of the tree in inches (in).
        ht (float): Height of the tree in feet (ft).
        division (str, optional): Division code. Default is an empty string.

    Returns:
        float: Gross total stem bark weight in pounds (lb).
    """
    return _run_model_form("s6", spcd, dia, ht, division, stdorgcd=stdorgcd)


@validated
def total_branch_weight(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
    *,
    stdorgcd=None,
) -> Union[float, NDArray]:
    """
    Wbranch -- predict GROSS total branch biomass as a function of D and H,
    using the appropriate model form and coefficients from table S7.

    Corresponds to step 9 of "Examples of Tree-Level Calculations" in the GTR.

    The GTR's description of step 9 also covers reducing the prediction for
    missing branches due to a broken top, and for dead-tree wood density
    reduction and structural loss. None of that is applied here -- this
    function returns the raw model prediction. Use
    :func:`total_branch_weight_reduced` for Wbranchred.

    Parameters:
        spcd (int): FIA species code.
        dia (float): Diameter of the tree in inches (in).
        ht (float): Height of the tree in feet (ft).
        division (str, optional): Division code. Default is an empty string.

    Returns:
        float: Gross total branch weight in pounds (lb).
    """
    return _run_model_form("s7", spcd, dia, ht, division, stdorgcd=stdorgcd)


@validated
def total_aboveground_biomass(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
    *,
    stdorgcd=None,
) -> Union[float, NDArray]:
    """
    AGBPredicted -- predict GROSS total aboveground biomass as a function of D
    and H, using the appropriate model form and coefficients from table S8.
    The GTR considers this the "optimal" biomass estimate, which is why the
    three separately modelled components are later harmonized onto it rather
    than the other way round.

    Corresponds to step 10 of "Examples of Tree-Level Calculations" in the GTR.

    The GTR's description of step 10 also covers reducing the prediction by the
    overall proportional loss derived from the stem wood, bark and branch
    component reductions. That is NOT applied here -- see
    :func:`agb_reduce_factor` for AGBReduce and :func:`agb_predicted_reduced`
    for AGBPredictedred.

    Note that foliage is excluded: NSVB aboveground biomass comprises wood,
    bark and branches only (GTR Example 1).

    Parameters:
        spcd (int): FIA species code.
        dia (float): Diameter of the tree in inches (in).
        ht (float): Height of the tree in feet (ft).
        division (str, optional): Division code. Default is an empty string.

    Returns:
        float: Gross total aboveground biomass in pounds (lb).
    """
    return _run_model_form("s8", spcd, dia, ht, division, stdorgcd=stdorgcd)


@validated
def total_foliage_dry_weight(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
    *,
    stdorgcd=None,
) -> Union[float, NDArray]:
    """
    Wfoliage -- directly predict GROSS total foliage dry weight as a function
    of D and H, using the appropriate model form and coefficients from
    table S9.

    Corresponds to step 15 of "Examples of Tree-Level Calculations" in the GTR.

    Foliage is kept separate from aboveground biomass, which comprises wood,
    bark and branches only. For the broken-top reduction, and for the GTR rule
    that foliage is zero on any dead tree, use
    :func:`total_foliage_dry_weight_reduced`.

    Parameters:
        spcd (int): FIA species code.
        dia (float): Diameter of the tree in inches (in).
        ht (float): Height of the tree in feet (ft).
        division (str, optional): Division code. Default is an empty string.

    Returns:
        float: Gross total foliage dry weight in pounds (lb).
    """
    return _run_model_form("s9", spcd, dia, ht, division, stdorgcd=stdorgcd)


# =============================================================================
# NSVB steps 4-6, 11-14, 16-17, plus the broken-top / dead-tree reduced
# variants of steps 7-9 and 15.
#
# Naming convention throughout: a bare name is the GROSS quantity (the raw
# model prediction, no deductions), and a ``_reduced`` / ``_sound`` suffix
# carries the cull, dead-tree density and broken-top reductions. The gross
# forms are not merely a convenience -- ``agb_reduce_factor`` needs them
# undeducted for its denominator.
# =============================================================================


# ----- Step 4: merchantable & sawlog heights -----


def _lookup_volob_coefs(spcd_val, div_val, org_val):
    """S3 coefs (a, b, c) for one tree, with Jenkins fallback."""
    try:
        return lookup_spcd_coefs(TABLES["s3a"], spcd_val, div_val, org_val)
    except KeyError:
        spgrp = int(REF_SPECIES[spcd_val]["JENKINS_SPGRPCD"])
        return TABLES["s3b"][spgrp]


def _lookup_rcumob_coefs(spcd_val, div_val, org_val):
    """S4 (alpha, beta) for one tree, with Jenkins fallback."""
    try:
        return lookup_spcd_coefs(TABLES["s4a"], spcd_val, div_val, org_val)
    except KeyError:
        spgrp = int(REF_SPECIES[spcd_val]["JENKINS_SPGRPCD"])
        return TABLES["s4b"][spgrp]


def _solve_top_height_scalar(spcd_val, dia_val, ht_val, div_val, top_dia, org_val):
    """Solve equation 7 for the height at which outside-bark diameter equals
    ``top_dia`` (inches). Returns NaN if ``top_dia`` is unreachable on this
    tree (e.g. tree too small to have a merchantable top)."""
    if not np.isfinite(top_dia) or not np.isfinite(dia_val) or dia_val <= top_dia:
        return np.nan
    s3 = _lookup_volob_coefs(spcd_val, div_val, org_val)
    s4 = _lookup_rcumob_coefs(spcd_val, div_val, org_val)
    a, b, c = s3["a"], s3["b"], s3["c"]
    alpha, beta = s4["alpha"], s4["beta"]
    # The volume-outside-bark prediction at full height (eqn 5).
    v_ob = a * (dia_val ** b) * (ht_val ** c)
    # eqn 7: top_dia - sqrt((v_ob / area_factor / H) * alpha * beta
    #          * (1 - h/H)^(alpha-1) * (1 - (1 - h/H)^alpha)^(beta-1))
    prefactor = v_ob / _INCH2_TO_FT2 / ht_val * alpha * beta

    def residual(h):
        r = 1.0 - h / ht_val
        inner = 1.0 - r ** alpha
        return top_dia - np.sqrt(prefactor * (r ** (alpha - 1)) * (inner ** (beta - 1)))

    # h=1 is the stump; h=HT is the tip (di -> 0). residual at h=1 is
    # negative (since stem diameter at the stump is large), residual at
    # h=HT is positive (di -> 0 < top_dia). Bracket [1, HT] matches the R
    # reference implementation. Tighten tolerances well below the GTR's
    # 12-decimal text precision so the solver doesn't bottom out at brentq's
    # defaults (xtol=2e-12 abs, rtol=8.9e-16 rel are tighter than the
    # default 8.881784197001252e-16 / 2e-12 anyway, but we override to be
    # explicit about wanting near-machine precision).
    return brentq(residual, 1.0, ht_val, xtol=1e-14, rtol=1e-12)


_solve_top_height = np.vectorize(_solve_top_height_scalar, otypes=[float])


# FIA convention: merchantable height is defined only for "trees" (DBH >= 5 in,
# i.e. not saplings); sawlog height is defined only for trees large enough
# to contain at least one sawlog above the 1-ft stump (softwoods DBH >= 9 in,
# hardwoods DBH >= 11 in). Below these thresholds the corresponding height
# is undefined and we return NaN, matching the R reference implementation.
_MERCH_MIN_DBH = 5.0
_SAWLOG_MIN_DBH_SOFTWOOD = 9.0
_SAWLOG_MIN_DBH_HARDWOOD = 11.0


@validated
def merchantable_height(spcd, dia, ht, division="", top_dia=4.0, *, stdorgcd=None):
    """Height (ft) from ground to the point where stem outside-bark diameter
    equals ``top_dia`` (default 4 inches -- the FIA merchantable top).
    Found by inverting equation 7 numerically using S3 and S4 coefficients.

    Returns NaN for trees with DBH < 5 in (FIA sapling/tree threshold).

    Step 4 of the GTR. Scalar or array inputs supported; returns the same
    shape as the inputs.
    """
    dia_arr = np.asarray(dia, dtype=float)
    result = _solve_top_height(spcd, dia, ht, division, top_dia, _org_key(stdorgcd))
    return np.where(dia_arr >= _MERCH_MIN_DBH, result, np.nan)


# Per the GTR, the sawlog top is 7 inches for softwoods and 9 inches for
# hardwoods. Hardwoods are SPCD >= 300 in the FIA REF_SPECIES table.
_SAWLOG_TOP_SOFTWOOD = 7.0
_SAWLOG_TOP_HARDWOOD = 9.0


@validated
def sawlog_height(spcd, dia, ht, division="", *, stdorgcd=None):
    """Height (ft) to the sawlog-top diameter: 7 in for softwoods (SPCD<300)
    or 9 in for hardwoods (SPCD>=300).

    Returns NaN for trees below the FIA sawtimber threshold (DBH < 9 in for
    softwoods, < 11 in for hardwoods).

    Step 4."""
    spcd_arr = np.asarray(spcd)
    dia_arr = np.asarray(dia, dtype=float)
    is_hwd = spcd_arr >= _HARDWOOD_SPCD_THRESHOLD
    top_dia = np.where(is_hwd, _SAWLOG_TOP_HARDWOOD, _SAWLOG_TOP_SOFTWOOD)
    min_dbh = np.where(is_hwd, _SAWLOG_MIN_DBH_HARDWOOD, _SAWLOG_MIN_DBH_SOFTWOOD)
    result = _solve_top_height(spcd, dia, ht, division, top_dia, _org_key(stdorgcd))
    return np.where(dia_arr >= min_dbh, result, np.nan)


# ----- Step 5: stem-profile volume ratios -----


def _lookup_rcumib_coefs(spcd_val, div_val, org_val):
    """S5 (alpha, beta) for one tree, with Jenkins fallback."""
    try:
        return lookup_spcd_coefs(TABLES["s5a"], spcd_val, div_val, org_val)
    except KeyError:
        spgrp = int(REF_SPECIES[spcd_val]["JENKINS_SPGRPCD"])
        return TABLES["s5b"][spgrp]


def _volume_ratio_scalar(spcd_val, ht_val, div_val, h_val, org_val):
    """R(h) = [1 - (1 - h/H)^alpha]^beta using S5 coefs (eqn 6).

    Returns NaN when h is non-finite -- vector inputs that mix
    valid and missing heights (e.g. ah=NaN for trees without a broken
    top) propagate cleanly.
    """
    if not np.isfinite(h_val):
        return np.nan
    s5 = _lookup_rcumib_coefs(spcd_val, div_val, org_val)
    return (1.0 - (1.0 - h_val / ht_val) ** s5["alpha"]) ** s5["beta"]


_volume_ratio = np.vectorize(_volume_ratio_scalar, otypes=[float])


STUMP_HEIGHT_FT = 1.0  # NSVB stump is always 1 foot


@validated
def stump_volume_ratio(spcd, dia, ht, division="", *, stdorgcd=None):
    """R at the 1-foot stump height (the GTR's R_1) using S5 coefficients.

    Note: dia is part of the standard estimator signature but is unused
    by the ratio formula itself. Step 5."""
    return _volume_ratio(spcd, ht, division, STUMP_HEIGHT_FT, _org_key(stdorgcd))


@validated
def merchantable_volume_ratio(spcd, dia, ht, division="", *, stdorgcd=None):
    """R at the merchantable height h_m (R_m) using S5 coefficients. Step 5."""
    h_m = merchantable_height(spcd, dia, ht, division, stdorgcd=stdorgcd)
    return _volume_ratio(spcd, ht, division, h_m, _org_key(stdorgcd))


@validated
def sawlog_volume_ratio(spcd, dia, ht, division="", *, stdorgcd=None):
    """R at the sawlog height h_s (R_s) using S5 coefficients. Step 5."""
    h_s = sawlog_height(spcd, dia, ht, division, stdorgcd=stdorgcd)
    return _volume_ratio(spcd, ht, division, h_s, _org_key(stdorgcd))


@validated
def broken_top_volume_ratio(spcd, dia, ht, division="", ah=None, *, stdorgcd=None):
    """R at AH (R_b) for broken-top trees. Returns NaN for trees with no
    broken top (ah=NaN or None). Step 5.

    ``ah=None`` is resolved to NaN and then broadcast like any other input,
    rather than short-circuiting to a bare scalar -- an array call with no
    broken tops must still return one NaN per tree, not a single ``()``-shaped
    NaN that silently collapses the caller's result.
    """
    ah_arr = np.asarray(np.nan if ah is None else ah, dtype=float)
    return _volume_ratio(spcd, ht, division, ah_arr, _org_key(stdorgcd))


def _merchantable_partition_ratio(spcd, dia, ht, division="", *, stdorgcd=None):
    """R_m where a merchantable stem exists; R_1 for saplings.

    GTR p.32: "It is assumed no merchantable volume is present for
    sapling-sized trees (1.0<=D<5.0); however, total stem wood and bark volume
    components are present. Prediction of biomass (and subsequently carbon)
    for saplings proceeds in the same manner as for larger trees."

    So a sapling has no merchantable *height* -- :func:`merchantable_height`
    and :func:`merchantable_volume_ratio` correctly report NaN, because the
    4-inch top does not exist on a 3-inch tree. But the stem still partitions
    into stump and top, and those still have to sum to the total. Collapsing
    the merchantable cut point onto the stump (R_m := R_1) makes the
    merchantable subcomponent exactly zero while leaving stump = R_1 and
    top = R_b - R_1, so the partition closes at R_b as it does for any other
    tree.

    Without this the NaN from R_m propagates through :func:`_effective_ratios`
    into every sound volume, every merchantable and stump weight, and
    DRYBIO_TOP -- turning an entire FIA size class (D >= 1.0 in is tallied)
    into NaN even though its biomass and carbon compute fine.
    """
    r_m = merchantable_volume_ratio(spcd, dia, ht, division, stdorgcd=stdorgcd)
    r_1 = stump_volume_ratio(spcd, dia, ht, division, stdorgcd=stdorgcd)
    return np.where(np.isfinite(r_m), r_m, r_1)


# ----- Step 6: subcomponent volumes (gross) -----
#
# Merchantable / sawlog volumes use the (R_top - R_1) * V_tot pattern.
# The GTR uses the SAME ratio coefficients (from the inside-bark ratio
# table S5) for both inside-bark and outside-bark sub-volumes to preserve
# additivity across the layers. Bark sub-volumes are derived by
# subtraction (V_bk = V_ob - V_ib) for the same reason.


@validated
def merchantable_inside_bark_volume(spcd, dia, ht, division="", *, stdorgcd=None):
    v_tot = total_inside_bark_wood_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
    r_m = _merchantable_partition_ratio(spcd, dia, ht, division, stdorgcd=stdorgcd)
    r_1 = stump_volume_ratio(spcd, dia, ht, division, stdorgcd=stdorgcd)
    return (r_m - r_1) * v_tot


@validated
def merchantable_outside_bark_volume(spcd, dia, ht, division="", *, stdorgcd=None):
    v_tot = total_outside_bark_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
    r_m = _merchantable_partition_ratio(spcd, dia, ht, division, stdorgcd=stdorgcd)
    r_1 = stump_volume_ratio(spcd, dia, ht, division, stdorgcd=stdorgcd)
    return (r_m - r_1) * v_tot


@validated
def merchantable_bark_volume(spcd, dia, ht, division="", *, stdorgcd=None):
    return (
        merchantable_outside_bark_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
        - merchantable_inside_bark_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
    )


@validated
def sawlog_inside_bark_volume(spcd, dia, ht, division="", *, stdorgcd=None):
    v_tot = total_inside_bark_wood_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
    r_s = sawlog_volume_ratio(spcd, dia, ht, division, stdorgcd=stdorgcd)
    r_1 = stump_volume_ratio(spcd, dia, ht, division, stdorgcd=stdorgcd)
    return (r_s - r_1) * v_tot


@validated
def sawlog_outside_bark_volume(spcd, dia, ht, division="", *, stdorgcd=None):
    v_tot = total_outside_bark_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
    r_s = sawlog_volume_ratio(spcd, dia, ht, division, stdorgcd=stdorgcd)
    r_1 = stump_volume_ratio(spcd, dia, ht, division, stdorgcd=stdorgcd)
    return (r_s - r_1) * v_tot


@validated
def sawlog_bark_volume(spcd, dia, ht, division="", *, stdorgcd=None):
    return (
        sawlog_outside_bark_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
        - sawlog_inside_bark_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
    )


@validated
def stump_inside_bark_volume(spcd, dia, ht, division="", *, stdorgcd=None):
    v_tot = total_inside_bark_wood_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
    r_1 = stump_volume_ratio(spcd, dia, ht, division, stdorgcd=stdorgcd)
    return r_1 * v_tot


@validated
def stump_outside_bark_volume(spcd, dia, ht, division="", *, stdorgcd=None):
    v_tot = total_outside_bark_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
    r_1 = stump_volume_ratio(spcd, dia, ht, division, stdorgcd=stdorgcd)
    return r_1 * v_tot


@validated
def stump_bark_volume(spcd, dia, ht, division="", *, stdorgcd=None):
    return (
        stump_outside_bark_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
        - stump_inside_bark_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
    )


@validated
def top_inside_bark_volume(spcd, dia, ht, division="", *, stdorgcd=None):
    return (
        total_inside_bark_wood_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
        - merchantable_inside_bark_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
        - stump_inside_bark_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
    )


@validated
def top_outside_bark_volume(spcd, dia, ht, division="", *, stdorgcd=None):
    return (
        total_outside_bark_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
        - merchantable_outside_bark_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
        - stump_outside_bark_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
    )


@validated
def top_bark_volume(spcd, dia, ht, division="", *, stdorgcd=None):
    return (
        top_outside_bark_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
        - top_inside_bark_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
    )


@validated
def missing_inside_bark_volume(spcd, dia, ht, division="", ah=None, *, stdorgcd=None):
    """Inside-bark wood volume above AH for broken-top trees. Step 6."""
    v_tot = total_inside_bark_wood_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
    r_b = broken_top_volume_ratio(spcd, dia, ht, division, ah, stdorgcd=stdorgcd)
    return v_tot * (1.0 - r_b)


@validated
def missing_outside_bark_volume(spcd, dia, ht, division="", ah=None, *, stdorgcd=None):
    v_tot = total_outside_bark_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
    r_b = broken_top_volume_ratio(spcd, dia, ht, division, ah, stdorgcd=stdorgcd)
    return v_tot * (1.0 - r_b)


@validated
def missing_bark_volume(spcd, dia, ht, division="", ah=None, *, stdorgcd=None):
    return (
        missing_outside_bark_volume(spcd, dia, ht, division, ah, stdorgcd=stdorgcd)
        - missing_inside_bark_volume(spcd, dia, ht, division, ah, stdorgcd=stdorgcd)
    )


# ----- Step 6 (sound): cull / broken-top adjusted volumes -----
#
# The GTR distinguishes three scenarios:
#   * intact top:              V_*_sound = V_*_gross with IB-only cull deduction
#   * broken top, AH >= h_m:   merchantable region intact; some top is missing
#   * broken top, AH <  h_m:   merchantable region itself partially broken;
#                              top region entirely gone
#
# All three unify cleanly via two effective ratios:
#   R_eff_mer = min(R_m, R_b)      (R_b = 1 for intact)
#   R_eff_top = max(0, R_b - R_m)  (yields 1 - R_m for intact)
# After which sub-volumes follow the same form as gross (with cull on IB only).


def _cull_factor(cull):
    """1 - cull/100 as numpy-friendly array."""
    return 1.0 - np.asarray(cull, dtype=float) / 100.0


def _broken_top_ratio(spcd, dia, ht, division, ah, *, stdorgcd=None):
    """R_b = R at AH, or 1.0 when ah is NaN/None (intact top)."""
    ah_arr = np.asarray(np.nan if ah is None else ah, dtype=float)
    rb = broken_top_volume_ratio(spcd, dia, ht, division, ah_arr, stdorgcd=stdorgcd)
    return np.where(np.isfinite(ah_arr), rb, 1.0)


def _effective_ratios(spcd, dia, ht, division, ah, *, stdorgcd=None):
    """Returns (R_1, R_eff_mer, R_eff_top): the stump / merchantable /
    top proportions that account for broken-top truncation.

    ``R_eff_mer + R_eff_top == R_b`` by construction, for every combination of
    intact/broken top and merchantable/sapling, which is what keeps the
    subcomponent volumes additive with the total.
    """
    r_1 = stump_volume_ratio(spcd, dia, ht, division, stdorgcd=stdorgcd)
    # R_1 for saplings -- see _merchantable_partition_ratio (GTR p.32).
    r_m = _merchantable_partition_ratio(spcd, dia, ht, division, stdorgcd=stdorgcd)
    r_b = _broken_top_ratio(spcd, dia, ht, division, ah, stdorgcd=stdorgcd)
    r_eff_mer = np.minimum(r_m, r_b)
    r_eff_top = np.maximum(0.0, r_b - r_m)
    return r_1, r_eff_mer, r_eff_top


@validated
def merchantable_inside_bark_volume_sound(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, *, stdorgcd=None):
    v_tot = total_inside_bark_wood_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
    r_1, r_eff_mer, _ = _effective_ratios(spcd, dia, ht, division, ah, stdorgcd=stdorgcd)
    return (r_eff_mer - r_1) * v_tot * _cull_factor(cull)


@validated
def merchantable_bark_volume_sound(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, *, stdorgcd=None):
    # Bark is unaffected by cull (cull is rotten WOOD).
    v_tot = total_bark_wood_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
    r_1, r_eff_mer, _ = _effective_ratios(spcd, dia, ht, division, ah, stdorgcd=stdorgcd)
    return (r_eff_mer - r_1) * v_tot


@validated
def merchantable_outside_bark_volume_sound(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, *, stdorgcd=None):
    return (
        merchantable_inside_bark_volume_sound(spcd, dia, ht, division, cull, ah, decaycd, stdorgcd=stdorgcd)
        + merchantable_bark_volume_sound(spcd, dia, ht, division, cull, ah, decaycd, stdorgcd=stdorgcd)
    )


@validated
def stump_inside_bark_volume_sound(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, *, stdorgcd=None):
    v_tot = total_inside_bark_wood_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
    r_1 = stump_volume_ratio(spcd, dia, ht, division, stdorgcd=stdorgcd)
    return r_1 * v_tot * _cull_factor(cull)


@validated
def stump_outside_bark_volume_sound(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, *, stdorgcd=None):
    v_tot_bk = total_bark_wood_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
    r_1 = stump_volume_ratio(spcd, dia, ht, division, stdorgcd=stdorgcd)
    return (
        stump_inside_bark_volume_sound(spcd, dia, ht, division, cull, ah, decaycd, stdorgcd=stdorgcd)
        + r_1 * v_tot_bk
    )


@validated
def top_inside_bark_volume_sound(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, *, stdorgcd=None):
    v_tot = total_inside_bark_wood_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
    _, _, r_eff_top = _effective_ratios(spcd, dia, ht, division, ah, stdorgcd=stdorgcd)
    return r_eff_top * v_tot * _cull_factor(cull)


@validated
def top_bark_volume_sound(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, *, stdorgcd=None):
    v_tot_bk = total_bark_wood_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
    _, _, r_eff_top = _effective_ratios(spcd, dia, ht, division, ah, stdorgcd=stdorgcd)
    return r_eff_top * v_tot_bk


@validated
def top_outside_bark_volume_sound(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, *, stdorgcd=None):
    return (
        top_inside_bark_volume_sound(spcd, dia, ht, division, cull, ah, decaycd, stdorgcd=stdorgcd)
        + top_bark_volume_sound(spcd, dia, ht, division, cull, ah, decaycd, stdorgcd=stdorgcd)
    )


@validated
def total_inside_bark_wood_volume_sound(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, *, stdorgcd=None):
    return (
        merchantable_inside_bark_volume_sound(spcd, dia, ht, division, cull, ah, decaycd, stdorgcd=stdorgcd)
        + stump_inside_bark_volume_sound(spcd, dia, ht, division, cull, ah, decaycd, stdorgcd=stdorgcd)
        + top_inside_bark_volume_sound(spcd, dia, ht, division, cull, ah, decaycd, stdorgcd=stdorgcd)
    )


@validated
def total_bark_volume_sound(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, *, stdorgcd=None):
    # No cull on bark; only broken-top reduction (via R_b).
    v_tot_bk = total_bark_wood_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
    r_b = _broken_top_ratio(spcd, dia, ht, division, ah, stdorgcd=stdorgcd)
    return v_tot_bk * r_b


@validated
def total_outside_bark_volume_sound(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, *, stdorgcd=None):
    return (
        total_inside_bark_wood_volume_sound(spcd, dia, ht, division, cull, ah, decaycd, stdorgcd=stdorgcd)
        + total_bark_volume_sound(spcd, dia, ht, division, cull, ah, decaycd, stdorgcd=stdorgcd)
    )


# ----- Helpers for broken-top geometry -----


def _decay_class(decaycd):
    """DECAYCD as an int array, with missing values meaning "live".

    FIADB populates DECAYCD only for standing dead trees -- live trees carry
    NULL -- so a caller joining FIA data naturally has NaN or None for every
    live tree. Mapping missing to 0 makes that the documented behaviour
    instead of an accident: ``np.asarray(nan_array, dtype=int)`` performs an
    unsafe cast that happens to land on 0 (with a RuntimeWarning), and
    ``np.asarray(None, dtype=int)`` raises outright. Out-of-range values are
    rejected up front by nsvb.validation.check_decaycd.
    """
    if decaycd is None:
        return np.asarray(0, dtype=int)
    values = np.asarray(decaycd, dtype=float)
    return np.where(np.isnan(values), 0, values).astype(int)


def _dead_tree_props_scalar(spcd_val, decaycd_val):
    """(DensProp, BarkProp, BranchProp) from Table 1 for one tree.

    Returns (1, 1, 1) for live trees (decaycd=0) so the formula degenerates
    to no reduction.
    """
    if decaycd_val <= 0:
        return 1.0, 1.0, 1.0
    cls = "H" if spcd_val >= _HARDWOOD_SPCD_THRESHOLD else "S"
    props = WOOD_DENSITY_PROPORTIONS[(cls, int(decaycd_val))]
    return props["DensProp"], props["BarkProp"], props["BranchProp"]


# DECAYCD=3 corresponds to the "rotten cull" density-reduction proportion
# applied to LIVE-tree cull (Harmon et al. 2011, GTR table 1).
_CULL_DECAYCD = 3


def _live_cull_dens_prop(spcd):
    """DensProp at DECAYCD=3 used when reducing live-tree cull weight."""
    spcd_arr = np.atleast_1d(spcd)
    out = np.empty(spcd_arr.shape, dtype=float)
    for i, s in enumerate(spcd_arr.flat):
        cls = "H" if int(s) >= _HARDWOOD_SPCD_THRESHOLD else "S"
        out.flat[i] = WOOD_DENSITY_PROPORTIONS[(cls, _CULL_DECAYCD)]["DensProp"]
    if np.ndim(spcd) == 0:
        return out.item()
    return out.reshape(spcd_arr.shape)


_dead_props = np.vectorize(_dead_tree_props_scalar, otypes=[float, float, float])


def crown_ratio_at_h(ht, ah, cr):
    """CRH: user-supplied crown ratio (measured relative to AH) standardized
    to total height H. Formula: ``[H - AH(1 - CR)] / H``."""
    return (np.asarray(ht) - np.asarray(ah) * (1.0 - np.asarray(cr))) / np.asarray(ht)


def _resolved_crh_scalar(spcd_val, ht_val, ah_val, cr_val, province_val):
    """Returns the crown ratio standardized to H, ready for use in
    BranchRem / FoliageRem. NaN if the tree has no broken top.

    If ``cr_val`` is finite (user supplied), standardize via crown_ratio_at_h.
    Otherwise look up the default from Table S11 by (province, hardwood).
    """
    if not np.isfinite(ah_val):
        return np.nan
    if np.isfinite(cr_val):
        return (ht_val - ah_val * (1.0 - cr_val)) / ht_val
    hwd = bool(spcd_val >= _HARDWOOD_SPCD_THRESHOLD)
    key = str(province_val)
    if (key, hwd) in CROWN_RATIO_DEFAULTS:
        return CROWN_RATIO_DEFAULTS[(key, hwd)]
    # Caller may have passed a DIVISION instead of a PROVINCE; resolve via
    # eco_div_prov and retry once. Last-resort fallback is "UNDEFINED" which
    # S11 stores explicitly.
    translated = ECO_DIV_PROV.get(key)
    if translated is not None and (translated, hwd) in CROWN_RATIO_DEFAULTS:
        return CROWN_RATIO_DEFAULTS[(translated, hwd)]
    return CROWN_RATIO_DEFAULTS.get(("UNDEFINED", hwd), np.nan)


_resolved_crh = np.vectorize(_resolved_crh_scalar, otypes=[float])


def _warn_province_fallback(spcd, ah, cr, province):
    """Warn when a Table S11 default crown ratio is resolved by guesswork.

    The S11 lookup only runs for broken-top trees with no observed crown
    ratio -- which per GTR p.12 is exactly the dead-tree case. It is also the
    most error-prone argument in the API: ``province`` sits beside
    ``division``, and passing a DIVISION where a PROVINCE is expected is
    silently absorbed by the eco_div_prov translation, which keeps an
    arbitrary first-match province per division (M240 -> M241) and shifts
    branch biomass by ~27 percent with no signal. Omitting ``province``
    entirely falls through to the S11 UNDEFINED row, equally silently.

    Raised once per call rather than once per tree, so a vectorized run over a
    million rows emits one warning rather than a million.
    """
    ah_arr = np.asarray(np.nan if ah is None else ah, dtype=float)
    cr_arr = np.asarray(np.nan if cr is None else cr, dtype=float)
    needs_default = np.isfinite(ah_arr) & ~np.isfinite(cr_arr)
    if not np.any(needs_default):
        return

    prov_arr = np.asarray("" if province is None else province)
    hwd_arr = np.asarray(spcd) >= _HARDWOOD_SPCD_THRESHOLD

    # Only inspect the trees that will actually consult S11. A vectorized call
    # routinely mixes intact-top trees (which never reach the lookup) with
    # broken-top ones, and warning about the former would fire on every batch.
    mask, provs, hwds = np.broadcast_arrays(needs_default, prov_arr, hwd_arr)

    translated, undefined = set(), set()
    for flag, prov, hwd in zip(np.ravel(mask), np.ravel(provs), np.ravel(hwds)):
        if not flag:
            continue
        key = str(prov)
        if (key, bool(hwd)) in CROWN_RATIO_DEFAULTS:
            continue
        if ECO_DIV_PROV.get(key) is not None and \
                (ECO_DIV_PROV[key], bool(hwd)) in CROWN_RATIO_DEFAULTS:
            translated.add(key)
        else:
            undefined.add(key)

    if translated:
        warnings.warn(
            f"province={sorted(translated)!r} looks like an ecological DIVISION, "
            f"not a PROVINCE. Table S11 crown ratios are keyed by province; "
            f"resolving via the first province listed for that division "
            f"({', '.join(f'{k} -> {ECO_DIV_PROV[k]}' for k in sorted(translated))}), "
            f"which is arbitrary and can shift branch and foliage biomass "
            f"materially. Pass the tree's PROVINCE for an exact match.",
            UserWarning,
            stacklevel=3,
        )
    if undefined:
        shown = sorted(undefined)
        warnings.warn(
            f"no Table S11 crown ratio for province={shown!r}; falling back to "
            f"the S11 UNDEFINED national mean. This affects broken-top trees "
            f"with no observed crown ratio (per GTR p.12, the standing-dead "
            f"case). Pass province= to use the regional mean instead.",
            UserWarning,
            stacklevel=3,
        )


def branch_remainder(ht, ah, crh):
    """BranchRem: proportion of branch wood remaining after a broken top.

    Formula (GTR): ``[AH - H(1 - CRH)] / (H * CRH)``, clamped to ``[0, 1]``.

    ``crh`` must already be standardized to total height H (use
    :func:`crown_ratio_at_h` for a user-observed crown ratio, or the
    Table S11 default).

    The clamp matters, and only on the Table S11 default-CR path. When ``crh``
    comes from an observed crown ratio, ``crown_ratio_at_h`` derives it from
    ``ah`` itself, so ``H*CRH = H - AH + AH*CR`` and the formula reduces to
    ``AH*CR / (H - AH + AH*CR)`` -- inside [0, 1] for any ``0 < AH <= H``. But
    a Table S11 default is a stand-level mean with no relationship to this
    tree's ``ah``, so nothing prevents ``AH < H(1 - CRH)``: a break below the
    base of the crown. The raw formula then returns a negative "proportion",
    which propagates into negative branch mass and can drive AGB below zero.

    Geometrically a break below the crown base means no branch wood survives,
    so 0 is the correct floor. The GTR does not state the clamp because its
    Example 3 (the only one using an S11 default) happens to sit 3.6 ft above
    the sign change; see GTR p.38, which lists nonlinear branch/foliage
    reductions for broken-top trees as future work, confirming the linear form
    is intended -- just not below zero.

    NaN propagates unchanged, so callers can keep using it to mark trees with
    no broken top.
    """
    ht = np.asarray(ht, dtype=float)
    ah = np.asarray(ah, dtype=float)
    crh = np.asarray(crh, dtype=float)
    return np.clip((ah - ht * (1.0 - crh)) / (ht * crh), 0.0, 1.0)


def foliage_remainder(ht, ah, crh):
    """FoliageRem: same formula as :func:`branch_remainder` -- the GTR uses
    one geometric proportion for both branch and foliage truncation, so the
    same ``[0, 1]`` clamp applies."""
    return branch_remainder(ht, ah, crh)


# ----- Step 7-9 (reduced): weights with cull / dead / broken-top reductions -----
#
# Unified weight reduction for stem wood (eqn / GTR text per example):
#
#   LIVE intact:        W_ib_red = V_tot_ib_gross * (1 - cull/100*(1-DensProp_3)) * WDSG * 62.4
#   LIVE broken top:    W_ib_red = (V_tot_ib_gross - V_miss_ib) * (1 - cull/100*(1-DensProp_3))
#                                  * WDSG * 62.4
#   DEAD (any):         W_ib_red = V_tot_ib_sound / (1 - cull/100) * WDSG * DensProp_decay * 62.4
#
# (For dead trees, cull is already accounted for in the density reduction,
#  so the cull-grossed V_tot_ib_sound is used.)


@validated
def total_stem_wood_dry_weight_reduced(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, *, stdorgcd=None):
    """Wtotibred -- step 7 with all reductions applied: live cull deduction,
    dead-tree density reduction, and broken-top volume loss."""
    spcd = np.asarray(spcd)
    cull = np.asarray(cull, dtype=float)
    decaycd_arr = _decay_class(decaycd)

    wdsg = _wdsg(spcd)

    v_tot_ib_gross = total_inside_bark_wood_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
    r_b = _broken_top_ratio(spcd, dia, ht, division, ah, stdorgcd=stdorgcd)

    # Live branch: cull-deducted weight on the (possibly broken) tree
    dens_prop_3 = _live_cull_dens_prop(spcd)
    live_factor = 1.0 - cull / 100.0 * (1.0 - dens_prop_3)
    v_live = v_tot_ib_gross * r_b  # missing-top loss baked in (r_b=1 for intact)
    w_live = v_live * live_factor * wdsg * WEIGHT_CUBIC_FOOT_WATER

    # Dead branch: density reduction takes over from cull
    dens_prop_d, _, _ = _dead_props(spcd, decaycd_arr)
    w_dead = v_tot_ib_gross * r_b * wdsg * dens_prop_d * WEIGHT_CUBIC_FOOT_WATER

    return np.where(decaycd_arr > 0, w_dead, w_live)


@validated
def total_stem_bark_weight_reduced(spcd, dia, ht, division="", ah=None, decaycd=0, *, stdorgcd=None):
    """Wtotbkred -- step 8. Unified form across all trees:
        W_bk_red = W_bk_gross * R_b * DensProp * BarkProp
    where R_b = 1 for intact and DensProp, BarkProp = 1 for live."""
    w_bk = total_stem_bark_weight(spcd, dia, ht, division, stdorgcd=stdorgcd)
    r_b = _broken_top_ratio(spcd, dia, ht, division, ah, stdorgcd=stdorgcd)
    dens_prop, bark_prop, _ = _dead_props(spcd, _decay_class(decaycd))
    return w_bk * r_b * dens_prop * bark_prop


@validated
def total_stem_outside_bark_weight_reduced(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, *, stdorgcd=None):
    """Wtotobred = Wtotibred + Wtotbkred."""
    return (
        total_stem_wood_dry_weight_reduced(spcd, dia, ht, division, cull, ah, decaycd, stdorgcd=stdorgcd)
        + total_stem_bark_weight_reduced(spcd, dia, ht, division, ah, decaycd, stdorgcd=stdorgcd)
    )


@validated
def total_branch_weight_reduced(spcd, dia, ht, division="", ah=None, decaycd=0, cr=None, province="", *, stdorgcd=None):
    """Wbranchred -- step 9.

    Unified form:
        W_branch_red = W_branch * DensProp * BranchProp * BranchRem
    where DensProp, BranchProp = 1 for live, and BranchRem = 1 for intact.
    For broken-top trees, BranchRem uses the H-standardized crown ratio
    (from user-supplied CR if given, else Table S11 default keyed by
    (province, hardwood)).
    """
    w_branch = total_branch_weight(spcd, dia, ht, division, stdorgcd=stdorgcd)
    dens_prop, _, branch_prop = _dead_props(spcd, _decay_class(decaycd))

    _warn_province_fallback(spcd, ah, cr, province)

    ah_arr = np.asarray(np.nan if ah is None else ah, dtype=float)
    cr_arr = np.asarray(np.nan if cr is None else cr, dtype=float)
    prov_arr = np.asarray("" if province is None else province)

    crh = _resolved_crh(spcd, ht, ah_arr, cr_arr, prov_arr)
    branch_rem = np.where(np.isfinite(crh), branch_remainder(ht, ah_arr, crh), 1.0)

    return w_branch * dens_prop * branch_prop * branch_rem


@validated
def total_foliage_dry_weight_reduced(spcd, dia, ht, division="", ah=None, decaycd=0, cr=None, province="", *, stdorgcd=None):
    """Wfoliagered -- step 15.

    Dead trees: zero by GTR rule. Live trees: gross foliage * FoliageRem
    (FoliageRem = 1 for intact tops). Same H-standardized crown-ratio
    resolution as :func:`total_branch_weight_reduced`, and deliberately the
    same ``(ah, decaycd, cr, province)`` parameter order -- these two are the
    natural pair to call together, and a mismatched ordering made a positional
    call silently return 0.0 (``cr=0`` reading as a live tree, ``decaycd=0.3``
    truncating to 0) rather than raising.
    """
    w_foliage = total_foliage_dry_weight(spcd, dia, ht, division, stdorgcd=stdorgcd)
    decaycd_arr = _decay_class(decaycd)

    _warn_province_fallback(spcd, ah, cr, province)

    ah_arr = np.asarray(np.nan if ah is None else ah, dtype=float)
    cr_arr = np.asarray(np.nan if cr is None else cr, dtype=float)
    prov_arr = np.asarray("" if province is None else province)

    crh = _resolved_crh(spcd, ht, ah_arr, cr_arr, prov_arr)
    foliage_rem = np.where(np.isfinite(crh), foliage_remainder(ht, ah_arr, crh), 1.0)

    w_live = w_foliage * foliage_rem
    return np.where(decaycd_arr > 0, 0.0, w_live)


# ----- Step 11-12: AGB harmonization -----
#
# Three independently-predicted stem-wood / stem-bark / branch weights need
# to be reconciled with an independently-predicted total aboveground
# biomass (S8 model). The GTR's protocol:
#   1. Sum the three REDUCED components -> AGBComponentred
#   2. Compute the reduction ratio AGBReduce = AGBComponentred / (sum of
#      the three GROSS components) to scale AGBPredicted (S8) by the same
#      proportional loss the components incurred
#   3. AGBPredictedred = AGBPredicted * AGBReduce
#   4. AGBDiff = AGBPredictedred - AGBComponentred (sign-aware: positive
#      when the S8 model predicts more than the sum of components)
#   5. Distribute AGBPredictedred proportionally across the three
#      components -> WoodHarmonized, BarkHarmonized, BranchHarmonized
#      which by construction sum to AGBPredictedred.


@validated
def agb_component_reduced(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, cr=None, province="", *, stdorgcd=None):
    """AGBComponentred = Wtotibred + Wtotbkred + Wbranchred (step 11)."""
    return (
        total_stem_wood_dry_weight_reduced(spcd, dia, ht, division, cull, ah, decaycd, stdorgcd=stdorgcd)
        + total_stem_bark_weight_reduced(spcd, dia, ht, division, ah, decaycd, stdorgcd=stdorgcd)
        + total_branch_weight_reduced(spcd, dia, ht, division, ah, decaycd, cr, province, stdorgcd=stdorgcd)
    )


@validated
def agb_reduce_factor(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, cr=None, province="", *, stdorgcd=None):
    """AGBReduce = AGBComponentred / (Wtotib + Wtotbk + Wbranch). Scales the
    independently-predicted AGB (S8) by the same proportional loss the
    components incurred. Step 11."""
    components_gross = (
        total_stem_wood_dry_weight(spcd, dia, ht, division, stdorgcd=stdorgcd)
        + total_stem_bark_weight(spcd, dia, ht, division, stdorgcd=stdorgcd)
        + total_branch_weight(spcd, dia, ht, division, stdorgcd=stdorgcd)
    )
    return agb_component_reduced(spcd, dia, ht, division, cull, ah, decaycd, cr, province, stdorgcd=stdorgcd) / components_gross


@validated
def agb_predicted_reduced(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, cr=None, province="", *, stdorgcd=None):
    """AGBPredictedred = AGBPredicted * AGBReduce. Step 11."""
    return (
        total_aboveground_biomass(spcd, dia, ht, division, stdorgcd=stdorgcd)
        * agb_reduce_factor(spcd, dia, ht, division, cull, ah, decaycd, cr, province, stdorgcd=stdorgcd)
    )


@validated
def agb_difference(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, cr=None, province="", *, stdorgcd=None):
    """AGBDiff = AGBPredictedred - AGBComponentred. Step 11."""
    return (
        agb_predicted_reduced(spcd, dia, ht, division, cull, ah, decaycd, cr, province, stdorgcd=stdorgcd)
        - agb_component_reduced(spcd, dia, ht, division, cull, ah, decaycd, cr, province, stdorgcd=stdorgcd)
    )


def _harmonize(component_red, spcd, dia, ht, division, cull, ah, decaycd, cr, province, *, stdorgcd=None):
    """Distribute AGBPredictedred proportionally to ``component_red`` (one
    of Wtotibred, Wtotbkred, Wbranchred)."""
    agb_red = agb_predicted_reduced(spcd, dia, ht, division, cull, ah, decaycd, cr, province, stdorgcd=stdorgcd)
    agb_comp = agb_component_reduced(spcd, dia, ht, division, cull, ah, decaycd, cr, province, stdorgcd=stdorgcd)
    return agb_red * (component_red / agb_comp)


@validated
def harmonized_wood(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, cr=None, province="", *, stdorgcd=None):
    """WoodHarmonized -- step 12."""
    return _harmonize(
        total_stem_wood_dry_weight_reduced(spcd, dia, ht, division, cull, ah, decaycd, stdorgcd=stdorgcd),
        spcd, dia, ht, division, cull, ah, decaycd, cr, province,
        stdorgcd=stdorgcd,
    )


@validated
def harmonized_bark(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, cr=None, province="", *, stdorgcd=None):
    """BarkHarmonized -- step 12."""
    return _harmonize(
        total_stem_bark_weight_reduced(spcd, dia, ht, division, ah, decaycd, stdorgcd=stdorgcd),
        spcd, dia, ht, division, cull, ah, decaycd, cr, province,
        stdorgcd=stdorgcd,
    )


@validated
def harmonized_branch(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, cr=None, province="", *, stdorgcd=None):
    """BranchHarmonized -- step 12."""
    return _harmonize(
        total_branch_weight_reduced(spcd, dia, ht, division, ah, decaycd, cr, province, stdorgcd=stdorgcd),
        spcd, dia, ht, division, cull, ah, decaycd, cr, province,
        stdorgcd=stdorgcd,
    )


# ----- Step 13: adjusted densities -----
#
# The adjusted densities convert the (broken-top-reduced, not-cull-deducted)
# stem volumes into harmonized weights. The denominator -- the "volume basis"
# -- is the gross stem volume with broken-top loss removed but cull-grossed:
#
#   V_tot_ib_basis = V_tot_ib_gross * R_b
#   V_tot_bk_basis = V_tot_bk_gross * R_b
#
# For an intact-top tree R_b = 1 and the basis is the gross volume.
# For broken-top trees R_b < 1 and the basis is the remaining stem volume.
# In all cases cull is excluded from the basis: cull rot still contributes
# to weight via DensProp / harmonized mass distribution, so the volume basis
# must match the volume that physically exists.


def _v_tot_ib_basis(spcd, dia, ht, division, ah, *, stdorgcd=None):
    """V_tot_ib volume basis for WDSGAdj and merchantable / stump weights:
    broken-top reduced (R_b) but NOT cull-deducted."""
    v_tot = total_inside_bark_wood_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
    return v_tot * _broken_top_ratio(spcd, dia, ht, division, ah, stdorgcd=stdorgcd)


def _v_tot_bk_basis(spcd, dia, ht, division, ah, *, stdorgcd=None):
    """V_tot_bk basis for BKSGAdj: broken-top reduced. Bark is unaffected
    by cull, so the basis equals V_tot_bk_sound."""
    v_tot_bk = total_bark_wood_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)
    return v_tot_bk * _broken_top_ratio(spcd, dia, ht, division, ah, stdorgcd=stdorgcd)


@validated
def adjusted_wood_density(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, cr=None, province="", *, stdorgcd=None):
    """WDSGAdj = WoodHarmonized / V_tot_ib_basis / 62.4. Step 13."""
    return (
        harmonized_wood(spcd, dia, ht, division, cull, ah, decaycd, cr, province, stdorgcd=stdorgcd)
        / _v_tot_ib_basis(spcd, dia, ht, division, ah, stdorgcd=stdorgcd)
        / WEIGHT_CUBIC_FOOT_WATER
    )


@validated
def adjusted_bark_density(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, cr=None, province="", *, stdorgcd=None):
    """BKSGAdj = BarkHarmonized / V_tot_bk_basis / 62.4. Step 13."""
    return (
        harmonized_bark(spcd, dia, ht, division, cull, ah, decaycd, cr, province, stdorgcd=stdorgcd)
        / _v_tot_bk_basis(spcd, dia, ht, division, ah, stdorgcd=stdorgcd)
        / WEIGHT_CUBIC_FOOT_WATER
    )


# ----- Step 14: merchantable & stump weights from adjusted densities -----
#
# Each weight is the (broken-top reduced, NOT cull-deducted) volume of the
# subcomponent times the adjusted density times 62.4 lb/ft^3.
#
#   V_mer_ib_basis = (R_eff_mer - R_1) * V_tot_ib_gross
#   V_stump_ib_basis = R_1 * V_tot_ib_gross    (stump never broken)
#
# For bark, no cull deduction ever applies, so the basis equals the
# corresponding _sound volume.
#
# WHY THE GROSS BASIS, AND NOT EXAMPLE 3'S PROSE. Example 3 (GTR p.20) writes
#
#   Wmerib = (VtotibSound/(1 - CULL/100) - VstumpibSound - VtopibSound)
#            * WDSGAdj * 62.4
#
# which mixes bases: the first term is cull-grossed (it equals R_b * V_tot_ib)
# while the two subtracted terms carry (1 - CULL/100) by their own definitions.
#
# Example 3's arithmetic does not follow its own prose. It substitutes
# 0.910282866061 for "VstumpibSound" -- twice, once here and again in Wstumpib
# -- and that value is VstumpibGross; VstumpibSound was computed as
# 0.819254579455 two steps earlier. So the published 163.031163476092 /
# 24.169078597057 match the cull-GROSSED reading implemented here. Taking the
# prose literally would give 165.448071 / 21.752171 instead.
#
# Example 4 (GTR p.25) then states the rule outright for the AH > h_m case, in
# both prose and arithmetic: "Wmerib = VmeribGross * WDSGAdj * 62.4" and
# "Wstumpib = VstumpibGross * WDSGAdj * 62.4", where VmeribGross = (R_m - R_1)
# * V_tot_ib and VstumpibGross = R_1 * V_tot_ib -- exactly _v_mer_ib_basis and
# _v_stump_ib_basis below. This is not a deviation from the GTR; it follows
# Example 4 where Example 3's prose contradicts it.
#
# Note what is NOT at stake: additivity. The literal form defines Wmerib by
# subtraction from the cull-grossed total, so Wmerib + Wstumpib + Wtopib
# telescopes to R_b * V_tot_ib * WDSGAdj * 62.4 = WoodHarmonized either way.
# The literal form MISALLOCATES rather than losing mass -- for CULL > 0 it
# inflates the bole by CULL/100 * (R_1 + R_b - R_m) * V_tot_ib * WDSGAdj * 62.4
# at the expense of the stump (CULL/100 * R_1 * ...) and the top
# (CULL/100 * (R_b - R_m) * ...). Example 3 cannot expose the top part of that
# because its VtopibSound is 0, but the stump part is visible in its published
# numbers, which is precisely how the prose/arithmetic mismatch above is
# established.
#
# What the gross basis does buy is R_eff_mer + R_eff_top == R_b exactly, which
# is what keeps the subcomponent volumes additive; see TestAdditivity in
# tests/test_properties.py.


def _v_mer_ib_basis(spcd, dia, ht, division, ah, *, stdorgcd=None):
    """Merchantable IB volume: (R_eff_mer - R_1) * V_tot_ib_gross."""
    r_1, r_eff_mer, _ = _effective_ratios(spcd, dia, ht, division, ah, stdorgcd=stdorgcd)
    return (r_eff_mer - r_1) * total_inside_bark_wood_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)


def _v_stump_ib_basis(spcd, dia, ht, division, *, stdorgcd=None):
    """Stump IB volume: R_1 * V_tot_ib_gross. Broken-top doesn't affect the
    stump."""
    return stump_volume_ratio(spcd, dia, ht, division, stdorgcd=stdorgcd) * total_inside_bark_wood_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)


def _v_stump_bk_basis(spcd, dia, ht, division, *, stdorgcd=None):
    """Stump BK volume: R_1 * V_tot_bk_gross."""
    return stump_volume_ratio(spcd, dia, ht, division, stdorgcd=stdorgcd) * total_bark_wood_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)


@validated
def merchantable_wood_weight(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, cr=None, province="", *, stdorgcd=None):
    """Wmerib -- step 14."""
    return (
        _v_mer_ib_basis(spcd, dia, ht, division, ah, stdorgcd=stdorgcd)
        * adjusted_wood_density(spcd, dia, ht, division, cull, ah, decaycd, cr, province, stdorgcd=stdorgcd)
        * WEIGHT_CUBIC_FOOT_WATER
    )


@validated
def merchantable_bark_weight(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, cr=None, province="", *, stdorgcd=None):
    """Wmerbk -- step 14. Bark sees no cull deduction, so the volume basis
    equals merchantable_bark_volume_sound."""
    return (
        merchantable_bark_volume_sound(spcd, dia, ht, division, cull, ah, decaycd, stdorgcd=stdorgcd)
        * adjusted_bark_density(spcd, dia, ht, division, cull, ah, decaycd, cr, province, stdorgcd=stdorgcd)
        * WEIGHT_CUBIC_FOOT_WATER
    )


@validated
def merchantable_outside_bark_weight(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, cr=None, province="", *, stdorgcd=None):
    """Wmerob = Wmerib + Wmerbk -- step 14. Equivalent to FIADB DRYBIO_BOLE."""
    return (
        merchantable_wood_weight(spcd, dia, ht, division, cull, ah, decaycd, cr, province, stdorgcd=stdorgcd)
        + merchantable_bark_weight(spcd, dia, ht, division, cull, ah, decaycd, cr, province, stdorgcd=stdorgcd)
    )


# ----- Step 14 (sawlog portion): FIADB DRYBIO_SAWLOG -----
#
# The GTR computes sawlog *volumes* in all four worked examples (1-foot stump
# to a 7-inch top outside bark for softwoods, 9-inch for hardwoods) but never
# converts them to weight. The conversion is the same one step 14 already
# applies to the merchantable bole: multiply the sawlog volume basis by the
# harmonized adjusted density. Using WDSGAdj / BKSGAdj rather than the raw
# WDSG keeps the sawlog weight consistent with the harmonized totals, so
# sawlog <= bole <= total holds by construction.
#
# Sawlog quantities are undefined (NaN) below the FIA sawtimber threshold --
# DBH 9 in for softwoods, 11 in for hardwoods -- because there is no sawlog
# top diameter on the stem. That differs deliberately from the sapling rule
# for the merchantable bole, where the GTR states outright (p.32) that no
# merchantable volume is present and the stump/top partition still has to
# close. Nothing downstream consumes the sawlog portion, the GTR makes no
# equivalent statement, and NaN matches FIADB, which leaves DRYBIO_SAWLOG
# NULL for non-sawtimber trees.


def _effective_sawlog_ratio(spcd, dia, ht, division, ah, *, stdorgcd=None):
    """(R_1, R_eff_saw): the stump and sawlog proportions, accounting for a
    broken top that truncates the sawlog portion (AH below h_s)."""
    r_1 = stump_volume_ratio(spcd, dia, ht, division, stdorgcd=stdorgcd)
    r_s = sawlog_volume_ratio(spcd, dia, ht, division, stdorgcd=stdorgcd)
    r_b = _broken_top_ratio(spcd, dia, ht, division, ah, stdorgcd=stdorgcd)
    return r_1, np.minimum(r_s, r_b)


def _v_saw_ib_basis(spcd, dia, ht, division, ah, *, stdorgcd=None):
    """Sawlog IB volume: (R_eff_saw - R_1) * V_tot_ib_gross. Broken-top
    reduced but NOT cull-deducted, matching the merchantable basis."""
    r_1, r_eff_saw = _effective_sawlog_ratio(spcd, dia, ht, division, ah, stdorgcd=stdorgcd)
    return (r_eff_saw - r_1) * total_inside_bark_wood_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)


@validated
def sawlog_inside_bark_volume_sound(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, *, stdorgcd=None):
    """Vsawib with cull and broken-top deductions."""
    return _v_saw_ib_basis(spcd, dia, ht, division, ah, stdorgcd=stdorgcd) * _cull_factor(cull)


@validated
def sawlog_bark_volume_sound(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, *, stdorgcd=None):
    """Vsawbk with broken-top deduction. Bark is unaffected by wood cull."""
    r_1, r_eff_saw = _effective_sawlog_ratio(spcd, dia, ht, division, ah, stdorgcd=stdorgcd)
    return (r_eff_saw - r_1) * total_bark_wood_volume(spcd, dia, ht, division, stdorgcd=stdorgcd)


@validated
def sawlog_outside_bark_volume_sound(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, *, stdorgcd=None):
    return (
        sawlog_inside_bark_volume_sound(spcd, dia, ht, division, cull, ah, decaycd, stdorgcd=stdorgcd)
        + sawlog_bark_volume_sound(spcd, dia, ht, division, cull, ah, decaycd, stdorgcd=stdorgcd)
    )


@validated
def sawlog_wood_weight(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, cr=None, province="", *, stdorgcd=None):
    """Wsawib -- sawlog stem wood weight, from the adjusted wood density."""
    return (
        _v_saw_ib_basis(spcd, dia, ht, division, ah, stdorgcd=stdorgcd)
        * adjusted_wood_density(spcd, dia, ht, division, cull, ah, decaycd, cr, province, stdorgcd=stdorgcd)
        * WEIGHT_CUBIC_FOOT_WATER
    )


@validated
def sawlog_bark_weight(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, cr=None, province="", *, stdorgcd=None):
    """Wsawbk -- sawlog stem bark weight. Bark sees no cull deduction, so the
    volume basis equals sawlog_bark_volume_sound."""
    return (
        sawlog_bark_volume_sound(spcd, dia, ht, division, cull, ah, decaycd, stdorgcd=stdorgcd)
        * adjusted_bark_density(spcd, dia, ht, division, cull, ah, decaycd, cr, province, stdorgcd=stdorgcd)
        * WEIGHT_CUBIC_FOOT_WATER
    )


@validated
def sawlog_outside_bark_weight(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, cr=None, province="", *, stdorgcd=None):
    """Wsawob = Wsawib + Wsawbk. Equivalent to FIADB DRYBIO_SAWLOG."""
    return (
        sawlog_wood_weight(spcd, dia, ht, division, cull, ah, decaycd, cr, province, stdorgcd=stdorgcd)
        + sawlog_bark_weight(spcd, dia, ht, division, cull, ah, decaycd, cr, province, stdorgcd=stdorgcd)
    )


@validated
def stump_wood_weight(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, cr=None, province="", *, stdorgcd=None):
    """Wstumpib -- step 14."""
    return (
        _v_stump_ib_basis(spcd, dia, ht, division, stdorgcd=stdorgcd)
        * adjusted_wood_density(spcd, dia, ht, division, cull, ah, decaycd, cr, province, stdorgcd=stdorgcd)
        * WEIGHT_CUBIC_FOOT_WATER
    )


@validated
def stump_bark_weight(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, cr=None, province="", *, stdorgcd=None):
    """Wstumpbk -- step 14."""
    return (
        _v_stump_bk_basis(spcd, dia, ht, division, stdorgcd=stdorgcd)
        * adjusted_bark_density(spcd, dia, ht, division, cull, ah, decaycd, cr, province, stdorgcd=stdorgcd)
        * WEIGHT_CUBIC_FOOT_WATER
    )


@validated
def stump_outside_bark_weight(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, cr=None, province="", *, stdorgcd=None):
    """Wstumpob = Wstumpib + Wstumpbk -- step 14. Equivalent to FIADB DRYBIO_STUMP."""
    return (
        stump_wood_weight(spcd, dia, ht, division, cull, ah, decaycd, cr, province, stdorgcd=stdorgcd)
        + stump_bark_weight(spcd, dia, ht, division, cull, ah, decaycd, cr, province, stdorgcd=stdorgcd)
    )


# ----- Step 16: top biomass -----


@validated
def drybio_top(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, cr=None, province="", *, stdorgcd=None):
    """DRYBIO_TOP = AGBPredictedred - Wmerob - Wstumpob.

    Top-and-limbs dry biomass: the harmonized AGB minus the merchantable
    bole and stump. Step 16. Equivalent to FIADB DRYBIO_TOP."""
    return (
        agb_predicted_reduced(spcd, dia, ht, division, cull, ah, decaycd, cr, province, stdorgcd=stdorgcd)
        - merchantable_outside_bark_weight(spcd, dia, ht, division, cull, ah, decaycd, cr, province, stdorgcd=stdorgcd)
        - stump_outside_bark_weight(spcd, dia, ht, division, cull, ah, decaycd, cr, province, stdorgcd=stdorgcd)
    )


# ----- Step 17: carbon content -----


def _carbon_fraction_scalar(spcd_val, decaycd_val):
    """CF (decimal) for one tree. Live: S10a by SPCD, falling back to the
    species' Jenkins-group mean for the one species S10a omits. Dead: S10b by
    (DECAYCD, hardwood)."""
    if decaycd_val <= 0:
        spcd_int = int(spcd_val)
        try:
            return CARBON_FRACTION_LIVE[spcd_int]
        except KeyError:
            group = int(float(REF_SPECIES[spcd_int]["JENKINS_SPGRPCD"]))
            return CARBON_FRACTION_LIVE_BY_JENKINS[group]
    hwd = int(spcd_val) >= _HARDWOOD_SPCD_THRESHOLD
    return CARBON_FRACTION_DEAD[(int(decaycd_val), bool(hwd))]


_carbon_fraction = np.vectorize(_carbon_fraction_scalar, otypes=[float])


@validated
def carbon_content(spcd, dia, ht, division="", cull=0.0, ah=None, decaycd=0, cr=None, province="", *, stdorgcd=None):
    """Carbon content (lb) = AGBPredictedred * CF (table S10a for live,
    S10b for dead). Step 17."""
    cf = _carbon_fraction(spcd, _decay_class(decaycd))
    return (
        agb_predicted_reduced(spcd, dia, ht, division, cull, ah, decaycd, cr, province, stdorgcd=stdorgcd)
        * cf
    )
