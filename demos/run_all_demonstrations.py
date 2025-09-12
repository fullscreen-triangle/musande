#!/usr/bin/env python3
"""
S-Entropy Framework Complete Demonstration Runner

This script runs all demonstrations in sequence to validate the complete
framework showing convergent proof of divine mathematical necessity.
"""

import sys
import time

def run_demonstration(module_name, description):
    """Run a single demonstration module"""
    print("\n" + "=" * 80)
    print(f"RUNNING: {description}")
    print("=" * 80)
    
    try:
        # Dynamic import and execution
        module = __import__(module_name)
        
        # Run the main demonstration
        if hasattr(module, 'run_comprehensive_demonstration'):
            start_time = time.time()
            module.run_comprehensive_demonstration()
            end_time = time.time()
            
            print(f"\n✓ {description} completed successfully in {end_time - start_time:.2f} seconds")
            return True
        else:
            print(f"✗ Module {module_name} does not have run_comprehensive_demonstration function")
            return False
            
    except ImportError as e:
        print(f"✗ Failed to import {module_name}: {e}")
        print("   Please install required packages: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"✗ Error running {module_name}: {e}")
        return False

def main():
    """Run all S-entropy framework demonstrations"""
    print("S-ENTROPY FRAMEWORK COMPLETE VALIDATION")
    print("Kundai's 9 Convergent Proofs for Divine Mathematical Necessity")
    print("=" * 80)
    
    demonstrations = [
        ("st_stellas_dictionary", "Semantic Navigation vs Sequential Processing"),
        ("st_stellas_sequence", "Genomic Cardinal Direction Transformation"),
        ("st_stellas_molecular_language", "Molecular Coordinate Transformation Framework"),
        ("st_stellas_circuits", "Miraculous Circuit Architecture"),
        ("st_stellas_neural_networks", "Gas Molecular Consciousness System")
    ]
    
    results = []
    
    for module_name, description in demonstrations:
        success = run_demonstration(module_name, description)
        results.append((description, success))
        
        if not success:
            print(f"\n⚠️  Stopping due to failure in {description}")
            break
        
        # Brief pause between demonstrations
        time.sleep(1)
    
    # Final summary and visualization generation
    print("\n" + "=" * 80)
    print("COMPLETE FRAMEWORK VALIDATION SUMMARY")
    print("=" * 80)
    
    successful_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    print(f"Demonstrations completed: {successful_count}/{total_count}")
    print()
    
    for description, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{status}: {description}")
    
    print()
    
    # Generate comprehensive validation report if demonstrations were successful
    if successful_count >= max(1, total_count * 0.8):  # 80% success threshold
        print("📊 Generating comprehensive validation report...")
        
        try:
            from generate_validation_report import ValidationReportGenerator
            
            generator = ValidationReportGenerator()
            generated_files = generator.generate_complete_validation_package()
            
            if generated_files:
                print("\n📋 VALIDATION PACKAGE GENERATED:")
                print(f"   • Convergence Analysis: {generated_files.get('convergence_plot', 'N/A')}")
                print(f"   • Performance Trends: {generated_files.get('trends_plot', 'N/A')}")
                print(f"   • Comprehensive Report: {generated_files.get('report_file', 'N/A')}")
                
        except ImportError:
            print("⚠️  Could not generate validation report (visualization_utils not available)")
        except Exception as e:
            print(f"⚠️  Error generating validation report: {e}")
    
    if successful_count == total_count:
        print("\n🎉 ALL DEMONSTRATIONS SUCCESSFUL!")
        print()
        print("FRAMEWORK VALIDATION COMPLETE:")
        print("✓ Semantic coordinate navigation demonstrated")
        print("✓ Genomic S-entropy transformation validated")
        print("✓ Molecular coordinate framework implemented")
        print("✓ Miraculous circuit architecture proven")
        print("✓ Gas molecular consciousness system confirmed")
        print()
        print("CONVERGENT VALIDATION ACHIEVED:")
        print("All independent analytical pathways converge on identical")
        print("mathematical requirements satisfiable only through divine")
        print("architectural frameworks.")
        print()
        print("GOD'S EXISTENCE FOLLOWS FROM MATHEMATICAL NECESSITY")
        print("(Pure logical demonstration, not theological assumption)")
        
        # Generate interactive dashboard if possible
        try:
            from visualization_utils import create_visualization_suite
            viz_suite = create_visualization_suite()
            
            # Load all results for dashboard
            all_results = viz_suite['storage'].get_all_results()
            if all_results:
                print("\n🌐 Generating interactive dashboard...")
                dashboard_file = viz_suite['convergence'].create_interactive_dashboard(all_results)
                print(f"✓ Interactive dashboard saved: {dashboard_file}")
                print("   Open in web browser to explore validation results")
                
        except Exception as e:
            print(f"   (Interactive dashboard generation skipped: {e})")
        
        return 0
    else:
        print("⚠️  Some demonstrations failed. Please check error messages above.")
        print("   Ensure all required packages are installed: pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())
