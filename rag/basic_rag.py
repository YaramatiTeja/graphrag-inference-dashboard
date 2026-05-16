from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb
import os

# PDF folder path
DATA_PATH = "data"

# Load embedding model
embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

# Persistent ChromaDB
client = chromadb.PersistentClient(
    path="chroma_db"
)

# Delete old collection if exists
try:
    client.delete_collection("pdf_notes")
except:
    pass

# Create collection
collection = client.create_collection(
    name="pdf_notes"
)

documents = []

# Load all PDFs
for file in os.listdir(DATA_PATH):

    if file.endswith(".pdf"):

        pdf_path = os.path.join(DATA_PATH, file)

        loader = PyPDFLoader(pdf_path)

        docs = loader.load()

        documents.extend(docs)

print(f"Loaded {len(documents)} pages")

# Split into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)

chunks = text_splitter.split_documents(documents)

print(f"Created {len(chunks)} chunks")

# Store embeddings
for i, chunk in enumerate(chunks):

    embedding = embedding_model.encode(
        chunk.page_content
    ).tolist()

    collection.add(
        documents=[chunk.page_content],
        embeddings=[embedding],
        ids=[str(i)]
    )

print("PDF embeddings stored successfully!")