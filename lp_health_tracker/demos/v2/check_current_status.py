#!/usr/bin/env python3
"""
Quick check of current test status after fixes
"""
import subprocess
import sys
import os

def run_tests():
    """Run pytest and show summary"""
    try:
        # Change to project directory
        os.chdir(r"C:\Users\annam\Documents\DeFi-RAG-Project\lp_health_tracker")
        
        print("🧪 Running pytest to check current status...")
        print("=" * 50)
        
        # Run pytest with summary
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", 
            "--tb=short",
            "--disable-warnings",
            "-q"  # Quiet mode for cleaner output
        ], capture_output=True, text=True, timeout=120)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)
        
        print(f"\nReturn code: {result.returncode}")
        
        # Count results
        output = result.stdout
        if "failed" in output and "passed" in output:
            print("\n📊 SUMMARY ANALYSIS:")
            lines = output.split('\n')
            for line in lines:
                if "failed" in line or "passed" in line or "error" in line:
                    print(f"   {line}")
        
    except subprocess.TimeoutExpired:
        print("❌ Tests timed out after 2 minutes")
    except Exception as e:
        print(f"❌ Error running tests: {e}")

if __name__ == "__main__":
    print("🎯 LP Health Tracker - Current Test Status Check")
    print("=" * 50)
    run_tests()
