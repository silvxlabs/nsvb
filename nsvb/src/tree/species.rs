use lazy_static::lazy_static;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

mod coefs;

#[derive(Serialize, Deserialize, Debug)]
pub struct ModelData {
    pub group: String,
    pub model: u8,
    pub coefs: Vec<f64>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct Component {
    pub wdsg: f64,
    pub bksg: f64,
    pub cfrac: f64,
    pub volib: HashMap<String, ModelData>,
    pub volbk: HashMap<String, ModelData>,
    pub volob: HashMap<String, ModelData>,
    pub rcumob: HashMap<String, ModelData>,
    pub rcumib: HashMap<String, ModelData>,
    pub total_biomass: HashMap<String, ModelData>,
    pub bark_biomass: HashMap<String, ModelData>,
    pub branch_biomass: HashMap<String, ModelData>,
    pub foliage_biomass: HashMap<String, ModelData>,
}

type SpeciesMap = HashMap<String, Component>;

lazy_static! {
    pub static ref SPECIES_MAP: SpeciesMap = {
        let species_data = coefs::SPECIES_DATA;
        serde_json::from_str(species_data).unwrap()
    };
}

#[derive(Serialize, Deserialize, Debug)]
pub struct Division {
    pub hardwood: f64,
    pub softwood: f64,
}

type MeanCrownRatioMap = HashMap<String, Division>;

lazy_static! {
    pub static ref MEAN_CROWN_RATIO_MAP: MeanCrownRatioMap = {
        let mean_crown_ratio_data = coefs::MEAN_CROWN_RATIO_DATA;
        serde_json::from_str(mean_crown_ratio_data).unwrap()
    };
}
