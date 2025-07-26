//! Error types for the S-Entropy Framework
//!
//! This module defines the error types used throughout the Musande system,
//! providing comprehensive error handling for entropy navigation, alignment failures,
//! and ridiculous solution generation.

use thiserror::Error;

/// Result type alias for Musande operations
pub type Result<T> = std::result::Result<T, MusandeError>;

/// Comprehensive error types for the S-Entropy Framework
#[derive(Error, Debug, Clone, PartialEq)]
pub enum MusandeError {
    /// Errors related to S-entropy calculations and navigation
    #[error("S-entropy calculation error: {0}")]
    SEntropyCalculation(String),

    /// Errors in tri-dimensional alignment processes
    #[error("Tri-dimensional alignment failed: {0}")]
    AlignmentFailure(String),

    /// Observer-process separation constraint violations
    #[error("Observer separation constraint violated: {0}")]
    ObserverSeparationViolation(String),

    /// Oscillation endpoint detection failures
    #[error("Cannot detect oscillation endpoint: {0}")]
    OscillationEndpointError(String),

    /// Invalid ridiculous solution generation
    #[error("Ridiculous solution generation failed: {0}")]
    RidiculousSolutionError(String),

    /// Global S-viability constraint violations
    #[error("Global S-viability violated: {0}")]
    GlobalViabilityViolation(String),

    /// Mathematical computation errors
    #[error("Mathematical computation error: {0}")]
    MathematicalError(String),

    /// Matrix associative memory errors (inspired by the neurocomputational paper)
    #[error("Matrix associative memory error: {0}")]
    AssociativeMemoryError(String),

    /// Context-dependent processing errors
    #[error("Context-dependent processing failed: {0}")]
    ContextProcessingError(String),

    /// Configuration and initialization errors
    #[error("Configuration error: {0}")]
    InvalidConfiguration(String),

    /// Input/Output errors
    #[error("I/O error: {0}")]
    IoError(String),

    /// Serialization/Deserialization errors
    #[error("Serialization error: {0}")]
    SerializationError(String),

    /// Network and service communication errors
    #[error("Network error: {0}")]
    NetworkError(String),

    /// Timeout errors for entropy navigation
    #[error("Operation timed out: {0}")]
    Timeout(String),

    /// Resource exhaustion errors
    #[error("Resource exhausted: {0}")]
    ResourceExhausted(String),

    /// Impossibility factor scaling errors
    #[error("Impossibility factor scaling failed: {0}")]
    ImpossibilityScalingError(String),

    /// Temporal navigation errors
    #[error("Temporal navigation error: {0}")]
    TemporalNavigationError(String),

    /// Knowledge extraction errors
    #[error("Knowledge extraction failed: {0}")]
    KnowledgeExtractionError(String),

    /// Entropy space mapping errors
    #[error("Entropy space mapping failed: {0}")]
    EntropySpaceMappingError(String),
}

impl MusandeError {
    /// Check if this error is recoverable through ridiculous solution generation
    pub fn is_recoverable_through_ridiculous_solutions(&self) -> bool {
        matches!(
            self,
            MusandeError::AlignmentFailure(_)
                | MusandeError::ObserverSeparationViolation(_)
                | MusandeError::OscillationEndpointError(_)
                | MusandeError::ContextProcessingError(_)
                | MusandeError::TemporalNavigationError(_)
        )
    }

    /// Check if this error indicates a fundamental mathematical impossibility
    pub fn is_fundamental_impossibility(&self) -> bool {
        matches!(
            self,
            MusandeError::GlobalViabilityViolation(_) | MusandeError::MathematicalError(_)
        )
    }

    /// Get the error category for diagnostic purposes
    pub fn category(&self) -> &'static str {
        match self {
            MusandeError::SEntropyCalculation(_) => "entropy",
            MusandeError::AlignmentFailure(_) => "alignment", 
            MusandeError::ObserverSeparationViolation(_) => "observer",
            MusandeError::OscillationEndpointError(_) => "oscillation",
            MusandeError::RidiculousSolutionError(_) => "ridiculous",
            MusandeError::GlobalViabilityViolation(_) => "viability",
            MusandeError::MathematicalError(_) => "mathematics",
            MusandeError::AssociativeMemoryError(_) => "memory",
            MusandeError::ContextProcessingError(_) => "context",
            MusandeError::InvalidConfiguration(_) => "configuration",
            MusandeError::IoError(_) => "io",
            MusandeError::SerializationError(_) => "serialization",
            MusandeError::NetworkError(_) => "network",
            MusandeError::Timeout(_) => "timeout",
            MusandeError::ResourceExhausted(_) => "resources",
            MusandeError::ImpossibilityScalingError(_) => "impossibility",
            MusandeError::TemporalNavigationError(_) => "temporal",
            MusandeError::KnowledgeExtractionError(_) => "knowledge",
            MusandeError::EntropySpaceMappingError(_) => "mapping",
        }
    }
}

// Convenient conversion from common error types
impl From<std::io::Error> for MusandeError {
    fn from(err: std::io::Error) -> Self {
        MusandeError::IoError(err.to_string())
    }
}

impl From<serde_json::Error> for MusandeError {
    fn from(err: serde_json::Error) -> Self {
        MusandeError::SerializationError(err.to_string())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_error_categories() {
        let entropy_error = MusandeError::SEntropyCalculation("test".to_string());
        assert_eq!(entropy_error.category(), "entropy");

        let alignment_error = MusandeError::AlignmentFailure("test".to_string());
        assert_eq!(alignment_error.category(), "alignment");
    }

    #[test]
    fn test_recoverable_errors() {
        let alignment_error = MusandeError::AlignmentFailure("test".to_string());
        assert!(alignment_error.is_recoverable_through_ridiculous_solutions());

        let math_error = MusandeError::MathematicalError("test".to_string());
        assert!(!math_error.is_recoverable_through_ridiculous_solutions());
    }

    #[test]
    fn test_fundamental_impossibilities() {
        let viability_error = MusandeError::GlobalViabilityViolation("test".to_string());
        assert!(viability_error.is_fundamental_impossibility());

        let alignment_error = MusandeError::AlignmentFailure("test".to_string());
        assert!(!alignment_error.is_fundamental_impossibility());
    }
} 