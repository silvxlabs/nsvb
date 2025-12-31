# User Guide

This guide provides detailed examples for all NSVB calculations, including special cases for dead trees, broken tops, and cull deductions.

## Volume Calculations

### Total Inside Bark Volume

Calculate the total inside bark wood volume (cubic feet):

```python
from nsvb import total_inside_bark_wood_volume

volume = total_inside_bark_wood_volume(
    spcd=202,      # Douglas-fir
    dia=20.0,      # inches DBH
    ht=110.0,      # feet
    division="240" # Marine Division
)
print(f"Inside bark volume: {volume:.2f} ft³")
```

### Total Bark Volume

Calculate bark volume separately:

```python
from nsvb import total_bark_wood_volume

bark_volume = total_bark_wood_volume(
    spcd=202,
    dia=20.0,
    ht=110.0,
    division="240"
)
print(f"Bark volume: {bark_volume:.2f} ft³")
```

### Total Outside Bark Volume

Calculate total outside bark volume (wood + bark):

```python
from nsvb import total_outside_bark_volume

total_volume = total_outside_bark_volume(
    spcd=202,
    dia=20.0,
    ht=110.0,
    division="240"
)
print(f"Total outside bark volume: {total_volume:.2f} ft³")
```

### Component Volumes

Calculate volumes for specific tree components:

```python
from nsvb import (
    stump_volume,
    merchantable_volume,
    sawlog_volume,
    top_volume
)

spcd = 202
dia = 20.0
ht = 110.0
division = "240"

# Stump (ground to 1 foot)
stump = stump_volume(spcd, dia, ht, division, bark="ib")
print(f"Stump volume (IB): {stump:.2f} ft³")

# Merchantable (1 foot to 4" top)
merch = merchantable_volume(spcd, dia, ht, division, bark="ib")
print(f"Merchantable volume (IB): {merch:.2f} ft³")

# Sawlog (1 foot to 7" top for softwood, 9" for hardwood)
sawlog = sawlog_volume(spcd, dia, ht, division, bark="ib")
print(f"Sawlog volume (IB): {sawlog:.2f} ft³")

# Top (from 4" top to tree tip)
top = top_volume(spcd, dia, ht, division, bark="ib")
print(f"Top volume (IB): {top:.2f} ft³")
```

Use `bark="ob"` for outside bark volumes or `bark="bk"` for bark-only volumes.

## Biomass Calculations

### Stem Wood Dry Weight

Calculate stem wood dry weight (pounds):

```python
from nsvb import total_stem_wood_dry_weight

wood_weight = total_stem_wood_dry_weight(
    spcd=202,
    dia=20.0,
    ht=110.0,
    division="240"
)
print(f"Stem wood: {wood_weight:.2f} lb")
```

### Stem Bark Weight

```python
from nsvb import total_stem_bark_weight

bark_weight = total_stem_bark_weight(
    spcd=202,
    dia=20.0,
    ht=110.0,
    division="240"
)
print(f"Stem bark: {bark_weight:.2f} lb")
```

### Branch and Foliage Weight

```python
from nsvb import total_branch_weight, total_foliage_dry_weight

branch_weight = total_branch_weight(spcd=202, dia=20.0, ht=110.0, division="240")
foliage_weight = total_foliage_dry_weight(spcd=202, dia=20.0, ht=110.0, division="240")

print(f"Branch weight: {branch_weight:.2f} lb")
print(f"Foliage weight: {foliage_weight:.2f} lb")
```

### Total Aboveground Biomass

```python
from nsvb import total_aboveground_biomass

agb = total_aboveground_biomass(
    spcd=202,
    dia=20.0,
    ht=110.0,
    division="240"
)
print(f"Total AGB: {agb:.2f} lb")
```

## Trees with Cull

Cull represents defect or rot in the tree. Use the `cull` parameter (percent cull):

```python
from nsvb import (
    total_stem_wood_dry_weight,
    total_aboveground_biomass,
    harmonize_components
)

# Red maple with 3% cull
spcd = 316
dia = 11.1
ht = 38.0
division = "M210"
cull = 3.0  # 3% cull

# Stem wood weight reduced by cull
wood_weight = total_stem_wood_dry_weight(spcd, dia, ht, division, cull=cull)
print(f"Stem wood (with cull): {wood_weight:.2f} lb")

# Harmonized components with cull
result = harmonize_components(spcd, dia, ht, division, cull=cull)
print(f"Wood:   {result['wood']:.2f} lb")
print(f"Bark:   {result['bark']:.2f} lb")
print(f"Branch: {result['branch']:.2f} lb")
print(f"AGB:    {result['agb']:.2f} lb")
```

## Dead Trees with Decay

Dead trees require the `decaycd` parameter (decay class 1-5):

