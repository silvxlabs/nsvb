mod ffi;
mod models;

// test
#[cfg(test)]

mod tests {
    use super::*;
    use assert_approx_eq::assert_approx_eq;

    #[test]
    fn test_stem_wood_volume() {
        // Create a C-compatible string for the division
        let vol = models::stem_wood_volume(202, 20.0, 110.0, "240").unwrap();
        assert_approx_eq!(vol, 88.45227554428, 1e-2);
    }
}
