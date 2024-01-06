// extern crate nsvb;

// use assert_approx_eq::assert_approx_eq;
// use nsvb::tree;

// #[test]
// fn test_example_1() {
//     // Data from example 1 in the NSVB manual
//     let spcd = 202;
//     let division = "240";
//     let dia = 20.0;
//     let ht = 110.0;
//     let cull = 0.0;

//     let decay = tree::Decay::new(spcd);

//     // Step 1
//     let v_tot_ib_gross = tree::gross_stem_vol_ib(spcd, division, dia, ht);
//     assert_approx_eq!(v_tot_ib_gross, 88.45227554428, 1e-2);

//     // Step 2
//     let v_tot_bk_gross = tree::gross_stem_vol_bk(spcd, division, dia, ht);
//     assert_approx_eq!(v_tot_bk_gross, 13.191436232306, 1e-2);

//     // Step 3
//     let v_tot_ob_gross = v_tot_ib_gross + v_tot_bk_gross;
//     assert_approx_eq!(v_tot_ob_gross, 101.643711776594, 1e-2);

//     // Step 4
//     let hm = tree::height_to_diameter(spcd, division, dia, ht, 4.0);
//     assert_approx_eq!(hm, 98.28126765402, 1e-2);
//     let hs = tree::height_to_diameter(spcd, division, dia, ht, 7.0);
//     assert_approx_eq!(hs, 83.785181046, 1e-2);

//     // Step 5
//     let r1 = tree::volume_ratio(spcd, division, 1.0, ht);
//     assert_approx_eq!(r1, 0.024198309503, 1e-2);
//     let rm = tree::volume_ratio(spcd, division, hm, ht);
//     assert_approx_eq!(rm, 0.993406175350, 1e-2);
//     let rs = tree::volume_ratio(spcd, division, hs, ht);
//     assert_approx_eq!(rs, 0.960553392655, 1e-2);
//     let v_mer_ib_gross = (rm * v_tot_ib_gross) - (r1 * v_tot_ib_gross);
//     assert_approx_eq!(v_mer_ib_gross, 85.728641209612, 1e-2);
//     let v_mer_ob_gross = (rm * v_tot_ob_gross) - (r1 * v_tot_ob_gross);
//     assert_approx_eq!(v_mer_ob_gross, 98.513884967785, 1e-2);
//     let v_mer_bk_gross = v_mer_ob_gross - v_mer_ib_gross;
//     assert_approx_eq!(v_mer_bk_gross, 12.785243758174, 1e-2);
//     let v_saw_ib_gross = (rs * v_tot_ib_gross) - (r1 * v_tot_ib_gross);
//     assert_approx_eq!(v_saw_ib_gross, 82.822737822255, 1e-2);
//     let v_saw_ob_gross = (rs * v_tot_ob_gross) - (r1 * v_tot_ob_gross);
//     assert_approx_eq!(v_saw_ob_gross, 95.174606192451, 1e-2);
//     let v_saw_bk_gross = v_saw_ob_gross - v_saw_ib_gross;
//     assert_approx_eq!(v_saw_bk_gross, 12.351868370196, 1e-2);
//     let v_stump_ob_gross = r1 * v_tot_ob_gross;
//     assert_approx_eq!(v_stump_ob_gross, 2.459605996608, 1e-2);
//     let v_stump_ib_gross = r1 * v_tot_ib_gross;
//     assert_approx_eq!(v_stump_ib_gross, 2.140395539869, 1e-2);
//     let v_stump_bk_gross = v_stump_ob_gross - v_stump_ib_gross;
//     assert_approx_eq!(v_stump_bk_gross, 0.319210456739, 1e-2);
//     let v_top_ob_gross = v_tot_ob_gross - v_mer_ob_gross - v_stump_ob_gross;
//     assert_approx_eq!(v_top_ob_gross, 0.670220812201, 1e-2);
//     let v_top_ib_gross = v_tot_ib_gross - v_mer_ib_gross - v_stump_ib_gross;
//     assert_approx_eq!(v_top_ib_gross, 0.583238794807, 1e-2);
//     let v_top_bk_gross = v_top_ob_gross - v_top_ib_gross;
//     assert_approx_eq!(v_top_bk_gross, 0.086982017394, 1e-2);

