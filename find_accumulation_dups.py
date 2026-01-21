"""Find all occurrences of AccumulationMetric in database.py"""
import re

filepath = r'C:\Users\annam\Documents\DeFi-RAG-Project\whale_tracker\models\database.py'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Find all class definitions
matches = list(re.finditer(r'class AccumulationMetric', content))

print(f"Found {len(matches)} occurrences of 'class AccumulationMetric':")
for i, match in enumerate(matches, 1):
    line_num = content[:match.start()].count('\n') + 1
    print(f"  {i}. Line {line_num}")

# Show context around each match
for i, match in enumerate(matches, 1):
    start = max(0, match.start() - 100)
    end = min(len(content), match.end() + 200)
    context = content[start:end]
    print(f"\n=== Occurrence {i} ===")
    print(context)
    print("=" * 50)
