use lazy_static::lazy_static;
use serde::de::{self, Deserializer, MapAccess, Visitor};
use serde::{Deserialize, Serialize};
use serde_json::Result;
use std::collections::HashMap;
use std::fmt;

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
