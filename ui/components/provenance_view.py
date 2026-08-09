"""
Provenance View component: Pipeline audit trail timeline visualization.
"""
import json
import streamlit as st

from src.db import repository as repo
from ui.theme import COLORS


def render_provenance(doc_id: int):
    """Render the provenance audit trail for a document.

    Args:
        doc_id: The document ID to show provenance for.
    """
    provenance_records = repo.get_provenance_by_document(doc_id)

    if not provenance_records:
        st.info("No provenance data available for this document.")
        return

    st.markdown("### 🔍 Pipeline Provenance Trail")

    for record in provenance_records:
        stage = record["stage_name"]
        status = record["status"]
        duration = record.get("duration_ms", 0)
        model = record.get("model_used", "")
        summary = record.get("output_summary", "")
        error = record.get("error_message", "")
        metadata = record.get("metadata_json", "")

        # Status indicator
        if status == "COMPLETED":
            icon = "✅"
            color = COLORS["success"]
        else:
            icon = "❌"
            color = COLORS["danger"]

        # Stage display name
        stage_display = stage.replace("STAGE_", "").replace("_", " ").title()

        # Build the timeline item
        with st.expander(
            f"{icon} {stage_display} — {duration}ms"
            + (f" | Model: `{model}`" if model else ""),
            expanded=False,
        ):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Status:** `{status}`")
                st.markdown(f"**Duration:** `{duration}ms`")
                if model:
                    st.markdown(f"**Model:** `{model}`")

            with col2:
                if record.get("started_at"):
                    st.markdown(f"**Started:** `{record['started_at']}`")
                if record.get("completed_at"):
                    st.markdown(f"**Completed:** `{record['completed_at']}`")

            if summary:
                st.markdown(f"**Output:** {summary}")

            if error:
                st.error(f"**Error:** {error}")

            if metadata:
                try:
                    meta = json.loads(metadata)
                    st.json(meta)
                except (json.JSONDecodeError, TypeError):
                    pass
