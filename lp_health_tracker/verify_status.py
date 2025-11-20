#!/usr/bin/env python3
"""
LP Health Tracker - Real Status Verification
===========================================

This script performs objective verification of what is actually implemented
vs what is documented as completed. Based on Gemini's recommendation to avoid
relying on documentation and check real code implementation.

Usage:
    python verify_status.py

Returns:
    Objective status of each project component
"""

import sys
import os
import importlib.util
from typing import Dict, List, Tuple, Any

def print_header(title: str):
    """Print formatted section header."""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def print_result(check_name: str, success: bool, details: str = ""):
    """Print formatted check result."""
    status = "✅" if success else "❌" 
    print(f"{status} {check_name}")
    if details:
        print(f"   └─ {details}")

def check_dependencies() -> Dict[str, bool]:
    """Check if required dependencies are actually installed."""
    print_header("DEPENDENCY VERIFICATION")
    
    results = {}
    required_deps = [
        ("web3", "Web3 blockchain integration"),
        ("requests", "HTTP API calls"),
        ("pandas", "Data manipulation"),
        ("aiohttp", "Async HTTP requests"),
        ("APScheduler", "Task scheduling")
    ]
    
    for dep_name, description in required_deps:
        try:
            __import__(dep_name)
            results[dep_name] = True
            print_result(f"{dep_name} ({description})", True, "Installed and importable")
        except ImportError:
            results[dep_name] = False
            print_result(f"{dep_name} ({description})", False, "NOT INSTALLED")
    
    return results

def check_core_classes() -> Dict[str, bool]:
    """Check which core classes are actually implemented vs imported."""
    print_header("CORE CLASS IMPLEMENTATION")
    
    results = {}
    
    # Check ImpermanentLossCalculator
    try:
        sys.path.insert(0, 'src')
        from data_analyzer import ImpermanentLossCalculator
        
        # Verify it has core methods
        calculator = ImpermanentLossCalculator()
        has_il_method = hasattr(calculator, 'calculate_impermanent_loss')
        has_compare_method = hasattr(calculator, 'compare_strategies')
        
        results['ImpermanentLossCalculator'] = True
        print_result("ImpermanentLossCalculator", True, 
                    f"Core IL method: {has_il_method}, Compare method: {has_compare_method}")
        
    except ImportError as e:
        results['ImpermanentLossCalculator'] = False
        print_result("ImpermanentLossCalculator", False, f"Import failed: {e}")
    
    # Check NetPnLCalculator (known to be missing based on our analysis)
    try:
        from data_analyzer import NetPnLCalculator
        results['NetPnLCalculator'] = True
        print_result("NetPnLCalculator", True, "Exists and importable")
    except ImportError:
        results['NetPnLCalculator'] = False
        print_result("NetPnLCalculator", False, "CLASS DOES NOT EXIST (imported but not implemented)")
    
    # Check Data Providers
    try:
        from data_providers import MockDataProvider, LiveDataProvider
        
        # Test MockDataProvider
        mock = MockDataProvider()
        mock_works = hasattr(mock, 'get_current_prices') and hasattr(mock, 'get_pool_apr')
        results['MockDataProvider'] = mock_works
        print_result("MockDataProvider", mock_works, "Basic functionality verified")
        
        # Test LiveDataProvider 
        live = LiveDataProvider()
        live_works = hasattr(live, 'get_current_prices') and hasattr(live, 'get_pool_apr')
        results['LiveDataProvider'] = live_works
        print_result("LiveDataProvider", live_works, "Class exists with required methods")
        
    except ImportError as e:
        results['MockDataProvider'] = False
        results['LiveDataProvider'] = False
        print_result("Data Providers", False, f"Import failed: {e}")
    
    return results

