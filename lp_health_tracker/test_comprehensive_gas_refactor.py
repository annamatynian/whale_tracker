#!/usr/bin/env python3
"""
Comprehensive Test Suite for GasCostCalculator Dependency Injection
================================================================

This test suite validates all changes made in the dependency injection refactoring:
1. Dependency injection implementation
2. Integration with main.py
3. Regression testing
4. Updated unit tests

Usage: python test_comprehensive_gas_refactor.py

Author: Generated for DeFi-RAG Project
"""

import subprocess
import sys
import os
import asyncio
from pathlib import Path


class GasRefactorTestSuite:
    """Comprehensive test suite for gas calculator refactoring."""
    
    def __init__(self):
        self.test_results = {}
        self.total_tests = 0
        self.passed_tests = 0
        
    def run_command(self, command, description, timeout=60):
        """Run a command and capture results."""
        print(f"\n🧪 {description}")
        print("=" * 60)
        
        try:
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                shell=True
            )
            
            success = result.returncode == 0
            self.test_results[description] = {
                'success': success,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
            
            # Print output
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
                
            self.total_tests += 1
            if success:
                self.passed_tests += 1
                print(f"✅ {description}: PASSED")
            else:
                print(f"❌ {description}: FAILED (exit code: {result.returncode})")
                
            return success
            
        except subprocess.TimeoutExpired:
            print(f"⏰ {description}: TIMEOUT")
            self.test_results[description] = {
                'success': False,
                'error': 'timeout'
            }
            self.total_tests += 1
            return False
            
        except Exception as e:
            print(f"💥 {description}: ERROR - {e}")
            self.test_results[description] = {
                'success': False,
                'error': str(e)
            }
            self.total_tests += 1
            return False

    async def run_all_tests(self):
        """Run the complete test suite."""
        print("🚀 STARTING COMPREHENSIVE GAS CALCULATOR TEST SUITE")
        print("=" * 80)
        print("Testing dependency injection refactoring changes...")
        
        # 1. NEW TESTS - Dependency Injection
        print("\n📍 PHASE 1: DEPENDENCY INJECTION VALIDATION")
        
        self.run_command(
            "python test_dependency_injection.py",
            "1. Dependency Injection Test"
        )
        
        # 2. INTEGRATION TESTS
        print("\n📍 PHASE 2: INTEGRATION VALIDATION")
        
        self.run_command(
            "python test_gas_integration.py",
            "2. Gas Calculator Integration Test"
        )
        
        # 3. UPDATED UNIT TESTS - Check if existing tests still work
        print("\n📍 PHASE 3: UNIT TEST VALIDATION")
        
        # Check if we need to update the existing unit test
        self.run_command(
            "pytest tests/unit/test_gas_cost_calculator.py -v",
            "3. Existing Unit Tests (may need updates)"
        )
        
        self.run_command(
            "pytest tests/unit/test_gas_quick.py -v",
            "4. Quick Gas Tests"
        )
        
        self.run_command(
            "pytest tests/unit/test_gas_simple.py -v",
            "5. Simple Gas Tests"
        )
        
        # 4. INTEGRATION TESTS
        print("\n📍 PHASE 4: INTEGRATION TESTS")
        
        self.run_command(
            "pytest tests/integration/test_integration_stage1.py -v",
            "6. Integration Stage 1"
        )
        
        self.run_command(
            "pytest tests/integration/test_integration_stage2.py -v",
            "7. Integration Stage 2"
        )
        
        # 5. CONFIGURATION VALIDATION
        print("\n📍 PHASE 5: CONFIGURATION VALIDATION")
        
        self.run_command(
            "pytest tests/integration/test_yaml_compatibility.py -v",
            "8. YAML Compatibility"
        )
        
        # 6. BASIC FUNCTIONALITY VERIFICATION
        print("\n📍 PHASE 6: BASIC FUNCTIONALITY VERIFICATION")
        
        self.run_command(
            "python simple_test.py",
            "9. Simple System Test"
        )
        
        self.run_command(
            "python quick_integration_check.py",
            "10. Quick Integration Check"
        )
        
        # 7. REGRESSION TESTING
        print("\n📍 PHASE 7: REGRESSION TESTING")
        
        self.run_command(
            "python regression_test.py",
            "11. Custom Regression Tests"
        )
        
        # 8. E2E TESTS (if they exist and are relevant)
        print("\n📍 PHASE 8: END-TO-END TESTING")
        
        if os.path.exists("tests/e2e/test_core_functionality.py"):
            self.run_command(
                "pytest tests/e2e/test_core_functionality.py -v",
                "12. E2E Core Functionality"
            )
        
        # 9. FINAL VALIDATION
        print("\n📍 PHASE 9: FINAL VALIDATION")
        
        self.run_command(
            "python final_verification.py",
            "13. Final System Verification"
        )
        
        # Generate final report
        self.generate_final_report()

    def generate_final_report(self):
        """Generate comprehensive test report."""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 80)
        
        print(f"\n📈 OVERALL RESULTS:")
        print(f"   Total Tests: {self.total_tests}")
        print(f"   Passed: {self.passed_tests}")
        print(f"   Failed: {self.total_tests - self.passed_tests}")
        print(f"   Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%" if self.total_tests > 0 else "N/A")
        
        print(f"\n📋 DETAILED RESULTS:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"   {status} - {test_name}")
            
            if not result['success'] and 'error' in result:
                print(f"      Error: {result['error']}")
            elif not result['success'] and 'returncode' in result:
                print(f"      Exit code: {result['returncode']}")
        
        # Critical assessment
        print(f"\n🎯 DEPENDENCY INJECTION ASSESSMENT:")
        
        critical_tests = [
            "1. Dependency Injection Test",
            "2. Gas Calculator Integration Test", 
            "11. Custom Regression Tests"
        ]
        
        critical_passed = sum(1 for test in critical_tests 
                            if test in self.test_results and self.test_results[test]['success'])
        
        if critical_passed == len(critical_tests):
            print("🎉 ✅ DEPENDENCY INJECTION REFACTORING: SUCCESS!")
            print("   All critical tests passed. Refactoring is stable.")
        else:
            print("⚠️  ❌ DEPENDENCY INJECTION REFACTORING: ISSUES DETECTED!")
            print("   Some critical tests failed. Review required.")
            
        print(f"\n💡 RECOMMENDATIONS:")
        
        failed_tests = [name for name, result in self.test_results.items() if not result['success']]
        
        if not failed_tests:
            print("   ✅ All tests passed! Dependency injection is successful.")
            print("   ✅ Code is ready for production use.")
        else:
            print("   🔧 Fix the following failing tests:")
            for test in failed_tests:
                print(f"      - {test}")
            
            if "3. Existing Unit Tests (may need updates)" in failed_tests:
                print("   📝 Note: Unit tests may need updates for new API signatures")
                
        print("\n" + "=" * 80)


async def main():
    """Main test execution."""
    suite = GasRefactorTestSuite()
    await suite.run_all_tests()


if __name__ == "__main__":
    print("🧪 COMPREHENSIVE GAS CALCULATOR REFACTORING TEST SUITE")
    print("Testing all dependency injection changes...\n")
    
    # Check if we're in the right directory
    if not os.path.exists("src/gas_cost_calculator.py"):
        print("❌ Error: Please run this from the lp_health_tracker root directory")
        sys.exit(1)
    
    asyncio.run(main())
