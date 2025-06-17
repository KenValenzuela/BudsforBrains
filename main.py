# === main.py (Improved Login + Sidebar Navigation) ===
import streamlit as st
from utils.supabase_client import supabase

st.set_page_config(page_title="Welcome to Budtender Assistant", page_icon="🌿")
st.title("🌿 Buds for Brains")

# === Auth Logic ===
if "user" not in st.session_state:
    st.subheader("🔐 Log In or Create an Account")

    st.markdown(
        "Enter **any valid email and a password you choose**. This is separate from your personal email provider.\n\n"
        "- If this is your **first time**, clicking **Sign Up** will create your account.\n"
        "- On future visits, just **Log In** with the same email/password."
    )

    email = st.text_input("📧 Email", placeholder="you@example.com")
    password = st.text_input("🔑 Password", type="password", placeholder="Create a password")

    col1, col2 = st.columns(2)

    if col1.button("🔐 Log In"):
        try:
            user = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state["user"] = user
            st.success(f"✅ Logged in as {user.user.email}")
            st.rerun()
        except Exception as e:
            st.error("❌ Login failed. Make sure your credentials are correct.")

    if col2.button("🆕 Sign Up"):
        try:
            user = supabase.auth.sign_up({"email": email, "password": password})
            st.session_state["user"] = user
            st.success("✅ Account created successfully. You're now logged in.")
            st.rerun()
        except Exception as e:
            st.error("❌ Signup failed. That email might already be in use.")

else:
    # === Authenticated View ===
    user_email = st.session_state["user"].user.email
    st.success(f"👋 Welcome back, {user_email}!")

    st.markdown("""
Use the sidebar to explore the app:

- 💬 Chat Assistant  
- 🌿 Explore Strains  
- 🧠 Take the Survey  
- 📘 View Your Journal  
- 🧬 View Your Profile  
- 📖 About the Project  
    """)

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Log Out"):
        st.session_state.clear()
        st.rerun()
