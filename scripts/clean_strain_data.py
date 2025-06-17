"""
Clean raw Leafly CSV → parquet + XGBoost terpene-imputer
-------------------------------------------------------

1. Fix garbled strain names (keeps apostrophes/dashes)
2. Strip invisible Unicode + bad bytes from descriptions
3. Drop rows with < 40 chars of usable description
4. Normalise THC/CBD columns
5. Train / save XGBoost model to impute dominant terpene
6. Export cleaned parquet  +   model / label-encoder pickles
"""

import os, re, html, unicodedata, joblib
import pandas as pd
import numpy  as np
import xgboost as xgb
from bs4 import BeautifulSoup
from sklearn.model_selection import train_test_split
from sklearn.preprocessing  import LabelEncoder

# ------------------------------------------------------------------#
# Paths
# ------------------------------------------------------------------#
ROOT_DIR   = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
INPUT_CSV  = os.path.join(ROOT_DIR, "leafly_strain_data_project.csv")
OUTPUT_PAR = os.path.join(ROOT_DIR, "cleaned_strains.parquet")
MODEL_DIR  = os.path.join(ROOT_DIR, "models")

os.makedirs(MODEL_DIR, exist_ok=True)

# ------------------------------------------------------------------#
# Helpers
# ------------------------------------------------------------------#
BAD_REPLACEMENTS = {
    "â€™": "'", "â€’": "-", "â€“": "-", "â€”": "-", "Ã©": "e",
    "Ã": "A",  "�": "",  "“": '"', "”": '"'
}

INVISIBLE_SPACE_RE = re.compile(r"[\u00A0\u200B\u200C\u200D\u202F\u2060]+")

def fix_strain_name(text: str) -> str:
    if not isinstance(text, str):
        return "unknown"
    text = html.unescape(text)
    text = BeautifulSoup(text, "html.parser").get_text()
    text = unicodedata.normalize("NFKC", text)
    for bad, good in BAD_REPLACEMENTS.items():
        text = text.replace(bad, good)
    return re.sub(r"\s+", " ", text).strip()

def clean_description(text: str) -> str:
    """Remove HTML, invisible bytes/spaces, keep punctuation & case."""
    if not isinstance(text, str):
        return ""
    text = html.unescape(text)
    text = BeautifulSoup(text, "html.parser").get_text(separator=" ")
    text = unicodedata.normalize("NFKC", text)

    # remove stray high-bit bytes while keeping ASCII punctuations
    text = text.encode("ascii", "ignore").decode("ascii")
    text = INVISIBLE_SPACE_RE.sub(" ", text)          # kill nbsp / zero-width
    return re.sub(r"\s+", " ", text).strip()

def pct_to_float(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
              .str.replace("%", "", regex=False)
              .replace("", np.nan)
              .astype(float)
              .fillna(0.0)
    )

# ------------------------------------------------------------------#
# 1. Load raw CSV
# ------------------------------------------------------------------#
print(f"🔍 Loading → {INPUT_CSV}")
df = pd.read_csv(INPUT_CSV)

# ------------------------------------------------------------------#
# 2. Basic column housekeeping
# ------------------------------------------------------------------#
df.drop(columns=["img_url", "strain_url"], errors="ignore", inplace=True)

if "strain_name" not in df.columns:
    df["strain_name"] = df.get("name", pd.Series([f"strain_{i}" for i in range(len(df))]))

df["strain_name"] = df["strain_name"].apply(fix_strain_name)

# ------------------------------------------------------------------#
# 3. Clean & filter descriptions
# ------------------------------------------------------------------#
df["aggressive_cleaned_description"] = df["description"].apply(clean_description)
before = len(df)
df = df[df["aggressive_cleaned_description"].str.len() > 40]   # keep only useful rows
print(f"🧹 Dropped {before - len(df):,} rows with empty/short descriptions")

# ------------------------------------------------------------------#
# 4. Numeric columns
# ------------------------------------------------------------------#
df["thc"] = pct_to_float(df["thc_level"].astype(str).str.extract(r"(\d+\.?\d*)")[0])
if "cbd" in df.columns:
    df["cbd"] = pd.to_numeric(df["cbd"], errors="coerce").fillna(0.0)
else:
    df["cbd"] = 0.0

# ------------------------------------------------------------------#
# 5. Dominant terpene column
# ------------------------------------------------------------------#
terp_col = "most_common_terpene" if "most_common_terpene" in df.columns else "dominant_terpene"
df["dominant_terpene"] = (
    df.get(terp_col, "unknown")
      .astype(str).str.lower()
      .str.replace("\u03b2-", "beta-", regex=False)
      .fillna("unknown")
)

# ------------------------------------------------------------------#
# 6. Build training set for terpene imputation
# ------------------------------------------------------------------#
train_df = df[df["dominant_terpene"] != "unknown"].copy()
top_terps = train_df["dominant_terpene"].value_counts()
train_df  = train_df[train_df["dominant_terpene"].isin(top_terps[top_terps >= 10].index)]

skip = {
    "name", "strain_name", "description", "thc_level",
    "dominant_terpene", "most_common_terpene",
    "aggressive_cleaned_description", "thc", "cbd"
}
effect_cols = []
for col in train_df.columns.difference(skip):
    try:
        train_df[col] = pct_to_float(train_df[col])
        effect_cols.append(col)
    except Exception:
        continue

# ------------------------------------------------------------------#
# 7. Train XGBoost model
# ------------------------------------------------------------------#
if effect_cols:
    X     = train_df[effect_cols + ["thc", "cbd"]].astype(np.float32)
    y     = train_df["dominant_terpene"]
    le    = LabelEncoder().fit(y)
    y_enc = le.transform(y)

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y_enc, stratify=y_enc, test_size=0.2, random_state=42
    )

    model = xgb.XGBClassifier(
        eval_metric="mlogloss",
        max_depth=6,
        n_estimators=300,
        learning_rate=0.15,
        subsample=0.8,
        random_state=42
    )
    model.fit(X_tr, y_tr)

    # ------------------------------------------------------------------#
    # 8. Impute missing terpenes
    # ------------------------------------------------------------------#
    for c in effect_cols:
        df[c] = pct_to_float(df.get(c, 0.0))

    X_all = df[effect_cols + ["thc", "cbd"]].astype(np.float32)
    df["dominant_terpene"] = le.inverse_transform(model.predict(X_all))

    # Save model artefacts
    joblib.dump(model, os.path.join(MODEL_DIR, "xgb_terpene_predictor.pkl"))
    joblib.dump(le,    os.path.join(MODEL_DIR, "terpene_label_encoder.pkl"))
    print("💾 XGBoost model + label encoder saved.")
else:
    print("⚠️ No effect columns found — terpene imputation skipped.")

# ------------------------------------------------------------------#
# 9. Save cleaned parquet
# ------------------------------------------------------------------#
df.to_parquet(OUTPUT_PAR, index=False)
print(f"✅ Cleaned dataset saved → {OUTPUT_PAR}  ({len(df):,} rows)")
