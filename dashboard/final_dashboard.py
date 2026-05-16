from dotenv import load_dotenv
import os
import time
import json
from pathlib import Path

import streamlit as st
import networkx as nx
import google.generativeai as genai
import pandas as pd

try:
    from bert_score import score as bert_score
    BERTSCORE_AVAILABLE = True
except Exception:
    bert_score = None
    BERTSCORE_AVAILABLE = False


# -----------------------------
# LOAD ENV
# -----------------------------

load_dotenv()


# -----------------------------
# GEMINI SETUP
# -----------------------------

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("models/gemini-2.5-flash")

# -----------------------------
# COST CONFIG
# -----------------------------

PRICING = {
    "input": 0.075,
    "output": 0.30,
}


def estimate_tokens(text: str) -> int:
    # Rough token estimate: about 4 chars/token.
    return max(1, len(text) // 4)


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    input_cost = (input_tokens / 1_000_000) * PRICING["input"]
    output_cost = (output_tokens / 1_000_000) * PRICING["output"]
    return input_cost + output_cost


@st.cache_data
def load_text_context() -> dict:
    context = {}
    data_dir = Path("data")

    if not data_dir.exists():
        return context

    for txt_file in data_dir.glob("*.txt"):
        try:
            context[txt_file.stem] = txt_file.read_text(encoding="utf-8")
        except Exception:
            # Skip unreadable files to keep dashboard resilient.
            continue

    return context


def basic_retrieve(query: str, context_map: dict, top_k: int = 4) -> list[str]:
    words = [w.strip().lower() for w in query.split() if w.strip()]
    scored = []

    for source, content in context_map.items():
        lowered = content.lower()
        score = sum(1 for w in words if w in lowered)
        if score > 0:
            sentences = [s.strip() for s in content.split(".") if s.strip()]
            picked = [s for s in sentences if any(w in s.lower() for w in words)]
            snippet = ". ".join(picked[:3]) if picked else ""
            if snippet:
                scored.append((score, source, snippet))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [f"[{source}] {snippet}" for _, source, snippet in scored[:top_k]]


def llm_judge_eval(query: str, answer: str) -> dict:
    prompt = f"""
You are an evaluation judge for retrieval QA systems.
Evaluate the answer quality from 1-10 using these criteria:
- relevance to the user question
- factual consistency with provided style and context
- clarity and completeness

Question:
{query}

Answer:
{answer}

Return strictly in this format:
SCORE: <number>
RATIONALE: <one short paragraph>
"""

    try:
        judge = model.generate_content(prompt).text
    except Exception as exc:
        return {"score": None, "raw": f"Judge unavailable: {exc}"}

    parsed_score = None
    for line in judge.splitlines():
        if line.strip().upper().startswith("SCORE:"):
            token = line.split(":", 1)[1].strip().split()[0]
            try:
                parsed_score = float(token)
            except Exception:
                parsed_score = None
            break

    return {"score": parsed_score, "raw": judge}


def bertscore_eval(reference: str, candidate: str) -> dict:
    if not BERTSCORE_AVAILABLE:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "status": "bert-score package not installed"}

    try:
        p, r, f1 = bert_score([candidate], [reference], lang="en", model_type="distilbert-base-uncased")
        return {
            "precision": float(p[0]),
            "recall": float(r[0]),
            "f1": float(f1[0]),
            "status": "ok",
        }
    except Exception as exc:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "status": f"error: {exc}"}


# -----------------------------
# GRAPH DATA
# -----------------------------

graph_data = {
    "GraphRAG": "GraphRAG extends Retrieval Augmented Generation using knowledge graphs and connected entities.",
    "RAG": "RAG retrieves relevant external information before LLM generation.",
    "Embeddings": "Embeddings convert text into numerical vectors for semantic search.",
    "LLM": "Large Language Models generate human-like responses.",
    "Transformers": "Transformers use attention mechanisms for language understanding.",
    "Knowledge Graph": "Knowledge graphs store entities and relationships.",
    "Entities": "Entities are important concepts extracted from documents.",
}


# -----------------------------
# GRAPH CREATION
# -----------------------------

G = nx.Graph()
G.add_edge("GraphRAG", "RAG")
G.add_edge("RAG", "Embeddings")
G.add_edge("GraphRAG", "Knowledge Graph")
G.add_edge("Knowledge Graph", "Entities")
G.add_edge("Transformers", "LLM")


