import os
from pypdf import PdfReader

DATA_PATH = "data"

total_words = 0

for file in os.listdir(DATA_PATH):

    if file.endswith(".pdf"):

        pdf_path = os.path.join(DATA_PATH, file)

        reader = PdfReader(pdf_path)

        text = ""

        for page in reader.pages:

            text += page.extract_text() or ""

        words = len(text.split())

        total_words += words

        print(f"{file}: {words} words")

# Approximate tokens
total_tokens = total_words * 1.3

print("\nTotal Words:", total_words)

print("Approx Tokens:", int(total_tokens))