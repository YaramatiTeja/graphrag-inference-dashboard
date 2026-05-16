#!/usr/bin/env python3
"""
GraphRAG Hackathon Dashboard - Startup Script
Automatically installs dependencies and runs the Streamlit dashboard
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a shell command with error handling"""
    print(f"\n{'='*60}")
    print(f"📦 {description}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"❌ Failed: {description}")
        return False
    print(f"✅ Success: {description}")
    return True

def main():
    print("\n" + "="*60)
    print("🚀 GraphRAG Hackathon Dashboard Launcher")
    print("="*60)
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("⚠️  Python 3.11+ required. Current version:", sys.version)
        sys.exit(1)
    
    # Check for .env file
    if not Path(".env").exists():
        print("\n⚠️  WARNING: .env file not found!")
        print("   Create .env with: GEMINI_API_KEY=your_api_key")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Install/upgrade dependencies
    if not run_command(
        f"{sys.executable} -m pip install --upgrade pip",
        "Upgrading pip"
    ):
        sys.exit(1)
    
    if not run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Installing dependencies from requirements.txt"
    ):
        sys.exit(1)
    
    # Run Streamlit dashboard
    print(f"\n{'='*60}")
    print("🎬 Starting Streamlit Dashboard...")
    print(f"{'='*60}\n")
    
    os.system(f"{sys.executable} -m streamlit run dashboard/streamlit_dashboard.py")

if __name__ == "__main__":
    main()
