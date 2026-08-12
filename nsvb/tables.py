import csv
from importlib.resources import files

DATA_PATH = files("nsvb").joinpath("data")

# GTR p.8: "k is a set segmentation point that is 9.0 inches for softwoods
# (SPCD<300) and 11.0 inches for hardwoods (SPCD>=300)."
#
# The GTR keys the hardwood/softwood split off the species code throughout --
# for the segmentation point k here, for the sawlog top diameter (7 vs 9 in),
# and for the table 1 / S10b dead-tree lookups. This is NOT always the same as
# REF_SPECIES.SFTWD_HRDWD: 39 species are classed 'S' by FIA despite having
# SPCD >= 300 (mostly exotic conifers such as Norfolk Island pine, SPCD 6156),
# and four carry a blank classification. Deriving k from SFTWD_HRDWD therefore
# both departed from the publication and risked a KeyError on the blank rows,
# so the threshold below is the single definition used everywhere.
HARDWOOD_SPCD_THRESHOLD = 300

K_VALUES = {
    "S": 9.0,
    "H": 11.0,
}


def is_hardwood(spcd):
    """GTR hardwood/softwood classification: SPCD >= 300 is hardwood."""
    return spcd >= HARDWOOD_SPCD_THRESHOLD


def segmentation_point(spcd):
    """k for the segmented model (GTR eqn 2), in inches."""
    return K_VALUES["H" if is_hardwood(spcd) else "S"]


def read_ref_species_table(filename):
    with open(DATA_PATH / filename, "r") as f:
        reader = csv.DictReader(f)
        return {int(float(row["SPCD"])): row for row in reader}


def read_wood_density_proportions_table(filename):
    """Table 1: dead-tree DensProp / BarkProp / BranchProp keyed by
    (class, DECAYCD) where class is 'H' (hardwood) or 'S' (softwood)."""
    with open(DATA_PATH / filename, "r") as f:
        reader = csv.DictReader(f)
        return {
            (row["class"], int(row["DECAYCD"])): {
                "DensProp": float(row["DensProp"]),
                "BarkProp": float(row["BarkProp"]),
                "BranchProp": float(row["BranchProp"]),
            }
            for row in reader
        }


def read_carbon_fraction_live(filename):
    """Table S10a: live-tree carbon fraction (decimal) keyed by SPCD."""
    with open(DATA_PATH / filename, "r") as f:
        reader = csv.DictReader(f)
        return {int(row["SPCD"]): float(row["fia.wood.c"]) / 100.0 for row in reader}


def build_carbon_fraction_by_jenkins_group(by_spcd):
    """Mean live carbon fraction per Jenkins species group.

    Table S10a covers 2,676 of the 2,677 species in REF_SPECIES -- SPCD 6856
    (Micronesian cycad) has no row. Every biomass model happily predicts for
    it via the Jenkins fallback, so without a carbon fallback the pipeline
    produces a biomass number and then dies on the carbon conversion. Taking
    the mean over the species' own Jenkins group keeps that consistent with
    how its biomass coefficients were already resolved.
    """
    sums, counts = {}, {}
    for spcd, fraction in by_spcd.items():
        row = REF_SPECIES.get(spcd)
        if row is None or not row.get("JENKINS_SPGRPCD"):
            continue
        group = int(float(row["JENKINS_SPGRPCD"]))
        sums[group] = sums.get(group, 0.0) + fraction
        counts[group] = counts.get(group, 0) + 1
    return {group: sums[group] / counts[group] for group in sums}


def read_carbon_fraction_dead(filename):
    """Table S10b: dead-tree carbon fraction (decimal) keyed by
    (DECAYCD, hardwood_bool). CSV labels the class as 'Hardwood'/'Softwood'
    (different from WOOD_DENSITY_PROPORTIONS, which uses 'H'/'S')."""
    with open(DATA_PATH / filename, "r") as f:
        reader = csv.DictReader(f)
        return {
            (int(row["Decay code"]), row["S/H"] == "Hardwood"): float(row["C fraction"]) / 100.0
            for row in reader
        }


def read_eco_div_prov_table(filename):
    """eco_div_prov.csv: maps FIA ecological DIVISION -> PROVINCE. The mapping
    is one-to-many (e.g. M240 -> M241, M242); we keep the FIRST province per
    division as the representative fallback for callers that have only a
    division code on hand. Callers who know the exact sub-province should
    pass it directly to functions taking a ``province`` argument."""
    with open(DATA_PATH / filename, "r") as f:
        reader = csv.DictReader(f)
        result = {}
        for row in reader:
            row = {k.lstrip("﻿"): v for k, v in row.items()}
            div = row["eco_division"]
            prov = row["eco_province"]
            # Keep first occurrence per division.
            result.setdefault(div, prov)
        return result


