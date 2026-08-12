"""
Property, contract, and data-integrity tests for the NSVB estimators.

``test_examples.py`` answers "does this reproduce the publication?" by checking
the four GTR worked examples. It does that well, but it is a *characterization*
suite: one oracle (the GTR text) evaluated at four points in a roughly
ten-dimensional input space. It cannot speak to input domains, return
contracts, or invariants, and it never visits saplings, four of the five decay
classes, model form 3, or 2,673 of the 2,677 species.

This module covers the orthogonal axis -- the software rather than the fidelity:

  * an *independent* transcription of GTR equations 1-5 and the coefficient
    CSVs, so a bug in ``models.py`` or ``tables.py`` cannot hide behind the
    same bug in the test;
  * invariants that must hold at every input, not just four (additivity,
    non-negativity, ratio ordering, monotonicity in decay class);
  * the scalar/array return contracts that ``_check_scalar`` is blind to;
  * data integrity of the vendored supplementary tables.

Tests marked ``xfail(strict=True)`` document known defects with a task
reference. When the fix lands the test starts passing, ``strict`` turns that
xpass into a failure, and the marker must be removed -- so a fix cannot land
without also retiring its own bug ticket.
"""

import csv
import inspect
import warnings
import itertools
from importlib.resources import files

import numpy as np
import pytest

from nsvb import estimators as e
from nsvb.tables import (
    CARBON_FRACTION_DEAD,
    CARBON_FRACTION_LIVE,
    CROWN_RATIO_DEFAULTS,
    REF_SPECIES,
    TABLES,
    WOOD_DENSITY_PROPORTIONS,
)

DATA_PATH = files("nsvb").joinpath("data")

# ---------------------------------------------------------------------------
# A broader tree grid than the four GTR examples
# ---------------------------------------------------------------------------
#
# Chosen to span the axes test_examples.py leaves fixed: coefficient source
# (SPCD/DIVISION, SPCD-level, Jenkins), hardwood vs softwood, live vs every
# decay class, intact vs broken top, observed vs Table S11 crown ratio, and
# tree size from sapling to large sawtimber.


class Tree:
    """One input row. ``full`` matches the (spcd, dia, ht, division, cull, ah,
    decaycd, cr, province) ordering used by the harmonization estimators."""

    def __init__(self, spcd, dia, ht, division="", cull=0.0, ah=None,
                 decaycd=0, cr=None, province="", label=""):
        self.spcd, self.dia, self.ht, self.division = spcd, dia, ht, division
        self.cull, self.ah, self.decaycd = cull, ah, decaycd
        self.cr, self.province, self.label = cr, province, label

    @property
    def full(self):
        return (self.spcd, self.dia, self.ht, self.division, self.cull,
                self.ah, self.decaycd, self.cr, self.province)

    @property
    def dhtd(self):
        return (self.spcd, self.dia, self.ht, self.division)

    def replace(self, **kw):
        d = dict(spcd=self.spcd, dia=self.dia, ht=self.ht, division=self.division,
                 cull=self.cull, ah=self.ah, decaycd=self.decaycd, cr=self.cr,
                 province=self.province, label=self.label)
        d.update(kw)
        return Tree(**d)

    def __repr__(self):
        return self.label or f"spcd{self.spcd}"


# Species picked so every coefficient-lookup path is represented.
DOUGLAS_FIR = 202   # softwood, SPCD/DIVISION rows
RED_MAPLE = 316     # hardwood, falls back to SPCD-level ("") rows
TANOAK = 631        # hardwood, falls back to Jenkins group
WHITE_OAK = 802     # hardwood, SPCD/DIVISION rows

GRID = [
    Tree(DOUGLAS_FIR, 20.0, 110.0, "240", label="doug-fir/large/live"),
    Tree(DOUGLAS_FIR, 7.5, 45.0, "240", cull=5.0, label="doug-fir/small/cull"),
    Tree(RED_MAPLE, 11.1, 38.0, "M210", cull=3.0, label="red-maple/live/cull"),
    Tree(TANOAK, 11.3, 28.0, "M240", cull=10.0, ah=21.0, decaycd=2,
         province="M242", label="tanoak/dead2/broken"),
    Tree(WHITE_OAK, 18.1, 65.0, "M220", cull=2.0, ah=59.0, cr=0.30,
         province="M220", label="white-oak/broken/obs-cr"),
    Tree(WHITE_OAK, 25.0, 80.0, "M220", label="white-oak/large/live"),
    Tree(DOUGLAS_FIR, 30.0, 150.0, "240", decaycd=4, province="M242",
         label="doug-fir/dead4/intact"),
    Tree(RED_MAPLE, 6.0, 30.0, "M210", decaycd=1, province="212",
         label="red-maple/dead1/intact"),
]

# Trees whose merchantable geometry is defined (D >= 5 in). Saplings are
# handled separately in TestSaplings.
MERCHANTABLE_GRID = [t for t in GRID if t.dia >= 5.0]

SAPLINGS = [
    Tree(DOUGLAS_FIR, 3.0, 15.0, "240", label="doug-fir/sapling"),
    Tree(WHITE_OAK, 1.5, 9.0, "M220", label="white-oak/sapling"),
    Tree(RED_MAPLE, 4.9, 22.0, "M210", cull=4.0, label="red-maple/sapling-edge"),
]


def ids(trees):
    return [t.label for t in trees]


def scalar(x):
    """Collapse any 0-d / 1-element result to a Python float."""
    return float(np.asarray(x).reshape(-1)[0])


# ---------------------------------------------------------------------------
# Independent oracle: GTR equations 1-5, transcribed from the publication
# ---------------------------------------------------------------------------
#
# Deliberately NOT importing nsvb.models. If models.py and this transcription
# agree, the model forms are right; if they agree because they share a bug,
# that bug had to be made twice from two different sources.


def gtr_eq1(dia, ht, a, b, c, **_):
    """Schumacher-Hall (GTR eqn 1): y = a * D^b * H^c"""
    return a * dia ** b * ht ** c


def gtr_eq2(dia, ht, a, b, b1, c, k, **_):
    """Segmented (GTR eqn 2). k = 9.0 softwood (SPCD<300), 11.0 hardwood."""
    if dia < k:
        return a * dia ** b * ht ** c
    return a * k ** (b - b1) * dia ** b1 * ht ** c


def gtr_eq3(dia, ht, a, a1, b, c, c1, **_):
    """Continuously Variable (GTR eqn 3):
    y = a * D^(a1 * (1-exp(-b*D))^c1) * H^c

    c1 raises only (1-exp(-b*D)), not a1*(1-exp(-b*D)) -- GTR p.8 prints c1 on
    the closing paren of the inner group with no outer parenthesis.

    Transcription alone cannot settle this: the rendered equation is ambiguous
    enough that an earlier version of both this oracle AND models.py carried
    the same wrong grouping, so they agreed with each other and the check
    passed. TestModelForms::test_model_3_* below therefore anchors model 3
    against evidence that does not depend on re-reading the equation."""
    return a * dia ** (a1 * (1 - np.exp(-b * dia)) ** c1) * ht ** c


def gtr_eq4(dia, ht, a, b, b1, c, **_):
    """Modified Wiley (GTR eqn 4): y = a * D^b * H^c * exp(-(b1*D))"""
    return a * dia ** b * ht ** c * np.exp(-(b1 * dia))


def gtr_eq5(dia, ht, a, b, c, wdsg, **_):
    """Modified Schumacher-Hall (GTR eqn 5): y = a * D^b * H^c * WDSG"""
    return a * dia ** b * ht ** c * wdsg


GTR_EQUATIONS = {1: gtr_eq1, 2: gtr_eq2, 3: gtr_eq3, 4: gtr_eq4, 5: gtr_eq5}


def read_raw(filename):
    """Read a supplementary CSV with no interpretation whatsoever."""
    with open(DATA_PATH / filename, "r") as f:
        return list(csv.DictReader(f))


SPCD_TABLE_FILES = {
    "s1a": "Table S1a_volib_coefs_spcd.csv",
    "s2a": "Table S2a_volbk_coefs_spcd.csv",
    "s3a": "Table S3a_volob_coefs_spcd.csv",
    "s4a": "Table S4a_rcumob_coefs_spcd.csv",
    "s5a": "Table S5a_rcumib_coefs_spcd.csv",
    "s6a": "Table S6a_bark_biomass_coefs_spcd.csv",
    "s7a": "Table S7a_branch_biomass_coefs_spcd.csv",
    "s8a": "Table S8a_total_biomass_coefs_spcd.csv",
    "s9a": "Table S9a_foliage_coefs_spcd.csv",
}

# Estimator entry points that read each coefficient table, for the
# end-to-end model-form check.
TABLE_ESTIMATORS = {
    "s1a": e.total_inside_bark_wood_volume,
    "s2a": e.total_bark_wood_volume,
    "s6a": e.total_stem_bark_weight,
    "s7a": e.total_branch_weight,
    "s8a": e.total_aboveground_biomass,
    "s9a": e.total_foliage_dry_weight,
}


