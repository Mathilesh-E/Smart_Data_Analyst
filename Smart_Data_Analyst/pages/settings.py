"""
Page: 10. Settings & Session Management
Controls for visual theme, chart sampling thresholds, session state resets,
and environment information.
"""
import streamlit as st
from modules.ui_components import render_header

def render_settings():
    render_header(
        title="Settings & Session Management",
        subtitle="Manage visualization preferences, sampling limits, and active session memory."
    )

    st.markdown("### ⚙️ Application Preferences")
    
    current_theme = st.session_state.get("theme", "dark")
    new_theme = st.selectbox("Dashboard Appearance Theme", ["dark", "light"], index=0 if current_theme == "dark" else 1)
    if new_theme != current_theme:
        st.session_state["theme"] = new_theme
        st.rerun()

    sample_size = st.slider("Visualization Sampling Limit (Rows)", 1000, 50000, 10000, step=1000)
    st.caption("Larger values allow higher chart fidelity but require more client memory for scatter/box plots.")

    st.markdown("---")
    st.markdown("### 🧹 Session & Memory Management")
    st.write(
        "Resetting the session clears all uploaded files, working copies, and cleaning logs "
        "from memory without affecting your disk files."
    )
    
    if st.button("Clear Active Session Memory", type="primary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.success("Session state cleared successfully!")
        st.rerun()

