//! Tri-Dimensional S-Entropy Navigation
//!
//! This module implements coordinate transformation algorithms for navigating
//! through S-entropy space, enabling the conversion of problems into navigation
//! challenges as described in the theoretical framework.

use nalgebra::{Matrix3, Vector3};
use serde::{Deserialize, Serialize};
use crate::types::s_entropy::SEntropy;
use crate::constants::saint_stella::*;
use crate::error::{MusandeError, Result};

/// Transformation matrix for S-entropy coordinate navigation
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SEntropyTransformation {
    /// 3x3 transformation matrix for coordinate navigation
    pub matrix: Matrix3<f64>,
    /// Scaling factor incorporating the St. Stella constant
    pub stella_scaling: f64,
    /// Whether this transformation preserves solution accessibility
    pub preserves_accessibility: bool,
}

impl SEntropyTransformation {
    /// Create a new S-entropy transformation matrix
    pub fn new(matrix: Matrix3<f64>) -> Self {
        Self {
            matrix,
            stella_scaling: STELLA_CONSTANT,
            preserves_accessibility: Self::check_accessibility_preservation(&matrix),
        }
    }

    /// Create an identity transformation (no change)
    pub fn identity() -> Self {
        Self::new(Matrix3::identity())
    }

    /// Create a scaling transformation
    pub fn scaling(factor: f64) -> Self {
        Self::new(Matrix3::from_diagonal(&Vector3::new(factor, factor, factor)))
    }

    /// Create a rotation transformation around a given axis
    pub fn rotation(axis: Vector3<f64>, angle: f64) -> Result<Self> {
        let normalized_axis = axis.normalize();
        let rotation_matrix = Matrix3::from_axis_angle(&nalgebra::Unit::new_unchecked(normalized_axis), angle);
        Ok(Self::new(rotation_matrix))
    }

    /// Apply transformation to an S-entropy coordinate
    pub fn transform(&self, coordinate: &SEntropy) -> SEntropy {
        let vector = coordinate.to_vector3();
        let transformed = self.matrix * vector * self.stella_scaling;
        SEntropy::from_vector3(transformed)
    }

    /// Calculate the inverse transformation
    pub fn inverse(&self) -> Result<Self> {
        match self.matrix.try_inverse() {
            Some(inverse_matrix) => Ok(Self {
                matrix: inverse_matrix,
                stella_scaling: 1.0 / self.stella_scaling,
                preserves_accessibility: self.preserves_accessibility,
            }),
            None => Err(MusandeError::MathematicalError(
                "Cannot compute inverse of singular transformation matrix".to_string()
            )),
        }
    }

    /// Compose this transformation with another
    pub fn compose(&self, other: &SEntropyTransformation) -> Self {
        Self {
            matrix: self.matrix * other.matrix,
            stella_scaling: self.stella_scaling * other.stella_scaling,
            preserves_accessibility: self.preserves_accessibility && other.preserves_accessibility,
        }
    }

    /// Check if the transformation matrix preserves solution accessibility
    fn check_accessibility_preservation(matrix: &Matrix3<f64>) -> bool {
        // A transformation preserves accessibility if it's invertible and maintains
        // relative distances (isometric transformations)
        let det = matrix.determinant();
        det.abs() > S_ENTROPY_PRECISION && (det.abs() - 1.0).abs() < S_ENTROPY_PRECISION
    }

    /// Apply St. Stella constant scaling for low-information scenarios
    pub fn apply_stella_constant_scaling(&mut self, impossibility_level: f64) {
        self.stella_scaling *= stella_scaling_factor(impossibility_level);
    }
}

/// Navigation pathway through S-entropy space
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NavigationPathway {
    /// Starting S-entropy coordinate
    pub start: SEntropy,
    /// Target S-entropy coordinate
    pub target: SEntropy,
    /// Sequence of transformations to reach target
    pub transformations: Vec<SEntropyTransformation>,
    /// Total navigation distance
    pub total_distance: f64,
    /// Navigation efficiency score
    pub efficiency: f64,
}

impl NavigationPathway {
    /// Create a new navigation pathway
    pub fn new(start: SEntropy, target: SEntropy) -> Self {
        let distance = start.distance(&target);
        let efficiency = start.navigation_efficiency(&target);
        
        Self {
            start,
            target,
            transformations: Vec::new(),
            total_distance: distance,
            efficiency,
        }
    }

    /// Add a transformation step to the pathway
    pub fn add_transformation(&mut self, transformation: SEntropyTransformation) {
        self.transformations.push(transformation);
        self.recalculate_metrics();
    }

    /// Execute the complete navigation pathway
    pub fn execute(&self) -> SEntropy {
        let mut current = self.start.clone();
        
        for transformation in &self.transformations {
            current = transformation.transform(&current);
        }
        
        current
    }

    /// Check if the pathway successfully reaches the target
    pub fn reaches_target(&self) -> bool {
        let final_position = self.execute();
        final_position.distance(&self.target) <= ALIGNMENT_CONVERGENCE_THRESHOLD
    }

    /// Optimize the pathway by removing redundant transformations
    pub fn optimize(&mut self) -> Result<()> {
        if self.transformations.is_empty() {
            return Ok(());
        }

        // Compose consecutive transformations that don't break accessibility preservation
        let mut optimized = Vec::new();
        let mut current_transform = self.transformations[0].clone();

        for transform in self.transformations.iter().skip(1) {
            if current_transform.preserves_accessibility && transform.preserves_accessibility {
                current_transform = current_transform.compose(transform);
            } else {
                optimized.push(current_transform);
                current_transform = transform.clone();
            }
        }
        optimized.push(current_transform);

        self.transformations = optimized;
        self.recalculate_metrics();
        Ok(())
    }

