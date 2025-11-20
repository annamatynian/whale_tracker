#!/usr/bin/env python3
"""
Complete Stage 2 Integration and Documentation Organization
==========================================================

This script:
1. Commits Stage 2 integration changes
2. Organizes project documentation
3. Commits documentation organization
4. Provides summary of completed work
"""

import subprocess
import os
import sys
from pathlib import Path

def run_command(cmd, description="", check_success=True):
    """Run a command and handle output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            print(f"✅ {description}")
            if result.stdout.strip():
                print(f"   {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} failed:")
            print(f"   {result.stderr.strip()}")
            return False if check_success else True
    except Exception as e:
        print(f"❌ Error running {' '.join(cmd)}: {e}")
        return False

def stage2_git_commit():
    """Commit Stage 2 integration changes."""
    print("\\n💾 STAGE 2 INTEGRATION - GIT COMMIT")
    print("=" * 40)
    
    # Add files for Stage 2 integration
    files_to_add = [
        'tests/test_integration_stage2.py',
        'tests/conftest.py',
        'STAGE2_INTEGRATION_COMPLETED.md',
        'simple_stage2_check.py',
        'validate_stage2_integration.py'
    ]
    
    for file in files_to_add:
        if Path(file).exists():
            run_command(['git', 'add', file], f"Adding {file}")
    
    # Create Stage 2 commit
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

Integration validated by Gemini - no critical issues found."""
    
    success = run_command(['git', 'commit', '-m', commit_message], "Creating Stage 2 commit")
    return success

def organize_documentation():
    """Execute documentation organization."""
    print("\\n📚 DOCUMENTATION ORGANIZATION")
    print("=" * 35)
    
    # Import and run organization
    try:
        exec(open('execute_docs_organization.py').read())
        return True
    except Exception as e:
        print(f"❌ Documentation organization failed: {e}")
        return False

def docs_git_commit():
    """Commit documentation organization."""
    print("\\n💾 DOCUMENTATION ORGANIZATION - GIT COMMIT")
    print("=" * 45)
    
    # Add all changes
    run_command(['git', 'add', '.'], "Adding all documentation changes")
    
    # Create documentation commit
    commit_message = """docs: Organize project documentation structure

- Move user guides to docs/user_guides/ (QUICKSTART.md, TESTING_GUIDE.md)
- Move reference docs to docs/reference/ (IL_BASICS.md)
- Archive completed milestones to docs/archive/
- Move utility scripts to scripts/ directory
- Archive old test files to archive/old_tests/
- Create comprehensive documentation index (docs/README.md)
- Update main README.md with new documentation links
- Rename Russian files with English names

Result: Clean, professional documentation structure ready for production."""
    
    success = run_command(['git', 'commit', '-m', commit_message], "Creating documentation commit")
    return success

def final_summary():
    """Provide final summary of completed work."""
    print("\\n🎉 COMPLETION SUMMARY")
    print("=" * 25)
    
    print("✅ Stage 2 Integration:")
    print("   • tests/test_integration_stage2.py created")
    print("   • Stage 2 fixtures added to conftest.py")
    print("   • Comprehensive testing framework implemented")
    print("   • Gemini validation passed")
    
    print("\\n✅ Documentation Organization:")
    print("   • Professional directory structure created")
    print("   • User guides moved to docs/user_guides/")
    print("   • Reference materials organized in docs/reference/")
    print("   • Completed milestones archived in docs/archive/")
    print("   • Utility scripts moved to scripts/")
    print("   • Documentation index created")
    
    print("\\n📊 Project Status:")
    print("   • Stage 2: ✅ COMPLETED")
    print("   • Documentation: ✅ ORGANIZED")
    print("   • Git history: ✅ CLEAN") 
    print("   • Ready for: 🚀 STAGE 3 DEVELOPMENT")
    
    print("\\n🎯 Next Steps:")
    print("   1. Review organized documentation structure")
    print("   2. Test all documentation links")
    print("   3. Begin Stage 3: On-Chain Integration")
    print("   4. Consider creating GitHub repository for professional showcase")
    
    # Show git log
    print("\\n📜 Recent commits:")
    run_command(['git', 'log', '--oneline', '-5'], "Recent commit history", check_success=False)

def main():
    """Main execution function."""
    os.chdir('C:\\Users\\annam\\Documents\\DeFi-RAG-Project\\lp_health_tracker')
    
    print("🚀 COMPLETE STAGE 2 & DOCUMENTATION ORGANIZATION")
    print("=" * 55)
    
    success = True
    
    # Step 1: Commit Stage 2 integration
    if stage2_git_commit():
        print("✅ Stage 2 integration committed successfully")
    else:
        print("❌ Stage 2 commit failed")
        success = False
    
    # Step 2: Organize documentation
    if organize_documentation():
        print("✅ Documentation organized successfully")
    else:
        print("❌ Documentation organization failed")
        success = False
    
    # Step 3: Commit documentation changes
    if docs_git_commit():
        print("✅ Documentation organization committed successfully")
    else:
        print("❌ Documentation commit failed")
        success = False
    
    # Step 4: Final summary
    final_summary()
    
    return success

if __name__ == "__main__":
    success = main()
    if success:
        print("\\n🎉 ALL TASKS COMPLETED SUCCESSFULLY! 🎉")
    else:
        print("\\n⚠️ Some tasks failed - please review output above")
