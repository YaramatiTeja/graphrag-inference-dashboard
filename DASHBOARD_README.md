# GraphRAG Hackathon - Comparison Dashboard

## ✨ Overview

A **Streamlit-based comparison dashboard** for evaluating three RAG architectures without ChromaDB dependencies:
- **LLM Only**: Direct LLM responses without context
- **Basic RAG**: Retrieve-augmented generation with simple keyword search
- **GraphRAG**: Enhanced RAG with knowledge graph simulation

**Key Features:**
- ✅ **No ChromaDB** (bypassed to avoid Windows/Python 3.12 build issues)
- ✅ **In-memory file-based retrieval** (reads from `data/*.txt`)
- ✅ **Metrics dashboard**: tokens, latency, cost estimation
- ✅ **Side-by-side comparison** of all three approaches
- ✅ **Python 3.12 compatible** on Windows
- ✅ **Minimal dependencies** (no build tools needed)

---

## 🚀 Quick Start (5 minutes)

### 1. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

**If you hit any issues**, try installing packages individually:
```bash
python -m pip install streamlit==1.35.0
python -m pip install google-generativeai==0.8.3
python -m pip install sentence-transformers==3.0.1
python -m pip install pandas python-dotenv networkx
```

### 2. Set Up Environment

Create `.env` file in project root:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

Get your API key from: https://aistudio.google.com/app/apikeys

### 3. Run Dashboard

**Option A: Automated launcher**
```bash
python run_dashboard.py
```

**Option B: Manual startup**
```bash
python -m streamlit run dashboard/streamlit_dashboard.py
```

The dashboard opens at `http://localhost:8501`

---

## 📊 Dashboard Features

### Single Query Mode
- Test each pipeline individually
- Compare metrics for one approach at a time
- See retrieved sources for RAG approaches

### Batch Comparison Mode
- Run all three approaches simultaneously
- View side-by-side metrics comparison
- Compare response quality and costs

### Metrics Tracked
| Metric | Description |
|--------|-------------|
| **Input Tokens** | Tokens in the prompt/context |
| **Output Tokens** | Tokens in the response |
| **Total Tokens** | Sum of input + output |
| **Latency** | Response time in seconds |
| **Cost** | Estimated API cost in USD |
| **Sources** | Retrieved documents (RAG only) |

---

## 🔧 Architecture

### File Structure
```
graphrag-hackathon/
├── dashboard/
│   ├── streamlit_dashboard.py    ← Main dashboard (NO ChromaDB!)
│   └── final_dashboard.py        ← Original (legacy)
├── data/
│   ├── graphrag.txt             ← Context data
│   ├── rag.txt
│   └── llm.txt
├── rag/
│   ├── basic_rag.py             ← RAG implementation
│   └── query_rag.py
├── graphrag/
│   └── graphrag_pipeline.py      ← GraphRAG implementation
├── requirements.txt              ← Dependencies (NO ChromaDB)
├── .env                          ← API credentials
├── run_dashboard.py              ← Launcher script
└── README.md                     ← This file
```

### How It Works

**LLM Only Pipeline:**
```
Query → Gemini API → Response
```

**Basic RAG Pipeline:**
```
Query → File Search → Context → Augmented Prompt → Gemini API → Response
```

**GraphRAG Pipeline:**
```
Query → Entity Embedding → Knowledge Graph Traversal → Context → 
        Augmented Prompt → Gemini API → Response
```

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'chromadb'"
✅ **Resolved** - New dashboard doesn't use ChromaDB!

### Issue: "ModuleNotFoundError: No module named 'streamlit'"
**Solution:**
```bash
python -m pip install streamlit==1.35.0
```

### Issue: "GEMINI_API_KEY not found in .env"
**Solution:**
1. Create `.env` file in project root
2. Add your API key: `GEMINI_API_KEY=your_key`
3. Get key from: https://aistudio.google.com/app/apikeys

### Issue: "sentence-transformers" import fails
**Solution:**
```bash
python -m pip install --upgrade sentence-transformers
```

