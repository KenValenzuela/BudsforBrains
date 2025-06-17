f
from supabase_profile_utils import fetch_or_create_user_profile

user_email = st.session_state["user"].user.email
live_profile = fetch_or_create_user_profile(user_email)
st.write("📦 Supabase Profile:", live_profile)
