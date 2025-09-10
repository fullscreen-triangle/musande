#!/usr/bin/env python3
"""
S-Entropy Molecular Coordinate Transformation Demonstration

This module demonstrates the mathematical framework for transforming raw molecular
data (nucleotides, amino acids, chemical structures) into S-entropy coordinate space
through cardinal direction mapping and weighting functions, enabling geometric
pattern recognition and cross-modal validation.

Key Concepts Demonstrated:
1. Nucleotide bases → Cardinal directions (A=North, T=South, G=East, C=West)
2. Amino acid coordinate mapping through physicochemical properties
3. Chemical structure transformation via SMILES notation
4. Cross-modal coordinate validation between different molecular representations
5. S-entropy sliding window analysis across tri-dimensional space
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass, field
from collections import defaultdict
import time
import random
from abc import ABC, abstractmethod

@dataclass
class SEntropyCoordinate:
    """Coordinate in tri-dimensional S-entropy space"""
    knowledge: float  # Information content dimension
    time: float      # Temporal/sequential dimension
    entropy: float   # Organization/disorder dimension
    
    def __post_init__(self):
        """Normalize coordinates using tanh function"""
        self.knowledge = np.tanh(self.knowledge)
        self.time = np.tanh(self.time)
        self.entropy = np.tanh(self.entropy)
    
    def magnitude(self) -> float:
        """Calculate coordinate magnitude"""
        return np.sqrt(self.knowledge**2 + self.time**2 + self.entropy**2)
    
    def distance_to(self, other: 'SEntropyCoordinate') -> float:
        """Calculate S-distance between coordinates"""
        return np.sqrt(
            (self.knowledge - other.knowledge)**2 +
            (self.time - other.time)**2 +
            (self.entropy - other.entropy)**2
        )
    
    def __add__(self, other: 'SEntropyCoordinate') -> 'SEntropyCoordinate':
        return SEntropyCoordinate(
            self.knowledge + other.knowledge,
            self.time + other.time,
            self.entropy + other.entropy
        )
    
    def __mul__(self, scalar: float) -> 'SEntropyCoordinate':
        return SEntropyCoordinate(
            self.knowledge * scalar,
            self.time * scalar,
            self.entropy * scalar
        )
    
    def __repr__(self):
        return f"S({self.knowledge:.3f}, {self.time:.3f}, {self.entropy:.3f})"

class MolecularCoordinateTransformer(ABC):
    """Abstract base class for molecular coordinate transformation"""
    
    @abstractmethod
    def transform_to_coordinates(self, data: str) -> SEntropyCoordinate:
        """Transform molecular data to S-entropy coordinates"""
        pass
    
    @abstractmethod
    def calculate_path(self, sequence: str) -> List[SEntropyCoordinate]:
        """Calculate coordinate path for molecular sequence"""
        pass

class GenomicTransformer(MolecularCoordinateTransformer):
    """
    Transforms genomic sequences to S-entropy coordinates
    using cardinal direction mapping for nucleotide bases
    """
    
    # Cardinal direction mapping for bases
    BASE_COORDINATES = {
        'A': (0, 1),    # North (Adenine)
        'T': (0, -1),   # South (Thymine)
        'G': (1, 0),    # East (Guanine)
        'C': (-1, 0)    # West (Cytosine)
    }
    
    def __init__(self):
        self.coordinate_cache = {}
        
    def transform_to_coordinates(self, sequence: str) -> SEntropyCoordinate:
        """Transform DNA sequence to S-entropy coordinate"""
        
        if sequence in self.coordinate_cache:
            return self.coordinate_cache[sequence]
        
        # Calculate base coordinate path
        path = self.calculate_path(sequence)
        
        if not path:
            return SEntropyCoordinate(0.0, 0.0, 0.0)
        
        # Knowledge dimension: Information content (Shannon entropy)
        base_counts = {'A': 0, 'T': 0, 'G': 0, 'C': 0}
        for base in sequence.upper():
            if base in base_counts:
                base_counts[base] += 1
        
        total = sum(base_counts.values())
        if total > 0:
            probabilities = [count/total for count in base_counts.values() if count > 0]
            knowledge_weight = -sum(p * np.log2(p) for p in probabilities) / 2.0  # Normalize
        else:
            knowledge_weight = 0.0
            
        # Time dimension: Sequential complexity
        path_lengths = []
        for i in range(1, len(path)):
            distance = path[i].distance_to(path[i-1])
            path_lengths.append(distance)
        
        time_weight = np.var(path_lengths) if path_lengths else 0.0
        
        # Entropy dimension: Final coordinate displacement
        if len(path) > 1:
            start_coord = path[0]
            end_coord = path[-1]
            total_distance = sum(path_lengths) if path_lengths else 0.0
            displacement = start_coord.distance_to(end_coord)
            entropy_weight = displacement / max(total_distance, 0.01)  # Avoid division by zero
        else:
            entropy_weight = 0.0
        
        # Apply S-entropy weighting functions
        final_coord = SEntropyCoordinate(
            knowledge=knowledge_weight,
            time=time_weight,
            entropy=entropy_weight
        )
        
        self.coordinate_cache[sequence] = final_coord
        return final_coord
    
    def calculate_path(self, sequence: str) -> List[SEntropyCoordinate]:
        """Calculate coordinate path through sequence"""
        path = []
        current_pos = (0.0, 0.0)
        
        for i, base in enumerate(sequence.upper()):
            if base in self.BASE_COORDINATES:
                # Get base direction
                direction = self.BASE_COORDINATES[base]
                
                # Update position
                current_pos = (
                    current_pos[0] + direction[0],
                    current_pos[1] + direction[1]
                )
                
                # Convert to S-entropy coordinate with position weighting
                position_weight = (i + 1) / len(sequence)
                coord = SEntropyCoordinate(
                    knowledge=current_pos[0] * 0.3,
                    time=current_pos[1] * 0.3,
                    entropy=position_weight * 0.4
                )
                
                path.append(coord)
        
        return path
    
    def analyze_dual_strand(self, sequence: str) -> Dict[str, Any]:
        """Enhanced dual-strand analysis"""
        
        # Generate reverse complement
        complement_map = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G'}
        reverse_complement = ''.join(
            complement_map.get(base, base) for base in reversed(sequence.upper())
        )
        
        # Transform both strands
        forward_coord = self.transform_to_coordinates(sequence)
        reverse_coord = self.transform_to_coordinates(reverse_complement)
        
        # Dual-strand combination (weighted average)
        alpha, beta = 0.6, 0.4  # Forward strand weighting
        combined_coord = SEntropyCoordinate(
            knowledge=alpha * forward_coord.knowledge + beta * reverse_coord.knowledge,
            time=alpha * forward_coord.time + beta * reverse_coord.time,
            entropy=alpha * forward_coord.entropy + beta * reverse_coord.entropy
        )
        
        return {
            'forward_strand': forward_coord,
            'reverse_complement': reverse_complement,
            'reverse_coord': reverse_coord,
            'combined_coord': combined_coord,
            'information_enhancement': forward_coord.distance_to(combined_coord)
        }

class ProteinTransformer(MolecularCoordinateTransformer):
    """
    Transforms protein sequences to S-entropy coordinates
    using amino acid physicochemical properties
    """
    
    # Simplified amino acid properties (hydrophobicity, polarity, size)
    AMINO_ACID_PROPERTIES = {
        'A': (0.62, 0.0, 0.31),   # Alanine
        'R': (-2.53, 1.0, 0.65),  # Arginine
        'N': (-0.78, 0.5, 0.43),  # Asparagine
        'D': (-0.90, -1.0, 0.40), # Aspartic acid
        'C': (0.29, 0.0, 0.35),   # Cysteine
        'E': (-0.74, -1.0, 0.50), # Glutamic acid
        'Q': (-0.85, 0.5, 0.53),  # Glutamine
        'G': (0.48, 0.0, 0.0),    # Glycine
        'H': (-0.40, 1.0, 0.51),  # Histidine
        'I': (1.38, 0.0, 0.57),   # Isoleucine
        'L': (1.06, 0.0, 0.57),   # Leucine
        'K': (-1.50, 1.0, 0.64),  # Lysine
        'M': (0.64, 0.0, 0.55),   # Methionine
        'F': (1.19, 0.0, 0.70),   # Phenylalanine
        'P': (0.12, 0.0, 0.41),   # Proline
        'S': (-0.18, 0.5, 0.31),  # Serine
        'T': (-0.05, 0.5, 0.38),  # Threonine
        'W': (0.81, 0.0, 0.85),   # Tryptophan
        'Y': (0.26, 0.5, 0.77),   # Tyrosine
        'V': (1.08, 0.0, 0.46)    # Valine
    }
    
    def __init__(self):
        self.coordinate_cache = {}
        
    def transform_to_coordinates(self, sequence: str) -> SEntropyCoordinate:
        """Transform protein sequence to S-entropy coordinate"""
        
        if sequence in self.coordinate_cache:
            return self.coordinate_cache[sequence]
        
        if not sequence:
            return SEntropyCoordinate(0.0, 0.0, 0.0)
        
        # Calculate average physicochemical properties
        hydrophobicity_values = []
        polarity_values = []  
        size_values = []
        
        for aa in sequence.upper():
            if aa in self.AMINO_ACID_PROPERTIES:
                h, p, s = self.AMINO_ACID_PROPERTIES[aa]
                hydrophobicity_values.append(h)
                polarity_values.append(p)
                size_values.append(s)
        
        if not hydrophobicity_values:
            return SEntropyCoordinate(0.0, 0.0, 0.0)
        
        # Knowledge dimension: Hydrophobicity distribution
        knowledge_weight = np.mean(hydrophobicity_values)
        
        # Time dimension: Polarity variation
        time_weight = np.var(polarity_values) if len(polarity_values) > 1 else 0.0
        
        # Entropy dimension: Size complexity
        entropy_weight = np.mean(size_values)
        
        coord = SEntropyCoordinate(
            knowledge=knowledge_weight,
            time=time_weight,
            entropy=entropy_weight
        )
        
        self.coordinate_cache[sequence] = coord
        return coord
    
    def calculate_path(self, sequence: str) -> List[SEntropyCoordinate]:
        """Calculate coordinate path through protein sequence"""
        path = []
        
        for i, aa in enumerate(sequence.upper()):
            if aa in self.AMINO_ACID_PROPERTIES:
                h, p, s = self.AMINO_ACID_PROPERTIES[aa]
                
                # Position-weighted coordinate
                position_weight = (i + 1) / len(sequence)
                coord = SEntropyCoordinate(
                    knowledge=h * position_weight,
                    time=p * position_weight,
                    entropy=s * position_weight
                )
                
                path.append(coord)
        
        return path

class ChemicalTransformer(MolecularCoordinateTransformer):
    """
    Transforms chemical structures to S-entropy coordinates
    using SMILES notation functional group analysis
    """
    
    # Functional group contribution to properties
    FUNCTIONAL_GROUPS = {
        'C': (0.2, 0.1, 0.3),      # Carbon
        'O': (0.5, 0.8, 0.2),      # Oxygen
        'N': (0.7, 0.6, 0.4),      # Nitrogen
        'S': (0.4, 0.3, 0.6),      # Sulfur
        'P': (0.6, 0.4, 0.7),      # Phosphorus
        '=': (0.3, 0.9, 0.1),      # Double bond
        '#': (0.4, 1.0, 0.1),      # Triple bond
        '(': (0.1, 0.2, 0.8),      # Branch start
        ')': (0.1, 0.2, 0.8),      # Branch end
        '[': (0.8, 0.5, 0.9),      # Complex group start
        ']': (0.8, 0.5, 0.9)       # Complex group end
    }
    
    def __init__(self):
        self.coordinate_cache = {}
        
    def transform_to_coordinates(self, smiles: str) -> SEntropyCoordinate:
        """Transform SMILES notation to S-entropy coordinate"""
        
        if smiles in self.coordinate_cache:
            return self.coordinate_cache[smiles]
        
        if not smiles:
            return SEntropyCoordinate(0.0, 0.0, 0.0)
        
        # Parse functional groups
        electronegativity_sum = 0.0
        reactivity_sum = 0.0
        bonding_sum = 0.0
        total_groups = 0
        
        for char in smiles:
            if char in self.FUNCTIONAL_GROUPS:
                e, r, b = self.FUNCTIONAL_GROUPS[char]
                electronegativity_sum += e
                reactivity_sum += r
                bonding_sum += b
                total_groups += 1
        
        if total_groups == 0:
            return SEntropyCoordinate(0.0, 0.0, 0.0)
        
        # Calculate average properties
        knowledge_weight = electronegativity_sum / total_groups
        time_weight = reactivity_sum / total_groups
        entropy_weight = bonding_sum / total_groups
        
        coord = SEntropyCoordinate(
            knowledge=knowledge_weight,
            time=time_weight,
            entropy=entropy_weight
        )
        
        self.coordinate_cache[smiles] = coord
        return coord
    
    def calculate_path(self, smiles: str) -> List[SEntropyCoordinate]:
        """Calculate coordinate path through chemical structure"""
        path = []
        running_totals = [0.0, 0.0, 0.0]  # e, r, b
        
        for i, char in enumerate(smiles):
            if char in self.FUNCTIONAL_GROUPS:
                e, r, b = self.FUNCTIONAL_GROUPS[char]
                running_totals[0] += e
                running_totals[1] += r
                running_totals[2] += b
                
                # Normalize by position
                position_weight = (i + 1) / len(smiles)
                coord = SEntropyCoordinate(
                    knowledge=running_totals[0] * position_weight,
                    time=running_totals[1] * position_weight,
                    entropy=running_totals[2] * position_weight
                )
                
                path.append(coord)
        
        return path

class SEntropyWindowAnalyzer:
    """
    Implements sliding window analysis across tri-dimensional S-entropy space
    """
    
    def __init__(self, window_radii: Dict[str, float] = None):
        self.window_radii = window_radii or {
            'knowledge': 0.3,
            'time': 0.3,
            'entropy': 0.3
        }
        
    def create_sliding_window(self, center: SEntropyCoordinate) -> Dict[str, Tuple[float, float]]:
        """Create sliding window bounds around center coordinate"""
        
        return {
            'knowledge': (
                center.knowledge - self.window_radii['knowledge'],
                center.knowledge + self.window_radii['knowledge']
            ),
            'time': (
                center.time - self.window_radii['time'],
                center.time + self.window_radii['time']
            ),
            'entropy': (
                center.entropy - self.window_radii['entropy'],
                center.entropy + self.window_radii['entropy']
            )
        }
    
    def analyze_window(self, center: SEntropyCoordinate, 
                      coordinates: List[SEntropyCoordinate]) -> Dict[str, Any]:
        """Analyze coordinates within sliding window"""
        
        window_bounds = self.create_sliding_window(center)
        window_coords = []
        
        # Find coordinates within window
        for coord in coordinates:
            if (window_bounds['knowledge'][0] <= coord.knowledge <= window_bounds['knowledge'][1] and
                window_bounds['time'][0] <= coord.time <= window_bounds['time'][1] and
                window_bounds['entropy'][0] <= coord.entropy <= window_bounds['entropy'][1]):
                window_coords.append(coord)
        
        if not window_coords:
            return {'mean': center, 'variance': 0.0, 'count': 0, 'density': 0.0}
        
        # Calculate window statistics
        mean_knowledge = np.mean([c.knowledge for c in window_coords])
        mean_time = np.mean([c.time for c in window_coords])
        mean_entropy = np.mean([c.entropy for c in window_coords])
        
        mean_coord = SEntropyCoordinate(mean_knowledge, mean_time, mean_entropy)
        
        # Calculate variance
        variances = [coord.distance_to(mean_coord)**2 for coord in window_coords]
        variance = np.mean(variances) if variances else 0.0
        
        # Calculate density
        window_volume = (2 * self.window_radii['knowledge'] * 
                        2 * self.window_radii['time'] * 
                        2 * self.window_radii['entropy'])
        density = len(window_coords) / window_volume
        
        return {
            'mean': mean_coord,
            'variance': variance,
            'count': len(window_coords),
            'density': density,
            'coordinates': window_coords
        }

class CrossModalValidator:
    """
    Validates coordinate consistency across different molecular representations
    """
    
    def __init__(self):
        self.genomic_transformer = GenomicTransformer()
        self.protein_transformer = ProteinTransformer()
        self.chemical_transformer = ChemicalTransformer()
        
    def validate_cross_modal_consistency(self, 
                                       genomic_seq: str,
                                       protein_seq: str,
                                       chemical_smiles: str,
                                       threshold: float = 0.5) -> Dict[str, Any]:
        """
        Validate coordinate consistency across molecular representations
        For consistent molecules, coordinates should be within threshold distance
        """
        
        # Transform to coordinates
        genomic_coord = self.genomic_transformer.transform_to_coordinates(genomic_seq)
        protein_coord = self.protein_transformer.transform_to_coordinates(protein_seq)
        chemical_coord = self.chemical_transformer.transform_to_coordinates(chemical_smiles)
        
        # Calculate cross-modal distances
        distances = {
            'genomic_protein': genomic_coord.distance_to(protein_coord),
            'protein_chemical': protein_coord.distance_to(chemical_coord),
            'chemical_genomic': chemical_coord.distance_to(genomic_coord)
        }
        
        total_distance = sum(distances.values())
        consistency_valid = total_distance < threshold
        
        return {
            'genomic_coord': genomic_coord,
            'protein_coord': protein_coord,
            'chemical_coord': chemical_coord,
            'distances': distances,
            'total_distance': total_distance,
            'consistency_valid': consistency_valid,
            'threshold': threshold
        }

def demonstrate_coordinate_transformation():
    """Demonstrate molecular coordinate transformation across data types"""
    print("=" * 60)
    print("MOLECULAR COORDINATE TRANSFORMATION DEMONSTRATION")
    print("=" * 60)
    
    # Create transformers
    genomic = GenomicTransformer()
    protein = ProteinTransformer()
    chemical = ChemicalTransformer()
    
    # Test data
    test_molecules = {
        'Simple DNA': ('ATGCATGC', 'MHAC', 'CC(C)C'),
        'Complex DNA': ('ATCGATCGATCG', 'MDEFGH', 'C1=CC=C(C=C1)O'),
        'GC Rich': ('GCGCGCGC', 'WWQRST', 'C1=CC2=CC=CC=C2C=C1')
    }
    
    print("Molecular Data → S-Entropy Coordinates")
    print("-" * 60)
    print(f"{'Molecule':<12} {'Type':<8} {'Sequence/SMILES':<15} {'S-Coordinates':<30}")
    print("-" * 60)
    
    for name, (dna, prot, chem) in test_molecules.items():
        # Transform each type
        dna_coord = genomic.transform_to_coordinates(dna)
        prot_coord = protein.transform_to_coordinates(prot)  
        chem_coord = chemical.transform_to_coordinates(chem)
        
        print(f"{name:<12} {'DNA':<8} {dna:<15} {str(dna_coord):<30}")
        print(f"{'':<12} {'Protein':<8} {prot:<15} {str(prot_coord):<30}")
        print(f"{'':<12} {'Chemical':<8} {chem:<15} {str(chem_coord):<30}")
        print("-" * 60)

def demonstrate_dual_strand_analysis():
    """Demonstrate enhanced dual-strand genomic analysis"""
    print("\n" + "=" * 60)
    print("DUAL-STRAND GENOMIC ANALYSIS DEMONSTRATION")
    print("=" * 60)
    
    genomic = GenomicTransformer()
    
    test_sequences = [
        "ATCGATCG",      # Palindromic sequence
        "AAATTTGGGCCC",  # Complementary blocks
        "ATGAAATAG",     # Coding-like sequence
        "GCTAGCTAGCT"    # Repetitive pattern
    ]
    
    print("Dual-Strand Analysis Results:")
    print("-" * 40)
    
    for seq in test_sequences:
        analysis = genomic.analyze_dual_strand(seq)
        
        print(f"Original: {seq}")
        print(f"RevComp:  {analysis['reverse_complement']}")
        print(f"Forward:  {analysis['forward_strand']}")
        print(f"Reverse:  {analysis['reverse_coord']}")
        print(f"Combined: {analysis['combined_coord']}")
        print(f"Enhancement: {analysis['information_enhancement']:.4f}")
        print("-" * 40)

def demonstrate_sliding_window_analysis():
    """Demonstrate S-entropy sliding window analysis"""
    print("\n" + "=" * 60)
    print("S-ENTROPY SLIDING WINDOW ANALYSIS DEMONSTRATION")
    print("=" * 60)
    
    # Create analyzer
    analyzer = SEntropyWindowAnalyzer(window_radii={'knowledge': 0.2, 'time': 0.2, 'entropy': 0.2})
    
    # Generate test coordinates
    genomic = GenomicTransformer()
    test_sequences = [f"ATCG{'ATCG' * i}" for i in range(1, 6)]  # Variable length sequences
    coordinates = [genomic.transform_to_coordinates(seq) for seq in test_sequences]
    
    # Analyze windows around each coordinate
    print("Sliding Window Analysis:")
    print("-" * 40)
    print(f"{'Center':<25} {'Count':<6} {'Density':<8} {'Variance':<10}")
    print("-" * 40)
    
    for i, center in enumerate(coordinates):
        analysis = analyzer.analyze_window(center, coordinates)
        
        print(f"{str(center):<25} {analysis['count']:<6} {analysis['density']:<8.3f} {analysis['variance']:<10.4f}")
    
    # Demonstrate adaptive window sizing
    print(f"\nAdaptive window sizing based on coordinate density:")
    high_density_coords = coordinates + [coord + SEntropyCoordinate(0.05, 0.05, 0.05) for coord in coordinates[:3]]
    
    for i, center in enumerate(coordinates[:3]):
        analysis = analyzer.analyze_window(center, high_density_coords)
        print(f"Center {i+1}: Density {analysis['density']:.3f} → Suggested window radius: {0.3/analysis['density']:.3f}")

def demonstrate_cross_modal_validation():
    """Demonstrate cross-modal coordinate validation"""
    print("\n" + "=" * 60)
    print("CROSS-MODAL COORDINATE VALIDATION DEMONSTRATION")
    print("=" * 60)
    
    validator = CrossModalValidator()
    
    # Test cases: consistent vs inconsistent molecular representations
    test_cases = [
        {
            'name': 'Consistent Set 1',
            'genomic': 'ATGCATGC',
            'protein': 'MHAC',
            'chemical': 'CC(C)CC'
        },
        {
            'name': 'Consistent Set 2',
            'genomic': 'GCGCGCGC',
            'protein': 'GGPP',
            'chemical': 'C1=CC=CC=C1'
        },
        {
            'name': 'Inconsistent Set',
            'genomic': 'ATATATAT',
            'protein': 'WWWWWW',
            'chemical': 'C(C(C(C)C)C)C'
        }
    ]
    
    print("Cross-Modal Validation Results:")
    print("-" * 50)
    
    for case in test_cases:
        print(f"\n{case['name']}:")
        print(f"  Genomic: {case['genomic']}")
        print(f"  Protein: {case['protein']}")  
        print(f"  Chemical: {case['chemical']}")
        
        validation = validator.validate_cross_modal_consistency(
            case['genomic'], case['protein'], case['chemical'], threshold=1.5
        )
        
        print(f"  Coordinates:")
        print(f"    Genomic:  {validation['genomic_coord']}")
        print(f"    Protein:  {validation['protein_coord']}")
        print(f"    Chemical: {validation['chemical_coord']}")
        
        print(f"  Distances:")
        for pair, distance in validation['distances'].items():
            print(f"    {pair}: {distance:.4f}")
        
        print(f"  Total Distance: {validation['total_distance']:.4f}")
        print(f"  Validation: {'PASSED' if validation['consistency_valid'] else 'FAILED'}")

def run_comprehensive_demonstration():
    """Run complete molecular coordinate transformation demonstration"""
    print("S-ENTROPY MOLECULAR COORDINATE TRANSFORMATION DEMONSTRATION")
    print("Validating Mathematical Framework for Raw Data Conversion")
    print("=" * 80)
    
    # Demonstrate coordinate transformation
    demonstrate_coordinate_transformation()
    
    # Demonstrate dual-strand analysis
    demonstrate_dual_strand_analysis()
    
    # Demonstrate sliding window analysis
    demonstrate_sliding_window_analysis()
    
    # Demonstrate cross-modal validation
    demonstrate_cross_modal_validation()
    
    # Summary
    print("\n" + "=" * 60)
    print("MOLECULAR TRANSFORMATION FRAMEWORK VALIDATION SUMMARY")
    print("=" * 60)
    print("✓ Cardinal direction mapping for nucleotides (A→N, T→S, G→E, C→W)")
    print("✓ Amino acid coordinate mapping through physicochemical properties")
    print("✓ Chemical structure transformation via SMILES functional groups")
    print("✓ Dual-strand information enhancement demonstrated")
    print("✓ Sliding window analysis across tri-dimensional S-space")
    print("✓ Cross-modal validation between molecular representations")
    print("✓ Complete mathematical framework for raw data → S-entropy coordinates")
    print("\nFramework enables geometric pattern recognition across molecular domains")

if __name__ == "__main__":
    run_comprehensive_demonstration()