def read_crown_ratio_table(filename):
    """Table S11: mean crown ratio (as DECIMAL fraction) keyed by
    (division_or_province, hardwood_bool). The CSV stores the value as a
    percentage in the 'Mean CR' column; we convert to fraction at load
    time so callers can multiply directly."""
    with open(DATA_PATH / filename, "r") as f:
        reader = csv.DictReader(f)
        # Source CSV has BOM-prefixed header; csv.DictReader sees it as
        # the first key. Normalize keys to be safe.
        result = {}
        for row in reader:
            # Strip BOM from any key
            row = {k.lstrip("﻿"): v for k, v in row.items()}
            div = row["Division"]
            hwd = row["HWD Y/N"] == "Y"
            mean_cr_pct = float(row["Mean CR"])
            result[(div, hwd)] = mean_cr_pct / 100.0
        return result


# GTR p.9: "for slash pine (Pinus elliottii) (SPCD = 111) and loblolly pine
# (P. taeda) (SPCD = 131), stand origins for planted (stand origin code
# (STDORGCD) = 1) and natural (STDORGCD = 0) stands may be fitted separately."
#
# STDORGCD is therefore part of the coefficient key, not an ignorable column.
# Only those two species carry it; every other row has STDORGCD blank, meaning
# "applies to any stand origin". Keying on (SPCD, DIVISION) alone silently
# dropped one of the two fitted models -- whichever parsed first -- which for
# the four affected (SPCD, DIVISION) combinations meant natural-origin
# coefficients were discarded outright, and often a different model form with
# them.
STDORGCD_ANY = ""       # row applies regardless of stand origin
STDORGCD_NATURAL = "0"
STDORGCD_PLANTED = "1"


def _stdorgcd_key(row):
    """Normalize the STDORGCD column to '', '0' or '1'."""
    raw = (row.get("STDORGCD") or "").strip()
    if raw in (STDORGCD_ANY, STDORGCD_NATURAL, STDORGCD_PLANTED):
        return raw
    raise ValueError(f"unexpected STDORGCD value {raw!r} in coefficient table")


def read_coefficient_table_fia(filename):
    """S1a/S2a/S6a-S9a coefs keyed by (SPCD, DIVISION, STDORGCD)."""
    with open(DATA_PATH / filename, "r") as f:
        reader = csv.DictReader(f)
        return {
            (int(row["SPCD"]), row["DIVISION"], _stdorgcd_key(row)): {
                "model": int(row["model"]),
                "a": float(row["a"]),
                "a1": float(row["a1"]) if row.get("a1") else None,
                "b": float(row["b"]),
                "b1": float(row["b1"]) if row.get("b1") else None,
                "c": float(row["c"]),
                "c1": float(row["c1"]) if row.get("c1") else None,
                "k": segmentation_point(int(row["SPCD"])),
            }
            for row in reader
        }


def resolve_stdorgcd(stdorgcd):
    """Normalize a caller-supplied stand origin to a table key.

    ``None`` means "not supplied", and resolves to natural (STDORGCD=0), which
    is FIA's baseline code and the more common condition nationally. Only
    SPCD 111 and 131 have origin-specific coefficients, so for every other
    species this choice is inert.
    """
    if stdorgcd is None:
        return STDORGCD_NATURAL
    if isinstance(stdorgcd, str):
        key = stdorgcd.strip()
    else:
        # Reject non-integral values rather than truncating them: str(int(1.5))
        # would silently resolve to planted.
        try:
            numeric = float(stdorgcd)
        except (TypeError, ValueError):
            raise ValueError(
                f"stdorgcd must be 0 (natural), 1 (planted) or None; "
                f"got {stdorgcd!r}"
            ) from None
        if numeric != int(numeric):
            raise ValueError(
                f"stdorgcd must be a whole number 0 or 1; got {stdorgcd!r}"
            )
        key = str(int(numeric))
    if key not in (STDORGCD_NATURAL, STDORGCD_PLANTED):
        raise ValueError(
            f"stdorgcd must be 0 (natural), 1 (planted) or None; got {stdorgcd!r}"
        )
    return key


def lookup_spcd_coefs(table, spcd, division, stdorgcd):
    """Resolve one row from a (SPCD, DIVISION, STDORGCD)-keyed table.

    Cascade, most specific first:

      1. (spcd, division, stdorgcd) -- origin-specific fit for this ecodivision
      2. (spcd, division, "")       -- ecodivision fit that ignores origin
      3. (spcd, "", stdorgcd)       -- origin-specific species-level fit
      4. (spcd, "", "")             -- species-level fit that ignores origin

    Raises KeyError if nothing matches, which is the caller's signal to fall
    back to the Jenkins species-group tables.

    Step 3 is preferred over a division-matched row with the *wrong* origin,
    because no split (SPCD, DIVISION) combination has an origin-agnostic row
    to fall back on and stand origin moves biomass by up to ~19 percent for
    these species. In practice this only fires for planted loblolly in
    DIVISION 220 or M230, where the GTR fitted a natural-origin model only.

    Evaluating each candidate lazily also removes a latent trap in the
    previous implementation, which used ``table[(spcd, "")]`` as a dict.get
    default: that expression was evaluated eagerly, so a species with an
    ecodivision row but no species-level row would have raised KeyError and
    fallen through to Jenkins even though a perfectly good row existed.
    """
    for key in (
        (spcd, division, stdorgcd),
        (spcd, division, STDORGCD_ANY),
        (spcd, "", stdorgcd),
        (spcd, "", STDORGCD_ANY),
    ):
        if key in table:
            return table[key]
    raise KeyError((spcd, division, stdorgcd))


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


