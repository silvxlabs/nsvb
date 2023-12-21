mod decay;
mod models;
mod species;

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
            .unwrap_or(species.volob.get("default").unwrap());
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
            .unwrap_or(species.rcumob.get("default").unwrap());
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
        0.0
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

    // Step 3: Gross total stem outside-bark volume

    // Step 4: Heights to merchantable top diameter and, if present, sawlog top diameter

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

#[cfg(test)]
mod tests {
    use super::*;
    use assert_approx_eq::assert_approx_eq;

    #[test]
    fn test_example_1() {
        // Data from example 1 in the NSVB manual
        let spcd = 202;
        let division = "240";
        let dia = 20.0;
        let ht = 110.0;
        let cull = 0.0;

        let decay = decay::Decay::new(spcd);

        // Step 1
        let v_tot_ib_gross = gross_stem_vol_ib(spcd, division, dia, ht);
        assert_approx_eq!(v_tot_ib_gross, 88.45227554428, 1e-2);

        // Step 2
        let v_tot_bk_gross = gross_stem_vol_bk(spcd, division, dia, ht);
        assert_approx_eq!(v_tot_bk_gross, 13.191436232306, 1e-2);

        // Step 3
        let v_tot_ob_gross = v_tot_ib_gross + v_tot_bk_gross;
        assert_approx_eq!(v_tot_ob_gross, 101.643711776594, 1e-2);

        // Step 4
        let hm = height_to_diameter(spcd, division, dia, ht, 4.0);
        assert_approx_eq!(hm, 98.28126765402, 1e-2);
        let hs = height_to_diameter(spcd, division, dia, ht, 7.0);
        assert_approx_eq!(hs, 83.785181046, 1e-2);

        // Step 5
        let r1 = volume_ratio(spcd, division, 1.0, ht);
        assert_approx_eq!(r1, 0.024198309503, 1e-2);
        let rm = volume_ratio(spcd, division, hm, ht);
        assert_approx_eq!(rm, 0.993406175350, 1e-2);
        let rs = volume_ratio(spcd, division, hs, ht);
        assert_approx_eq!(rs, 0.960553392655, 1e-2);
        let v_mer_ib_gross = (rm * v_tot_ib_gross) - (r1 * v_tot_ib_gross);
        assert_approx_eq!(v_mer_ib_gross, 85.728641209612, 1e-2);
        let v_mer_ob_gross = (rm * v_tot_ob_gross) - (r1 * v_tot_ob_gross);
        assert_approx_eq!(v_mer_ob_gross, 98.513884967785, 1e-2);
        let v_mer_bk_gross = v_mer_ob_gross - v_mer_ib_gross;
        assert_approx_eq!(v_mer_bk_gross, 12.785243758174, 1e-2);
        let v_saw_ib_gross = (rs * v_tot_ib_gross) - (r1 * v_tot_ib_gross);
        assert_approx_eq!(v_saw_ib_gross, 82.822737822255, 1e-2);
        let v_saw_ob_gross = (rs * v_tot_ob_gross) - (r1 * v_tot_ob_gross);
        assert_approx_eq!(v_saw_ob_gross, 95.174606192451, 1e-2);
        let v_saw_bk_gross = v_saw_ob_gross - v_saw_ib_gross;
        assert_approx_eq!(v_saw_bk_gross, 12.351868370196, 1e-2);
        let v_stump_ob_gross = r1 * v_tot_ob_gross;
        assert_approx_eq!(v_stump_ob_gross, 2.459605996608, 1e-2);
        let v_stump_ib_gross = r1 * v_tot_ib_gross;
        assert_approx_eq!(v_stump_ib_gross, 2.140395539869, 1e-2);
        let v_stump_bk_gross = v_stump_ob_gross - v_stump_ib_gross;
        assert_approx_eq!(v_stump_bk_gross, 0.319210456739, 1e-2);
        let v_top_ob_gross = v_tot_ob_gross - v_mer_ob_gross - v_stump_ob_gross;
        assert_approx_eq!(v_top_ob_gross, 0.670220812201, 1e-2);
        let v_top_ib_gross = v_tot_ib_gross - v_mer_ib_gross - v_stump_ib_gross;
        assert_approx_eq!(v_top_ib_gross, 0.583238794807, 1e-2);
        let v_top_bk_gross = v_top_ob_gross - v_top_ib_gross;
        assert_approx_eq!(v_top_bk_gross, 0.086982017394, 1e-2);

        // Step 6
        let v_tot_ib_sound = v_tot_ib_gross * (1.0 - cull / 100.0);
        assert_approx_eq!(v_tot_ib_sound, 88.452275544288, 1e-2);
        let v_tot_ob_sound = v_tot_ib_sound + v_tot_bk_gross;
        assert_approx_eq!(v_tot_ob_sound, 101.643711776594, 1e-2);

        let w_tot_ib = v_tot_ib_gross * wood_specief_gravity(spcd) * 62.4;
        assert_approx_eq!(w_tot_ib, 2483.739897283610, 1e-2);
        let w_tot_ib_red = v_tot_ib_gross
            * (1.0 - cull / 100.0 * (decay.get_wood_density_proportion(3).unwrap_or(1.0)))
            * wood_specief_gravity(spcd)
            * 62.4;
        assert_approx_eq!(w_tot_ib_red, 2483.739897283610, 1e-2);

        let w_tot_bk = stem_bark_biomass(spcd, division, dia, ht);
        assert_approx_eq!(w_tot_bk, 361.782496100100, 1e-2);

        let w_branch = branch_biomass(spcd, division, dia, ht);
        assert_approx_eq!(w_branch, 277.487756904646, 1e-2);

        let abg_predicted = above_groud_biomass(spcd, division, dia, ht);
        assert_approx_eq!(abg_predicted, 3154.5539926725, 1e-2);

        let agb_component_red = w_tot_ib_red + w_tot_bk + w_branch;
        assert_approx_eq!(agb_component_red, 3123.010150288360, 1e-2);

        let agb_reduce = agb_component_red / (w_tot_ib + w_tot_bk + w_branch);
        assert_approx_eq!(agb_reduce, 1.000000000000, 1e-2);

        let agb_predicted_red = abg_predicted * agb_reduce;
        assert_approx_eq!(agb_predicted_red, 3154.5539926725, 1e-2);

        let agb_diff = agb_predicted_red - agb_component_red;
        assert_approx_eq!(agb_diff, 31.543842384153, 1e-2);

        let wood_harmonized = agb_predicted_red * (w_tot_ib_red / agb_component_red);
        assert_approx_eq!(wood_harmonized, 2508.826815376370, 1e-2);

        let bark_harmonized = agb_predicted_red * (w_tot_bk / agb_component_red);
        assert_approx_eq!(bark_harmonized, 365.436666110811, 1e-2);

        let branch_harmonized = agb_predicted_red * (w_branch / agb_component_red);
        assert_approx_eq!(branch_harmonized, 280.290511185328, 1e-2);

        let w_foliage = foilage_biomass(spcd, division, dia, ht);
        assert_approx_eq!(w_foliage, 83.634788855934, 1e-2);

        let wdsg_adj = wood_harmonized / v_tot_ib_sound / 62.4;
        assert_approx_eq!(wdsg_adj, 0.454545207473, 1e-2);

        let bksg_adj = bark_harmonized / v_tot_bk_gross / 62.4;
        assert_approx_eq!(bksg_adj, 0.4439514186, 1e-2);

        let w_mer_ib = v_mer_ib_gross * wdsg_adj * 62.4;
        assert_approx_eq!(w_mer_ib, 2431.57468351127, 1e-2);

        let w_mer_bk = v_mer_bk_gross * bksg_adj * 62.4;
        assert_approx_eq!(w_mer_bk, 354.184091263592, 1e-2);

        let w_mer_ob = w_mer_ib + w_mer_bk;
        assert_approx_eq!(w_mer_ob, 2785.75877477486, 1e-2);

        let w_stump_ib = v_stump_ib_gross * wdsg_adj * 62.4;
        assert_approx_eq!(w_stump_ib, 60.709367768006, 1e-2);

        let w_stump_bk = v_stump_bk_gross * bksg_adj * 62.4;
        assert_approx_eq!(w_stump_bk, 8.842949550309, 1e-2);

        let w_stump_ob = w_stump_ib + w_stump_bk;
        assert_approx_eq!(w_stump_ob, 69.552317318315, 1e-2);

        let drybio_top = agb_predicted_red - w_mer_ob - w_stump_ob;
        assert_approx_eq!(drybio_top, 299.242900579325, 1e-2);

        let c = agb_predicted_red * carbon_fraction(spcd);
        assert_approx_eq!(c, 1626.474894645920, 1e-2);
    }
}