```python
from nsvb import (
    total_stem_wood_dry_weight,
    total_stem_bark_weight,
    total_branch_weight,
    harmonize_components
)

# Dead tanoak, decay class 2
spcd = 631      # Tanoak
dia = 11.3
ht = 28.0
division = "M240"
decaycd = 2     # Decay class 2

# Decay reduces density and component retention
wood_weight = total_stem_wood_dry_weight(spcd, dia, ht, division, decaycd=decaycd)
bark_weight = total_stem_bark_weight(spcd, dia, ht, division, decaycd=decaycd)
branch_weight = total_branch_weight(spcd, dia, ht, division, decaycd=decaycd)

print(f"Stem wood (decay class 2): {wood_weight:.2f} lb")
print(f"Bark (decay class 2): {bark_weight:.2f} lb")
print(f"Branches (decay class 2): {branch_weight:.2f} lb")

# Harmonization accounts for decay
result = harmonize_components(spcd, dia, ht, division, decaycd=decaycd)
print(f"Total AGB with decay: {result['agb']:.2f} lb")
```

### Decay Classes

Decay classes (1-5) represent progressive stages of decomposition:

- **Class 1**: Recently dead, minimal decay
- **Class 2**: Moderate decay, some bark loss
- **Class 3**: Advanced decay, significant bark and branch loss
- **Class 4**: Very decayed, minimal bark, no branches
- **Class 5**: Extremely decayed, no bark or branches

## Broken Top Trees

Trees with broken tops use the `ah` (actual height) parameter:

```python
from nsvb import (
    total_stem_wood_dry_weight,
    total_stem_bark_weight,
    total_branch_weight,
)

# White oak with broken top
spcd = 802       # White oak
dia = 18.1
ht = 65.0        # Original height
ah = 59.0        # Actual height (broken at 59 feet)
division = "M220"
cr = 30.0        # Crown ratio (30%)
cull = 2.0

# Calculations use actual height to adjust volumes
wood_weight = total_stem_wood_dry_weight(spcd, dia, ht, ah=ah, division=division, cull=cull)
bark_weight = total_stem_bark_weight(spcd, dia, ht, ah=ah, division=division)
branch_weight = total_branch_weight(spcd, dia, ht, ah=ah, division=division, cr=cr)

print(f"Stem wood (broken top): {wood_weight:.2f} lb")
print(f"Bark (broken top): {bark_weight:.2f} lb")
print(f"Branches (broken top): {branch_weight:.2f} lb")
```

### Dead Trees with Broken Tops

Combine `decaycd` and `ah` for dead trees with broken tops:

```python
from nsvb import total_stem_wood_dry_weight, total_branch_weight

# Dead tanoak with broken top
spcd = 631
dia = 11.3
ht = 28.0        # Original height
ah = 21.0        # Broken at 21 feet
division = "M240"
decaycd = 2
cull = 10.0

# Both decay and broken top adjustments applied
wood_weight = total_stem_wood_dry_weight(
    spcd, dia, ht, ah=ah, division=division, cull=cull, decaycd=decaycd
)

# Crown ratio looked up from Table S11 for dead trees
branch_weight = total_branch_weight(
    spcd, dia, ht, ah=ah, division="M242", decaycd=decaycd  # Use province for CR lookup
)

print(f"Stem wood (dead, broken): {wood_weight:.2f} lb")
print(f"Branches (dead, broken): {branch_weight:.2f} lb")
```

## Component Harmonization

Harmonization ensures that wood + bark + branch = total AGB:

```python
from nsvb import harmonize_components

# Standard harmonization
result = harmonize_components(
    spcd=202,
    dia=20.0,
    ht=110.0,
    division="240"
)

# Components now sum exactly to AGB
total = result['wood'] + result['bark'] + result['branch']
assert abs(total - result['agb']) < 1e-6

print(f"Harmonized wood:   {result['wood']:.2f} lb")
print(f"Harmonized bark:   {result['bark']:.2f} lb")
print(f"Harmonized branch: {result['branch']:.2f} lb")
print(f"Total AGB:         {result['agb']:.2f} lb")
```

Harmonization works with all modifiers (cull, decay, broken top):

```python
# Harmonization with cull
result = harmonize_components(spcd=316, dia=11.1, ht=38.0, division="M210", cull=3.0)

# Harmonization with decay
result = harmonize_components(spcd=631, dia=11.3, ht=28.0, division="M240", decaycd=2)
```

## Carbon Calculations

### Live Tree Carbon

```python
from nsvb import calculate_carbon

# Carbon content for live tree
carbon = calculate_carbon(
    spcd=202,      # Douglas-fir
    dia=20.0,
    ht=110.0,
    division="240"
)
print(f"Carbon: {carbon:.2f} lb")
```

### Dead Tree Carbon

