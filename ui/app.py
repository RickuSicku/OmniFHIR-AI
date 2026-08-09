"""
OmniFHIR-AI: Streamlit Application Entry Point

Main application with page routing between Dashboard and Detail views.
Includes sidebar with batch upload, export, and database controls.
"""
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from src.db.models import initialize_database
from src.db import repository as repo
from ui.theme import get_custom_css, COLORS
from ui.components.dashboard import render_dashboard
from ui.components.detail_view import render_detail_view
from ui.components.batch_upload import render_batch_upload
from ui.components.export import render_export


# ─── Page Configuration ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="OmniFHIR AI — Clinical Abstraction Pipeline",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize database
initialize_database()

# Inject custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

# ─── Session State Initialization ─────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state["page"] = "dashboard"
if "selected_doc_id" not in st.session_state:
    st.session_state["selected_doc_id"] = None


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo / Brand Header
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['accent']} 100%);
            color: white;
            padding: 1.2rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            text-align: center;
        ">
            <div style="font-size: 1.4rem; font-weight: 700; letter-spacing: -0.5px;">
                🏥 OmniFHIR AI
            </div>
            <div style="font-size: 0.75rem; opacity: 0.85; margin-top: 0.2rem;">
                Clinical Abstraction Pipeline
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Navigation
    st.markdown("### 🧭 Navigation")
    if st.button("📊 Dashboard", use_container_width=True):
        st.session_state["page"] = "dashboard"
        st.session_state.pop("selected_doc_id", None)
        st.rerun()

    st.markdown("---")

    # Batch Upload
    render_batch_upload()

    st.markdown("---")

    # Export
    render_export()

    st.markdown("---")

    # Database Controls
    st.markdown("### ⚙️ Settings")
    if st.button("🗑️ Clear All Data", use_container_width=True):
        repo.clear_all_data()
        st.success("All data cleared.")
        st.rerun()


# ─── Main Content Area ───────────────────────────────────────────────────────

# Header Banner
st.markdown(
    """
    <div class="main-header">
        <h1>🏥 OmniFHIR AI</h1>
        <p>Multi-Modal GenAI Clinical Abstraction Pipeline — Cotiviti Innovation</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Page Router
current_page = st.session_state.get("page", "dashboard")

if current_page == "detail" and st.session_state.get("selected_doc_id"):
    render_detail_view(st.session_state["selected_doc_id"])
else:
    render_dashboard()
