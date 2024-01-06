use crate::models;

pub struct Tree {
    pub spcd: u16,
    pub dbh: f64,
    pub ht: f64,
    pub decay_class: u8,
    pub percent_cull: f64,
}

impl Tree {
    pub fn new(spcd: u16, dbh: f64, ht: f64, decay_class: u8, percent_cull: f64) -> Tree {
        Tree {
            spcd: spcd,
            dbh: dbh,
            ht: ht,
            decay_class: decay_class,
            percent_cull: percent_cull,
        }
    }

    pub fn stem_wood_volume(&self) -> Result<f64, String> {
        models::stem_wood_volume(self.spcd, self.dbh, self.ht, None)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_new() {
        let tree = Tree::new(202, 20.0, 110.0, 0, 0.0);
        assert_eq!(tree.spcd, 202);
        assert_eq!(tree.dbh, 20.0);
        assert_eq!(tree.ht, 110.0);
        assert_eq!(tree.decay_class, 0);
        assert_eq!(tree.percent_cull, 0.0);
    }

    #[test]
    fn test_stem_wood_volume() {
        let tree = Tree::new(202, 20.0, 110.0, 0, 0.0);
        assert_eq!(tree.stem_wood_volume().unwrap(), 83.68448227429401);
    }
}
