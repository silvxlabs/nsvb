mod decay;
mod models;
pub mod species;

/// Represents a record of a tree from the CSV file.
#[derive(Debug, serde::Deserialize)]
pub struct TreeRecordInput {
    pub spcd: u16,
    division: String,
    dia: f64,
    ht: f64,
    actual_ht: f64,
    decay_class: u8,
    cull: f64,
}

#[derive(Debug, serde::Serialize)]
pub struct TreeRecordOutput {
    spcd: u16,
    division: String,
    dia: f64,
    ht: f64,
    actual_ht: f64,
    decay_class: u8,
    cull: f64,
}

impl TreeRecordInput {
    pub fn process(self) -> TreeRecordOutput {
        if let Some(component) = species::SPECIES_MAP.get(&self.spcd.to_string()) {
            println!("Found species {:?}", component);
        }
        TreeRecordOutput {
            spcd: self.spcd,
            division: self.division,
            dia: self.dia,
            ht: self.ht,
            actual_ht: self.actual_ht,
            decay_class: self.decay_class,
            cull: self.cull,
        }
    }
}
