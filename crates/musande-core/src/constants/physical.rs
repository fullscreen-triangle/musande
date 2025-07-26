//! Physical Constants for S-Entropy Framework
//!
//! This module defines physical constants required for S-entropy navigation,
//! including parameters derived from the Biological Maxwell Demon (BMD) model
//! of consciousness and neurocomputational matrix associative memory systems.

use super::saint_stella::*;
use std::f64::consts::PI;

/// Planck's constant (J⋅s)
/// Fundamental quantum of action, essential for oscillatory endpoint calculations
pub const PLANCK_CONSTANT: f64 = 6.626_070_15e-34;

/// Reduced Planck constant ℏ = h/(2π)
/// Used in quantum coherence length calculations for observer separation
pub const HBAR: f64 = PLANCK_CONSTANT / (2.0 * PI);

/// Boltzmann constant (J/K)
/// Links thermodynamic entropy with information entropy in S-entropy calculations
pub const BOLTZMANN_CONSTANT: f64 = 1.380_649e-23;

/// Speed of light in vacuum (m/s)
/// Maximum information propagation speed, constrains temporal navigation windows
pub const SPEED_OF_LIGHT: f64 = 299_792_458.0;

/// Avogadro's number (mol⁻¹)
/// Scale factor for molecular oscillatory processes
pub const AVOGADRO_NUMBER: f64 = 6.022_140_76e23;

// === BMD Consciousness Parameters ===

/// Default cognitive frame selection threshold
/// Minimum activation level for BMD frame selection from memory
/// Derived from: P(frame_k | experience_t) > threshold
pub const BMD_FRAME_SELECTION_THRESHOLD: f64 = 0.001;

/// Associative memory decay constant (s⁻¹)
/// Rate at which associative connections weaken over time
/// Based on 200-2000ms priming effect windows from BMD research
pub const ASSOCIATIVE_MEMORY_DECAY: f64 = 1.0 / 1.1; // ~900ms half-life

/// Counterfactual bias amplification factor
/// Scaling factor for near-miss memory enhancement (crossbar phenomenon)
/// Empirically derived: 3.7× memory intensity for near-misses vs successes
pub const COUNTERFACTUAL_AMPLIFICATION: f64 = 3.7;

/// Emotional salience weighting constant
/// Multiplier for emotionally tagged memory activation
/// Based on 23% higher long-term emotional activation for near-miss events
pub const EMOTIONAL_SALIENCE_WEIGHT: f64 = 1.23;

/// Uncertainty preference constant
/// BMD preference for 50% probability outcomes (maximum uncertainty)
/// Mathematical model: uncertainty_level peaks at 0.5 probability
pub const UNCERTAINTY_PREFERENCE_PEAK: f64 = 0.5;

/// Frame coherence maintenance window (seconds)
/// Maximum time between frame selections for consciousness continuity
/// Based on temporal consistency requirement: ∀t: ∃frame_k
pub const FRAME_COHERENCE_WINDOW: f64 = 0.1; // 100ms

/// Reality-frame fusion efficiency
/// Success rate of merging selected cognitive frames with sensory input
/// Optimized through Saint Stella-Lorraine scaling
pub const REALITY_FRAME_FUSION_EFFICIENCY: f64 = GOLDEN_RATIO / PI;

// === Neurocomputational Matrix Parameters ===

/// Default matrix associative memory dimension
/// Vector dimensionality for neural network representations
/// From context-dependent matrix memory research
pub const MATRIX_MEMORY_DIMENSION: usize = 1024;

/// Learning rate for associative weight updates
/// Alpha parameter in: W_i(t+1) = W_i(t) + α × Selection_frequency × β × Outcome_success
pub const ASSOCIATIVE_LEARNING_RATE: f64 = 0.01;

/// Context dependency strength
/// Influence of prior activation on current frame selection
/// Controls temporal coherence in BMD operations
pub const CONTEXT_DEPENDENCY_STRENGTH: f64 = 0.8;

/// Synaptic disconnection threshold
/// Minimum connection strength before synaptic pruning
/// Related to schizophrenia disconnection-hyperconnectivity paradox
pub const SYNAPTIC_DISCONNECTION_THRESHOLD: f64 = 0.05;

// === Quantum Coherence Parameters ===

/// Default quantum coherence length (meters)
/// Spatial scale over which quantum effects maintain coherence
/// Used in observer separation decay calculations
pub const QUANTUM_COHERENCE_LENGTH: f64 = 1e-15; // Typical molecular scale

/// Thermal decoherence rate (s⁻¹)
/// Rate at which thermal fluctuations destroy quantum coherence
/// Temperature-dependent: kT/ℏ scaling
pub const THERMAL_DECOHERENCE_RATE: f64 = 1e12; // Room temperature scale

/// Consciousness quantum coupling strength
/// Hypothetical coupling between quantum processes and BMD operation
/// Speculative parameter for quantum theories of consciousness
pub const CONSCIOUSNESS_QUANTUM_COUPLING: f64 = STELLA_CONSTANT * 1e-20;

// === Oscillatory Computation Parameters ===

