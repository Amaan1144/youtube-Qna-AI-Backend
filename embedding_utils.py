import os
import uuid
import google.generativeai as genai
from pinecone import Pinecone
import textwrap
from typing import List, Dict, Any
from pinecone import QueryResponse 
from dotenv import load_dotenv

load_dotenv()

# Load env variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not PINECONE_API_KEY:
  raise ValueError("PINECONE_API_KEY is not set in environment variables.")
if not PINECONE_INDEX:
  raise ValueError("PINECONE_INDEX is not set in environment variables.")
if not GOOGLE_API_KEY:
  raise ValueError("GOOGLE_API_KEY is not set in environment variables.")

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# Create Pinecone instance
pc = Pinecone(api_key=PINECONE_API_KEY)

# Access existing index
index = pc.Index(PINECONE_INDEX)


# === Function to generate embeddings using Gemini ===
def get_gemini_embedding(text: str) -> list:
  # Use the embed_content function instead
  result = genai.embed_content(
      model="models/embedding-001",
      content=text,
      task_type="retrieval_document"  # Use "retrieval_query" for queries
  )
  return result["embedding"]


# === Split transcript into chunks ===
def chunk_text(text, chunk_size=500, overlap=50):
  chunks = []
  words = text.split()
  i = 0
  while i < len(words):
    chunk = ' '.join(words[i:i + chunk_size])
    chunks.append(chunk)
    i += chunk_size - overlap
  return chunks


# === Store transcript in Pinecone ===
def store_transcript(title, transcript):
  doc_id = str(uuid.uuid4())

  # Chunk the transcript for better retrieval
  chunks = chunk_text(transcript)

  # Upsert each chunk with metadata
  for i, chunk in enumerate(chunks):
    chunk_id = f"{doc_id}_{i}"
    embedding = get_gemini_embedding(chunk)
    metadata = {
        "title": title,
        "doc_id": doc_id,
        "chunk_id": chunk_id,
        "content": chunk,
        "chunk_index": i
    }
    index.upsert(vectors=[{
        "id": chunk_id,
        "values": embedding,
        "metadata": metadata
    }])

  return doc_id


# === Answer question based on video ===
def answer_question(question: str, doc_id: str) -> str:
  try:
      # 1. Get embedding for the question
      query_embedding = genai.embed_content(
          model='models/embedding-001',
          content=question,
          task_type="retrieval_query"
      )["embedding"]

      # 2. Query Pinecone
      results = index.query(
          vector=query_embedding,
          top_k=5,
          include_metadata=True
      )

      # 3. Process results
      contexts = [
          match['metadata']['content']
          for match in results['matches']
          if match['metadata']['doc_id'] == doc_id
      ]

      if not contexts:
          return "No relevant information found."

      # 4. Generate response using gemini-2.0-flash
      model = genai.GenerativeModel('gemini-2.0-flash')

      prompt = f"""Analyze this context and answer the question:

      Context:
      {' '.join(contexts)}

      Question: {question}

      Provide a concise and accurate answer:"""

      response = model.generate_content(prompt)
      return response.text

  except Exception as e:
      return f"Error: {str(e)}"