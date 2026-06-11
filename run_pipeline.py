import os
import sys
import json
from pathlib import Path
from unittest.mock import MagicMock

# Mock llama_cpp module to bypass the heavy local C++ dependency
sys.modules['llama_cpp'] = MagicMock()

# Set the environment variable for the configuration file to the current directory
os.environ["CONFIG_FILE"] = str(Path.cwd() / "config.yml")

# Now import the Docs2KG components
from Docs2KG.digitization.image.pdf_docling import PDFDocling
from Docs2KG.kg_construction.layout_kg.layout_kg import LayoutKGConstruction
from Docs2KG.kg_construction.semantic_kg.ner.ner_spacy_match import NERSpacyMatcher
from Docs2KG.utils.config import PROJECT_CONFIG

if __name__ == "__main__":
    # Get PDF filename from CLI argument or default to "sample.pdf"
    pdf_name = sys.argv[1] if len(sys.argv) > 1 else "sample.pdf"
    
    # 1. Ingest/Digitize PDF to Markdown format using PDFDocling (which uses Docling under the hood)
    pdf_path = PROJECT_CONFIG.data.input_dir / pdf_name
    print(f"--- 1. Digitizing PDF: {pdf_path} ---")
    processor = PDFDocling(file_path=pdf_path)
    markdown_path = processor.process()
    print(f"Generated Markdown at: {markdown_path}\n")

    # 2. Construct Layout Knowledge Graph from the digitized output
    project_id = "sample_project"
    print(f"--- 2. Constructing Layout KG for Project: {project_id} ---")
    layout_kg_construction = LayoutKGConstruction(project_id)
    
    # Read the generated markdown and feed it to layout graph builder
    md_content = markdown_path.read_text(encoding="utf-8")
    layout_kg_construction.construct(
        [{"content": md_content, "filename": markdown_path.stem}]
    )
    
    layout_json_path = (
        PROJECT_CONFIG.data.output_dir 
        / "projects" 
        / project_id 
        / "layout" 
        / f"{markdown_path.stem}.json"
    )
    print(f"Generated Layout KG JSON at: {layout_json_path}\n")

    # 3. Entity Extraction using NER Spacy Matcher
    print("--- 3. Running Semantic NER Entity Extraction ---")
    
    # Monkeypatch the buggy validation method of the library at the class level before initializing.
    # The original _validate_match returns False if adjacent tokens are alphabetic (which excludes
    # almost all matches next to other words in a sentence).
    NERSpacyMatcher._validate_match = staticmethod(lambda doc, start, end: True)
    print("Patched NERSpacyMatcher._validate_match to bypass token adjacency check bug.")
    
    entity_extractor = NERSpacyMatcher(project_id)
    
    # We monkeypatch/mock the LLM judge to always return True.
    # This allows us to run the matcher locally without needing Ollama or OpenAI APIs.
    if hasattr(entity_extractor, "llm_judgement_agent"):
        entity_extractor.llm_judgement_agent.judge = lambda ner, ner_type, text: True
        print("Mocked LLM judge to run locally without external LLM API dependencies.")
        
    entity_extractor.construct_kg([layout_json_path])
    print("Semantic KG construction completed!\n")
    
    # 4. Display the resulting Knowledge Graph JSON structure
    if layout_json_path.exists():
        with open(layout_json_path, "r", encoding="utf-8") as f:
            kg_data = json.load(f)
            print("--- Resulting KG JSON Content ---")
            print(json.dumps(kg_data, indent=2))
