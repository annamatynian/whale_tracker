"""Show and remove old AccumulationMetric definition"""

filepath = r'C:\Users\annam\Documents\DeFi-RAG-Project\whale_tracker\models\database.py'

with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find OLD definition (around line 341)
print("=== LINES 330-410 (showing old definition area) ===")
for i in range(330, min(410, len(lines))):
    print(f"{i+1:4d}: {lines[i]}", end='')

print("\n" + "="*60)
print("Looking for class definition boundaries...")

# Find start and end of OLD class
old_class_start = None
old_class_end = None

for i, line in enumerate(lines):
    if i >= 340 and i <= 350 and 'class AccumulationMetric(Base):' in line:
        old_class_start = i
        print(f"OLD class starts at line {i+1}")
        break

# Find where old class ends (next class definition or end of indentation)
if old_class_start is not None:
    indent_level = len(lines[old_class_start]) - len(lines[old_class_start].lstrip())
    
    for i in range(old_class_start + 1, len(lines)):
        line = lines[i]
        
        # Check if we hit another class definition
        if line.strip().startswith('class ') and not line.strip().startswith('#'):
            old_class_end = i - 1
            print(f"OLD class ends at line {i} (next class found)")
            break
        
        # Check if line is not indented (end of class)
        if line.strip() and not line.startswith(' ' * (indent_level + 1)) and not line.strip().startswith('#'):
            if 'class' not in line:  # Skip if it's another class
                continue
            old_class_end = i - 1
            print(f"OLD class ends at line {i} (dedent found)")
            break

if old_class_start and old_class_end:
    print(f"\nOLD AccumulationMetric: lines {old_class_start+1} to {old_class_end+1}")
    print(f"Will delete {old_class_end - old_class_start + 1} lines")
    
    print("\n=== OLD CLASS PREVIEW ===")
    for i in range(old_class_start, min(old_class_start + 20, old_class_end + 1)):
        print(f"{i+1:4d}: {lines[i]}", end='')
    print("...")
else:
    print("Could not determine class boundaries")
