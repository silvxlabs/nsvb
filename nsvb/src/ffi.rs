use std::ffi::CStr;
use std::os::raw::c_char;

use crate::models;

/// Helper function to convert a C string to a Rust string slice.
fn c_str_to_str(c_str: *const c_char) -> Result<&'static str, &'static str> {
    unsafe {
        if c_str.is_null() {
            return Err("Null pointer passed");
        }

        CStr::from_ptr(c_str)
            .to_str()
            .map_err(|_| "Invalid UTF-8 string")
    }
}

#[no_mangle]
pub extern "C" fn stem_wood_volume_ffi(
    spcd: u16,
    dia: f64,
    ht: f64,
    division: *const c_char,
) -> f64 {
    let division_str = match c_str_to_str(division) {
        Ok(str) => str,
        Err(_) => return -1.0,
    };
    match models::stem_wood_volume(spcd, dia, ht, Some(division_str)) {
        Ok(volume) => volume,
        Err(_) => -1.0,
    }
}

#[no_mangle]
pub extern "C" fn stem_bark_volume_ffi(
    spcd: u16,
    dia: f64,
    ht: f64,
    division: *const c_char,
) -> f64 {
    let division_str = match c_str_to_str(division) {
        Ok(str) => str,
        Err(_) => return -1.0,
    };
    match models::stem_bark_volume(spcd, dia, ht, Some(division_str)) {
        Ok(volume) => volume,
        Err(_) => -1.0,
    }
}

#[no_mangle]
pub extern "C" fn total_biomass_ffi(spcd: u16, dia: f64, ht: f64, division: *const c_char) -> f64 {
    let division_str = match c_str_to_str(division) {
        Ok(str) => str,
        Err(_) => return -1.0,
    };
    match models::total_biomass(spcd, dia, ht, Some(division_str)) {
        Ok(volume) => volume,
        Err(_) => -1.0,
    }
}
