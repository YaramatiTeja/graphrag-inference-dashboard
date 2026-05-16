from dotenv import load_dotenv
import os
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Select model
model = genai.GenerativeModel("models/gemini-2.5-flash")

# Generate response
response = model.generate_content(
    "Explain RAG and GraphRAG in very simple words"
)

# Print output
print(response.text)