# Getting Started

This guide will get you calculating tree volumes and biomass quickly.

## Basic Volume Calculation

Calculate total inside bark volume for a Douglas-fir:

```python
from nsvb import total_inside_bark_wood_volume

# Douglas-fir (SPCD=202), D=20.0", H=110', Division=240
volume = total_inside_bark_wood_volume(
    spcd=202,
    dia=20.0,    # inches
    ht=110.0,    # feet
    division="240"
)

print(f"Volume: {volume:.2f} ft³")
# Volume: 88.45 ft³
```

## Basic Biomass Calculation

Calculate stem wood dry weight and total aboveground biomass:

```python
from nsvb import total_stem_wood_dry_weight, total_aboveground_biomass

spcd = 202      # Douglas-fir
dia = 20.0      # inches
ht = 110.0      # feet
division = "240"

# Stem wood weight
wood_weight = total_stem_wood_dry_weight(spcd, dia, ht, division)
print(f"Stem wood: {wood_weight:.2f} lb")
# Stem wood: 2483.74 lb

# Total aboveground biomass (wood + bark + branches + foliage)
agb = total_aboveground_biomass(spcd, dia, ht, division)
print(f"Total AGB: {agb:.2f} lb")
# Total AGB: 3154.55 lb
```

## Harmonized Component Biomass

Get harmonized estimates that ensure components sum to total AGB:

```python
from nsvb import harmonize_components

result = harmonize_components(
    spcd=202,
    dia=20.0,
    ht=110.0,
    division="240"
)

print(f"Wood:    {result['wood']:.2f} lb")
print(f"Bark:    {result['bark']:.2f} lb")
print(f"Branch:  {result['branch']:.2f} lb")
print(f"Total:   {result['agb']:.2f} lb")
# Wood:    2508.83 lb
# Bark:    365.44 lb
# Branch:  280.29 lb
# Total:   3154.55 lb

# Verify components sum to total
assert abs(result['wood'] + result['bark'] + result['branch'] - result['agb']) < 0.01
```

## Carbon Content

Calculate carbon content for a tree:

```python
from nsvb import calculate_carbon

carbon = calculate_carbon(
    spcd=202,
    dia=20.0,
    ht=110.0,
    division="240"
)

print(f"Carbon: {carbon:.2f} lb")
# Carbon: 1626.50 lb
```

## Trees with Cull

Account for cull (defect) in volume and biomass:

```python
from nsvb import total_stem_wood_dry_weight

# Red maple with 3% cull
wood_no_cull = total_stem_wood_dry_weight(
    spcd=316,
    dia=11.1,
    ht=38.0,
    division="M210",
    cull=0.0
)

wood_with_cull = total_stem_wood_dry_weight(
    spcd=316,
    dia=11.1,
    ht=38.0,
    division="M210",
    cull=3.0  # 3% cull
)

print(f"Without cull: {wood_no_cull:.2f} lb")
print(f"With 3% cull: {wood_with_cull:.2f} lb")
# Without cull: 288.24 lb
# With 3% cull: 284.27 lb
```

## Processing Multiple Trees

Use NumPy arrays to process multiple trees at once:

```python
import numpy as np
from nsvb import total_inside_bark_wood_volume, total_aboveground_biomass

# Three trees: Douglas-fir, Red maple, White oak
spcd = np.array([202, 316, 802])
dia = np.array([20.0, 11.1, 18.1])
ht = np.array([110.0, 38.0, 65.0])
division = np.array(["240", "M210", "M220"])

# Calculate volumes for all trees at once
volumes = total_inside_bark_wood_volume(spcd, dia, ht, division)
print("Volumes:", volumes)
# Volumes: [88.45 9.43 42.28]

# Calculate AGB for all trees
agb = total_aboveground_biomass(spcd, dia, ht, division)
print("AGB:", agb)
# AGB: [3154.55  532.58 2590.39]
```

## Common Parameters

All functions accept these core parameters:

- **spcd**: FIA species code (integer, e.g., 202 for Douglas-fir)
- **dia**: Diameter at breast height in inches (float or array)
- **ht**: Total tree height in feet (float or array)
- **division**: Ecodivision code (string or array, e.g., "240", "M210")

Optional parameters:

- **cull**: Percent cull/defect (float, default=0.0)
- **decaycd**: Decay class for dead trees (int 1-5, default=None for live trees)
- **ah**: Actual height for broken top trees (float, default=None)
- **cr**: Crown ratio as percentage (float, default=None)

## Next Steps

- **[User Guide](user-guide.md)** - Detailed examples for special cases
- **[API Reference](reference.md)** - Complete function documentation
