//! Alignment Engine for S-Entropy Navigation
//!
//! This module implements the core alignment algorithms that enable transformation
//! of problems into solution coordinates through S-entropy navigation.

use nalgebra::{Vector3, Matrix3};
use serde::{Deserialize, Serialize};
use musande_core::{SEntropy, constants::saint_stella::*, error::{MusandeError, Result}};

/// Strategies for S-entropy alignment
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum AlignmentStrategy {
    /// Direct coordinate transformation
    Direct,
    /// Gradual alignment through multiple steps
    Iterative,
    /// Zero-computation instant alignment
    ZeroComputation,
    /// Ridiculous alignment for impossible scenarios
    Ridiculous,
}

/// Result of an alignment operation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlignmentResult {
    /// Original problem coordinate
    pub original: SEntropy,
    /// Final aligned coordinate
    pub aligned: SEntropy,
    /// Strategy used for alignment
    pub strategy: AlignmentStrategy,
    /// Number of steps required
    pub steps: usize,
    /// Final alignment error (distance from target)
    pub alignment_error: f64,
    /// Navigation efficiency achieved
    pub efficiency: f64,
    /// Whether global viability was maintained
    pub globally_viable: bool,
}

impl AlignmentResult {
    /// Check if the alignment was successful
    pub fn is_successful(&self) -> bool {
        self.alignment_error <= ALIGNMENT_CONVERGENCE_THRESHOLD
    }

    /// Check if the solution required ridiculous methods
    pub fn required_ridiculous_approach(&self) -> bool {
        matches!(self.strategy, AlignmentStrategy::Ridiculous)
    }
}

/// Core alignment engine for S-entropy coordinates
#[derive(Debug, Clone)]
pub struct AlignmentEngine {
    /// Maximum number of iterations for iterative alignment
    pub max_iterations: usize,
    /// Convergence threshold for alignment
    pub convergence_threshold: f64,
    /// Default alignment strategy
    pub default_strategy: AlignmentStrategy,
}

impl AlignmentEngine {
    /// Create a new alignment engine with default configuration
    pub fn new() -> Self {
        Self {
            max_iterations: 1000,
            convergence_threshold: ALIGNMENT_CONVERGENCE_THRESHOLD,
            default_strategy: AlignmentStrategy::Direct,
        }
    }

    /// Perform S-entropy alignment from source to target coordinate
    pub fn align(&self, source: SEntropy, target: SEntropy) -> Result<AlignmentResult> {
        // Validate input coordinates
        source.validate()?;
        target.validate()?;

        // Check if already aligned
        let initial_error = source.distance(&target);
        if initial_error <= self.convergence_threshold {
            return Ok(AlignmentResult {
                original: source.clone(),
                aligned: source,
                strategy: AlignmentStrategy::Direct,
                steps: 0,
                alignment_error: initial_error,
                efficiency: f64::INFINITY,
                globally_viable: true,
            });
        }

        // Determine optimal alignment strategy
        let strategy = self.determine_optimal_strategy(&source, &target)?;
        
        match strategy {
            AlignmentStrategy::Direct => self.align_direct(source, target),
            AlignmentStrategy::Iterative => self.align_iterative(source, target),
            AlignmentStrategy::ZeroComputation => self.align_zero_computation(source, target),
            AlignmentStrategy::Ridiculous => self.align_ridiculous(source, target),
        }
    }

    /// Direct alignment using single transformation
    fn align_direct(&self, source: SEntropy, target: SEntropy) -> Result<AlignmentResult> {
        // Calculate direct transformation vector
        let transformation_vector = &target - &source;
        
        // Apply St. Stella constant scaling
        let scaling_factor = stella_scaling_factor(transformation_vector.magnitude());
        let aligned = source + (transformation_vector * scaling_factor);
        
        let alignment_error = aligned.distance(&target);
        let efficiency = source.navigation_efficiency(&aligned);
        
        Ok(AlignmentResult {
            original: source,
            aligned,
            strategy: AlignmentStrategy::Direct,
            steps: 1,
            alignment_error,
            efficiency,
            globally_viable: alignment_error <= MAX_IMPOSSIBILITY_FACTOR,
        })
    }

    /// Iterative alignment through multiple steps
    fn align_iterative(&self, source: SEntropy, target: SEntropy) -> Result<AlignmentResult> {
        let mut current = source.clone();
        let mut steps = 0;

        while steps < self.max_iterations {
            let distance_to_target = current.distance(&target);
            
            if distance_to_target <= self.convergence_threshold {
                break;
            }

            // Calculate step toward target
            let direction = &target - &current;
            let step_size = (distance_to_target * STELLA_CONSTANT).min(1.0);
            let step = direction * (step_size / direction.magnitude());
            
            current = current + step;
            steps += 1;
        }

        let alignment_error = current.distance(&target);
        let efficiency = source.navigation_efficiency(&current);

        Ok(AlignmentResult {
            original: source,
            aligned: current,
            strategy: AlignmentStrategy::Iterative,
            steps,
            alignment_error,
            efficiency,
            globally_viable: alignment_error <= MIN_GLOBAL_VIABILITY,
        })
    }

