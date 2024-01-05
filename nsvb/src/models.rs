mod decay;
mod eqns;
mod species;

use species::structs::Model;

pub fn stem_wood_volume(spcd: u16, dia: f64, ht: f64, division: &str) -> Result<f64, String> {
    let model = species::get_model(spcd, Model::StemWoodVolume, division)?;
    Ok(eqns::weight_volume(dia, ht, model.form, &model.coefs))
}

pub fn stem_bark_volume(spcd: u16, dia: f64, ht: f64, division: &str) -> Result<f64, String> {
    let model = species::get_model(spcd, Model::StemBarkVolume, division)?;
    Ok(eqns::weight_volume(dia, ht, model.form, &model.coefs))
}

pub fn height_to_diameter(
    spcd: u16,
    dia: f64,
    ht: f64,
    dia_top: f64,
    division: &str,
) -> Result<f64, String> {
    let volume_model = species::get_model(spcd, Model::StemTotalVolume, division)?;
    let ratio_model = species::get_model(spcd, Model::StemWoodVolumeRatio, division)?;
    Ok(eqns::height_to_diameter(
        dia,
        ht,
        dia_top,
        &volume_model.coefs,
        &ratio_model.coefs,
    ))
}

pub fn stem_volume_ratio(spcd: u16, z: f64, ht: f64, division: &str) -> Result<f64, String> {
    let model = species::get_model(spcd, Model::StemTotalVolumeRatio, division)?;
    Ok(eqns::volume_ratio(z, ht, model.coefs[0], model.coefs[1]))
}

pub fn total_biomass(spcd: u16, dia: f64, ht: f64, division: &str) -> Result<f64, String> {
    let model = species::get_model(spcd, Model::TotalBiomass, division)?;
    Ok(eqns::weight_volume(dia, ht, model.form, &model.coefs))
}

pub fn bark_biomass(spcd: u16, dia: f64, ht: f64, division: &str) -> Result<f64, String> {
    let model = species::get_model(spcd, Model::BarkBiomass, division)?;
    Ok(eqns::weight_volume(dia, ht, model.form, &model.coefs))
}

pub fn branch_biomass(spcd: u16, dia: f64, ht: f64, division: &str) -> Result<f64, String> {
    let model = species::get_model(spcd, Model::BranchBiomass, division)?;
    Ok(eqns::weight_volume(dia, ht, model.form, &model.coefs))
}

pub fn foliage_biomass(spcd: u16, dia: f64, ht: f64, division: &str) -> Result<f64, String> {
    let model = species::get_model(spcd, Model::FoliageBiomass, division)?;
    Ok(eqns::weight_volume(dia, ht, model.form, &model.coefs))
}