# =============================================================================
# Model forms -- checked against an independent transcription of the GTR
# =============================================================================
class TestModelForms:
    """Equations 1-5 straight from GTR pp. 8 and 10, applied to coefficients
    read straight from the CSVs, compared against the estimator."""

    @pytest.mark.parametrize("table", sorted(TABLE_ESTIMATORS))
    @pytest.mark.parametrize("model", [1, 2, 3, 4])
    def test_every_model_form_matches_the_gtr_equation(self, table, model):
        """Each (table, model form) combination present in the data is
        evaluated both ways. Model 3 has no coverage at all in
        test_examples.py -- no GTR example species uses it."""
        rows = [r for r in read_raw(SPCD_TABLE_FILES[table])
                if int(r["model"]) == model]
        if not rows:
            pytest.skip(f"{table} has no model-{model} rows")

        estimator = TABLE_ESTIMATORS[table]
        checked = 0
        for row in rows:
            spcd, division = int(row["SPCD"]), row["DIVISION"]
            # Rows split by stand origin are ambiguous until STDORGCD is
            # honoured (task #7); TestCoefficientTables covers them.
            if row.get("STDORGCD", "") != "":
                continue
            if int(row["model"]) != model:
                continue
            hardwood = spcd >= 300              # GTR p.8 defines k this way
            coefs = dict(
                a=float(row["a"]),
                a1=float(row["a1"]) if row.get("a1") else None,
                b=float(row["b"]),
                b1=float(row["b1"]) if row.get("b1") else None,
                c=float(row["c"]),
                c1=float(row["c1"]) if row.get("c1") else None,
                k=11.0 if hardwood else 9.0,
                wdsg=float(REF_SPECIES[spcd]["WOOD_SPGR_GREENVOL_DRYWT"]),
            )
            for dia, ht in [(6.0, 35.0), (14.0, 70.0), (26.0, 105.0)]:
                expected = GTR_EQUATIONS[model](dia, ht, **coefs)
                got = scalar(estimator(spcd, dia, ht, division))
                np.testing.assert_allclose(
                    got, expected, rtol=1e-12,
                    err_msg=f"{table} model {model} SPCD={spcd} DIV={division!r} "
                            f"D={dia} H={ht}",
                )
            checked += 1
        if checked == 0:
            # Every row for this (table, model) belongs to SPCD 111/131 and is
            # split by stand origin, so which coefficients the estimator will
            # return is undefined until task #7 lands. Affects s6a/m4, s7a/m2,
            # s8a/m3, s9a/m3 and s9a/m4.
            pytest.skip(f"{table} model {model}: all rows are STDORGCD-split")

    def test_model_3_is_exercised_end_to_end(self):
        """Model 3 (Continuously Variable) has zero coverage in
        test_examples.py -- no GTR example species uses it. S1a routes SPCD
        800 through it, so this is a genuine end-to-end check rather than a
        table lookup."""
        rows = [r for r in read_raw(SPCD_TABLE_FILES["s1a"])
                if int(r["model"]) == 3 and r.get("STDORGCD", "") == ""]
        assert rows, "S1a should contain testable model-3 rows"
        row = rows[0]
        spcd, division = int(row["SPCD"]), row["DIVISION"]
        assert TABLES["s1a"][(spcd, division, "")]["model"] == 3
        expected = gtr_eq3(14.0, 70.0, a=float(row["a"]), a1=float(row["a1"]),
                           b=float(row["b"]), c=float(row["c"]),
                           c1=float(row["c1"]))
        got = scalar(e.total_inside_bark_wood_volume(spcd, 14.0, 70.0, division))
        np.testing.assert_allclose(got, expected, rtol=1e-12)

    # Every model-3 row in the shipped tables, as (table, SPCD, STDORGCD).
    MODEL_3_ROWS = [("s1a", 800, ""), ("s2a", 12, ""),
                    ("s8a", 111, "1"), ("s9a", 131, "1")]

    @pytest.mark.parametrize("table,spcd,stdorgcd", MODEL_3_ROWS,
                             ids=[f"{t}-spcd{s}" for t, s, _ in MODEL_3_ROWS])
    def test_model_3_diameter_exponent_is_allometrically_plausible(
            self, table, spcd, stdorgcd):
        """Anchor for eqn 3's exponent grouping that does NOT re-read the
        equation. As D grows, (1 - exp(-b*D)) -> 1, so the diameter exponent
        tends to a1 under the correct grouping and to a1**c1 under the wrong
        one. Volume and biomass both scale close to D^2, so the limit has to
        sit in a plausible allometric band; a1**c1 collapses to 1.16-1.53,
        which is far too low for any of these components."""
        # DIVISION "" so the row matches the estimator call below; SPCD 12 has
        # four model-3 rows across different divisions.
        row = next(r for r in read_raw(SPCD_TABLE_FILES[table])
                   if int(r["SPCD"]) == spcd and int(r["model"]) == 3
                   and r["DIVISION"] == "" and r.get("STDORGCD", "") == stdorgcd)
        a1, c1 = float(row["a1"]), float(row["c1"])

        # Empirical limit of the exponent the code actually applies.
        big = 1_000.0
        org = int(stdorgcd) if stdorgcd else None
        implied = np.log(
            scalar(TABLE_ESTIMATORS[table](spcd, big, 60.0, "", stdorgcd=org))
            / scalar(TABLE_ESTIMATORS[table](spcd, big / 2, 60.0, "", stdorgcd=org))
        ) / np.log(2)
        assert 1.6 <= implied <= 2.3, (
            f"{table} SPCD {spcd}: implied large-D exponent {implied:.4f} "
            f"(a1={a1:.4f}, a1**c1={a1 ** c1:.4f})"
        )
        np.testing.assert_allclose(implied, a1, rtol=1e-3)

    @pytest.mark.parametrize("table,jenkins_table,spcd",
                             [("s1a", "s1b", 800), ("s2a", "s2b", 12)],
                             ids=["oak-volib", "balsam-fir-volbk"])
    def test_model_3_agrees_with_the_species_jenkins_group(
            self, table, jenkins_table, spcd):
        """Second independent anchor: a species-level model must land near its
        own Jenkins species-group model, which uses a different form and
        different coefficients. The wrong exponent grouping misses by 3-7x."""
        group = int(REF_SPECIES[spcd]["JENKINS_SPGRPCD"])
        row = TABLES[jenkins_table][group]
        for dia, ht in [(8.0, 45.0), (16.0, 80.0), (26.0, 105.0)]:
            jenkins = GTR_EQUATIONS[row["model"]](
                dia, ht, wdsg=float(REF_SPECIES[spcd]["WOOD_SPGR_GREENVOL_DRYWT"]),
                **{k: row[k] for k in ("a", "b", "c") if k in row})
            species = scalar(TABLE_ESTIMATORS[table](spcd, dia, ht, ""))
            assert species == pytest.approx(jenkins, rel=0.45), (
                f"{table} SPCD {spcd} at D={dia} H={ht}: species-level "
                f"{species:.4f} vs Jenkins group {jenkins:.4f}"
            )

    def test_jenkins_fallback_uses_model_5_with_wdsg(self):
        """Biomass Jenkins tables use eqn 5, which multiplies by the species
        WDSG rather than a group-level constant."""
        spcd, dia, ht = TANOAK, 11.3, 28.0
        spgrp = int(REF_SPECIES[spcd]["JENKINS_SPGRPCD"])
        row = TABLES["s8b"][spgrp]
        assert row["model"] == 5
        expected = gtr_eq5(dia, ht, row["a"], row["b"], row["c"],
                           float(REF_SPECIES[spcd]["WOOD_SPGR_GREENVOL_DRYWT"]))
        got = scalar(e.total_aboveground_biomass(spcd, dia, ht, "M240"))
        np.testing.assert_allclose(got, expected, rtol=1e-12)


# =============================================================================
# Data integrity of the vendored supplementary tables
# =============================================================================
class TestCoefficientTables:

    @pytest.mark.parametrize("table", sorted(SPCD_TABLE_FILES))
    def test_species_level_fallback_row_exists(self, table):
        """``_run_model_form`` evaluates ``table[(spcd, "")]`` eagerly as a
        dict.get default. A species with a DIVISION row but no species-level
        row would silently fall through to Jenkins."""
        rows = read_raw(SPCD_TABLE_FILES[table])
        by_spcd = {}
        for r in rows:
            by_spcd.setdefault(int(r["SPCD"]), set()).add(r["DIVISION"])
        missing = sorted(s for s, divs in by_spcd.items() if "" not in divs)
        assert not missing, (
            f"{table}: SPCDs with DIVISION rows but no species-level row: {missing}"
        )

    @pytest.mark.parametrize("table", sorted(SPCD_TABLE_FILES))
    def test_stand_origin_rows_are_not_silently_dropped(self, table):
        """GTR p.9: slash pine (111) and loblolly pine (131) have separately
        fitted planted (STDORGCD=1) and natural (STDORGCD=0) coefficients,
        often with different model forms. Keying on (SPCD, DIVISION) alone
        keeps whichever row parses last."""
        rows = read_raw(SPCD_TABLE_FILES[table])
        assert len(rows) == len(TABLES[table]), (
            f"{table}: {len(rows)} CSV rows collapsed to {len(TABLES[table])} "
            f"table entries -- {len(rows) - len(TABLES[table])} coefficient "
            f"sets are unreachable"
        )

    def test_k_segmentation_point_matches_gtr_definition(self):
        """GTR p.8: k is 9.0 in for softwoods (SPCD<300) and 11.0 in for
        hardwoods (SPCD>=300)."""
        for table in SPCD_TABLE_FILES:
            for (spcd, _division, _stdorgcd), row in TABLES[table].items():
                if "k" not in row:
                    continue
                assert row["k"] == (11.0 if spcd >= 300 else 9.0), (
                    f"{table} SPCD={spcd}: k={row['k']}"
                )

    def test_table_1_matches_the_publication(self):
        """GTR table 1, p.11. Decay class 4 values are reused for DECAYCD 5."""
        published = {
            ("H", 1): (0.99, 1.0, 1.0), ("H", 2): (0.80, 0.8, 0.5),
            ("H", 3): (0.54, 0.5, 0.1), ("H", 4): (0.43, 0.2, 0.0),
            ("H", 5): (0.43, 0.0, 0.0),
            ("S", 1): (0.97, 1.0, 1.0), ("S", 2): (1.00, 0.8, 0.5),
            ("S", 3): (0.92, 0.5, 0.1), ("S", 4): (0.55, 0.2, 0.0),
            ("S", 5): (0.55, 0.0, 0.0),
        }
        assert set(WOOD_DENSITY_PROPORTIONS) == set(published)
        for key, (dens, bark, branch) in published.items():
            row = WOOD_DENSITY_PROPORTIONS[key]
            assert (row["DensProp"], row["BarkProp"], row["BranchProp"]) == \
                   (dens, bark, branch), f"table 1 row {key}"

    def test_dead_carbon_fraction_table_is_complete(self):
        """S10b must cover all 10 (decay class, hardwood) combinations."""
        assert set(CARBON_FRACTION_DEAD) == {
            (d, h) for d in range(1, 6) for h in (True, False)
        }
        for cf in CARBON_FRACTION_DEAD.values():
            assert 0.3 < cf < 0.7, cf

    @pytest.mark.xfail(strict=True, reason="upstream data gap, not a package "
                                           "bug: the published Table S10a has "
                                           "no row for SPCD 6856 (Micronesian "
                                           "cycad). Kept as a live marker so "
                                           "the gap is noticed if the USFS "
                                           "reissues the table; the estimators "
                                           "cover it via a Jenkins-group mean")
    def test_live_carbon_fraction_covers_every_species(self):
        uncovered = sorted(set(REF_SPECIES) - set(CARBON_FRACTION_LIVE))
        assert not uncovered, f"SPCDs with no S10a carbon fraction: {uncovered}"

    def test_carbon_content_works_wherever_biomass_does(self):
        """A species the biomass models happily predict for must not blow up
        one step later in the carbon conversion."""
        assert np.isfinite(scalar(e.agb_predicted_reduced(6856, 12.0, 50.0, "")))
        assert np.isfinite(scalar(e.carbon_content(6856, 12.0, 50.0, "")))

    def test_carbon_fraction_fallback_uses_the_species_jenkins_group(self):
        """The fallback is the group mean, not an invented constant, so it is
        consistent with how that species' biomass coefficients already
        resolve (SPCD 6856 has no species-level rows either)."""
        from nsvb.tables import CARBON_FRACTION_LIVE_BY_JENKINS
        group = int(float(REF_SPECIES[6856]["JENKINS_SPGRPCD"]))
        expected = CARBON_FRACTION_LIVE_BY_JENKINS[group]
        assert 0.3 < expected < 0.7
        np.testing.assert_allclose(
            scalar(e.carbon_content(6856, 12.0, 50.0, "")),
            scalar(e.agb_predicted_reduced(6856, 12.0, 50.0, "")) * expected,
            rtol=1e-12)

    def test_species_with_an_s10a_row_ignore_the_fallback(self):
        np.testing.assert_allclose(
            scalar(e.carbon_content(802, 12.0, 50.0, "")),
            scalar(e.agb_predicted_reduced(802, 12.0, 50.0, ""))
            * CARBON_FRACTION_LIVE[802], rtol=1e-12)

    def test_crown_ratio_defaults_are_fractions_with_a_fallback(self):
        assert ("UNDEFINED", True) in CROWN_RATIO_DEFAULTS
        assert ("UNDEFINED", False) in CROWN_RATIO_DEFAULTS
        for key, cr in CROWN_RATIO_DEFAULTS.items():
            assert 0.0 < cr < 1.0, f"S11 {key} = {cr} (expected a fraction)"


