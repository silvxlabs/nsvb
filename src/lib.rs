pub mod ffi;
mod models;
mod tree;

// Re-export the tree module to bring it into the crate namespace.
pub use tree::Tree;

// Re-export the models to bring them into the crate namespace. The functions
// live in the models module so they can be reused by the FFI functions in ffi.rs
// and Tree struct in tree.rs. However, we want to expose them at the root level
// for user's convenience when building interfaces with other languages.
pub use models::bark_biomass;
pub use models::branch_biomass;
pub use models::foliage_biomass;
pub use models::height_to_diameter;
pub use models::stem_bark_volume;
pub use models::stem_volume_ratio;
pub use models::stem_wood_volume;
pub use models::total_biomass;
