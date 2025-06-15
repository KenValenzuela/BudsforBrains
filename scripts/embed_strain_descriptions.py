"""
Embed cleaned strain descriptions into OpenAI vectors and save a
flat parquet file ready for FAISS indexing.

Input:
    data/cleaned_strains.parquet
Output:
    data/docs_df_with_embeddings.parquet
"""

import os
import pandas as pd
from tqdm import tqdm
import nltk
from nltk.tokenize import sent_tokenize
from openai import OpenAI
from dotenv import load_dotenv

# === Config ===
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CLEANED_PATH = os.path.join(ROOT_DIR, "data", "cleaned_strains.parquet")
EMB_PATH = os.path.join(ROOT_DIR, "data", "docs_df_with_embeddings.parquet")
CHUNK_SIZE = 2
EMBED_MODEL = "text-embedding-3-small"

# === Setup ===
nltk.download("punkt", quiet=True)
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
tqdm.pandas()

# === Helpers ===
def chunk_sentences(text: str, k: int = CHUNK_SIZE) -> list[str]:
    """Chunk text into groups of k sentences."""
    if not isinstance(text, str) or not text.strip():
        return []
    sents = sent_tokenize(text)
    return [" ".join(sents[i:i + k]) for i in range(0, len(sents), k)]

def embed(text: str) -> list[float] | None:
    try:
        response = client.embeddings.create(input=[text], model=EMBED_MODEL)
        return response.data[0].embedding
    except Exception as e:
        print("❌ Embedding error:", e)
        return None

# === Main ===
def main():
    print(f"🔍 Loading cleaned strain data from {CLEANED_PATH} …")
    if not os.path.exists(CLEANED_PATH):
        raise FileNotFoundError(f"Missing file: {CLEANED_PATH}")
    df = pd.read_parquet(CLEANED_PATH)

    if "strain_name" not in df.columns or "aggressive_cleaned_description" not in df.columns:
        raise KeyError("❌ Required columns 'strain_name' or 'aggressive_cleaned_description' missing.")

    df["aggressive_cleaned_description"] = df["aggressive_cleaned_description"].fillna("").astype(str)
    df["chunks"] = df["aggressive_cleaned_description"].progress_apply(chunk_sentences)

    print("📎 Flattening chunks …")
    records = []
    for sid, (name, chunks) in enumerate(zip(df["strain_name"], df["chunks"])):
        for idx, chunk in enumerate(chunks):
            if chunk.strip():
                records.append({
                    "strain_id": sid,
                    "strain_name": name,
                    "chunk_index": idx,
                    "chunk": chunk
                })

    if not records:
        raise ValueError("⚠️ No valid chunks generated.")

    docs = pd.DataFrame(records)
    print(f"📄 Prepared {len(docs):,} chunks for embedding.")

    if os.path.exists(EMB_PATH):
        old = pd.read_parquet(EMB_PATH)
        required_cols = {"strain_name", "chunk_index", "embedding"}
        if not required_cols.issubset(old.columns):
            print("⚠️ Corrupt existing file. Rebuilding from scratch.")
            os.remove(EMB_PATH)
            old = None
    else:
        old = None

    if old is not None:
        docs = docs.merge(
            old[["strain_name", "chunk_index", "embedding"]],
            on=["strain_name", "chunk_index"],
            how="left"
        )
    else:
        docs["embedding"] = None

    to_embed_mask = docs["embedding"].isna()
    to_embed_ct = to_embed_mask.sum()
    print(f"➡️ Chunks to embed: {to_embed_ct:,}")

    if to_embed_ct > 0:
        docs.loc[to_embed_mask, "embedding"] = docs.loc[to_embed_mask, "chunk"].progress_apply(embed)

    docs.dropna(subset=["embedding"], inplace=True)
    docs.to_parquet(EMB_PATH, index=False)
    print(f"✅ Saved {len(docs):,} embedded chunks → {EMB_PATH}")

if __name__ == "__main__":
    main()