# =============================================================================
# Stand origin (STDORGCD)
# =============================================================================
class TestStandOrigin:
    """GTR p.9 fits slash pine (111) and loblolly pine (131) separately for
    planted (STDORGCD=1) and natural (STDORGCD=0) stands. Those are the only
    two species affected, so every test here doubles as a check that the
    parameter is inert everywhere else."""

    SPLIT = [(131, "230"), (131, ""), (111, "230"), (111, "")]

    @pytest.mark.parametrize("spcd,division", SPLIT,
                             ids=lambda v: str(v))
    def test_both_origins_are_reachable_and_differ(self, spcd, division):
        natural = scalar(e.total_aboveground_biomass(spcd, 20.0, 95.0, division,
                                                     stdorgcd=0))
        planted = scalar(e.total_aboveground_biomass(spcd, 20.0, 95.0, division,
                                                     stdorgcd=1))
        assert natural > 0 and planted > 0
        assert abs(planted - natural) / natural > 0.01, (
            "the two fitted models should not collapse onto the same answer"
        )

    @pytest.mark.parametrize("spcd,division", SPLIT, ids=lambda v: str(v))
    def test_default_is_natural(self, spcd, division):
        """FIA's baseline code. Before this was keyed properly the planted row
        won by accident of CSV ordering."""
        np.testing.assert_allclose(
            scalar(e.total_aboveground_biomass(spcd, 20.0, 95.0, division)),
            scalar(e.total_aboveground_biomass(spcd, 20.0, 95.0, division,
                                               stdorgcd=0)), rtol=1e-12)

    def test_stand_origin_can_select_a_different_model_form(self):
        """Not merely different coefficients: loblolly in DIVISION 230 is
        Schumacher-Hall (model 1) when natural and segmented (model 2) when
        planted, so dropping the key discarded a whole model form."""
        from nsvb.tables import lookup_spcd_coefs
        assert lookup_spcd_coefs(TABLES["s1a"], 131, "230", "0")["model"] == 1
        assert lookup_spcd_coefs(TABLES["s1a"], 131, "230", "1")["model"] == 2

    def test_cascade_prefers_origin_match_over_division_match(self):
        """DIVISION 220 has a natural-origin loblolly row but no planted one,
        and no origin-agnostic row to fall back on. A planted request resolves
        to the species-level PLANTED fit rather than the division-matched
        NATURAL one."""
        from nsvb.tables import lookup_spcd_coefs
        resolved = lookup_spcd_coefs(TABLES["s1a"], 131, "220", "1")
        assert resolved == lookup_spcd_coefs(TABLES["s1a"], 131, "", "1")
        assert resolved != lookup_spcd_coefs(TABLES["s1a"], 131, "220", "0")

    @pytest.mark.parametrize("spcd,division",
                             [(202, "240"), (316, "M210"), (631, "M240"),
                              (802, "M220"), (800, ""), (12, "130")])
    def test_stand_origin_is_inert_for_every_other_species(self, spcd, division):
        np.testing.assert_allclose(
            scalar(e.agb_predicted_reduced(spcd, 16.0, 70.0, division, stdorgcd=0)),
            scalar(e.agb_predicted_reduced(spcd, 16.0, 70.0, division, stdorgcd=1)),
            rtol=1e-12)

    def test_vectorized_call_can_mix_stand_origins(self):
        result = e.agb_predicted_reduced(
            np.array([131, 131, 202]), np.array([20.0, 20.0, 20.0]),
            np.array([95.0, 95.0, 95.0]), np.array(["230", "230", "240"]),
            stdorgcd=np.array([0, 1, 0]))
        expected = [
            scalar(e.agb_predicted_reduced(131, 20.0, 95.0, "230", stdorgcd=0)),
            scalar(e.agb_predicted_reduced(131, 20.0, 95.0, "230", stdorgcd=1)),
            scalar(e.agb_predicted_reduced(202, 20.0, 95.0, "240", stdorgcd=0)),
        ]
        np.testing.assert_allclose(result, expected, rtol=1e-12)
        assert result[0] != result[1]

    @pytest.mark.parametrize("bad", [2, -1, "x", 1.5])
    def test_invalid_stand_origin_is_rejected(self, bad):
        with pytest.raises(ValueError, match="stdorgcd"):
            e.total_aboveground_biomass(131, 20.0, 95.0, "230", stdorgcd=bad)

    def test_stdorgcd_is_keyword_only_everywhere(self):
        """Placed after every existing parameter and keyword-only, so no
        positional call written against the previous API can silently bind to
        it."""
        checked = 0
        for name in dir(e):
            fn = getattr(e, name)
            if name.startswith("_") or not callable(fn) or not hasattr(fn, "__module__"):
                continue
            if getattr(fn, "__module__", None) != e.__name__:
                continue
            params = inspect.signature(fn).parameters
            if "stdorgcd" not in params:
                continue
            assert params["stdorgcd"].kind is inspect.Parameter.KEYWORD_ONLY, name
            assert list(params)[-1] == "stdorgcd", name
            checked += 1
        assert checked >= 60, f"only {checked} estimators expose stdorgcd"

    def test_unexpected_stdorgcd_in_the_source_csv_is_rejected_at_load(self):
        """The loader must not quietly key an unrecognised stand-origin code
        into the table, where it would become an unreachable row."""
        from nsvb.tables import _stdorgcd_key
        assert _stdorgcd_key({"STDORGCD": " 1 "}) == "1"
        assert _stdorgcd_key({"STDORGCD": None}) == ""
        assert _stdorgcd_key({}) == ""
        with pytest.raises(ValueError, match="unexpected STDORGCD"):
            _stdorgcd_key({"STDORGCD": "2"})

    def test_every_estimator_taking_division_also_takes_stdorgcd(self):
        """They are two halves of one coefficient key; a function that accepts
        one and silently ignores the other would resolve the wrong row."""
        missing = []
        for name in dir(e):
            fn = getattr(e, name)
            if name.startswith("_") or not callable(fn):
                continue
            if getattr(fn, "__module__", None) != e.__name__:
                continue
            params = inspect.signature(fn).parameters
            if "division" in params and "stdorgcd" not in params:
                missing.append(name)
        assert not missing, f"take division but not stdorgcd: {missing}"


# =============================================================================
# Additivity -- the strongest correctness property in the framework
# =============================================================================
class TestAdditivity:
    """The whole point of the harmonization protocol (GTR steps 11-12) is that
    the components sum to the predicted total. Nothing in test_examples.py
    asserts this, yet it holds to ~1e-13 and would break loudly under most
    plausible edits to steps 11-14."""

    @pytest.mark.parametrize("tree", MERCHANTABLE_GRID, ids=ids(MERCHANTABLE_GRID))
    def test_harmonized_components_sum_to_agb(self, tree):
        total = (scalar(e.harmonized_wood(*tree.full))
                 + scalar(e.harmonized_bark(*tree.full))
                 + scalar(e.harmonized_branch(*tree.full)))
        np.testing.assert_allclose(total, scalar(e.agb_predicted_reduced(*tree.full)),
                                   rtol=1e-12)

    @pytest.mark.parametrize("tree", MERCHANTABLE_GRID, ids=ids(MERCHANTABLE_GRID))
    def test_bole_stump_and_top_sum_to_agb(self, tree):
        """DRYBIO_TOP is defined as the residual (GTR step 16), so this is
        near-tautological -- but it pins the definition against a refactor."""
        total = (scalar(e.merchantable_outside_bark_weight(*tree.full))
                 + scalar(e.stump_outside_bark_weight(*tree.full))
                 + scalar(e.drybio_top(*tree.full)))
        np.testing.assert_allclose(total, scalar(e.agb_predicted_reduced(*tree.full)),
                                   rtol=1e-12)

    @pytest.mark.parametrize("tree", MERCHANTABLE_GRID, ids=ids(MERCHANTABLE_GRID))
    def test_stem_volume_subcomponents_sum_to_the_total(self, tree):
        """Merchantable + stump + top = total, for sound volumes.

        Holds because R_eff_mer + R_eff_top == R_b by construction. Note this
        invariant does NOT discriminate between the gross basis used here and
        the literal reading of GTR Example 3's Wmerib prose -- that form is
        defined by subtraction from the total, so it telescopes too. The two
        differ in how they *allocate* mass between bole, stump and top when
        CULL > 0; Example 4 (GTR p.25) settles the allocation in favour of the
        gross basis. See the Step 14 comment in estimators.py."""
        args = tree.full[:7]  # (spcd, dia, ht, division, cull, ah, decaycd)
        total = (scalar(e.merchantable_inside_bark_volume_sound(*args))
                 + scalar(e.stump_inside_bark_volume_sound(*args))
                 + scalar(e.top_inside_bark_volume_sound(*args)))
        np.testing.assert_allclose(
            total, scalar(e.total_inside_bark_wood_volume_sound(*args)), rtol=1e-12)

    @pytest.mark.parametrize("tree", MERCHANTABLE_GRID, ids=ids(MERCHANTABLE_GRID))
    def test_outside_bark_equals_wood_plus_bark(self, tree):
        np.testing.assert_allclose(
            scalar(e.total_outside_bark_volume(*tree.dhtd)),
            scalar(e.total_inside_bark_wood_volume(*tree.dhtd))
            + scalar(e.total_bark_wood_volume(*tree.dhtd)),
            rtol=1e-12,
        )
        args = tree.full[:7]
        np.testing.assert_allclose(
            scalar(e.total_outside_bark_volume_sound(*args)),
            scalar(e.total_inside_bark_wood_volume_sound(*args))
            + scalar(e.total_bark_volume_sound(*args)),
            rtol=1e-12,
        )


