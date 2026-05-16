"""
GraphRAG Hackathon - Comparison Dashboard
Compares LLM-only, Basic RAG, and GraphRAG approaches
WITHOUT ChromaDB (uses in-memory file-based storage instead)
"""

import streamlit as st
import os
import time
import json
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import pandas as pd
import warnings

try:
    from bert_score import score as bert_score
    BERTSCORE_AVAILABLE = True
except Exception:
    bert_score = None
    BERTSCORE_AVAILABLE = False

warnings.filterwarnings('ignore')

# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="GraphRAG Comparison Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Gemini pricing (per million tokens)
PRICING = {
    "input": 0.075,      # $0.075 per 1M input tokens
    "output": 0.30       # $0.30 per 1M output tokens
}

# ============================================================
# INITIALIZE SESSION STATE
# ============================================================

if "responses" not in st.session_state:
    st.session_state.responses = {}
    st.session_state.metrics = {}

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def load_text_files():
    """Load all text files from data directory as context"""
    data_path = Path("data")
    context_data = {}
    
    if data_path.exists():
        for txt_file in data_path.glob("*.txt"):
            with open(txt_file, 'r', encoding='utf-8') as f:
                context_data[txt_file.stem] = f.read()
    
    return context_data


def estimate_tokens(text):
    """Rough token estimation: ~4 chars per token"""
    return max(1, len(text) // 4)


def calculate_cost(input_tokens, output_tokens):
    """Calculate estimated cost in USD"""
    input_cost = (input_tokens / 1_000_000) * PRICING["input"]
    output_cost = (output_tokens / 1_000_000) * PRICING["output"]
    return input_cost + output_cost


def create_simple_search(query, context_data):
    """Simple keyword-based retrieval (replaces ChromaDB)"""
    query_lower = query.lower()
    results = []
    
    for source, content in context_data.items():
        # Simple keyword matching
        if any(word in content.lower() for word in query_lower.split()):
            # Extract relevant chunks (sentences containing query words)
            sentences = content.split('.')
            relevant = [s.strip() for s in sentences 
                       if any(word in s.lower() for word in query_lower.split())
                       and s.strip()]
            
            if relevant:
                snippet = '. '.join(relevant[:3])  # First 3 relevant sentences
                results.append({
                    'source': source,
                    'content': snippet,
                    'relevance': len([w for w in query_lower.split() if w in content.lower()])
                })
    
    # Sort by relevance
    results.sort(key=lambda x: x['relevance'], reverse=True)
    return results[:3]  # Return top 3


# ============================================================
# BENCHMARK & EVALUATION FUNCTIONS
# ============================================================

def evaluate_with_llm_judge(query, answer):
    """Use LLM-as-a-Judge to evaluate answer quality"""
    model, _ = load_models()
    
    judge_prompt = f"""You are an expert evaluator. Rate the following answer on a scale of 1-10.

Query: {query}

Answer: {answer}

Provide evaluation as:
SCORE: [1-10]
REASONING: [brief explanation]"""
    
    try:
        response = model.generate_content(judge_prompt)
        return response.text
    except:
        return "Evaluation unavailable"


def calculate_bertscore(query, answer):
    """Calculate BERTScore between answer and query"""
    if not BERTSCORE_AVAILABLE:
        return {
            'precision': 0.0,
            'recall': 0.0,
            'f1': 0.0,
            'status': 'bert-score package not installed'
        }

    try:
        P, R, F1 = bert_score(
            [answer], 
            [query],
            lang='en',
            model_type='distilbert-base-uncased',
            batch_size=32,
            nthreads=4
        )
        return {
            'precision': float(P[0]),
            'recall': float(R[0]),
            'f1': float(F1[0]),
            'status': 'ok'
        }
    except Exception as exc:
        return {
            'precision': 0.0,
            'recall': 0.0,
            'f1': 0.0,
            'status': f'error: {exc}'
        }


def generate_benchmark_report(results_dict, query):
    """Generate comprehensive benchmark report"""
    report = {
        'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
        'query': query,
        'approaches': {}
    }
    
    for approach, result in results_dict.items():
        approach_name = approach.replace('_', ' ').upper()
        answer = result.get('answer', '')
        
        bertscore = calculate_bertscore(query, answer)
        llm_judge_eval = evaluate_with_llm_judge(query, answer)
        
        report['approaches'][approach_name] = {
            'latency': result.get('latency', 0),
            'input_tokens': result.get('input_tokens', 0),
            'output_tokens': result.get('output_tokens', 0),
            'total_tokens': result.get('total_tokens', 0),
            'cost_usd': result.get('cost', 0),
            'bertscore': bertscore,
            'llm_judge': llm_judge_eval
        }
    
    return report


@st.cache_resource
def load_models():
    """Load Gemini and embedding models"""
    model = genai.GenerativeModel("models/gemini-2.5-flash")
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return model, embedding_model


@st.cache_resource
def load_context():
    """Load and cache text files"""
    return load_text_files()


def llm_only_pipeline(query):
    """LLM-only: Direct response without context"""
    model, _ = load_models()
    
    start_time = time.time()
    
    response = model.generate_content(query)
    answer = response.text
    
    latency = time.time() - start_time
    
    input_tokens = estimate_tokens(query)
    output_tokens = estimate_tokens(answer)
    cost = calculate_cost(input_tokens, output_tokens)
    
    return {
        'answer': answer,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'total_tokens': input_tokens + output_tokens,
        'latency': latency,
        'cost': cost,
        'sources': []
    }


def basic_rag_pipeline(query):
    """Basic RAG: Retrieve + Generate with simple search"""
    model, _ = load_models()
    context_data = load_context()
    
    start_time = time.time()
    
    # Retrieve relevant documents
    retrieved = create_simple_search(query, context_data)
    
    # Build context string
    context_str = "\n\n".join([
        f"[From {r['source']}]\n{r['content']}"
        for r in retrieved
    ])
    
    # Create augmented prompt
    if context_str:
        prompt = f"""Based on the following context, answer the question:

Context:
{context_str}

Question: {query}

Answer:"""
    else:
        prompt = query
    
    response = model.generate_content(prompt)
    answer = response.text
    
    latency = time.time() - start_time
    
    input_tokens = estimate_tokens(prompt)
    output_tokens = estimate_tokens(answer)
    cost = calculate_cost(input_tokens, output_tokens)
    
    return {
        'answer': answer,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'total_tokens': input_tokens + output_tokens,
        'latency': latency,
        'cost': cost,
        'sources': [r['source'] for r in retrieved]
    }


def graphrag_pipeline(query):
    """GraphRAG simulation: Uses structured knowledge graph concepts"""
    model, embedding_model = load_models()
    context_data = load_context()
    
    start_time = time.time()
    
    # Simulate entity extraction from query
    query_embedding = embedding_model.encode(query)
    
    # Simulate knowledge graph traversal with entity relationships
    knowledge_graph_context = """
Key Relationships:
- GraphRAG extends RAG with knowledge graphs
- Knowledge graphs connect entities and relationships
- Entities: GraphRAG, RAG, Embeddings, ChromaDB, LLM, Knowledge Graph
- RAG uses embeddings for semantic search
- Embeddings are numerical vectors for text
- ChromaDB stores vector embeddings
- LLMs generate responses based on context
"""
    
    # Retrieve context with emphasis on relationships
    retrieved = create_simple_search(query, context_data)
    
    # Build knowledge-aware context
    context_str = knowledge_graph_context + "\n\nRetrieved Context:\n"
    context_str += "\n\n".join([
        f"[{r['source']}]\n{r['content']}"
        for r in retrieved
    ])
    
    # Create enhanced prompt with reasoning steps
    prompt = f"""You are a GraphRAG system that reasons through entity relationships.

Knowledge Graph Context:
{context_str}

Question: {query}

Instructions:
1. Identify key entities in the question
2. Follow relationships through the knowledge graph
3. Synthesize information from connected entities
4. Provide a comprehensive answer

Answer:"""
    
    response = model.generate_content(prompt)
    answer = response.text
    
    latency = time.time() - start_time
    
    input_tokens = estimate_tokens(prompt)
    output_tokens = estimate_tokens(answer)
    cost = calculate_cost(input_tokens, output_tokens)
    
    return {
        'answer': answer,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'total_tokens': input_tokens + output_tokens,
        'latency': latency,
        'cost': cost,
        'sources': [r['source'] for r in retrieved]
    }


# ============================================================
# CUSTOM CSS FOR MODERN THEME
# ============================================================

st.markdown("""
<style>
    /* Modern color scheme */
    :root {
        --primary-color: #1f2937;
        --secondary-color: #10b981;
        --accent-color: #3b82f6;
    }
    
    /* Hero section styling */
    .hero-section {
        text-align: center;
        padding: 3rem 2rem;
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.95) 100%);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 2.5rem;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    }
    
    .hero-title {
        font-size: 3.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #3b82f6 0%, #10b981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0 0 0.5rem 0;
        letter-spacing: -0.02em;
    }
    
    .hero-subtitle {
        font-size: 1.1rem;
        color: rgba(226, 232, 240, 0.8);
        margin-top: 0.5rem;
        font-weight: 400;
        letter-spacing: 0.05em;
    }
    
    .divider-gradient {
        height: 3px;
        background: linear-gradient(90deg, transparent, #3b82f6, #10b981, transparent);
        margin: 2rem 0;
        border-radius: 2px;
    }
    
    /* Metric cards styling */
    .metric-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
    }
    
    /* Answer card styling */
    .answer-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.9) 100%);
        border-left: 4px solid #3b82f6;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    /* Button styling */
    .button-primary {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        cursor: pointer;
    }
    
    .button-primary:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HERO SECTION
# ============================================================

st.markdown("""
<div class="hero-section">
    <div class="hero-title">✨ GraphRAG Performance Studio</div>
    <div class="hero-subtitle">Advanced AI Retrieval Benchmark & Comparison Suite</div>
</div>
<div class="divider-gradient"></div>
""", unsafe_allow_html=True)

# Sidebar for configuration
with st.sidebar:
    st.markdown("""
    <div style="padding: 1rem 0; text-align: center;">
        <h3 style="margin: 0; font-size: 1.3rem; margin-bottom: 0.5rem;">⚙️ Settings</h3>
        <p style="margin: 0; color: rgba(226, 232, 240, 0.6); font-size: 0.85rem;">Configure dashboard behavior</p>
    </div>
    <div style="height: 2px; background: linear-gradient(90deg, transparent, #3b82f6, transparent); margin: 1rem 0;"></div>
    """, unsafe_allow_html=True)
    
    mode = st.radio(
        "**Select Mode**",
        ["Single Query", "Batch Comparison"],
        help="📌 Single Query: Test one approach at a time\n⚡ Batch: Compare all three simultaneously"
    )
    
    st.markdown("---")
    st.markdown("""
    <div style="font-size: 0.85rem; color: rgba(226, 232, 240, 0.6); line-height: 1.5;">
        <p><strong>💡 Tip:</strong> Use technical questions about GraphRAG, RAG, embeddings, or knowledge graphs for best results.</p>
    </div>
    """, unsafe_allow_html=True)

# Main interface
if mode == "Single Query":
    st.subheader("🔍 Single Query Mode", divider="blue")
    
    query = st.text_area(
        "Enter your question:",
        placeholder="Ask about GraphRAG, RAG, embeddings, or knowledge graphs...",
        height=100,
        label_visibility="collapsed"
    )
    
    col1, col2, col3 = st.columns(3, gap="small")
    
    with col1:
        if st.button("🤖 LLM Only", use_container_width=True, key="btn_llm"):
            if query.strip():
                with st.spinner("Generating response..."):
                    result = llm_only_pipeline(query)
                    st.session_state.responses['llm_only'] = result
    
    with col2:
        if st.button("📚 Basic RAG", use_container_width=True, key="btn_rag"):
            if query.strip():
                with st.spinner("Retrieving and generating..."):
                    result = basic_rag_pipeline(query)
                    st.session_state.responses['basic_rag'] = result
    
    with col3:
        if st.button("🕸️ GraphRAG", use_container_width=True, key="btn_graph"):
            if query.strip():
                with st.spinner("Processing with knowledge graph..."):
                    result = graphrag_pipeline(query)
                    st.session_state.responses['graphrag'] = result
    
    # Display results with improved cards
    if st.session_state.responses:
        st.markdown("---")
        
        for approach, result in st.session_state.responses.items():
            approach_name = approach.replace('_', ' ').upper()
            
            # Create answer card with equal height
            with st.container(border=True):
                st.markdown(f"### {approach_name}")
                
                # Answer with max height for scrolling
                col_answer = st.columns(1)[0]
                with col_answer:
                    st.markdown(f"""
                    <div style="max-height: 300px; overflow-y: auto; padding: 1rem; background-color: rgba(15, 23, 42, 0.5); border-radius: 8px;">
                    {result['answer']}
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("")  # Spacing
                
                # Metrics in clean columns
                metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                
                with metric_col1:
                    st.metric("⏱️ Latency", f"{result['latency']:.2f}s")
                with metric_col2:
                    st.metric("📥 Input Tokens", f"{result['input_tokens']}")
                with metric_col3:
                    st.metric("📤 Output Tokens", f"{result['output_tokens']}")
                with metric_col4:
                    st.metric("💰 Cost", f"${result['cost']:.6f}")
                
                if result['sources']:
                    st.caption(f"📖 **Sources:** {', '.join(result['sources'])}")
        
        # Benchmark Report for Single Query Mode
        if len(st.session_state.responses) >= 2:
            st.markdown("---")
            if st.button("📊 Generate Benchmark Report for Selected Queries"):
                st.subheader("📊 Benchmark Report")
                with st.spinner("Generating comprehensive evaluation..."):
                    benchmark_report = generate_benchmark_report(st.session_state.responses, query)
                
                # Tokens & Cost
                st.markdown("#### 📈 Token Usage & Cost")
                token_data = []
                for approach_name, metrics in benchmark_report['approaches'].items():
                    token_data.append({
                        'Approach': approach_name,
                        'Input Tokens': metrics['input_tokens'],
                        'Output Tokens': metrics['output_tokens'],
                        'Total Tokens': metrics['total_tokens'],
                        'Cost': f"${metrics['cost_usd']:.6f}"
                    })
                st.dataframe(token_data, use_container_width=True, hide_index=True)
                
                # BERTScore
                st.markdown("#### 🎯 Semantic Relevance (BERTScore)")
                bertscore_data = []
                for approach_name, metrics in benchmark_report['approaches'].items():
                    bs = metrics['bertscore']
                    bertscore_data.append({
                        'Approach': approach_name,
                        'Precision': f"{bs['precision']:.4f}",
                        'Recall': f"{bs['recall']:.4f}",
                        'F1 Score': f"{bs['f1']:.4f}"
                    })
                st.dataframe(bertscore_data, use_container_width=True, hide_index=True)
                
                # LLM Judge
                st.markdown("#### 🤖 Expert Evaluation (LLM Judge)")
                for approach_name, metrics in benchmark_report['approaches'].items():
                    with st.expander(f"{approach_name}"):
                        st.write(metrics.get('llm_judge', 'No evaluation'))

else:  # Batch Comparison
    st.subheader("⚡ Batch Comparison Mode", divider="green")
    
    query = st.text_area(
        "Enter your question:",
        placeholder="Ask about GraphRAG, RAG, embeddings, or knowledge graphs...",
        height=100,
        key="batch_query",
        label_visibility="collapsed"
    )
    
    if st.button("🚀 Run All Pipelines", use_container_width=True):
        if query.strip():
            col1, col2, col3 = st.columns(3)
            
            with col1:
                with st.spinner("Running LLM-only..."):
                    st.session_state.responses['llm_only'] = llm_only_pipeline(query)
            
            with col2:
                with st.spinner("Running Basic RAG..."):
                    st.session_state.responses['basic_rag'] = basic_rag_pipeline(query)
            
            with col3:
                with st.spinner("Running GraphRAG..."):
                    st.session_state.responses['graphrag'] = graphrag_pipeline(query)
            
            st.success("✅ All pipelines completed!")
    
    # Comparison metrics - 3 column layout
    if st.session_state.responses and len(st.session_state.responses) == 3:
        st.markdown("---")
        st.subheader("📊 Performance Comparison")
        
        # Create 3-column layout for comparison cards
        col1, col2, col3 = st.columns(3, gap="medium")
        
        approaches = {
            'llm_only': ('🤖 LLM Only', col1),
            'basic_rag': ('📚 Basic RAG', col2),
            'graphrag': ('🕸️ GraphRAG', col3)
        }
        
        for key, (label, col) in approaches.items():
            result = st.session_state.responses[key]
            
            with col:
                with st.container(border=True):
                    st.markdown(f"**{label}**")
                    
                    # Answer with scrollable container
                    st.markdown(f"""
                    <div style="max-height: 300px; overflow-y: auto; padding: 1rem; background-color: rgba(15, 23, 42, 0.5); border-radius: 8px; margin-bottom: 1rem;">
                    {result['answer']}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Metrics
                    st.metric("⏱️ Latency", f"{result['latency']:.2f}s")
                    st.metric("💰 Cost", f"${result['cost']:.6f}")
                    st.metric("📊 Total Tokens", f"{result['total_tokens']}")
                    
                    if result['sources']:
                        st.caption(f"📖 **Sources:** {', '.join(result['sources'])}")
        
        # Detailed comparison table
        st.markdown("---")
        st.subheader("📈 Detailed Metrics Comparison")
        
        metrics_data = []
        for approach, result in st.session_state.responses.items():
            metrics_data.append({
                'Approach': approach.replace('_', ' ').upper(),
                'Latency (s)': round(result['latency'], 3),
                'Input Tokens': result['input_tokens'],
                'Output Tokens': result['output_tokens'],
                'Total Tokens': result['total_tokens'],
                'Cost ($)': f"${result['cost']:.6f}"
            })
        
        st.dataframe(
            metrics_data,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Latency (s)": st.column_config.NumberColumn(format="%.3f"),
                "Cost ($)": st.column_config.TextColumn()
            }
        )

        # Advanced Benchmark Report
        st.markdown("---")
        st.subheader("🏆 Comprehensive Benchmark Report")
        
        with st.spinner("Generating benchmark evaluation..."):
            benchmark_report = generate_benchmark_report(st.session_state.responses, query)

        export_rows = []
        for approach_name, metrics in benchmark_report['approaches'].items():
            export_rows.append({
                'Approach': approach_name,
                'Latency (s)': round(metrics['latency'], 3),
                'Input Tokens': metrics['input_tokens'],
                'Output Tokens': metrics['output_tokens'],
                'Total Tokens': metrics['total_tokens'],
                'Cost (USD)': round(metrics['cost_usd'], 6),
                'BERTScore Precision': round(metrics['bertscore']['precision'], 4),
                'BERTScore Recall': round(metrics['bertscore']['recall'], 4),
                'BERTScore F1': round(metrics['bertscore']['f1'], 4),
                'LLM Judge': metrics.get('llm_judge', 'N/A')
            })

        export_df = pd.DataFrame(export_rows)
        export_json = json.dumps(
            {
                'timestamp': benchmark_report.get('timestamp'),
                'query': benchmark_report.get('query'),
                'results': export_rows,
            },
            indent=2,
            ensure_ascii=True,
            default=str,
        )

        dcol1, dcol2 = st.columns(2)
        with dcol1:
            st.download_button(
                label="Download Benchmark CSV",
                data=export_df.to_csv(index=False),
                file_name="benchmark_report.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with dcol2:
            st.download_button(
                label="Download Benchmark JSON",
                data=export_json,
                file_name="benchmark_report.json",
                mime="application/json",
                use_container_width=True,
            )
        
        # Display benchmark metrics tabs
        benchmark_tabs = st.tabs(["📊 Tokens & Cost", "🎯 BERTScore", "🤖 LLM Judge"])
        
        # Tab 1: Tokens & Cost Summary
        with benchmark_tabs[0]:
            st.markdown("#### Token Usage & Cost Analysis")
            
            token_cost_data = []
            for approach_name, metrics in benchmark_report['approaches'].items():
                token_cost_data.append({
                    'Approach': approach_name,
                    'Input Tokens': metrics['input_tokens'],
                    'Output Tokens': metrics['output_tokens'],
                    'Total Tokens': metrics['total_tokens'],
                    'Cost (USD)': f"${metrics['cost_usd']:.6f}",
                    'Cost per 1K Tokens': f"${(metrics['cost_usd'] / max(metrics['total_tokens'], 1) * 1000):.4f}"
                })
            
            st.dataframe(
                token_cost_data,
                use_container_width=True,
                hide_index=True
            )
            
            # Visualization
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Token Distribution**")
                token_viz = pd.DataFrame([
                    {'Approach': a.split()[0], 'Input': metrics['input_tokens'], 'Output': metrics['output_tokens']}
                    for a, metrics in benchmark_report['approaches'].items()
                ])
                st.bar_chart(token_viz.set_index('Approach'))
            
            with col2:
                st.markdown("**Cost Comparison**")
                cost_viz = pd.DataFrame([
                    {'Approach': a.split()[0], 'Cost': metrics['cost_usd']}
                    for a, metrics in benchmark_report['approaches'].items()
                ])
                st.bar_chart(cost_viz.set_index('Approach'))
        
        # Tab 2: BERTScore Evaluation
        with benchmark_tabs[1]:
            st.markdown("#### Semantic Similarity & Relevance (BERTScore)")
            st.info("BERTScore measures semantic similarity between the answer and query using contextual embeddings.")
            
            bertscore_data = []
            for approach_name, metrics in benchmark_report['approaches'].items():
                bs = metrics['bertscore']
                bertscore_data.append({
                    'Approach': approach_name,
                    'Precision': f"{bs['precision']:.4f}",
                    'Recall': f"{bs['recall']:.4f}",
                    'F1 Score': f"{bs['f1']:.4f}"
                })
            
            st.dataframe(
                bertscore_data,
                use_container_width=True,
                hide_index=True
            )
            
            # Visualization
            st.markdown("**BERTScore F1 Comparison**")
            bertscore_viz = pd.DataFrame([
                {'Approach': a.split()[0], 'F1 Score': metrics['bertscore']['f1']}
                for a, metrics in benchmark_report['approaches'].items()
            ])
            st.bar_chart(bertscore_viz.set_index('Approach'))
        
        # Tab 3: LLM-as-a-Judge Evaluation
        with benchmark_tabs[2]:
            st.markdown("#### Expert Evaluation (LLM-as-a-Judge)")
            st.info("Qualitative evaluation using Gemini's judgment of answer quality.")
            
            for approach_name, metrics in benchmark_report['approaches'].items():
                with st.expander(f"**{approach_name}** - Judge Evaluation", expanded=False):
                    judge_eval = metrics.get('llm_judge', 'No evaluation available')
                    st.markdown(judge_eval)
        
        # Summary Statistics
        st.markdown("---")
        st.subheader("📈 Summary Statistics")
        
        summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
        
        # Find best approach for each metric
        approaches_list = list(benchmark_report['approaches'].items())
        
        best_latency = min(approaches_list, key=lambda x: x[1]['latency'])
        best_cost = min(approaches_list, key=lambda x: x[1]['cost_usd'])
        best_bertscore = max(approaches_list, key=lambda x: x[1]['bertscore']['f1'])
        best_tokens = min(approaches_list, key=lambda x: x[1]['total_tokens'])
        
        with summary_col1:
            st.metric("⚡ Fastest", best_latency[0], f"{best_latency[1]['latency']:.3f}s")
        with summary_col2:
            st.metric("💰 Cheapest", best_cost[0], f"${best_cost[1]['cost_usd']:.6f}")
        with summary_col3:
            st.metric("🎯 Best Relevance", best_bertscore[0], f"{best_bertscore[1]['bertscore']['f1']:.4f}")
        with summary_col4:
            st.metric("💾 Least Tokens", best_tokens[0], f"{best_tokens[1]['total_tokens']}")
        

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem 0; color: rgba(226, 232, 240, 0.6);">
    <p style="margin: 0; font-size: 0.95rem;">
        <strong>GraphRAG Performance Studio</strong> | Hackathon Project<br>
        <span style="font-size: 0.85rem;">Powered by Gemini 2.5 Flash | Built with Streamlit</span>
    </p>
</div>
""", unsafe_allow_html=True)
