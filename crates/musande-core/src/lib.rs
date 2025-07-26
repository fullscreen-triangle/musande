//! # Musande Core: S-Entropy Framework Foundation
//!
//! This crate provides the fundamental mathematical types and operations for the S-Entropy Framework,
//! implementing the tri-dimensional entropy navigation system based on Saint Stella-Lorraine's S constant.
//!
//! ## Core Concepts
//!
//! - **S-Entropy**: Entropy accessible to observers, constrained by their separation from the process
//! - **Tri-Dimensional S**: S = (S_knowledge, S_time, S_entropy) representing informational deficit,
//!   temporal distance to solution, and thermodynamic navigation respectively
//! - **Observer-Process Separation**: Mathematical framework for non-universal observer limitations
//! - **Oscillatory Endpoints**: Entropy as the computational endpoint of atomic oscillations
//!
//! ## Mathematical Foundation
//!
//! The framework is built on matrix associative memory architectures, inspired by neurocomputational
//! models of language processing, where context-dependent neural networks enable goal-oriented behavior
//! through modular associative memory systems.

use std::fmt;

pub mod constants;
pub mod types;
pub mod math;
pub mod error;

// Re-export core types for convenience
pub use constants::saint_stella::*;
pub use types::{SEntropy, TriDimensionalS, ObserverSeparation, OscillationEndpoint};
pub use error::{MusandeError, Result};

/// The fundamental S-Entropy type representing the tri-dimensional entropy navigation system
///
/// Based on the mathematical formulation:
/// ```text
/// S = (S_knowledge, S_time, S_entropy)
/// 
/// Where:
/// S_knowledge = Informational_Deficit = log₂(Unknown_States/Total_States)
/// S_time = Temporal_Distance = T_solution - T_current  
/// S_entropy = Accessible_Entropy_Change = S_observed - S_true
/// ```
#[derive(Debug, Clone, PartialEq)]
pub struct MusandeCore {
    /// Version of the S-Entropy Framework implementation
    pub version: &'static str,
    /// Saint Stella-Lorraine constant for eternal optimization
    pub stella_constant: f64,
}

impl Default for MusandeCore {
    fn default() -> Self {
        Self {
            version: env!("CARGO_PKG_VERSION"),
            stella_constant: constants::saint_stella::STELLA_CONSTANT,
        }
    }
}

impl fmt::Display for MusandeCore {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "Musande S-Entropy Framework v{} (Stella Constant: {})",
            self.version, self.stella_constant
        )
    }
}

/// Initialize the Musande Core system with default S-entropy navigation parameters
pub fn initialize() -> MusandeCore {
    MusandeCore::default()
}

/// Quick verification that the S-Entropy Framework is properly configured
pub fn verify_s_entropy_system() -> Result<()> {
    let core = initialize();
    
    // Verify Saint Stella-Lorraine constant is properly set
    if core.stella_constant <= 0.0 {
        return Err(MusandeError::InvalidConfiguration(
            "Stella constant must be positive for eternal optimization".to_string()
        ));
    }
    
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_core_initialization() {
        let core = initialize();
        assert_eq!(core.version, env!("CARGO_PKG_VERSION"));
        assert!(core.stella_constant > 0.0);
    }

    #[test]
    fn test_s_entropy_system_verification() {
        assert!(verify_s_entropy_system().is_ok());
    }

    #[test]
    fn test_display_formatting() {
        let core = initialize();
        let display = format!("{}", core);
        assert!(display.contains("Musande S-Entropy Framework"));
        assert!(display.contains("Stella Constant"));
    }
} 