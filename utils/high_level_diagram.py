# utils/mini_pipeline_diagram.py
from __future__ import annotations

import importlib
from diagrams import Diagram, Edge


def pick_icon_any(choices: list[tuple[str, list[str]]]):
    """
    Try (module_path, [ClassCandidates...]) in order.
    Returns the first class that exists.
    """
    last_err = None
    for module_path, candidates in choices:
        try:
            mod = importlib.import_module(module_path)
        except Exception as e:
            last_err = e
            continue

        for name in candidates:
            if hasattr(mod, name):
                return getattr(mod, name)

        available = sorted([x for x in dir(mod) if x[:1].isupper()])
        last_err = ImportError(
            f"None of {candidates} exist in {module_path}. Available: {available}"
        )
    raise ImportError(f"Could not resolve icon. Last error: {last_err}")


# ---------------------------
# Paper-safe, vendor-neutral icons (no AWS/GCP/Azure)
# ---------------------------
# PDF / file artifact
PDF = pick_icon_any(
    [
        ("diagrams.generic.storage", ["Storage"]),
        ("diagrams.generic.storage", ["Disk"]),
    ]
)

# Pipeline core (Python)
Python = pick_icon_any(
    [
        ("diagrams.programming.language", ["Python"]),
        ("diagrams.onprem.compute", ["Server", "VM", "Baremetal"]),
        ("diagrams.generic.compute", ["Rack", "Server"]),
    ]
)

# Structured data output (SQL-ish / dataset)
Structured = pick_icon_any(
    [
        ("diagrams.generic.database", ["SQL", "Database"]),
        ("diagrams.onprem.database", ["Postgresql", "Mysql"]),
    ]
)

# Excel report output (best neutral “file/report” icon available)
Excel = pick_icon_any(
    [
        ("diagrams.onprem.analytics", ["Superset"]),  # if present, looks like reporting
        ("diagrams.generic.storage", ["Storage"]),
        ("diagrams.generic.storage", ["Disk"]),
    ]
)


COMMON_GRAPH_ATTR = {
    "splines": "spline",  # smooth curves like your screenshot
    "pad": "0.55",
    "nodesep": "0.55",
    "ranksep": "0.85",
    "fontsize": "12",
    "bgcolor": "transparent",
}

COMMON_NODE_ATTR = {
    "fontsize": "12",
    "shape": "box",
    "style": "rounded",
}

COMMON_EDGE_ATTR = {
    "arrowsize": "0.9",
    "penwidth": "2.0",
}


def main():
    ink = "#1f4e79"

    with Diagram(
        "Schema-Governed Pipeline Overview",
        show=False,
        direction="LR",
        filename="output/charts_and_excels/schema_governed_overview",
        outformat="png",  # change to "svg" for paper-quality vector output
        graph_attr=COMMON_GRAPH_ATTR,
        node_attr=COMMON_NODE_ATTR,
        edge_attr=COMMON_EDGE_ATTR,
    ):
        pdf = PDF("PDF")

        # Keep it as one “pipeline box” like your screenshot.
        # The Python icon helps communicate implementation.
        pipeline = Python("Schema-Governed\nPipeline\n(Python + Mistral OCR)")

        structured = Structured("Structured Data\n(CSV/Parquet)")
        excel = Excel("Excel Report\n(.xlsx)")

        # Edges (curved automatically because splines=spline)
        pdf >> Edge(color=ink) >> pipeline

        # Two outgoing curved-ish connections (Graphviz chooses routing)
        pipeline >> Edge(color=ink) >> structured
        pipeline >> Edge(color=ink) >> excel


if __name__ == "__main__":
    main()