//     // Step 6
//     let v_tot_ib_sound = v_tot_ib_gross * (1.0 - cull / 100.0);
//     assert_approx_eq!(v_tot_ib_sound, 88.452275544288, 1e-2);
//     let v_tot_ob_sound = v_tot_ib_sound + v_tot_bk_gross;
//     assert_approx_eq!(v_tot_ob_sound, 101.643711776594, 1e-2);

//     // Step 7
//     let w_tot_ib = v_tot_ib_gross * tree::wood_specific_gravity(spcd) * 62.4;
//     assert_approx_eq!(w_tot_ib, 2483.739897283610, 1e-2);
//     let w_tot_ib_red = v_tot_ib_gross
//         * (1.0 - cull / 100.0 * (1.0 - decay.get_wood_density_proportion(3).unwrap_or(1.0)))
//         * tree::wood_specific_gravity(spcd)
//         * 62.4;
//     assert_approx_eq!(w_tot_ib_red, 2483.739897283610, 1e-2);

//     // Step 8
//     let w_tot_bk = tree::stem_bark_biomass(spcd, division, dia, ht);
//     assert_approx_eq!(w_tot_bk, 361.782496100100, 1e-2);

//     // Step 9
//     let w_branch = tree::branch_biomass(spcd, division, dia, ht);
//     assert_approx_eq!(w_branch, 277.487756904646, 1e-2);

//     // Step 10
//     let abg_predicted = tree::above_groud_biomass(spcd, division, dia, ht);
//     assert_approx_eq!(abg_predicted, 3154.5539926725, 1e-2);
//     let agb_component_red = w_tot_ib_red + w_tot_bk + w_branch;
//     assert_approx_eq!(agb_component_red, 3123.010150288360, 1e-2);

//     // Step 11
//     let agb_reduce = agb_component_red / (w_tot_ib + w_tot_bk + w_branch);
//     assert_approx_eq!(agb_reduce, 1.000000000000, 1e-2);
//     let agb_predicted_red = abg_predicted * agb_reduce;
//     assert_approx_eq!(agb_predicted_red, 3154.5539926725, 1e-2);
//     let agb_diff = agb_predicted_red - agb_component_red;
//     assert_approx_eq!(agb_diff, 31.543842384153, 1e-2);

//     // Step 12
//     let wood_harmonized = agb_predicted_red * (w_tot_ib_red / agb_component_red);
//     assert_approx_eq!(wood_harmonized, 2508.826815376370, 1e-2);
//     let bark_harmonized = agb_predicted_red * (w_tot_bk / agb_component_red);
//     assert_approx_eq!(bark_harmonized, 365.436666110811, 1e-2);
//     let branch_harmonized = agb_predicted_red * (w_branch / agb_component_red);
//     assert_approx_eq!(branch_harmonized, 280.290511185328, 1e-2);

//     // Step 13
//     let wdsg_adj = wood_harmonized / v_tot_ib_gross / 62.4;
//     assert_approx_eq!(wdsg_adj, 0.454545207473, 1e-2);
//     let w_mer_ib = v_mer_ib_gross * wdsg_adj * 62.4;
//     assert_approx_eq!(w_mer_ib, 2431.57468351127, 1e-2);
//     let w_stump_ib = v_stump_ib_gross * wdsg_adj * 62.4;
//     assert_approx_eq!(w_stump_ib, 60.709367768006, 1e-2);

//     // Step 14
//     let bksg_adj = bark_harmonized / v_tot_bk_gross / 62.4;
//     assert_approx_eq!(bksg_adj, 0.4439514186, 1e-2);
//     let w_mer_bk = v_mer_bk_gross * bksg_adj * 62.4;
//     assert_approx_eq!(w_mer_bk, 354.184091263592, 1e-2);
//     let w_stump_bk = v_stump_bk_gross * bksg_adj * 62.4;
//     assert_approx_eq!(w_stump_bk, 8.842949550309, 1e-2);
//     let w_mer_ob = w_mer_ib + w_mer_bk;
//     assert_approx_eq!(w_mer_ob, 2785.75877477486, 1e-2);
//     let w_stump_ob = w_stump_ib + w_stump_bk;
//     assert_approx_eq!(w_stump_ob, 69.552317318315, 1e-2);
//     let drybio_top = agb_predicted_red - w_mer_ob - w_stump_ob;
//     assert_approx_eq!(drybio_top, 299.242900579325, 1e-2);

//     // Step 15
//     let w_foliage = tree::foilage_biomass(spcd, division, dia, ht);
//     assert_approx_eq!(w_foliage, 83.634788855934, 1e-2);

