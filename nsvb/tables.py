import csv
from importlib.resources import files

DATA_PATH = files("nsvb").joinpath("data")

K_VALUES = {
    "S": 9.0,
    "H": 11.0,
}


def read_ref_species_table(filename):
    with open(DATA_PATH / filename, "r") as f:
        reader = csv.DictReader(f)
        return {int(float(row["SPCD"])): row for row in reader}


def read_wood_density_proportions_table(filename):
    with open(DATA_PATH / filename, "r") as f:
        reader = csv.DictReader(f)
        return {
            (row["class"], int(row["DECAYCD"])): {
                float(row["DensProp"]),
                float(row["BarkProp"]),
                float(row["BranchProp"]),
            }
            for row in reader
        }


def read_coefficient_table_fia(filename):
    with open(DATA_PATH / filename, "r") as f:
        reader = csv.DictReader(f)
        return {
            (int(row["SPCD"]), row["DIVISION"]): {
                "model": int(row["model"]),
                "a": float(row["a"]),
                "a1": float(row["a1"]) if row.get("a1") else None,
                "b": float(row["b"]),
                "b1": float(row["b1"]) if row.get("b1") else None,
                "c": float(row["c"]),
                "c1": float(row["c1"]) if row.get("c1") else None,
                "k": K_VALUES[REF_SPECIES[int(row["SPCD"])]["SFTWD_HRDWD"]],
            }
            for row in reader
        }


def read_coefficient_table_jenkins(filename):
    with open(DATA_PATH / filename, "r") as f:
        reader = csv.DictReader(f)
        return {
            int(row["JENKINS_SPGRPCD"]): {
                "model": int(row["model"]),
                "a": float(row["a"]),
                "b": float(row["b"]),
                "c": float(row["c"]),
            }
            for row in reader
        }


def read_volume_ratio_table_fia(filename):
    """Read volume ratio coefficient tables (S4a, S5a) with alpha/beta columns."""
    with open(DATA_PATH / filename, "r") as f:
        reader = csv.DictReader(f)
        return {
            (int(row["SPCD"]), row["DIVISION"]): {
                "model": int(row["model"]),
                "alpha": float(row["alpha"]),
                "beta": float(row["beta"]),
            }
            for row in reader
        }


def read_volume_ratio_table_jenkins(filename):
    """Read volume ratio coefficient tables (S4b, S5b) with alpha/beta columns."""
    with open(DATA_PATH / filename, "r") as f:
        reader = csv.DictReader(f)
        return {
            int(row["JENKINS_SPGRPCD"]): {
                "model": int(row["model"]),
                "alpha": float(row["alpha"]),
                "beta": float(row["beta"]),
            }
            for row in reader
        }


def read_carbon_fraction_table_live(filename):
    """
    Read Table S10a: Carbon fractions for live trees by species.

    The CSV contains species-specific carbon fractions in the 'fia.wood.c' column
    as percentages (e.g., 49.31 means 49.31%). This function converts them to
    fractions (e.g., 0.4931).

    Parameters:
        filename: CSV filename in the data directory

    Returns:
        Dictionary mapping SPCD (int) to carbon fraction (float, 0-1)
    """
    with open(DATA_PATH / filename, "r") as f:
        reader = csv.DictReader(f)
        return {
            int(float(row["SPCD"])): float(row["fia.wood.c"]) / 100
            for row in reader
            if row["fia.wood.c"]  # Skip rows with missing carbon fractions
        }


def read_carbon_fraction_table_dead(filename):
    """
    Read Table S10b: Carbon fractions for dead trees by decay class.

    The CSV contains carbon fractions by decay class and wood type (S/H).
    Values are percentages (e.g., 47 means 47%). This function converts them
    to fractions (e.g., 0.47).

    Parameters:
        filename: CSV filename in the data directory

    Returns:
        Dictionary mapping (decay_code, wood_type) to carbon fraction (float, 0-1)
        where wood_type is "Hardwood" or "Softwood"
    """
    with open(DATA_PATH / filename, "r") as f:
        reader = csv.DictReader(f)
        return {
            (int(row["Decay code"]), row["S/H"]): float(row["C fraction"]) / 100
            for row in reader
        }


