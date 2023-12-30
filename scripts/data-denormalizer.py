"""
Notes:

This script is designed to denormalize and preprocess coefficient data from various
CSV files for use in a Rust library. It reads multiple coefficient tables
from the NSVB GTR Supplement, processes them, and compiles a data structure that maps
species codes to their respective coefficients for different biomass and volume components
and eco division groupings. A heirachical fallback is embedded in the data structure such
that species-specific coefficients for a given eco division is used first if available,
following by species-specific cross-divisions coefficients, followed by Jenkins group level
coefficients. The processed data is then serialized into a JSON string and written directly
into a Rust source file--effectively, this is code generation.

The primary objective of this script is to create a highly efficient, queryable data
structure (a Rust HashMap) that can be embedded directly within the NSVB Rust executable.
This approach ensures that all necessary data is contained within the executable itself,
thereby enhancing the performance, reducing I/O overhead, and eliminating external data
dependencies at runtime. These benefits come at the cost of a larger executable size and
limited flexibility in terms of updating the data. These tradeoffs are acceptable for
this application, as the data is relatively static and an executable size of ~1.5 MB is
not a concern.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, List

# Define the base path to the data directory. Depending on where you run this
# script from, you may need to change `base_path`.
data_path = Path("../data/")


# ==============================================================================
# FILE NAMES
# ------------------------------------------------------------------------------
# Define the file names for each data file
ref_species_file = "REF_SPECIES.csv"

live_carbon_file = "Table S10a_fia_wood_c_frac_live.csv"
mean_crown_ratio_file = "Table S11_mean_crprop.csv"

# The key names here are important to maintain as they are used in the Rust CLI
# to access coefficients for each component.
coef_files = {
    "volib": {
        "spcd": "Table S1a_volib_coefs_spcd.csv",
        "jenkins": "Table S1b_volib_coefs_jenkins.csv",
    },
    "volbk": {
        "spcd": "Table S2a_volbk_coefs_spcd.csv",
        "jenkins": "Table S2b_volbk_coefs_jenkins.csv",
    },
    "volob": {
        "spcd": "Table S3a_volob_coefs_spcd.csv",
        "jenkins": "Table S3b_volob_coefs_jenkins.csv",
    },
    "rcumob": {
        "spcd": "Table S4a_rcumob_coefs_spcd.csv",
        "jenkins": "Table S4b_rcumob_coefs_jenkins.csv",
    },
    "rcumib": {
        "spcd": "Table S5a_rcumib_coefs_spcd.csv",
        "jenkins": "Table S5b_rcumib_coefs_jenkins.csv",
    },
    "bark_biomass": {
        "spcd": "Table S6a_bark_biomass_coefs_spcd.csv",
        "jenkins": "Table S6b_bark_biomass_coefs_jenkins.csv",
    },
    "branch_biomass": {
        "spcd": "Table S7a_branch_biomass_coefs_spcd.csv",
        "jenkins": "Table S7b_branch_biomass_coefs_jenkins.csv",
    },
    "total_biomass": {
        "spcd": "Table S8a_total_biomass_coefs_spcd.csv",
        "jenkins": "Table S8b_total_biomass_coefs_jenkins.csv",
    },
    "foliage_biomass": {
        "spcd": "Table S9a_foliage_coefs_spcd.csv",
        "jenkins": "Table S9b_foliage_coefs_jenkins.csv",
    },
}


# ==============================================================================
# READ IN DATA
# ------------------------------------------------------------------------------
# Read in reference species file
ref_species = pd.read_csv(data_path / ref_species_file)

# Read in non-coefficient files from NSVB.
# Note: The data from dead carbon content is hard-coded in the Rust CLI
live_carbon = pd.read_csv(data_path / live_carbon_file)
# Pre-process live_carbon to map species codes to carbon fractions
carbon_fraction_map = live_carbon.set_index("SPCD")["fia.wood.c"].to_dict()

# TODO: We are currently seeking clarification on the mean crown ratio table from
# the Forest Service. The table is organized by the eco subdivision code, but the
# GTR examples only reference division codes.
mean_crown_ratio = pd.read_csv(data_path / mean_crown_ratio_file)

# Read in each coefficient file
coef_dfs = {}
for coef_name, coef_file in coef_files.items():
    coef_dfs[coef_name] = {}
    for coef_type, coef_path in coef_file.items():
        coef_dfs[coef_name][coef_type] = pd.read_csv(data_path / coef_path)
        # If 'equation' is in the columns, change it to 'model'.
        # This is likely a mistake in the original data
        if "equation" in coef_dfs[coef_name][coef_type].columns:
            coef_dfs[coef_name][coef_type].rename(
                columns={"equation": "model"}, inplace=True
            )


# ==============================================================================
# DENORMALIZE DATA
# ------------------------------------------------------------------------------
def parse_model_coefs(row: pd.Series, k: float, wdsg: float) -> Tuple[int, List[float]]:
    """
    Helper function to parse the model and coefficients from a row in a
    coefficient table.

    Parameters
    ----------
    row : pd.Series
        A row from a coefficient table
    k : float
        The k value to use as the segmentation point for model 2
    wdsg : float
        The wood specific gravity for this species

    Returns
    -------
    Tuple[int, List[float]]
        A tuple containing the model number and a list of coefficients
    """
    model = int(row["model"])
    coefficient_map = {
        1: ["a", "b", "c"],
        2: ["a", "b", "b1", "c"],
        3: ["a", "a1", "b", "c", "c1"],
        4: ["a", "b", "b1", "c"],
        5: ["a", "b", "c"],
        6: ["alpha", "beta"],
    }

    if model not in coefficient_map:
        raise ValueError(f"Unsupported model number: {model}")

    coefficients = [row[coef] for coef in coefficient_map[model]]

    if model == 2:
        coefficients.append(k)
    elif model == 5:
        coefficients.append(wdsg)

    return model, coefficients


# Initialize data dictionary
data = {}

# Iterate over REF_SPECIES DataFrame
for ref_index, ref_row in ref_species.iterrows():
    spcd = int(ref_row["SPCD"])
    jenkins_group = ref_row["JENKINS_SPGRPCD"]
    wdsg = ref_row["WOOD_SPGR_GREENVOL_DRYWT"]
    bksg = ref_row["BARK_SPGR_GREENVOL_DRYWT"]
    seg_point = 9.0 if spcd < 300 else 11.0

    # Skip non-domestic species, woodland species, and species without a
    # Jenkins group designation.
    if spcd > 999 or pd.isna(jenkins_group) or jenkins_group == 10:
        continue

    # Retrieve carbon fraction from the map, defaults to 0.5 if species is not found
    carbon_fraction = carbon_fraction_map.get(spcd, 0.5)

    # Initialize species data
    species_data = {"wdsg": wdsg, "bksg": bksg, "cfrac": carbon_fraction}

    # Process component model coefficients and eco divisions
    for component, group in coef_dfs.items():
        species_data[component] = {}
        spcd_df = group["spcd"][group["spcd"]["SPCD"] == spcd]

        # Use the species-specific, and possibly division-specific, coefficients
        # if they exist
        if not spcd_df.empty:
            # Loop over possible division codes
            for index, row in spcd_df.iterrows():
                model, coefs = parse_model_coefs(row, seg_point, wdsg)
                if not pd.isnull(row["DIVISION"]):
                    division_code = row["DIVISION"]
                else:
                    division_code = "default"
                species_data[component][division_code] = {
                    "group": "spcd",
                    "model": model,
                    "coefs": coefs,
                }

        # Otherwise, fallback on the Jenkins group coefficients
        else:
            jenkins_row = group["jenkins"][
                group["jenkins"]["JENKINS_SPGRPCD"] == jenkins_group
            ].iloc[0]
            model, coefs = parse_model_coefs(jenkins_row, seg_point, wdsg)
            species_data[component]["default"] = {
                "group": "jenkins",
                "model": model,
                "coefs": coefs,
            }

    # Add species data to main data dictionary
    data[spcd] = species_data

# Build dictionary for mean crown ratio by hardwood/softwood and division
mean_cr = {}
# Remove the Islan division
mean_crown_ratio = mean_crown_ratio[mean_crown_ratio["Division"] != "Islan"]
# Change undefined divisions to default
mean_crown_ratio["Division"] = mean_crown_ratio["Division"].replace(
    "UNDEFINED", "default"
)
# Get unique division codes
divisions = mean_crown_ratio["Division"].unique()
for division in divisions:
    hard_soft = mean_crown_ratio[mean_crown_ratio["Division"] == division]
    mean_cr[division] = {
        "hardwood": hard_soft[hard_soft["HWD Y/N"] == "Y"].iloc[0]["Mean CR"] / 100.0,
        "softwood": hard_soft[hard_soft["HWD Y/N"] == "N"].iloc[0]["Mean CR"] / 100.0,
    }


# Write to a Rust file
with open("./coefs.rs", "w") as f:
    species_data = json.dumps(data, sort_keys=True, separators=(",", ":"))
    mean_cr_data = json.dumps(mean_cr, sort_keys=True, separators=(",", ":"))
    f.write(
        f'pub const SPECIES_DATA: &str = r#"{species_data}"#;\n\npub const MEAN_CROWN_RATIO_DATA: &str = r#"{mean_cr_data}"#;'
    )
