# =============================================================
# LOGIN / REGISTER PAGE
# Author: Aakash Kushwah
# =============================================================

import streamlit as st
import time
import sys
import os

# Fix import path to project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from auth.auth_service import login_or_register

# -------------------------------------------------------------
# PAGE UI
# -------------------------------------------------------------
st.title("🔐 Login / Register")

st.markdown("""
Enter your username and password.  
- **Existing user?** → You'll be logged in.  
- **New user?** → Your account will be created automatically.
""")

st.markdown("---")

username = st.text_input("👤 Username")
password = st.text_input("🔑 Password", type="password")

# -------------------------------------------------------------
# SUBMIT BUTTON
# -------------------------------------------------------------
if st.button("Continue →"):

    if username.strip() == "" or password.strip() == "":
        st.warning("⚠️ Please fill in both fields.")

    else:
        result = login_or_register(username.strip(), password.strip())

        if result == "login_success":

            with st.spinner("Logging you in..."):
                time.sleep(1)

            st.success("✅ Login successful! Redirecting...")
            st.switch_page("pages/2_Dashboard.py")

        elif result == "register_success":

            with st.spinner("Creating your account..."):
                time.sleep(1)

            st.success("🎉 Account created! Redirecting...")
            st.switch_page("pages/2_Dashboard.py")

        elif result == "login_failed":
            st.error("❌ Incorrect password. Please try again.")

        else:
            st.error("❌ Something went wrong. Please check your connection.")

# -------------------------------------------------------------
# FOOTER
# -------------------------------------------------------------
st.markdown("---")
st.caption("Built with ❤️ by Aakash Kushwah")