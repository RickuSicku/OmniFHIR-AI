# 🏥 OmniFHIR AI

<div align="center">
  <em>A Multi-Modal GenAI Clinical Abstraction Pipeline</em>
</div>
<br/>

**OmniFHIR AI** is an advanced, fully local, multi-modal data pipeline designed to ingest noisy clinical documents (PDFs, handwritten faxes, faxes, text notes), extract critical clinical data points using vision models and LLMs, evaluate them against HEDIS compliance rules, and output standardized FHIR JSON bundles.

It is built to demonstrate how open-weight AI (Ollama + Llama 3.2 Vision + Mistral) can automate clinical abstraction workflows securely and offline.

---

## ✨ Key Features

- 📄 **Multi-Modal Ingestion:** Supports `.txt`, `.pdf`, `.png`, `.jpg`, and multi-page `.tiff` files.
- 👁️ **Dual-Channel OCR:** Uses `llama3.2-vision` for primary optical character recognition with a `tesseract` fallback for low-confidence reads.
- 🧠 **GenAI Extraction:** Uses `mistral` (via Ollama) to structure raw text into patient demographics, lab names, values, units, and dates.
- ⚖️ **HEDIS Rules Engine:** Automatically evaluates extracted lab results (e.g., HbA1c) against predefined clinical compliance thresholds.
- 🔄 **FHIR Standardization:** Converts the extracted and evaluated data into compliant FHIR `Observation` JSON resources.
- 📊 **Streamlit Dashboard:** Includes a modern web portal for Batch Processing, Document Queue management, Human-in-the-Loop (HITL) review, and data export.
- 🔒 **100% Local & Secure:** All inference runs locally via Ollama, ensuring PHI never leaves the machine.

## 🏗️ Architecture

The system operates in a linear 6-stage pipeline:

1. **Ingestion:** Validates file types and integrity.
2. **OCR / Vision Processing:** Extracts text from images and PDFs. Splits multi-page TIFFs for comprehensive reading.
3. **LLM Extraction:** Parses the unstructured OCR output into a structured Pydantic schema.
4. **Validation:** Ensures data types and logical bounds are met.
5. **Rules Engine:** Runs the extracted data against HEDIS compliance measures.
6. **FHIR Output & Persist:** Generates the FHIR JSON and stores the provenance, status, and metrics in a local SQLite database.

## 🚀 Quickstart

### Prerequisites
- **Python 3.12+**
- **Ollama** installed and running on `localhost:11434`
- **Tesseract OCR** (Optional, for fallback OCR)

### Installation

1. Clone the repository and create a virtual environment:
   ```bash
   git clone https://github.com/RickuSicku/OmniFHIR-AI.git
   cd OmniFHIR-AI
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the automated setup check. This will automatically pull the required models (`mistral` and `llama3.2-vision`) and initialize the SQLite database:
   ```bash
   python setup_check.py
   ```

### Running the System

#### Option 1: Web Interface (Recommended)
Launch the Streamlit dashboard for a visual, interactive experience:
```bash
streamlit run ui/app.py
```
Open `http://localhost:8501` in your browser. From here, you can load sample files, review extractions, approve FHIR outputs, and export CSVs/Bundles.

#### Option 2: CLI Batch Pipeline
Run the pipeline headlessly on all files in the `sample_data/` directory:
```bash
python -m src.pipeline
```

## 🧪 Generating Sample Data

Need test data? The repository includes a robust synthetic data generator that creates noisy, realistic clinical documents (including corrupt files for testing error handling).

```bash
python generate_test_data.py
```
This will populate the `sample_data/` folder with a mix of PDFs, DOCX, TXT, and image files simulating different clinical scenarios (e.g., handwritten lab slips, discharge summaries).

## 📁 Repository Structure

```text
OmniFHIR-AI/
├── src/
│   ├── db/            # SQLite database models and engine
│   ├── extraction/    # LLM integration (Ollama/Mistral)
│   ├── fhir/          # FHIR Observation resource building
│   ├── ocr/           # Llama Vision and Tesseract orchestration
│   ├── provenance/    # Audit trails and logging
│   ├── rules/         # HEDIS compliance engine
│   ├── config.py      # System configuration
│   └── pipeline.py    # Main orchestration logic
├── ui/
│   └── app.py         # Streamlit dashboard
├── generate_test_data.py # Synthetic data creator
├── setup_check.py     # Environment verifier
└── requirements.txt
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
