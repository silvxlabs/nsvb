from nsvb.models import MODEL_MAP
from nsvb.tables import REF_SPECIES, TABLES

WEIGHT_CUBIC_FOOT_WATER = 62.4  # lb/ft^3


def _run_model_form(
    table_name: str, spcd: int, dia: float, ht: float, division: str = ""
) -> float:
    """
    Run the model form for the given table.

    Parameters:
        table_name (str): Table name.
        spcd (int): Species code.
        dia (float): Diameter of the tree.
        ht (float): Height of the tree.
        division (str, optional): Division code. Default is an empty string.

    Returns:
        float: Model form result.
    """
    try:
        table_name_spcd = f"{table_name}a"
        table_data = TABLES[table_name_spcd]
        data = table_data.get((spcd, division), table_data[(spcd, "")])
    except KeyError:
        spgrp = int(REF_SPECIES[spcd]["JENKINS_SPGRPCD"])
        table_name_spgrp = f"{table_name}b"
        table_data = TABLES[table_name_spgrp]
        data = table_data.get(spgrp)
        wdsg = float(REF_SPECIES[spcd]["WOOD_SPGR_GREENVOL_DRYWT"])
        data["wdsg"] = wdsg
    model_function = MODEL_MAP[data["model"]]
    return model_function(dia, ht, **data)


def total_inside_bark_wood_volume(
    spcd: int, dia: float, ht: float, division: str = ""
) -> float:
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
    spcd: int, dia: float, ht: float, division: str = ""
) -> float:
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
    spcd: int, dia: float, ht: float, division: str = ""
) -> float:
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
    spcd: int, dia: float, ht: float, division: str = "", cull: float = 0
) -> float:
    """
    Convert total stem wood gross volume to
    biomass weight using published wood density
    values (Miles and Smith 2009). Reduce stem
    wood weight due to broken top, cull deductions
    (accounting for nonzero weight of cull), and dead
    tree wood density reduction.

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
    wdsg = float(REF_SPECIES[spcd]["WOOD_SPGR_GREENVOL_DRYWT"])
    v_tot_ib = total_inside_bark_wood_volume(spcd, dia, ht, division)

    if cull > 0:
        # It is considered that most cull will be rotten wood, which would
        # still contribute to the stem weight. As such, it is assumed the
        # density of cull wood is reduced by the proportion for DECAYCD = 3
        # (see table 1; wood density proportion (DensProp) is 0.54 for
        # hardwood species and 0.92 for softwood species)
        dens_prop = 0.54 if REF_SPECIES[spcd]["SFTWD_HRDWD"] == "H" else 0.92

        return (
            v_tot_ib
            * (1 - cull / 100 * (1 - dens_prop))
            * wdsg
            * WEIGHT_CUBIC_FOOT_WATER
        )

    # No cull
    return v_tot_ib * wdsg * WEIGHT_CUBIC_FOOT_WATER


def total_stem_bark_weight(
    spcd: int, dia: float, ht: float, division: str = ""
) -> float:
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


def total_branch_weight(spcd: int, dia: float, ht: float, division: str = "") -> float:
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
    spcd: int, dia: float, ht: float, division: str = ""
) -> float:
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
    spcd: int, dia: float, ht: float, division: str = ""
) -> float:
    """
    Directly predict total foliage dry weight as a
    function of D and H. Use the appropriate model
    form and coefficients from table S9.

    Corresponds to step 15 of "Examples of Tree-Level Calculations" in the GTR.

    """
    return _run_model_form("s9", spcd, dia, ht, division)