# =============================================================================
# Bounds -- values that are physically impossible must not be returned
# =============================================================================
class TestBounds:

    @pytest.mark.parametrize("tree", MERCHANTABLE_GRID, ids=ids(MERCHANTABLE_GRID))
    def test_volume_ratios_are_ordered_and_in_unit_interval(self, tree):
        r_1 = scalar(e.stump_volume_ratio(*tree.dhtd))
        r_m = scalar(e.merchantable_volume_ratio(*tree.dhtd))
        assert 0.0 < r_1 < r_m <= 1.0, f"R1={r_1} Rm={r_m}"
        r_s = scalar(e.sawlog_volume_ratio(*tree.dhtd))
        if np.isfinite(r_s):
            assert r_1 < r_s < r_m, f"R1={r_1} Rs={r_s} Rm={r_m}"

    @pytest.mark.parametrize("tree", MERCHANTABLE_GRID, ids=ids(MERCHANTABLE_GRID))
    def test_all_biomass_components_are_non_negative(self, tree):
        for name, fn, args in [
            ("wood", e.total_stem_wood_dry_weight_reduced, tree.full[:7]),
            ("bark", e.total_stem_bark_weight_reduced,
             (tree.spcd, tree.dia, tree.ht, tree.division, tree.ah, tree.decaycd)),
            ("branch", e.total_branch_weight_reduced,
             (tree.spcd, tree.dia, tree.ht, tree.division, tree.ah,
              tree.decaycd, tree.cr, tree.province)),
            ("agb", e.agb_predicted_reduced, tree.full),
            ("carbon", e.carbon_content, tree.full),
            ("drybio_top", e.drybio_top, tree.full),
        ]:
            assert scalar(fn(*args)) >= 0.0, f"{name} is negative for {tree.label}"

    # Example 3 tanoak: H=28, S11 default CR=0.378, so the crown base sits at
    # H(1-CR) = 17.42 ft. The publication chose AH=21.0 -- 3.6 ft clear of the
    # sign flip, which is the entire reason the bug survived.
    CROWN_BASE_FT = 28.0 * (1 - 0.378)

    @pytest.mark.parametrize("ah", [28.0, 26.0, 21.0, 17.5])
    def test_branch_remainder_in_unit_interval_above_the_crown_base(self, ah):
        """Above the crown base the formula is well behaved -- pin it so a
        clamp added for the low-break case cannot distort this range."""
        assert ah > self.CROWN_BASE_FT
        crh = CROWN_RATIO_DEFAULTS[("M242", True)]
        rem = scalar(e.branch_remainder(28.0, ah, crh))
        assert 0.0 <= rem <= 1.0, f"BranchRem={rem} at AH={ah}"

    @pytest.mark.parametrize("ah", [17.0, 12.0, 5.0, 1.5])
    def test_branch_remainder_in_unit_interval_below_the_crown_base(self, ah):
        """The Table S11 default-CR path (used for dead broken-top trees,
        GTR p.12) carries no geometric guarantee that AH exceeds the crown
        base -- unlike the observed-CR path, where CRH is derived from AH and
        BranchRem is non-negative by construction."""
        assert ah < self.CROWN_BASE_FT
        crh = CROWN_RATIO_DEFAULTS[("M242", True)]
        rem = scalar(e.branch_remainder(28.0, ah, crh))
        assert 0.0 <= rem <= 1.0, f"BranchRem={rem} at AH={ah}"

    @pytest.mark.parametrize("ah", [59.0, 45.0, 30.0, 10.0, 2.0])
    def test_observed_crown_ratio_path_is_non_negative_by_construction(self, ah):
        """CRH = [H - AH(1-CR)]/H makes H*CRH = H - AH + AH*CR, so
        BranchRem = AH*CR/(H - AH + AH*CR), which is in [0,1] for any
        0 < AH <= H. This is why GTR Example 4 could never have exposed the
        clamp bug, no matter which AH the authors picked."""
        crh = scalar(e.crown_ratio_at_h(65.0, ah, 0.30))
        rem = scalar(e.branch_remainder(65.0, ah, crh))
        assert 0.0 <= rem <= 1.0, f"BranchRem={rem} at AH={ah}"

    def test_low_break_never_produces_negative_biomass(self):
        tree = Tree(TANOAK, 11.3, 28.0, "M240", cull=10.0, ah=5.0,
                    decaycd=2, province="M242")
        assert scalar(e.total_branch_weight_reduced(
            tree.spcd, tree.dia, tree.ht, tree.division, tree.ah,
            tree.decaycd, tree.cr, tree.province)) >= 0.0
        assert scalar(e.agb_predicted_reduced(*tree.full)) >= 0.0

    @pytest.mark.parametrize("tree", MERCHANTABLE_GRID, ids=ids(MERCHANTABLE_GRID))
    def test_reductions_never_increase_biomass_above_the_gross_prediction(self, tree):
        """AGBReduce is a proportional loss factor, so the reduced total can
        never exceed the raw S8 prediction. (Note it *can* exceed the live
        cull-deducted weight: for dead trees the GTR drops the cull deduction
        in favour of the density reduction -- p.25.)"""
        gross = scalar(e.total_aboveground_biomass(*tree.dhtd))
        assert scalar(e.agb_predicted_reduced(*tree.full)) <= gross * (1 + 1e-12)

    @pytest.mark.parametrize("tree", MERCHANTABLE_GRID, ids=ids(MERCHANTABLE_GRID))
    def test_carbon_is_a_plausible_fraction_of_biomass(self, tree):
        agb = scalar(e.agb_predicted_reduced(*tree.full))
        carbon = scalar(e.carbon_content(*tree.full))
        assert 0.3 * agb <= carbon <= 0.7 * agb


# =============================================================================
# Monotonicity
# =============================================================================
class TestMonotonicity:

    @pytest.mark.parametrize("spcd", [DOUGLAS_FIR, WHITE_OAK],
                             ids=["softwood", "hardwood"])
    def test_biomass_decreases_with_advancing_decay(self, spcd):
        """Monotone across DECAYCD 1-5 only. Live (0) is deliberately excluded:
        a live tree carries its cull deduction while a dead tree does not, so
        a decay-1 tree can out-weigh a heavily culled live one (GTR p.25).
        Softwood DensProp also *rises* 0.97 -> 1.00 from class 1 to 2; the
        bark and branch losses more than offset it."""
        vals = [scalar(e.agb_predicted_reduced(spcd, 18.0, 70.0, "", 0.0, None, d))
                for d in range(1, 6)]
        assert all(a >= b for a, b in zip(vals, vals[1:])), vals

    @pytest.mark.parametrize("spcd,expected_dens",
                             [(DOUGLAS_FIR, 0.97), (WHITE_OAK, 0.99)])
    def test_decay_class_1_scales_agb_by_exactly_densprop(self, spcd, expected_dens):
        """An exact analytic check, not an inequality: at DECAYCD=1 both
        BarkProp and BranchProp are 1.0, so every component is scaled by
        DensProp alone and AGBReduce collapses to DensProp."""
        live = scalar(e.agb_predicted_reduced(spcd, 18.0, 70.0, "", 0.0, None, 0))
        dead = scalar(e.agb_predicted_reduced(spcd, 18.0, 70.0, "", 0.0, None, 1))
        np.testing.assert_allclose(dead / live, expected_dens, rtol=1e-12)

    @pytest.mark.parametrize("tree", MERCHANTABLE_GRID, ids=ids(MERCHANTABLE_GRID))
    def test_biomass_increases_with_diameter_and_height(self, tree):
        base = scalar(e.agb_predicted_reduced(*tree.full))
        assert scalar(e.agb_predicted_reduced(*tree.replace(dia=tree.dia * 1.2).full)) > base
        assert scalar(e.agb_predicted_reduced(*tree.replace(ht=tree.ht * 1.2).full)) > base

    def test_a_lower_break_never_leaves_more_biomass(self):
        tree = Tree(WHITE_OAK, 18.1, 65.0, "M220", cull=2.0, cr=0.30,
                    province="M220")
        vals = [scalar(e.agb_predicted_reduced(*tree.replace(ah=ah).full))
                for ah in [64.0, 59.0, 45.0, 30.0, 20.0]]
        assert all(a >= b for a, b in zip(vals, vals[1:])), vals