def read_volob_table_fia(filename):
    """S3a: outside-bark volume coefs (a, b, c) keyed by
    (SPCD, DIVISION, STDORGCD)."""
    with open(DATA_PATH / filename, "r") as f:
        reader = csv.DictReader(f)
        return {
            (int(row["SPCD"]), row["DIVISION"], _stdorgcd_key(row)): {
                "model": int(row["model"]),
                "a": float(row["a"]),
                "b": float(row["b"]),
                "c": float(row["c"]),
            }
            for row in reader
        }


def read_volob_table_jenkins(filename):
    """S3b: outside-bark volume coefs (a, b, c) keyed by JENKINS_SPGRPCD."""
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


def read_rcum_table_fia(filename):
    """S4a / S5a: volume-ratio coefs (alpha, beta) keyed by
    (SPCD, DIVISION, STDORGCD)."""
    with open(DATA_PATH / filename, "r") as f:
        reader = csv.DictReader(f)
        return {
            (int(row["SPCD"]), row["DIVISION"], _stdorgcd_key(row)): {
                "model": int(row["model"]),
                "alpha": float(row["alpha"]),
                "beta": float(row["beta"]),
            }
            for row in reader
        }


def read_rcum_table_jenkins(filename):
    """S4b / S5b: volume-ratio coefs (alpha, beta) keyed by JENKINS_SPGRPCD."""
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


REF_SPECIES = read_ref_species_table("REF_SPECIES.csv")
WOOD_DENSITY_PROPORTIONS = read_wood_density_proportions_table(
    "WOOD_DENSITY_PROPORTIONS.csv"
)
# Table S11: mean crown ratio defaults by (Province, hardwood). The CSV
# column is labeled "Division" but actually contains province codes; see the
# R reference repository's comment for the same observation.
CROWN_RATIO_DEFAULTS = read_crown_ratio_table("Table S11_mean_crprop.csv")
# FIA ecological DIVISION -> PROVINCE mapping for fallback S11 lookups when a
# caller only knows the division (one province per division, first match).
ECO_DIV_PROV = read_eco_div_prov_table("eco_div_prov.csv")
# Table S10a / S10b: carbon fraction for live (by SPCD) and dead (by
# DECAYCD + hardwood) trees, as decimals. Multiply AGBPredictedred by these
# to obtain C content in pounds.
CARBON_FRACTION_LIVE = read_carbon_fraction_live(
    "Table S10a_fia_wood_c_frac_live.csv.csv"
)
# Jenkins-group means, used only for species S10a omits (currently SPCD 6856).
CARBON_FRACTION_LIVE_BY_JENKINS = build_carbon_fraction_by_jenkins_group(
    CARBON_FRACTION_LIVE
)
CARBON_FRACTION_DEAD = read_carbon_fraction_dead(
    "Table S10b_fia_wood_c_frac_dead.csv.csv"
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

# Table S3a.—Coefficients for predicting total stem outside-bark cubic-foot
# volume based on FIA species code (SPCD). Used for the iterative
# merchantable / sawlog height solver (equation 7).
table_s3a = read_volob_table_fia("Table S3a_volob_coefs_spcd.csv")

# Table S3b.—Outside-bark volume coefficients keyed by Jenkins species group.
table_s3b = read_volob_table_jenkins("Table S3b_volob_coefs_jenkins.csv")

# Table S4a.—Outside-bark volume RATIO coefficients (alpha, beta) keyed by
# (SPCD, DIVISION). Combined with S3 to solve equation 7 for the height
# corresponding to a given top outside-bark diameter.
table_s4a = read_rcum_table_fia("Table S4a_rcumob_coefs_spcd.csv")

# Table S4b.—Outside-bark volume RATIO coefficients keyed by Jenkins group.
table_s4b = read_rcum_table_jenkins("Table S4b_rcumob_coefs_jenkins.csv")

# Table S5a.—Inside-bark volume RATIO coefficients (alpha, beta) keyed by
# (SPCD, DIVISION). Used for R_1, R_m, R_s and R_b in the stem-profile
# integral (equation 6).
table_s5a = read_rcum_table_fia("Table S5a_rcumib_coefs_spcd.csv")

# Table S5b.—Inside-bark volume RATIO coefficients keyed by Jenkins group.
table_s5b = read_rcum_table_jenkins("Table S5b_rcumib_coefs_jenkins.csv")

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
