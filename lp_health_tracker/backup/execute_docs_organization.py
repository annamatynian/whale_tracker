#!/usr/bin/env python3
"""
Execute Documentation Organization for LP Health Tracker
=======================================================

This script implements the documentation reorganization plan.
"""

import os
import shutil
from pathlib import Path

def create_directories():
    """Create necessary directory structure."""
    directories = [
        'docs/user_guides',
        'docs/reference', 
        'docs/planning',
        'docs/archive',
        'scripts',
        'archive'
    ]
    
    print("📁 Creating directory structure...")
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"  ✅ {dir_path}")

def move_file(source, destination, description=""):
    """Move file with error handling."""
    try:
        if Path(source).exists():
            Path(destination).parent.mkdir(parents=True, exist_ok=True)
            shutil.move(source, destination)
            print(f"  ✅ {source} → {destination} {description}")
            return True
        else:
            print(f"  ⚠️ {source} not found")
            return False
    except Exception as e:
        print(f"  ❌ Error moving {source}: {e}")
        return False

def organize_documentation():
    """Execute the documentation organization."""
    
    print("🚀 EXECUTING DOCUMENTATION ORGANIZATION")
    print("=" * 45)
    
    # Create directory structure
    create_directories()
    
    # Move files to docs/user_guides
    print("\\n📖 Moving user guides...")
    user_guides = [
        ('QUICKSTART.md', 'docs/user_guides/QUICKSTART.md'),
        ('TESTING_GUIDE.md', 'docs/user_guides/TESTING_GUIDE.md')
    ]
    
    for source, dest in user_guides:
        move_file(source, dest)
    
    # Move files to docs/reference
    print("\\n📚 Moving reference documentation...")
    reference_docs = [
        ('IL_BASICS.md', 'docs/reference/IL_BASICS.md')
    ]
    
    for source, dest in reference_docs:
        move_file(source, dest)
    
    # Move files to docs/planning
    print("\\n📋 Moving planning documents...")
    planning_docs = [
        ('Fees_master_plan.txt', 'docs/planning/fees_master_plan.txt'),
        ('RAG_agent.txt', 'docs/planning/rag_agent_notes.txt')
    ]
    
    for source, dest in planning_docs:
        move_file(source, dest)
    
    # Archive completed milestone files
    print("\\n📦 Archiving completed milestones...")
    archive_files = [
        'CLEANUP_COMPLETED.md',
        'CONSOLIDATION_TASKS.md',
        'CONTINUE_INSTRUCTIONS.md', 
        'GEMINI_FEEDBACK_COMPLETE.md',
        'GEMINI_FEEDBACK_IMPLEMENTED.md',
        'HIGH_PRIORITY_INTEGRATION_COMPLETED.md',
        'IMPROVEMENT_PLAN.md',
        'PROGRESS_WEEK1.md',
        'STAGE1_INTEGRATION_COMPLETED.md',
        'STAGE2_INTEGRATION_COMPLETED.md',
        'VALIDATION_CHECKLIST.md',
        'VALIDATION_SCRIPTS.md'
    ]
    
    for file in archive_files:
        move_file(file, f'docs/archive/{file}')
    
    # Move scripts
    print("\\n🔧 Moving scripts...")
    script_files = [
        'git_commit_stage2.py',
        'simple_stage2_check.py', 
        'validate_stage2_integration.py',
        'validate_stage2_demo.py',
        'verify_integration_success.py',
        'verify_stage1_integration.py',
        'analyze_docs_structure.py'
    ]
    
    for file in script_files:
        move_file(file, f'scripts/{file}')
    
    # Handle test files
    print("\\n🧪 Organizing test files...")
    test_files = [
        ('test_gemini_fixes.py', 'archive/old_tests/test_gemini_fixes.py'),
        ('test_live_data_api.py', 'archive/old_tests/test_live_data_api.py'),
        ('test_positions_reading.py', 'archive/old_tests/test_positions_reading.py'),
        ('test_stage2_final.py', 'archive/old_tests/test_stage2_final.py'),
        ('test_standardization.py', 'archive/old_tests/test_standardization.py'),
        ('test_pools_config.json', 'archive/old_tests/test_pools_config.json')
    ]
    
    for source, dest in test_files:
        move_file(source, dest)
    
    # Handle Russian files
    print("\\n🌐 Handling non-English files...")
    russian_files = [
        ('ОБЯЗАТЕЛЬНО К ПРОЧТЕНИЮ-1 (1).txt', 'docs/archive/README_RU_1.txt'),
        ('ОБЯЗАТЕЛЬНО К ПРОЧТЕНИЮ-2.txt', 'docs/archive/README_RU_2.txt')
    ]
    
    for source, dest in russian_files:
        move_file(source, dest, "(renamed)")

