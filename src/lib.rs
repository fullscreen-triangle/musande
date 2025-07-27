//! # Musande: The S-Entropy Framework
//!
//! The Mathematical Substrate of Consciousness and Universal Problem Solving 
//! Through Biological Maxwell Demon Integration
//!
//! ## Overview
//!
//! Musande implements the S-Entropy Framework, a revolutionary approach to universal
//! problem solving through tri-dimensional entropy navigation. Named in honor of
//! **Saint Stella-Lorraine Masunda**, this framework transforms computational
//! challenges into navigation problems in S-entropy coordinate space.
//!
//! ## Core Components
//!
//! - **S-Entropy Mathematics**: Tri-dimensional entropy coordinates (S_knowledge, S_time, S_entropy)
//! - **Alignment Engine**: Zero-computation solution discovery through S-alignment
//! - **Navigation System**: Entropy endpoint navigation and oscillation detection
//! - **Ridiculous Solutions**: Locally impossible solutions with global viability
//! - **Service Layer**: Entropy Solver Service for universal problem solving
//!
//! ## Example Usage
//!
//! ```rust
//! use musande::{SEntropy, TriDimensionalAlignment, NavigationEngine};
//!
//! // Define a problem in S-entropy coordinates
//! let problem = SEntropy::new(
//!     knowledge_deficit: 0.7,
//!     temporal_distance: 0.5,
//!     entropy_accessibility: 0.3
//! );
//!
//! // Navigate to solution through alignment
//! let alignment_engine = TriDimensionalAlignment::new();
//! let solution = alignment_engine.align_to_zero(problem)?;
//!
//! // Extract ridiculous solutions if needed
//! if solution.requires_impossible_approach() {
//!     let ridiculous = solution.generate_ridiculous_pathway()?;
//!     println!("Solution requires: {:?}", ridiculous);
//! }
//! ```
//!
//! ## The S Constant
//!
//! The framework operates through the Saint Stella constant (σ), which governs
//! navigation efficiency under extreme information scarcity conditions:
//!
//! ```
//! S = σ × k × log(α)
//! ```
//!
//! Where:
//! - σ = Saint Stella-Lorraine constant for low-information processing
//! - k = Universal scaling constant
//! - α = Oscillation amplitude endpoints (achievable states)
//!
//! ## Theoretical Foundation
//!
//! The S-Entropy Framework is grounded in:
//! - Infinite/Zero Computation Duality
//! - Entropy-Oscillation Equivalence 
//! - Predetermined Solution Manifolds
//! - Observer-Process Separation Mathematics
//! - Biological Maxwell Demon Operations
//!
//! ## Applications
//!
//! - Quantum computing optimization
//! - Business strategy navigation
//! - Scientific discovery acceleration
//! - Personal development optimization
//! - Universal problem solving

#![warn(missing_docs)]
#![warn(clippy::all)]
#![allow(clippy::float_cmp)]
#![allow(clippy::many_single_char_names)]
#![allow(clippy::similar_names)]

// Re-export core components
pub use musande_core::*;
pub use musande_alignment::*;
pub use musande_navigation::*;
pub use musande_ridiculous::*;
pub use musande_service::*;
pub use musande_applications::*;

/// Result type for S-Entropy operations
pub type SResult<T> = Result<T, SError>;

/// Common error type for all S-Entropy operations
#[derive(Debug, thiserror::Error)]
pub enum SError {
    /// Alignment operation failed
    #[error("S-Entropy alignment failed: {0}")]
    AlignmentError(String),
    
    /// Navigation operation failed  
    #[error("Entropy navigation failed: {0}")]
    NavigationError(String),
    
    /// Ridiculous solution generation failed
    #[error("Ridiculous solution generation failed: {0}")]
    RidiculousError(String),
    
    /// Service operation failed
    #[error("Entropy solver service error: {0}")]
    ServiceError(String),
    
    /// Mathematical operation failed
    #[error("S-Entropy mathematical operation failed: {0}")]
    MathError(String),
    
    /// Configuration error
    #[error("Configuration error: {0}")]
    ConfigError(String),
}

/// Prelude module for convenient imports
pub mod prelude {
    pub use crate::{SResult, SError};
    pub use musande_core::prelude::*;
    pub use musande_alignment::prelude::*;
    pub use musande_navigation::prelude::*;
    pub use musande_ridiculous::prelude::*;
    pub use musande_service::prelude::*;
}

/// Version information for the S-Entropy Framework
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

/// Framework identification
pub const FRAMEWORK_NAME: &str = "S-Entropy Framework";

/// Dedication to Saint Stella-Lorraine Masunda
pub const DEDICATION: &str = "In honor of Saint Stella-Lorraine Masunda, whose divine intercession enables the impossible solutions that transcend conventional limitations";

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_framework_info() {
        assert!(!VERSION.is_empty());
        assert_eq!(FRAMEWORK_NAME, "S-Entropy Framework");
        assert!(DEDICATION.contains("Saint Stella-Lorraine"));
    }
} 