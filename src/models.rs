mod decay;
mod eqns;
mod species;

use species::structs::Model;

/// Calculate the inside bark stem wood volume in cubic feet.
///
/// # Arguments
///
/// * `spcd` - FIA species code
/// * `dia` - Diameter at breast height (in)
/// * `ht` - Total tree height (ft)
/// * `division` - Optional ecodivision code
///
/// # Examples
///
/// ```
/// use nsvb;
///
/// let volume = nsvb::stem_wood_volume(202, 20.0, 110.0, Some("240")).unwrap();
/// assert_eq!(volume, 88.45229093648126);
/// ```
///
/// # Notes
///
/// This function queries coefficients from Table S1a and S1b from the NSVB GTR
/// supplement.
pub fn stem_wood_volume(
    spcd: u16,
    dia: f64,
    ht: f64,
    division: Option<&str>,
) -> Result<f64, String> {
    let div = division.unwrap_or("default");
    let model = species::get_model(spcd, Model::StemWoodVolume, div)?;
    Ok(eqns::weight_volume(dia, ht, model.form, &model.coefs))
}

/// Calculate the volume of stem bark in cubic feet.
///
/// # Arguments
///
/// * `spcd` - FIA species code
/// * `dia` - Diameter at breast height (in)
/// * `ht` - Total tree height (ft)
/// * `division` - Optional ecodivision code
///
/// # Examples
///
/// ```
/// use nsvb;
///
/// let volume = nsvb::stem_bark_volume(202, 20.0, 110.0, Some("240")).unwrap();
/// assert_eq!(volume, 13.197130062388565);
/// ```
///
/// # Notes
///
/// This function queries coefficients from Table S2a and S2b from the NSVB GTR
/// supplement.
pub fn stem_bark_volume(
    spcd: u16,
    dia: f64,
    ht: f64,
    division: Option<&str>,
) -> Result<f64, String> {
    let div = division.unwrap_or("default");
    let model = species::get_model(spcd, Model::StemBarkVolume, div)?;
    Ok(eqns::weight_volume(dia, ht, model.form, &model.coefs))
}

/// Calculate the height in feet along the stem to a specified top-end diameter.
///
/// # Arguments
///
/// * `spcd` - FIA species code
/// * `dia` - Diameter at breast height (in)
/// * `ht` - Total tree height (ft)
/// * `dia_top` - Diameter at the specified height (in)
/// * `division` - Optional ecodivision code
///
/// # Examples
///
/// ```
/// use nsvb;
///
/// let height = nsvb::height_to_diameter(202, 20.0, 110.0, 9.0, None).unwrap();
/// assert_eq!(height, 78.32313537597656);
/// ```
///
/// # Notes
///
/// This function queries coefficients from Tabls S3a, S3b, S4a, and S4b from
/// the NSVB GTR supplement.
pub fn height_to_diameter(
    spcd: u16,
    dia: f64,
    ht: f64,
    dia_top: f64,
    division: Option<&str>,
) -> Result<f64, String> {
    let div = division.unwrap_or("default");
    let volume_model = species::get_model(spcd, Model::StemTotalVolume, div)?;
    let ratio_model = species::get_model(spcd, Model::StemWoodVolumeRatio, div)?;
    Ok(eqns::height_to_diameter(
        dia,
        ht,
        dia_top,
        &volume_model.coefs,
        &ratio_model.coefs,
    ))
}

/// Calculate the outside bark stem volume ratio for a specified height fraction
/// of the total tree height.
///
/// # Arguments
///
/// * `spcd` - FIA species code
/// * `ht_ratio` - Height ratio (height / total height)
/// * `division` - Optional ecodivision code
///
/// # Examples
///
/// ```
/// use nsvb;
///
/// let ratio = nsvb::stem_volume_ratio(202, 78.32313537597656/110.0, Some("240")).unwrap();
/// assert_eq!(ratio, 0.9533893700705219);
/// ```
///
/// # Notes
///
/// This function queries coefficients from Tabls S5a and S5b from the NSVB GTR
/// supplement.
pub fn stem_volume_ratio(spcd: u16, ht_ratio: f64, division: Option<&str>) -> Result<f64, String> {
    let div = division.unwrap_or("default");
    let model = species::get_model(spcd, Model::StemTotalVolumeRatio, div)?;
    Ok(eqns::volume_ratio(ht_ratio, model.coefs[0], model.coefs[1]))
}