For dead trees, carbon fractions vary by decay class:

```python
from nsvb import calculate_carbon, get_carbon_fraction

# Dead tanoak, decay class 2
spcd = 631
decaycd = 2

# Get decay-class-specific carbon fraction
carbon_fraction = get_carbon_fraction(spcd=spcd, decaycd=decaycd)
print(f"Carbon fraction (hardwood, decay 2): {carbon_fraction:.4f}")

# Calculate total carbon
carbon = calculate_carbon(
    spcd=spcd,
    dia=11.3,
    ht=28.0,
    division="M240",
    decaycd=decaycd
)
print(f"Carbon (dead tree): {carbon:.2f} lb")
```

### Carbon with Cull

```python
from nsvb import calculate_carbon

# Red maple with 3% cull
carbon = calculate_carbon(
    spcd=316,
    dia=11.1,
    ht=38.0,
    division="M210",
    cull=3.0
)
print(f"Carbon (with cull): {carbon:.2f} lb")
```

## DRYBIO Partitioning

Partition stem wood biomass into components:

```python
from nsvb import drybio_stump, drybio_bole, drybio_top

spcd = 202
dia = 20.0
ht = 110.0
division = "240"

# Stump: ground to 1 foot
stump = drybio_stump(spcd, dia, ht, division)

# Bole: 1 foot to 4" top diameter
bole = drybio_bole(spcd, dia, ht, division)

# Top: 4" top to tree tip
top = drybio_top(spcd, dia, ht, division)

print(f"DRYBIO_STUMP: {stump:.2f} lb")
print(f"DRYBIO_BOLE:  {bole:.2f} lb")
print(f"DRYBIO_TOP:   {top:.2f} lb")
print(f"Total:        {stump + bole + top:.2f} lb")
```

### Sapling Biomass

For saplings (D < 5 inches):

```python
from nsvb import drybio_sapling

sapling_biomass = drybio_sapling(
    spcd=202,
    dia=3.5,   # Small diameter
    ht=25.0,
    division="240"
)
print(f"DRYBIO_SAPLING: {sapling_biomass:.2f} lb")
```

### Woodland Species

For woodland species, use total AGB:

```python
from nsvb import drybio_wdld_spp

woodland_biomass = drybio_wdld_spp(
    spcd=202,
    dia=10.0,
    ht=40.0,
    division="240"
)
print(f"DRYBIO_WDLD_SPP: {woodland_biomass:.2f} lb")
```

## Vectorized Calculations

Process multiple trees efficiently using NumPy arrays:

```python
import numpy as np
from nsvb import (
    total_inside_bark_wood_volume,
    total_aboveground_biomass,
    harmonize_components,
    calculate_carbon
)

# Arrays of tree data
spcd = np.array([202, 316, 631, 802])
dia = np.array([20.0, 11.1, 11.3, 18.1])
ht = np.array([110.0, 38.0, 28.0, 65.0])
division = np.array(["240", "M210", "M240", "M220"])
cull = np.array([0.0, 3.0, 10.0, 2.0])

# Calculate for all trees at once
volumes = total_inside_bark_wood_volume(spcd, dia, ht, division)
agb = total_aboveground_biomass(spcd, dia, ht, division)
carbon = calculate_carbon(spcd, dia, ht, division, cull=cull)

print("Volumes:", volumes)
print("AGB:", agb)
print("Carbon:", carbon)

# Harmonization with arrays
result = harmonize_components(spcd, dia, ht, division, cull=cull)
print("Harmonized wood:", result['wood'])
print("Harmonized AGB:", result['agb'])
```

## Common Parameters Reference

### Required Parameters

- **spcd** (int or array): FIA species code
- **dia** (float or array): Diameter at breast height (inches)
- **ht** (float or array): Total tree height (feet)
- **division** (str or array): Ecodivision code (e.g., "240", "M210")

### Optional Parameters

- **cull** (float or array): Percent cull/defect (default: 0.0)
- **decaycd** (int or array): Decay class 1-5 for dead trees (default: None)
- **ah** (float or array): Actual height for broken top trees (default: None)
- **cr** (float or array): Crown ratio as percentage (default: None, auto-lookup from Table S11)

### Common Species Codes (SPCD)

- 202: Douglas-fir (Pseudotsuga menziesii)
- 316: Red maple (Acer rubrum)
- 631: Tanoak (Notholithocarpus densiflorus)
- 802: White oak (Quercus alba)

See FIADB documentation for complete species code list.

### Common Ecodivisions

- "240": Marine Division
- "M210": Warm Continental Mountains
- "M220": Hot Continental Mountains
- "M240": Marine Mountains
- "M242": Marine Mountains (Province)

## Next Steps

- **[API Reference](reference.md)** - Complete function documentation