//     // Step 16
//     let c = agb_predicted_red * tree::carbon_fraction(spcd);
//     assert_approx_eq!(c, 1626.474894645920, 1e-2);
// }

// #[test]
// fn test_example_2() {
//     // Data from example 2 in the NSVB manual
//     let spcd = 316;
//     let division = "M210";
//     let dia = 11.1;
//     let ht = 38.0;
//     let cull = 3.0;

//     let decay = tree::Decay::new(spcd);

//     // Step 1
//     let v_tot_ib_gross = tree::gross_stem_vol_ib(spcd, division, dia, ht);
//     assert_approx_eq!(v_tot_ib_gross, 9.427112777611, 1e-2);

//     // Step 2
//     let v_tot_bk_gross = tree::gross_stem_vol_bk(spcd, division, dia, ht);
//     assert_approx_eq!(v_tot_bk_gross, 2.155106401987, 1e-2);

//     // Step 3
//     let v_tot_ob_gross = v_tot_ib_gross + v_tot_bk_gross;
//     assert_approx_eq!(v_tot_ob_gross, 11.582219179599, 1e-2);

//     // Step 4
//     let hm = tree::height_to_diameter(spcd, division, dia, ht, 4.0);
//     assert_approx_eq!(hm, 28.047839250135, 1e-2);
//     let hs = tree::height_to_diameter(spcd, division, dia, ht, 9.0);
//     assert_approx_eq!(hs, 9.98078332380462, 1e-2);

//     // Step 5
//     let r1 = tree::volume_ratio(spcd, division, 1.0, ht);
//     assert_approx_eq!(r1, 0.091117585499, 1e-2);
//     let rm = tree::volume_ratio(spcd, division, hm, ht);
//     assert_approx_eq!(rm, 0.970485778632, 1e-2);
//     let rs = tree::volume_ratio(spcd, division, hs, ht);
//     assert_approx_eq!(rs, 0.580175217851, 1e-2);
//     let v_mer_ib_gross = (rm * v_tot_ib_gross) - (r1 * v_tot_ib_gross);
//     assert_approx_eq!(v_mer_ib_gross, 8.289903129704, 1e-2);
//     let v_mer_ob_gross = (rm * v_tot_ob_gross) - (r1 * v_tot_ob_gross);
//     assert_approx_eq!(v_mer_ob_gross, 10.185035152427, 1e-2);
//     let v_mer_bk_gross = v_mer_ob_gross - v_mer_ib_gross;
//     assert_approx_eq!(v_mer_bk_gross, 1.895132022724, 1e-2);
//     let v_saw_ib_gross = (rs * v_tot_ib_gross) - (r1 * v_tot_ib_gross);
//     assert_approx_eq!(v_saw_ib_gross, 4.610401454934, 1e-2);
//     let v_saw_ob_gross = (rs * v_tot_ob_gross) - (r1 * v_tot_ob_gross);
//     assert_approx_eq!(v_saw_ob_gross, 5.664372689357, 1e-2);
//     let v_saw_bk_gross = v_saw_ob_gross - v_saw_ib_gross;
//     assert_approx_eq!(v_saw_bk_gross, 1.053971234423, 1e-2);
//     let v_stump_ob_gross = r1 * v_tot_ob_gross;
//     assert_approx_eq!(v_stump_ob_gross, 1.055343846369, 1e-2);
//     let v_stump_ib_gross = r1 * v_tot_ib_gross;
//     assert_approx_eq!(v_stump_ib_gross, 0.858975754526, 1e-2);
//     let v_stump_bk_gross = v_stump_ob_gross - v_stump_ib_gross;
//     assert_approx_eq!(v_stump_bk_gross, 0.196368091843, 1e-2);
//     let v_top_ob_gross = v_tot_ob_gross - v_mer_ob_gross - v_stump_ob_gross;
//     assert_approx_eq!(v_top_ob_gross, 0.341840180802, 1e-2);
//     let v_top_ib_gross = v_tot_ib_gross - v_mer_ib_gross - v_stump_ib_gross;
//     assert_approx_eq!(v_top_ib_gross, 0.278233893382, 1e-2);
//     let v_top_bk_gross = v_top_ob_gross - v_top_ib_gross;
//     assert_approx_eq!(v_top_bk_gross, 0.06360628742, 1e-2);