/// Calculate the total above ground dry biomass in pounds. This include stem wood
/// and bark, and branch wood and bark. It does not include foliage.
///
/// # Arguments
///
/// * `spcd` - FIA species code
/// * `dia` - Diameter at breast height (in)
/// * `ht` - Total tree height (ft)
/// * `division` - Optional ecodivision code
///
/// # Examples
///
/// ```
/// use nsvb;
///
/// let biomass = nsvb::total_biomass(202, 20.0, 110.0, Some("240")).unwrap();
/// assert_eq!(biomass, 3154.553996629238);
/// ```
///
/// # Notes
///
/// This function queries coefficients from Table S8a and S8b from the NSVB GTR
/// supplement.
pub fn total_biomass(spcd: u16, dia: f64, ht: f64, division: Option<&str>) -> Result<f64, String> {
    let div = division.unwrap_or("default");
    let model = species::get_model(spcd, Model::TotalBiomass, div)?;
    Ok(eqns::weight_volume(dia, ht, model.form, &model.coefs))
}

/// Calculate the total bark biomass in pounds.
///
/// # Arguments
///
/// * `spcd` - FIA species code
/// * `dia` - Diameter at breast height (in)
/// * `ht` - Total tree height (ft)
/// * `division` - Optional ecodivision code
///
/// # Examples
///
/// ```
/// use nsvb;
///
/// let biomass = nsvb::bark_biomass(202, 20.0, 110.0, Some("240")).unwrap();
/// assert_eq!(biomass, 361.7824889136451);
/// ```
///
/// # Notes
///
/// This function queries coefficients from Table S6a and S6b from the NSVB GTR
/// supplement.
pub fn bark_biomass(spcd: u16, dia: f64, ht: f64, division: Option<&str>) -> Result<f64, String> {
    let div = division.unwrap_or("default");
    let model = species::get_model(spcd, Model::BarkBiomass, div)?;
    Ok(eqns::weight_volume(dia, ht, model.form, &model.coefs))
}

/// Calculate the total branch biomass in pounds.
///
/// # Arguments
///
/// * `spcd` - FIA species code
/// * `dia` - Diameter at breast height (in)
/// * `ht` - Total tree height (ft)
/// * `division` - Optional ecodivision code
///
/// # Examples
///
/// ```
/// use nsvb;
///
/// let biomass = nsvb::branch_biomass(202, 20.0, 110.0, Some("240")).unwrap();
/// assert_eq!(biomass, 277.4877562341372);
/// ```
///
/// # Notes
///
/// This function queries coefficients from Table S7a and S7b from the NSVB GTR
/// supplement.
pub fn branch_biomass(spcd: u16, dia: f64, ht: f64, division: Option<&str>) -> Result<f64, String> {
    let div = division.unwrap_or("default");
    let model = species::get_model(spcd, Model::BranchBiomass, div)?;
    Ok(eqns::weight_volume(dia, ht, model.form, &model.coefs))
}

/// Calculate the total foliage dry biomass in pounds.
///
/// # Arguments
///
/// * `spcd` - FIA species code
/// * `dia` - Diameter at breast height (in)
/// * `ht` - Total tree height (ft)
/// * `division` - Optional ecodivision code
///
/// # Examples
///
/// ```
/// use nsvb;
///
/// let biomass = nsvb::foliage_biomass(202, 20.0, 110.0, Some("240")).unwrap();
/// assert_eq!(biomass, 83.63478892024017);
/// ```
///
/// # Notes
///
/// This function queries coefficients from Table S9a and S9b from the NSVB GTR
/// supplement.
pub fn foliage_biomass(
    spcd: u16,
    dia: f64,
    ht: f64,
    division: Option<&str>,
) -> Result<f64, String> {
    let div = division.unwrap_or("default");
    let model = species::get_model(spcd, Model::FoliageBiomass, div)?;
    Ok(eqns::weight_volume(dia, ht, model.form, &model.coefs))
}