# =============================================================================
# Every decay class, both species classes
# =============================================================================
class TestDecayClasses:
    """test_examples.py exercises exactly one of table 1's ten rows: ('H', 2)."""

    @pytest.mark.parametrize("decaycd,hardwood",
                             list(itertools.product(range(1, 6), [True, False])))
    def test_dead_tree_reduction_applies_the_published_proportions(
            self, decaycd, hardwood):
        """Reproduce the GTR step 7-9 reductions by hand from table 1 and
        compare against the estimators, for every (class, DECAYCD) row."""
        spcd = WHITE_OAK if hardwood else DOUGLAS_FIR
        dia, ht, division = 16.0, 62.0, ""
        props = WOOD_DENSITY_PROPORTIONS[("H" if hardwood else "S", decaycd)]
        wdsg = float(REF_SPECIES[spcd]["WOOD_SPGR_GREENVOL_DRYWT"])

        expected_wood = (scalar(e.total_inside_bark_wood_volume(spcd, dia, ht, division))
                         * wdsg * props["DensProp"] * 62.4)
        np.testing.assert_allclose(
            scalar(e.total_stem_wood_dry_weight_reduced(
                spcd, dia, ht, division, 0.0, None, decaycd)),
            expected_wood, rtol=1e-12)

        expected_bark = (scalar(e.total_stem_bark_weight(spcd, dia, ht, division))
                         * props["DensProp"] * props["BarkProp"])
        np.testing.assert_allclose(
            scalar(e.total_stem_bark_weight_reduced(
                spcd, dia, ht, division, None, decaycd)),
            expected_bark, rtol=1e-12)

        expected_branch = (scalar(e.total_branch_weight(spcd, dia, ht, division))
                           * props["DensProp"] * props["BranchProp"])
        np.testing.assert_allclose(
            scalar(e.total_branch_weight_reduced(
                spcd, dia, ht, division, None, decaycd)),
            expected_branch, rtol=1e-12)

    @pytest.mark.parametrize("decaycd", range(1, 6))
    def test_foliage_is_zero_for_every_dead_tree(self, decaycd):
        """GTR p.26: 'In the case of dead trees, foliage weight is assumed to
        be zero.'"""
        assert scalar(e.total_foliage_dry_weight_reduced(
            WHITE_OAK, 16.0, 62.0, "", None, decaycd)) == 0.0

    @pytest.mark.parametrize("decaycd,hardwood",
                             list(itertools.product(range(1, 6), [True, False])))
    def test_dead_trees_use_the_s10b_carbon_fraction(self, decaycd, hardwood):
        """Live trees use S10a keyed by SPCD; dead trees use S10b keyed by
        (DECAYCD, hardwood). Getting this wrong is invisible in aggregate."""
        spcd = WHITE_OAK if hardwood else DOUGLAS_FIR
        args = (spcd, 16.0, 62.0, "", 0.0, None, decaycd)
        expected = (scalar(e.agb_predicted_reduced(*args))
                    * CARBON_FRACTION_DEAD[(decaycd, hardwood)])
        np.testing.assert_allclose(scalar(e.carbon_content(*args)),
                                   expected, rtol=1e-12)

    def test_live_trees_use_the_s10a_carbon_fraction(self):
        args = (WHITE_OAK, 16.0, 62.0, "", 0.0, None, 0)
        expected = (scalar(e.agb_predicted_reduced(*args))
                    * CARBON_FRACTION_LIVE[WHITE_OAK])
        np.testing.assert_allclose(scalar(e.carbon_content(*args)),
                                   expected, rtol=1e-12)


# =============================================================================
# Return contracts
# =============================================================================
#
# _check_vector asserts isinstance(result, np.ndarray); _check_scalar asserts
# nothing about type, because assert_allclose accepts float, np.float64, 0-d
# array and 1-element array interchangeably. So the vectorized contract is
# tested and the scalar contract -- the one released v0.2.1 callers depend on
# -- is not.

CONTRACT_FUNCTIONS = [
    ("total_inside_bark_wood_volume", lambda s: e.total_inside_bark_wood_volume(*s.dhtd)),
    ("total_bark_wood_volume", lambda s: e.total_bark_wood_volume(*s.dhtd)),
    ("total_stem_wood_dry_weight", lambda s: e.total_stem_wood_dry_weight(*s.dhtd)),
    ("total_aboveground_biomass", lambda s: e.total_aboveground_biomass(*s.dhtd)),
    ("merchantable_height", lambda s: e.merchantable_height(*s.dhtd)),
    ("stump_volume_ratio", lambda s: e.stump_volume_ratio(*s.dhtd)),
    ("agb_predicted_reduced", lambda s: e.agb_predicted_reduced(*s.full)),
    ("carbon_content", lambda s: e.carbon_content(*s.full)),
    ("drybio_top", lambda s: e.drybio_top(*s.full)),
]


class TestReturnContracts:

    @pytest.mark.parametrize("name,call", CONTRACT_FUNCTIONS,
                             ids=[n for n, _ in CONTRACT_FUNCTIONS])
    def test_scalar_input_returns_a_zero_dimensional_result(self, name, call):
        """Whatever the type, a scalar call must not return something with a
        shape -- that part holds today and is worth pinning."""
        result = call(GRID[0])
        assert np.ndim(result) == 0, f"{name} returned ndim={np.ndim(result)}"

    @pytest.mark.xfail(strict=True, reason="known API inconsistency: scalar "
                                           "calls return a mix of float, "
                                           "np.float64 and 0-d ndarray "
                                           "because np.where leaks out of "
                                           "segmented_model, so the return "
                                           "type depends on which model form "
                                           "the species happens to use")
    def test_scalar_input_returns_a_python_float(self):
        """Released v0.2.1 returned plain floats for scalar input. A 0-d
        ndarray breaks `isinstance(x, float)` and json.dumps in caller code.
        Asserted as one test over all entry points so the failure message
        names every offender at once."""
        offenders = {
            name: type(call(GRID[0])).__name__
            for name, call in CONTRACT_FUNCTIONS
            if not isinstance(call(GRID[0]), float)
        }
        assert not offenders, f"non-float scalar returns: {offenders}"

    @pytest.mark.xfail(strict=True, reason="known API inconsistency: the "
                                           "scalar return type varies with the "
                                           "species' model form")
    def test_scalar_return_type_does_not_depend_on_the_species(self):
        """The sharpest form of the inconsistency: the same function returns
        different types for two different species, because SPCD 202 routes
        through the segmented model (np.where -> 0-d array) and SPCD 631
        through Schumacher-Hall (plain float)."""
        segmented = e.total_inside_bark_wood_volume(202, 20.0, 110.0, "240")
        schumacher = e.total_inside_bark_wood_volume(631, 11.3, 28.0, "M240")
        assert type(segmented) is type(schumacher), (
            f"SPCD 202 -> {type(segmented).__name__}, "
            f"SPCD 631 -> {type(schumacher).__name__}"
        )

    def test_array_input_returns_an_ndarray_of_matching_shape(self):
        n = len(GRID)
        args = (
            np.array([t.spcd for t in GRID]),
            np.array([t.dia for t in GRID]),
            np.array([t.ht for t in GRID]),
            np.array([t.division for t in GRID]),
            np.array([t.cull for t in GRID]),
            np.array([np.nan if t.ah is None else t.ah for t in GRID]),
            np.array([t.decaycd for t in GRID]),
            np.array([np.nan if t.cr is None else t.cr for t in GRID]),
            np.array([t.province for t in GRID]),
        )
        # (spcd, dia, ht, division, cull, ah, decaycd, cr, province). The
        # foliage estimator takes no cull, but its remaining parameters now
        # share the branch ordering, so a plain slice suffices -- before the
        # task #2 fix this call needed a hand-shuffled argument list.
        foliage_args = args[:4] + args[5:]
        for fn in [e.agb_predicted_reduced, e.carbon_content,
                   e.harmonized_wood, e.total_foliage_dry_weight_reduced]:
            call = (fn(*foliage_args)
                    if fn is e.total_foliage_dry_weight_reduced else fn(*args))
            assert isinstance(call, np.ndarray), fn.__name__
            assert call.shape == (n,), f"{fn.__name__}: {call.shape}"

    def test_broken_top_ratio_is_nan_for_an_intact_top(self):
        """Characterises the documented scalar behaviour: no broken top means
        no R_b. (``_broken_top_ratio`` substitutes 1.0 internally; the public
        function reports NaN.)"""
        assert np.isnan(scalar(e.broken_top_volume_ratio(202, 20.0, 110.0, "240", None)))
        assert np.isnan(scalar(e.broken_top_volume_ratio(202, 20.0, 110.0, "240", np.nan)))

    def test_broken_top_ratio_keeps_array_shape_when_ah_is_none(self):
        result = e.broken_top_volume_ratio(
            np.array([202, 316]), np.array([20.0, 11.1]),
            np.array([110.0, 38.0]), np.array(["240", "M210"]), None)
        assert np.shape(result) == (2,), f"collapsed to {np.shape(result)}"

    def test_vectorized_and_scalar_paths_agree(self):
        """The two code paths are written separately; nothing currently
        checks that they produce the same numbers."""
        trees = MERCHANTABLE_GRID
        vec = e.agb_predicted_reduced(
            np.array([t.spcd for t in trees]),
            np.array([t.dia for t in trees]),
            np.array([t.ht for t in trees]),
            np.array([t.division for t in trees]),
            np.array([t.cull for t in trees]),
            np.array([np.nan if t.ah is None else t.ah for t in trees]),
            np.array([t.decaycd for t in trees]),
            np.array([np.nan if t.cr is None else t.cr for t in trees]),
            np.array([t.province for t in trees]),
        )
        one_at_a_time = [scalar(e.agb_predicted_reduced(*t.full)) for t in trees]
        np.testing.assert_allclose(vec, one_at_a_time, rtol=1e-12)


