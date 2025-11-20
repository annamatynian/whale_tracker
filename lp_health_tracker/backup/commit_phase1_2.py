#!/usr/bin/env python3
"""
Git commit script for Phase 1.2 - Create GasCostCalculator module
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
    print("🚀 Phase 1.2: Committing GasCostCalculator module...")
    
    # Add new file
    commands = [
        "git add src/gas_cost_calculator.py",
        'git commit -m "Phase 1.2: Create GasCostCalculator module with real blockchain integration

✅ Core Features:
- Real gas cost calculation from transaction receipts  
- USD conversion with ETH price integration
- Smart caching to avoid redundant RPC calls
- Fallback to manual gas_costs_usd values for reliability

✅ Key Methods:
- calculate_tx_cost_usd(): Real blockchain transaction cost calculation
- update_position_gas_costs(): Individual position gas cost updates  
- update_all_positions_gas_costs(): Batch processing for efficiency
- get_gas_cost_summary(): Analytics and reporting

✅ Architecture:
- Integrates with existing Web3Manager
- Prepared for integration with SimpleMultiPoolManager
- Professional error handling and logging
- GasEstimator utility class for operation cost estimates

📋 Next: Phase 1.3 - Integration with SimpleMultiPoolManager"'
    ]
    
    for cmd in commands:
        print(f"Running: {cmd}")
        if not run_git_command(cmd):
            sys.exit(1)
    
    print("\n✅ Phase 1.2 Complete!")
    print("📋 Next step: Phase 1.3 - Integrate with SimpleMultiPoolManager")

if __name__ == "__main__":
    main()
