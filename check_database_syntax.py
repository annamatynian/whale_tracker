"""Syntax check for database.py"""
import py_compile
import sys

try:
    py_compile.compile(
        r'C:\Users\annam\Documents\DeFi-RAG-Project\whale_tracker\models\database.py',
        doraise=True
    )
    print("✅ Syntax check PASSED - database.py is valid")
    sys.exit(0)
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")
    sys.exit(1)
