use argmin::core::Executor;
use argmin::core::{CostFunction, Error};
use argmin::solver::neldermead::NelderMead;

#[derive(Default)]
struct HeightToDiameter {
    dia: f64,
    ht: f64,
    d_i: f64,
    a: f64,
    b: f64,
    c: f64,
    alpha: f64,
    beta: f64,
}

impl CostFunction for HeightToDiameter {
    type Param = f64;
    type Output = f64;

    fn cost(&self, h_i: &Self::Param) -> Result<Self::Output, Error> {
        let term1 = (self.a * self.dia.powf(self.b) * self.ht.powf(self.c) / 0.005454154) / self.ht
            * self.alpha
            * self.beta;
        let term2 = (1.0 - h_i / self.ht).abs().powf(self.alpha - 1.0);
        let term3 = (1.0 - (1.0 - h_i / self.ht).abs().powf(self.alpha)).powf(self.beta - 1.0);
        Ok((self.d_i - (term1 * term2 * term3).powf(0.5)).abs())
    }
}

pub fn height_to_diameter(
    dia: f64,
    ht: f64,
    d_i: f64,
    volob_coefs: &Vec<f64>,
    ratio_coefs: &Vec<f64>,
) -> f64 {
    let ht_to_dia = HeightToDiameter {
        dia: dia,
        ht: ht,
        d_i: d_i,
        a: volob_coefs[0],
        b: volob_coefs[1],
        c: volob_coefs[2],
        alpha: ratio_coefs[0],
        beta: ratio_coefs[1],
    };
    // Initial parameter vector (initial guess)
    let init_param: Vec<f64> = [0.0, ht_to_dia.ht].to_vec();

    // Set up solver
    let solver = NelderMead::new(init_param);

    // Run solver
    let res = Executor::new(ht_to_dia, solver)
        .configure(|state| state.max_iters(100).target_cost(0.0001))
        .run()
        .unwrap();

    return res.state.best_param.unwrap();
}

// Volume ratio model
pub fn volume_ratio(z: f64, ht: f64, alpha: f64, beta: f64) -> f64 {
    return (1.0 - (1.0 - z / ht).powf(alpha)).powf(beta);
}

// Weight-volume models
pub fn weight_volume(dia: f64, ht: f64, model: u8, coefs: &Vec<f64>) -> f64 {
    match model {
        1 => schumacher_hall(dia, ht, coefs[0], coefs[1], coefs[2]),
        2 => segmented(dia, ht, coefs[0], coefs[1], coefs[2], coefs[3], coefs[4]),
        3 => continuously_varible(dia, ht, coefs[0], coefs[1], coefs[2], coefs[3], coefs[4]),
        4 => modified_wiley(dia, ht, coefs[0], coefs[1], coefs[2], coefs[3]),
        5 => modified_schumacher_hall(dia, ht, coefs[0], coefs[1], coefs[2], coefs[3]),
        _ => panic!("Model not found"),
    }
}

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
