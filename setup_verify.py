#!/usr/bin/env python3
"""
GraphRAG Hackathon - Quick Setup & Verification Script
Helps diagnose and fix common installation issues
"""

import subprocess
import sys
import os
from pathlib import Path

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def check_python():
    """Check Python version"""
    print_header("1️⃣ Python Version Check")
    
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("❌ ERROR: Python 3.11+ required")
        return False
    
    print("✅ Python version is OK")
    return True

def check_env_file():
    """Check for .env file"""
    print_header("2️⃣ Environment File Check")
    
    if not Path(".env").exists():
        print("❌ .env file not found")
        print("\nCreate .env file with:")
        print("  GEMINI_API_KEY=your_api_key_here")
        print("\nGet your API key at:")
        print("  https://aistudio.google.com/app/apikeys")
        return False
    
    with open(".env", "r") as f:
        content = f.read()
        if "GEMINI_API_KEY" in content:
            print("✅ .env file exists with GEMINI_API_KEY")
            return True
        else:
            print("⚠ .env file exists but missing GEMINI_API_KEY")
            return False

def check_dependencies():
    """Check if required packages are installed"""
    print_header("3️⃣ Dependencies Check")
    
    required = {
        "streamlit": "Streamlit (UI framework)",
        "google.generativeai": "Gemini API client",
        "sentence_transformers": "Embeddings model",
        "pandas": "Data processing",
        "dotenv": "Environment loading",
        "networkx": "Graph processing"
    }
    
    all_good = True
    for package, description in required.items():
        try:
            __import__(package)
            print(f"✅ {description}: {package}")
        except ImportError:
            print(f"❌ {description}: {package} (NOT INSTALLED)")
            all_good = False
    
    return all_good

def check_data_files():
    """Check if data files exist"""
    print_header("4️⃣ Data Files Check")
    
    data_path = Path("data")
    if not data_path.exists():
        print("❌ data/ directory not found")
        return False
    
    txt_files = list(data_path.glob("*.txt"))
    if not txt_files:
        print("⚠ data/ directory exists but is empty")
        print("  Add .txt files to data/ for RAG context")
        return False
    
    print(f"✅ Found {len(txt_files)} context files:")
    for f in txt_files:
        size = f.stat().st_size
        print(f"   - {f.name} ({size:,} bytes)")
    
    return True

def install_dependencies():
    """Install missing dependencies"""
    print_header("5️⃣ Installing Dependencies")
    
    print("Installing from requirements.txt...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ Dependencies installed successfully")
        return True
    else:
        print("❌ Installation failed")
        print("\nError output:")
        print(result.stderr)
        return False

def test_imports():
    """Test that imports work"""
    print_header("6️⃣ Import Test")
    
    imports = {
        "streamlit": "Streamlit",
        "google.generativeai": "Gemini API",
        "sentence_transformers": "Embeddings",
        "pandas": "Pandas",
        "dotenv": "Python-dotenv",
        "networkx": "NetworkX"
    }
    
    all_good = True
    for module, name in imports.items():
        try:
            __import__(module)
            print(f"✅ {name}: {module}")
        except Exception as e:
            print(f"❌ {name}: {module} - {e}")
            all_good = False
    
    return all_good

def main():
    """Run all checks"""
    print("\n" + "="*60)
    print("  GraphRAG Hackathon - Setup Verification")
    print("="*60)
    
    checks = [
        ("Python Version", check_python),
        ("Environment File", check_env_file),
        ("Data Files", check_data_files),
    ]
    
    results = {}
    for name, check in checks:
        results[name] = check()
    
    # If data files missing, create sample
    if not results.get("Data Files", False):
        print("\n" + "="*60)
        print("  Creating sample data files...")
        print("="*60)
        
        Path("data").mkdir(exist_ok=True)
        
        sample_files = {
            "graphrag.txt": """GraphRAG: Graph-based Retrieval Augmented Generation
GraphRAG extends traditional RAG by incorporating knowledge graphs.
Knowledge graphs store entities and their relationships.
This enables more sophisticated reasoning and multi-hop retrieval.
GraphRAG is useful for complex queries requiring entity reasoning.
""",
            "rag.txt": """RAG: Retrieval Augmented Generation
RAG improves LLM responses by retrieving relevant external information.
The retrieved context is then used to augment the LLM prompt.
This reduces hallucinations and provides factual accuracy.
RAG uses semantic search via embeddings for retrieval.
""",
            "llm.txt": """LLM: Large Language Models
LLMs are neural networks trained on vast amounts of text.
They generate human-like responses based on learned patterns.
Popular LLMs include GPT, Claude, Gemini, and LLaMA.
LLMs can perform tasks like translation, summarization, and reasoning.
"""
        }
        
        for filename, content in sample_files.items():
            with open(f"data/{filename}", "w") as f:
                f.write(content)
            print(f"✅ Created data/{filename}")
    
    # Check if dependencies need installation
    if not results.get("Dependencies", True):
        print("\n" + "="*60)
        print("  Installing Missing Dependencies...")
        print("="*60)
        install_dependencies()
    
    # Final test
    print_header("Final Verification")
    test_imports()
    
    # Summary and next steps
    print_header("Next Steps")
    print("✅ Setup Complete!")
    print("\nTo launch the dashboard, run one of:")
    print("  • python run_dashboard.py          (cross-platform)")
    print("  • run_dashboard.bat                (Windows batch)")
    print("  • ./run_dashboard.ps1              (Windows PowerShell)")
    print("  • streamlit run dashboard/streamlit_dashboard.py")
    print("\nThe dashboard will open at: http://localhost:8501")
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