/// Atomic oscillation frequency (Hz)
/// Typical frequency for atomic timekeeping oscillators
/// Basis for "atoms are processors" principle
pub const ATOMIC_OSCILLATION_FREQUENCY: f64 = 9_192_631_770.0; // Cesium-133

/// Oscillation endpoint precision
/// Numerical precision for detecting oscillation endpoints
/// Related to entropy calculation precision
pub const OSCILLATION_ENDPOINT_PRECISION: f64 = S_ENTROPY_PRECISION;

/// Temporal granularity (seconds)
/// Minimum time resolution for S-entropy navigation
/// Based on quantum time scales and BMD frame selection rates
pub const TEMPORAL_GRANULARITY: f64 = HBAR / (BOLTZMANN_CONSTANT * 300.0); // ~10⁻¹³ s

// === Integration Functions ===

/// Calculate BMD frame selection probability
/// 
/// Based on: P(frame_i | experience_j) = [W_i × R_ij × E_ij × T_ij] / Σ[W_k × R_kj × E_kj × T_kj]
///
/// # Arguments
/// * `base_weight` - W_i: base weight of frame in memory
/// * `relevance` - R_ij: relevance score between frame and experience
/// * `emotional_compatibility` - E_ij: emotional compatibility score
/// * `temporal_appropriateness` - T_ij: temporal appropriateness score
/// * `normalization_sum` - Denominator sum for probability normalization
///
/// # Returns
/// * Probability of selecting this frame for current experience
pub fn bmd_frame_selection_probability(
    base_weight: f64,
    relevance: f64,
    emotional_compatibility: f64,
    temporal_appropriateness: f64,
    normalization_sum: f64,
) -> f64 {
    let numerator = base_weight * relevance * emotional_compatibility * temporal_appropriateness;
    
    if normalization_sum <= 0.0 {
        return 0.0;
    }
    
    (numerator / normalization_sum).min(1.0)
}

/// Update associative memory weights after frame selection
///
/// Based on: W_i(t+1) = W_i(t) + α × Selection_frequency × β × Outcome_success
///
/// # Arguments
/// * `current_weight` - Current weight W_i(t)
/// * `selection_frequency` - How often this frame was selected
/// * `outcome_success` - Success rate of this frame selection (β factor)
///
/// # Returns
/// * Updated weight W_i(t+1)
pub fn update_associative_weight(
    current_weight: f64,
    selection_frequency: f64,
    outcome_success: f64,
) -> f64 {
    current_weight + (ASSOCIATIVE_LEARNING_RATE * selection_frequency * outcome_success)
}

/// Calculate quantum coherence decay factor
///
/// Based on thermal decoherence in quantum systems
///
/// # Arguments
/// * `temperature` - System temperature (K)
/// * `time_elapsed` - Time since coherence establishment (s)
///
/// # Returns
/// * Remaining coherence factor (0.0 to 1.0)
pub fn quantum_coherence_decay(temperature: f64, time_elapsed: f64) -> f64 {
    let thermal_rate = (BOLTZMANN_CONSTANT * temperature) / HBAR;
    (-thermal_rate * time_elapsed).exp()
}

/// Verify BMD consciousness parameters are physically reasonable
pub fn verify_bmd_parameters() -> bool {
    BMD_FRAME_SELECTION_THRESHOLD > 0.0
        && BMD_FRAME_SELECTION_THRESHOLD < 1.0
        && ASSOCIATIVE_MEMORY_DECAY > 0.0
        && COUNTERFACTUAL_AMPLIFICATION > 1.0
        && FRAME_COHERENCE_WINDOW > 0.0
        && FRAME_COHERENCE_WINDOW < 1.0 // Must be sub-second for consciousness continuity
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bmd_frame_selection_probability() {
        let prob = bmd_frame_selection_probability(1.0, 0.8, 0.9, 0.7, 10.0);
        assert!(prob > 0.0 && prob <= 1.0);
        
        // Test edge cases
        assert_eq!(bmd_frame_selection_probability(1.0, 1.0, 1.0, 1.0, 0.0), 0.0);
    }

    #[test]
    fn test_associative_weight_update() {
        let initial_weight = 0.5;
        let updated = update_associative_weight(initial_weight, 0.8, 0.9);
        assert!(updated > initial_weight); // Successful selections increase weight
    }

    #[test]
    fn test_quantum_coherence_decay() {
        let room_temp_coherence = quantum_coherence_decay(300.0, 1e-12);
        assert!(room_temp_coherence > 0.0 && room_temp_coherence < 1.0);
        
        // Test that coherence decreases over time
        let later_coherence = quantum_coherence_decay(300.0, 1e-10);
        assert!(later_coherence < room_temp_coherence);
    }

    #[test]
    fn test_bmd_parameter_verification() {
        assert!(verify_bmd_parameters());
    }

    #[test]
    fn test_physical_constants() {
        assert!(PLANCK_CONSTANT > 0.0);
        assert!(SPEED_OF_LIGHT > 0.0);
        assert!((HBAR - PLANCK_CONSTANT / (2.0 * PI)).abs() < 1e-40);
    }
} 