    /// Recalculate pathway metrics after modifications
    fn recalculate_metrics(&mut self) {
        if self.transformations.is_empty() {
            self.total_distance = self.start.distance(&self.target);
            self.efficiency = self.start.navigation_efficiency(&self.target);
            return;
        }

        let final_position = self.execute();
        self.total_distance = self.start.distance(&final_position);
        self.efficiency = if self.total_distance > S_ENTROPY_PRECISION {
            STELLA_CONSTANT / self.total_distance
        } else {
            f64::INFINITY
        };
    }
}

/// Algorithm for calculating optimal navigation pathways
pub struct NavigationAlgorithm {
    /// Maximum number of transformation steps allowed
    pub max_steps: usize,
    /// Convergence threshold for pathway optimization
    pub convergence_threshold: f64,
}

impl NavigationAlgorithm {
    /// Create a new navigation algorithm with default parameters
    pub fn new() -> Self {
        Self {
            max_steps: 100,
            convergence_threshold: ALIGNMENT_CONVERGENCE_THRESHOLD,
        }
    }

    /// Calculate the optimal pathway between two S-entropy coordinates
    pub fn calculate_pathway(&self, start: SEntropy, target: SEntropy) -> Result<NavigationPathway> {
        let mut pathway = NavigationPathway::new(start.clone(), target.clone());
        
        // Direct path check
        if start.distance(&target) <= self.convergence_threshold {
            return Ok(pathway);
        }

        // Calculate direct transformation matrix
        let direction = &target - &start;
        let direction_vector = direction.to_vector3();
        
        if direction_vector.magnitude() < S_ENTROPY_PRECISION {
            return Ok(pathway);
        }

        // Create transformation that moves from start toward target
        let normalized_direction = direction_vector.normalize();
        let distance = direction_vector.magnitude();
        
        // Use a scaling transformation that incorporates the St. Stella constant
        let scaling_factor = stella_scaling_factor(distance);
        let transformation_matrix = Matrix3::from_diagonal(&Vector3::new(
            scaling_factor,
            scaling_factor,
            scaling_factor,
        ));

        let mut transformation = SEntropyTransformation::new(transformation_matrix);
        transformation.apply_stella_constant_scaling(distance);
        
        pathway.add_transformation(transformation);
        
        Ok(pathway)
    }

    /// Generate a ridiculous pathway for locally impossible solutions
    pub fn generate_ridiculous_pathway(&self, start: SEntropy, target: SEntropy, impossibility_level: f64) -> Result<NavigationPathway> {
        if impossibility_level > MAX_IMPOSSIBILITY_FACTOR {
            return Err(MusandeError::MathematicalError(
                format!("Impossibility level {} exceeds maximum {}", impossibility_level, MAX_IMPOSSIBILITY_FACTOR)
            ));
        }

        let mut pathway = self.calculate_pathway(start, target)?;
        
        // Apply ridiculous scaling for impossible scenarios
        let ridiculous_scaling = stella_scaling_factor(impossibility_level);
        let ridiculous_matrix = Matrix3::from_diagonal(&Vector3::new(
            ridiculous_scaling,
            ridiculous_scaling * GOLDEN_RATIO,
            ridiculous_scaling * CUBE_ROOT_TWO,
        ));

        let mut ridiculous_transform = SEntropyTransformation::new(ridiculous_matrix);
        ridiculous_transform.apply_stella_constant_scaling(impossibility_level);
        
        pathway.add_transformation(ridiculous_transform);
        pathway.optimize()?;
        
        Ok(pathway)
    }
}

impl Default for NavigationAlgorithm {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_transformation_creation() {
        let identity = SEntropyTransformation::identity();
        assert_eq!(identity.matrix, Matrix3::identity());
        assert!(identity.preserves_accessibility);
    }

    #[test]
    fn test_transformation_application() {
        let coordinate = SEntropy::new(1.0, 2.0, 3.0);
        let scaling = SEntropyTransformation::scaling(2.0);
        let transformed = scaling.transform(&coordinate);
        
        // Should be scaled by 2.0 * STELLA_CONSTANT
        let expected_scale = 2.0 * STELLA_CONSTANT;
        assert!((transformed.knowledge_deficit - coordinate.knowledge_deficit * expected_scale).abs() < 1e-10);
    }

    #[test]
    fn test_navigation_pathway() {
        let start = SEntropy::new(0.0, 0.0, 0.0);
        let target = SEntropy::new(1.0, 1.0, 1.0);
        let pathway = NavigationPathway::new(start, target);
        
        assert_eq!(pathway.start.magnitude(), 0.0);
        assert!((pathway.total_distance - target.magnitude()).abs() < 1e-10);
    }

    #[test]
    fn test_navigation_algorithm() {
        let algorithm = NavigationAlgorithm::new();
        let start = SEntropy::origin();
        let target = SEntropy::new(1.0, 1.0, 1.0);
        
        let pathway = algorithm.calculate_pathway(start, target).unwrap();
        assert!(!pathway.transformations.is_empty());
    }

    #[test]
    fn test_ridiculous_pathway() {
        let algorithm = NavigationAlgorithm::new();
        let start = SEntropy::origin();
        let target = SEntropy::new(100.0, 100.0, 100.0); // Highly impossible
        
        let pathway = algorithm.generate_ridiculous_pathway(start, target, 1000.0).unwrap();
        assert!(!pathway.transformations.is_empty());
    }
} 