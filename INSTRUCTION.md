# Docs2KG Pipeline — Setup & Usage Instructions

## Prerequisites

- **Python 3.13+**
- **pip** (comes with Python)

---

## 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/Docs2KG-2.git
cd Docs2KG-2
```

---

## 2. Create the Virtual Environment & Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate      # Linux/macOS
# .venv\Scripts\activate       # Windows

pip install -r requirements.txt
```

> **Note:** The `requirements.txt` includes all pinned dependencies (180 packages).
> If you only want the core packages, you can install them manually:
>
> ```bash
> pip install Docs2KG==0.3.5 pyvis reportlab
> ```
>
> The `llama_cpp` package is NOT required — all scripts mock it automatically.

---

## 3. Project Structure

```
Docs2KG-2/
├── config.yml                  # Docs2KG configuration (paths, API keys)
├── requirements.txt            # Pinned Python dependencies
├── generate_pdf.py             # Generate a simple sample PDF
├── generate_complex_pdf.py     # Generate a complex PDF with nested tables
├── run_pipeline.py             # Run the full pipeline (digitize → layout KG → NER)
├── run_cli.py                  # Wrapper to run Docs2KG CLI (mocks llama_cpp)
├── visualize_graph.py          # Generate interactive HTML graph visualization
├── data/
│   ├── input/                  # Place your PDF files here
│   ├── output/                 # Generated outputs (markdown, JSON, graph HTML)
│   └── ontology/
│       ├── ontology.json       # Entity types and relation types
│       └── entity_list.csv     # Known entities for NER matching
└── .gitignore
```

---

## 4. Running the Pipeline

### Step 1: Generate a sample PDF (optional)

If you don't have a PDF to test with:

```bash
.venv/bin/python generate_pdf.py             # simple document
.venv/bin/python generate_complex_pdf.py     # complex nested tables
```

This creates PDF files inside `data/input/`.

### Step 2: Run the full pipeline

```bash
.venv/bin/python run_pipeline.py                    # processes sample.pdf
.venv/bin/python run_pipeline.py complex_sample.pdf  # processes complex_sample.pdf
```

This will:
1. **Digitize** the PDF → Markdown (using Docling)
2. **Construct Layout KG** → JSON file with document structure
3. **Extract Entities** using NER SpaCy Matcher → populates `"entities"` arrays

Output is saved to: `data/output/projects/sample_project/layout/<filename>.json`

### Step 3: Visualize the graph

```bash
# Visualize ALL documents in the project
.venv/bin/python visualize_graph.py

# Visualize a SINGLE document
.venv/bin/python visualize_graph.py data/output/projects/sample_project/layout/complex_sample.json
```

Then serve the HTML locally and open it in your browser:

```bash
.venv/bin/python -m http.server 8888 --directory data/output/projects/sample_project/
# Open http://localhost:8888/graph.html
```

---

## 5. Customizing the Ontology

### Entity types and known entities

Edit `data/ontology/ontology.json` to define your entity and relation types:

```json
{
  "entity_types": ["Person", "Organization", "Department", "Project"],
  "relation_types": ["WorksFor", "Manages", "LeadsProject", "BelongsTo"]
}
```

Edit `data/ontology/entity_list.csv` to add known entities for NER matching:

```csv
entity,label
alice,Person
bob,Person
acme corp,Organization
engineering,Department
apollo project,Project
```

---

## 6. Using the Docs2KG CLI (Optional)

The `run_cli.py` script wraps the Docs2KG CLI with a `llama_cpp` mock so it works without compiling the C++ library:

```bash
# Example: start Neo4j via Docker (requires Docker on your system)
CONFIG_FILE=config.yml .venv/bin/python run_cli.py neo4j sample_project --mode docker_start

# Load graph data into Neo4j
CONFIG_FILE=config.yml .venv/bin/python run_cli.py neo4j sample_project --mode load
```

> **Note:** Neo4j commands require Docker or Podman running on your system.
> If you don't have Docker, use `visualize_graph.py` instead — it generates
> the exact same graph structure as the Neo4j loader without any database.

---

## 7. Graph Edge Types

The visualization (and Neo4j loader) produce the following edge types:

| Edge Type      | Meaning                                              |
|----------------|------------------------------------------------------|
| `CONTAINS`     | Structural hierarchy (File → Header → Paragraph)     |
| `NEXT`         | Sequential reading order between same-level siblings  |
| `HAS_ENTITY`   | A text block contains an extracted entity             |
| `RELATES_TO`   | Semantic relation between two entities                |

---

## 8. Human-in-the-Loop (Optional)

To add semantic relations between entities:

1. Upload your layout JSON to the [Docs2KG Web Interface](https://docs2kg.kaiaperth.com/)
2. Annotate relations in the editor (link entities and assign relation labels)
3. Download the updated JSON and replace your local file
4. Re-run `visualize_graph.py` to see the relations in the graph

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: llama_cpp` | Use `run_pipeline.py` or `run_cli.py` — they mock this automatically |
| `No entities extracted` | Check that `data/ontology/entity_list.csv` has entries matching your document |
| Graph HTML shows blank page | Serve via HTTP (`python -m http.server`) instead of opening as `file://` |
| Neo4j connection refused | Ensure Docker/Podman container is running and ports 7474/7687 are mapped |
