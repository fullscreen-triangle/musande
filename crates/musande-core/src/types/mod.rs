//! Core Types for S-Entropy Framework
//!
//! This module defines the fundamental types that integrate the Biological Maxwell Demon (BMD)
//! model of consciousness with tri-dimensional S-entropy navigation. These types represent
//! the computational substrate underlying consciousness itself.

pub mod s_entropy;
pub mod tri_dimensional;
pub mod observer;
pub mod oscillation;
pub mod cognitive_frame;
pub mod associative_memory;

// Re-export core types for convenience
pub use s_entropy::*;
pub use tri_dimensional::*;
pub use observer::*;
pub use oscillation::*;
pub use cognitive_frame::*;
pub use associative_memory::*; 