import os
from functools import lru_cache
import faiss, numpy as np
from dotenv import load_dotenv
from openai import OpenAI
import pandas as pd

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INDEX_PATH     = os.path.join(ROOT, "vector_store", "index.faiss")
METADATA_PATH  = os.path.join(ROOT, "vector_store", "docs_metadata.pkl")

def get_embedding(text: str,
                  model: str = "text-embedding-3-small") -> np.ndarray:
    resp = client.embeddings.create(input=[text], model=model)
    return np.asarray(resp.data[0].embedding, dtype=np.float32)

@lru_cache
def load_faiss() -> faiss.Index:
    return faiss.read_index(INDEX_PATH)

@lru_cache
def load_metadata() -> pd.DataFrame:
    return pd.read_pickle(METADATA_PATH)
