//! S-Entropy Core Type
//!
//! This module implements the fundamental S-entropy type representing points in the
//! tri-dimensional entropy navigation space. Based on the theoretical framework for
//! universal problem solving through coordinate transformation.

use nalgebra::{Vector3, Matrix3};
use serde::{Deserialize, Serialize};
use std::ops::{Add, Sub, Mul, Div};
use crate::constants::saint_stella::*;
use crate::error::{MusandeError, Result};

/// Core S-entropy type representing a point in tri-dimensional entropy space
/// 
/// The S-entropy coordinate system maps problems to three-dimensional space:
/// - S_knowledge: Information deficit dimension
/// - S_time: Temporal processing dimension  
/// - S_entropy: Thermodynamic accessibility dimension
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SEntropy {
    /// Information deficit: log₂(Required_Information / Available_Information)
    pub knowledge_deficit: f64,
    /// Temporal distance to solution in abstract time units
    pub temporal_distance: f64,
    /// Thermodynamic entropy change required for solution accessibility
    pub entropy_accessibility: f64,
}

impl SEntropy {
    /// Create a new S-entropy coordinate
    pub fn new(knowledge_deficit: f64, temporal_distance: f64, entropy_accessibility: f64) -> Self {
        Self {
            knowledge_deficit,
            temporal_distance,
            entropy_accessibility,
        }
    }

    /// Create S-entropy coordinates at the origin (perfect alignment)
    pub fn origin() -> Self {
        Self::new(0.0, 0.0, 0.0)
    }

    /// Calculate the magnitude (distance from origin) in S-entropy space
    pub fn magnitude(&self) -> f64 {
        (self.knowledge_deficit.powi(2) + 
         self.temporal_distance.powi(2) + 
         self.entropy_accessibility.powi(2)).sqrt()
    }

    /// Calculate distance between two S-entropy coordinates
    pub fn distance(&self, other: &SEntropy) -> f64 {
        let diff = self - other;
        diff.magnitude()
    }

    /// Check if this S-entropy coordinate represents a solution state
    /// (within alignment convergence threshold)
    pub fn is_solution(&self) -> bool {
        self.magnitude() <= ALIGNMENT_CONVERGENCE_THRESHOLD
    }

    /// Apply St. Stella constant scaling for low-information processing
    pub fn apply_stella_scaling(&self, scaling_factor: f64) -> Self {
        Self {
            knowledge_deficit: self.knowledge_deficit * scaling_factor,
            temporal_distance: self.temporal_distance * scaling_factor,
            entropy_accessibility: self.entropy_accessibility * scaling_factor,
        }
    }

    /// Convert to nalgebra Vector3 for mathematical operations
    pub fn to_vector3(&self) -> Vector3<f64> {
        Vector3::new(
            self.knowledge_deficit,
            self.temporal_distance,
            self.entropy_accessibility,
        )
    }

    /// Create from nalgebra Vector3
    pub fn from_vector3(v: Vector3<f64>) -> Self {
        Self::new(v.x, v.y, v.z)
    }

    /// Normalize the S-entropy coordinates to unit magnitude
    pub fn normalize(&self) -> Result<Self> {
        let mag = self.magnitude();
        if mag < S_ENTROPY_PRECISION {
            return Err(MusandeError::MathematicalError(
                "Cannot normalize S-entropy coordinate with near-zero magnitude".to_string()
            ));
        }
        
        Ok(Self {
            knowledge_deficit: self.knowledge_deficit / mag,
            temporal_distance: self.temporal_distance / mag,
            entropy_accessibility: self.entropy_accessibility / mag,
        })
    }

    /// Calculate the navigation efficiency for reaching a target coordinate
    pub fn navigation_efficiency(&self, target: &SEntropy) -> f64 {
        let distance = self.distance(target);
        if distance < S_ENTROPY_PRECISION {
            return f64::INFINITY; // Perfect efficiency for identical coordinates
        }
        
        STELLA_CONSTANT / distance
    }

    /// Validate that the S-entropy coordinates are mathematically valid
    pub fn validate(&self) -> Result<()> {
        if !self.knowledge_deficit.is_finite() {
            return Err(MusandeError::InvalidCoordinate(
                "Knowledge deficit must be finite".to_string()
            ));
        }
        
        if !self.temporal_distance.is_finite() {
            return Err(MusandeError::InvalidCoordinate(
                "Temporal distance must be finite".to_string()
            ));
        }
        
        if !self.entropy_accessibility.is_finite() {
            return Err(MusandeError::InvalidCoordinate(
                "Entropy accessibility must be finite".to_string()
            ));
        }
        
        Ok(())
    }
}

// Implement arithmetic operations for S-entropy coordinates
impl Add for SEntropy {
    type Output = SEntropy;
    
    fn add(self, other: SEntropy) -> SEntropy {
        SEntropy {
            knowledge_deficit: self.knowledge_deficit + other.knowledge_deficit,
            temporal_distance: self.temporal_distance + other.temporal_distance,
            entropy_accessibility: self.entropy_accessibility + other.entropy_accessibility,
        }
    }
}

