# 🚀 GraphRAG Hackathon - QUICK START

## ⚡ 3-Step Setup (5 minutes)

### Step 1️⃣: Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### Step 2️⃣: Create API Key File

Create a file named `.env` in your project root:
```
GEMINI_API_KEY=your_api_key_here
```

👉 **Get your free API key:** https://aistudio.google.com/app/apikeys

### Step 3️⃣: Run Dashboard

**Windows (easiest):**
```bash
run_dashboard.bat
```

**Any OS:**
```bash
python run_dashboard.py
```

**Manual:**
```bash
python -m streamlit run dashboard/streamlit_dashboard.py
```

✅ **Done!** Dashboard opens at: http://localhost:8501

---

## 🎯 What You Get

A professional dashboard comparing three RAG approaches:

| Approach | How It Works | Best For |
|----------|-------------|----------|
| **LLM Only** | Direct response, no context | Speed, simplicity |
| **Basic RAG** | Retrieve + Augment + Generate | Factual accuracy |
| **GraphRAG** | Knowledge graph + reasoning | Complex questions |

---

## 📊 Dashboard Modes

### Single Query Mode
- Test one approach at a time
- See metrics for each individually

### Batch Comparison Mode ⭐ (Recommended for hackathon)
- Run all three simultaneously
- View side-by-side metrics table
- Perfect for demos

---

## 📈 Metrics Included

For each approach, you'll see:
- ⏱️ **Latency**: Response time in seconds
- 🔤 **Input Tokens**: Tokens in your question
- 📝 **Output Tokens**: Tokens in the response
- 📊 **Total Tokens**: Combined token count
- 💰 **Cost**: Estimated USD cost for this query
- 📚 **Sources**: Retrieved documents (RAG only)

---

## 🎓 Example Questions to Try

1. "What is GraphRAG and how is it different from regular RAG?"
2. "Explain embeddings and their role in semantic search"
3. "How do knowledge graphs improve retrieval?"
4. "What are the advantages of using ChromaDB for vector storage?"
5. "Compare the computational costs of LLM-only vs RAG approaches"

---

## ✅ If You Get Stuck

### Issue: Module not found error
```bash
python -m pip install -r requirements.txt
```

### Issue: GEMINI_API_KEY error
Create `.env` file with your API key from: https://aistudio.google.com/app/apikeys

### Issue: Dashboard won't open
```bash
python -m streamlit run dashboard/streamlit_dashboard.py --server.port 8501
```
Then open: http://localhost:8501

### Issue: Verify everything works
```bash
python setup_verify.py
```

---

## 📚 Full Documentation

- **Setup details:** Read `SETUP_GUIDE.md`
- **Dashboard features:** Read `DASHBOARD_README.md`
- **Solution summary:** Read `SOLUTION_SUMMARY.md`

---

## ✨ That's It!

You're ready to:
- ✅ Compare three RAG approaches
- ✅ View metrics (tokens, latency, cost)
- ✅ Demo for hackathon judges
- ✅ Test with your own questions
- ✅ Add your own data files to `data/` folder

**Happy hacking!** 🚀

---

**Note:** This setup uses Python 3.12 on Windows with NO build tool dependencies. The original ChromaDB issues are completely bypassed using file-based context storage.
