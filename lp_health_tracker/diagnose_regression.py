#!/usr/bin/env python3
"""
Diagnostic Test for Regression Issues
====================================

Check what's causing the regression test to fail.

Author: Generated for DeFi-RAG Project
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def diagnose_imports():
    """Diagnose import issues."""
    print("DIAGNOSING IMPORT ISSUES")
    print("=" * 40)
    
    modules_to_test = [
        'src.position_models',
        'src.position_manager', 
        'src.gas_cost_calculator',
        'src.main',
        'src.web3_utils'
    ]
    
    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"[PASS] {module_name}")
        except Exception as e:
            print(f"[FAIL] {module_name}: {e}")
            print(f"       Error type: {type(e)}")
    
    print()

def diagnose_position_models():
    """Diagnose position model issues."""
    print("DIAGNOSING POSITION MODELS")
    print("=" * 40)
    
    try:
        from src.position_models import LPPosition, TokenInfo
        print("[PASS] Basic imports work")
        
        # Test TokenInfo with valid Ethereum address
        token = TokenInfo(symbol="TEST", address="0x1234567890123456789012345678901234567890")
        print(f"[PASS] TokenInfo creation: {token.symbol}")
        
        # Test if create_example_position_model exists
        try:
            from src.position_models import create_example_position_model
            example = create_example_position_model()
            print(f"[PASS] create_example_position_model: {example.name}")
        except ImportError as e:
            print(f"[FAIL] create_example_position_model import: {e}")
        except Exception as e:
            print(f"[FAIL] create_example_position_model creation: {e}")
        
    except Exception as e:
        print(f"[FAIL] Position models error: {e}")
        import traceback
        traceback.print_exc()
    
    print()

def diagnose_position_manager():
    """Diagnose position manager issues."""
    print("DIAGNOSING POSITION MANAGER")
    print("=" * 40)
    
    try:
        from src.position_manager import PositionManager, create_example_position
        print("[PASS] Basic imports work")
        
        # Test PositionManager creation
        pm = PositionManager()
        print("[PASS] PositionManager creation")
        
        # Test example creation
        example = create_example_position()
        print(f"[PASS] create_example_position: {example.name}")
        
    except Exception as e:
        print(f"[FAIL] Position manager error: {e}")
        import traceback
        traceback.print_exc()
    
    print()

def check_file_structure():
    """Check file structure."""
    print("CHECKING FILE STRUCTURE")
    print("=" * 40)
    
    files_to_check = [
        "src/position_models.py",
        "src/position_manager.py", 
        "src/gas_cost_calculator.py",
        "src/main.py",
        "data/positions.json"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"[PASS] {file_path} exists")
        else:
            print(f"[FAIL] {file_path} missing")
    
    print()

if __name__ == "__main__":
    print("REGRESSION TEST DIAGNOSTICS")
    print("=" * 50)
    print()
    
    diagnose_imports()
    diagnose_position_models()
    diagnose_position_manager()
    check_file_structure()
    
    print("DIAGNOSIS COMPLETE")
    print("=" * 50)
