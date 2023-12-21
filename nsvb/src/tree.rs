use std::ffi::CStr;
mod decay;
mod models;
pub mod species;

/// Represents a record of a tree from the CSV file.
#[derive(Debug, serde::Deserialize, serde::Serialize)]
pub struct TreeRecordInput {
    spcd: u16,
    division: String,
    dia: f64,
    ht: f64,
    actual_ht: f64,
    decay_class: u8,
    cull: f64,
}

impl TreeRecordInput {
    pub fn get_gross_stem_volume(self) -> f64 {
        if let Some(species) = species::SPECIES_MAP.get(self.spcd.to_string().as_str()) {
            let model = species
                .volob
                .divisions
                .get(self.division.as_str())
                .unwrap_or(&species.volob.divisions["default"]);
            models::weight_volume(self.dia, self.ht, model.model, &model.coefs)
        } else {
            0.0
        }
    }
}

pub extern "C" fn get_total_gross_stem_volume(spcd: u16, division: *c_char, dia: f64, ht: f64) -> f64 {
    let division = unsafe { CStr::from_ptr(division).to_str().unwrap() };
    if let Some(species) = species::SPECIES_MAP.get(spcd.to_string().as_str()) {
        let model = species
            .volob
            .divisions
            .get(division)
            .unwrap_or(&species.volob.divisions["default"]);
        models::weight_volume(dia, ht, model.model, &model.coefs)
    } else {
        0.0
    }
}
