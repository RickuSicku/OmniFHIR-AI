"""
Dashboard component: File overview table with summary metrics.
"""
import streamlit as st
import pandas as pd

from src.db import repository as repo
from ui.theme import (
    render_badge,
    render_confidence,
    render_metric_card,
    COLORS,
)


def render_dashboard():
    """Render the main dashboard with summary metrics and document table."""

    # ── Summary Metrics Row ────────────────────────────────────────────
    stats = repo.get_summary_statistics()

    cols = st.columns(6)
    metrics = [
        (str(stats["total"]), "Total Files"),
        (str(stats["completed"]), "Processed"),
        (str(stats["compliant"]), "Compliant"),
        (str(stats["non_compliant"]), "Non-Compliant"),
        (str(stats["pending_review"]), "Pending Review"),
        (str(stats["failed"]), "Failed"),
    ]

    for col, (value, label) in zip(cols, metrics):
        with col:
            st.markdown(render_metric_card(value, label), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Document Table ─────────────────────────────────────────────────
    dashboard_data = repo.get_dashboard_data()

    if not dashboard_data:
        st.info(
            "📂 No documents processed yet. Upload files using the sidebar to get started."
        )
        return

    # Build display dataframe
    rows = []
    for doc in dashboard_data:
        confidence = doc.get("confidence_score")
        compliance = doc.get("compliance_status", "N/A")
        review = doc.get("review_status", "PENDING_REVIEW")
        status = doc.get("doc_status", "UNKNOWN")

        # Determine badge types
        if status == "FAILED":
            status_badge = render_badge("FAILED", "failed")
        elif compliance == "COMPLIANT":
            compliance_badge = render_badge("COMPLIANT", "compliant")
        elif compliance == "NON-COMPLIANT":
            compliance_badge = render_badge("NON-COMPLIANT", "non-compliant")
        else:
            compliance_badge = render_badge("N/A", "pending")

        if review == "APPROVED":
            review_badge = render_badge("APPROVED", "approved")
        elif review == "REJECTED":
            review_badge = render_badge("REJECTED", "rejected")
        elif review == "FLAGGED":
            review_badge = render_badge("FLAGGED", "flagged")
        else:
            review_badge = render_badge("PENDING", "pending")

        # Flag low confidence
        conf_display = render_confidence(confidence) if confidence is not None else "—"
        if confidence is not None and confidence < 0.7:
            conf_display = f"⚠️ {conf_display}"

        rows.append({
            "doc_id": doc["doc_id"],
            "filename": doc["filename"],
            "type": doc.get("file_type", ""),
            "patient_id": doc.get("patient_id", "—"),
            "test_value": f"{doc['test_value']}{doc.get('test_unit', '%')}" if doc.get("test_value") else "—",
            "confidence": confidence,
            "confidence_display": conf_display,
            "compliance": compliance,
            "compliance_badge": compliance_badge if status != "FAILED" else status_badge,
            "review": review or "PENDING_REVIEW",
            "review_badge": review_badge,
            "status": status,
        })

    # ── Render Table ───────────────────────────────────────────────────
    st.markdown("### 📋 Document Queue")

    for row in rows:
        with st.container():
            cols = st.columns([3, 1, 1, 1, 1, 1, 1])

            with cols[0]:
                # Clickable filename
                if st.button(
                    f"📄 {row['filename']}",
                    key=f"doc_{row['doc_id']}",
                    use_container_width=True,
                ):
                    st.session_state["selected_doc_id"] = row["doc_id"]
                    st.session_state["page"] = "detail"
                    st.rerun()

            with cols[1]:
                st.markdown(f"**{row['type']}**")

            with cols[2]:
                st.markdown(row.get("patient_id", "—"))

            with cols[3]:
                st.markdown(row.get("test_value", "—"))

            with cols[4]:
                st.markdown(row["confidence_display"], unsafe_allow_html=True)

            with cols[5]:
                st.markdown(row["compliance_badge"], unsafe_allow_html=True)

            with cols[6]:
                st.markdown(row["review_badge"], unsafe_allow_html=True)

            st.markdown("---")
