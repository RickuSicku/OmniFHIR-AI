"""
Detail View component: Three-column layout for document review.

Left: Original document viewer
Center: FHIR JSON with syntax highlighting
Right: Action panel (Approve/Reject/Flag + reviewer notes)
"""
import json
import streamlit as st
from PIL import Image

from src.db import repository as repo
from src.config import STATUS_COMPLETED, REVIEW_APPROVED, REVIEW_REJECTED, REVIEW_FLAGGED
from ui.theme import render_badge, render_confidence, COLORS
from ui.components.provenance_view import render_provenance


def render_detail_view(doc_id: int):
    """Render the three-column detail view for a single document.

    Args:
        doc_id: The document ID to display.
    """
    doc = repo.get_document(doc_id)
    if not doc:
        st.error(f"Document {doc_id} not found.")
        return

    extraction = repo.get_extraction_by_document(doc_id)
    compliance = repo.get_compliance_by_document(doc_id)
    fhir_output = repo.get_fhir_output_by_document(doc_id)
    latest_review = repo.get_latest_review(doc_id)

    # ── Back Button ────────────────────────────────────────────────────
    if st.button("← Back to Dashboard", key="back_btn"):
        st.session_state["page"] = "dashboard"
        st.session_state.pop("selected_doc_id", None)
        st.rerun()

    # ── Document Header ───────────────────────────────────────────────
    st.markdown(f"### 📄 {doc['filename']}")

    header_cols = st.columns(4)
    with header_cols[0]:
        st.markdown(f"**Type:** `{doc['file_type']}`")
    with header_cols[1]:
        st.markdown(f"**Modality:** `{doc['modality']}`")
    with header_cols[2]:
        st.markdown(f"**Status:** `{doc['status']}`")
    with header_cols[3]:
        if extraction:
            st.markdown(
                f"**Confidence:** {render_confidence(extraction['confidence_score'])}",
                unsafe_allow_html=True,
            )

    st.markdown("---")

    if doc["status"] == "FAILED":
        st.error(f"⚠️ Processing failed: {doc.get('error_message', 'Unknown error')}")
        render_provenance(doc_id)
        return

    # ── Three-Column Layout ───────────────────────────────────────────
    col_doc, col_fhir, col_actions = st.columns([4, 4, 3])

    # ── LEFT: Document Viewer ─────────────────────────────────────────
    with col_doc:
        st.markdown(
            '<div class="panel-header">📝 Source Document</div>',
            unsafe_allow_html=True,
        )

        if doc["modality"] == "image":
            try:
                img = Image.open(doc["file_path"])
                st.image(img, use_container_width=True, caption=doc["filename"])
            except Exception:
                st.warning("Cannot display image file.")
        elif extraction and extraction.get("raw_text"):
            st.text_area(
                "Document Content",
                value=extraction["raw_text"],
                height=400,
                disabled=True,
                label_visibility="collapsed",
            )
        else:
            st.info("No document content available.")

        # Source snippet highlight
        if extraction and extraction.get("source_snippet"):
            st.markdown("**📌 Evidence Snippet:**")
            st.success(f'"{extraction["source_snippet"]}"')

    # ── CENTER: FHIR JSON ─────────────────────────────────────────────
    with col_fhir:
        st.markdown(
            '<div class="panel-header">🔬 FHIR Observation</div>',
            unsafe_allow_html=True,
        )

        with st.container(height=400):
            if fhir_output:
                try:
                    fhir_data = json.loads(fhir_output["fhir_json"])
                    formatted = json.dumps(fhir_data, indent=2)
                    st.code(formatted, language="json")
                except json.JSONDecodeError:
                    st.code(fhir_output["fhir_json"], language="json")
            else:
                st.info("No FHIR output generated.")

        # Extraction summary
        if extraction:
            st.markdown("**Extraction Summary:**")
            ext_cols = st.columns(2)
            with ext_cols[0]:
                st.markdown(f"**Patient:** `{extraction.get('patient_id', 'N/A')}`")
                st.markdown(f"**Test:** `{extraction.get('test_name', 'N/A')}`")
            with ext_cols[1]:
                st.markdown(f"**Value:** `{extraction.get('test_value', 'N/A')}{extraction.get('test_unit', '')}`")
                st.markdown(f"**Date:** `{extraction.get('test_date', 'N/A')}`")

    # ── RIGHT: Actions Panel ──────────────────────────────────────────
    with col_actions:
        st.markdown(
            '<div class="panel-header">⚡ Review Actions</div>',
            unsafe_allow_html=True,
        )

        # Compliance Status Card
        if compliance:
            is_comp = compliance["is_compliant"]
            status_color = COLORS["success"] if is_comp else COLORS["danger"]
            status_text = compliance["status"]
            badge_type = "compliant" if is_comp else "non-compliant"

            st.markdown(
                f"**Compliance:** {render_badge(status_text, badge_type)}",
                unsafe_allow_html=True,
            )
            st.markdown(f"*{compliance.get('detail', '')}*")
            st.markdown("---")

        # Current review status
        if latest_review:
            st.markdown(
                f"**Current Review:** {render_badge(latest_review['reviewer_action'], latest_review['reviewer_action'].lower())}",
                unsafe_allow_html=True,
            )
            if latest_review.get("reviewer_notes"):
                st.markdown(f"*Notes: {latest_review['reviewer_notes']}*")
            st.markdown("---")

        # Review Actions
        st.markdown("**Submit Review:**")

        reviewer_notes = st.text_area(
            "Reviewer Notes",
            placeholder="Add notes about this review...",
            key=f"notes_{doc_id}",
            height=100,
        )

        btn_cols = st.columns(3)

        with btn_cols[0]:
            if st.button("Approve", key=f"approve_{doc_id}", type="primary", use_container_width=True):
                repo.create_review(doc_id, REVIEW_APPROVED, reviewer_notes)
                st.success("Document approved!")
                st.rerun()

        with btn_cols[1]:
            if st.button("Reject", key=f"reject_{doc_id}", use_container_width=True):
                repo.create_review(doc_id, REVIEW_REJECTED, reviewer_notes)
                st.warning("Document rejected.")
                st.rerun()

        with btn_cols[2]:
            if st.button("Flag", key=f"flag_{doc_id}", use_container_width=True):
                repo.create_review(doc_id, REVIEW_FLAGGED, reviewer_notes)
                st.info("Document flagged for further review.")
                st.rerun()

        # Re-processing option
        if latest_review and latest_review["reviewer_action"] == REVIEW_REJECTED:
            st.markdown("---")
            st.markdown("**🔄 Re-process:**")
            if st.button("Re-run Pipeline", key=f"reprocess_{doc_id}"):
                with st.spinner("Re-processing document..."):
                    from src.pipeline import process_single_document
                    result = process_single_document(doc["file_path"])
                    if result["status"] == "COMPLETED":
                        st.success("Re-processing complete!")
                    else:
                        st.error(f"Re-processing failed: {result.get('error', 'Unknown')}")
                    st.rerun()

    # ── Provenance Trail ──────────────────────────────────────────────
    st.markdown("---")
    render_provenance(doc_id)
