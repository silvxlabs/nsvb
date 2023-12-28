pub mod decay;
mod models;
mod species;

pub use decay::Decay;

/// Represents a record of a tree from the CSV file.
#[derive(Debug, serde::Deserialize, serde::Serialize)]
pub struct TreeRecordInput {
    pub spcd: u16,
    pub division: String,
    pub dia: f64,
    pub ht: f64,
    pub actual_ht: f64,
    pub decay_class: u8,
    pub cull: f64,
}

impl TreeRecordInput {
    pub fn gross_stem_vol_ib(&self) -> f64 {
        gross_stem_vol_ib(self.spcd, self.division.as_str(), self.dia, self.ht)
    }
}

pub fn gross_stem_vol_ib(spcd: u16, division: &str, dia: f64, ht: f64) -> f64 {
    if let Some(species) = species::SPECIES_MAP.get(spcd.to_string().as_str()) {
        let model = species
            .volib
            .get(division)
            .unwrap_or(species.volib.get("default").unwrap());
        models::weight_volume(dia, ht, model.model, &model.coefs)
    } else {
        0.0
    }
}

pub fn gross_stem_vol_ib_bulk(
    spcd: &Vec<u16>,
    division: &Vec<String>,
    dia: &Vec<f64>,
    ht: &Vec<f64>,
) -> Vec<f64> {
    let mut result = Vec::new();
    for i in 0..spcd.len() {
        result.push(gross_stem_vol_ib(
            spcd[i],
            division[i].as_str(),
            dia[i],
            ht[i],
        ));
    }
    result
}

pub fn gross_stem_vol_bk(spcd: u16, division: &str, dia: f64, ht: f64) -> f64 {
    if let Some(species) = species::SPECIES_MAP.get(spcd.to_string().as_str()) {
        let model = species
            .volbk
            .get(division)
            .unwrap_or(species.volbk.get("default").unwrap());
        models::weight_volume(dia, ht, model.model, &model.coefs)
    } else {
        0.0
    }
}

pub fn height_to_diameter(spcd: u16, division: &str, dia: f64, ht: f64, target_dia: f64) -> f64 {
    if let Some(species) = species::SPECIES_MAP.get(spcd.to_string().as_str()) {
        let volob_model = species
            .volob
            .get(division)
            .unwrap_or(species.volob.get("default").unwrap());
        let ratio_model = species
            .rcumob
            .get(division)
            .unwrap_or(species.rcumob.get("default").unwrap());
        models::height_to_diameter(dia, ht, target_dia, &volob_model.coefs, &ratio_model.coefs)
    } else {
        0.0
    }
}

pub fn volume_ratio(spcd: u16, division: &str, target_ht: f64, ht: f64) -> f64 {
    if let Some(species) = species::SPECIES_MAP.get(spcd.to_string().as_str()) {
        let ratio_model = species
            .rcumib
            .get(division)
            .unwrap_or(species.rcumib.get("default").unwrap());
        models::volume_ratio(target_ht, ht, ratio_model.coefs[0], ratio_model.coefs[1])
    } else {
        0.0
    }
}

pub fn stem_bark_biomass(spcd: u16, division: &str, dia: f64, ht: f64) -> f64 {
    if let Some(species) = species::SPECIES_MAP.get(spcd.to_string().as_str()) {
        let model = species
            .bark_biomass
            .get(division)
            .unwrap_or(species.bark_biomass.get("default").unwrap());
        models::weight_volume(dia, ht, model.model, &model.coefs)
    } else {
        0.0
    }
}

pub fn branch_biomass(spcd: u16, division: &str, dia: f64, ht: f64) -> f64 {
    if let Some(species) = species::SPECIES_MAP.get(spcd.to_string().as_str()) {
        let model = species
            .branch_biomass
            .get(division)
            .unwrap_or(species.branch_biomass.get("default").unwrap());
        models::weight_volume(dia, ht, model.model, &model.coefs)
    } else {
        0.0
    }
}

pub fn above_groud_biomass(spcd: u16, division: &str, dia: f64, ht: f64) -> f64 {
    if let Some(species) = species::SPECIES_MAP.get(spcd.to_string().as_str()) {
        let model = species
            .total_biomass
            .get(division)
            .unwrap_or(species.total_biomass.get("default").unwrap());
        models::weight_volume(dia, ht, model.model, &model.coefs)
    } else {
        0.0
    }
}

pub fn foilage_biomass(spcd: u16, division: &str, dia: f64, ht: f64) -> f64 {
    if let Some(species) = species::SPECIES_MAP.get(spcd.to_string().as_str()) {
        let model = species
            .foliage_biomass
            .get(division)
            .unwrap_or(species.foliage_biomass.get("default").unwrap());
        models::weight_volume(dia, ht, model.model, &model.coefs)
    } else {
        0.0
    }
}

pub fn wood_specief_gravity(spcd: u16) -> f64 {
    if let Some(species) = species::SPECIES_MAP.get(spcd.to_string().as_str()) {
        species.wdsg
    } else {
        0.0
    }
}

pub fn carbon_fraction(spcd: u16) -> f64 {
    if let Some(species) = species::SPECIES_MAP.get(spcd.to_string().as_str()) {
        species.cfrac / 100.0
    } else {
        0.5
    }
}

pub fn all_components(
    spcd: u16,
    division: &str,
    dia: f64,
    ht: f64,
    actual_ht: f64,
    decay_class: u8,
    cull: f64,
    merch_dia: f64,
    saw_dia: f64,
) -> (f64, f64, f64, f64, f64) {
    // Step 1: Gross total stem volume
    let v_tot_ib_gross = gross_stem_vol_ib(spcd, division, dia, ht);
    println!("v_tot_ib_gross: {}", v_tot_ib_gross);

    // Step 2: Gross total stem bark volume
    let v_tot_bk_gross = gross_stem_vol_bk(spcd, division, dia, ht);

    // Step 3: Gross total stem outside-bark volume
    let v_tot_ob_gross = v_tot_ib_gross + v_tot_bk_gross;

    // Step 4: Heights to merchantable top diameter and, if present, sawlog top diameter
    let hm = height_to_diameter(spcd, division, dia, ht, merch_dia);
    let hs = height_to_diameter(spcd, division, dia, ht, saw_dia);

    // Step 5: Stem component gross volumes (stump, merch stem, sawlog, stem top)

    // Step 6: Stem component sound volumes

    // Step 7: Covert stem component volume to biomass weight

    // Step 8: Total stem bark biomass

    // Step 9: Total branch biomass

    // Step 10: Total above-ground biomass

    // Step 11: Sum stem wood biomass for second agb biomass

    // Step 12: Proportionally distribute the difference

    // Step 13: Adjusted wood density

    // Step 14: Adjusted bark density

    // Step 15: Foliage biomass

    // Step 16: Total above-ground carbon

    (0.0, 0.0, 0.0, 0.0, 0.0)
}
