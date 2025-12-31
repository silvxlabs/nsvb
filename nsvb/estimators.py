from typing import Union

import numpy as np
from numpy.typing import ArrayLike, NDArray

from nsvb.models import MODEL_MAP
from nsvb.tables import (
    REF_SPECIES,
    TABLES,
    CARBON_FRACTIONS_LIVE,
    CARBON_FRACTIONS_DEAD,
    CROWN_RATIOS,
)

WEIGHT_CUBIC_FOOT_WATER = 62.4  # lb/ft^3


def _run_model_form(
    table_name: str,
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
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

    # Scalar implementation (unchanged)
    def _scalar_lookup(spcd_val, dia_val, ht_val, div_val):
        try:
            table_name_spcd = f"{table_name}a"
            table_data = TABLES[table_name_spcd]
            data = table_data.get((spcd_val, div_val), table_data[(spcd_val, "")])
        except KeyError:
            spgrp = int(REF_SPECIES[spcd_val]["JENKINS_SPGRPCD"])
            table_name_spgrp = f"{table_name}b"
            table_data = TABLES[table_name_spgrp]
            data = table_data.get(spgrp)
            wdsg = float(REF_SPECIES[spcd_val]["WOOD_SPGR_GREENVOL_DRYWT"])
            data = data.copy()
            data["wdsg"] = wdsg
        model_function = MODEL_MAP[data["model"]]
        return model_function(dia_val, ht_val, **data)

    # Check if inputs are arrays
    is_array = (
        isinstance(spcd, np.ndarray)
        or isinstance(dia, np.ndarray)
        or isinstance(ht, np.ndarray)
    )

    if is_array:
        # Vectorize the scalar function
        vectorized_fn = np.vectorize(_scalar_lookup)
        return vectorized_fn(spcd, dia, ht, division)
    else:
        # Use scalar path directly
        return _scalar_lookup(int(spcd), float(dia), float(ht), str(division))


def total_inside_bark_wood_volume(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
    ah: Union[float, ArrayLike, None] = None,
) -> Union[float, NDArray]:
    """
    Predict gross total stem wood volume as a function of diameter at breast
    height (D) and total height (H). Use the appropriate model form and
    coefficients from table S1.

    GTR-WO-104 Step 1 (page 12): Predict gross total stem wood volume using
    Equations 1-5 (pages 10-11) with Table S1 coefficients.

    For trees with broken tops (ah < ht), applies volume ratio adjustment:
    VtotibBT = R(AH) × VtotibGross

    Where R(AH) is the cumulative volume ratio at actual height (GTR Equation 6).

    Parameters:
        spcd (int): FIA species code.
        dia (float): Diameter of the tree in inches (in).
        ht (float): Height of the tree in feet (ft).
        division (str, optional): Division code. Default is an empty string.
        ah (float, optional): Actual height for broken top trees (ft).
            If None or >= ht, returns full tree volume.

    Returns:
        float: Total inside bark wood volume in cubic feet (ft³).
    """
    # GTR-WO-104 Equations 1-5 (pages 10-11) with Table S1 coefficients
    v_gross = _run_model_form("s1", spcd, dia, ht, division)

    # Apply broken top adjustment if ah is provided
    if ah is not None:
        # GTR-WO-104 broken top adjustment: VtotibBT = R(AH) × VtotibGross
        r_ah = volume_ratio(spcd, ah, ht, division, bark="ib")
        return v_gross * r_ah

    return v_gross


def total_bark_wood_volume(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
    ah: Union[float, ArrayLike, None] = None,
) -> Union[float, NDArray]:
    """
    Predict gross total stem bark volume as a function of D and H. Uses the
    appropriate model form and coefficients from table S2.

    GTR-WO-104 Step 2 (page 12): Predict gross total stem bark volume using
    Equations 1-5 (pages 10-11) with Table S2 coefficients.

    For trees with broken tops (ah < ht), applies volume ratio adjustment:
    VtotbkBT = R(AH) × VtotbkGross

    Where R(AH) is the cumulative volume ratio at actual height using
    outside-bark coefficients (Table S4) since bark volume is outside the wood.

    Parameters:
        spcd (int): FIA species code.
        dia (float): Diameter of the tree in inches (in).
        ht (float): Height of the tree in feet (ft).
        division (str, optional): Division code. Default is an empty string.
        ah (float, optional): Actual height for broken top trees (ft).
            If None or >= ht, returns full tree bark volume.

    Returns:
        float: Total bark volume in cubic feet (ft³).
    """
    # GTR-WO-104 Equations 1-5 (pages 10-11) with Table S2 coefficients
    v_gross = _run_model_form("s2", spcd, dia, ht, division)

    # Apply broken top adjustment if ah is provided
    if ah is not None:
        # For bark volume, use outside-bark volume ratio (S4)
        r_ah = volume_ratio(spcd, ah, ht, division, bark="ob")
        return v_gross * r_ah

    return v_gross


def total_outside_bark_volume(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
) -> Union[float, NDArray]:
    """
    Obtain gross total stem outside-bark volume as the sum of wood and bark
    gross volumes.

    GTR-WO-104 Step 3 (page 12): VtotobGross = VtotibGross + VtotbkGross

    Parameters:
        spcd (int): FIA species code.
        dia (float): Diameter of the tree in inches (in).
        ht (float): Height of the tree in feet (ft).
        division (str, optional): Division code. Default is an empty string.

    Returns:
        float: Total outside bark volume in cubic feet (ft³).
    """
    # GTR-WO-104 Step 3 (page 12): VtotobGross = VtotibGross + VtotbkGross
    v_tot_ib = total_inside_bark_wood_volume(spcd, dia, ht, division)
    v_tot_bk = total_bark_wood_volume(spcd, dia, ht, division)
    return v_tot_ib + v_tot_bk


def total_stem_wood_dry_weight(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
    cull: Union[float, ArrayLike] = 0,
    ah: Union[float, ArrayLike, None] = None,
    decaycd: Union[int, ArrayLike, None] = None,
) -> Union[float, NDArray]:
    """
    Convert total stem wood gross volume to biomass weight using published
    wood density values (Miles and Smith 2009). Reduce stem wood weight due
    to broken top, cull deductions (accounting for nonzero weight of cull),
    and dead tree wood density reduction.

    GTR-WO-104 Step 7 (page 13): WstemwdGross = VtotibGross × SGwd × 62.4

    For live trees with cull (CULL > 0%), applies cull deduction per GTR page 23:
    WstemwdGross × [1 - CULL/100 × (1 - DensProp)]

    For dead trees (decaycd provided), per GTR Example 3 (page 19):
    Wtotibred = VtotibBT × WDSG × DensProp × 62.4

    Parameters:
        spcd (int): FIA species code.
        dia (float): Diameter of the tree in inches (in).
        ht (float): Height of the tree in feet (ft).
        division (str, optional): Division code. Default is an empty string.
        cull (float, optional): Rotten and missing cull percentage (0-100).
        ah (float, optional): Actual height for broken-top trees (ft).
        decaycd (int, optional): Decay class for dead trees (1-5).

    Returns:
        float: Total stem wood dry weight in pounds (lb).
    """
    # Check if array input
    is_array = isinstance(spcd, np.ndarray) or isinstance(dia, np.ndarray)

    # Scalar path
    if not is_array:
        wdsg = float(REF_SPECIES[spcd]["WOOD_SPGR_GREENVOL_DRYWT"])
        v_tot_ib = total_inside_bark_wood_volume(spcd, dia, ht, division, ah=ah)

        # Dead tree path (decaycd provided)
        if decaycd is not None:
            # GTR Example 3 (page 19): Wtotibred = VtotibBT × WDSG × DensProp × 62.4
            props = get_decay_proportions(spcd, decaycd)
            return v_tot_ib * wdsg * props["dens_prop"] * WEIGHT_CUBIC_FOOT_WATER

        # Live tree path
        if cull > 0:
            dens_prop = 0.54 if REF_SPECIES[spcd]["SFTWD_HRDWD"] == "H" else 0.92
            return (
                v_tot_ib
                * (1 - cull / 100 * (1 - dens_prop))
                * wdsg
                * WEIGHT_CUBIC_FOOT_WATER
            )
        return v_tot_ib * wdsg * WEIGHT_CUBIC_FOOT_WATER

    # Array path
    spcd_arr = np.atleast_1d(spcd)
    dia_arr = np.atleast_1d(dia)
    ht_arr = np.atleast_1d(ht)
    div_arr = np.atleast_1d(division)
    cull_arr = np.atleast_1d(cull)
    ah_arr = np.atleast_1d(ah) if ah is not None else None
    decaycd_arr = np.atleast_1d(decaycd) if decaycd is not None else None

    # Get volume (will be vectorized through _run_model_form)
    v_tot_ib = total_inside_bark_wood_volume(
        spcd_arr, dia_arr, ht_arr, div_arr, ah=ah_arr
    )

    # Vectorize lookups from REF_SPECIES
    wdsg_arr = np.array(
        [float(REF_SPECIES[int(s)]["WOOD_SPGR_GREENVOL_DRYWT"]) for s in spcd_arr]
    )

    # Dead tree path (decaycd provided)
    if decaycd_arr is not None:
        dens_prop_arr = np.array(
            [
                get_decay_proportions(int(s), int(d))["dens_prop"]
                for s, d in zip(spcd_arr, decaycd_arr)
            ]
        )
        return v_tot_ib * wdsg_arr * dens_prop_arr * WEIGHT_CUBIC_FOOT_WATER

    # Live tree path
    dens_prop_arr = np.array(
        [0.54 if REF_SPECIES[int(s)]["SFTWD_HRDWD"] == "H" else 0.92 for s in spcd_arr]
    )

    # Vectorized calculation
    weight = np.where(
        cull_arr > 0,
        v_tot_ib
        * (1 - cull_arr / 100 * (1 - dens_prop_arr))
        * wdsg_arr
        * WEIGHT_CUBIC_FOOT_WATER,
        v_tot_ib * wdsg_arr * WEIGHT_CUBIC_FOOT_WATER,
    )

    return weight


def total_stem_bark_weight(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
    ah: Union[float, ArrayLike, None] = None,
    decaycd: Union[int, ArrayLike, None] = None,
) -> Union[float, NDArray]:
    """
    Predict total stem bark biomass as a function of D and H. Use the
    appropriate model form and coefficients from Table S6.

    GTR-WO-104 Step 8 (page 13): Predict total stem bark biomass using
    Equations 1-5 (pages 10-11) with Table S6 coefficients.

    For trees with broken tops (ah < ht), applies volume ratio adjustment:
    Wtotbkred = Wtotbk × Rb

    Where Rb is the outside-bark volume ratio at actual height (Table S4).

    For dead trees (decaycd provided), applies bark proportion reduction
    from GTR Table 1: Wtotbkred = Wtotbk × BarkProp

    For dead trees with broken tops, both adjustments are applied:
    Wtotbkred = Wtotbk × Rb × DensProp × BarkProp

    Parameters:
        spcd (int): FIA species code.
        dia (float): Diameter of the tree in inches (in).
        ht (float): Height of the tree in feet (ft).
        division (str, optional): Division code. Default is an empty string.
        ah (float, optional): Actual height for broken top trees (ft).
        decaycd (int, optional): Decay class for dead trees (1-5).

    Returns:
        float: Total stem bark weight in pounds (lb).
    """
    # GTR-WO-104 Equations 1-5 (pages 10-11) with Table S6 coefficients
    weight = _run_model_form("s6", spcd, dia, ht, division)

    # Check if array input
    is_array = isinstance(spcd, np.ndarray) or isinstance(dia, np.ndarray)

    if not is_array:
        # Scalar path
        reduction = 1.0

        # Apply broken top adjustment
        if ah is not None:
            # GTR uses inside-bark volume ratio (Rm) for bark weight reduction
            rm = volume_ratio(spcd, ah, ht, division, bark="ib")
            reduction *= rm

        # Apply decay reduction for dead trees
        if decaycd is not None:
            props = get_decay_proportions(spcd, decaycd)
            # GTR Example 3: Wtotbkred = Wtotbk × Rm × DensProp × BarkProp
            reduction *= props["dens_prop"] * props["bark_prop"]

        return weight * reduction

    # Array path
    spcd_arr = np.atleast_1d(spcd)
    ah_arr = np.atleast_1d(ah) if ah is not None else None
    decaycd_arr = np.atleast_1d(decaycd) if decaycd is not None else None
    div_arr = np.atleast_1d(division)
    ht_arr = np.atleast_1d(ht)

    reduction = np.ones_like(weight, dtype=float)

    # Apply broken top adjustment
    if ah_arr is not None:
        rm = volume_ratio(spcd_arr, ah_arr, ht_arr, div_arr, bark="ib")
        reduction *= rm

    # Apply decay reduction for dead trees
    if decaycd_arr is not None:
        for i, (s, d) in enumerate(zip(spcd_arr, decaycd_arr)):
            props = get_decay_proportions(int(s), int(d))
            reduction[i] *= props["dens_prop"] * props["bark_prop"]

    return weight * reduction


def total_branch_weight(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
    ah: Union[float, ArrayLike, None] = None,
    cr: Union[float, ArrayLike, None] = None,
    decaycd: Union[int, ArrayLike, None] = None,
) -> Union[float, NDArray]:
    """
    Predict total branch biomass as a function of D and H. Use the
    appropriate model form and coefficients from Table S7.

    GTR-WO-104 Step 9 (page 13): Predict total branch biomass using
    Equations 1-5 (pages 10-11) with Table S7 coefficients.

    For trees with broken tops (ah < ht):
    - Live trees with observed CR: Calculate CRH and BranchRem
    - Dead trees: Look up CR from Table S11 and calculate BranchRem

    For dead trees (decaycd provided), applies additional reductions
    from GTR Table 1: Wbranchred = Wbranch × DensProp × BranchProp × BranchRem

    Parameters:
        spcd (int): FIA species code.
        dia (float): Diameter of the tree in inches (in).
        ht (float): Height of the tree in feet (ft).
        division (str, optional): Division code. Default is an empty string.
        ah (float, optional): Actual height for broken top trees (ft).
        cr (float, optional): Observed crown ratio (0-1) for live broken-top trees.
            If None and ah is provided, uses Table S11 lookup.
        decaycd (int, optional): Decay class for dead trees (1-5).

    Returns:
        float: Total branch weight in pounds (lb).
    """
    # GTR-WO-104 Equations 1-5 (pages 10-11) with Table S7 coefficients
    weight = _run_model_form("s7", spcd, dia, ht, division)

    # Check if array input
    is_array = isinstance(spcd, np.ndarray) or isinstance(dia, np.ndarray)

    if not is_array:
        # Scalar path
        reduction = 1.0

        # Apply broken top adjustment
        if ah is not None:
            if cr is not None:
                # Live tree with observed CR: calculate CRH then BranchRem
                crh = calculate_crh(ah, ht, cr)
                branch_rem = calculate_branch_foliage_remaining(ah, ht, crh)
            else:
                # Dead tree (or no CR provided): look up CR from Table S11
                cr_lookup = get_crown_ratio(spcd, division)
                # BranchRem = [AH - H × (1 - CR)] / (H × CR)
                branch_rem = (ah - ht * (1 - cr_lookup)) / (ht * cr_lookup)
            reduction *= branch_rem

        # Apply decay reduction for dead trees
        if decaycd is not None:
            props = get_decay_proportions(spcd, decaycd)
            # GTR Example 3: Wbranchred = Wbranch × DensProp × BranchProp × BranchRem
            reduction *= props["dens_prop"] * props["branch_prop"]

        return weight * reduction

    # Array path
    spcd_arr = np.atleast_1d(spcd)
    ht_arr = np.atleast_1d(ht)
    div_arr = np.atleast_1d(division)
    ah_arr = np.atleast_1d(ah) if ah is not None else None
    cr_arr = np.atleast_1d(cr) if cr is not None else None
    decaycd_arr = np.atleast_1d(decaycd) if decaycd is not None else None

    reduction = np.ones_like(weight, dtype=float)

    # Apply broken top adjustment
    if ah_arr is not None:
        for i, (s, h, d, a) in enumerate(zip(spcd_arr, ht_arr, div_arr, ah_arr)):
            if cr_arr is not None:
                # Live tree with observed CR
                crh = calculate_crh(a, h, cr_arr[i])
                branch_rem = calculate_branch_foliage_remaining(a, h, crh)
            else:
                # Dead tree or no CR: look up from S11
                cr_lookup = get_crown_ratio(int(s), str(d))
                branch_rem = (a - h * (1 - cr_lookup)) / (h * cr_lookup)
            reduction[i] *= branch_rem

    # Apply decay reduction for dead trees
    if decaycd_arr is not None:
        for i, (s, d) in enumerate(zip(spcd_arr, decaycd_arr)):
            props = get_decay_proportions(int(s), int(d))
            reduction[i] *= props["dens_prop"] * props["branch_prop"]

    return weight * reduction


def total_aboveground_biomass(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
) -> Union[float, NDArray]:
    """
    Predict total aboveground biomass as a function of D and H. This biomass
    value is considered the "optimal" biomass estimate. Use the appropriate
    model form and coefficients from Table S8.

    GTR-WO-104 Step 10 (page 13): Predict total aboveground biomass using
    Equations 1-5 (pages 10-11) with Table S8 coefficients.

    Parameters:
        spcd (int): FIA species code.
        dia (float): Diameter of the tree in inches (in).
        ht (float): Height of the tree in feet (ft).
        division (str, optional): Division code. Default is an empty string.

    Returns:
        float: Total aboveground biomass in pounds (lb).
    """
    # GTR-WO-104 Equations 1-5 (pages 10-11) with Table S8 coefficients
    return _run_model_form("s8", spcd, dia, ht, division)


def total_foliage_dry_weight(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
    ah: Union[float, ArrayLike, None] = None,
    cr: Union[float, ArrayLike, None] = None,
) -> Union[float, NDArray]:
    """
    Directly predict total foliage dry weight as a function of D and H.
    Use the appropriate model form and coefficients from Table S9.

    GTR-WO-104 Step 15 (page 13): Predict total foliage dry weight using
    Equations 1-5 (pages 10-11) with Table S9 coefficients.

    For trees with broken tops (ah < ht), applies FoliageRem adjustment:
    - Live trees with observed CR: Calculate CRH and FoliageRem
    - FoliageRem = [AH - H × (1 - CRH)] / (H × CRH)

    Note: Dead trees have no foliage (return 0).

    Parameters:
        spcd (int): FIA species code.
        dia (float): Diameter of the tree in inches (in).
        ht (float): Height of the tree in feet (ft).
        division (str, optional): Division code. Default is an empty string.
        ah (float, optional): Actual height for broken top trees (ft).
        cr (float, optional): Observed crown ratio (0-1) for broken-top trees.

    Returns:
        float: Total foliage dry weight in pounds (lb).
    """
    # GTR-WO-104 Equations 1-5 (pages 10-11) with Table S9 coefficients
    weight = _run_model_form("s9", spcd, dia, ht, division)

    # Apply broken top adjustment if both ah and cr are provided
    if ah is not None and cr is not None:
        # Check if array input
        is_array = isinstance(spcd, np.ndarray) or isinstance(dia, np.ndarray)

        if not is_array:
            # Scalar path
            # Calculate CRH and FoliageRem (same formula as BranchRem)
            crh = calculate_crh(ah, ht, cr)
            foliage_rem = calculate_branch_foliage_remaining(ah, ht, crh)
            return weight * foliage_rem

        # Array path
        ht_arr = np.atleast_1d(ht)
        ah_arr = np.atleast_1d(ah)
        cr_arr = np.atleast_1d(cr)

        reduction = np.ones_like(weight, dtype=float)
        for i, (h, a, c) in enumerate(zip(ht_arr, ah_arr, cr_arr)):
            crh = calculate_crh(a, h, c)
            foliage_rem = calculate_branch_foliage_remaining(a, h, crh)
            reduction[i] = foliage_rem

        return weight * reduction

    return weight


def _get_volume_ratio_coefficients(
    spcd: int,
    division: str,
    bark: str,
) -> dict:
    """
    Get volume ratio coefficients from table S4 (outside-bark) or S5 (inside-bark).

    Parameters:
        spcd: FIA species code
        division: Division code
        bark: "ib" for inside-bark, "ob" for outside-bark

    Returns:
        Dictionary with 'alpha' and 'beta' coefficients
    """
    # Select table based on bark type
    table_name = "s5" if bark == "ib" else "s4"

    # Try FIA species code table first
    try:
        table_name_spcd = f"{table_name}a"
        table_data = TABLES[table_name_spcd]
        data = table_data.get((spcd, division), table_data.get((spcd, "")))
        if data is None:
            raise KeyError(f"No data for SPCD {spcd}")
        return data
    except (KeyError, TypeError):
        # Fall back to Jenkins species group
        spgrp = int(REF_SPECIES[spcd]["JENKINS_SPGRPCD"])
        table_name_spgrp = f"{table_name}b"
        table_data = TABLES[table_name_spgrp]
        return table_data[spgrp]


def volume_ratio(
    spcd: Union[int, ArrayLike],
    h: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
    bark: str = "ib",
) -> Union[float, NDArray]:
    """
    Calculate the cumulative volume ratio at height h.

    GTR-WO-104 Equation 6 (page 11):
    R = [1 - (1 - h/H)^α]^β

    Where α, β are from Table S4 (outside-bark) or Table S5 (inside-bark).

    Parameters:
        spcd: FIA species code
        h: Height at which to calculate volume ratio (ft)
        ht: Total tree height (ft)
        division: Division code
        bark: "ib" for inside-bark (Table S5), "ob" for outside-bark (Table S4)

    Returns:
        Volume ratio at height h (0-1)
    """

    def _scalar_volume_ratio(spcd_val, h_val, ht_val, div_val):
        coefs = _get_volume_ratio_coefficients(int(spcd_val), str(div_val), bark)
        alpha = coefs["alpha"]
        beta = coefs["beta"]
        # GTR-WO-104 Equation 6 (page 11): R = [1 - (1 - h/H)^α]^β
        return (1 - (1 - h_val / ht_val) ** alpha) ** beta

    is_array = (
        isinstance(spcd, np.ndarray)
        or isinstance(h, np.ndarray)
        or isinstance(ht, np.ndarray)
    )

    if is_array:
        vectorized_fn = np.vectorize(_scalar_volume_ratio)
        return vectorized_fn(spcd, h, ht, division)
    else:
        return _scalar_volume_ratio(spcd, h, ht, division)


def _get_volume_coefficients(
    spcd: int,
    division: str,
    table_name: str,
) -> dict:
    """
    Get volume coefficients from table S1, S2, or S3.

    Parameters:
        spcd: FIA species code
        division: Division code
        table_name: "s1" (inside-bark), "s2" (bark), or "s3" (outside-bark)

    Returns:
        Dictionary with 'a', 'b', 'c' coefficients
    """
    # Try FIA species code table first
    try:
        table_name_spcd = f"{table_name}a"
        table_data = TABLES[table_name_spcd]
        data = table_data.get((spcd, division), table_data.get((spcd, "")))
        if data is None:
            raise KeyError(f"No data for SPCD {spcd}")
        return data
    except (KeyError, TypeError):
        # Fall back to Jenkins species group
        spgrp = int(REF_SPECIES[spcd]["JENKINS_SPGRPCD"])
        table_name_spgrp = f"{table_name}b"
        table_data = TABLES[table_name_spgrp]
        return table_data[spgrp]


def height_to_diameter(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    target_dia: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
    bark: str = "ob",
) -> Union[float, NDArray]:
    """
    Find the height at which stem diameter equals target_dia using iterative minimization.

    Equation 7 from GTR-WO-104 (page 14): Solves for h where d(h) = target_dia

    Uses the relationship between volume ratios to find the height at which
    the stem reaches a target diameter.

    d(h) = sqrt(a × D^b × H^c / (0.005454154 × H) × α × β × (1 - h/H)^(α-1) × [1 - (1 - h/H)^α]^(β-1))

    Where:
        - a, b, c are from Table S3a/S3b (outside-bark volume coefficients)
        - α, β are from Table S4a/S4b (outside-bark volume ratio coefficients)
        - 0.005454154 = π/576 (conversion factor for diameter to basal area)

    Parameters:
        spcd: FIA species code
        dia: Diameter at breast height (in)
        ht: Total tree height (ft)
        target_dia: Target stem diameter (in)
        division: Division code
        bark: "ob" for outside-bark calculations

    Returns:
        Height at which stem diameter equals target_dia (ft)
    """
    from scipy.optimize import brentq

    # Conversion constant from GTR: (π/4) / 144 = π/576 ≈ 0.005454154
    # This converts diameter² (in²) to basal area (ft²)
    K = 0.005454154

    def _scalar_height_to_diameter(spcd_val, dia_val, ht_val, target_dia_val, div_val):
        spcd_int = int(spcd_val)
        div_str = str(div_val)

        # Get outside-bark volume coefficients from Table S3 (GTR page 14)
        vol_coefs = _get_volume_coefficients(spcd_int, div_str, "s3")
        a = vol_coefs["a"]
        b = vol_coefs["b"]
        c = vol_coefs["c"]

        # Get outside-bark volume ratio coefficients from Table S4 (GTR page 14)
        ratio_coefs = _get_volume_ratio_coefficients(spcd_int, div_str, "ob")
        alpha = ratio_coefs["alpha"]
        beta = ratio_coefs["beta"]

        # Equation 7 from GTR-WO-104 (page 14):
        # d(h) = sqrt(a × D^b × H^c / (K × H) × α × β × t^(α-1) × (1-t^α)^(β-1))
        # where t = (1 - h/H) and K = 0.005454154

        def diameter_at_height(h):
            if h >= ht_val:
                return 0.0
            if h <= 0:
                h = 0.001

            t = 1 - h / ht_val  # (1 - h/H)
            if t <= 0:
                return 0.0

            r_term = 1 - t**alpha  # (1 - t^α)
            if r_term <= 0:
                r_term = 1e-10

            # Compute diameter using Equation 7 from GTR page 14
            volume_term = a * (dia_val**b) * (ht_val**c)
            ratio_derivative = (
                alpha * beta * (t ** (alpha - 1)) * (r_term ** (beta - 1))
            )
            diameter = np.sqrt(volume_term / (K * ht_val) * ratio_derivative)

            return diameter

        # Find height where diameter equals target
        def objective(h):
            return diameter_at_height(h) - target_dia_val

        # Check if target diameter is achievable
        d_at_stump = diameter_at_height(1.0)
        d_at_top = diameter_at_height(ht_val - 0.1)

        if target_dia_val > d_at_stump:
            # Target diameter is larger than stump diameter
            return 1.0

        if target_dia_val < d_at_top:
            # Target diameter is smaller than at top
            return ht_val

        # Use Brent's method to find the root
        try:
            result = brentq(objective, 1.0, ht_val - 0.01, xtol=1e-6)
            return result
        except ValueError:
            # If no root found in range, return the closest bound
            return ht_val

    is_array = (
        isinstance(spcd, np.ndarray)
        or isinstance(dia, np.ndarray)
        or isinstance(ht, np.ndarray)
    )

    if is_array:
        vectorized_fn = np.vectorize(_scalar_height_to_diameter)
        return vectorized_fn(spcd, dia, ht, target_dia, division)
    else:
        return _scalar_height_to_diameter(spcd, dia, ht, target_dia, division)


def merchantable_height(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
) -> Union[float, NDArray]:
    """
    Find the height to a 4.0-inch top diameter (merchantable height).

    GTR-WO-104 Step 4 (page 12): Determine hm (height to 4.0" top) using
    Equation 7 (page 14) with iterative minimization.

    Parameters:
        spcd: FIA species code
        dia: Diameter at breast height (in)
        ht: Total tree height (ft)
        division: Division code

    Returns:
        Height to 4.0-inch top diameter (ft)
    """
    # GTR-WO-104 Step 4 (page 12): Use Equation 7 to find height to 4.0" top
    return height_to_diameter(spcd, dia, ht, 4.0, division)


def sawlog_height(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
) -> Union[float, NDArray]:
    """
    Find the height to sawlog top diameter (7.0" for softwoods, 9.0" for hardwoods).

    GTR-WO-104 Step 4 (page 12): Determine hs (height to sawlog top) using
    Equation 7 (page 14) with iterative minimization.
    - Softwoods (SPCD < 300): 7.0" top diameter
    - Hardwoods (SPCD >= 300): 9.0" top diameter

    Parameters:
        spcd: FIA species code
        dia: Diameter at breast height (in)
        ht: Total tree height (ft)
        division: Division code

    Returns:
        Height to sawlog top diameter (ft)
    """

    def _scalar_sawlog_height(spcd_val, dia_val, ht_val, div_val):
        spcd_int = int(spcd_val)
        # GTR-WO-104: Softwoods (SPCD < 300) use 7.0" top, hardwoods use 9.0" top
        sawlog_top = 7.0 if spcd_int < 300 else 9.0
        return height_to_diameter(spcd_int, dia_val, ht_val, sawlog_top, div_val)

    is_array = (
        isinstance(spcd, np.ndarray)
        or isinstance(dia, np.ndarray)
        or isinstance(ht, np.ndarray)
    )

    if is_array:
        vectorized_fn = np.vectorize(_scalar_sawlog_height)
        return vectorized_fn(spcd, dia, ht, division)
    else:
        return _scalar_sawlog_height(spcd, dia, ht, division)


def stump_volume(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
    bark: str = "ib",
) -> Union[float, NDArray]:
    """
    Calculate stump volume (from ground to 1-foot stump height).

    GTR-WO-104 Step 5 (page 12):
    VstumpGross = R1 × VtotalGross

    Where R1 is the volume ratio at 1-foot stump height using Equation 6
    with inside-bark coefficients (Table S5).

    Parameters:
        spcd: FIA species code
        dia: Diameter at breast height (in)
        ht: Total tree height (ft)
        division: Division code
        bark: "ib" for inside-bark, "ob" for outside-bark

    Returns:
        Stump volume in cubic feet (ft³)
    """
    # GTR-WO-104 Step 5: R1 from Equation 6 with inside-bark coefficients (S5)
    r1 = volume_ratio(spcd, 1.0, ht, division, bark="ib")

    if bark == "ib":
        v_total = total_inside_bark_wood_volume(spcd, dia, ht, division)
    elif bark == "ob":
        v_total = total_outside_bark_volume(spcd, dia, ht, division)
    else:
        raise ValueError(f"Invalid bark type: {bark}. Must be 'ib' or 'ob'.")

    # GTR-WO-104 Step 5: VstumpGross = R1 × VtotalGross
    return r1 * v_total


def merchantable_volume(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
    bark: str = "ib",
) -> Union[float, NDArray]:
    """
    Calculate merchantable volume (from stump to 4.0" top).

    GTR-WO-104 Step 5 (page 12):
    VmerGross = (Rm - R1) × VtotalGross

    Where Rm and R1 are volume ratios from Equation 6 with inside-bark
    coefficients (Table S5), and VtotalGross is the appropriate total volume.

    Parameters:
        spcd: FIA species code
        dia: Diameter at breast height (in)
        ht: Total tree height (ft)
        division: Division code
        bark: "ib" for inside-bark, "ob" for outside-bark, "bk" for bark only

    Returns:
        Merchantable volume in cubic feet (ft³)
    """
    if bark == "bk":
        # Bark volume = outside-bark - inside-bark
        v_mer_ob = merchantable_volume(spcd, dia, ht, division, "ob")
        v_mer_ib = merchantable_volume(spcd, dia, ht, division, "ib")
        return v_mer_ob - v_mer_ib

    # GTR-WO-104 Step 4: Get merchantable height (hm) from Equation 7
    hm = merchantable_height(spcd, dia, ht, division)

    # GTR-WO-104 Step 5: Volume ratios from Equation 6 with inside-bark coefficients (S5)
    r1 = volume_ratio(spcd, 1.0, ht, division, bark="ib")
    rm = volume_ratio(spcd, hm, ht, division, bark="ib")

    if bark == "ib":
        v_total = total_inside_bark_wood_volume(spcd, dia, ht, division)
    else:  # "ob"
        v_total = total_outside_bark_volume(spcd, dia, ht, division)

    # GTR-WO-104 Step 5: VmerGross = (Rm - R1) × VtotalGross
    return (rm - r1) * v_total


def sawlog_volume(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
    bark: str = "ib",
) -> Union[float, NDArray]:
    """
    Calculate sawlog volume (from stump to sawlog top).

    GTR-WO-104 Step 5 (page 12):
    VsawGross = (Rs - R1) × VtotalGross

    Where Rs and R1 are volume ratios from Equation 6 with inside-bark
    coefficients (Table S5).

    Parameters:
        spcd: FIA species code
        dia: Diameter at breast height (in)
        ht: Total tree height (ft)
        division: Division code
        bark: "ib" for inside-bark, "ob" for outside-bark

    Returns:
        Sawlog volume in cubic feet (ft³)
    """
    # GTR-WO-104 Step 4: Get sawlog height (hs) from Equation 7
    hs = sawlog_height(spcd, dia, ht, division)

    # GTR-WO-104 Step 5: Volume ratios from Equation 6 with inside-bark coefficients (S5)
    r1 = volume_ratio(spcd, 1.0, ht, division, bark="ib")
    rs = volume_ratio(spcd, hs, ht, division, bark="ib")

    if bark == "ib":
        v_total = total_inside_bark_wood_volume(spcd, dia, ht, division)
    elif bark == "ob":
        v_total = total_outside_bark_volume(spcd, dia, ht, division)
    else:
        raise ValueError(f"Invalid bark type: {bark}. Must be 'ib' or 'ob'.")

    # GTR-WO-104 Step 5: VsawGross = (Rs - R1) × VtotalGross
    return (rs - r1) * v_total


def top_volume(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
    bark: str = "ib",
) -> Union[float, NDArray]:
    """
    Calculate top volume (from merchantable height to tip).

    GTR-WO-104 Step 5 (page 12):
    VtopGross = VtotalGross - VmerGross - VstumpGross = (1 - Rm) × VtotalGross

    Where Rm is the volume ratio at merchantable height from Equation 6
    with inside-bark coefficients (Table S5).

    Parameters:
        spcd: FIA species code
        dia: Diameter at breast height (in)
        ht: Total tree height (ft)
        division: Division code
        bark: "ib" for inside-bark, "ob" for outside-bark

    Returns:
        Top volume in cubic feet (ft³)
    """
    # GTR-WO-104 Step 4: Get merchantable height (hm) from Equation 7
    hm = merchantable_height(spcd, dia, ht, division)

    # GTR-WO-104 Step 5: Volume ratio from Equation 6 with inside-bark coefficients (S5)
    rm = volume_ratio(spcd, hm, ht, division, bark="ib")

    if bark == "ib":
        v_total = total_inside_bark_wood_volume(spcd, dia, ht, division)
    elif bark == "ob":
        v_total = total_outside_bark_volume(spcd, dia, ht, division)
    else:
        raise ValueError(f"Invalid bark type: {bark}. Must be 'ib' or 'ob'.")

    # GTR-WO-104 Step 5: VtopGross = (1 - Rm) × VtotalGross
    return (1 - rm) * v_total


# =============================================================================
# Sound Volume Functions (GTR-WO-104 Step 6)
# =============================================================================


def sound_inside_bark_volume(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
    cull: Union[float, ArrayLike] = 0.0,
) -> Union[float, NDArray]:
    """
    Calculate sound total inside-bark volume accounting for cull deductions.

    GTR-WO-104 Step 6 (page 13):
    VtotibSound = VtotibGross × (1 – CULL/100)

    Sound volume is the gross volume reduced by the cull percentage. This
    represents the volume of sound (non-defective) wood in the tree.

    Parameters:
        spcd: FIA species code
        dia: Diameter at breast height (in)
        ht: Total tree height (ft)
        division: Division code
        cull: Cull percentage (0-100), representing the proportion of
              volume that is defective (rotten or missing)

    Returns:
        Sound inside-bark volume in cubic feet (ft³)
    """
    # GTR-WO-104 Step 6 (page 13): VtotibSound = VtotibGross × (1 – CULL/100)
    v_gross = total_inside_bark_wood_volume(spcd, dia, ht, division)

    # Handle both scalar and array inputs
    is_array = isinstance(cull, np.ndarray) or isinstance(v_gross, np.ndarray)

    if is_array:
        cull_arr = np.atleast_1d(cull)
        v_gross_arr = np.atleast_1d(v_gross)
        return v_gross_arr * (1 - cull_arr / 100)
    else:
        return v_gross * (1 - cull / 100)


def sound_merchantable_volume(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
    cull: Union[float, ArrayLike] = 0.0,
) -> Union[float, NDArray]:
    """
    Calculate sound merchantable volume accounting for cull deductions.

    GTR-WO-104 Step 6 (page 13):
    VmeribSound = VmeribGross × (1 – CULL/100)

    Parameters:
        spcd: FIA species code
        dia: Diameter at breast height (in)
        ht: Total tree height (ft)
        division: Division code
        cull: Cull percentage (0-100)

    Returns:
        Sound merchantable volume in cubic feet (ft³)
    """
    # GTR-WO-104 Step 6 (page 13): VmeribSound = VmeribGross × (1 – CULL/100)
    v_gross = merchantable_volume(spcd, dia, ht, division, bark="ib")

    is_array = isinstance(cull, np.ndarray) or isinstance(v_gross, np.ndarray)

    if is_array:
        cull_arr = np.atleast_1d(cull)
        v_gross_arr = np.atleast_1d(v_gross)
        return v_gross_arr * (1 - cull_arr / 100)
    else:
        return v_gross * (1 - cull / 100)


def sound_sawlog_volume(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
    cull: Union[float, ArrayLike] = 0.0,
) -> Union[float, NDArray]:
    """
    Calculate sound sawlog volume accounting for cull deductions.

    GTR-WO-104 Step 6 (page 13):
    VsawibSound = VsawibGross × (1 – CULL/100)

    Parameters:
        spcd: FIA species code
        dia: Diameter at breast height (in)
        ht: Total tree height (ft)
        division: Division code
        cull: Cull percentage (0-100)

    Returns:
        Sound sawlog volume in cubic feet (ft³)
    """
    # GTR-WO-104 Step 6 (page 13): VsawibSound = VsawibGross × (1 – CULL/100)
    v_gross = sawlog_volume(spcd, dia, ht, division, bark="ib")

    is_array = isinstance(cull, np.ndarray) or isinstance(v_gross, np.ndarray)

    if is_array:
        cull_arr = np.atleast_1d(cull)
        v_gross_arr = np.atleast_1d(v_gross)
        return v_gross_arr * (1 - cull_arr / 100)
    else:
        return v_gross * (1 - cull / 100)


# =============================================================================
# Component Harmonization (GTR-WO-104 Steps 11-12)
# =============================================================================


def harmonize_components(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
    cull: Union[float, ArrayLike] = 0.0,
    ah: Union[float, ArrayLike, None] = None,
    decaycd: Union[int, ArrayLike, None] = None,
) -> dict:
    """
    Harmonize component weights so they sum to predicted AGB.

    GTR-WO-104 Steps 11-12 (pages 10-11, 13-14):

    Step 11: Sum component weights (reduced for cull if applicable) to get
    AGBComponentred. Calculate reduction factor AGBReduce.

    Step 12: Proportionally distribute AGBPredictedred across components
    to ensure wood + bark + branches = total AGB.

    The harmonization formula:
    - AGBReduce = AGBComponentred / AGBComponent
    - AGBPredictedred = AGBPredicted × AGBReduce
    - ComponentHarmonized = AGBPredictedred × (ComponentRed / AGBComponentred)

    For dead trees (decaycd provided), applies decay proportions from Table 1:
    - Wood weight reduced by DensProp
    - Bark weight reduced by BarkProp
    - Branch weight reduced by BranchProp

    Parameters:
        spcd: FIA species code
        dia: Diameter at breast height (in)
        ht: Total tree height (ft)
        division: Division code
        cull: Cull percentage (0-100)
        ah: Actual height for broken-top trees (ft)
        decaycd: Decay class for dead trees (1-5)

    Returns:
        Dictionary with harmonized component weights:
        - wood: Harmonized stem wood weight (lb)
        - bark: Harmonized stem bark weight (lb)
        - branch: Harmonized branch weight (lb)
        - agb: Reduced predicted AGB (lb)
    """
    # Calculate unreduced component weights (live tree equivalents)
    w_wood_unreduced = total_stem_wood_dry_weight(spcd, dia, ht, division, cull=0)
    w_bark_unreduced = total_stem_bark_weight(spcd, dia, ht, division)
    w_branch_unreduced = total_branch_weight(spcd, dia, ht, division)

    # Calculate reduced component weights
    if decaycd is not None:
        # Dead tree: apply decay proportions
        w_wood_reduced = total_stem_wood_dry_weight(
            spcd, dia, ht, division, cull=0, ah=ah, decaycd=decaycd
        )
        w_bark_reduced = total_stem_bark_weight(
            spcd, dia, ht, division, decaycd=decaycd
        )
        w_branch_reduced = total_branch_weight(spcd, dia, ht, division, decaycd=decaycd)
    else:
        # Live tree: apply cull to wood only
        w_wood_reduced = total_stem_wood_dry_weight(spcd, dia, ht, division, cull)
        w_bark_reduced = w_bark_unreduced
        w_branch_reduced = w_branch_unreduced

    # GTR-WO-104 Step 11: Sum component weights
    # AGBComponent = unreduced component sum
    # AGBComponentred = reduced component sum
    agb_component = w_wood_unreduced + w_bark_unreduced + w_branch_unreduced
    agb_component_red = w_wood_reduced + w_bark_reduced + w_branch_reduced

    # Calculate AGBReduce factor
    agb_reduce = agb_component_red / agb_component

    # Get predicted AGB from Table S8
    agb_predicted = total_aboveground_biomass(spcd, dia, ht, division)

    # Apply reduction factor
    agb_predicted_red = agb_predicted * agb_reduce

    # GTR-WO-104 Step 12: Harmonize components proportionally
    # ComponentHarmonized = AGBPredictedred × (ComponentRed / AGBComponentred)
    wood_harmonized = agb_predicted_red * (w_wood_reduced / agb_component_red)
    bark_harmonized = agb_predicted_red * (w_bark_reduced / agb_component_red)
    branch_harmonized = agb_predicted_red * (w_branch_reduced / agb_component_red)

    return {
        "wood": wood_harmonized,
        "bark": bark_harmonized,
        "branch": branch_harmonized,
        "agb": agb_predicted_red,
    }


# =============================================================================
# Missing Volume Calculations for Broken Tops
# =============================================================================


def missing_inside_bark_volume(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    ah: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
) -> Union[float, NDArray]:
    """
    Calculate missing inside-bark volume due to broken top.

    GTR-WO-104 Example 4 (page 21):
    VmissibGross = VtotibGross × (1 - Rm)

    Where:
    - VtotibGross = gross total inside-bark volume
    - Rm = inside-bark volume ratio at actual height

    Parameters:
        spcd: FIA species code
        dia: Diameter at breast height (inches)
        ht: Total tree height (feet)
        ah: Actual height to broken top (feet)
        division: Division code

    Returns:
        Missing inside-bark volume in cubic feet
    """
    v_gross = total_inside_bark_wood_volume(spcd, dia, ht, division)
    rm = volume_ratio(spcd, ah, ht, division, bark="ib")
    return v_gross * (1 - rm)


def missing_bark_volume(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    ah: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
) -> Union[float, NDArray]:
    """
    Calculate missing bark volume due to broken top.

    GTR-WO-104:
    VmissbkGross = VtotbkGross × (1 - Rb)

    Where:
    - VtotbkGross = gross total bark volume
    - Rb = outside-bark volume ratio at actual height

    Parameters:
        spcd: FIA species code
        dia: Diameter at breast height (inches)
        ht: Total tree height (feet)
        ah: Actual height to broken top (feet)
        division: Division code

    Returns:
        Missing bark volume in cubic feet
    """
    v_gross = total_bark_wood_volume(spcd, dia, ht, division)
    rb = volume_ratio(spcd, ah, ht, division, bark="ob")
    return v_gross * (1 - rb)


# =============================================================================
# Broken Top Calculations (GTR-WO-104 Page 22)
# =============================================================================


def calculate_crh(
    ah: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    cr: Union[float, ArrayLike],
) -> Union[float, NDArray]:
    """
    Calculate standardized crown ratio (CRH) based on total height.

    GTR-WO-104 (page 22):
    CRH = [H - AH × (1 - CR)] / H

    This converts the observed crown ratio (CR) measured from actual height (AH)
    to a standardized crown ratio based on total tree height (H).

    Parameters:
        ah: Actual height (ft) - height to broken top
        ht: Total tree height (ft)
        cr: Observed crown ratio (0-1) based on actual height

    Returns:
        Standardized crown ratio (0-1) based on total height
    """
    # CRH = [H - AH × (1 - CR)] / H
    return (ht - ah * (1 - cr)) / ht


def calculate_branch_foliage_remaining(
    ah: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    crh: Union[float, ArrayLike],
) -> Union[float, NDArray]:
    """
    Calculate proportion of branches/foliage remaining after broken top loss.

    GTR-WO-104 (page 22):
    BranchRem = [AH - H × (1 - CRH)] / (H × CRH)
    FoliageRem = [AH - H × (1 - CRH)] / (H × CRH)

    This calculates what proportion of the crown (branches/foliage) remains
    after the top portion is broken off.

    Parameters:
        ah: Actual height (ft) - height to broken top
        ht: Total tree height (ft)
        crh: Standardized crown ratio (0-1) from calculate_crh()

    Returns:
        Proportion of branches/foliage remaining (0-1)
    """
    # BranchRem = FoliageRem = [AH - H × (1 - CRH)] / (H × CRH)
    return (ah - ht * (1 - crh)) / (ht * crh)


# =============================================================================
# Crown Ratio Lookup (GTR-WO-104 Table S11)
# =============================================================================


def get_crown_ratio(
    spcd: Union[int, ArrayLike],
    division: Union[str, ArrayLike],
) -> Union[float, NDArray]:
    """
    Get mean crown ratio from Table S11 for dead trees with broken tops.

    GTR-WO-104 Table S11: Mean crown ratio proportions by division and wood type.
    Used when the observed crown ratio is not available (e.g., for dead trees).

    The function looks up the mean crown ratio based on:
    - Division (or province) code
    - Whether the species is hardwood or softwood

    If the specific division is not found, falls back to "UNDEFINED" values.

    Parameters:
        spcd: FIA species code (used to determine hardwood/softwood)
        division: Division or province code (e.g., "M242", "240")

    Returns:
        Crown ratio as a fraction (0-1)
    """
    # Check if array input
    is_array = isinstance(spcd, np.ndarray) or isinstance(division, np.ndarray)

    # Scalar path
    if not is_array:
        # Determine if species is hardwood
        wood_type = REF_SPECIES[spcd]["SFTWD_HRDWD"]
        is_hardwood = wood_type == "H"

        # Try to look up by specific division
        key = (str(division), is_hardwood)
        if key in CROWN_RATIOS:
            return CROWN_RATIOS[key]

        # Fall back to UNDEFINED
        fallback_key = ("UNDEFINED", is_hardwood)
        return CROWN_RATIOS[fallback_key]

    # Array path
    spcd_arr = np.atleast_1d(spcd)
    div_arr = np.atleast_1d(division)

    result = []
    for s, d in zip(spcd_arr, div_arr):
        wood_type = REF_SPECIES[int(s)]["SFTWD_HRDWD"]
        is_hardwood = wood_type == "H"

        key = (str(d), is_hardwood)
        if key in CROWN_RATIOS:
            result.append(CROWN_RATIOS[key])
        else:
            fallback_key = ("UNDEFINED", is_hardwood)
            result.append(CROWN_RATIOS[fallback_key])

    return np.array(result)


# =============================================================================
# Dead Tree Decay Adjustments (GTR-WO-104 Table 1)
# =============================================================================

# GTR-WO-104 Table 1: Dead tree adjustment proportions by decay class
# DensProp: Wood density proportion (multiplied against live wood density)
# BarkProp: Proportion of bark remaining
# BranchProp: Proportion of branches remaining
DECAY_TABLE_HARDWOOD = {
    1: {"dens_prop": 0.99, "bark_prop": 1.0, "branch_prop": 1.0},
    2: {"dens_prop": 0.80, "bark_prop": 0.8, "branch_prop": 0.5},
    3: {"dens_prop": 0.54, "bark_prop": 0.5, "branch_prop": 0.1},
    4: {"dens_prop": 0.43, "bark_prop": 0.2, "branch_prop": 0.0},
    5: {"dens_prop": 0.43, "bark_prop": 0.0, "branch_prop": 0.0},
}

DECAY_TABLE_SOFTWOOD = {
    1: {"dens_prop": 0.97, "bark_prop": 1.0, "branch_prop": 1.0},
    2: {"dens_prop": 1.00, "bark_prop": 0.8, "branch_prop": 0.5},
    3: {"dens_prop": 0.92, "bark_prop": 0.5, "branch_prop": 0.1},
    4: {"dens_prop": 0.55, "bark_prop": 0.2, "branch_prop": 0.0},
    5: {"dens_prop": 0.55, "bark_prop": 0.0, "branch_prop": 0.0},
}


def get_decay_proportions(
    spcd: int,
    decaycd: int,
) -> dict:
    """
    Get decay adjustment proportions for dead trees based on decay class.

    GTR-WO-104 Table 1 (page 16): Dead tree adjustment proportions by decay class.

    Dead trees have reduced wood density and may lose bark and branches as
    decay progresses. This function returns the proportions to apply:
    - dens_prop: Multiplier for wood density (0-1)
    - bark_prop: Proportion of bark remaining (0-1)
    - branch_prop: Proportion of branches remaining (0-1)

    Parameters:
        spcd: FIA species code (used to determine hardwood/softwood)
        decaycd: Decay class (1-5, where 1 is least decayed)

    Returns:
        Dictionary with dens_prop, bark_prop, and branch_prop values
    """
    # Determine if species is hardwood or softwood from REF_SPECIES
    wood_type = REF_SPECIES[spcd]["SFTWD_HRDWD"]

    # Select appropriate decay table
    if wood_type == "H":
        decay_table = DECAY_TABLE_HARDWOOD
    else:
        decay_table = DECAY_TABLE_SOFTWOOD

    # Return proportions for the given decay class
    return decay_table[decaycd]


def get_carbon_fraction(
    spcd: Union[int, ArrayLike],
    decaycd: Union[int, ArrayLike, None] = None,
) -> Union[float, NDArray]:
    """
    Get carbon fraction for biomass to carbon conversion.

    GTR-WO-104 Step 13: Carbon = Biomass × Carbon_fraction

    For live trees: Uses species-specific carbon fraction from Table S10a
    For dead trees: Uses decay-class-specific carbon fraction from Table S10b

    Parameters:
        spcd: FIA species code
        decaycd: Decay class for dead trees (1-5). If None, uses live tree fraction.

    Returns:
        Carbon fraction (0-1)
    """
    # Check if array input
    is_array = isinstance(spcd, np.ndarray)

    # Scalar path
    if not is_array:
        if decaycd is not None:
            # Dead tree: use Table S10b based on wood type and decay class
            wood_type = REF_SPECIES[spcd]["SFTWD_HRDWD"]
            wood_type_key = "Hardwood" if wood_type == "H" else "Softwood"
            return CARBON_FRACTIONS_DEAD[(decaycd, wood_type_key)]
        else:
            # Live tree: use species-specific carbon fraction from Table S10a
            return CARBON_FRACTIONS_LIVE[spcd]

    # Array path
    spcd_arr = np.atleast_1d(spcd)

    if decaycd is not None:
        decaycd_arr = np.atleast_1d(decaycd)
        result = []
        for s, d in zip(spcd_arr, decaycd_arr):
            wood_type = REF_SPECIES[int(s)]["SFTWD_HRDWD"]
            wood_type_key = "Hardwood" if wood_type == "H" else "Softwood"
            result.append(CARBON_FRACTIONS_DEAD[(int(d), wood_type_key)])
        return np.array(result)
    else:
        return np.array([CARBON_FRACTIONS_LIVE[int(s)] for s in spcd_arr])


# =============================================================================
# DRYBIO Calculations (GTR-WO-104 Step 14)
# =============================================================================


def drybio_stump(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
    cull: Union[float, ArrayLike] = 0,
    decaycd: Union[int, ArrayLike, None] = None,
) -> Union[float, NDArray]:
    """
    Calculate dry biomass of the stump (ground to 1-foot height).

    GTR-WO-104 Step 14: DRYBIO_STUMP = R1 × Wstemwd

    Where:
    - R1 = volume ratio at 1-foot stump height (Equation 6)
    - Wstemwd = total stem wood dry weight

    For live trees with cull, the weight is reduced by cull deduction.
    For dead trees, applies DensProp reduction from Table 1.

    Parameters:
        spcd: FIA species code
        dia: Diameter at breast height (inches)
        ht: Total tree height (feet)
        division: Division code
        cull: Cull percentage (0-100) for live trees
        decaycd: Decay class for dead trees (1-5)

    Returns:
        Dry biomass of stump in pounds (lb)
    """
    # Get volume ratio at 1-foot stump height
    r1 = volume_ratio(spcd, 1.0, ht, division, bark="ib")

    # Get total stem wood weight (with cull and decay adjustments)
    w_stem = total_stem_wood_dry_weight(
        spcd, dia, ht, division, cull=cull, decaycd=decaycd
    )

    # DRYBIO_STUMP = R1 × Wstemwd
    return r1 * w_stem


def drybio_bole(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
    cull: Union[float, ArrayLike] = 0,
    ah: Union[float, ArrayLike, None] = None,
    decaycd: Union[int, ArrayLike, None] = None,
) -> Union[float, NDArray]:
    """
    Calculate dry biomass of the bole (merchantable portion from 1-foot stump
    to 4-inch top diameter).

    GTR-WO-104 Step 14: DRYBIO_BOLE = (Rm - R1) × Wstemwd

    Where:
    - Rm = volume ratio at merchantable height (4-inch top)
    - R1 = volume ratio at 1-foot stump height
    - Wstemwd = total stem wood dry weight

    For trees with broken tops (ah < ht):
    - If ah < merchantable height, uses ah as the upper limit
    - DRYBIO_BOLE = (R(ah) - R1) × Wstemwd

    Parameters:
        spcd: FIA species code
        dia: Diameter at breast height (inches)
        ht: Total tree height (feet)
        division: Division code
        cull: Cull percentage (0-100) for live trees
        ah: Actual height for broken-top trees (feet)
        decaycd: Decay class for dead trees (1-5)

    Returns:
        Dry biomass of bole in pounds (lb)
    """
    # Check if array input
    is_array = isinstance(spcd, np.ndarray) or isinstance(dia, np.ndarray)

    if not is_array:
        # Get merchantable height
        hm = merchantable_height(spcd, dia, ht, division)

        # Get volume ratios
        r1 = volume_ratio(spcd, 1.0, ht, division, bark="ib")

        # For broken tops, use the lesser of ah and hm
        if ah is not None and ah < hm:
            r_upper = volume_ratio(spcd, ah, ht, division, bark="ib")
        else:
            r_upper = volume_ratio(spcd, hm, ht, division, bark="ib")

        # Get total stem wood weight (with cull and decay adjustments)
        w_stem = total_stem_wood_dry_weight(
            spcd, dia, ht, division, cull=cull, decaycd=decaycd
        )

        # DRYBIO_BOLE = (Rm - R1) × Wstemwd
        return (r_upper - r1) * w_stem

    # Array path
    spcd_arr = np.atleast_1d(spcd)
    dia_arr = np.atleast_1d(dia)
    ht_arr = np.atleast_1d(ht)
    div_arr = np.atleast_1d(division)
    cull_arr = np.atleast_1d(cull)
    ah_arr = np.atleast_1d(ah) if ah is not None else None

    # Get merchantable heights
    hm_arr = merchantable_height(spcd_arr, dia_arr, ht_arr, div_arr)

    # Get volume ratios
    r1_arr = volume_ratio(spcd_arr, 1.0, ht_arr, div_arr, bark="ib")

    # Calculate upper bound ratio (accounting for broken tops)
    if ah_arr is not None:
        # Use lesser of ah and hm for each tree
        h_upper = np.minimum(ah_arr, hm_arr)
    else:
        h_upper = hm_arr

    r_upper_arr = volume_ratio(spcd_arr, h_upper, ht_arr, div_arr, bark="ib")

    # Get total stem wood weight
    w_stem_arr = total_stem_wood_dry_weight(
        spcd_arr, dia_arr, ht_arr, div_arr, cull=cull_arr, decaycd=decaycd
    )

    return (r_upper_arr - r1_arr) * w_stem_arr


def drybio_top(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
    cull: Union[float, ArrayLike] = 0,
    ah: Union[float, ArrayLike, None] = None,
    decaycd: Union[int, ArrayLike, None] = None,
) -> Union[float, NDArray]:
    """
    Calculate dry biomass of the top (from 4-inch top diameter to tip).

    GTR-WO-104 Step 14: DRYBIO_TOP = (1 - Rm) × Wstemwd

    Where:
    - Rm = volume ratio at merchantable height (4-inch top)
    - Wstemwd = total stem wood dry weight

    For trees with broken tops (ah < ht):
    - If ah < merchantable height, top biomass is 0 (already in "missing" portion)
    - If ah >= merchantable height, DRYBIO_TOP = (R(ah) - Rm) × Wstemwd

    Parameters:
        spcd: FIA species code
        dia: Diameter at breast height (inches)
        ht: Total tree height (feet)
        division: Division code
        cull: Cull percentage (0-100) for live trees
        ah: Actual height for broken-top trees (feet)
        decaycd: Decay class for dead trees (1-5)

    Returns:
        Dry biomass of top in pounds (lb)
    """
    # Check if array input
    is_array = isinstance(spcd, np.ndarray) or isinstance(dia, np.ndarray)

    if not is_array:
        # Get merchantable height
        hm = merchantable_height(spcd, dia, ht, division)

        # Get total stem wood weight
        w_stem = total_stem_wood_dry_weight(
            spcd, dia, ht, division, cull=cull, decaycd=decaycd
        )

        # Handle broken tops
        if ah is not None:
            if ah <= hm:
                # Broken below merchantable height - no top
                return 0.0
            else:
                # Broken above merchantable height - partial top
                rm = volume_ratio(spcd, hm, ht, division, bark="ib")
                r_ah = volume_ratio(spcd, ah, ht, division, bark="ib")
                return (r_ah - rm) * w_stem

        # Full tree - complete top
        rm = volume_ratio(spcd, hm, ht, division, bark="ib")
        return (1 - rm) * w_stem

    # Array path
    spcd_arr = np.atleast_1d(spcd)
    dia_arr = np.atleast_1d(dia)
    ht_arr = np.atleast_1d(ht)
    div_arr = np.atleast_1d(division)
    cull_arr = np.atleast_1d(cull)
    ah_arr = np.atleast_1d(ah) if ah is not None else None

    # Get merchantable heights
    hm_arr = merchantable_height(spcd_arr, dia_arr, ht_arr, div_arr)

    # Get volume ratios at merchantable height
    rm_arr = volume_ratio(spcd_arr, hm_arr, ht_arr, div_arr, bark="ib")

    # Get total stem wood weight
    w_stem_arr = total_stem_wood_dry_weight(
        spcd_arr, dia_arr, ht_arr, div_arr, cull=cull_arr, decaycd=decaycd
    )

    if ah_arr is not None:
        # Calculate ratio at actual height for each tree
        r_ah_arr = volume_ratio(spcd_arr, ah_arr, ht_arr, div_arr, bark="ib")

        # Calculate top biomass based on broken top status
        result = np.where(
            ah_arr <= hm_arr,
            0.0,  # Broken below merchantable - no top
            (r_ah_arr - rm_arr) * w_stem_arr,  # Partial top
        )
        return result

    # Full trees
    return (1 - rm_arr) * w_stem_arr


def drybio_sapling(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
) -> Union[float, NDArray]:
    """
    Calculate dry biomass for saplings (trees with diameter < 5 inches).

    GTR-WO-104 Step 14: For saplings, the entire stem wood weight is used
    since there is no meaningful merchantable portion.

    DRYBIO_SAPLING = Wstemwd (total stem wood dry weight)

    Note: This function is intended for trees with D < 5.0 inches. For larger
    trees, use drybio_bole(), drybio_stump(), and drybio_top() separately.

    Parameters:
        spcd: FIA species code
        dia: Diameter at breast height (inches) - should be < 5.0
        ht: Total tree height (feet)
        division: Division code

    Returns:
        Dry biomass of sapling in pounds (lb)
    """
    # For saplings, return total stem wood weight
    return total_stem_wood_dry_weight(spcd, dia, ht, division)


def drybio_wdld_spp(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
) -> Union[float, NDArray]:
    """
    Calculate dry biomass for woodland species.

    GTR-WO-104 Step 14: Woodland species (typically multi-stemmed shrubs and
    small trees) use total aboveground biomass directly from Table S8.

    DRYBIO_WDLD_SPP = AGBPredicted (from Table S8)

    Note: Woodland species have different growth forms than typical forest trees
    and may not have the same stem/branch distinctions.

    Parameters:
        spcd: FIA species code for woodland species
        dia: Diameter at breast height (inches)
        ht: Total tree height (feet)
        division: Division code

    Returns:
        Dry biomass of woodland species in pounds (lb)
    """
    # For woodland species, use total AGB from Table S8
    return total_aboveground_biomass(spcd, dia, ht, division)


def calculate_carbon(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
    cull: Union[float, ArrayLike] = 0,
    ah: Union[float, ArrayLike, None] = None,
    decaycd: Union[int, ArrayLike, None] = None,
) -> Union[float, NDArray]:
    """
    Calculate carbon content from aboveground biomass.

    GTR-WO-104 Step 13: Carbon = AGB × Carbon_fraction

    For live trees with cull, uses harmonized/reduced AGB.
    For dead trees, applies decay-class-specific carbon fraction.

    Parameters:
        spcd: FIA species code
        dia: Diameter in inches
        ht: Height in feet
        division: Division code
        cull: Cull percentage (0-100) for live trees
        ah: Actual height for broken-top trees
        decaycd: Decay class for dead trees (1-5)

    Returns:
        Carbon content in pounds (lb)
    """
    # Get carbon fraction
    carbon_frac = get_carbon_fraction(spcd, decaycd)

    # Get biomass
    # For live trees with cull, use harmonized components
    is_array = isinstance(spcd, np.ndarray) or isinstance(dia, np.ndarray)

    if not is_array:
        if cull > 0 and decaycd is None:
            # Live tree with cull: use harmonized AGB
            result = harmonize_components(
                spcd=spcd, dia=dia, ht=ht, division=division, cull=cull
            )
            agb = result["agb"]
        else:
            # Live tree without cull or dead tree
            agb = total_aboveground_biomass(
                spcd=spcd, dia=dia, ht=ht, division=division
            )
    else:
        cull_arr = np.atleast_1d(cull)

        # Check if any trees have cull
        if np.any(cull_arr > 0) and decaycd is None:
            result = harmonize_components(
                spcd=spcd, dia=dia, ht=ht, division=division, cull=cull
            )
            agb = result["agb"]
        else:
            agb = total_aboveground_biomass(
                spcd=spcd, dia=dia, ht=ht, division=division
            )

    return agb * carbon_frac
