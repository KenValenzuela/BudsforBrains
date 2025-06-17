# === main.py (Improved with Confirmation Guidance) ===
import streamlit as st
from utils.supabase_client import supabase

st.set_page_config(page_title="Welcome to Budtender Assistant", page_icon="🌿")
st.title("🌿 Buds for Brains")

# === Auth Logic ===
if "user" not in st.session_state:
    st.subheader("🔐 Log In or Create an Account")

    st.markdown("""
Enter a valid email and create a password to get started.

- If this is your **first time**, click **Sign Up** to create an account.
- You'll get a **confirmation email** — check your inbox and click the link.
- On future visits, just **Log In** with the same credentials.
    """)

    email = st.text_input("📧 Email", placeholder="you@example.com")
    password = st.text_input("🔑 Password", type="password", placeholder="Create a password")

    col1, col2 = st.columns(2)

    if col1.button("🔐 Log In"):
        try:
            user = supabase.auth.sign_in_with_password({"email": email, "password": password})
            if not user.user.email_confirmed_at:
                st.warning("📧 Your email is not confirmed. Please check your inbox and click the confirmation link.")
            else:
                st.session_state["user"] = user
                st.success(f"✅ Logged in as {user.user.email}")
                st.rerun()
        except Exception as e:
            st.error(f"❌ Login failed: {str(e)}")

    if col2.button("🆕 Sign Up"):
        try:
            user = supabase.auth.sign_up({"email": email, "password": password})
            st.info("📧 Account created. Check your email and click the confirmation link to activate your account.")
        except Exception as e:
            if "User already registered" in str(e):
                st.warning("⚠️ This email is already registered. Try logging in instead.")
            else:
                st.error(f"❌ Signup failed: {str(e)}")

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
