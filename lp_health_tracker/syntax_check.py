#!/usr/bin/env python3
"""
Syntax check for our modified files
"""

import ast
import sys
from pathlib import Path

def check_syntax(file_path):
    """Check if a Python file has valid syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Try to parse the AST
        ast.parse(source, filename=str(file_path))
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error: {e}"

def main():
    """Check syntax of key files."""
    print("🔍 Checking syntax of modified files...")
    print("=" * 50)
    
    files_to_check = [
        'src/simple_multi_pool.py',
        'src/datetime_helpers.py', 
        'data/positions.json',
        'tests/conftest.py'
    ]
    
    all_good = True
    
    for file_path in files_to_check:
        path = Path(file_path)
        if not path.exists():
            print(f"❌ {file_path}: File not found")
            all_good = False
            continue
        
        if file_path.endswith('.json'):
            # Special handling for JSON files
            try:
                import json
                with open(path, 'r') as f:
                    json.load(f)
                print(f"✅ {file_path}: Valid JSON")
            except json.JSONDecodeError as e:
                print(f"❌ {file_path}: Invalid JSON - {e}")
                all_good = False
        else:
            # Python syntax check
            is_valid, error = check_syntax(path)
            if is_valid:
                print(f"✅ {file_path}: Valid Python syntax")
            else:
                print(f"❌ {file_path}: {error}")
                all_good = False
    
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 All files have valid syntax!")
    else:
        print("⚠️ Some files have syntax errors!")
    
    return all_good

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
