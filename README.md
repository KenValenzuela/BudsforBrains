# Buds for Brains

Buds for Brains is an interactive Streamlit application that helps users explore cannabis strains, record personal experiences and generate recommendations using OpenAI embeddings and a FAISS vector store. User data is managed in Supabase.

## Features

- **Authentication** with Supabase (email and password).
- **Chat Assistant** for strain questions powered by retrieval‑augmented generation.
- **Strain Explorer** with filters by type, terpene and effects.
- **Budtender Survey** to collect preferences and update a personal profile.
- **Journal** to log strains and effects which updates the profile dashboard.
- **Profile Dashboard** summarising logged effects and past strains.
- **About** page describing the project background.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Provide environment variables (e.g. in a `.env` file):
   - `OPENAI_API_KEY` – OpenAI API key for embeddings and chat completions.
   - `SUPABASE_URL` and `SUPABASE_KEY` – credentials for your Supabase project.
3. Run the application:
   ```bash
   streamlit run main.py
   ```

The repository includes pre-built FAISS indexes and example user data. Scripts in the `scripts/` directory can rebuild the dataset from the raw Leafly data and create embeddings.

## Data Sources

Strain information is derived from public sources such as Leafly, AllBud and Weedmaps via simple scrapers. Terpene and cannabinoid metadata lives in `data/terpene_info.json` and `data/cannabinoid_info.json`.

## License

No license file is provided. Please consult the repository owner before redistributing or using the code in a commercial setting.
