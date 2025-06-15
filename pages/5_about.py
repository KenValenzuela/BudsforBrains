import streamlit as st

st.set_page_config(page_title="About This App", page_icon="📘")

st.title("About the Project")

st.markdown("""
##  My Story

I started this project while working as a budtender — helping patients, first-timers, and daily users navigate a market that often felt more like a guessing game than a science.

People would ask:  
> *"What’s good for anxiety?"*  
> *"What’s the difference between these two strains?"*  
> *"Why did that last one make me paranoid?"*

And the truth was, it depended. There was no easy way to explain terpene profiles, effects, or the “why” behind a recommendation without overwhelming them.

Even after I left the cannabis industry, I couldn’t shake the feeling that **this should exist** — a place where people could explore cannabis at their own pace, ask real questions, and get smarter recommendations.

So I built it.  
Not because I had to, but because I believed in it.

This is a passion project I refused to let go of — combining my background in data science, natural language processing, and my time behind the counter.

---

##  What This App Does

The Budtender Assistant blends explainability and personalization:

-  AI Chatbot (RAG): Ask anything. It searches real strain data to answer in plain English.
-  Guided Survey: Your preferences are saved and used to guide better strain matches.
-  Explore Page: Filter across terpenes, effects, and strain types.
-  Journal Page: Keep track of what worked and how you felt.
-  ML Model: An XGBoost model predicts missing dominant terpenes for strains that don’t list them.

---

## ️ Built With

- **Streamlit** for the UI
- **FAISS** for semantic search
- **OpenAI** for embeddings and completions
- **XGBoost** for dominant terpene imputation
- **Pandas + Parquet** for data handling
- **You**, the user, to guide the assistant through real feedback

---

##  Why It Matters

Most recommendation engines just push products.  
This one listens first.

It’s not just about getting high — it’s about understanding what works for you and *why*.  
Whether you're here for focus, pain relief, or just curiosity — this app gives you space to learn, reflect, and grow your understanding of cannabis.

---

##  Who Made This

I’m a data science graduate who started as a budtender.  
This app is my way of blending both worlds — using tech to make cannabis more transparent, accessible, and useful to real people.

If you're curious about the project, want to collaborate, or just want to chat — feel free to reach out via [GitHub](#) or [LinkedIn](#).
""")
