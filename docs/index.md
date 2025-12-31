# NSVB: National-Scale Volume and Biomass Estimators

Welcome to the NSVB Python package documentation. NSVB provides a faithful implementation of the National-Scale Volume and Biomass (NSVB) framework for estimating tree volume, biomass, and carbon as published in the USDA Forest Service General Technical Report GTR-WO-104.

## What is NSVB?

NSVB is a comprehensive framework for calculating:

- **Tree volumes** (inside bark, bark, total outside bark)
- **Component volumes** (stump, merchantable, sawlog, top)
- **Biomass estimates** (stem wood, bark, branches, foliage, total aboveground biomass)
- **Carbon content** for live and dead trees
- **Special adjustments** for cull, broken tops, and decay classes

The package implements all equations, models, and workflows from GTR-WO-104, validated against the worked examples in the technical report.

## Installation

Install NSVB from PyPI using pip:

```bash
pip install nsvb
```

Or using uv:

```bash
uv add nsvb
```

## Quick Example

Calculate volume and biomass for a Douglas-fir tree:

```python
from nsvb import (
    total_inside_bark_wood_volume,
    total_stem_wood_dry_weight,
    total_aboveground_biomass,
)

# Douglas-fir (SPCD=202), D=20.0", H=110', Division=240
spcd = 202
dia = 20.0  # inches
ht = 110.0  # feet
division = "240"

# Calculate volume (cubic feet)
volume = total_inside_bark_wood_volume(spcd, dia, ht, division)
print(f"Total inside bark volume: {volume:.2f} ft³")
# Total inside bark volume: 88.45 ft³

# Calculate stem wood dry weight (pounds)
wood_weight = total_stem_wood_dry_weight(spcd, dia, ht, division)
print(f"Stem wood dry weight: {wood_weight:.2f} lb")
# Stem wood dry weight: 2483.74 lb

# Calculate total aboveground biomass (pounds)
agb = total_aboveground_biomass(spcd, dia, ht, division)
print(f"Total aboveground biomass: {agb:.2f} lb")
# Total aboveground biomass: 3154.55 lb
```

## Next Steps

- **[Getting Started](getting-started.md)** - Quick start guide with practical examples
- **[User Guide](user-guide.md)** - Detailed guide covering all calculations and special cases
- **[API Reference](reference.md)** - Complete API documentation

## Reference Documentation

This package implements the methods described in:

Westfall, James A.; Coulston, John W.; Gray, Andrew N.; Shaw, John D.; Radtke, Philip J.; Walker, David M.; Weiskittel, Aaron R.; MacFarlane, David W.; Affleck, David L.R.; Zhao, Dehai; Temesgen, Hailemariam; Poudel, Krishna P.; Frank, Jereme M.; Prisley, Stephen P.; Wang, Yingfang; Sánchez Meador, Andrew J.; Auty, David; Domke, Grant M. 2024. A national-scale tree volume, biomass, and carbon modeling system for the United States. Gen. Tech. Rep. WO-104. Washington, DC: U.S. Department of Agriculture, Forest Service. 37 p. https://doi.org/10.2737/WO-GTR-104.

Bibtex entry:
```
 @book{Westfall_2024, title={A national-scale tree volume, biomass, and carbon modeling system for the United States}, url={http://dx.doi.org/10.2737/WO-GTR-104}, DOI={10.2737/wo-gtr-104}, institution={U.S. Department of Agriculture, Forest Service}, author={Westfall, James A. and Coulston, John W. and Gray, Andrew N. and Shaw, John D. and Radtke, Philip J. and Walker, David M. and Weiskittel, Aaron R. and MacFarlane, David W. and Affleck, David L.R. and Zhao, Dehai and Temesgen, Hailemariam and Poudel, Krishna P. and Frank, Jereme M. and Prisley, Stephen P. and Wang, Yingfang and Sánchez Meador, Andrew J. and Auty, David and Domke, Grant M.}, year={2024} }
```

PDF available at: [https://doi.org/10.2737/WO-GTR-104](https://doi.org/10.2737/WO-GTR-104)

## Source Code

GitHub: [https://github.com/silvxlabs/nsvb](https://github.com/silvxlabs/nsvb)

## License

MIT License
