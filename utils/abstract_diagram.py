# utils/diagram.py
from __future__ import annotations

import importlib
from pathlib import Path

from diagrams import Diagram, Cluster
from diagrams.custom import Custom


def pick_icon_any(choices: list[tuple[str, list[str]]]):
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


# ---------------------------------------------------------------------
# Paper-safe, vendor-neutral, nicer icon palette
# ---------------------------------------------------------------------
PDF = pick_icon_any(
    [
        ("diagrams.generic.storage", ["Storage"]),
        ("diagrams.generic.storage", ["Disk"]),
    ]
)

Artifact = pick_icon_any(
    [
        ("diagrams.generic.storage", ["Storage"]),
        ("diagrams.generic.storage", ["Disk"]),
    ]
)

SQL = pick_icon_any(
    [
        ("diagrams.onprem.database", ["Postgresql", "Mysql", "Mongodb"]),
        ("diagrams.generic.database", ["SQL", "Database"]),
    ]
)

PythonStep = pick_icon_any(
    [
        ("diagrams.programming.language", ["Python"]),
        ("diagrams.onprem.compute", ["Server", "VM", "Baremetal"]),
        ("diagrams.generic.compute", ["Rack", "Server"]),
    ]
)

Service = pick_icon_any(
    [
        ("diagrams.onprem.compute", ["Server", "VM", "Baremetal"]),
        ("diagrams.generic.compute", ["Rack", "Server"]),
    ]
)

Orchestrator = pick_icon_any(
    [
        ("diagrams.onprem.workflow", ["Airflow", "Nifi"]),
    ]
)

Queue = pick_icon_any(
    [
        ("diagrams.onprem.queue", ["Rabbitmq", "Kafka"]),
    ]
)

Gate = pick_icon_any(
    [
        ("diagrams.generic.network", ["Firewall", "Router", "Switch"]),
    ]
)

Decision = pick_icon_any(
    [
        ("diagrams.generic.network", ["LoadBalancer", "Router", "Switch"]),
    ]
)

Analytics = pick_icon_any(
    [
        ("diagrams.onprem.analytics", ["Spark", "Flink"]),
        ("diagrams.generic.compute", ["Rack", "Server"]),
    ]
)

Report = pick_icon_any(
    [
        ("diagrams.onprem.analytics", ["Superset", "Spark"]),
        ("diagrams.generic.storage", ["Storage"]),
    ]
)


# ---------------------------------------------------------------------
# Custom icon: Mistral OCR
# ---------------------------------------------------------------------
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
MISTRAL_ICON = ASSETS_DIR / "mistral_logo.png"
if not MISTRAL_ICON.exists():
    raise FileNotFoundError(f"Missing icon: {MISTRAL_ICON}")


def MistralOCR(label):
    return Custom(label, MISTRAL_ICON.as_posix())


# ---------------------------------------------------------------------
# Styling for paper figures
# Tip: switch outformat="svg" for camera-ready figures
# ---------------------------------------------------------------------
COMMON_GRAPH_ATTR = {
    "splines": "spline",
    "pad": "0.60",
    "nodesep": "0.35",
    "ranksep": "0.55",
    "fontsize": "11",
    "bgcolor": "transparent",
}

COMMON_NODE_ATTR = {
    "fontsize": "10",
    "shape": "box",
    "style": "rounded",
}

COMMON_EDGE_ATTR = {
    "fontsize": "9",
    "arrowsize": "0.8",
}


# ---------------------------
# 1. INGESTION (COMPACT)
# ---------------------------
with Diagram(
    "PDF Corpus Processing and Annotation Flow",
    show=False,
    direction="LR",
    filename="output/charts_and_excels/pdf_corpus_flow_ingestion",
    outformat="png",
    graph_attr=COMMON_GRAPH_ATTR,
    node_attr=COMMON_NODE_ATTR,
    edge_attr=COMMON_EDGE_ATTR,
):
    with Cluster("1. Ingestion and Resume Logic"):
        ingest = PDF("Load PDF corpus\n+ read bytes")
        fingerprints = PythonStep("Fingerprint\n(SHA1 + page count)")
        validate = Decision("Valid PDF?")
        skip_bad = PythonStep("Skip invalid")

        encode = PythonStep("Encode\n(base64)")
        resume_idx = SQL("Resume index\n(SQL)")
        seen = Decision("Already processed?")
        skip_resume = PythonStep("Skip (resume)")
        to_chunking = Service("Proceed to\nchunking")

        ingest >> fingerprints >> validate
        validate >> skip_bad
        validate >> encode >> resume_idx >> seen
        seen >> skip_resume
        seen >> to_chunking


