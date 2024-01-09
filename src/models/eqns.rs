// Model 1
fn schumacher_hall(dia: f64, ht: f64, a: f64, b: f64, c: f64) -> f64 {
    return a * dia.powf(b) * ht.powf(c);
}

// Model 2
fn segmented(dia: f64, ht: f64, a: f64, b: f64, b1: f64, c: f64, k: f64) -> f64 {
    if dia < k {
        return a * dia.powf(b) * ht.powf(c);
    } else {
        return a * k.powf(b - b1) * dia.powf(b1) * ht.powf(c);
    }
}

// Model 3
fn continuously_varible(dia: f64, ht: f64, a: f64, a1: f64, b: f64, c: f64, c1: f64) -> f64 {
    return a * dia.powf(a1 * (1.0 - (-b * dia).exp()).powf(c1)) * ht.powf(c);
}

// Model 4
fn modified_wiley(dia: f64, ht: f64, a: f64, b: f64, b1: f64, c: f64) -> f64 {
    return a * dia.powf(b) * ht.powf(c) * (-(b1 * dia)).exp();
}

// Model 5
fn modified_schumacher_hall(dia: f64, ht: f64, a: f64, b: f64, c: f64, wdsg: f64) -> f64 {
    return a * dia.powf(b) * ht.powf(c) * wdsg;
}

// Weight-volume models
pub fn weight_volume(dia: f64, ht: f64, form: u8, coefs: &Vec<f64>) -> f64 {
    match form {
        1 => schumacher_hall(dia, ht, coefs[0], coefs[1], coefs[2]),
        2 => segmented(dia, ht, coefs[0], coefs[1], coefs[2], coefs[3], coefs[4]),
        3 => continuously_varible(dia, ht, coefs[0], coefs[1], coefs[2], coefs[3], coefs[4]),
        4 => modified_wiley(dia, ht, coefs[0], coefs[1], coefs[2], coefs[3]),
        5 => modified_schumacher_hall(dia, ht, coefs[0], coefs[1], coefs[2], coefs[3]),
        _ => panic!("Model not found"),
    }
}

// Volume ratio model (Model 6)
pub fn volume_ratio(ht_ratio: f64, alpha: f64, beta: f64) -> f64 {
    return (1.0 - (1.0 - ht_ratio).powf(alpha)).powf(beta);
}

pub fn height(dia: f64, coefs: &Vec<f64>) -> f64 {
    return coefs[6] * dia.powf(coefs[7]);
}

pub fn height_lri(dia: f64, lri: f64, coefs: &Vec<f64>) -> f64 {
    let a = coefs[0] * lri + coefs[4] * (1.0 - lri);
    let b = coefs[1] * lri + coefs[5] * (1.0 - lri);
    return a * dia.powf(b);
}

pub fn diameter_at_height(
    dia: f64,
    ht: f64,
    hi: f64,
    volob_coefs: &Vec<f64>,
    ratio_coefs: &Vec<f64>,
) -> f64 {
    let term1 = (volob_coefs[0] * dia.powf(volob_coefs[1]) * ht.powf(volob_coefs[2]) / 0.005454154)
        / ht
        * ratio_coefs[0]
        * ratio_coefs[1];
    let term2 = (1.0 - hi / ht).abs().powf(ratio_coefs[0] - 1.0);
    let term3 = (1.0 - (1.0 - hi / ht).abs().powf(ratio_coefs[0])).powf(ratio_coefs[1] - 1.0);
    (term1 * term2 * term3).powf(0.5)
}

pub fn height_at_diameter(
    dia: f64,
    ht: f64,
    di: f64,
    volob_coefs: &Vec<f64>,
    ratio_coefs: &Vec<f64>,
) -> f64 {
    // Initialize upper and lower bounds
    let mut low = 0.0;
    let mut high = ht;
    let mut hi = (low + high) / 2.0;

    // Iterate until the difference between the top diameter and the desired
    // diameter is less than 0.001
    while high - low > 0.001 {
        hi = (low + high) / 2.0;
        let top_dia = diameter_at_height(dia, ht, hi, volob_coefs, ratio_coefs);

        if (top_dia - di).abs() < 0.001 {
            return hi;
        } else if top_dia > di {
            low = hi;
        } else {
            high = hi;
        }
    }

    hi
}

pub fn dbh_from_stump_dia(
    stump_dia: f64,
    stump_height: f64,
    volob_coefs: &Vec<f64>,
    ratio_coefs: &Vec<f64>,
    height_coefs: &Vec<f64>,
) -> f64 {
    let mut low = 0.0;
    let mut high = stump_dia;
    let mut dbh = (low + high) / 2.0;

    while high - low > 0.001 {
        dbh = (low + high) / 2.0;
        let ht = height(dbh, height_coefs);
        let dia = diameter_at_height(dbh, ht, stump_height, volob_coefs, ratio_coefs);

        if (dia - stump_dia).abs() < 0.001 {
            return dbh;
        } else if dia > stump_dia {
            high = dbh;
        } else {
            low = dbh;
        }
    }

    dbh
}