    /// Zero-computation alignment (theoretical instantaneous alignment)
    fn align_zero_computation(&self, source: SEntropy, target: SEntropy) -> Result<AlignmentResult> {
        // Zero-computation alignment assumes perfect coordinate transformation
        // This represents the theoretical limit of navigation efficiency
        
        let aligned = target.clone();
        let efficiency = f64::INFINITY; // Perfect efficiency
        
        Ok(AlignmentResult {
            original: source,
            aligned,
            strategy: AlignmentStrategy::ZeroComputation,
            steps: 0,
            alignment_error: 0.0,
            efficiency,
            globally_viable: true,
        })
    }

    /// Ridiculous alignment for locally impossible scenarios
    fn align_ridiculous(&self, source: SEntropy, target: SEntropy) -> Result<AlignmentResult> {
        let impossibility_level = source.distance(&target);
        
        if impossibility_level > MAX_IMPOSSIBILITY_FACTOR {
            return Err(MusandeError::RidiculousSolutionError(
                format!("Impossibility level {} exceeds maximum", impossibility_level)
            ));
        }

        // Apply ridiculous transformation using multiple scaling factors
        let stella_scaling = stella_scaling_factor(impossibility_level);
        let golden_scaling = GOLDEN_RATIO.powf(impossibility_level.log2());
        let cube_scaling = CUBE_ROOT_TWO.powf(impossibility_level.sqrt());

        let ridiculous_transformation = SEntropy::new(
            target.knowledge_deficit * stella_scaling,
            target.temporal_distance * golden_scaling,
            target.entropy_accessibility * cube_scaling,
        );

        // Check global viability
        let global_viability = self.check_global_viability(&ridiculous_transformation)?;

        Ok(AlignmentResult {
            original: source,
            aligned: ridiculous_transformation,
            strategy: AlignmentStrategy::Ridiculous,
            steps: 1,
            alignment_error: ridiculous_transformation.distance(&target),
            efficiency: stella_scaling,
            globally_viable: global_viability,
        })
    }

    /// Determine the optimal alignment strategy for given coordinates
    fn determine_optimal_strategy(&self, source: &SEntropy, target: &SEntropy) -> Result<AlignmentStrategy> {
        let distance = source.distance(target);
        let impossibility_level = distance / STELLA_CONSTANT;

        if distance <= self.convergence_threshold {
            Ok(AlignmentStrategy::Direct)
        } else if impossibility_level > MAX_IMPOSSIBILITY_FACTOR {
            Ok(AlignmentStrategy::Ridiculous)
        } else if distance <= TEMPORAL_NAVIGATION_WINDOW {
            Ok(AlignmentStrategy::ZeroComputation)
        } else {
            Ok(AlignmentStrategy::Iterative)
        }
    }

    /// Check if a coordinate maintains global viability
    fn check_global_viability(&self, coordinate: &SEntropy) -> Result<bool> {
        let magnitude = coordinate.magnitude();
        let viability = magnitude <= MAX_IMPOSSIBILITY_FACTOR && magnitude >= MIN_GLOBAL_VIABILITY;
        Ok(viability)
    }
}

impl Default for AlignmentEngine {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_alignment_engine_creation() {
        let engine = AlignmentEngine::new();
        assert_eq!(engine.max_iterations, 1000);
        assert!(engine.convergence_threshold > 0.0);
    }

    #[test]
    fn test_direct_alignment() {
        let engine = AlignmentEngine::new();
        let source = SEntropy::new(1.0, 1.0, 1.0);
        let target = SEntropy::new(0.0, 0.0, 0.0);

        let result = engine.align_direct(source, target).unwrap();
        assert!(result.alignment_error < 100.0); // Should be reasonable
        assert_eq!(result.strategy, AlignmentStrategy::Direct);
    }

    #[test]
    fn test_zero_computation_alignment() {
        let engine = AlignmentEngine::new();
        let source = SEntropy::new(5.0, 5.0, 5.0);
        let target = SEntropy::origin();

        let result = engine.align_zero_computation(source, target).unwrap();
        assert_eq!(result.alignment_error, 0.0);
        assert_eq!(result.strategy, AlignmentStrategy::ZeroComputation);
        assert!(result.is_successful());
    }

    #[test]
    fn test_alignment_result_validation() {
        let result = AlignmentResult {
            original: SEntropy::new(1.0, 1.0, 1.0),
            aligned: SEntropy::origin(),
            strategy: AlignmentStrategy::ZeroComputation,
            steps: 0,
            alignment_error: 0.0,
            efficiency: f64::INFINITY,
            globally_viable: true,
        };

        assert!(result.is_successful());
        assert!(!result.required_ridiculous_approach());
    }

    #[test]
    fn test_strategy_determination() {
        let engine = AlignmentEngine::new();
        
        // Close coordinates should use direct strategy
        let close_source = SEntropy::origin();
        let close_target = SEntropy::new(0.001, 0.001, 0.001);
        let strategy = engine.determine_optimal_strategy(&close_source, &close_target).unwrap();
        assert_eq!(strategy, AlignmentStrategy::Direct);
    }
} 