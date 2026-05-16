"""
GraphRAG Hackathon - LLM Only Pipeline (No Dependencies)
Standalone script to test LLM-only approach without Streamlit
"""

import os
import time
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Gemini pricing
PRICING = {
    "input": 0.075,      # $0.075 per 1M input tokens
    "output": 0.30       # $0.30 per 1M output tokens
}

def estimate_tokens(text):
    """Rough token estimation"""
    return max(1, len(text) // 4)

def calculate_cost(input_tokens, output_tokens):
    """Calculate estimated cost"""
    input_cost = (input_tokens / 1_000_000) * PRICING["input"]
    output_cost = (output_tokens / 1_000_000) * PRICING["output"]
    return input_cost + output_cost

def llm_only_pipeline(query):
    """Direct LLM response without any context"""
    model = genai.GenerativeModel("models/gemini-2.5-flash")
    
    print(f"\n{'='*60}")
    print(f"🤖 LLM-Only Pipeline")
    print(f"{'='*60}")
    print(f"Query: {query}\n")
    
    start_time = time.time()
    response = model.generate_content(query)
    answer = response.text
    latency = time.time() - start_time
    
    input_tokens = estimate_tokens(query)
    output_tokens = estimate_tokens(answer)
    cost = calculate_cost(input_tokens, output_tokens)
    
    print(f"Answer:\n{answer}\n")
    print(f"{'='*60}")
    print(f"📊 Metrics:")
    print(f"  Input Tokens:  {input_tokens}")
    print(f"  Output Tokens: {output_tokens}")
    print(f"  Total Tokens:  {input_tokens + output_tokens}")
    print(f"  Latency:       {latency:.2f}s")
    print(f"  Cost:          ${cost:.6f}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    # Example queries
    queries = [
        "Explain RAG in one sentence",
        "What is GraphRAG?",
        "How do embeddings work?"
    ]
    
    print("\n" + "="*60)
    print("GraphRAG Hackathon - LLM Only Demo")
    print("="*60)
    
    for query in queries:
        llm_only_pipeline(query)
        time.sleep(1)  # Be nice to the API
