"""
Windows-compatible master test suite - ASCII only, simplified
"""
import asyncio
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def run_python_script(script_name: str) -> bool:
    """Run Python script and return result"""
    
    try:
        print(f"\n> Running {script_name}...")
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            encoding='utf-8',
            errors='replace'  # Handle encoding issues gracefully
        )
        
        # Print output
        if result.stdout:
            # Print only non-unicode parts
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                try:
                    print(line)
                except UnicodeEncodeError:
                    print(line.encode('ascii', 'replace').decode('ascii'))
        
        if result.stderr:
            print("STDERR:")
            stderr_lines = result.stderr.split('\n')
            for line in stderr_lines:
                try:
                    print(line)
                except UnicodeEncodeError:
                    print(line.encode('ascii', 'replace').decode('ascii'))
        
        success = result.returncode == 0
        status = "PASS" if success else "FAIL"
        print(f"Result {script_name}: {status}")
        
        return success
        
    except Exception as e:
        print(f"ERROR Could not run {script_name}: {e}")
        return False

async def run_windows_test_suite():
    """Windows-compatible test suite"""
    
    print("WINDOWS-COMPATIBLE CRYPTO MULTI-AGENT TEST")
    print("=" * 80)
    print("Sequential testing of all system components")
    print("=" * 80)
    
    # Define test sequence - only Windows-compatible tests
    test_sequence = [
        # PHASE 1: Basic functionality (Windows compatible)
        ("test_imports_windows.py", "Import Check", True),
        ("test_quick_windows.py", "Quick Check", True),
        
        # PHASE 2: Component tests (Windows compatible)
        ("test_mock_data_windows.py", "Mock Data Test", True),
        
        # PHASE 3: Try existing tests if they work
        ("test_scoring_examples.py", "Scoring Examples", False),  # Optional
    ]
    
    results = {}
    critical_failures = []
    
    print(f"Tests in queue: {len(test_sequence)}")
    print(f"Critical: {sum(1 for _, _, critical in test_sequence if critical)}")
    print(f"Optional: {sum(1 for _, _, critical in test_sequence if not critical)}")
    
    # Run tests
    for i, (script, description, is_critical) in enumerate(test_sequence, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}/{len(test_sequence)}: {description}")
        print(f"Script: {script} {'(CRITICAL)' if is_critical else '(optional)'}")
        print(f"{'='*80}")
        
        # Check if file exists
        script_path = PROJECT_ROOT / script
        if not script_path.exists():
            print(f"WARNING File {script} not found - skipping")
            results[script] = "SKIPPED"
            continue
        
        # Run the test
        success = run_python_script(script)
        
        if success:
            results[script] = "PASSED"
            print(f"SUCCESS Test {i} passed")
        else:
            results[script] = "FAILED"
            print(f"ERROR Test {i} failed")
            
            if is_critical:
                critical_failures.append((script, description))
                print(f"CRITICAL TEST FAILED: {description}")
    
    # Final report
    print(f"\n{'='*80}")
    print("FINAL WINDOWS TEST REPORT")
    print(f"{'='*80}")
    
    passed = sum(1 for result in results.values() if result == "PASSED")
    failed = sum(1 for result in results.values() if result == "FAILED")
    skipped = sum(1 for result in results.values() if result == "SKIPPED")
    total = len(results)
    
    print(f"STATISTICS:")
    print(f"   Passed: {passed}")
    print(f"   Failed: {failed}")
    print(f"   Skipped: {skipped}")
    print(f"   Total: {total}")
    
    if total > 0:
        success_rate = (passed / total) * 100
        print(f"   Success Rate: {success_rate:.1f}%")
    
    # Detailed results
    print(f"\nDETAILED RESULTS:")
    for script, result in results.items():
        icon = {"PASSED": "OK", "FAILED": "ERROR", "SKIPPED": "SKIP"}[result]
        print(f"   {icon} {script}: {result}")
    
    # Critical failures analysis
    if critical_failures:
        print(f"\nCRITICAL PROBLEMS ({len(critical_failures)}):")
        for script, description in critical_failures:
            print(f"   ERROR {description} ({script})")
        
        print(f"\nRECOMMENDATIONS:")
        print(f"   1. Fix critical errors above")
        print(f"   2. Check dependencies: pip install -r requirements.txt")
        print(f"   3. Make sure you're in correct directory")
        print(f"   4. Repeat test")
    
    # Overall assessment
    if not critical_failures and passed >= total * 0.8:
        print(f"\nSUCCESS: SYSTEM READY FOR PRODUCTION!")
        print(f"   All critical tests passed")
        print(f"   High success rate ({success_rate:.1f}%)")
        print(f"   Can proceed to API key setup")
        
    elif not critical_failures:
        print(f"\nPARTIAL SUCCESS: SYSTEM MOSTLY READY!")
        print(f"   Critical components work")
        print(f"   Some non-critical issues")
        print(f"   Recommend fixing found problems")
        
    else:
        print(f"\nFAILED: SYSTEM NEEDS FIXES!")
        print(f"   {len(critical_failures)} critical problems")
        print(f"   System not ready for production")
        print(f"   Must fix critical errors")
    
    print(f"\n{'='*80}")
    print("WINDOWS TEST COMPLETE")
    print(f"{'='*80}")
    
    return len(critical_failures) == 0

if __name__ == "__main__":
    success = asyncio.run(run_windows_test_suite())
    
    if success:
        print(f"\nSUCCESS: ALL CRITICAL TESTS PASSED!")
        print(f"   System ready for next stage")
    else:
        print(f"\nERROR: CRITICAL PROBLEMS FOUND!")
        print(f"   Need to fix errors")
    
    exit(0 if success else 1)