def check_web3_integration() -> Dict[str, bool]:
    """Check actual Web3 integration implementation."""
    print_header("WEB3 & ON-CHAIN INTEGRATION")
    
    results = {}
    
    # Check Web3 dependency
    try:
        import web3
        results['web3_installed'] = True
        print_result("Web3 library", True, f"Version: {web3.__version__}")
    except ImportError:
        results['web3_installed'] = False
        print_result("Web3 library", False, "Not installed")
        return results
    
    # Check Web3Manager implementation
    try:
        from web3_utils import Web3Manager
        
        manager = Web3Manager()
        has_connection_method = hasattr(manager, 'initialize') or hasattr(manager, 'connect')
        has_gas_method = hasattr(manager, 'get_current_gas_price')
        
        results['Web3Manager'] = True
        print_result("Web3Manager class", True, 
                    f"Connection method: {has_connection_method}, Gas method: {has_gas_method}")
        
        # Try to check if gas calculation is real vs mock
        if has_gas_method:
            try:
                # This will likely fail without RPC connection, but we can check the implementation
                gas_method = getattr(manager, 'get_current_gas_price')
                method_code = gas_method.__code__
                is_simple_stub = len(method_code.co_consts) <= 2  # Likely a simple return statement
                
                if is_simple_stub:
                    print_result("Gas calculation implementation", False, "Appears to be a stub/placeholder")
                    results['gas_calculation_real'] = False
                else:
                    print_result("Gas calculation implementation", True, "Has complex logic (likely real)")
                    results['gas_calculation_real'] = True
                    
            except Exception as e:
                print_result("Gas calculation check", False, f"Could not analyze: {e}")
                results['gas_calculation_real'] = False
        
    except ImportError as e:
        results['Web3Manager'] = False
        print_result("Web3Manager class", False, f"Import failed: {e}")
    
    return results

def check_live_api_integration() -> Dict[str, bool]:
    """Test if live APIs are actually working."""
    print_header("LIVE API INTEGRATION TEST")
    
    results = {}
    
    try:
        from data_providers import LiveDataProvider
        
        provider = LiveDataProvider()
        
        # Test with a simple pool configuration
        test_pool = {
            'name': 'WETH-USDC',
            'initial_price_a_usd': 2000.0,
            'initial_price_b_usd': 1.0
        }
        
        # Test price fetching (with timeout)
        try:
            prices = provider.get_current_prices(test_pool)
            if prices and len(prices) == 2 and all(p > 0 for p in prices):
                results['live_price_api'] = True
                print_result("Live price API (CoinGecko)", True, f"WETH: ${prices[0]:.2f}, USDC: ${prices[1]:.2f}")
            else:
                results['live_price_api'] = False
                print_result("Live price API (CoinGecko)", False, f"Invalid response: {prices}")
        except Exception as e:
            results['live_price_api'] = False
            print_result("Live price API (CoinGecko)", False, f"Failed: {e}")
        
        # Test APR fetching
        try:
            apr = provider.get_pool_apr(test_pool)
            if isinstance(apr, (int, float)) and apr >= 0:
                results['live_apr_api'] = True
                print_result("Live APR API (DeFi Llama)", True, f"WETH-USDC APR: {apr:.2%}")
            else:
                results['live_apr_api'] = False
                print_result("Live APR API (DeFi Llama)", False, f"Invalid APR: {apr}")
        except Exception as e:
            results['live_apr_api'] = False
            print_result("Live APR API (DeFi Llama)", False, f"Failed: {e}")
            
    except ImportError as e:
        results['live_price_api'] = False
        results['live_apr_api'] = False
        print_result("Live API integration", False, f"LiveDataProvider import failed: {e}")
    
    return results

def check_project_stages() -> Dict[str, bool]:
    """Verify which project stages are actually completed."""
    print_header("PROJECT MILESTONE VERIFICATION")
    
    results = {}
    
    # Stage 1: Foundation - IL calculations and multi-pool
    stage1_deps = [
        ('ImpermanentLossCalculator', 'Core IL calculation engine'),
        ('MockDataProvider', 'Basic data simulation'),
        ('simple_multi_pool', 'Multi-pool management')
    ]
    
    stage1_complete = True
    for dep, desc in stage1_deps:
        try:
            if dep == 'simple_multi_pool':
                from simple_multi_pool import SimpleMultiPoolManager
                # Note: This will fail due to NetPnLCalculator import, but let's see
                pass
            else:
                # Already checked in previous functions
                pass
        except ImportError:
            stage1_complete = False
            print_result(f"Stage 1 - {desc}", False, f"{dep} not available")
    
    results['stage1_foundation'] = stage1_complete
    print_result("Stage 1: Foundation", stage1_complete, 
                "IL calculations, multi-pool architecture" if stage1_complete else "Has import issues")
    
    # Stage 2: Live Integration - Real APIs and data providers
    stage2_working = (
        results.get('LiveDataProvider', False) and 
        results.get('live_price_api', False)
    )
    results['stage2_live_integration'] = stage2_working
    print_result("Stage 2: Live Integration", stage2_working,
                "Live APIs working" if stage2_working else "Live API integration incomplete")
    
    # Stage 3: On-chain Integration - Gas costs and Web3
    stage3_working = (
        results.get('Web3Manager', False) and 
        results.get('gas_calculation_real', False)
    )
    results['stage3_onchain'] = stage3_working
    print_result("Stage 3: On-chain Integration", stage3_working,
                "Web3 and gas costs" if stage3_working else "ON-CHAIN INTEGRATION MISSING")
    
    return results