# -----------------------------
# STREAMLIT UI
# -----------------------------

st.title("GraphRAG Inference Hackathon")
st.write("Compare LLM-Only vs Basic RAG vs GraphRAG")

query = st.text_input("Enter your question")


# -----------------------------
# RUN PIPELINES
# -----------------------------

if st.button("Run Comparison") and query.strip():
    # =========================================
    # PIPELINE 1 — LLM ONLY
    # =========================================

    llm_prompt = query
    llm_in_tokens = estimate_tokens(llm_prompt)

    start = time.time()
    llm_response = model.generate_content(llm_prompt)
    llm_latency = time.time() - start

    llm_out_tokens = estimate_tokens(llm_response.text)
    llm_total_tokens = llm_in_tokens + llm_out_tokens
    llm_cost = estimate_cost(llm_in_tokens, llm_out_tokens)

    # =========================================
    # PIPELINE 2 — BASIC RAG (FILE-BASED)
    # =========================================

    context_map = load_text_context()
    retrieved_docs = basic_retrieve(query, context_map, top_k=4)
    rag_context = "\n".join(retrieved_docs)

    if not rag_context:
        rag_context = "No strongly matched context found in local text files."

    rag_prompt = f"""
Answer the question using the context below.

Context:
{rag_context}

Question:
{query}
"""

    rag_in_tokens = estimate_tokens(rag_prompt)

    start = time.time()
    rag_response = model.generate_content(rag_prompt)
    rag_latency = time.time() - start

    rag_out_tokens = estimate_tokens(rag_response.text)
    rag_total_tokens = rag_in_tokens + rag_out_tokens
    rag_cost = estimate_cost(rag_in_tokens, rag_out_tokens)

    # =========================================
    # PIPELINE 3 — GRAPHRAG
    # =========================================

    related_nodes = []
    for node in G.nodes():
        if node.lower() in query.lower():
            related_nodes.append(node)
            related_nodes.extend(list(G.neighbors(node)))

    related_nodes = list(set(related_nodes))

    graph_context_lines = []
    for node in related_nodes:
        if node in graph_data:
            graph_context_lines.append(graph_data[node])

    if not graph_context_lines:
        graph_context_lines = [
            graph_data["GraphRAG"],
            graph_data["Knowledge Graph"],
            graph_data["RAG"],
        ]

    graph_context = "\n".join(graph_context_lines)

    graphrag_prompt = f"""
Answer the question using graph context.

Graph Context:
{graph_context}

Question:
{query}
"""

    graphrag_in_tokens = estimate_tokens(graphrag_prompt)

    start = time.time()
    graphrag_response = model.generate_content(graphrag_prompt)
    graphrag_latency = time.time() - start

    graphrag_out_tokens = estimate_tokens(graphrag_response.text)
    graphrag_total_tokens = graphrag_in_tokens + graphrag_out_tokens
    graphrag_cost = estimate_cost(graphrag_in_tokens, graphrag_out_tokens)

    # =========================================
    # DISPLAY RESULTS
    # =========================================

    st.header("Pipeline Comparison")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("LLM Only")
        st.write(llm_response.text)
        st.write("Tokens:", llm_total_tokens)
        st.write("Latency:", round(llm_latency, 2))
        st.write("Cost:", f"${llm_cost:.6f}")

    with col2:
        st.subheader("Basic RAG")
        st.write(rag_response.text)
        st.write("Tokens:", rag_total_tokens)
        st.write("Latency:", round(rag_latency, 2))
        st.write("Cost:", f"${rag_cost:.6f}")

    with col3:
        st.subheader("GraphRAG")
        st.write(graphrag_response.text)
        st.write("Tokens:", graphrag_total_tokens)
        st.write("Latency:", round(graphrag_latency, 2))
        st.write("Cost:", f"${graphrag_cost:.6f}")

    st.markdown("---")
    st.header("Benchmark Report")

    rows = [
        {
            "Approach": "LLM Only",
            "Input Tokens": llm_in_tokens,
            "Output Tokens": llm_out_tokens,
            "Total Tokens": llm_total_tokens,
            "Latency (s)": round(llm_latency, 3),
            "Cost (USD)": round(llm_cost, 6),
            "Answer": llm_response.text,
        },
        {
            "Approach": "Basic RAG",
            "Input Tokens": rag_in_tokens,
            "Output Tokens": rag_out_tokens,
            "Total Tokens": rag_total_tokens,
            "Latency (s)": round(rag_latency, 3),
            "Cost (USD)": round(rag_cost, 6),
            "Answer": rag_response.text,
        },
        {
            "Approach": "GraphRAG",
            "Input Tokens": graphrag_in_tokens,
            "Output Tokens": graphrag_out_tokens,
            "Total Tokens": graphrag_total_tokens,
            "Latency (s)": round(graphrag_latency, 3),
            "Cost (USD)": round(graphrag_cost, 6),
            "Answer": graphrag_response.text,
        },
    ]

    with st.spinner("Running LLM-as-a-Judge and BERTScore evaluation..."):
        for row in rows:
            judge = llm_judge_eval(query, row["Answer"])
            bscore = bertscore_eval(query, row["Answer"])
            row["Judge Score"] = judge["score"] if judge["score"] is not None else "N/A"
            row["BERTScore F1"] = round(bscore["f1"], 4)
            row["Judge Raw"] = judge["raw"]
            row["BERTScore Status"] = bscore["status"]

    bench_df = pd.DataFrame(
        [
            {
                "Approach": row["Approach"],
                "Input Tokens": row["Input Tokens"],
                "Output Tokens": row["Output Tokens"],
                "Total Tokens": row["Total Tokens"],
                "Latency (s)": row["Latency (s)"],
                "Cost (USD)": row["Cost (USD)"],
                "Judge Score": row["Judge Score"],
                "BERTScore F1": row["BERTScore F1"],
            }
            for row in rows
        ]
    )

    st.dataframe(bench_df, use_container_width=True, hide_index=True)

    export_json = json.dumps(
        {
            "query": query,
            "results": [
                {
                    "Approach": row["Approach"],
                    "Input Tokens": row["Input Tokens"],
                    "Output Tokens": row["Output Tokens"],
                    "Total Tokens": row["Total Tokens"],
                    "Latency (s)": row["Latency (s)"],
                    "Cost (USD)": row["Cost (USD)"],
                    "Judge Score": row["Judge Score"],
                    "BERTScore F1": row["BERTScore F1"],
                    "Judge Raw": row["Judge Raw"],
                    "BERTScore Status": row["BERTScore Status"],
                }
                for row in rows
            ],
        },
        indent=2,
        ensure_ascii=True,
        default=str,
    )

    e1, e2 = st.columns(2)
    with e1:
        st.download_button(
            label="Download Benchmark CSV",
            data=bench_df.to_csv(index=False),
            file_name="benchmark_report.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with e2:
        st.download_button(
            label="Download Benchmark JSON",
            data=export_json,
            file_name="benchmark_report.json",
            mime="application/json",
            use_container_width=True,
        )

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Fastest", bench_df.loc[bench_df["Latency (s)"].idxmin(), "Approach"], f"{bench_df['Latency (s)'].min():.3f}s")
    with k2:
        st.metric("Lowest Cost", bench_df.loc[bench_df["Cost (USD)"].idxmin(), "Approach"], f"${bench_df['Cost (USD)'].min():.6f}")
    with k3:
        top_judge_idx = bench_df["Judge Score"].apply(lambda x: -1 if x == "N/A" else float(x)).idxmax()
        top_judge_val = bench_df.loc[top_judge_idx, "Judge Score"]
        st.metric("Best Judge Score", bench_df.loc[top_judge_idx, "Approach"], f"{top_judge_val}")
    with k4:
        st.metric("Best BERTScore F1", bench_df.loc[bench_df["BERTScore F1"].idxmax(), "Approach"], f"{bench_df['BERTScore F1'].max():.4f}")

    judge_tabs = st.tabs(["LLM Only Judge", "Basic RAG Judge", "GraphRAG Judge"])
    with judge_tabs[0]:
        st.write(rows[0]["Judge Raw"])
    with judge_tabs[1]:
        st.write(rows[1]["Judge Raw"])
    with judge_tabs[2]:
        st.write(rows[2]["Judge Raw"])

    if not BERTSCORE_AVAILABLE:
        st.warning("BERTScore package is not installed in this environment. Install with: pip install bert-score")
