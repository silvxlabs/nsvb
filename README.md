# <center> VBX </center>

## Introduction
Welcome to the Tree Biomass and Volume Extension Library (VBX). VBX faithfully implements the National Scale Volume and Biomass (NSVB) models released by the Forest Service. It's tailored to offer a robust suite of functionalities, ranging from standard tree volume and biomass calculations to extended functionality such as diameter increment and volume estimates from stump measurements.

## Features
- __NSVB Models:__ Includes a full implementation of the National Scale Volume and Biomass models. Our test suite is built around the four example in the NSVB GTR document.
- __Growth Estimation:__ Features innovative models to estimate diameter and height increments based on annual carbon accumulation.
- __Stump Measurements:__ Utilizes stump measurements to calculate tree volume and biomass, aiding in post-harvest assessments, ecological studies, and timber theft apprasials.
- __User-Friendly API:__ VBX provides a user-friendly API, making complex calculations and model implementations accessible to a wide range of users. We provide Foriegn Function Interface library for integration with other programming languages such as Python and R.

## Basic usage

VBX exposes all the volume and biomass calculation to the root namespace as native Rust function and FFI compatible functions. You can use them like this:

```rust
use vbx;

// Calculate stem wood volume in cubic feet (inside bark)
let vol = vbx.stem_wood_volume(202, 20.0, 110.0, Some("M240"));
println!("Volume: {}", vol);
```

> FFI compatible functions are suffixed with `_ffi`. For example, the FFI compatible version of the `stem_wood_volume()` function is named `stem_wood_volume_ffi()`.

We also provide a object-oriented approach using a `Tree` struct and implementations for the component calculations.

```rust
use vbx::Tree;

// Create a new tree and calculate foliage biomass
let doug_fir = Tree::new(202, 20.0, 110.0, Some("M240"))
println!("Foliage biomass: {}", doug_fir.foliage_biomass());
```



