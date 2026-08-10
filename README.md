# OmniFHIR AI

<div align="center">
  <em>A Multi-Modal GenAI Clinical Abstraction Pipeline</em>
</div>
<br/>

**OmniFHIR AI** is a local, multi-modal pipeline built to extract clinical data from unstructured documents and evaluate HEDIS compliance. It ingests noisy clinical documents (PDFs, handwritten faxes, text notes), extracts critical data points using vision models and LLMs, evaluates them against predefined rules, and outputs standardized FHIR JSON bundles.

It demonstrates how open-weight AI (Ollama + Llama 3.2 Vision + Mistral) can automate clinical abstraction workflows securely and offline.

---

## Assessment Context

This repository was built specifically as a Proof-of-Concept for the Generative AI / Agentic AI / Research Cotiviti Internship assessment. It aims to showcase an end-to-end understanding of clinical data pipelines, from multimodal OCR and local LLM extraction to HEDIS rule evaluation and FHIR standardization.

## Key Features

- **Multi-Modal Ingestion:** Supports `.txt`, `.pdf`, `.png`, `.jpg`, and multi-page `.tiff` files.
- **Dual-Channel OCR:** Uses `llama3.2-vision` for primary optical character recognition with a `tesseract` fallback for low-confidence reads.
- **GenAI Extraction:** Uses `mistral` (via Ollama) to structure raw text into patient demographics, lab names, values, units, and dates.
- **HEDIS Rules Engine:** Automatically evaluates extracted lab results (e.g., HbA1c) against predefined clinical compliance thresholds.
- **FHIR Standardization:** Converts the extracted and evaluated data into compliant FHIR `Observation` JSON resources.
- **Streamlit Dashboard:** Includes a modern web portal for Batch Processing, Document Queue management, Human-in-the-Loop (HITL) review, and data export.
- **100% Local & Secure:** All inference runs locally via Ollama, ensuring PHI never leaves the machine.

## Architecture

The system operates in a linear 6-stage pipeline:

1. **Ingestion:** Validates file types and integrity.
2. **OCR / Vision Processing:** Extracts text from images and PDFs. Splits multi-page TIFFs for comprehensive reading.
3. **LLM Extraction:** Parses the unstructured OCR output into a structured Pydantic schema.
4. **Validation:** Ensures data types and logical bounds are met.
5. **Rules Engine:** Runs the extracted data against HEDIS compliance measures.
6. **FHIR Output & Persist:** Generates the FHIR JSON and stores the provenance, status, and metrics in a local SQLite database.

## Quickstart

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

## Generating Sample Data

Need test data? The repository includes a robust synthetic data generator that creates noisy, realistic clinical documents (including corrupt files for testing error handling).

```bash
python generate_test_data.py
```
This will populate the `sample_data/` folder with a mix of PDFs, DOCX, TXT, and image files simulating different clinical scenarios (e.g., handwritten lab slips, discharge summaries).

## Repository Structure

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

## Path to Production

While this repository is a functional local POC, the core architecture is designed to be extensible. If an organization like Cotiviti were to adapt this for large-scale production, here are a few ways the system could evolve:

#### 1. Infrastructure & Orchestration
*   **Microservices:** The pipeline stages (Ingestion, OCR, Extraction, Rules, FHIR) can be decoupled into containerized microservices (e.g., Kubernetes). This allows independent scaling, like spinning up more OCR nodes to handle image-heavy batches.
*   **Event-Driven Ingestion:** Instead of synchronous batch processing, the system could tie into message brokers like Kafka or RabbitMQ. Documents dropped via SFTP or API would hit a topic and seamlessly feed the worker nodes.

#### 2. Model Hosting Strategies
*   **Hybrid Deployments:** Small, fast models (like `llama3.2-vision`) could run on-premise for triage and simple OCR. Highly complex or edge-case documents could be routed securely to managed, HIPAA-compliant private cloud models (like Azure OpenAI or AWS Bedrock).
*   **Privacy Guarantees:** By using pluggable backends, organizations can ensure PHI never crosses public internet boundaries, keeping everything within their VPC and compliant with BAAs.

#### 3. Interoperability
*   **Data Lake Integration:** The output layer can be wired to drop FHIR R4 JSON bundles directly into existing data warehouses (like Snowflake or Hadoop) for downstream analytics.
*   **API Gateways:** REST or GraphQL APIs could be exposed so existing EMR/EHR front-ends can request real-time, single-document abstractions.

#### 4. Extensibility
*   **Pluggable Models:** The LLM client abstraction makes it easy to swap models based on cost or accuracy (e.g., testing Claude 3.5 Sonnet against a fine-tuned internal model).
*   **Dynamic Rules Engine:** The Python-based rules engine could be extended with a UI, allowing clinical SMEs to define new HEDIS measures and thresholds without needing to write code.
*   **Custom NLP:** The pipeline could inject specialized Named Entity Recognition (NER) models for specific specialties (like Oncology) to improve the base LLM's accuracy.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
