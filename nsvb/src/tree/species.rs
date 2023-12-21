use lazy_static::lazy_static;
use serde::{Deserialize, Serialize};
use serde_json::Result;
use std::collections::HashMap;

mod coefs;

#[derive(Serialize, Deserialize, Debug)]
pub struct ModelData {
    pub group: String,
    pub model: u8,
    pub coefs: Vec<f64>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct Division {
    #[serde(flatten)]
    pub divisions: HashMap<String, ModelData>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct Component {
    pub wdsg: f64,
    pub bksg: f64,
    pub cfrac: f64,
    pub volib: Division,
    pub volbk: Division,
    pub volob: Division,
    pub rcumob: Division,
    pub rcumib: Division,
    pub total_biomass: Division,
    pub bark_biomass: Division,
    pub branch_biomass: Division,
    pub foliage_biomass: Division,
}

type SpeciesMap = HashMap<String, Component>;

lazy_static! {
    pub static ref SPECIES_MAP: SpeciesMap = {
        let species_data = coefs::SPECIES_DATA;
        serde_json::from_str(species_data).unwrap()
    };
}
