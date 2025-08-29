//! S-Entropy Framework Optimization Demo
//!
//! This demonstrates how the S-Entropy Framework can solve optimization problems
//! through coordinate navigation rather than traditional computational search.

use musande_core::{SEntropy, constants::saint_stella::STELLA_CONSTANT};
use musande_alignment::{MusandeAlignment, AlignmentStrategy};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Represents different types of optimization problems
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum OptimizationProblem {
    /// Resource allocation with constraints
    ResourceAllocation {
        resources: Vec<f64>,
        demands: Vec<f64>,
        constraints: Vec<f64>,
    },
    /// Portfolio optimization
    Portfolio {
        assets: Vec<String>,
        returns: Vec<f64>,
        risks: Vec<f64>,
        target_return: f64,
    },
    /// Production scheduling
    Scheduling {
        tasks: Vec<String>,
        durations: Vec<f64>,
        dependencies: Vec<(usize, usize)>,
        deadline: f64,
    },
    /// Supply chain optimization
    SupplyChain {
        suppliers: Vec<String>,
        costs: Vec<f64>,
        capacities: Vec<f64>,
        demand: f64,
    },
}

impl OptimizationProblem {
    /// Map the optimization problem to S-entropy coordinates
    pub fn to_s_entropy(&self) -> SEntropy {
        match self {
            OptimizationProblem::ResourceAllocation { resources, demands, constraints } => {
                let total_demand: f64 = demands.iter().sum();
                let total_supply: f64 = resources.iter().sum();
                let constraint_pressure: f64 = constraints.iter().sum();

                SEntropy::new(
                    // Knowledge deficit: How much we don't know about optimal allocation
                    (total_demand / total_supply).ln().abs(),
                    // Temporal distance: Complexity of the allocation problem
                    (demands.len() as f64).sqrt() * STELLA_CONSTANT,
                    // Entropy accessibility: Constraint satisfaction difficulty
                    constraint_pressure / total_supply,
                )
            },
            
            OptimizationProblem::Portfolio { assets, returns, risks, target_return } => {
                let avg_return: f64 = returns.iter().sum::<f64>() / returns.len() as f64;
                let avg_risk: f64 = risks.iter().sum::<f64>() / risks.len() as f64;
                let return_gap = (target_return - avg_return).abs();

                SEntropy::new(
                    // Knowledge deficit: Uncertainty about future performance
                    avg_risk / avg_return.abs().max(0.01),
                    // Temporal distance: Time to achieve target return
                    return_gap * (assets.len() as f64).sqrt(),
                    // Entropy accessibility: Market efficiency constraints
                    avg_risk * STELLA_CONSTANT,
                )
            },
            
            OptimizationProblem::Scheduling { tasks, durations, dependencies, deadline } => {
                let total_duration: f64 = durations.iter().sum();
                let dependency_complexity = dependencies.len() as f64 / tasks.len() as f64;
                let deadline_pressure = total_duration / deadline;

                SEntropy::new(
                    // Knowledge deficit: Uncertainty about task dependencies
                    dependency_complexity * (tasks.len() as f64).ln(),
                    // Temporal distance: Gap between required and available time
                    deadline_pressure.max(1.0).ln(),
                    // Entropy accessibility: Scheduling constraint complexity
                    dependency_complexity * STELLA_CONSTANT,
                )
            },
            
            OptimizationProblem::SupplyChain { suppliers, costs, capacities, demand } => {
                let total_capacity: f64 = capacities.iter().sum();
                let avg_cost: f64 = costs.iter().sum::<f64>() / costs.len() as f64;
                let capacity_utilization = demand / total_capacity;

                SEntropy::new(
                    // Knowledge deficit: Uncertainty about supply reliability
                    capacity_utilization.ln().abs(),
                    // Temporal distance: Supply chain complexity
                    (suppliers.len() as f64).sqrt() * avg_cost / 100.0,
                    // Entropy accessibility: Cost optimization constraints
                    capacity_utilization * STELLA_CONSTANT,
                )
            },
        }
    }
}

/// Solution to an optimization problem in S-entropy space
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OptimizationSolution {
    pub original_problem: OptimizationProblem,
    pub s_entropy_coordinate: SEntropy,
    pub aligned_coordinate: SEntropy,
    pub strategy_used: AlignmentStrategy,
    pub solution_quality: f64,
    pub computation_time: f64,
    pub recommendations: Vec<String>,
}

