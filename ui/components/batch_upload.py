"""
Batch Upload component: Multi-file upload with progress bar.
"""
import os
import tempfile
import streamlit as st

from src.config import ALL_SUPPORTED_TYPES, SAMPLE_DATA_DIR
from src.db.models import initialize_database


def render_batch_upload():
    """Render the batch file upload widget in the sidebar."""

    st.markdown("### 📤 Upload Documents")

    uploaded_files = st.file_uploader(
        "Drop medical records here",
        type=[ext.lstrip(".") for ext in ALL_SUPPORTED_TYPES],
        accept_multiple_files=True,
        key="file_uploader",
    )

    if uploaded_files:
        st.markdown(f"**{len(uploaded_files)} file(s) selected**")

        if st.button("🚀 Process Batch", type="primary", use_container_width=True):
            _process_uploaded_files(uploaded_files)

    st.markdown("---")

    # Quick-load sample data
    st.markdown("### 🧪 Sample Data")
    if st.button("Load Sample Files", use_container_width=True):
        _load_sample_data()


def _process_uploaded_files(uploaded_files):
    """Save uploaded files to a temp directory and process them."""
    from src.pipeline import process_batch

    initialize_database()

    # Save uploaded files to temp directory
    temp_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "uploads"
    )
    os.makedirs(temp_dir, exist_ok=True)

    file_paths = []
    for uploaded_file in uploaded_files:
        file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        file_paths.append(file_path)

    # Process with progress bar
    progress_bar = st.progress(0, text="Processing documents...")
    status_text = st.empty()

    total = len(file_paths)
    results = []

    from src.pipeline import process_single_document
    from src.db import repository as repo

    batch_id = repo.create_batch(total_files=total)
    success = 0
    failed = 0

    for i, fp in enumerate(file_paths):
        filename = os.path.basename(fp)
        status_text.markdown(f"Processing **{filename}** ({i+1}/{total})...")
        progress_bar.progress((i + 1) / total)

        result = process_single_document(fp, batch_id=batch_id)
        results.append(result)

        if result["status"] == "COMPLETED":
            success += 1
        else:
            failed += 1

        repo.update_batch_progress(batch_id, i + 1, success, failed)

    progress_bar.progress(1.0, text="Complete!")
    status_text.empty()

    # Show summary
    st.success(
        f"✅ Batch complete: **{success}** succeeded, **{failed}** failed "
        f"out of **{total}** files."
    )

    st.rerun()


def _load_sample_data():
    """Load and process files from the sample_data directory."""
    import glob
    from src.pipeline import process_batch

    initialize_database()

    extensions = ("*.txt", "*.pdf", "*.docx", "*.png", "*.jpg", "*.jpeg", "*.tiff", "*.tif")
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(SAMPLE_DATA_DIR, ext)))

    if not files:
        st.warning(
            f"No sample files found in `{SAMPLE_DATA_DIR}`. "
            "Run `python generate_test_data.py` first."
        )
        return

    st.info(f"Found **{len(files)}** sample file(s). Processing...")

    progress_bar = st.progress(0, text="Processing sample data...")

    from src.pipeline import process_single_document
    from src.db import repository as repo

    batch_id = repo.create_batch(total_files=len(files))
    success = 0
    failed = 0

    for i, fp in enumerate(files):
        filename = os.path.basename(fp)
        progress_bar.progress((i + 1) / len(files), text=f"Processing {filename}...")

        result = process_single_document(fp, batch_id=batch_id)
        if result["status"] == "COMPLETED":
            success += 1
        else:
            failed += 1

        repo.update_batch_progress(batch_id, i + 1, success, failed)

    progress_bar.progress(1.0, text="Complete!")
    st.success(f"✅ Loaded {success}/{len(files)} sample files.")
    st.rerun()
