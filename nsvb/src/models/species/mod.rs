use lazy_static::lazy_static;

mod db;
pub mod structs;

// Load the species data into a static variable
lazy_static! {
    pub static ref SPECIES_MAP: structs::SpeciesMap = {
        let species_data = db::SPECIES_DATA;
        serde_json::from_str(species_data).unwrap()
    };
}

pub fn get_species(spcd: u16) -> Result<&'static structs::Species, String> {
    match SPECIES_MAP.get(spcd.to_string().as_str()) {
        Some(species) => Ok(species),
        None => Err(format!("Species code {} not found", spcd)),
    }
}

pub fn get_property(spcd: u16, property: structs::Property) -> Result<f64, String> {
    let species = get_species(spcd)?;
    match species.properties.get(&property) {
        Some(value) => Ok(*value),
        None => Err(format!(
            "Property {:?} not found for species code {}",
            property, spcd
        )),
    }
}

pub fn get_model(
    spcd: u16,
    model_name: structs::Model,
    division: &str,
) -> Result<&'static structs::ModelData, String> {
    let species = get_species(spcd)?;
    match species.models.get(&model_name) {
        Some(models) => {
            // Try to get the specified division, or fall back to "default"
            let model = models.get(division).or_else(|| models.get("default"));
            match model {
                Some(model) => Ok(model),
                None => Err(format!(
                    "Division {} not found for model {:?} and default model does not exist",
                    division, model_name
                )),
            }
        }
        None => Err(format!(
            "Model {:?} not found for species code {}",
            model_name, spcd
        )),
    }
}

// Come back to this once we have clarification on the mean crown ratio data
// #[derive(Serialize, Deserialize, Debug)]
// pub struct Division {
//     pub hardwood: f64,
//     pub softwood: f64,
// }

// type MeanCrownRatioMap = HashMap<String, Division>;

// lazy_static! {
//     pub static ref MEAN_CROWN_RATIO_MAP: MeanCrownRatioMap = {
//         let mean_crown_ratio_data = db::MEAN_CROWN_RATIO_DATA;
//         serde_json::from_str(mean_crown_ratio_data).unwrap()
//     };
// }