### Issue: "Failed building wheel for..." on Windows
**Solution:** You don't need to build wheels anymore!
The new dashboard avoids problematic packages like:
- ❌ chromadb (removed)
- ❌ chroma-hnswlib (removed)
- ❌ faiss-cpu (removed)

All dependencies are pure Python or pre-built wheels.

---

## 📈 Performance Expectations

### Typical Response Times
- **LLM Only**: 1-3 seconds
- **Basic RAG**: 2-4 seconds  
- **GraphRAG**: 3-5 seconds

### Estimated Costs (per query)
- **LLM Only**: $0.000001 - $0.00001 (very cheap)
- **Basic RAG**: $0.00001 - $0.0001 (cheap)
- **GraphRAG**: $0.0001 - $0.001 (still cheap)

*Based on Gemini 2.5 Flash pricing*

---

## 🎓 What's Different from Original

| Feature | Original | New |
|---------|----------|-----|
| Storage | ChromaDB (persistent) | In-memory + file-based |
| Build Tools | ⚠️ Needs MSVC 14.0 | ✅ Pure Python |
| Windows 3.12 | ❌ Fails | ✅ Works |
| Setup Time | 15+ minutes | < 5 minutes |
| Dependency Issues | ❌ Yes (build errors) | ✅ No |
| Features | Dashboard | ✅ Enhanced metrics |

---

## 🔄 Data Sources

The dashboard uses text files from `data/` directory as context:
- `data/graphrag.txt` - GraphRAG concepts
- `data/rag.txt` - RAG concepts  
- `data/llm.txt` - LLM concepts

Add your own `.txt` files to `data/` to expand context!

---

## 💡 Advanced Usage

### Use with Your Own Documents

Add text files to `data/` folder:
```
data/
├── my_document.txt
├── another_file.txt
└── research.txt
```

The dashboard will automatically include them in retrieval!

### Customize Gemini Model

Edit `streamlit_dashboard.py` line ~80:
```python
model = genai.GenerativeModel("models/gemini-2.5-flash")
```

Available models:
- `gemini-2.5-flash` (recommended)
- `gemini-1.5-pro`
- `gemini-1.5-flash`

### Adjust Token Cost Estimates

Edit `PRICING` dictionary in `streamlit_dashboard.py`:
```python
PRICING = {
    "input": 0.075,      # Per 1M tokens
    "output": 0.30       # Per 1M tokens
}
```

---

## 📝 Example Queries

Try these questions with the dashboard:

1. **"Explain the difference between RAG and GraphRAG"**
2. **"What are embeddings used for?"**
3. **"How does ChromaDB work with embeddings?"**
4. **"What is a knowledge graph?"**
5. **"Compare LLM-only vs RAG approaches"**

---

## 🎯 Hackathon Submission

This dashboard is perfect for hackathon submissions because:
- ✅ **No build/setup issues** - clean installation
- ✅ **Shows metrics** - tokens, latency, cost
- ✅ **Compares approaches** - demonstrates understanding
- ✅ **Works reliably** - no dependency problems
- ✅ **Professional UI** - Streamlit looks polished
- ✅ **Reproducible** - easy for judges to run

---

## 📚 Related Files

| File | Purpose |
|------|---------|
| `dashboard/streamlit_dashboard.py` | Main dashboard (use this!) |
| `dashboard/final_dashboard.py` | Original version (legacy) |
| `run_dashboard.py` | Automated launcher |
| `requirements.txt` | Dependencies (updated) |
| `rag/basic_rag.py` | RAG implementation reference |
| `graphrag/graphrag_pipeline.py` | GraphRAG reference |

---

## 🤝 Support

If you encounter issues:
1. Check `.env` has your API key
2. Run `python -m pip install -r requirements.txt` again
3. Delete `.streamlit/` folder and restart
4. Try: `python -m pip install --upgrade streamlit`

---

## ⚡ Pro Tips

1. **First run is slower** - models download on first use (embedding model ~500MB)
2. **API key security** - Never commit `.env` to git
3. **Test your data** - Ensure `data/` files contain relevant content
4. **Cost estimation** - Shown in USD, uses Gemini's official pricing
5. **For hackathon** - Batch mode shows best side-by-side comparison

---

**Happy hacking! 🚀**
