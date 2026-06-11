"""
Docs2KG Graph Visualizer — Replicates the Neo4j loader logic locally.

This script reads the layout JSON files and the layout schema, then builds
the exact same graph that the Neo4jTransformer would create, including:

  1. File node (root)
  2. Layout nodes (H1–H6, P, TABLE, TR, TD, TH, etc.)
  3. Entity nodes (Person, Organization, Department, Project, etc.)
  4. CONTAINS edges   — structural hierarchy (File→Header→Paragraph, Table→TR→TD)
  5. NEXT edges        — sequential same-level siblings
  6. HAS_ENTITY edges  — layout block → extracted entity
  7. RELATES_TO edges  — semantic relations between entities (from "relations" array)

After building the graph it also merges duplicate entities (same text + label),
exactly as Neo4jTransformer.merge_entities() does.

Usage:
    .venv/bin/python visualize_graph.py [layout_json_path]

    If no argument is given, it processes all JSON files in the project layout dir.
    The output is an interactive HTML file opened in your default browser.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

from pyvis.network import Network

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PROJECT_ID = "sample_project"
DATA_OUTPUT = Path("data/output")
LAYOUT_DIR = DATA_OUTPUT / "projects" / PROJECT_ID / "layout"
SCHEMA_PATH = LAYOUT_DIR / "schema.json"
OUTPUT_HTML = DATA_OUTPUT / "projects" / PROJECT_ID / "graph.html"

# Color palette
COLORS = {
    # Layout nodes
    "File": "#1a1a2e",
    "H1": "#16213e",
    "H2": "#0f3460",
    "H3": "#1a508b",
    "H4": "#2c6fbb",
    "H5": "#4a90d9",
    "H6": "#6fb1fc",
    "P": "#3a506b",
    "T": "#2d6a4f",
    "TABLE": "#2d6a4f",
    "TR": "#40916c",
    "TD": "#52b788",
    "TH": "#74c69d",
    "LI": "#5a189a",
    "OL": "#7b2cbf",
    "UL": "#9d4edd",
    "QUOTE": "#e07a5f",
    "CODE": "#f2cc8f",
    # Entity nodes
    "Person": "#e63946",
    "Organization": "#f4a261",
    "Department": "#2a9d8f",
    "Project": "#e9c46a",
    "Entity": "#adb5bd",  # fallback
}

# Edge colors
EDGE_COLORS = {
    "CONTAINS": "#555555",
    "NEXT": "#888888",
    "HAS_ENTITY": "#e76f51",
    "RELATES_TO": "#264653",
}

# Node shapes
SHAPES = {
    "File": "diamond",
    "H1": "box",
    "H2": "box",
    "H3": "box",
    "H4": "box",
    "H5": "box",
    "H6": "box",
    "P": "ellipse",
    "T": "triangle",
    "TABLE": "triangle",
    "TR": "triangle",
    "TD": "dot",
    "TH": "dot",
    "LI": "dot",
    "OL": "dot",
    "UL": "dot",
    "QUOTE": "square",
    "CODE": "square",
}


def sanitize_label(label: str) -> str:
    """Replicate Neo4jTransformer.sanitize_label"""
    sanitized = label.replace(" ", "_").replace("-", "_").upper()
    if sanitized and sanitized[0].isdigit():
        leading_nums = ""
        i = 0
        while i < len(sanitized) and (sanitized[i].isdigit() or sanitized[i] == "_"):
            leading_nums += sanitized[i]
            i += 1
        return f"{sanitized[i:]}{leading_nums}" if i < len(sanitized) else sanitized
    return sanitized


def truncate(text: str, max_len: int = 40) -> str:
    """Truncate text for display."""
    text = text.replace("\n", " ").strip()
    return text[:max_len] + "…" if len(text) > max_len else text


# ---------------------------------------------------------------------------
# Graph builder — mirrors Neo4jTransformer logic
# ---------------------------------------------------------------------------
class GraphBuilder:
    def __init__(self, project_id: str, schema: Dict):
        self.project_id = project_id
        self.schema = schema
        self.header_stack: List[tuple] = []  # [(label, id), ...]
        self.nodes: Dict[str, dict] = {}     # id -> {label, text, type, ...}
        self.edges: List[dict] = []          # [{source, target, type}, ...]

    # -- Node helpers -------------------------------------------------------
    def add_node(self, node_id: str, label: str, text: str, node_type: str = "layout", **extra):
        self.nodes[node_id] = {
            "id": node_id,
            "label": label,
            "text": text,
            "type": node_type,
            **extra,
        }

    def add_edge(self, source: str, target: str, edge_type: str, **extra):
        self.edges.append({"source": source, "target": target, "type": edge_type, **extra})

    # -- Hierarchy logic (mirrors _find_parent_node) -------------------------
    def _find_parent_node(self, current_item: Dict, previous_items: List[Dict], file_id: str) -> str:
        current_label = current_item["label"]

        # Header hierarchy
        if current_label.startswith("H"):
            current_level = int(current_label[1])
            while self.header_stack and int(self.header_stack[-1][0][1]) >= current_level:
                self.header_stack.pop()
            if not self.header_stack:
                return file_id  # attach to File
            return self.header_stack[-1][1]

        # Schema-based containment
        if previous_items:
            prev_item = previous_items[-1]
            prev_label = prev_item["label"]
            if prev_label in self.schema and current_label in self.schema[prev_label]:
                return prev_item["id"]
            if self.header_stack:
                return self.header_stack[-1][1]

        return file_id

    # -- Main load (mirrors transform_and_load + _create_layout) -------------
    def load_layout_json(self, layout_json: dict):
        filename = layout_json["filename"]
        file_id = f"{self.project_id}_{filename}"

        # 1. File node
        self.add_node(file_id, "File", filename, node_type="file")

        # Reset header stack per file
        self.header_stack = []
        processed_items: List[Dict] = []

        data = layout_json["data"]

        # 2. Layout nodes + CONTAINS + NEXT edges
        for idx, item in enumerate(data):
            item_id = item["id"]
            label = sanitize_label(item.get("label", "Item"))
            text = item.get("text", "")

            self.add_node(item_id, label, text, node_type="layout", sequence=idx)

            # CONTAINS edge
            parent_id = self._find_parent_node(item, processed_items, file_id)
            self.add_edge(parent_id, item_id, "CONTAINS")

            # Header stack update
            if label.startswith("H"):
                self.header_stack.append((label, item_id))

            # NEXT edge (same-label sequential siblings)
            if processed_items:
                prev = processed_items[-1]
                if prev["label"] == item["label"]:
                    self.add_edge(prev["id"], item_id, "NEXT")

            processed_items.append(item)

        # 3. Entity nodes + HAS_ENTITY edges
        for item in data:
            for entity in item.get("entities", []):
                ent_id = entity.get("id", "")
                ent_label = sanitize_label(entity.get("label", "Entity"))
                ent_text = entity.get("text", "")
                self.add_node(
                    ent_id, ent_label, ent_text,
                    node_type="entity",
                    confidence=entity.get("confidence", 0.0),
                    method=entity.get("method", ""),
                )
                self.add_edge(item["id"], ent_id, "HAS_ENTITY")

        # 4. Relation edges (RELATES_TO)
        for item in data:
            for relation in item.get("relations", []):
                rel_type = relation.get("type", "RELATES_TO")
                if "source_id" in relation and "target_id" in relation:
                    self.add_edge(
                        relation["source_id"],
                        relation["target_id"],
                        "RELATES_TO",
                        rel_label=rel_type,
                    )

    # -- Entity merging (mirrors merge_entities) -----------------------------
    def merge_entities(self):
        """Merge duplicate entity nodes with same (text, label)."""
        # Group entities by (text_lower, label)
        groups: Dict[tuple, List[str]] = defaultdict(list)
        for node_id, node in self.nodes.items():
            if node["type"] == "entity":
                key = (node["text"].lower(), node["label"])
                groups[key].append(node_id)

        for key, ids in groups.items():
            if len(ids) <= 1:
                continue

            primary_id = ids[0]
            for dup_id in ids[1:]:
                # Redirect all edges pointing to/from dup to primary
                for edge in self.edges:
                    if edge["target"] == dup_id:
                        edge["target"] = primary_id
                    if edge["source"] == dup_id:
                        edge["source"] = primary_id

                # Remove dup node
                del self.nodes[dup_id]

        # Remove self-loops created by merge
        self.edges = [e for e in self.edges if e["source"] != e["target"]]

        # Remove duplicate edges
        seen = set()
        unique_edges = []
        for e in self.edges:
            key = (e["source"], e["target"], e["type"])
            if key not in seen:
                seen.add(key)
                unique_edges.append(e)
        self.edges = unique_edges


# ---------------------------------------------------------------------------
# Visualization
# ---------------------------------------------------------------------------
def build_pyvis(builder: GraphBuilder) -> Network:
    net = Network(
        height="900px",
        width="100%",
        bgcolor="#1a1a2e",
        font_color="#e0e0e0",
        directed=True,
        cdn_resources="remote",
    )

    # Use a simpler physics config that works reliably
    net.barnes_hut(
        gravity=-8000,
        central_gravity=0.3,
        spring_length=200,
        spring_strength=0.04,
        damping=0.5,
    )

    # Add nodes
    for node_id, node in builder.nodes.items():
        label = node["label"]
        text = node["text"]
        display_label = f"[{label}]\n{truncate(text, 25)}" if text else f"[{label}]"
        title_lines = [
            f"<b>Type:</b> {label}",
            f"<b>Text:</b> {text[:200]}",
            f"<b>ID:</b> {node_id}",
        ]
        if node["type"] == "entity":
            title_lines.append(f"<b>Method:</b> {node.get('method', 'N/A')}")
            title_lines.append(f"<b>Confidence:</b> {node.get('confidence', 'N/A')}")

        color = COLORS.get(label, COLORS.get("Entity", "#adb5bd"))

        # Size by type
        if node["type"] == "file":
            size = 40
        elif node["type"] == "entity":
            size = 25
        elif label.startswith("H"):
            size = 30
        else:
            size = 18

        shape = SHAPES.get(label, "dot") if node["type"] != "entity" else "star"

        net.add_node(
            node_id,
            label=display_label,
            title="<br>".join(title_lines),
            color=color,
            size=size,
            shape=shape,
            group=label,
        )

    # Add edges
    for edge in builder.edges:
        edge_type = edge["type"]
        edge_color = EDGE_COLORS.get(edge_type, "#999999")
        edge_label = edge.get("rel_label", edge_type)

        # Style by type
        if edge_type == "NEXT":
            dashes = True
            width = 1
        elif edge_type == "HAS_ENTITY":
            dashes = False
            width = 2
        elif edge_type == "RELATES_TO":
            dashes = False
            width = 3
        else:  # CONTAINS
            dashes = False
            width = 1.5

        net.add_edge(
            edge["source"],
            edge["target"],
            title=edge_label,
            label=edge_label if edge_type in ("RELATES_TO",) else "",
            color=edge_color,
            width=width,
            dashes=dashes,
        )

    return net


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    # Load schema
    if not SCHEMA_PATH.exists():
        print(f"Error: Schema not found at {SCHEMA_PATH}")
        sys.exit(1)

    with open(SCHEMA_PATH, "r") as f:
        schema = json.load(f)

    builder = GraphBuilder(PROJECT_ID, schema)

    # Determine which JSON files to process
    if len(sys.argv) > 1:
        json_files = [Path(sys.argv[1])]
    else:
        json_files = sorted(LAYOUT_DIR.glob("*.json"))
        json_files = [f for f in json_files if f.name != "schema.json"]

    if not json_files:
        print(f"No layout JSON files found in {LAYOUT_DIR}")
        sys.exit(1)

    for json_file in json_files:
        print(f"Loading: {json_file.name}")
        with open(json_file, "r", encoding="utf-8") as f:
            layout_json = json.load(f)
        builder.load_layout_json(layout_json)

    # Merge duplicate entities (same as Neo4j pipeline)
    builder.merge_entities()

    # Stats
    node_types = defaultdict(int)
    for n in builder.nodes.values():
        node_types[n["type"]] += 1
    edge_types = defaultdict(int)
    for e in builder.edges:
        edge_types[e["type"]] += 1

    print(f"\n--- Graph Statistics ---")
    print(f"Total nodes: {len(builder.nodes)}")
    for t, c in sorted(node_types.items()):
        print(f"  {t}: {c}")
    print(f"Total edges: {len(builder.edges)}")
    for t, c in sorted(edge_types.items()):
        print(f"  {t}: {c}")

    # Build and save visualization
    net = build_pyvis(builder)
    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    net.save_graph(str(OUTPUT_HTML))
    print(f"\nGraph saved to: {OUTPUT_HTML}")
    print(f"Open it in your browser: file://{OUTPUT_HTML.resolve()}")


if __name__ == "__main__":
    main()
