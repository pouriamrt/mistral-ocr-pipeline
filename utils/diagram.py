# utils/diagram.py
from __future__ import annotations

import importlib
from pathlib import Path

from diagrams import Diagram, Cluster
from diagrams.custom import Custom


def pick_icon_any(choices: list[tuple[str, list[str]]]):
    """
    Try (module_path, [ClassCandidates...]) in order.
    Returns the first class that exists.

    This keeps the diagram code portable across diagrams versions.
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


# ---------------------------------------------------------------------
# Paper-safe, vendor-neutral, nicer icon palette
# (no AWS/GCP/Azure). Uses recognizable on-prem + programming icons.
# ---------------------------------------------------------------------

# PDFs / documents / artifacts (prefer "Document" style icons if available)
PDF = pick_icon_any(
    [
        ("diagrams.onprem.client", ["User"]),  # fallback if some sets are missing
        ("diagrams.generic.storage", ["Storage"]),
        ("diagrams.generic.storage", ["Disk"]),
    ]
)

# A more "document-like" artifact icon for markdown/excel outputs
Artifact = pick_icon_any(
    [
        ("diagrams.generic.storage", ["Storage"]),
        ("diagrams.generic.storage", ["Disk"]),
    ]
)

# Structured storage / index / dataset (prefer richer DB icons if present)
SQL = pick_icon_any(
    [
        ("diagrams.onprem.database", ["Postgresql", "Mysql", "Mongodb"]),
        ("diagrams.generic.database", ["SQL", "Database"]),
    ]
)

# Python execution blocks (prefer Python icon, else compute/server)
PythonStep = pick_icon_any(
    [
        ("diagrams.programming.language", ["Python"]),
        ("diagrams.onprem.compute", ["Server", "VM", "Baremetal"]),
        ("diagrams.generic.compute", ["Rack", "Server"]),
    ]
)

# Chunking service / OCR service (prefer app/server look)
Service = pick_icon_any(
    [
        ("diagrams.onprem.compute", ["Server", "VM", "Baremetal"]),
        ("diagrams.generic.compute", ["Rack", "Server"]),
    ]
)

# Orchestration / async scheduling (prefer Airflow, else Nifi)
Orchestrator = pick_icon_any(
    [
        ("diagrams.onprem.workflow", ["Airflow", "Nifi"]),
    ]
)

# Queue / buffering (prefer RabbitMQ, else Kafka)
Queue = pick_icon_any(
    [
        ("diagrams.onprem.queue", ["Rabbitmq", "Kafka"]),
    ]
)

# Rate limiting / concurrency control (use network/security-style gate icons)
Gate = pick_icon_any(
    [
        ("diagrams.generic.network", ["Firewall", "Router", "Switch"]),
    ]
)

# "Decision" proxy (closest: load balancer/router/switch)
Decision = pick_icon_any(
    [
        ("diagrams.generic.network", ["LoadBalancer", "Router", "Switch"]),
    ]
)

# Analytics / aggregation stage (prefer Spark/Flink)
Analytics = pick_icon_any(
    [
        ("diagrams.onprem.analytics", ["Spark", "Flink"]),
        ("diagrams.generic.compute", ["Rack", "Server"]),
    ]
)

# Observability / reporting (optional but makes figure nicer)
Report = pick_icon_any(
    [
        ("diagrams.onprem.analytics", ["Superset"]),
        ("diagrams.onprem.analytics", ["Spark"]),
        ("diagrams.generic.storage", ["Storage"]),
    ]
)

# ---------------------------------------------------------------------
# Custom icon: Mistral OCR (paper-appropriate)
# ---------------------------------------------------------------------
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
MISTRAL_ICON = ASSETS_DIR / "mistral_logo.png"

if not MISTRAL_ICON.exists():
    raise FileNotFoundError(f"Missing icon: {MISTRAL_ICON}")


# Graphviz is happier with forward slashes even on Windows.
def MistralOCR(label):
    return Custom(label, MISTRAL_ICON.as_posix())


# ---------------------------------------------------------------------
# Styling for paper figures (clean, neutral, crisp)
# Tip: use outformat="svg" for publication quality
# ---------------------------------------------------------------------
COMMON_GRAPH_ATTR = {
    "splines": "spline",
    "pad": "0.65",
    "nodesep": "0.50",
    "ranksep": "0.80",
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
# 1. INGESTION
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
        discover = PDF("Discover\nPDF corpus")
        readpdf = PDF("Read\nPDF bytes")

        sha1 = PythonStep("SHA1 hash\n(Python)")
        pagecount = PythonStep("Page count\n(Python)")

        valid = Decision("Page count\nvalid?")
        skip_invalid = PythonStep("Skip\ninvalid PDF")

        base64encode = PythonStep("Base64 encode\n(Python)")
        check_index = SQL("Processed index\n(SQL)")
        key_present = Decision("Source key\npresent?")

        skip_resume = PythonStep("Resume mode:\nskip PDF")
        proceed_chunk = Service("Proceed to\npage chunking")

        discover >> readpdf >> sha1 >> pagecount >> valid
        valid >> skip_invalid
        valid >> base64encode >> check_index >> key_present
        key_present >> skip_resume
        key_present >> proceed_chunk


# ---------------------------
# 2. CHUNKING
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
    with Cluster("2. Page Chunking and Async Scheduling"):
        fit_one = Decision("Pages fit in\none chunk?")
        single_chunk = PythonStep("Single-chunk\nsubmission")
        multi_chunk = PythonStep("Partition into\npage chunks")

        async_task = Orchestrator("Async\nscheduler")
        semaphore = Gate("Concurrency\nsemaphore")
        queue = Queue("Work\nqueue")
        send_ocr = Service("Dispatch\nto OCR layer")

        proceed_chunk >> fit_one
        fit_one >> single_chunk >> async_task
        fit_one >> multi_chunk >> async_task
        async_task >> semaphore >> queue >> send_ocr


# ---------------------------
# 3. OCR + SCHEMA EXTRACTION
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
    with Cluster("3. Mistral OCR and Schema-constrained Extraction"):
        rate_init = Gate("Retry policy\n+ rate control")
        payload_list = Artifact(
            "Schema payloads\n(Metadata, Population,\nMethods, Outcomes,\nDiagnostics)"
        )
        prep_request = PythonStep("Prepare OCR\nrequests")

        limiter = Gate("Rate limiter")
        mistral_ocr = MistralOCR("Mistral OCR\n(page-level OCR)")

        rate_or_error = Decision("Rate limit\nor error?")
        backoff = PythonStep("Exponential\nbackoff + retry")
        ocr_resp = Artifact("OCR response")

        caption_detect = PythonStep("Detect figure\ncaptions")
        caption_chunk = PythonStep("Caption as\nsemantic chunk")
        body_extract = PythonStep("Extract body\ntext")
        image_extract = PythonStep("Extract image\nregions")

        parse_anno = PythonStep("Schema-constrained\nparsing")
        prep_md = PythonStep("Prepare image info\nfor markdown")
        chunk_dicts = SQL("Chunk-level\npayload dicts")

        send_ocr >> rate_init >> payload_list >> prep_request >> limiter >> mistral_ocr
        mistral_ocr >> rate_or_error
        rate_or_error >> backoff >> limiter
        rate_or_error >> ocr_resp

        ocr_resp >> caption_detect >> caption_chunk >> parse_anno
        ocr_resp >> body_extract >> parse_anno
        ocr_resp >> image_extract >> prep_md

        parse_anno >> chunk_dicts
        prep_md >> chunk_dicts


# ---------------------------
# 4. MERGING + 5/6/7 OUTPUTS
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
    # 4. MERGING
    with Cluster("4. Merging into Study-level Records"):
        collect = SQL("Collect payloads\nacross chunks")
        merge_scalar = PythonStep("Merge scalar\nfields")
        merge_list = PythonStep("Merge list\nfields")
        merge_sent = PythonStep("Merge sentence-\nlevel evidence")
        study_annotation = SQL("Study-level\nannotation")
        integrate = PythonStep("Integrate all\npayloads")
        attach_meta = Artifact("Attach source key\n+ metadata")

        chunk_dicts >> collect
        collect >> merge_scalar >> study_annotation
        collect >> merge_list >> study_annotation
        collect >> merge_sent >> study_annotation
        study_annotation >> integrate >> attach_meta

    # 5. TABULAR OUTPUT
    with Cluster("5. Tabular Output"):
        csv_out = Artifact("CSV output")
        pq_out = Artifact("Parquet output")
        dataset = SQL("Schema-conforming\nannotation dataset")

        attach_meta >> csv_out >> dataset
        attach_meta >> pq_out >> dataset

    # 6. MARKDOWN + MULTIMODAL
    with Cluster("6. Markdown and Multimodal Reconstruction"):
        md_build = PythonStep("Build study-level\nmarkdown")
        md_summary = Artifact("Render structured\nannotation summary")
        md_body = Artifact("Render OCR text\n+ captions")
        md_inline = Artifact("Inline images\n+ descriptions")
        md_final = Artifact("Markdown for QA\nand curation")

        attach_meta >> md_build
        md_build >> md_summary >> md_final
        md_build >> md_body >> md_final
        md_build >> md_inline >> md_final

    # 7. POST-PROCESSING
    with Cluster("7. Post-processing and Aggregation"):
        load_valid = SQL("Load validated\nannotations")
        detect_lists = PythonStep("Detect list-like\nfields")
        stratified = Analytics("Build stratified\nvariables")
        value_counts = Analytics("Compute value\ncounts")
        export_excel = Report("Export Excel\nworkbook")
        dist_summary = Report("Distributional\nsummaries")

        (
            dataset
            >> load_valid
            >> detect_lists
            >> stratified
            >> value_counts
            >> export_excel
            >> dist_summary
        )
