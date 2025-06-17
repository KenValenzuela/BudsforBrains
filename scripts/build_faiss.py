# === scripts/build_faiss.py (Hardened) ===

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

# === URL Utility ===
def generate_leafly_url(name: str) -> str:
    if isinstance(name, str) and name.strip():
        slug = name.strip().lower().replace(" ", "-").replace("'", "")
        return f"https://www.leafly.com/strains/{slug}"
    return "https://www.leafly.com/strains"

# === Load and Validate Data ===
print(f"📂 Loading: {DATA_PATH}")
if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"❌ Missing file: {DATA_PATH}")

df = pd.read_parquet(DATA_PATH)

if "embedding" not in df.columns:
    raise ValueError("❌ 'embedding' column missing. Cannot proceed.")

df = df.dropna(subset=["embedding"])
if df.empty:
    raise ValueError("❌ No rows with valid embeddings.")

# === Build FAISS Index ===
print("⚙️ Building FAISS index …")
embedding_dim = len(df["embedding"].iloc[0])
embedding_matrix = np.vstack(df["embedding"].tolist()).astype("float32")

index = faiss.IndexFlatL2(embedding_dim)
index.add(embedding_matrix)

# === Ensure Output Directory Exists ===
os.makedirs(VECTOR_STORE_DIR, exist_ok=True)

# === Save Artifacts ===
faiss.write_index(index, INDEX_PATH)
np.save(MATRIX_PATH, embedding_matrix)

print(f"✅ FAISS index with {index.ntotal:,} vectors (dim={embedding_dim})")
print(f"📦 Saved: {INDEX_PATH}")
print(f"📦 Saved: {MATRIX_PATH}")

# === Build Metadata ===
print("🧠 Creating metadata …")
required_cols = ["strain_id", "strain_name", "chunk", "effects", "dominant_terpene"]
missing_cols = [c for c in required_cols if c not in df.columns]
if missing_cols:
    raise ValueError(f"❌ Missing metadata columns: {missing_cols}")

metadata_df = df[required_cols].copy()
metadata_df["leafly_url"] = metadata_df["strain_name"].apply(generate_leafly_url)
metadata_df.rename(columns={"chunk": "content"}, inplace=True)
metadata_df.dropna(subset=["content"], inplace=True)

# Convert to list-of-dicts format for Streamlit/JSON usage
metadata = metadata_df.to_dict(orient="records")
pd.to_pickle(metadata, METADATA_PATH)

print(f"📦 Saved: {METADATA_PATH}")
print("✅ All vector and metadata artifacts built successfully.")
