# === 6_about.py (Professional & Personal Storytelling with Emojis + Links) ===
import streamlit as st

st.set_page_config(page_title="About This App", page_icon="📘")
st.title("📘 About Bud for Brains")

st.markdown("""
## 🌿 Why I Built This

When I worked as a **budtender**, I saw the same thing every day: people walking in, overwhelmed by options and unsure where to start. 

They’d ask:
> *“What’s good for focus?”*  
> *“Why did this one knock me out but that one didn’t?”*

We’d talk about terpenes,the entourage effect,tolerances and forms —but it was hard to explain the science while watching a line form behind your patient.

Later, when I moved into a **data analyst role** in a dispensary’s corporate setting, I saw just how manual and outdated the industry’s data systems really were.  That experience drove home the need for smarter tools that bridge the gap between product chemistry and personal experience.

Even after I left the cannabis industry to pursue my masters in AI for Business, this problem stayed with me.
So I built the solution I wish I had on the job: a **personalized cannabis assistant** powered by data, education, and user feedback. 

---

## 🧠 What It Does

- **Smart Chat Assistant:** Ask anything. Get informed, context-aware answers using RAG (retrieval-augmented generation).
- **Guided Survey:** Capture your preferences, effects, and goals.
- **Explorer:** Filter strains by dominant terpene, reported effects, or classification.
- **Journal:** Log experiences and build your personal history.
- **Predictive Modeling:** Uses XGBoost to fill in missing terpene data.

Everything gets sharper with use, so the system learns from you. 📈

---

## ⚙️ Built With

-  **Streamlit** for the front-end interface
-  **Supabase** for authentication and user data storage
-  **FAISS** for fast vector-based semantic search
-  **OpenAI** for embeddings and natural language answers
-  **Pandas** + **XGBoost** for processing and prediction

---

## 💡 Why It Matters

Most cannabis apps are designed to push products. 🛒 This one is designed to help you understand them.

Whether you’re a medical patient, a curious first-timer, or a returning user trying to track what works for you, **Bud for Brains puts education and personalization first.**

No hype. Just help. 🙌

> It’s built to teach you how to ask better questions—and find better answers.

---

## 👋 About Me

My name is Ken Valenzuela, and I graduated with a BS in Data Science. As I worked towards my degree, I took a job 5 minutes from home at a dispensary, which started my journey in the cannabis retail world. 🌱

I’ve worked the sales floor, starting at front desk admin, to patient service representative, then finally as a dat analyst. I understand this space from multiple angles—and I’m passionate about combining that experience with machine learning and human-centered design.

This app is part capstone, part case study, and part personal mission. 🎓💼

Want to collaborate or give feedback?
- [GitHub](https://github.com/KenValenzuela)
- [LinkedIn](https://www.linkedin.com/in/ken-valenzuela)
""")
