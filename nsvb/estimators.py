from typing import Union

import numpy as np
from numpy.typing import ArrayLike, NDArray

from nsvb.models import MODEL_MAP
from nsvb.tables import REF_SPECIES, TABLES

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
    is_array = isinstance(spcd, np.ndarray) or isinstance(dia, np.ndarray) or isinstance(ht, np.ndarray)

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
    return _run_model_form("s1", spcd, dia, ht, division)


def total_bark_wood_volume(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
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
        float: Total outside bark wood volume.
    """
    return _run_model_form("s2", spcd, dia, ht, division)


def total_outside_bark_volume(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
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
    v_tot_ib = total_inside_bark_wood_volume(spcd, dia, ht, division)
    v_tot_bk = total_bark_wood_volume(spcd, dia, ht, division)
    return v_tot_ib + v_tot_bk


def total_stem_wood_dry_weight(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
    cull: Union[float, ArrayLike] = 0,
) -> Union[float, NDArray]:
    """
    Convert total stem wood gross volume to
    biomass weight using published wood density
    values (Miles and Smith 2009). Reduce stem
    wood weight due to broken top, cull deductions
    (accounting for nonzero weight of cull), and dead
    tree wood density reduction.

    Works with scalar or array inputs.

    Corresponds to step 7 of "Examples of Tree-Level Calculations" in the GTR.

    Parameters:
        spcd (int): FIA species code.
        dia (float): Diameter of the tree in inches (in).
        ht (float): Height of the tree in feet (ft).
        division (str, optional): Division code. Default is an empty string.
        cull (int, optional): Rotten and missing cull. The percent of the cubic-foot volume in a live or dead tally tree that is rotten or missing.

    Returns:
        float: Total stem wood dry weight in pounds (lb).
    """
    # Check if array input
    is_array = isinstance(spcd, np.ndarray) or isinstance(dia, np.ndarray)

    # Scalar path
    if not is_array:
        wdsg = float(REF_SPECIES[spcd]["WOOD_SPGR_GREENVOL_DRYWT"])
        v_tot_ib = total_inside_bark_wood_volume(spcd, dia, ht, division)

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

    # Get volume (will be vectorized through _run_model_form)
    v_tot_ib = total_inside_bark_wood_volume(spcd_arr, dia_arr, ht_arr, div_arr)

    # Vectorize lookups from REF_SPECIES
    wdsg_arr = np.array([float(REF_SPECIES[int(s)]["WOOD_SPGR_GREENVOL_DRYWT"]) for s in spcd_arr])
    dens_prop_arr = np.array([0.54 if REF_SPECIES[int(s)]["SFTWD_HRDWD"] == "H" else 0.92 for s in spcd_arr])

    # Vectorized calculation
    weight = np.where(
        cull_arr > 0,
        v_tot_ib * (1 - cull_arr / 100 * (1 - dens_prop_arr)) * wdsg_arr * WEIGHT_CUBIC_FOOT_WATER,
        v_tot_ib * wdsg_arr * WEIGHT_CUBIC_FOOT_WATER
    )

    return weight


def total_stem_bark_weight(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
) -> Union[float, NDArray]:
    """
    Predict total stem bark biomass as a function of
    D and H. Reduce the prediction if necessary for
    missing bark due to a broken top or dead tree
    structural loss, if either is present. Use the
    appropriate model form and coefficients from
    table S6.

    Corresponds to step 8 of "Examples of Tree-Level Calculations" in the GTR.

    Parameters:
        spcd (int): Species code.
        dia (float): Diameter of the tree.
        ht (float): Height of the tree.
        division (str, optional): Division code. Default is an empty string.

    Returns:
        float: Total stem bark weight in pounds (lb).
    """
    return _run_model_form("s6", spcd, dia, ht, division)


def total_branch_weight(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
) -> Union[float, NDArray]:
    """
    Predict total branch biomass as a function of D
    and H. Reduce the prediction if necessary for
    missing branches due to a broken top or dead
    tree wood density reduction and structural loss,
    if present. Use the appropriate model form and
    coefficients from table S7.

    Corresponds to step 9 of "Examples of Tree-Level Calculations" in the GTR.

    Parameters:
        spcd (int): Species code.
        dia (float): Diameter of the tree.
        ht (float): Height of the tree.
        division (str, optional): Division code. Default is an empty string.

    Returns:
        float: Total branch weight in pounds (lb).
    """
    return _run_model_form("s7", spcd, dia, ht, division)


def total_aboveground_biomass(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
) -> Union[float, NDArray]:
    """
    Predict total aboveground biomass as a function
    of D and H. Reduce the prediction if necessary
    using the overall proportional reduction
    obtained from the stem wood, bark, and branch
    component reductions. This biomass value is
    considered the “optimal” biomass estimate. Use
    the appropriate model form and coefficients from
    table S8.

    Corresponds to step 10 of "Examples of Tree-Level Calculations" in the GTR.

    Parameters:
        spcd (int): FIA species code.
        dia (float): Diameter of the tree in inches (in).
        ht (float): Height of the tree in feet (ft).
        division (str, optional): Division code. Default is an empty string.

    Returns:
        float: Total aboveground biomass in pounds (lb).
    """
    return _run_model_form("s8", spcd, dia, ht, division)


def total_foliage_dry_weight(
    spcd: Union[int, ArrayLike],
    dia: Union[float, ArrayLike],
    ht: Union[float, ArrayLike],
    division: Union[str, ArrayLike] = "",
) -> Union[float, NDArray]:
    """
    Directly predict total foliage dry weight as a
    function of D and H. Use the appropriate model
    form and coefficients from table S9.

    Corresponds to step 15 of "Examples of Tree-Level Calculations" in the GTR.

    """
    return _run_model_form("s9", spcd, dia, ht, division)