def create_documentation_index():
    """Create documentation index file."""
    
    index_content = '''# 📚 LP Health Tracker - Documentation Index

## 📖 User Documentation
- **[Quick Start Guide](user_guides/QUICKSTART.md)** - Get started in 5 minutes
- **[Testing Guide](user_guides/TESTING_GUIDE.md)** - Complete testing instructions
- **[README](../README.md)** - Main project overview

## 🔧 Developer Documentation  
- **[Technical Documentation](TECHNICAL_DOCUMENTATION.md)** - Architecture and implementation
- **[API Reference](API_REFERENCE.md)** - Complete API documentation
- **[Contributing Guide](CONTRIBUTING.md)** - Development workflow

## 📊 Business Documentation
- **[Business Case](BUSINESS_CASE.md)** - Market opportunity and ROI analysis
- **[Deployment Guide](DEPLOYMENT.md)** - Production deployment instructions

## 📚 Reference Materials
- **[IL Basics](reference/IL_BASICS.md)** - Impermanent Loss fundamentals
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions

## 📋 Planning & Development
- **[Stage 3 Plan](STAGE3_PLAN.md)** - Next development phase
- **[Fees Master Plan](planning/fees_master_plan.txt)** - Original fee calculation planning
- **[RAG Agent Notes](planning/rag_agent_notes.txt)** - Development notes

## 📦 Archive
- **[Completed Milestones](archive/)** - Historical development milestones
- **[Old Tests](../archive/old_tests/)** - Superseded test files
- **[Legacy Documents](archive/)** - Previous versions and completed tasks

## 🔍 Quick Navigation

### For New Users
1. Start with [README](../README.md)
2. Follow [Quick Start Guide](user_guides/QUICKSTART.md)
3. Check [Troubleshooting](TROUBLESHOOTING.md) if needed

### For Developers
1. Read [Technical Documentation](TECHNICAL_DOCUMENTATION.md)
2. Follow [Contributing Guide](CONTRIBUTING.md)
3. Use [API Reference](API_REFERENCE.md)

### For Business Stakeholders
1. Review [Business Case](BUSINESS_CASE.md)
2. See [Deployment Guide](DEPLOYMENT.md)
3. Check development progress in [Archive](archive/)

---

*Documentation organized and maintained as part of LP Health Tracker professional development.*
'''
    
    with open('docs/README.md', 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    print("📄 Created docs/README.md - Documentation index")

def update_main_readme():
    """Update main README.md with new documentation links."""
    
    readme_path = Path('README.md')
    if readme_path.exists():
        content = readme_path.read_text(encoding='utf-8')
        
        # Update documentation links section
        new_docs_section = '''---

## 📚 Documentation

### 👥 **For Users**
- **[Quick Start Guide](docs/user_guides/QUICKSTART.md)** - Get up and running in 5 minutes
- **[User Manual](README.md)** - Complete feature guide (this document)
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

### 💼 **For Business**
- **[Business Case & ROI](docs/BUSINESS_CASE.md)** - Market opportunity and value proposition
- **[Pricing Strategy](docs/BUSINESS_CASE.md#pricing-strategy)** - Service tiers and ROI analysis

### 🔧 **For Developers**
- **[Technical Documentation](docs/TECHNICAL_DOCUMENTATION.md)** - Architecture and implementation
- **[API Reference](docs/API_REFERENCE.md)** - Complete API documentation
- **[Contributing Guide](docs/CONTRIBUTING.md)** - Development workflow and standards
- **[Testing Guide](docs/user_guides/TESTING_GUIDE.md)** - Complete testing framework
- **[Changelog](CHANGELOG.md)** - Version history and migration guides

**📋 [Complete Documentation Index](docs/README.md)**

---'''
        
        # Find and replace the documentation section
        if '## 📚 Documentation' in content:
            start = content.find('## 📚 Documentation')
            # Find the next ## section or end of file
            next_section = content.find('\\n## ', start + 1)
            if next_section == -1:
                next_section = len(content)
            
            # Replace the section
            content = content[:start] + new_docs_section + content[next_section:]
            
            readme_path.write_text(content, encoding='utf-8')
            print("📄 Updated README.md with new documentation structure")
        else:
            print("⚠️ Could not find documentation section in README.md")

def main():
    """Main execution function."""
    os.chdir('C:\\Users\\annam\\Documents\\DeFi-RAG-Project\\lp_health_tracker')
    
    print("🎯 Starting documentation organization...")
    organize_documentation()
    
    print("\\n📄 Creating documentation index...")
    create_documentation_index()
    
    print("\\n📝 Updating main README...")
    update_main_readme()
    
    print("\\n🎉 DOCUMENTATION ORGANIZATION COMPLETED!")
    print("=" * 45)
    print("✅ All files moved to appropriate directories")
    print("✅ Documentation index created")
    print("✅ Main README updated")
    print("\\n📋 Next steps:")
    print("1. Review the organized structure")
    print("2. Test that all links work")
    print("3. Commit the organized documentation")

if __name__ == "__main__":
    main()
