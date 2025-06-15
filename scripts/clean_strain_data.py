import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import os
import joblib
import re
import html
from bs4 import BeautifulSoup

# === Define Paths === #
ROOT = "../data"
INPUT = os.path.join(ROOT, "leafly_strain_data_project.csv")
OUTPUT = os.path.join(ROOT, "cleaned_strains.parquet")
MODEL_DIR = os.path.join(ROOT, "models")

# === Define Cleaning Functions === #
def aggressive_clean_description(text):
    if pd.isna(text):
        return ""
    text = html.unescape(text)
    text = BeautifulSoup(text, "html.parser").get_text()
    text = text.encode("raw_unicode_escape").decode("utf-8", errors="ignore")
    text = re.sub(r"\\u[0-9a-fA-F]{4}", "", text)
    text = re.sub(r"[^\x00-\x7F]+", " ", text)  # Replace broken chars with space
    return re.sub(r"\s+", " ", text).strip().lower()

def clean_percentage_column(series):
    return (
        series.astype(str)
        .str.replace("%", "", regex=False)
        .replace("", "0")
        .fillna("0")
        .astype(float)
    )

# === Load and Prepare Data === #
df = pd.read_csv(INPUT)
df.drop(columns=["img_url", "strain_url"], errors="ignore", inplace=True)

# Ensure unique strain name
if "strain_name" not in df.columns:
    df["strain_name"] = df.get("name", pd.Series([f"strain_{i}" for i in range(len(df))]))

# === Clean Strain Name Encoding Issues === #
df["strain_name"] = df["strain_name"].apply(lambda x: (
    BeautifulSoup(html.unescape(str(x)), "html.parser")
    .get_text()
    .encode("raw_unicode_escape")
    .decode("utf-8", errors="ignore")
    .replace("â€™", "'")
    .replace("â€œ", '"')
    .replace("â€", '"')
    .replace("â€“", "-")
    .replace("Ã", "A")
    .replace("�", "")
    .strip()
))

# === Clean Description Field === #
df["aggressive_cleaned_description"] = df["description"].apply(aggressive_clean_description)

# === Clean THC and CBD === #
df["thc"] = clean_percentage_column(df["thc_level"].astype(str).str.extract(r"(\d+\.?\d*)")[0])
df["cbd"] = pd.to_numeric(df.get("cbd", pd.Series([0.0] * len(df))), errors="coerce").fillna(0.0)

# === Standardize Dominant Terpene Column === #
terp_col = "most_common_terpene" if "most_common_terpene" in df.columns else "dominant_terpene"
df["dominant_terpene"] = (
    df.get(terp_col, pd.Series(["unknown"] * len(df)))
    .astype(str)
    .fillna("unknown")
    .str.replace("β-", "beta-", regex=False)
    .str.lower()
)

# === Prepare Data for Terpene Imputation === #
train_df = df[df["dominant_terpene"] != "unknown"].copy()
counts = train_df["dominant_terpene"].value_counts()
valid_classes = counts[counts >= 10].index
train_df = train_df[train_df["dominant_terpene"].isin(valid_classes)]

skip_cols = {
    "name", "strain_name", "description", "thc_level",
    "dominant_terpene", "most_common_terpene", "aggressive_cleaned_description",
    "thc", "cbd"
}

effect_cols = []
for col in train_df.columns:
    if col not in skip_cols:
        try:
            train_df[col] = clean_percentage_column(train_df[col])
            effect_cols.append(col)
        except Exception:
            continue

# === Train XGBoost Classifier === #
X = train_df[effect_cols + ["thc", "cbd"]].astype(np.float32)
y = train_df["dominant_terpene"]
le = LabelEncoder()
y_enc = le.fit_transform(y)

X_train, X_test, y_train, y_test = train_test_split(
    X, y_enc, stratify=y_enc, test_size=0.2, random_state=42
)

model = xgb.XGBClassifier(eval_metric="mlogloss", random_state=42)
model.fit(X_train, y_train)

# === Impute for Full Dataset === #
for col in effect_cols:
    df[col] = clean_percentage_column(df.get(col, 0.0))

X_all = df[effect_cols + ["thc", "cbd"]].astype(np.float32)
df["dominant_terpene"] = le.inverse_transform(model.predict(X_all))

# === Save Cleaned Data and Models === #
os.makedirs(MODEL_DIR, exist_ok=True)
joblib.dump(model, os.path.join(MODEL_DIR, "xgb_terpene_predictor.pkl"))
joblib.dump(le, os.path.join(MODEL_DIR, "terpene_label_encoder.pkl"))
df.to_parquet(OUTPUT, index=False)

print(f"✅ Saved cleaned dataset to: {OUTPUT}")
