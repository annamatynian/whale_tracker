#!/usr/bin/env python3
"""
Git commit script for HMM data collector changes
"""
import subprocess
import sys
import os

def run_git_command(cmd, cwd=None):
    """Run git command and return result"""
    try:
        result = subprocess.run(
            cmd, 
            cwd=cwd or "C:/Users/annam/Documents/DeFi-RAG-Project/lp_health_tracker",
            capture_output=True, 
            text=True,
            check=False
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def main():
    project_dir = "C:/Users/annam/Documents/DeFi-RAG-Project/lp_health_tracker"
    
    print("🔍 Checking git status...")
    stdout, stderr, code = run_git_command(["git", "status", "--short"], project_dir)
    
    if code != 0:
        print(f"❌ Git error: {stderr}")
        return 1
    
    print("Current changes:")
    print(stdout or "No changes detected")
    
    print("\n📦 Adding HMM data collector to git...")
    stdout, stderr, code = run_git_command(["git", "add", "hmm/hmm_market_data_collector.py"], project_dir)
    
    if code != 0:
        print(f"❌ Git add error: {stderr}")
        return 1
    
    print("✅ Files added successfully")
    
    commit_message = """feat: Enhance HMM data collector with whale activity detection

- Add comprehensive whale activity detection using Z-score and IQR analysis
- Include max_priority_fee_gwei metric for quantifying jump bids  
- Add hourly_volume_percentage_of_total for activity significance
- Implement outlier_detected flag for anomalous gas price behavior
- Fix indentation issues in gas stats calculation
- Update CSV headers with new whale detection metrics
- Add proper error handling and logging throughout

This enables HMM models to distinguish between:
- High volatility + high volume (profitable for LP)
- High volatility + low volume (dangerous for LP)
- Normal activity vs whale-driven market movements"""

    print("\n💾 Committing changes...")
    stdout, stderr, code = run_git_command(["git", "commit", "-m", commit_message], project_dir)
    
    if code != 0:
        print(f"❌ Git commit error: {stderr}")
        return 1
    
    print("✅ Commit successful!")
    print(stdout)
    
    print("\n📊 Final git status:")
    stdout, stderr, code = run_git_command(["git", "status", "--short"], project_dir)
    print(stdout or "Working directory clean")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
