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


REF_SPECIES = read_ref_species_table("REF_SPECIES.csv")
WOOD_DENSITY_PROPORTIONS = read_wood_density_proportions_table(
    "WOOD_DENSITY_PROPORTIONS.csv"
)


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
    "s6a": table_s6a,
    "s6b": table_s6b,
    "s7a": table_7a,
    "s7b": table_7b,
    "s8a": table_8a,
    "s8b": table_8b,
    "s9a": table_9a,
    "s9b": table_9b,
}
