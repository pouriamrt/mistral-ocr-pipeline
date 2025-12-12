# diagram.py
from diagrams import Diagram, Cluster
from diagrams.generic.compute import Rack as Step
from diagrams.generic.storage import Storage as Data
from diagrams.generic.database import SQL as Table
from diagrams.generic.network import Firewall as Decision

with Diagram(
    "PDF Corpus Processing and Annotation Flow",
    show=False,
    direction="LR",
    filename="output/charts_and_excels/pdf_corpus_flow_ingestion",
    outformat="png",
    graph_attr={
        "splines": "spline",
        "pad": "0.5",
        "nodesep": "0.4",
        "ranksep": "0.7",
        "fontsize": "10",
    },
):
    # ---------------------------
    # 1. INGESTION
    # ---------------------------
    with Cluster("1. Ingestion and Resume Logic"):
        discover = Step("Discover\nPDF corpus")
        readpdf = Step("Read\nPDF bytes")
        sha1 = Step("Compute\nSHA1 hash")
        pagecount = Step("Compute\npage count")

        valid = Decision("Page count\nvalid?")
        skip_invalid = Step("Skip\ninvalid PDF")

        base64encode = Step("Encode PDF\nas base64")
        check_index = Table("Check\nprocessed index")
        key_present = Decision("Source key\npresent?")

        skip_resume = Step("Skip PDF\n(resume mode)")
        proceed_chunk = Step("Proceed to\npage chunking")

        discover >> readpdf >> sha1 >> pagecount >> valid
        valid >> skip_invalid
        valid >> base64encode
        base64encode >> check_index >> key_present
        key_present >> skip_resume
        key_present >> proceed_chunk

with Diagram(
    "PDF Corpus Processing and Annotation Flow",
    show=False,
    direction="LR",
    filename="output/charts_and_excels/pdf_corpus_flow_chunking",
    outformat="png",
    graph_attr={
        "splines": "spline",
        "pad": "0.5",
        "nodesep": "0.4",
        "ranksep": "0.7",
        "fontsize": "10",
    },
):
    # ---------------------------
    # 2. CHUNKING
    # ---------------------------
    with Cluster("2. Page Chunking and Async Scheduling"):
        fit_one = Decision("Pages fit in\none chunk?")
        single_chunk = Step("Single-chunk\nsubmission")
        multi_chunk = Step("Partition into\npage chunks")

        async_task = Step("Create\nasync task")
        semaphore = Step("Acquire\nsemaphore")
        send_ocr = Step("Send to\nOCR layer")

        proceed_chunk >> fit_one
        fit_one >> single_chunk
        fit_one >> multi_chunk
        single_chunk >> async_task
        multi_chunk >> async_task
        async_task >> semaphore >> send_ocr

with Diagram(
    "PDF Corpus Processing and Annotation Flow",
    show=False,
    direction="LR",
    filename="output/charts_and_excels/pdf_corpus_flow_ocr",
    outformat="png",
    graph_attr={
        "splines": "spline",
        "pad": "0.5",
        "nodesep": "0.4",
        "ranksep": "0.7",
        "fontsize": "10",
    },
):
    # ---------------------------
    # 3. OCR + SCHEMA EXTRACTION
    # ---------------------------
    with Cluster("3. Mistral OCR and Schema-constrained Extraction"):
        rate_init = Step("Init rate limiter\n+ retry policy")
        payload_list = Step(
            "Define payload list\n(Meta, Pop., Methods,\nOutcomes, Diagnostics)"
        )
        prep_request = Step("Prepare OCR\nrequests")
        limiter = Step("Apply rate\nlimiter")
        call_mistral = Step("Call Mistral OCR\non page chunks")

        rate_or_error = Decision("Rate limit\nor error?")
        backoff = Step("Exponential\nbackoff + retry")
        ocr_resp = Data("Receive OCR\nresponse")

        caption_detect = Step("Detect figure\ncaptions")
        caption_chunk = Step("Treat caption as\nsemantic chunk")
        body_extract = Step("Extract body\ntext")
        image_extract = Step("Extract image\nregions")

        parse_anno = Data("Parse annotations\ninto payload dict")
        prep_md = Data("Prepare image info\nfor markdown")
        chunk_dicts = Data("Chunk-level\npayload dicts")

        send_ocr >> rate_init >> payload_list >> prep_request >> limiter >> call_mistral
        call_mistral >> rate_or_error
        rate_or_error >> backoff >> limiter
        rate_or_error >> ocr_resp

        ocr_resp >> caption_detect >> caption_chunk >> parse_anno
        ocr_resp >> body_extract >> parse_anno
        ocr_resp >> image_extract >> prep_md

        parse_anno >> chunk_dicts
        prep_md >> chunk_dicts

with Diagram(
    "PDF Corpus Processing and Annotation Flow",
    show=False,
    direction="LR",
    filename="output/charts_and_excels/pdf_corpus_flow_merging",
    outformat="png",
    graph_attr={
        "splines": "spline",
        "pad": "0.5",
        "nodesep": "0.4",
        "ranksep": "0.7",
        "fontsize": "10",
    },
):
    # ---------------------------
    # 4. MERGING
    # ---------------------------
    with Cluster("4. Merging into Study-level Records"):
        collect = Data("Collect payloads\nacross chunks")
        merge_scalar = Step("Merge scalar\nfields")
        merge_list = Step("Merge list\nfields")
        merge_sent = Step("Merge sentence-\nlevel evidence")
        study_annotation = Data("Study-level\nannotation")
        integrate = Step("Integrate all\npayloads")
        attach_meta = Data("Attach source key\n+ metadata")

        chunk_dicts >> collect
        collect >> merge_scalar >> study_annotation
        collect >> merge_list >> study_annotation
        collect >> merge_sent >> study_annotation
        study_annotation >> integrate >> attach_meta

    # ---------------------------
    # 5. TABULAR OUTPUT
    # ---------------------------
    with Cluster("5. Tabular Output"):
        csv_out = Table("Append record\nto CSV")
        pq_out = Table("Append record\nto Parquet")
        dataset = Table("Schema-conforming\nannotation dataset")

        attach_meta >> csv_out >> dataset
        attach_meta >> pq_out >> dataset

    # ---------------------------
    # 6. MARKDOWN + MULTIMODAL
    # ---------------------------
    with Cluster("6. Markdown and Multimodal Reconstruction"):
        md_build = Step("Build study-level\nmarkdown")
        md_summary = Step("Render structured\nannotation summary")
        md_body = Step("Render OCR\ntext + captions")
        md_inline = Step("Inline images\nwith descriptions")
        md_final = Data("Markdown for QA\nand curation")

        attach_meta >> md_build
        md_build >> md_summary >> md_final
        md_build >> md_body >> md_final
        md_build >> md_inline >> md_final

    # ---------------------------
    # 7. POST-PROCESSING
    # ---------------------------
    with Cluster("7. Post-processing and Aggregation"):
        load_valid = Data("Load validated\nannotations")
        detect_lists = Step("Detect list-like\nfields")
        stratified = Step("Build stratified\nvariables")
        value_counts = Step("Compute value\ncounts")
        export_excel = Data("Export Excel\nworkbook")
        dist_summary = Data("Distributional\nsummaries")

        (
            dataset
            >> load_valid
            >> detect_lists
            >> stratified
            >> value_counts
            >> export_excel
            >> dist_summary
        )
