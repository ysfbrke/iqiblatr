from pathlib import Path
import sys
import streamlit as st
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))
from common.analytics import show_platform
if st.button("← Ana Sayfaya Dön"):
    st.session_state.active_app = "home"
    st.rerun()
show_platform("Shopify")