impl Add for &SEntropy {
    type Output = SEntropy;
    
    fn add(self, other: &SEntropy) -> SEntropy {
        SEntropy {
            knowledge_deficit: self.knowledge_deficit + other.knowledge_deficit,
            temporal_distance: self.temporal_distance + other.temporal_distance,
            entropy_accessibility: self.entropy_accessibility + other.entropy_accessibility,
        }
    }
}

impl Sub for SEntropy {
    type Output = SEntropy;
    
    fn sub(self, other: SEntropy) -> SEntropy {
        SEntropy {
            knowledge_deficit: self.knowledge_deficit - other.knowledge_deficit,
            temporal_distance: self.temporal_distance - other.temporal_distance,
            entropy_accessibility: self.entropy_accessibility - other.entropy_accessibility,
        }
    }
}

impl Sub for &SEntropy {
    type Output = SEntropy;
    
    fn sub(self, other: &SEntropy) -> SEntropy {
        SEntropy {
            knowledge_deficit: self.knowledge_deficit - other.knowledge_deficit,
            temporal_distance: self.temporal_distance - other.temporal_distance,
            entropy_accessibility: self.entropy_accessibility - other.entropy_accessibility,
        }
    }
}

impl Mul<f64> for SEntropy {
    type Output = SEntropy;
    
    fn mul(self, scalar: f64) -> SEntropy {
        SEntropy {
            knowledge_deficit: self.knowledge_deficit * scalar,
            temporal_distance: self.temporal_distance * scalar,
            entropy_accessibility: self.entropy_accessibility * scalar,
        }
    }
}

impl Mul<f64> for &SEntropy {
    type Output = SEntropy;
    
    fn mul(self, scalar: f64) -> SEntropy {
        SEntropy {
            knowledge_deficit: self.knowledge_deficit * scalar,
            temporal_distance: self.temporal_distance * scalar,
            entropy_accessibility: self.entropy_accessibility * scalar,
        }
    }
}

impl Div<f64> for SEntropy {
    type Output = SEntropy;
    
    fn div(self, scalar: f64) -> SEntropy {
        SEntropy {
            knowledge_deficit: self.knowledge_deficit / scalar,
            temporal_distance: self.temporal_distance / scalar,
            entropy_accessibility: self.entropy_accessibility / scalar,
        }
    }
}

impl Default for SEntropy {
    fn default() -> Self {
        Self::origin()
    }
}

impl std::fmt::Display for SEntropy {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "S({:.6}, {:.6}, {:.6})",
            self.knowledge_deficit,
            self.temporal_distance,
            self.entropy_accessibility
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_s_entropy_creation() {
        let s = SEntropy::new(0.5, 0.3, 0.1);
        assert_eq!(s.knowledge_deficit, 0.5);
        assert_eq!(s.temporal_distance, 0.3);
        assert_eq!(s.entropy_accessibility, 0.1);
    }

    #[test]
    fn test_s_entropy_origin() {
        let origin = SEntropy::origin();
        assert_eq!(origin.magnitude(), 0.0);
        assert!(origin.is_solution());
    }

    #[test]
    fn test_s_entropy_magnitude() {
        let s = SEntropy::new(3.0, 4.0, 0.0);
        assert_eq!(s.magnitude(), 5.0);
    }

    #[test]
    fn test_s_entropy_distance() {
        let s1 = SEntropy::new(0.0, 0.0, 0.0);
        let s2 = SEntropy::new(3.0, 4.0, 0.0);
        assert_eq!(s1.distance(&s2), 5.0);
    }

    #[test]
    fn test_s_entropy_arithmetic() {
        let s1 = SEntropy::new(1.0, 2.0, 3.0);
        let s2 = SEntropy::new(2.0, 3.0, 4.0);
        
        let sum = s1.clone() + s2.clone();
        assert_eq!(sum.knowledge_deficit, 3.0);
        assert_eq!(sum.temporal_distance, 5.0);
        assert_eq!(sum.entropy_accessibility, 7.0);
        
        let diff = s2 - s1;
        assert_eq!(diff.knowledge_deficit, 1.0);
        assert_eq!(diff.temporal_distance, 1.0);
        assert_eq!(diff.entropy_accessibility, 1.0);
    }

    #[test]
    fn test_stella_scaling() {
        let s = SEntropy::new(1.0, 1.0, 1.0);
        let scaled = s.apply_stella_scaling(2.0);
        assert_eq!(scaled.knowledge_deficit, 2.0);
        assert_eq!(scaled.temporal_distance, 2.0);
        assert_eq!(scaled.entropy_accessibility, 2.0);
    }

    #[test]
    fn test_validation() {
        let valid = SEntropy::new(1.0, 2.0, 3.0);
        assert!(valid.validate().is_ok());
        
        let invalid = SEntropy::new(f64::NAN, 2.0, 3.0);
        assert!(invalid.validate().is_err());
    }
} 