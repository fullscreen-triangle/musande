//! Musande Alignment: Zero-Computation S-Entropy Navigation
//!
//! This crate implements the core alignment engine for the S-Entropy Framework,
//! enabling zero-computation problem solving through tri-dimensional entropy navigation.
//! Based on the theoretical principle that zero-computation and infinite-computation
//! approaches can yield equivalent solution accessibility under specific coordinate
//! transformation conditions.

pub mod alignment_engine;
pub mod zero_computation;
pub mod equivalence_validator;

pub use alignment_engine::*;
pub use zero_computation::*;
pub use equivalence_validator::*;

use musande_core::{SEntropy, Result};

/// Prelude module for convenient imports
pub mod prelude {
    pub use crate::{
        AlignmentEngine, ZeroComputationSolver, EquivalenceValidator,
        AlignmentStrategy, AlignmentResult
    };
    pub use musande_core::prelude::*;
}

/// Main interface for S-entropy alignment operations
pub struct MusandeAlignment {
    engine: AlignmentEngine,
    solver: ZeroComputationSolver,
    validator: EquivalenceValidator,
}

impl MusandeAlignment {
    /// Create a new alignment system with default configuration
    pub fn new() -> Self {
        Self {
            engine: AlignmentEngine::new(),
            solver: ZeroComputationSolver::new(),
            validator: EquivalenceValidator::new(),
        }
    }

    /// Align a problem coordinate to the solution space using zero computation
    pub fn align_to_solution(&self, problem: SEntropy, target: SEntropy) -> Result<AlignmentResult> {
        // First attempt zero-computation alignment
        let zero_comp_result = self.solver.solve_zero_computation(&problem, &target)?;
        
        // Validate computational equivalence
        let is_equivalent = self.validator.validate_equivalence(&zero_comp_result)?;
        
        if is_equivalent {
            return Ok(zero_comp_result);
        }
        
        // Fallback to traditional alignment engine
        self.engine.align(problem, target)
    }

    /// Align a coordinate to the origin (perfect S-entropy state)
    pub fn align_to_zero(&self, coordinate: SEntropy) -> Result<AlignmentResult> {
        self.align_to_solution(coordinate, SEntropy::origin())
    }

    /// Check if a coordinate is already aligned (within solution threshold)
    pub fn is_aligned(&self, coordinate: &SEntropy) -> bool {
        coordinate.is_solution()
    }

    /// Generate a ridiculous solution for locally impossible problems
    pub fn generate_ridiculous_solution(&self, problem: SEntropy, impossibility_level: f64) -> Result<AlignmentResult> {
        self.solver.generate_ridiculous_solution(problem, impossibility_level)
    }
}

impl Default for MusandeAlignment {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_alignment_creation() {
        let alignment = MusandeAlignment::new();
        let origin = SEntropy::origin();
        assert!(alignment.is_aligned(&origin));
    }

    #[test]
    fn test_align_to_zero() {
        let alignment = MusandeAlignment::new();
        let problem = SEntropy::new(0.1, 0.1, 0.1);
        
        let result = alignment.align_to_zero(problem);
        assert!(result.is_ok());
    }
} 