impl OptimizationSolution {
    /// Generate human-readable recommendations based on the solution
    pub fn generate_recommendations(&mut self) {
        match &self.original_problem {
            OptimizationProblem::ResourceAllocation { .. } => {
                self.recommendations = vec![
                    "Balance resource allocation based on demand priorities".to_string(),
                    "Consider constraint relaxation for improved efficiency".to_string(),
                    "Implement dynamic reallocation based on real-time demand".to_string(),
                ];
            },
            OptimizationProblem::Portfolio { .. } => {
                self.recommendations = vec![
                    "Diversify across uncorrelated assets".to_string(),
                    "Adjust risk tolerance based on market conditions".to_string(),
                    "Implement dynamic rebalancing strategy".to_string(),
                ];
            },
            OptimizationProblem::Scheduling { .. } => {
                self.recommendations = vec![
                    "Prioritize critical path tasks".to_string(),
                    "Build buffer time for high-risk dependencies".to_string(),
                    "Consider parallel execution where possible".to_string(),
                ];
            },
            OptimizationProblem::SupplyChain { .. } => {
                self.recommendations = vec![
                    "Diversify supplier base to reduce risk".to_string(),
                    "Optimize transportation costs through consolidation".to_string(),
                    "Implement just-in-time delivery where feasible".to_string(),
                ];
            },
        }
    }
}

/// S-Entropy Optimization Engine
pub struct SEntropyOptimizer {
    alignment_engine: MusandeAlignment,
}

impl SEntropyOptimizer {
    pub fn new() -> Self {
        Self {
            alignment_engine: MusandeAlignment::new(),
        }
    }

    /// Solve an optimization problem using S-entropy navigation
    pub async fn solve(&self, problem: OptimizationProblem) -> anyhow::Result<OptimizationSolution> {
        let start_time = std::time::Instant::now();
        
        // Map problem to S-entropy coordinates
        let s_entropy_coord = problem.to_s_entropy();
        println!("Problem mapped to S-entropy: {}", s_entropy_coord);

        // Define target (optimal solution at origin)
        let target = SEntropy::origin();

        // Perform S-entropy alignment
        let alignment_result = self.alignment_engine.align_to_solution(s_entropy_coord.clone(), target)?;
        
        let computation_time = start_time.elapsed().as_secs_f64();
        
        // Calculate solution quality
        let solution_quality = 1.0 / (1.0 + alignment_result.alignment_error);

        let mut solution = OptimizationSolution {
            original_problem: problem,
            s_entropy_coordinate: s_entropy_coord,
            aligned_coordinate: alignment_result.aligned,
            strategy_used: alignment_result.strategy,
            solution_quality,
            computation_time,
            recommendations: Vec::new(),
        };

        solution.generate_recommendations();
        
        Ok(solution)
    }

    /// Solve multiple optimization problems and compare approaches
    pub async fn benchmark_solutions(&self, problems: Vec<OptimizationProblem>) -> anyhow::Result<Vec<OptimizationSolution>> {
        let mut solutions = Vec::new();
        
        for problem in problems {
            let solution = self.solve(problem).await?;
            solutions.push(solution);
        }
        
        Ok(solutions)
    }
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    println!("🌟 S-Entropy Framework Optimization Demo");
    println!("==========================================");
    
    let optimizer = SEntropyOptimizer::new();

    // Create sample optimization problems
    let problems = vec![
        OptimizationProblem::ResourceAllocation {
            resources: vec![100.0, 150.0, 80.0],
            demands: vec![120.0, 90.0, 110.0],
            constraints: vec![10.0, 20.0, 15.0],
        },
        
        OptimizationProblem::Portfolio {
            assets: vec!["TECH".to_string(), "REAL_ESTATE".to_string(), "BONDS".to_string()],
            returns: vec![0.12, 0.08, 0.04],
            risks: vec![0.20, 0.15, 0.05],
            target_return: 0.10,
        },
        
        OptimizationProblem::Scheduling {
            tasks: vec!["Design".to_string(), "Development".to_string(), "Testing".to_string(), "Deployment".to_string()],
            durations: vec![5.0, 10.0, 3.0, 2.0],
            dependencies: vec![(0, 1), (1, 2), (2, 3)],
            deadline: 18.0,
        },
    ];

    let solutions = optimizer.benchmark_solutions(problems).await?;

    // Display results
    for (i, solution) in solutions.iter().enumerate() {
        println!("\n📊 Problem {} Results:", i + 1);
        println!("Strategy used: {:?}", solution.strategy_used);
        println!("Solution quality: {:.4}", solution.solution_quality);
        println!("Computation time: {:.6}s", solution.computation_time);
        println!("Original S-entropy: {}", solution.s_entropy_coordinate);
        println!("Aligned S-entropy: {}", solution.aligned_coordinate);
        
        println!("\n💡 Recommendations:");
        for rec in &solution.recommendations {
            println!("  • {}", rec);
        }
        
        // Check if ridiculous methods were needed
        if matches!(solution.strategy_used, AlignmentStrategy::Ridiculous) {
            println!("⚠️  This problem required ridiculous solution methods!");
        } else if matches!(solution.strategy_used, AlignmentStrategy::ZeroComputation) {
            println!("✨ Solved using zero-computation navigation!");
        }
    }

    println!("\n🎯 S-Entropy Framework successfully solved {} optimization problems!", solutions.len());
    println!("   Average solution quality: {:.4}", 
             solutions.iter().map(|s| s.solution_quality).sum::<f64>() / solutions.len() as f64);

    Ok(())
} 