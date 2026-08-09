"""
Export component: FHIR Bundle JSON and CSV summary export.
"""
import csv
import io
import json
from datetime import datetime

import streamlit as st

from src.db import repository as repo


def render_export():
    """Render the export buttons in the sidebar."""
    st.markdown("### 📥 Export Data")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("FHIR Bundle", use_container_width=True):
            _export_fhir_bundle()

    with col2:
        if st.button("CSV Summary", use_container_width=True):
            _export_csv()


def _export_fhir_bundle():
    """Export approved FHIR Observations as a FHIR Bundle JSON."""
    approved_outputs = repo.get_approved_fhir_outputs()

    if not approved_outputs:
        st.warning("No approved FHIR outputs to export. Approve documents first.")
        return

    # Build FHIR Bundle
    entries = []
    for output in approved_outputs:
        try:
            resource = json.loads(output["fhir_json"])
            entries.append({
                "fullUrl": f"urn:uuid:{resource.get('id', '')}",
                "resource": resource,
            })
        except json.JSONDecodeError:
            continue

    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "total": len(entries),
        "entry": entries,
    }

    bundle_json = json.dumps(bundle, indent=2)

    st.download_button(
        label="⬇️ Download FHIR Bundle",
        data=bundle_json,
        file_name=f"omnifhir_bundle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
        use_container_width=True,
    )

    st.success(f"Bundle ready: {len(entries)} observation(s)")


def _export_csv():
    """Export all document data as a CSV summary."""
    export_data = repo.get_export_data()

    if not export_data:
        st.warning("No data to export.")
        return

    # Build CSV
    output = io.StringIO()
    if export_data:
        writer = csv.DictWriter(output, fieldnames=export_data[0].keys())
        writer.writeheader()
        writer.writerows(export_data)

    csv_content = output.getvalue()

    st.download_button(
        label="⬇️ Download CSV",
        data=csv_content,
        file_name=f"omnifhir_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.success(f"CSV ready: {len(export_data)} row(s)")
