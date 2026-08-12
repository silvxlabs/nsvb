# nsvb

National Scale Volume and Biomass Estimators — a Python implementation of
Westfall et al. (2024), *A national-scale tree volume, biomass, and carbon
modeling system for the United States*, USDA Forest Service GTR WO-104
([doi:10.2737/WO-GTR-104](https://doi.org/10.2737/WO-GTR-104)).

Every estimator is validated against the four worked examples in the GTR's
"Examples of Tree-Level Calculations" section, to the 12 decimal places the
publication prints.

## Installation

```bash
pip install nsvb
```

## Quick start

```python
from nsvb import estimators

# A live Douglas-fir, 20 in DBH, 110 ft tall, in the Marine ecodivision.
estimators.total_aboveground_biomass(202, 20.0, 110.0, "240")   # 3154.55 lb
estimators.carbon_content(202, 20.0, 110.0, "240")              # 1626.47 lb C
```

The first four arguments are always `spcd`, `dia`, `ht`, `division`:

| argument | meaning | units |
|---|---|---|
| `spcd` | FIA species code (FIADB `REF_SPECIES`) | — |
| `dia` | diameter at breast height | inches |
| `ht` | total height | feet |
| `division` | Cleland ecodivision code, e.g. `"240"`, `"M220"` | — |

Everything else is optional and describes deductions:

| argument | meaning | default |
|---|---|---|
| `cull` | rotten/missing cull, as a **percentage** (0–100) | `0` |
| `ah` | actual height of a broken top; `None` if intact | `None` |
| `decaycd` | FIA decay class: `0`/`None` = live, `1`–`5` = standing dead | `0` |
| `cr` | observed crown ratio, as a **decimal fraction** (0–1] | `None` |
| `province` | Cleland ecoprovince, for the Table S11 default crown ratio | `""` |
| `stdorgcd` | stand origin: `0` natural, `1` planted (keyword-only) | `0` |

> `cull` is a percentage and `cr` is a fraction — a 30 percent crown ratio is
> `cr=0.30`, not `cr=30`. Passing `cr=30` raises.

## Dead trees and decay class

Dead-tree reduction is applied through `decaycd`. Following GTR table 1, the
stem wood is scaled by a wood density proportion, bark and branches by further
proportions, and foliage is zero for any dead tree. Dead trees also use a
different carbon fraction (table S10b, by decay class) than live trees
(table S10a, by species).

```python
# A dead tanoak, decay class 2, 10% cull, broken top at 21 ft.
estimators.agb_predicted_reduced(
    631, 11.3, 28.0, "M240", cull=10.0, ah=21.0, decaycd=2, province="M242",
)                                                               # 241.97 lb
estimators.carbon_content(
    631, 11.3, 28.0, "M240", cull=10.0, ah=21.0, decaycd=2, province="M242",
)                                                               # 114.45 lb C
```

FIADB populates `DECAYCD` only for standing dead trees, so live trees arrive
as `NULL`. `decaycd=None` and `decaycd=NaN` are both treated as live.

### Broken tops and `province`

For a broken-top tree the remaining branch and foliage mass depends on the
crown ratio. If you observed one, pass `cr`. If you did not, the estimator
falls back to the Table S11 regional mean, which is keyed by **ecoprovince**
(e.g. `"M242"`), not ecodivision (`"M240"`). Passing a division where a
province is expected still returns a number, but a different one — up to about
27 percent on branch biomass — so the package warns rather than resolving it
silently. Omitting `province` falls back to a national mean and warns too.

## Gross vs. reduced

Bare names are the **gross** model prediction with no deductions; the
`_reduced` and `_sound` suffixes carry the cull, dead-tree and broken-top
reductions. The gross forms are not just a convenience — `agb_reduce_factor`
needs them undeducted for its denominator.

```python
estimators.total_stem_wood_dry_weight(...)          # Wtotib   (gross)
estimators.total_stem_wood_dry_weight_reduced(...)  # Wtotibred
```

## What's available

Roughly following the GTR's numbered steps:

| | functions |
|---|---|
| Volumes (steps 1–3, 6) | `total_inside_bark_wood_volume`, `total_bark_wood_volume`, `total_outside_bark_volume`, and `merchantable_*`, `sawlog_*`, `stump_*`, `top_*`, `missing_*` variants, each with a `_sound` counterpart |
| Heights and ratios (steps 4–5) | `merchantable_height`, `sawlog_height`, `stump_volume_ratio`, `merchantable_volume_ratio`, `sawlog_volume_ratio`, `broken_top_volume_ratio` |
| Component weights (steps 7–9, 15) | `total_stem_wood_dry_weight`, `total_stem_bark_weight`, `total_branch_weight`, `total_foliage_dry_weight`, plus `_reduced` variants |
| Harmonization (steps 10–13) | `total_aboveground_biomass`, `agb_component_reduced`, `agb_reduce_factor`, `agb_predicted_reduced`, `agb_difference`, `harmonized_wood`/`_bark`/`_branch`, `adjusted_wood_density`, `adjusted_bark_density` |
| FIADB components (steps 14, 16) | `merchantable_outside_bark_weight` (`DRYBIO_BOLE`), `sawlog_outside_bark_weight` (`DRYBIO_SAWLOG`), `stump_outside_bark_weight` (`DRYBIO_STUMP`), `drybio_top` (`DRYBIO_TOP`) |
| Carbon (step 17) | `carbon_content` |

### Not implemented

**Belowground coarse-root biomass.** The GTR describes it in a single sentence
(p. 11) — the approach of Heath et al. (2009), modified to use NSVB
merchantable stem wood volume and the table 1 density proportions for standing
dead trees — but publishes no equation, no coefficients (there is no
belowground table among S1–S20), and no worked example. Implementing it needs
the Heath et al. (2009) method, and substituting a different published root
model would not be the NSVB quantity. Note that FIADB `REF_SPECIES` ships
`JENKINS_ROOT_RATIO_B1`/`B2`, but those are the Jenkins et al. (2003) ratio
applied to *aboveground* biomass — a different method from the one the GTR
describes.

## Arrays

Every estimator accepts scalars or array-likes and returns the matching shape,
so a whole inventory can go through in one call:

```python
import numpy as np

estimators.carbon_content(
    np.array([202, 631]),
    np.array([20.0, 11.3]),
    np.array([110.0, 28.0]),
    np.array(["240", "M240"]),
    np.array([0.0, 10.0]),          # cull
    np.array([np.nan, 21.0]),       # ah — NaN means an intact top
    np.array([0, 2]),               # decaycd
    np.array([np.nan, np.nan]),     # cr — NaN means use the Table S11 default
    np.array(["", "M242"]),         # province
)
```

Missing measurements propagate as `NaN` rather than raising, so a batch with
unrecorded heights yields `NaN` for those rows and real numbers everywhere
else. Out-of-domain values (negative diameter, `cull > 100`, `ah > ht`, an
unknown species code) raise `ValueError` — the underlying models are unguarded
power functions that would otherwise return complex numbers or silently wrong
results.

## Accuracy notes

Two quantities cannot be reproduced from the published supplementary CSVs to
the precision of the GTR's printed examples:

- Ten rows in tables S2a/S6a/S7a store the `a` coefficient in Excel scientific
  notation truncated to three significant figures (e.g. `3.19E-05` where the
  GTR text uses `0.000031886237`), which drifts bark quantities by up to
  ~4e-4 relative.
- The GTR's printed merchantable and sawlog heights are under-converged
  iterates — the residual of equation 7 at the published values is ~1e-6.
  This package solves to ~1e-14, so the two differ by ~1e-6 relative.

Both are publication-precision limits rather than implementation differences,
and the test suite documents each one where it applies.

## References

Westfall, James A.; Coulston, John W.; Gray, Andrew N.; Shaw, John D.;
Radtke, Philip J.; Walker, David M.; Weiskittel, Aaron R.; MacFarlane,
David W.; Affleck, David L.R.; Zhao, Dehai; Temesgen, Hailemariam; Poudel,
Krishna P.; Frank, Jereme M.; Prisley, Stephen P.; Wang, Yingfang; Sánchez
Meador, Andrew J.; Auty, David; Domke, Grant M. 2024. *A national-scale tree
volume, biomass, and carbon modeling system for the United States.* Gen. Tech.
Rep. WO-104. Washington, DC: U.S. Department of Agriculture, Forest Service.
37 p. https://doi.org/10.2737/WO-GTR-104
