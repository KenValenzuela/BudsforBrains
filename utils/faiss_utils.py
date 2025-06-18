import os
import pandas as pd
import numpy as np
import faiss
import pickle

# === Paths ===
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(ROOT, "data", "docs_df_with_embeddings.parquet")
VECTOR_STORE_DIR = os.path.join(ROOT, "vector_store")
INDEX_PATH = os.path.join(VECTOR_STORE_DIR, "index.faiss")
MATRIX_PATH = os.path.join(VECTOR_STORE_DIR, "embeddings_matrix.npy")
METADATA_PATH = os.path.join(VECTOR_STORE_DIR, "docs_metadata.pkl")

def generate_leafly_url(name: str) -> str:
    if isinstance(name, str) and name.strip():
        slug = name.strip().lower().replace(" ", "-").replace("'", "")
        return f"https://www.leafly.com/strains/{slug}"
    return "https://www.leafly.com/strains"

def load_faiss_index_safe():
    """Load or rebuild the FAISS index if it fails validation."""
    try:
        index = faiss.read_index(INDEX_PATH)
        return index
    except Exception:
        print("⚠️ FAISS index is missing or corrupted. Rebuilding…")
        return rebuild_faiss_index()

def rebuild_faiss_index():
    """Rebuild index.faiss, embeddings_matrix.npy, and docs_metadata.pkl"""
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError("Missing: docs_df_with_embeddings.parquet")

    df = pd.read_parquet(DATA_PATH)

    if "embedding" not in df.columns:
        raise ValueError("Missing 'embedding' column in input data")

    df = df.dropna(subset=["embedding"])
    if df.empty:
        raise ValueError("No valid embeddings to build FAISS index")

    # Build FAISS index
    embedding_dim = len(df["embedding"].iloc[0])
    embedding_matrix = np.vstack(df["embedding"].tolist()).astype("float32")
    index = faiss.IndexFlatL2(embedding_dim)
    index.add(embedding_matrix)

    os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
    faiss.write_index(index, INDEX_PATH)
    np.save(MATRIX_PATH, embedding_matrix)

    # Save metadata
    required = ["strain_id", "strain_name", "chunk", "effects", "dominant_terpene"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing metadata columns: {missing}")

    meta_df = df[required].copy()
    meta_df["leafly_url"] = meta_df["strain_name"].apply(generate_leafly_url)
    meta_df.rename(columns={"chunk": "content"}, inplace=True)
    meta_df.dropna(subset=["content"], inplace=True)
    metadata = meta_df.to_dict(orient="records")
    with open(METADATA_PATH, "wb") as f:
        pickle.dump(metadata, f)

    print(f"✅ Rebuilt FAISS index with {index.ntotal:,} vectors (dim={embedding_dim})")
    return index
