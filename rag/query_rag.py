from dotenv import load_dotenv
import os
import chromadb
import google.generativeai as genai

from sentence_transformers import SentenceTransformer

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

# Embedding model
embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

# Connect to ChromaDB
client = chromadb.PersistentClient(
    path = "chroma_db"
)

collection = client.get_collection(
    name="pdf_notes"
)

# User question
query = input("Ask a question: ")

# Convert question into embedding
query_embedding = embedding_model.encode(
    query
).tolist()

# Search similar chunks
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=2
)

# Extract retrieved text
retrieved_docs = results["documents"][0]
context = "\n".join(retrieved_docs)
print("\nRetrieved Chunks:\n")
print(context)

# Create final prompt
prompt = f"""
Answer the question using the context below.

Context:
{context}

Question:
{query}
"""

# Generate answer
response = model.generate_content(prompt)

# Print answer
print("\nAnswer:\n")
print(response.text)