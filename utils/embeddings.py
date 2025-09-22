# utils/embeddings.py
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

def get_embeddings(texts):
    """
    Accepts a list of strings, returns a list of embedding vectors.
    Uses Google's text-embedding-004 model.
    """
    if isinstance(texts, str):
        texts = [texts]

    # Use Google's embedding model
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=texts,
        task_type="retrieval_document"
    )
    
    # Handle different response formats
    if 'embedding' in result:
        embedding_data = result['embedding']
        # Check if it's a nested list (list of lists)
        if isinstance(embedding_data, list) and len(embedding_data) > 0 and isinstance(embedding_data[0], list):
            return embedding_data
        else:
            return [embedding_data] if len(texts) == 1 else embedding_data
    elif 'embeddings' in result:
        return result['embeddings']
    else:
        raise ValueError(f"Unexpected response format from Google embeddings API: {result}")
