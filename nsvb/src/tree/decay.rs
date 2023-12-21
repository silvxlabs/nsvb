pub struct Decay {
    properties: Vec<Vec<f32>>,
}

impl Decay {
    pub fn new(spcd: u16) -> Self {
        let properties = if spcd < 300 {
            // Softwood
            vec![
                vec![0.97, 1.0, 1.0, 50.1], // DC1
                vec![1.0, 0.8, 0.5, 50.4],  // DC2
                vec![0.92, 0.5, 0.1, 50.6], // DC3
                vec![0.55, 0.2, 0.0, 52.0], // DC4
                vec![0.55, 0.0, 0.0, 52.7], // DC5
            ]
        } else {
            // Hardwood
            vec![
                vec![0.99, 1.0, 1.0, 47.0], // DC1
                vec![0.8, 0.8, 0.5, 47.3],  // DC2
                vec![0.54, 0.5, 0.1, 48.1], // DC3
                vec![0.43, 0.2, 0.0, 48.0], // DC4
                vec![0.43, 0.0, 0.0, 47.2], // DC5
            ]
        };

        Decay { properties }
    }

    pub fn get_wood_density_proportion(&self, decay_class: usize) -> Option<f32> {
        self.get_property(decay_class, DecayProperty::WoodDensityProportion)
    }

    pub fn get_remaining_bark_proportion(&self, decay_class: usize) -> Option<f32> {
        self.get_property(decay_class, DecayProperty::RemainingBarkProportion)
    }

    pub fn get_remaining_branch_proportion(&self, decay_class: usize) -> Option<f32> {
        self.get_property(decay_class, DecayProperty::RemainingBranchProportion)
    }

    pub fn get_carbon_fraction(&self, decay_class: usize) -> Option<f32> {
        self.get_property(decay_class, DecayProperty::CarbonFraction)
    }

    fn get_property(&self, decay_class: usize, property: DecayProperty) -> Option<f32> {
        if decay_class == 0 || decay_class > self.properties.len() {
            None
        } else {
            self.properties
                .get(decay_class - 1)
                .and_then(|properties| properties.get(property as usize).copied())
        }
    }
}

#[derive(Clone, Copy)]
pub enum DecayProperty {
    WoodDensityProportion = 0,
    RemainingBarkProportion = 1,
    RemainingBranchProportion = 2,
    CarbonFraction = 3,
}
