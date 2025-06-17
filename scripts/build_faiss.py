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
    if isinstance(name, str):
        slug = name.strip().lower().replace(" ", "-").replace("'", "")
        return f"https://www.leafly.com/strains/{slug}"
    return "https://www.leafly.com/strains"

# === Load and Validate Data ===
print(f"📂 Loading embedded data from: {DATA_PATH}")
if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"❌ Missing file: {DATA_PATH}")

df = pd.read_parquet(DATA_PATH)

if "embedding" not in df.columns:
    raise ValueError("❌ Missing required column: 'embedding'")

df = df.dropna(subset=["embedding"])
if df.empty:
    raise ValueError("❌ No valid embeddings found to index.")

# === Build FAISS Index ===
print("⚙️ Building FAISS index …")
embedding_dim = len(df["embedding"].iloc[0])
embeddings_matrix = np.vstack(df["embedding"]).astype("float32")

index = faiss.IndexFlatL2(embedding_dim)
index.add(embeddings_matrix)

# === Save Vector Index and Matrix ===
os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
faiss.write_index(index, INDEX_PATH)
np.save(MATRIX_PATH, embeddings_matrix)

print(f"✅ FAISS index built with {index.ntotal:,} vectors (dim={embedding_dim})")

# === Create Metadata Store ===
print("🧠 Generating metadata …")
metadata = df[["strain_id", "strain_name", "chunk", "effects", "dominant_terpene"]].copy()
metadata["leafly_url"] = metadata["strain_name"].apply(generate_leafly_url)
metadata.rename(columns={"chunk": "content"}, inplace=True)

# Optionally drop any null/empty content
metadata.dropna(subset=["content"], inplace=True)
metadata = metadata.to_dict(orient="records")

# === Save Metadata ===
pd.to_pickle(metadata, METADATA_PATH)

print(f"📦 Saved FAISS index → {INDEX_PATH}")
print(f"📦 Saved matrix → {MATRIX_PATH}")
print(f"📦 Saved metadata → {METADATA_PATH}")
