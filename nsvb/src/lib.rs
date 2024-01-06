pub mod ffi;
mod models;

// Re-export the models to bring them into the root crate namespace. The functions
// live in the models module so they can be reused by the FFI functions in ffi.rs.
// However, we want to expose them at the root level for user's convenience.
pub use models::bark_biomass;
pub use models::branch_biomass;
pub use models::foliage_biomass;
pub use models::height_to_diameter;
pub use models::stem_bark_volume;
pub use models::stem_volume_ratio;
pub use models::stem_wood_volume;
pub use models::total_biomass;
