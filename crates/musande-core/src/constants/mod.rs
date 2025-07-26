//! Constants for the S-Entropy Framework
//!
//! This module contains fundamental constants used throughout the Musande system,
//! including Saint Stella-Lorraine's S constant and physical constants required
//! for entropy navigation and oscillatory computation.

pub mod saint_stella;
pub mod physical;

// Re-export key constants for convenience
pub use saint_stella::*;
pub use physical::*; 