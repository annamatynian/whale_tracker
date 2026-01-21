"""Remove OLD AccumulationMetric definition (keep only NEW one)"""

filepath = r'C:\Users\annam\Documents\DeFi-RAG-Project\whale_tracker\models\database.py'

with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find BOTH class definitions
classes = []
for i, line in enumerate(lines):
    if 'class AccumulationMetric(Base):' in line:
        classes.append(i)

print(f"Found AccumulationMetric at lines: {[c+1 for c in classes]}")

if len(classes) != 2:
    print(f"ERROR: Expected 2 classes, found {len(classes)}")
    exit(1)

old_start = classes[0]  # Line 340 (0-indexed)
new_start = classes[1]  # Line 410 (0-indexed)

print(f"\nOLD class: line {old_start+1}")
print(f"NEW class: line {new_start+1}")

# Find end of OLD class (where NEW class starts - 1)
old_end = new_start - 1

# Remove empty lines before new class
while old_end > old_start and lines[old_end].strip() == '':
    old_end -= 1

print(f"Will DELETE lines {old_start+1} to {old_end+1} ({old_end - old_start + 1} lines)")

# Create new content WITHOUT old class
new_lines = lines[:old_start] + lines[new_start:]

# Write back
with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"\n✅ Removed OLD AccumulationMetric definition")
print(f"✅ Kept NEW AccumulationMetric at line {new_start+1 - (old_end - old_start + 1)}")
