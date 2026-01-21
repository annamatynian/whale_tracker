"""Quick syntax check for accumulation_score_calculator.py"""
import py_compile
import sys

try:
    py_compile.compile(
        r'C:\Users\annam\Documents\DeFi-RAG-Project\whale_tracker\src\analyzers\accumulation_score_calculator.py',
        doraise=True
    )
    print("✅ Syntax check PASSED - accumulation_score_calculator.py is valid")
    sys.exit(0)
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")
    sys.exit(1)