//     // Step 6
//     let v_tot_ib_sound = v_tot_ib_gross * (1.0 - cull / 100.0);
//     assert_approx_eq!(v_tot_ib_sound, 9.144299394283, 1e-2);
//     let v_tot_ob_sound = v_tot_ib_sound + v_tot_bk_gross;
//     assert_approx_eq!(v_tot_ob_sound, 11.299405796270, 1e-2);

//     // Step 7
//     let w_tot_ib = v_tot_ib_gross * tree::wood_specific_gravity(spcd) * 62.4;
//     assert_approx_eq!(w_tot_ib, 288.243400288234, 1e-2);
//     let w_tot_ib_red = v_tot_ib_gross
//         * (1.0 - cull / 100.0 * (1.0 - decay.get_wood_density_proportion(3).unwrap_or(1.0)))
//         * tree::wood_specific_gravity(spcd)
//         * 62.4;
//     assert_approx_eq!(w_tot_ib_red, 284.265641364256, 1e-2);

//     // Step 8
//     let w_tot_bk = tree::stem_bark_biomass(spcd, division, dia, ht);
//     assert_approx_eq!(w_tot_bk, 52.945466015848, 1e-2);
//     let w_tot_ob_red = w_tot_ib_red + w_tot_bk;
//     assert_approx_eq!(w_tot_ob_red, 337.211107380104, 1e-2);

//     // Step 9
//     let w_branch = tree::branch_biomass(spcd, division, dia, ht);
//     assert_approx_eq!(w_branch, 135.001927997271, 1e-2);

//     // Step 10
//     let abg_predicted = tree::above_groud_biomass(spcd, division, dia, ht);
//     assert_approx_eq!(abg_predicted, 532.584798820042, 1e-2);
//     let agb_component_red = w_tot_ib_red + w_tot_bk + w_branch;
//     assert_approx_eq!(agb_component_red, 472.213035377375, 1e-2);

//     // Step 11
//     let agb_reduce = agb_component_red / (w_tot_ib + w_tot_bk + w_branch);
//     assert_approx_eq!(agb_reduce, 0.991646711840, 1e-2);
//     let agb_predicted_red = abg_predicted * agb_reduce;
//     assert_approx_eq!(agb_predicted_red, 528.135964525863, 1e-2);
//     let agb_diff = agb_predicted_red - agb_component_red;
//     assert_approx_eq!(agb_diff, 55.922929148488, 1e-2);

//     // Step 12
//     let wood_harmonized = agb_predicted_red * (w_tot_ib_red / agb_component_red);
//     assert_approx_eq!(wood_harmonized, 317.930462388645, 1e-2);
//     let bark_harmonized = agb_predicted_red * (w_tot_bk / agb_component_red);
//     assert_approx_eq!(bark_harmonized, 59.215656211618, 1e-2);
//     let branch_harmonized = agb_predicted_red * (w_branch / agb_component_red);
//     assert_approx_eq!(branch_harmonized, 150.989845925600, 1e-2);

//     // Step 13
//     let wdsg_adj = wood_harmonized / v_tot_ib_gross / 62.4;
//     assert_approx_eq!(wdsg_adj, 0.540466586276, 1e-2);
//     let w_mer_ib = v_mer_ib_gross * wdsg_adj * 62.4;
//     assert_approx_eq!(w_mer_ib, 279.577936252521, 1e-2);
//     let w_stump_ib = v_stump_ib_gross * wdsg_adj * 62.4;
//     assert_approx_eq!(w_stump_ib, 28.969056089533, 1e-2);

//     // Step 14
//     let bksg_adj = bark_harmonized / v_tot_bk_gross / 62.4;
//     assert_approx_eq!(bksg_adj, 0.440335033421, 1e-2);
//     let w_mer_bk = v_mer_bk_gross * bksg_adj * 62.4;
//     assert_approx_eq!(w_mer_bk, 52.072364607955, 1e-2);
//     let w_stump_bk = v_stump_bk_gross * bksg_adj * 62.4;
//     assert_approx_eq!(w_stump_bk, 5.395587617753, 1e-2);
//     let w_mer_ob = w_mer_ib + w_mer_bk;
//     assert_approx_eq!(w_mer_ob, 331.650300860476, 1e-2);
//     let w_stump_ob = w_stump_ib + w_stump_bk;
//     assert_approx_eq!(w_stump_ob, 34.364643707286, 1e-2);
//     let drybio_top = agb_predicted_red - w_mer_ob - w_stump_ob;
//     assert_approx_eq!(drybio_top, 162.121019958101, 1e-2);

