#!/usr/bin/env python3
"""
Git commit script for Phase 1.1 - Add gas cost fields to position structure
"""

import subprocess
import sys

def run_git_command(command):
    """Run git command and return result."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Error: {result.stderr}")
            return False
        print(f"✅ {result.stdout.strip()}")
        return True
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    print("🚀 Phase 1.1: Committing gas cost structure changes...")
    
    # Add changed files
    commands = [
        "git add data/positions.json.example",
        "git add data/positions.json", 
        'git commit -m "Phase 1.1: Add entry_tx_hash and gas_costs_calculated fields to position structure

- Added entry_tx_hash field to track entry transaction for real gas cost calculation
- Added gas_costs_calculated flag to enable caching and avoid redundant RPC calls  
- Kept gas_costs_usd as fallback for reliability
- Updated both positions.json.example and positions.json
- Preparation for Web3Manager integration in Phase 1.2"'
    ]
    
    for cmd in commands:
        print(f"Running: {cmd}")
        if not run_git_command(cmd):
            sys.exit(1)
    
    print("\n✅ Phase 1.1 Complete!")
    print("📋 Next step: Phase 1.2 - Create GasCostCalculator module")

if __name__ == "__main__":
    main()