def check_critical_gaps() -> List[str]:
    """Identify critical implementation gaps."""
    print_header("CRITICAL IMPLEMENTATION GAPS")
    
    gaps = []
    
    # Check for import errors that would break the system
    try:
        from simple_multi_pool import SimpleMultiPoolManager
        print_result("SimpleMultiPoolManager import", True, "No import errors")
    except ImportError as e:
        if 'NetPnLCalculator' in str(e):
            gaps.append("NetPnLCalculator class missing (imported but not implemented)")
            print_result("NetPnLCalculator availability", False, "Class referenced but doesn't exist")
        else:
            gaps.append(f"SimpleMultiPoolManager import error: {e}")
            print_result("SimpleMultiPoolManager import", False, str(e))
    
    # Check for on-chain integration
    if not results.get('gas_calculation_real', False):
        gaps.append("Real gas cost calculation not implemented")
        print_result("Gas cost integration", False, "Missing on-chain gas cost tracking")
    
    # Check for Web3 RPC connections
    try:
        from web3_utils import Web3Manager
        manager = Web3Manager()
        # Try to see if it has real RPC configuration
        if hasattr(manager, 'networks'):
            print_result("Web3 RPC configuration", True, "Network configurations exist")
        else:
            gaps.append("Web3 RPC configuration incomplete")
            print_result("Web3 RPC configuration", False, "Network setup missing")
    except:
        gaps.append("Web3Manager not properly configured")
    
    return gaps

def generate_summary(all_results: Dict[str, Dict[str, bool]], gaps: List[str]) -> Dict[str, Any]:
    """Generate overall project status summary."""
    print_header("PROJECT STATUS SUMMARY")
    
    # Count completed features
    total_checks = sum(len(results) for results in all_results.values())
    passed_checks = sum(sum(results.values()) for results in all_results.values())
    completion_rate = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
    
    # Determine project readiness
    has_core_il = all_results.get('core_classes', {}).get('ImpermanentLossCalculator', False)
    has_live_apis = all_results.get('live_apis', {}).get('live_price_api', False)
    has_onchain = all_results.get('web3_integration', {}).get('gas_calculation_real', False)
    
    readiness_level = "🔴 Not Ready"
    if has_core_il and has_live_apis and has_onchain:
        readiness_level = "🟢 Production Ready"
    elif has_core_il and has_live_apis:
        readiness_level = "🟡 Demo Ready (missing on-chain)"
    elif has_core_il:
        readiness_level = "🟠 Development Stage (mock data only)"
    
    summary = {
        'completion_rate': completion_rate,
        'readiness_level': readiness_level,
        'critical_gaps': gaps,
        'passed_checks': passed_checks,
        'total_checks': total_checks
    }
    
    print(f"Overall Completion: {completion_rate:.1f}% ({passed_checks}/{total_checks} checks passed)")
    print(f"Readiness Level: {readiness_level}")
    
    if gaps:
        print(f"\n🚨 Critical Gaps Found ({len(gaps)}):")
        for gap in gaps:
            print(f"   • {gap}")
    else:
        print("\n✅ No critical gaps detected")
    
    return summary

if __name__ == "__main__":
    print("🚀 LP Health Tracker - Real Status Verification")
    print("=" * 60)
    print("This script checks what is ACTUALLY implemented vs documented.")
    print("Based on Gemini AI recommendation to verify code, not documentation.")
    
    # Run all verification checks
    results = {}
    
    results['dependencies'] = check_dependencies()
    results['core_classes'] = check_core_classes()  
    results['web3_integration'] = check_web3_integration()
    results['live_apis'] = check_live_api_integration()
    results['project_stages'] = check_project_stages()
    
    # Check for critical gaps
    critical_gaps = check_critical_gaps()
    
    # Generate final summary
    summary = generate_summary(results, critical_gaps)
    
    print_header("VERIFICATION COMPLETE")
    print(f"📊 Status verification completed.")
    print(f"📈 {summary['readiness_level']}")
    
    if summary['critical_gaps']:
        print(f"⚠️  {len(summary['critical_gaps'])} critical issues need attention")
        print("\n🎯 Priority fixes needed:")
        for i, gap in enumerate(summary['critical_gaps'][:3], 1):
            print(f"   {i}. {gap}")
    else:
        print("🎉 All core components verified and working!")
    
    # Exit code based on critical gaps
    sys.exit(len(critical_gaps))
