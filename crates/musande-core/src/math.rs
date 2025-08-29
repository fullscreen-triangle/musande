//! Mathematical operations for S-entropy calculations
//!
//! This module provides core mathematical functions for S-entropy navigation,
//! coordinate transformations, and St. Stella constant calculations.

use crate::constants::saint_stella::*;
use nalgebra::{Vector3, Matrix3};

/// Calculate the S-entropy distance metric between two coordinates
pub fn s_entropy_distance(a: &Vector3<f64>, b: &Vector3<f64>) -> f64 {
    (a - b).magnitude()
}

/// Apply St. Stella constant scaling to a value
pub fn apply_stella_scaling(value: f64, impossibility_level: f64) -> f64 {
    value * stella_scaling_factor(impossibility_level)
}

/// Calculate navigation efficiency between two points
pub fn navigation_efficiency(distance: f64) -> f64 {
    if distance < S_ENTROPY_PRECISION {
        f64::INFINITY
    } else {
        STELLA_CONSTANT / distance
    }
}

/// Check if a value is within S-entropy precision threshold
pub fn within_precision(value: f64) -> bool {
    value.abs() <= S_ENTROPY_PRECISION
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_distance_calculation() {
        let a = Vector3::new(1.0, 2.0, 3.0);
        let b = Vector3::new(4.0, 6.0, 8.0);
        let distance = s_entropy_distance(&a, &b);
        assert!(distance > 0.0);
    }

    #[test]
    fn test_precision_check() {
        assert!(within_precision(1e-13));
        assert!(!within_precision(1e-10));
    }
} 