# =============================================================================
# Saplings (1.0 <= D < 5.0)
# =============================================================================
class TestSaplings:
    """GTR p.32: 'It is assumed no merchantable volume is present for
    sapling-sized trees (1.0<=D<5.0); however, total stem wood and bark volume
    components are present. Prediction of biomass (and subsequently carbon)
    for saplings proceeds in the same manner as for larger trees.'

    FIA tallies every tree with D >= 1.0 in, so this is a large share of real
    records, and test_examples.py's smallest tree is D = 11.1 in."""

    @pytest.mark.parametrize("tree", SAPLINGS, ids=ids(SAPLINGS))
    def test_biomass_and_carbon_are_finite(self, tree):
        """The part that already works."""
        for fn in [e.total_inside_bark_wood_volume]:
            assert np.isfinite(scalar(fn(*tree.dhtd)))
        for fn in [e.agb_predicted_reduced, e.carbon_content, e.harmonized_wood]:
            value = scalar(fn(*tree.full))
            assert np.isfinite(value) and value > 0, fn.__name__

    @pytest.mark.parametrize("tree", SAPLINGS, ids=ids(SAPLINGS))
    def test_merchantable_height_is_undefined(self, tree):
        """Correct as-is: there is no merchantable top on a sapling."""
        assert np.isnan(scalar(e.merchantable_height(*tree.dhtd)))

    @pytest.mark.parametrize("tree", SAPLINGS, ids=ids(SAPLINGS))
    def test_sound_volumes_and_top_biomass_are_finite(self, tree):
        assert np.isfinite(scalar(e.total_inside_bark_wood_volume_sound(*tree.full[:7])))
        assert np.isfinite(scalar(e.drybio_top(*tree.full)))

    @pytest.mark.parametrize("tree", SAPLINGS, ids=ids(SAPLINGS))
    def test_merchantable_weight_is_zero_not_nan(self, tree):
        assert scalar(e.merchantable_outside_bark_weight(*tree.full)) == 0.0

    @pytest.mark.parametrize("tree", SAPLINGS, ids=ids(SAPLINGS))
    def test_additivity_holds_for_saplings(self, tree):
        total = (scalar(e.merchantable_outside_bark_weight(*tree.full))
                 + scalar(e.stump_outside_bark_weight(*tree.full))
                 + scalar(e.drybio_top(*tree.full)))
        np.testing.assert_allclose(total, scalar(e.agb_predicted_reduced(*tree.full)),
                                   rtol=1e-12)

    @pytest.mark.parametrize("tree", SAPLINGS, ids=ids(SAPLINGS))
    def test_gross_merchantable_volume_is_zero_and_the_stem_still_partitions(self, tree):
        """The gross (step 6) volumes must agree with the sound ones about
        there being no bole, and stump + top must still recover the total."""
        assert scalar(e.merchantable_inside_bark_volume(*tree.dhtd)) == 0.0
        assert scalar(e.merchantable_bark_volume(*tree.dhtd)) == 0.0
        np.testing.assert_allclose(
            scalar(e.stump_inside_bark_volume(*tree.dhtd))
            + scalar(e.top_inside_bark_volume(*tree.dhtd)),
            scalar(e.total_inside_bark_wood_volume(*tree.dhtd)), rtol=1e-12)

    @pytest.mark.parametrize("tree", SAPLINGS, ids=ids(SAPLINGS))
    def test_drybio_top_is_agb_less_the_stump(self, tree):
        """With no bole, all non-stump biomass is top-and-limbs."""
        np.testing.assert_allclose(
            scalar(e.drybio_top(*tree.full)),
            scalar(e.agb_predicted_reduced(*tree.full))
            - scalar(e.stump_outside_bark_weight(*tree.full)), rtol=1e-12)

    def test_biomass_and_carbon_are_continuous_across_the_sapling_threshold(self):
        """GTR p.38 lists "consistent modeling results for all trees having a
        diameter at breast height >= 1.0 inch" as a headline property, and
        contrasts NSVB with the CRM's "ad hoc adjustment factor for saplings to
        help smooth predictions for trees crossing the D = 5.0-inch threshold".

        AGB and carbon never reference R_m, so they must cross D=5.0 smoothly.
        Compared against local allometric growth rather than an absolute
        tolerance, so ordinary size trend is not mistaken for a step."""
        def agb(dia):
            return scalar(e.agb_predicted_reduced(202, dia, 25.0, "240"))

        step_below = agb(4.99) - agb(4.98)      # trend just below the boundary
        step_across = agb(5.00) - agb(4.99)     # the step that spans it
        assert step_across == pytest.approx(step_below, rel=0.05), (
            f"AGB steps {step_across} across D=5.0 vs {step_below} just below"
        )

    def test_the_bole_top_split_is_discontinuous_by_definition(self):
        """The counterpart: DRYBIO_TOP *does* jump at D=5.0, because the GTR
        declares saplings to have no merchantable portion, so the bole appears
        all at once. Pinned deliberately -- this is the publication's rule, and
        a future 'smoothing' fix here would be a departure from the GTR, not a
        bug fix."""
        below = scalar(e.drybio_top(202, 4.99, 25.0, "240"))
        above = scalar(e.drybio_top(202, 5.00, 25.0, "240"))
        assert scalar(e.merchantable_outside_bark_weight(202, 4.99, 25.0, "240")) == 0.0
        assert scalar(e.merchantable_outside_bark_weight(202, 5.00, 25.0, "240")) > 0.0
        assert below > above * 1.2, (
            f"expected DRYBIO_TOP to drop sharply once the bole exists: "
            f"{below} -> {above}"
        )


# =============================================================================
# Sawlog weights (FIADB DRYBIO_SAWLOG)
# =============================================================================
class TestSawlogWeights:
    """The GTR computes sawlog volumes in all four examples but never converts
    them to weight, so there is no published number to check against. These
    tests pin the conversion against the merchantable bole, which the GTR does
    specify (Example 4, p.25), and against the containment relationships that
    make the sawlog a sub-portion of the stem."""

    SAWTIMBER = [t for t in MERCHANTABLE_GRID
                 if t.dia >= (11.0 if t.spcd >= 300 else 9.0)]

    @pytest.mark.parametrize("tree", SAWTIMBER, ids=ids(SAWTIMBER))
    def test_sawlog_is_contained_in_the_bole_and_the_tree(self, tree):
        """1-ft stump to a 7/9-inch top is inside 1-ft stump to a 4-inch top,
        which is inside the whole tree."""
        sawlog = scalar(e.sawlog_outside_bark_weight(*tree.full))
        bole = scalar(e.merchantable_outside_bark_weight(*tree.full))
        agb = scalar(e.agb_predicted_reduced(*tree.full))
        assert 0 < sawlog <= bole <= agb

    @pytest.mark.parametrize("tree", SAWTIMBER, ids=ids(SAWTIMBER))
    def test_sawlog_weight_uses_the_harmonized_adjusted_density(self, tree):
        """Same conversion the GTR states for the bole in Example 4:
        volume basis x adjusted density x 62.4. Using the raw WDSG instead
        would break consistency with the harmonized totals."""
        density = scalar(e.adjusted_wood_density(*tree.full))
        basis = scalar(e._v_saw_ib_basis(tree.spcd, tree.dia, tree.ht,
                                         tree.division, tree.ah))
        np.testing.assert_allclose(scalar(e.sawlog_wood_weight(*tree.full)),
                                   basis * density * 62.4, rtol=1e-12)

    @pytest.mark.parametrize("tree", SAWTIMBER, ids=ids(SAWTIMBER))
    def test_sawlog_outside_bark_is_wood_plus_bark(self, tree):
        np.testing.assert_allclose(
            scalar(e.sawlog_outside_bark_weight(*tree.full)),
            scalar(e.sawlog_wood_weight(*tree.full))
            + scalar(e.sawlog_bark_weight(*tree.full)), rtol=1e-12)

    @pytest.mark.parametrize("spcd,dia,defined", [
        (DOUGLAS_FIR, 8.0, False), (DOUGLAS_FIR, 9.5, True),
        (WHITE_OAK, 10.0, False), (WHITE_OAK, 12.0, True),
    ], ids=["swd-below", "swd-above", "hwd-below", "hwd-above"])
    def test_sub_sawtimber_trees_are_undefined_not_zero(self, spcd, dia, defined):
        """NaN rather than 0, matching FIADB (DRYBIO_SAWLOG is NULL for
        non-sawtimber trees) and unlike the sapling bole rule, where the GTR
        explicitly states no merchantable volume is present."""
        weight = scalar(e.sawlog_outside_bark_weight(spcd, dia, 55.0, ""))
        assert np.isfinite(weight) if defined else np.isnan(weight)

    def test_a_break_below_the_sawlog_height_truncates_the_sawlog(self):
        """Above h_s the sawlog portion is intact; below it the sawlog is
        shortened along with the stem."""
        args = (WHITE_OAK, 18.1, 65.0, "M220")
        h_s = scalar(e.sawlog_height(*args))
        def weight(ah):
            return scalar(e.sawlog_outside_bark_weight(
                *args, 0.0, ah, 0, 0.30, "M220"))
        intact = weight(None)
        np.testing.assert_allclose(weight(h_s + 5.0), intact, rtol=1e-12)
        assert weight(h_s - 10.0) < intact
        assert weight(h_s - 20.0) < weight(h_s - 10.0)

    @pytest.mark.parametrize("tree", SAWTIMBER, ids=ids(SAWTIMBER))
    def test_sawlog_sound_volumes_are_additive_and_cull_deducted(self, tree):
        args = tree.full[:7]
        ib = scalar(e.sawlog_inside_bark_volume_sound(*args))
        bk = scalar(e.sawlog_bark_volume_sound(*args))
        np.testing.assert_allclose(
            scalar(e.sawlog_outside_bark_volume_sound(*args)), ib + bk, rtol=1e-12)
        # Cull deducts from wood only, never from bark.
        gross_ib = scalar(e.sawlog_inside_bark_volume_sound(
            tree.spcd, tree.dia, tree.ht, tree.division, 0.0, tree.ah, tree.decaycd))
        np.testing.assert_allclose(ib, gross_ib * (1 - tree.cull / 100), rtol=1e-12)
        np.testing.assert_allclose(bk, scalar(e.sawlog_bark_volume_sound(
            tree.spcd, tree.dia, tree.ht, tree.division, 0.0, tree.ah, tree.decaycd)),
            rtol=1e-12)

    def test_missing_decay_class_is_live_for_a_scalar_none(self):
        """FIADB leaves DECAYCD NULL for live trees; None must not reach the
        int cast."""
        np.testing.assert_allclose(
            scalar(e.agb_predicted_reduced(WHITE_OAK, 18.1, 65.0, "M220",
                                           0.0, None, None)),
            scalar(e.agb_predicted_reduced(WHITE_OAK, 18.1, 65.0, "M220",
                                           0.0, None, 0)), rtol=1e-12)

    def test_sawlog_volume_and_weight_agree_on_stand_origin(self):
        """The new estimators must honour stdorgcd like every other one."""
        args = (131, 20.0, 95.0, "230")
        natural = scalar(e.sawlog_outside_bark_weight(*args, stdorgcd=0))
        planted = scalar(e.sawlog_outside_bark_weight(*args, stdorgcd=1))
        assert natural != planted