//     // Step 15
//     let w_foliage = tree::foilage_biomass(spcd, division, dia, ht);
//     assert_approx_eq!(w_foliage, 22.807960563788, 1e-2);

//     // Step 16
//     let c = agb_predicted_red * tree::carbon_fraction(spcd);
//     assert_approx_eq!(c, 256.533242502186, 1e-2);
// }

// #[test]
// fn test_example_3() {
//     // Data from example 3 in the NSVB manual
//     let spcd = 631;
//     let division = "M240";
//     let dia = 11.3;
//     let ht = 28.0;
//     let actual_ht = 21.0;
//     let cull = 10.0;
//     let decay_class = 2;

//     let decay = tree::Decay::new(spcd);

//     // Step 1
//     let v_tot_ib_gross = tree::gross_stem_vol_ib(spcd, division, dia, ht);
//     assert_approx_eq!(v_tot_ib_gross, 7.283117547652, 1e-2);

//     // Step 2
//     let v_tot_bk_gross = tree::gross_stem_vol_bk(spcd, division, dia, ht);
//     assert_approx_eq!(v_tot_bk_gross, 1.907136145131, 1e-2);

//     // Step 3
//     let v_tot_ob_gross = v_tot_ib_gross + v_tot_bk_gross;
//     assert_approx_eq!(v_tot_ob_gross, 9.190253692783, 1e-2);

//     // Step 4
//     let hm = tree::height_to_diameter(spcd, division, dia, ht, 4.0);
//     assert_approx_eq!(hm, 21.790361419761, 1e-2);
//     let hs = tree::height_to_diameter(spcd, division, dia, ht, 9.0);
//     assert_approx_eq!(hs, 8.10427459853, 1e-2);

//     // Step 5
//     let r1 = tree::volume_ratio(spcd, division, 1.0, ht);
//     assert_approx_eq!(r1, 0.124985332188, 1e-2);
//     let rm = tree::volume_ratio(spcd, division, hm, ht);
//     assert_approx_eq!(rm, 0.975933190572, 1e-2);
//     let rs = tree::volume_ratio(spcd, division, hs, ht);
//     assert_approx_eq!(rs, 0.610622756652, 1e-2);
//     let v_mer_ib_gross = (rm * v_tot_ib_gross) - (r1 * v_tot_ib_gross);
//     assert_approx_eq!(v_mer_ib_gross, 6.197553279533, 1e-2);
//     let v_mer_ob_gross = (rm * v_tot_ob_gross) - (r1 * v_tot_ob_gross);
//     assert_approx_eq!(v_mer_ob_gross, 7.820426697879, 1e-2);
//     let v_mer_bk_gross = v_mer_ob_gross - v_mer_ib_gross;
//     assert_approx_eq!(v_mer_bk_gross, 1.622873418346, 1e-2);
//     let v_saw_ib_gross = (rs * v_tot_ib_gross) - (r1 * v_tot_ib_gross);
//     assert_approx_eq!(v_saw_ib_gross, 3.536954447910, 1e-2);
//     let v_saw_ob_gross = (rs * v_tot_ob_gross) - (r1 * v_tot_ob_gross);
//     assert_approx_eq!(v_saw_ob_gross, 4.463131133534, 1e-2);
//     let v_saw_bk_gross = v_saw_ob_gross - v_saw_ib_gross;
//     assert_approx_eq!(v_saw_bk_gross, 0.926176685624, 1e-2);
//     let v_stump_ob_gross = r1 * v_tot_ob_gross;
//     assert_approx_eq!(v_stump_ob_gross, 1.148646910689, 1e-2);
//     let v_stump_ib_gross = r1 * v_tot_ib_gross;
//     assert_approx_eq!(v_stump_ib_gross, 0.910282866061, 1e-2);
//     let v_stump_bk_gross = v_stump_ob_gross - v_stump_ib_gross;
//     assert_approx_eq!(v_stump_bk_gross, 0.238364044628, 1e-2);
//     // let v_top_ob_gross = v_tot_ob_gross - v_mer_ob_gross - v_stump_ob_gross;
//     // assert_approx_eq!(v_top_ob_gross, 0.341840180802, 1e-2);
//     // let v_top_ib_gross = v_tot_ib_gross - v_mer_ib_gross - v_stump_ib_gross;
//     // assert_approx_eq!(v_top_ib_gross, 0.278233893382, 1e-2);
//     // let v_top_bk_gross = v_top_ob_gross - v_top_ib_gross;
//     // assert_approx_eq!(v_top_bk_gross, 0.06360628742, 1e-2);

