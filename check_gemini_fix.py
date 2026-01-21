"""Quick syntax check for Gemini looping fix"""
import py_compile
import sys

filepath = r"C:\Users\annam\Documents\DeFi-RAG-Project\whale_tracker\src\analyzers\accumulation_score_calculator.py"

try:
    py_compile.compile(filepath, doraise=True)
    print("✅ SYNTAX OK - No Python errors!")
    sys.exit(0)
except py_compile.PyCompileError as e:
    print(f"❌ SYNTAX ERROR:\n{e}")
    sys.exit(1)
