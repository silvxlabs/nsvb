use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ModelData {
    pub group: String,
    pub form: u8,
    pub coefs: Vec<f64>,
}

#[derive(Hash, Eq, PartialEq, Deserialize, Serialize, Debug)]
pub enum Model {
    StemWoodVolume,
    StemBarkVolume,
    StemTotalVolume, // Always Model 1. To be used with StemWoodVolumeRatio (Model 7)
    StemWoodVolumeRatio, // Always Model 6. To be used with StemTotalVolume (Model 7)
    StemTotalVolumeRatio,
    TotalBiomass,
    BarkBiomass,
    BranchBiomass,
    FoliageBiomass,
    HeightDiameter,
}

#[derive(Hash, Eq, PartialEq, Deserialize, Serialize, Debug)]
pub enum Property {
    WoodSpecificGravity,
    BarkSpecificGravity,
    CarbonFraction,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct Species {
    pub models: HashMap<Model, HashMap<String, ModelData>>,
    pub properties: HashMap<Property, f64>,
}

pub type SpeciesMap = HashMap<String, Species>;
