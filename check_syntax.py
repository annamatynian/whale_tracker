"""
Syntax check for accumulation_score_calculator.py after precision vulnerability fix.
"""

import sys
import py_compile

file_path = r"C:\Users\annam\Documents\DeFi-RAG-Project\whale_tracker\src\analyzers\accumulation_score_calculator.py"

print(f"Checking syntax of {file_path}...")

try:
    py_compile.compile(file_path, doraise=True)
    print("✅ Syntax check PASSED - no errors")
    sys.exit(0)
except py_compile.PyCompileError as e:
    print(f"❌ Syntax error found:\n{e}")
    sys.exit(1)