//     // Step 6
//     let rm_sound = tree::volume_ratio(spcd, division, actual_ht, ht);
//     let v_mer_ib_sound =
//         ((rm_sound * v_tot_ib_gross) - (r1 * v_tot_ib_gross)) * (1.0 - cull / 100.0);
//     assert_approx_eq!(v_mer_ib_sound, 5.526235794852, 1e-2);
//     let v_mer_bk_sound = (rm_sound * v_tot_bk_gross) - (r1 * v_tot_bk_gross);
//     assert_approx_eq!(v_mer_bk_sound, 1.607871287707, 1e-2);
//     let v_mer_ob_sound = v_mer_ib_sound + v_mer_bk_sound;
//     assert_approx_eq!(v_mer_ob_sound, 7.134107082559, 1e-2);
//     let v_stump_ib_sound = v_stump_ib_gross * (1.0 - cull / 100.0);
//     assert_approx_eq!(v_stump_ib_sound, 0.819254579455, 1e-2);
//     let v_stump_ob_sound = v_stump_ib_sound + v_stump_bk_gross;
//     assert_approx_eq!(v_stump_ob_sound, 1.057618624083, 1e-2);
//     let v_tot_ob_sound = v_mer_ob_sound + v_stump_ob_sound;
//     assert_approx_eq!(v_tot_ob_sound, 8.191725706642, 1e-2);
//     let v_tot_ib_sound = v_mer_ib_sound + v_stump_ib_sound;
//     assert_approx_eq!(v_tot_ib_sound, 6.345490374317, 1e-2);
//     let v_tot_bk_sound = v_tot_ob_sound - v_tot_ib_sound;
//     assert_approx_eq!(v_tot_bk_sound, 1.846235332335, 1e-2);
//     let v_top_ob_sound = v_tot_ob_sound - v_mer_ob_sound - v_stump_ob_sound;
//     assert_approx_eq!(v_top_ob_sound, 0.000000000000, 1e-2);
//     let v_top_ib_sound = v_tot_ib_sound - v_mer_ib_sound - v_stump_ib_sound;
//     assert_approx_eq!(v_top_ib_sound, 0.000000000000, 1e-2);
//     let v_top_bk_sound = v_top_ob_sound - v_top_ib_sound;
//     assert_approx_eq!(v_top_bk_sound, 0.000000000000, 1e-2);

//     // Step 7
//     let w_tot_ib = v_tot_ib_gross * tree::wood_specific_gravity(spcd) * 62.4;
//     assert_approx_eq!(w_tot_ib, 263.590590284621, 1e-2);
//     let w_tot_ib_red = v_tot_ib_sound / (1.0 - cull / 100.0)
//         * (decay
//             .get_wood_density_proportion(decay_class)
//             .unwrap_or(1.0))
//         * tree::wood_specific_gravity(spcd)
//         * 62.4;
//     assert_approx_eq!(w_tot_ib_red, 204.13865566837, 1e-2);

//     // Step 8
//     let w_tot_bk = tree::stem_bark_biomass(spcd, division, dia, ht);
//     assert_approx_eq!(w_tot_bk, 46.816664266025, 1e-2);
//     let w_tot_bk_red = w_tot_bk
//         * rm_sound
//         * (decay
//             .get_remaining_bark_proportion(decay_class)
//             .unwrap_or(1.0))
//         * decay
//             .get_wood_density_proportion(decay_class)
//             .unwrap_or(1.0);
//     assert_approx_eq!(w_tot_bk_red, 29.005863664008, 1e-2);
//     let w_tot_ob_red = w_tot_ib_red + w_tot_bk;
//     assert_approx_eq!(w_tot_ob_red, 250.9552877717427, 1e-2);

//     // Step 9
//     let w_branch = tree::branch_biomass(spcd, division, dia, ht);
//     assert_approx_eq!(w_branch, 226.788002348975, 1e-2);
//     // =========================================================================
//     // START BACK HERE WHEN CONTINUING WORK ON TESTS
//     // TODO: We need clarification from FS about the MEAN_CR table (S11).
//     // =========================================================================
//     let cr = tree::mean_crown_ratio(spcd, division);
//     let branch_rem = (actual_ht - ht * (1.0 - cr)) / (ht * cr);
//     assert_approx_eq!(branch_rem, 0.338624338624, 1e-2);
// }
