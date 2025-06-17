# === main.py (Login + Sidebar Navigation Only) ===
import streamlit as st
from utils.supabase_client import supabase

st.set_page_config(page_title="Welcome to Budtender Assistant", page_icon="🌿")
st.title("🌿 Buds for Brains")

# === Login / Signup Form ===
if "user" not in st.session_state:
    st.subheader("🔐 Login or Sign Up")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    col1, col2 = st.columns(2)

    if col1.button("Login"):
        try:
            user = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state["user"] = user
            st.success("✅ Logged in.")
            st.rerun()
        except Exception as e:
            st.error("❌ Login failed. Check your credentials.")

    if col2.button("Sign Up"):
        try:
            user = supabase.auth.sign_up({"email": email, "password": password})
            st.session_state["user"] = user
            st.success("✅ Signed up.")
            st.rerun()
        except Exception as e:
            st.error("❌ Signup failed. Email may already exist.")

else:
    # === Authenticated View ===
    user_email = st.session_state["user"].user.email
    st.success(f"Welcome back, {user_email}!")

    st.markdown("""
    Use the sidebar to navigate:
    - 💬 Chat Assistant
    - 🌿 Explore Strains
    - 🧠 Take the Survey
    - 📘 View Your Journal
    - 🧬 View Your Profile
    - 📖 About the Project
    """)

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()