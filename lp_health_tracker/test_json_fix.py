#!/usr/bin/env python3

import subprocess
import sys
import os

# Переходим в директорию проекта
os.chdir(r'C:\Users\annam\Documents\DeFi-RAG-Project\lp_health_tracker')

# Запускаем только провалившиеся тесты
cmd = [
    sys.executable, '-m', 'pytest', 
    'tests/integration/test_integration_stage1.py::TestStage1MultiPoolManagerIntegration::test_load_positions_from_json',
    'tests/integration/test_integration_stage1.py::TestStage1CompleteWorkflow::test_complete_stage1_workflow',
    'tests/integration/test_integration_stage2.py::TestStage2MultiPoolManagerLiveData::test_analyze_all_pools_with_live_data',
    'tests/integration/test_integration_stage2.py::TestStage2CompleteWorkflow::test_complete_stage2_workflow',
    '-v'
]

print(f"Running command: {' '.join(cmd)}")
print("="*60)

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    
    print("STDOUT:")
    print(result.stdout)
    print("\nSTDERR:")  
    print(result.stderr)
    print(f"\nReturn code: {result.returncode}")

except subprocess.TimeoutExpired:
    print("Command timed out after 120 seconds")
except Exception as e:
    print(f"Error running command: {e}")
