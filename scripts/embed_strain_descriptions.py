"""
Embed cleaned strain descriptions into OpenAI vectors and save a
compressed parquet file ready for FAISS indexing.
"""

import os
import numpy as np
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
    if not isinstance(text, str) or not text.strip():
        return []
    sents = sent_tokenize(text)
    return [" ".join(sents[i:i + k]) for i in range(0, len(sents), k)]

def embed(text: str) -> list[float] | None:
    try:
        response = client.embeddings.create(input=[text], model=EMBED_MODEL)
        return response.data[0].embedding
    except Exception as e:
        print(f"❌ Embedding error for chunk: {text[:30]}… → {e}")
        return None

# === Main ===
def main():
    print(f"🔍 Loading → {CLEANED_PATH}")
    if not os.path.exists(CLEANED_PATH):
        raise FileNotFoundError(f"Missing: {CLEANED_PATH}")

    df = pd.read_parquet(CLEANED_PATH)

    # Ensure required columns exist
    df = df.fillna("")
    df["effects"] = df.get("effects", "")
    df["dominant_terpene"] = df.get("dominant_terpene", "unknown")
    df["chunks"] = df["aggressive_cleaned_description"].progress_apply(chunk_sentences)

    # Flatten
    records = []
    for sid, (name, chunks, effects, terp) in enumerate(zip(df["strain_name"], df["chunks"], df["effects"], df["dominant_terpene"])):
        for idx, chunk in enumerate(chunks):
            if chunk.strip():
                records.append({
                    "strain_id": sid,
                    "strain_name": name,
                    "chunk_index": idx,
                    "chunk": chunk,
                    "effects": effects,
                    "dominant_terpene": terp
                })

    docs = pd.DataFrame(records)
    print(f"📄 {len(docs)} chunks ready for embedding.")

    # Resume from existing
    if os.path.exists(EMB_PATH):
        old = pd.read_parquet(EMB_PATH)
        if {"strain_name", "chunk_index", "embedding"}.issubset(old.columns):
            docs = docs.merge(old[["strain_name", "chunk_index", "embedding"]],
                              on=["strain_name", "chunk_index"], how="left")
        else:
            docs["embedding"] = None
    else:
        docs["embedding"] = None

    # Embed
    to_embed = docs["embedding"].isna()
    print(f"➡️ Embedding {to_embed.sum()} chunks …")
    if to_embed.any():
        docs.loc[to_embed, "embedding"] = docs.loc[to_embed, "chunk"].progress_apply(embed)

    docs.dropna(subset=["embedding"], inplace=True)
    docs["embedding"] = docs["embedding"].apply(lambda x: np.array(x, dtype=np.float32).tolist())
    docs.to_parquet(EMB_PATH, index=False, compression="snappy")
    print(f"✅ Saved → {EMB_PATH} (compressed)")

if __name__ == "__main__":
    main()
