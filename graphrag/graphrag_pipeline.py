from dotenv import load_dotenv
import os
import time
import networkx as nx
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

# Gemini model
model = genai.GenerativeModel(
    "models/gemini-2.5-flash"
)

# -----------------------------
# KNOWLEDGE GRAPH DATA
# -----------------------------

graph_data = {

    "GraphRAG":
    "GraphRAG extends Retrieval Augmented Generation using knowledge graphs and connected entities.",

    "RAG":
    "RAG retrieves relevant external information before LLM generation.",

    "Embeddings":
    "Embeddings convert text into numerical vectors for semantic search.",

    "ChromaDB":
    "ChromaDB stores vector embeddings for retrieval.",

    "LLM":
    "Large Language Models generate human-like responses.",

    "Transformers":
    "Transformers use attention mechanisms for language understanding.",

    "Knowledge Graph":
    "Knowledge graphs store entities and relationships.",

    "Entities":
    "Entities are important concepts extracted from documents.",

    "Attention":
    "Attention helps transformers focus on important words in text.",

    "Semantic Search":
    "Semantic search finds meaning-based similarities instead of keyword matching."
}

# -----------------------------
# CREATE GRAPH
# -----------------------------

G = nx.Graph()

# Add relationships
G.add_edge("GraphRAG", "RAG")

G.add_edge("RAG", "Embeddings")

G.add_edge("Embeddings", "ChromaDB")

G.add_edge("GraphRAG", "Knowledge Graph")

G.add_edge("Knowledge Graph", "Entities")

G.add_edge("Transformers", "Attention")

G.add_edge("Transformers", "LLM")

G.add_edge("Embeddings", "Semantic Search")

# -----------------------------
# USER QUESTION
# -----------------------------

query = input("Ask a question: ")

# Prevent empty query
if not query.strip():

    print("Please enter a valid question.")

    exit()

# -----------------------------
# GRAPH RETRIEVAL
# -----------------------------

related_nodes = []

# Find matching nodes
for node in G.nodes():

    if node.lower() in query.lower():

        related_nodes.append(node)

        # Add neighboring nodes
        neighbors = list(G.neighbors(node))

        related_nodes.extend(neighbors)

# Remove duplicates
related_nodes = list(set(related_nodes))

# -----------------------------
# BUILD GRAPH CONTEXT
# -----------------------------

context = ""

for node in related_nodes:

    if node in graph_data:

        context += graph_data[node] + "\n"

# Print graph context
print("\nGraph Context:\n")

print(context)

# -----------------------------
# FINAL PROMPT
# -----------------------------

prompt = f"""
Answer the question using the graph context below.

Graph Context:
{context}

Question:
{query}
"""

# -----------------------------
# METRICS
# -----------------------------

# Approx token count
token_count = len(prompt.split())

# Start timer
start = time.time()

# Gemini response
response = model.generate_content(prompt)

# End timer
end = time.time()

# Calculate latency
latency = end - start

# Estimated cost
cost = token_count * 0.000001

# -----------------------------
# FINAL OUTPUT
# -----------------------------

print("\nAnswer:\n")

print(response.text)

print("\nMetrics:\n")

print("Tokens:", token_count)

print("Latency:", latency)

print("Estimated Cost:", cost)