# =============================================================================
# Cross-function consistency
# =============================================================================
class TestCrossFunctionConsistency:

    @pytest.mark.parametrize("tree", [t for t in MERCHANTABLE_GRID
                                      if t.cull == 0 and t.ah is None and t.decaycd == 0],
                             ids=lambda t: t.label)
    def test_reduced_equals_gross_when_there_is_nothing_to_reduce(self, tree):
        """A live, intact, cull-free tree must come back untouched through the
        reduction machinery (GTR Example 1 makes this point explicitly)."""
        np.testing.assert_allclose(
            scalar(e.total_stem_wood_dry_weight_reduced(*tree.full[:7])),
            scalar(e.total_stem_wood_dry_weight(*tree.dhtd)), rtol=1e-12)
        np.testing.assert_allclose(
            scalar(e.total_stem_bark_weight_reduced(
                tree.spcd, tree.dia, tree.ht, tree.division, None, 0)),
            scalar(e.total_stem_bark_weight(*tree.dhtd)), rtol=1e-12)
        np.testing.assert_allclose(
            scalar(e.agb_predicted_reduced(*tree.full)),
            scalar(e.total_aboveground_biomass(*tree.dhtd)), rtol=1e-12)

    # Species classed 'S' by FIA despite SPCD >= 300. GTR p.8 defines the
    # split by species code, so every SPCD-keyed lookup must agree with the
    # threshold rather than with REF_SPECIES.SFTWD_HRDWD.
    MISCLASSIFIED = [6156, 8183, 5420, 6786, 8738]

    @pytest.mark.parametrize("spcd", MISCLASSIFIED)
    def test_every_hardwood_lookup_agrees_on_the_gtr_classification(self, spcd):
        """The cull DensProp, the dead-tree table 1 row, the dead carbon
        fraction and the sawlog top diameter are four independent lookups that
        each need a hardwood/softwood answer. They must not disagree."""
        from nsvb.tables import HARDWOOD_SPCD_THRESHOLD, is_hardwood
        assert spcd >= HARDWOOD_SPCD_THRESHOLD and is_hardwood(spcd)
        assert REF_SPECIES[spcd]["SFTWD_HRDWD"] == "S"  # the disagreement

        # Cull DensProp: hardwood row of table 1 at DECAYCD 3 is 0.54.
        assert scalar(e._live_cull_dens_prop(spcd)) == 0.54
        # Table 1 dead-tree proportions: hardwood DECAYCD 2 is (0.80, 0.8, 0.5).
        dens, bark, branch = (scalar(x) for x in e._dead_props(spcd, 2))
        assert (dens, bark, branch) == (0.80, 0.8, 0.5)
        # S10b dead carbon fraction resolves to the hardwood row.
        assert (scalar(e._carbon_fraction(spcd, 2))
                == CARBON_FRACTION_DEAD[(2, True)])
        # Sawlog top diameter: 9 in for hardwoods, so h_s < the 7-in softwood
        # height would be. Just check it resolves against the hardwood
        # minimum DBH of 11.0 in rather than the softwood 9.0 in.
        assert np.isnan(scalar(e.sawlog_height(spcd, 10.0, 60.0, "")))
        assert np.isfinite(scalar(e.sawlog_height(spcd, 12.0, 60.0, "")))

    def test_segmentation_point_is_keyed_off_spcd_not_the_fia_class(self):
        """tables.py builds ``k`` at import time; this is the loader-side half
        of the same rule the estimators use."""
        from nsvb.tables import segmentation_point
        assert segmentation_point(202) == 9.0     # softwood
        assert segmentation_point(802) == 11.0    # hardwood
        assert segmentation_point(6156) == 11.0   # SPCD >= 300, FIA says 'S'

    def test_gross_stem_wood_weight_takes_no_deductions(self):
        """Wtotib is the gross quantity (GTR Example 1). The ``cull`` argument
        was removed because it duplicated Wtotibred under the Wtotib name and
        disagreed with it for the misclassified species above."""
        params = inspect.signature(e.total_stem_wood_dry_weight).parameters
        assert "cull" not in params
        assert list(params) == ["spcd", "dia", "ht", "division", "stdorgcd"]
        assert params["stdorgcd"].kind is inspect.Parameter.KEYWORD_ONLY
        expected = (scalar(e.total_inside_bark_wood_volume(802, 18.0, 70.0, ""))
                    * float(REF_SPECIES[802]["WOOD_SPGR_GREENVOL_DRYWT"]) * 62.4)
        np.testing.assert_allclose(
            scalar(e.total_stem_wood_dry_weight(802, 18.0, 70.0, "")),
            expected, rtol=1e-12)

    def test_step_14_uses_the_gross_volume_basis_from_gtr_example_4(self):
        """GTR Example 4 (p.25) states Step 14 explicitly, in prose and
        arithmetic: "Wmerib = VmeribGross x WDSGAdj x 62.4" and
        "Wstumpib = VstumpibGross x WDSGAdj x 62.4".

        Worth its own test because *additivity cannot detect this*. Example 3's
        prose defines Wmerib by subtraction from the cull-grossed total, so its
        components telescope to WoodHarmonized just as these do -- the two
        readings differ only in how they allocate mass between bole, stump and
        top once CULL > 0. Exercised on a dead, culled, broken-top tree, where
        the gap is widest (~7.4 lb on the bole for this tree).
        """
        spcd, dia, ht, division, cull, ah = 802, 18.1, 65.0, "M220", 10.0, 59.0
        full = (spcd, dia, ht, division, cull, ah, 2, 0.30, "M220")
        assert scalar(e.merchantable_height(spcd, dia, ht, division)) < ah

        v = scalar(e.total_inside_bark_wood_volume(spcd, dia, ht, division))
        r_1 = scalar(e.stump_volume_ratio(spcd, dia, ht, division))
        r_m = scalar(e.merchantable_volume_ratio(spcd, dia, ht, division))
        density = scalar(e.adjusted_wood_density(*full)) * 62.4

        # Example 4's rule, spelled out with no reference to the code's helpers.
        np.testing.assert_allclose(scalar(e.merchantable_wood_weight(*full)),
                                   (r_m - r_1) * v * density, rtol=1e-12)
        np.testing.assert_allclose(scalar(e.stump_wood_weight(*full)),
                                   r_1 * v * density, rtol=1e-12)

        # And confirm the discarded reading really is different here, so this
        # test would fail if the basis were ever switched to it.
        literal_stump = r_1 * v * (1 - cull / 100) * density
        assert abs(literal_stump - scalar(e.stump_wood_weight(*full))) > 1.0

    def test_foliage_and_branch_share_the_same_broken_top_geometry(self):
        """GTR uses one geometric proportion for both (BranchRem == FoliageRem).
        Called with matching keyword arguments so the transposed positional
        signatures (task #2) cannot mask a real divergence."""
        common = dict(spcd=WHITE_OAK, dia=18.1, ht=65.0, division="M220",
                      ah=59.0, cr=0.30, province="M220")
        branch_ratio = (
            scalar(e.total_branch_weight_reduced(decaycd=0, **common))
            / scalar(e.total_branch_weight(WHITE_OAK, 18.1, 65.0, "M220")))
        foliage_ratio = (
            scalar(e.total_foliage_dry_weight_reduced(decaycd=0, **common))
            / scalar(e.total_foliage_dry_weight(WHITE_OAK, 18.1, 65.0, "M220")))
        np.testing.assert_allclose(branch_ratio, foliage_ratio, rtol=1e-12)

    def test_reduced_estimators_share_a_parameter_ordering(self):
        """Before this was fixed, a positional call written from the branch
        signature silently returned 0.0 from the foliage one -- cr=0 read as
        live, decaycd=0.30 truncated to 0. No exception, just a wrong number.

        Checked across every reduced/harmonized estimator, not just the two
        that diverged, so a new one cannot be added with a fresh ordering."""
        def tail(fn):
            return [p for p in inspect.signature(fn).parameters
                    if p in ("cull", "ah", "decaycd", "cr", "province")]

        reference = tail(e.agb_predicted_reduced)
        assert reference == ["cull", "ah", "decaycd", "cr", "province"]
        for fn in [e.total_stem_wood_dry_weight_reduced,
                   e.total_stem_bark_weight_reduced,
                   e.total_branch_weight_reduced,
                   e.total_foliage_dry_weight_reduced,
                   e.agb_component_reduced, e.agb_reduce_factor,
                   e.harmonized_wood, e.harmonized_bark, e.harmonized_branch,
                   e.adjusted_wood_density, e.adjusted_bark_density,
                   e.merchantable_wood_weight, e.stump_wood_weight,
                   e.drybio_top, e.carbon_content]:
            observed = tail(fn)
            assert observed == [p for p in reference if p in observed], (
                f"{fn.__name__} orders its optional parameters {observed}, "
                f"which is not a subsequence of {reference}"
            )


