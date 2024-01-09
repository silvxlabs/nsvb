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
/// use vbx;
///
/// let volume = vbx::stem_wood_volume(202, 20.0, 110.0, Some("240")).unwrap();
/// assert_eq!(volume, 88.45229093648126);
/// ```
///
/// # Notes
///
/// This function queries coefficients from Table S1a and S1b from the vbx GTR
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
/// use vbx;
///
/// let volume = vbx::stem_bark_volume(202, 20.0, 110.0, Some("240")).unwrap();
/// assert_eq!(volume, 13.197130062388565);
/// ```
///
/// # Notes
///
/// This function queries coefficients from Table S2a and S2b from the vbx GTR
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

/// Calculate the diameter in inches at a specified height in feet along the stem.
///
/// # Arguments
///
/// * `spcd` - FIA species code
/// * `dia` - Diameter at breast height (in)
/// * `ht` - Total tree height (ft)
/// * `hi` - Height along the stem (ft)
/// * `division` - Optional ecodivision code
///
/// # Examples
///
/// ```
/// use vbx;
///
/// let diameter = vbx::diameter_at_height(202, 20.0, 110.0, 78.32313537597656, None).unwrap();
/// assert_eq!(diameter, 8.999981811805483);
/// ```
pub fn diameter_at_height(
    spcd: u16,
    dia: f64,
    ht: f64,
    hi: f64,
    division: Option<&str>,
) -> Result<f64, String> {
    let div = division.unwrap_or("default");
    let volob_model = species::get_model(spcd, Model::StemTotalVolume, div)?;
    let ratio_model = species::get_model(spcd, Model::StemWoodVolumeRatio, div)?;
    Ok(eqns::diameter_at_height(
        dia,
        ht,
        hi,
        &volob_model.coefs,
        &ratio_model.coefs,
    ))
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
/// use vbx;
///
/// let height = vbx::height_at_diameter(202, 20.0, 110.0, 9.0, None).unwrap();
/// assert_eq!(height, 78.323974609375);
/// ```
///
/// # Notes
///
/// This function queries coefficients from Tabls S3a, S3b, S4a, and S4b from
/// the vbx GTR supplement.
pub fn height_at_diameter(
    spcd: u16,
    dia: f64,
    ht: f64,
    dia_top: f64,
    division: Option<&str>,
) -> Result<f64, String> {
    let div = division.unwrap_or("default");
    let volob_model = species::get_model(spcd, Model::StemTotalVolume, div)?;
    let ratio_model = species::get_model(spcd, Model::StemWoodVolumeRatio, div)?;
    Ok(eqns::height_at_diameter(
        dia,
        ht,
        dia_top,
        &volob_model.coefs,
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
/// use vbx;
///
/// let ratio = vbx::stem_volume_ratio(202, 78.32313537597656/110.0, Some("240")).unwrap();
/// assert_eq!(ratio, 0.9533893700705219);
/// ```
///
/// # Notes
///
/// This function queries coefficients from Tabls S5a and S5b from the vbx GTR
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
/// use vbx;
///
/// let biomass = vbx::total_biomass(202, 20.0, 110.0, Some("240")).unwrap();
/// assert_eq!(biomass, 3154.553996629238);
/// ```
///
/// # Notes
///
/// This function queries coefficients from Table S8a and S8b from the vbx GTR
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
/// use vbx;
///
/// let biomass = vbx::bark_biomass(202, 20.0, 110.0, Some("240")).unwrap();
/// assert_eq!(biomass, 361.7824889136451);
/// ```
///
/// # Notes
///
/// This function queries coefficients from Table S6a and S6b from the vbx GTR
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
/// use vbx;
///
/// let biomass = vbx::branch_biomass(202, 20.0, 110.0, Some("240")).unwrap();
/// assert_eq!(biomass, 277.4877562341372);
/// ```
///
/// # Notes
///
/// This function queries coefficients from Table S7a and S7b from the vbx GTR
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
/// use vbx;
///
/// let biomass = vbx::foliage_biomass(202, 20.0, 110.0, Some("240")).unwrap();
/// assert_eq!(biomass, 83.63478892024017);
/// ```
///
/// # Notes
///
/// This function queries coefficients from Table S9a and S9b from the vbx GTR
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

/// Calculate the height in feet given a diameter at breast height in inches.
///
/// # Arguments
///
/// * `spcd` - FIA species code
/// * `dia` - Diameter at breast height (in)
///
/// # Examples
///
/// ```
/// use vbx;
///
/// let height = vbx::height(202, 20.0).unwrap();
/// assert_eq!(height, 94.4010122345696);
/// ```
pub fn height(spcd: u16, dia: f64) -> Result<f64, String> {
    let model = species::get_model(spcd, Model::HeightDiameter, "default")?;
    Ok(eqns::height(dia, &model.coefs))
}

/// Calculate the height in feet given a diameter at breast height in inches and
/// a light resource index.
///
/// # Arguments
///
/// * `spcd` - FIA species code
/// * `dia` - Diameter at breast height (in)
/// * `lri` - Light resource index
///
/// # Examples
///
/// ```
/// use vbx;
///
/// let height = vbx::height_lri(202, 20.0, 0.375).unwrap();
/// assert_eq!(height, 110.1549613551761);
/// ```
pub fn height_lri(spcd: u16, dia: f64, lri: f64) -> Result<f64, String> {
    let model = species::get_model(spcd, Model::HeightDiameter, "default")?;
    Ok(eqns::height_lri(dia, lri, &model.coefs))
}

/// Calculate the light resource index given a diameter at breast height in
/// inches and a target height in feet.
///
/// # Arguments
///
/// * `spcd` - FIA species code
/// * `dia` - Diameter at breast height (in)
/// * `target_ht` - Target height (ft)
///
/// # Examples
///
/// ```
/// use vbx;
///
/// let lri = vbx::find_lri(202, 20.0, 110.1549613551761);
/// assert_eq!(lri, 0.375);
/// ```
///
/// # Notes
///
/// This function uses the bisection method to find the light resource index
/// that results in the target height. The bisection method is used because the
/// height to diameter equation is not easily invertible. In a future release
/// we will update this function to use a derivative-based method to improve
/// speed of convergence.
pub fn find_lri(spcd: u16, dia: f64, target_ht: f64) -> f64 {
    // TODO: Move to eqns.rs
    // Initialize upper and lower bounds
    let mut low = 0.0;
    let mut high = 1.0;
    // Initial guess for light resource index
    let mut lri = (low + high) / 2.0;

    // Iterate until the height is within 0.01 ft of the target height
    while high - low > 0.01 {
        lri = (low + high) / 2.0;
        let ht = height_lri(spcd, dia, lri).unwrap();

        if (ht - target_ht).abs() < 0.01 {
            return lri;
        } else if ht > target_ht {
            low = lri;
        } else {
            high = lri;
        }
    }

    lri
}

/// Calculate the diameter at breast height in inches given a stump diameter in
/// inches and a stump height in feet.
///
/// # Arguments
///
/// * `spcd` - FIA species code
/// * `stump_dia` - Stump diameter (in)
/// * `stump_height` - Stump height (ft)
/// * `division` - Optional ecodivision code
///
/// # Examples
///
/// ```
/// use vbx;
///
/// let dbh = vbx::dbh_from_stump_dia(242, 22.0, 1.0, Some("240")).unwrap();
/// assert_eq!(dbh, 20.0);
/// ```
pub fn dbh_from_stump_dia(
    spcd: u16,
    stump_dia: f64,
    stump_height: f64,
    division: Option<&str>,
) -> Result<f64, String> {
    let div = division.unwrap_or("default");
    let volob_model = species::get_model(spcd, Model::StemTotalVolume, div)?;
    let ratio_model = species::get_model(spcd, Model::StemWoodVolumeRatio, div)?;
    let height_model = species::get_model(spcd, Model::HeightDiameter, div)?;
    Ok(eqns::dbh_from_stump_dia(
        stump_dia,
        stump_height,
        &volob_model.coefs,
        &ratio_model.coefs,
        &height_model.coefs,
    ))
}

//==============================================================================
// Species properties
//==============================================================================
pub fn carbon_fraction(spcd: u16) -> Result<f64, String> {
    species::get_property(spcd, species::structs::Property::CarbonFraction)
}

pub fn wood_specific_gravity(spcd: u16) -> Result<f64, String> {
    species::get_property(spcd, species::structs::Property::WoodSpecificGravity)
}

pub fn bark_specific_gravity(spcd: u16) -> Result<f64, String> {
    species::get_property(spcd, species::structs::Property::BarkSpecificGravity)
}
