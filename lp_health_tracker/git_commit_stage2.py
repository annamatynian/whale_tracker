#!/usr/bin/env python3
import subprocess
import os
import sys

def run_git_command(cmd, description=""):
    """Run git command and return result."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            print(f"✅ {description}")
            if result.stdout.strip():
                print(result.stdout)
        else:
            print(f"❌ {description} failed:")
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running {' '.join(cmd)}: {e}")
        return False

def main():
    # Change to project directory
    os.chdir('C:\\Users\\annam\\Documents\\DeFi-RAG-Project\\lp_health_tracker')
    
    print("🔄 STAGE 2 INTEGRATION - GIT OPERATIONS")
    print("=" * 45)
    
    # Check current status
    print("\n📋 Current Git Status:")
    run_git_command(['git', 'status', '--short'], "Checking status")
    
    # Add new files
    print("\n➕ Adding new files to git...")
    files_to_add = [
        'tests/test_integration_stage2.py',
        'tests/conftest.py',
        'STAGE2_INTEGRATION_COMPLETED.md',
        'simple_stage2_check.py',
        'validate_stage2_integration.py'
    ]
    
    for file in files_to_add:
        if os.path.exists(file):
            success = run_git_command(['git', 'add', file], f"Adding {file}")
        else:
            print(f"⚠️ File not found: {file}")
    
    # Show staged files
    print("\n📦 Files staged for commit:")
    run_git_command(['git', 'status', '--cached', '--short'], "Showing staged files")
    
    # Create commit
    commit_message = """feat: Add Stage 2 Integration Test

- Create tests/test_integration_stage2.py based on test_stage2_final.py
- Add Stage 2 fixtures to conftest.py (stage2_position_data, live_data_provider)
- Implement comprehensive Stage 2 testing framework:
  * LiveDataProvider API integration tests
  * Real date parsing (replacing days_held_mock)
  * Error handling for API failures
  * Complete workflow validation
- Add validation scripts and documentation
- Ready for Stage 2 milestone completion

Integration validated by Gemini - no critical issues found.
"""
    
    print("\n💾 Creating commit...")
    success = run_git_command(['git', 'commit', '-m', commit_message], "Creating commit")
    
    if success:
        print("\n🎉 SUCCESS: Stage 2 integration committed!")
        print("✅ All changes saved to git")
        print("✅ Ready for next development phase")
        
        # Show commit info
        print("\n📊 Commit details:")
        run_git_command(['git', 'log', '--oneline', '-1'], "Last commit")
        
    else:
        print("\n❌ Commit failed - please check git status manually")

if __name__ == "__main__":
    main()
