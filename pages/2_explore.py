import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Strain Explorer", page_icon="🔬")

# === Path Setup ===
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(ROOT_DIR, "data", "cleaned_strains.parquet")

@st.cache_data
def load_strain_data():
    df = pd.read_parquet(DATA_PATH)

    # Select key effects for top-level summary
    effect_cols = [
        'relaxed', 'happy', 'euphoric', 'uplifted', 'sleepy', 'creative',
        'energetic', 'focused', 'giggly', 'aroused', 'talkative', 'tingly'
    ]
    def extract_top_effects(row):
        effects = [(col, float(row[col])) for col in effect_cols if col in row and float(row[col]) > 0.0]
        effects = sorted(effects, key=lambda x: x[1], reverse=True)[:5]
        return ", ".join([f"{e[0].capitalize()} ({e[1]}%)" for e in effects])

    df["effects"] = df.apply(extract_top_effects, axis=1)
    df["thc"] = df["thc"].astype(str) + "%"
    df["cbd"] = df["cbd"].astype(str) + "%"

    return df

df = load_strain_data()

# === UI Layout ===
st.title("🔬 Strain Explorer")
st.caption("Browse and filter strains by type, terpene, and top effects.")

# === Filter Options ===
types = sorted(df["type"].dropna().unique())
terpenes = sorted(df["dominant_terpene"].dropna().unique())
effect_keywords = sorted({e.split(" ")[0] for entry in df["effects"] for e in entry.split(", ")})

selected_type = st.selectbox("Filter by Strain Type", ["All"] + types)
selected_terp = st.selectbox("Filter by Dominant Terpene", ["All"] + terpenes)
selected_effect = st.selectbox("Filter by Effect", ["None"] + effect_keywords)

# === Apply Filters ===
filtered_df = df.copy()

if selected_type != "All":
    filtered_df = filtered_df[filtered_df["type"] == selected_type]

if selected_terp != "All":
    filtered_df = filtered_df[filtered_df["dominant_terpene"] == selected_terp]

if selected_effect != "None":
    filtered_df = filtered_df[filtered_df["effects"].str.contains(selected_effect, case=False)]

# === Display ===
st.markdown(f"#### Showing {len(filtered_df)} matching strains:")
st.dataframe(
    filtered_df[[
        "strain_name", "type", "dominant_terpene", "thc", "cbd", "effects", "aggressive_cleaned_description"
    ]].rename(columns={
        "aggressive_cleaned_description": "description"
    }).reset_index(drop=True),
    use_container_width=True
)

st.download_button(
    label="📥 Download Filtered CSV",
    data=filtered_df.to_csv(index=False),
    file_name="filtered_strains.csv",
    mime="text/csv"
)