# =============================================================================
# Input validation
# =============================================================================
class TestInputValidation:
    """1,034 lines of test_examples.py contain no invalid input at all, which
    is why a DECAYCD of 6 currently surfaces as ``KeyError: ('H', 6)``."""

    LIVE = (WHITE_OAK, 18.1, 65.0, "M220")

    @pytest.mark.parametrize("decaycd", [6, 99, -1, 2.5])
    def test_invalid_decay_class_raises_a_clear_error(self, decaycd):
        with pytest.raises(ValueError, match="(?i)decay"):
            e.agb_predicted_reduced(*self.LIVE, 0.0, None, decaycd)

    def test_broken_top_above_total_height_raises_a_clear_error(self):
        with pytest.raises(ValueError, match="(?i)(height|ah)"):
            e.agb_predicted_reduced(*self.LIVE, 0.0, 80.0, 0)

    @pytest.mark.parametrize("ah", [0.99, 0.5, 0.0])
    def test_broken_top_below_the_stump_raises_a_clear_error(self, ah):
        """Below the 1-ft stump R_b < R_1, which drives the merchantable
        volume basis negative. Additivity does not catch it -- the
        R_eff_mer + R_eff_top == R_b identity still holds -- so it needs an
        explicit guard."""
        with pytest.raises(ValueError, match="(?i)(stump|ah)"):
            e.agb_predicted_reduced(*self.LIVE, 0.0, ah, 0)

    @pytest.mark.parametrize("cr", [30.0, 1.5, 0.0, -0.2])
    def test_crown_ratio_outside_the_unit_interval_raises(self, cr):
        """cr is a decimal fraction while cull is a percentage, so passing
        cr=30 for "30 percent" is the obvious mistake to make."""
        with pytest.raises(ValueError, match="(?i)crown ratio"):
            e.total_branch_weight_reduced(WHITE_OAK, 18.1, 65.0, "M220",
                                          59.0, 0, cr, "M220")

    def test_missing_measurements_propagate_as_nan_rather_than_raising(self):
        """A batch with unrecorded heights should yield NaN for those rows,
        not abort the whole array -- otherwise validation is unusable on real
        FIA extracts."""
        result = e.agb_predicted_reduced(
            np.array([202, 202]), np.array([20.0, 20.0]),
            np.array([110.0, np.nan]), np.array(["240", "240"]))
        assert np.isfinite(result[0]) and np.isnan(result[1])

    @pytest.mark.parametrize("param,bad,pattern", [
        ("dia", -5.0, "diameter"), ("ht", 0.0, "height"),
        ("cull", 120.0, "cull"), ("cr", 30.0, "crown ratio"),
        ("decaycd", 7, "decay"), ("spcd", 99999, "species"),
    ])
    def test_scalar_and_array_validation_agree(self, param, bad, pattern):
        """The scalar fast path exists purely for speed, so it must reject
        exactly what the array path rejects and say the same thing."""
        base = dict(spcd=WHITE_OAK, dia=18.1, ht=65.0, division="M220",
                    cull=0.0, ah=None, decaycd=0, cr=None, province="M220")
        order = ("spcd", "dia", "ht", "division", "cull", "ah", "decaycd",
                 "cr", "province")

        scalar_args = dict(base, **{param: bad})
        with pytest.raises(ValueError, match=f"(?i){pattern}"):
            e.agb_predicted_reduced(*[scalar_args[k] for k in order])

        array_args = dict(base)
        array_args[param] = np.array([bad, bad])
        for key in ("spcd", "dia", "ht", "division"):
            if key != param:
                array_args[key] = np.array([base[key], base[key]])
        with pytest.raises(ValueError, match=f"(?i){pattern}"):
            e.agb_predicted_reduced(*[array_args[k] for k in order])

    def test_a_valid_batch_is_never_rejected(self):
        """Guard against the checks being too strict: every tree in the
        property grid, plus the four GTR examples, must pass."""
        for tree in GRID + SAPLINGS:
            assert np.isfinite(scalar(e.agb_predicted_reduced(*tree.full)))

    def test_validation_runs_once_not_at_every_nested_frame(self):
        """carbon_content composes about ten estimator calls deep. Validation
        is suppressed below the outermost frame; if that regressed, the checks
        would run ten times per tree."""
        from nsvb import validation
        calls = []
        original = validation.check_dia
        validation.check_dia = lambda v: calls.append(v)
        validation._CHECKERS["dia"] = validation.check_dia
        try:
            e.carbon_content(WHITE_OAK, 18.1, 65.0, "M220")
        finally:
            validation.check_dia = original
            validation._CHECKERS["dia"] = original
        assert len(calls) == 1, f"dia validated {len(calls)} times"

    def test_array_broken_top_heights_are_range_checked(self):
        """check_ah's array branch, which the scalar fast path bypasses."""
        spcd, dia, ht, div = (np.full(2, WHITE_OAK), np.full(2, 18.1),
                              np.full(2, 65.0), np.full(2, "M220"))
        with pytest.raises(ValueError, match="(?i)exceed total height"):
            e.agb_predicted_reduced(spcd, dia, ht, div, np.zeros(2),
                                    np.array([59.0, 80.0]), np.zeros(2, dtype=int))
        with pytest.raises(ValueError, match="(?i)stump height"):
            e.agb_predicted_reduced(spcd, dia, ht, div, np.zeros(2),
                                    np.array([59.0, 0.5]), np.zeros(2, dtype=int))

    def test_array_decay_classes_are_range_checked(self):
        spcd, dia, ht, div = (np.full(2, WHITE_OAK), np.full(2, 18.1),
                              np.full(2, 65.0), np.full(2, "M220"))
        with pytest.raises(ValueError, match="(?i)decay"):
            e.agb_predicted_reduced(spcd, dia, ht, div, np.zeros(2),
                                    np.full(2, np.nan), np.array([0, 9]))
        # FIADB leaves DECAYCD NULL for live trees, so a missing decay class
        # means live -- not invalid, and not a silently-garbage int cast.
        missing = e.agb_predicted_reduced(spcd, dia, ht, div, np.zeros(2),
                                          np.full(2, np.nan), np.full(2, np.nan))
        live = e.agb_predicted_reduced(spcd, dia, ht, div, np.zeros(2),
                                       np.full(2, np.nan), np.zeros(2, dtype=int))
        np.testing.assert_allclose(missing, live, rtol=1e-12)

    def test_too_many_positional_arguments_is_a_type_error(self):
        with pytest.raises(TypeError, match="positional"):
            e.total_inside_bark_wood_volume(WHITE_OAK, 18.1, 65.0, "M220", 1, 2, 3)

    def test_non_numeric_stand_origin_is_rejected(self):
        with pytest.raises(ValueError, match="stdorgcd"):
            e.total_inside_bark_wood_volume(WHITE_OAK, 18.1, 65.0, "M220",
                                            stdorgcd=object())

    def test_validation_reports_against_the_function_the_caller_named(self):
        """Estimators compose about ten frames deep; the error should not
        surface from an internal helper."""
        with pytest.raises(ValueError) as excinfo:
            e.carbon_content(WHITE_OAK, -1.0, 65.0, "M220")
        assert "diameter" in str(excinfo.value)

    @pytest.mark.parametrize("dia", [-5.0, 0.0])
    def test_non_positive_diameter_raises_a_clear_error(self, dia):
        with pytest.raises(ValueError, match="(?i)diameter"):
            e.total_inside_bark_wood_volume(WHITE_OAK, dia, 65.0, "M220")

    @pytest.mark.parametrize("cull", [-1.0, 120.0])
    def test_cull_outside_0_100_raises_a_clear_error(self, cull):
        with pytest.raises(ValueError, match="(?i)cull"):
            e.total_inside_bark_wood_volume_sound(*self.LIVE, cull)

    def test_unknown_species_code_raises_a_clear_error(self):
        with pytest.raises(ValueError, match="(?i)(species|spcd)"):
            e.total_inside_bark_wood_volume(99999, 18.1, 65.0, "M220")

    def test_list_input_is_accepted_as_advertised(self):
        result = e.total_inside_bark_wood_volume(
            [202, 316], [20.0, 11.1], [110.0, 38.0], ["240", "M210"])
        assert np.shape(result) == (2,)

    def test_array_cull_with_scalar_species_is_accepted(self):
        """Was a task #8 xfail against the gross function's ``if cull > 0``
        scalar path; removing that argument in task #4 deleted the failure
        mode. The reduced variant is now the only cull entry point and has
        always broadcast correctly."""
        result = e.total_stem_wood_dry_weight_reduced(
            202, 20.0, 110.0, "240", np.array([0.0, 3.0]))
        assert np.shape(result) == (2,)
        np.testing.assert_allclose(
            result[0], scalar(e.total_stem_wood_dry_weight(202, 20.0, 110.0, "240")),
            rtol=1e-12)


# =============================================================================
# The Table S11 province lookup
# =============================================================================
class TestProvinceResolution:
    """The most error-prone argument in the API: `province` sits beside
    `division`, is silently absorbed when confused with it, and only matters
    for dead broken-top trees -- the case with no independent sanity check."""

    TANOAK_ARGS = dict(spcd=TANOAK, dia=11.3, ht=28.0, division="M240",
                       ah=21.0, decaycd=2, cr=None)

    def test_correct_province_reproduces_the_gtr_example(self):
        got = scalar(e.total_branch_weight_reduced(province="M242", **self.TANOAK_ARGS))
        np.testing.assert_allclose(got, 30.718374921312, rtol=1e-6)

    def test_division_and_province_give_materially_different_answers(self):
        """Pins the size of the blast radius so a future 'harmless' change to
        the fallback cannot quietly shift results."""
        correct = scalar(e.total_branch_weight_reduced(province="M242", **self.TANOAK_ARGS))
        as_division = scalar(e.total_branch_weight_reduced(province="M240", **self.TANOAK_ARGS))
        omitted = scalar(e.total_branch_weight_reduced(province="", **self.TANOAK_ARGS))
        assert abs(as_division - correct) / correct > 0.20
        assert omitted != correct

    def test_passing_a_division_as_a_province_warns(self):
        with pytest.warns(UserWarning, match="(?i)division"):
            e.total_branch_weight_reduced(province="M240", **self.TANOAK_ARGS)

    def test_missing_province_warns(self):
        with pytest.warns(UserWarning, match="(?i)UNDEFINED"):
            e.total_branch_weight_reduced(province="", **self.TANOAK_ARGS)

    def test_correct_province_is_silent(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            e.total_branch_weight_reduced(province="M242", **self.TANOAK_ARGS)

    @pytest.mark.parametrize("kwargs,label", [
        (dict(ah=None, cr=None), "intact top never consults S11"),
        (dict(ah=21.0, cr=0.40), "observed crown ratio bypasses S11"),
    ], ids=["intact-top", "observed-cr"])
    def test_no_warning_when_the_s11_default_is_not_consulted(self, kwargs, label):
        """The lookup only runs for broken-top trees with no observed crown
        ratio. Warning on any other tree would fire on essentially every
        batch and train users to ignore it."""
        args = dict(self.TANOAK_ARGS, province="", **kwargs)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            e.total_branch_weight_reduced(**args)

    def test_warning_is_raised_once_per_call_not_once_per_tree(self):
        """A vectorized run over a large batch must not emit one warning per
        row."""
        n = 500
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            e.total_branch_weight_reduced(
                np.full(n, TANOAK), np.full(n, 11.3), np.full(n, 28.0),
                np.full(n, "M240"), np.full(n, 21.0), np.full(n, 2),
                np.full(n, np.nan), np.full(n, "M240"))
        assert len(caught) == 1, f"{len(caught)} warnings for {n} trees"

    def test_mixed_batch_warns_only_about_the_trees_that_consult_s11(self):
        """Intact-top trees carrying an empty province must not trigger the
        UNDEFINED warning just by sharing an array with a broken-top tree."""
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            e.total_branch_weight_reduced(
                np.array([DOUGLAS_FIR, RED_MAPLE, TANOAK]),
                np.array([20.0, 11.1, 11.3]), np.array([110.0, 38.0, 28.0]),
                np.array(["240", "M210", "M240"]),
                np.array([np.nan, np.nan, 21.0]), np.array([0, 0, 2]),
                np.array([np.nan, np.nan, np.nan]),
                np.array(["", "", "M242"]))