# ---------------------------
# 2. CHUNKING (COMPACT)
# ---------------------------
with Diagram(
    "PDF Corpus Processing and Annotation Flow",
    show=False,
    direction="LR",
    filename="output/charts_and_excels/pdf_corpus_flow_chunking",
    outformat="png",
    graph_attr=COMMON_GRAPH_ATTR,
    node_attr=COMMON_NODE_ATTR,
    edge_attr=COMMON_EDGE_ATTR,
):
    with Cluster("2. Chunking and Async Scheduling"):
        chunk_decision = Decision("Fits in one chunk?")
        single = PythonStep("Single submission")
        multi = PythonStep("Partition pages\ninto chunks")

        schedule = Orchestrator("Async scheduler")
        gate = Gate("Concurrency\n+ throttling")
        q = Queue("Work queue")
        dispatch = Service("Dispatch to OCR")

        to_chunking >> chunk_decision
        chunk_decision >> single >> schedule
        chunk_decision >> multi >> schedule
        schedule >> gate >> q >> dispatch


# ---------------------------
# 3. OCR + EXTRACTION (COMPACT)
# ---------------------------
with Diagram(
    "PDF Corpus Processing and Annotation Flow",
    show=False,
    direction="LR",
    filename="output/charts_and_excels/pdf_corpus_flow_ocr",
    outformat="png",
    graph_attr=COMMON_GRAPH_ATTR,
    node_attr=COMMON_NODE_ATTR,
    edge_attr=COMMON_EDGE_ATTR,
):
    with Cluster("3. Mistral OCR and Schema Extraction"):
        prep = PythonStep("Prepare requests\n+ schemas")
        rate = Gate("Rate-limit\n+ retries")
        ocr = MistralOCR("Mistral OCR\n(page chunks)")
        err = Decision("Error / limit?")
        backoff = PythonStep("Backoff\n+ retry")

        parse = PythonStep("Parse outputs\n+ evidence linking\n(captions/body/images)")
        chunk_payloads = SQL("Chunk payloads\n(SQL dicts)")

        dispatch >> prep >> rate >> ocr >> err
        err >> backoff >> rate
        err >> parse >> chunk_payloads


# ---------------------------
# 4–7. MERGE + OUTPUTS (COMPACT)
# ---------------------------
with Diagram(
    "PDF Corpus Processing and Annotation Flow",
    show=False,
    direction="LR",
    filename="output/charts_and_excels/pdf_corpus_flow_merging",
    outformat="png",
    graph_attr=COMMON_GRAPH_ATTR,
    node_attr=COMMON_NODE_ATTR,
    edge_attr=COMMON_EDGE_ATTR,
):
    with Cluster("4. Merge to Study-level"):
        collect = SQL("Collect chunks\n(SQL)")
        merge = PythonStep("Merge\n(scalars, lists,\n sentence evidence)")
        study = SQL("Study-level\nannotation")
        attach = Artifact("Attach metadata\n+ source key")

        chunk_payloads >> collect >> merge >> study >> attach

    with Cluster("5. Tabular Outputs"):
        tabular = Artifact("CSV + Parquet")
        dataset = SQL("Final dataset\n(schema-conforming)")
        attach >> tabular >> dataset

    with Cluster("6. Markdown Reconstruction"):
        md = Artifact(
            "Study markdown\n(text + captions + images)\n+ structured summary"
        )
        attach >> md

    with Cluster("7. Post-processing"):
        post = Analytics("Aggregation\n+ stratification\n+ value counts")
        excel = Report("Excel workbook\n+ distributions")
        dataset >> post >> excel
