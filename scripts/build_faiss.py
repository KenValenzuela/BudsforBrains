"""
Build FAISS index from embedded strain chunks and store metadata.

Input:
    data/docs_df_with_embeddings.parquet
Output:
    vector_store/index.faiss
    vector_store/embeddings_matrix.npy
    vector_store/docs_metadata.pkl
"""

import os
import pandas as pd
import numpy as np
import faiss

# === Paths ===
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(ROOT_DIR, "data", "docs_df_with_embeddings.parquet")
VECTOR_STORE_DIR = os.path.join(ROOT_DIR, "vector_store")
INDEX_PATH = os.path.join(VECTOR_STORE_DIR, "index.faiss")
MATRIX_PATH = os.path.join(VECTOR_STORE_DIR, "embeddings_matrix.npy")
METADATA_PATH = os.path.join(VECTOR_STORE_DIR, "docs_metadata.pkl")

# === Utilities ===
def generate_leafly_url(name):
    if isinstance(name, str):
        slug = name.strip().lower().replace(" ", "-").replace("'", "")
        return f"https://www.leafly.com/strains/{slug}"
    return None

def row_to_metadata(row):
    return {
        "strain_id": row.get("strain_id"),
        "strain_name": row.get("strain_name"),
        "content": row.get("chunk"),
        "effects": row.get("effects", None),
        "dominant_terpene": row.get("dominant_terpene", "unknown"),
        "leafly_url": generate_leafly_url(row.get("strain_name")),
    }

# === Load embedded data ===
print(f"📂 Loading embedded data from {DATA_PATH}")
if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"Missing required file: {DATA_PATH}")

df = pd.read_parquet(DATA_PATH)

if "embedding" not in df.columns:
    raise ValueError("Missing 'embedding' column in data.")

df = df.dropna(subset=["embedding"])
if df.empty:
    raise ValueError("❌ No embeddings found to index.")

# === Build FAISS index ===
print("⚙️ Building FAISS index …")
embedding_dim = len(df["embedding"].iloc[0])
embeddings_matrix = np.vstack(df["embedding"]).astype("float32")

index = faiss.IndexFlatL2(embedding_dim)
index.add(embeddings_matrix)

# === Save index and matrix ===
os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
faiss.write_index(index, INDEX_PATH)
np.save(MATRIX_PATH, embeddings_matrix)

# === Build and save metadata ===
print("🧠 Generating metadata …")
metadata = df.apply(row_to_metadata, axis=1).tolist()
pd.to_pickle(metadata, METADATA_PATH)

# === Done ===
print(f"✅ FAISS index built with {index.ntotal:,} vectors (dim={embedding_dim})")
print(f"📦 Saved → {INDEX_PATH}")
print(f"📦 Saved → {MATRIX_PATH}")
print(f"📦 Saved → {METADATA_PATH}")