def read_crown_ratio_table(filename):
    """
    Read Table S11: Mean crown ratio proportions by division and wood type.

    The CSV contains mean crown ratios by division (or province) and hardwood/softwood
    classification. Crown ratios are stored as percentages (e.g., 43.9 means 43.9%).
    This function converts them to fractions (e.g., 0.439).

    Parameters:
        filename: CSV filename in the data directory

    Returns:
        Dictionary mapping (division, is_hardwood) to crown ratio fraction (float, 0-1)
        where is_hardwood is True/False based on "HWD Y/N" column
    """
    # Use utf-8-sig encoding to handle BOM (byte order mark) in CSV
    with open(DATA_PATH / filename, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return {
            (row["Division"], row["HWD Y/N"] == "Y"): float(row["Mean CR"]) / 100
            for row in reader
        }


REF_SPECIES = read_ref_species_table("REF_SPECIES.csv")
WOOD_DENSITY_PROPORTIONS = read_wood_density_proportions_table(
    "WOOD_DENSITY_PROPORTIONS.csv"
)

# Table S10a: Carbon fractions for live trees by species (SPCD)
CARBON_FRACTIONS_LIVE = read_carbon_fraction_table_live(
    "Table S10a_fia_wood_c_frac_live.csv.csv"
)

# Table S10b: Carbon fractions for dead trees by decay class and wood type
CARBON_FRACTIONS_DEAD = read_carbon_fraction_table_dead(
    "Table S10b_fia_wood_c_frac_dead.csv.csv"
)

# Table S11: Mean crown ratio proportions by division and wood type
CROWN_RATIOS = read_crown_ratio_table("Table S11_mean_crprop.csv")


# Table S1a Coefficients for predicting total stem inside-bark wood
# cubic-foot volume based on FIA species code (SPCD).
table_s1a = read_coefficient_table_fia("Table S1a_volib_coefs_spcd.csv")

# Table S1b.—Coefficients for predicting total stem inside-bark wood
# cubic-foot volume based on Jenkins species group (JENKINS_SPGRPCD).
table_s1b = read_coefficient_table_jenkins("Table S1b_volib_coefs_jenkins.csv")

# Table S2a.—Coefficients for predicting total stem bark cubic-foot volume
# based on FIA species code (SPCD).
table_s2a = read_coefficient_table_fia("Table S2a_volbk_coefs_spcd.csv")

# Table S2b.—Coefficients for predicting total stem bark cubic-foot volume
# based on Jenkins species group (JENKINS_SPGRPCD).
table_s2b = read_coefficient_table_jenkins("Table S2b_volbk_coefs_jenkins.csv")

# Table S3a.—Coefficients for predicting total stem outside-bark cubic-foot
# volume based on FIA species code (SPCD).
# Used in Equation 7 for height-to-diameter calculations (GTR page 14).
table_s3a = read_coefficient_table_fia("Table S3a_volob_coefs_spcd.csv")

# Table S3b.—Coefficients for predicting total stem outside-bark cubic-foot
# volume based on Jenkins species group (JENKINS_SPGRPCD).
# Used in Equation 7 for height-to-diameter calculations (GTR page 14).
table_s3b = read_coefficient_table_jenkins("Table S3b_volob_coefs_jenkins.csv")

# Table S4a.—Coefficients for predicting cumulative outside-bark volume ratio
# based on FIA species code (SPCD).
table_s4a = read_volume_ratio_table_fia("Table S4a_rcumob_coefs_spcd.csv")

# Table S4b.—Coefficients for predicting cumulative outside-bark volume ratio
# based on Jenkins species group (JENKINS_SPGRPCD).
table_s4b = read_volume_ratio_table_jenkins("Table S4b_rcumob_coefs_jenkins.csv")

# Table S5a.—Coefficients for predicting cumulative inside-bark volume ratio
# based on FIA species code (SPCD).
table_s5a = read_volume_ratio_table_fia("Table S5a_rcumib_coefs_spcd.csv")

# Table S5b.—Coefficients for predicting cumulative inside-bark volume ratio
# based on Jenkins species group (JENKINS_SPGRPCD).
table_s5b = read_volume_ratio_table_jenkins("Table S5b_rcumib_coefs_jenkins.csv")

# Table S6a.—Coefficients for predicting total stem bark biomass based on FIA
# species code (SPCD).
table_s6a = read_coefficient_table_fia("Table S6a_bark_biomass_coefs_spcd.csv")

# Table S6b.—Coefficients for predicting total stem bark biomass based on
# Jenkins species group (JENKINS_SPGRPCD).
table_s6b = read_coefficient_table_jenkins("Table S6b_bark_biomass_coefs_jenkins.csv")

# Table S7a.—Coefficients for predicting total branch biomass based on FIA
# species code (SPCD).
table_7a = read_coefficient_table_fia("Table S7a_branch_biomass_coefs_spcd.csv")

# Table S7b.—Coefficients for predicting total branch biomass based on Jenkins
# species group (JENKINS_SPGRPCD).
table_7b = read_coefficient_table_jenkins("Table S7b_branch_biomass_coefs_jenkins.csv")

# Table S8a.—Coefficients for predicting total tree biomass based on FIA
# species code (SPCD).
table_8a = read_coefficient_table_fia("Table S8a_total_biomass_coefs_spcd.csv")

# Table S8b.—Coefficients for predicting total tree biomass based on Jenkins
# species group (JENKINS_SPGRPCD).
table_8b = read_coefficient_table_jenkins("Table S8b_total_biomass_coefs_jenkins.csv")

# Table S9a.—Coefficients for predicting total foliage biomass based on FIA
# species code (SPCD).
table_9a = read_coefficient_table_fia("Table S9a_foliage_coefs_spcd.csv")

# Table S9b.—Coefficients for predicting total foliage biomass based on Jenkins
# species group (JENKINS_SPGRPCD).
table_9b = read_coefficient_table_jenkins("Table S9b_foliage_coefs_jenkins.csv")

TABLES = {
    "s1a": table_s1a,
    "s1b": table_s1b,
    "s2a": table_s2a,
    "s2b": table_s2b,
    "s3a": table_s3a,
    "s3b": table_s3b,
    "s4a": table_s4a,
    "s4b": table_s4b,
    "s5a": table_s5a,
    "s5b": table_s5b,
    "s6a": table_s6a,
    "s6b": table_s6b,
    "s7a": table_7a,
    "s7b": table_7b,
    "s8a": table_8a,
    "s8b": table_8b,
    "s9a": table_9a,
    "s9b": table_9b,
}
