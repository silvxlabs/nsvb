use std::ffi::CStr;
use std::os::raw::{c_char, c_double, c_uint};
use std::slice;
pub mod tree;

#[no_mangle]
pub extern "C" fn gross_stem_vol_ib_ffi(
    spcd: u16,
    division: *const c_char,
    dia: f64,
    ht: f64,
) -> f64 {
    // Convert the C string to a Rust string
    let division_cstr = unsafe {
        assert!(!division.is_null());
        CStr::from_ptr(division)
    };
    let division_str = division_cstr.to_str().unwrap();

    // Call the original Rust function
    tree::gross_stem_vol_ib(spcd, division_str, dia, ht)
}

#[no_mangle]
pub extern "C" fn gross_stem_vol_ib_bulk_ffi(
    spcd_ptr: *const c_uint, // u16 in C is often represented as unsigned int
    division_ptr: *const *const c_char,
    dia_ptr: *const c_double,
    ht_ptr: *const c_double,
    len: usize,
) -> *mut c_double {
    // Convert raw pointers to slices
    let spcd = unsafe { slice::from_raw_parts(spcd_ptr, len) };
    let dia = unsafe { slice::from_raw_parts(dia_ptr, len) };
    let ht = unsafe { slice::from_raw_parts(ht_ptr, len) };

    let divisions: Vec<String> = (0..len)
        .map(|i| unsafe {
            let c_str = CStr::from_ptr(*division_ptr.add(i));
            c_str.to_string_lossy().into_owned()
        })
        .collect();

    let result = tree::gross_stem_vol_ib_bulk(
        &spcd.iter().map(|&s| s as u16).collect(),
        &divisions,
        &dia.to_vec(),
        &ht.to_vec(),
    );

    // Convert Vec<f64> to raw pointer for FFI
    let boxed_result = result.into_boxed_slice();
    Box::into_raw(boxed_result) as *mut c_double
}
