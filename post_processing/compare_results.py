"""
Deep semantic comparison: human review (Covidence) vs LLM extraction (IE-Mistral).

Matching: title + author + year + journal (multi-signal, handles empty titles).
Comparison: semantic-level — understands that different wording can convey the
same clinical/scientific meaning.
"""

import csv
import re
import html
import ast
from pathlib import Path
from difflib import SequenceMatcher

_ROOT = Path(__file__).resolve().parent.parent
REVIEW_PATH = _ROOT / "data/review_538190_20260320052905.csv"
OUTPUT_PATH = _ROOT / "output/aggregated/df_annotations_v2.csv"
REPORT_PATH = _ROOT / "output/comparison_report.html"


# ═══════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════


def load_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def norm(s: str) -> str:
    """Lowercase, collapse whitespace, strip most punctuation."""
    s = re.sub(r"[\n\r]+", " ", s)
    s = re.sub(r"\s+", " ", s.lower().strip())
    s = re.sub(r"[^\w\s/\-]", "", s)
    return s.strip()


def parse_list(val: str) -> list[str]:
    """Parse Python list repr, semicolon-separated, or comma-separated values."""
    val = val.strip()
    if not val:
        return []
    if val.startswith("["):
        try:
            items = ast.literal_eval(val)
            return [str(x).strip() for x in items if str(x).strip()]
        except Exception:
            pass
    if ";" in val:
        return [x.strip() for x in val.split(";") if x.strip()]
    return [val.strip()]


def sim(a: str, b: str) -> float:
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


def esc(s: str) -> str:
    return html.escape(str(s))


# ═══════════════════════════════════════════════
# Robust row matching (title + author + year + journal)
# ═══════════════════════════════════════════════


def extract_last_name(author: str) -> str:
    parts = author.strip().split()
    return parts[-1].lower() if parts else ""


def match_rows(
    review: list[dict], output: list[dict]
) -> list[tuple[dict, dict | None]]:
    used: set[int] = set()
    pairs: list[tuple[dict, dict | None]] = []

    for rv in review:
        rv_title = rv.get("Title", "").strip()
        rv_author = rv.get("Lead Author (First Name Initial, Last Name)", "").strip()
        rv_year = rv.get("Publication Year", "").strip()
        rv_journal = rv.get("Journal", "").strip()
        rv_last = extract_last_name(rv_author)

        best_score = -1.0
        best_idx = -1

        for j, out in enumerate(output):
            if j in used:
                continue
            score = 0.0
            out_title = out.get("Title", "").strip()
            out_year = re.sub(r"\.0$", "", out.get("Publication Year", "").strip())
            out_journal = out.get("Journal", "").strip()

            # Title similarity (0-1, weighted x3)
            if rv_title and out_title:
                score += sim(rv_title, out_title) * 3.0
            # Year exact match (+1)
            if rv_year and out_year and rv_year.strip() == out_year.strip():
                score += 1.0
            # Journal similarity (+1)
            if rv_journal and out_journal:
                score += sim(rv_journal, out_journal) * 1.0
            # Author last name in title/journal (fallback for empty titles)
            if rv_last and rv_last in norm(out_title):
                score += 0.5

            if score > best_score:
                best_score = score
                best_idx = j

        if best_score >= 1.5 and best_idx >= 0:
            used.add(best_idx)
            pairs.append((rv, output[best_idx]))
        else:
            pairs.append((rv, None))

    return pairs


# ═══════════════════════════════════════════════
# Semantic concept extraction
# ═══════════════════════════════════════════════

# Study design canonical mapping
DESIGN_CANON = {
    "case report": "case_report",
    "case series": "case_report",
    "case study": "case_report",
    "pharmacokinetic study": "pk_study",
    "pk study": "pk_study",
    "pharmacokinetic": "pk_study",
    "cohort study": "cohort",
    "cohort": "cohort",
    "prospective cohort": "cohort",
    "retrospective cohort": "cohort",
    "observational": "observational",
    "non-randomized observational study": "observational",
    "nonrandomized observational study": "observational",
    "observational study": "observational",
    "cross-sectional study": "cross_sectional",
    "cross-sectional": "cross_sectional",
    "crosssectional study": "cross_sectional",
    "randomized controlled trial": "rct",
    "rct": "rct",
    "randomized clinical trial": "rct",
    "open-label study": "open_label",
    "open label": "open_label",
    "phase ii clinical trial": "clinical_trial",
    "phase iii clinical trial": "clinical_trial",
    "clinical trial": "clinical_trial",
    "meta-analysis": "meta_analysis",
    "systematic review": "systematic_review",
    "post-hoc analysis": "post_hoc",
    "post hoc analysis": "post_hoc",
    "secondary analysis": "post_hoc",
    "sub-analysis": "post_hoc",
    "retrospective analysis": "retrospective",
    "retrospective study": "retrospective",
    "retrospective": "retrospective",
    "prospective study": "prospective",
    "prospective": "prospective",
}

# Study design semantic groups (designs that are conceptually compatible)
DESIGN_COMPAT = {
    "pk_study": {
        "pk_study",
        "observational",
        "open_label",
        "prospective",
        "clinical_trial",
    },
    "observational": {
        "observational",
        "cohort",
        "cross_sectional",
        "prospective",
        "retrospective",
    },
    "cohort": {"cohort", "observational", "prospective", "retrospective"},
    "retrospective": {"retrospective", "cohort", "observational"},
    "prospective": {"prospective", "cohort", "observational", "open_label"},
    "case_report": {"case_report"},
    "rct": {"rct", "clinical_trial"},
    "clinical_trial": {"clinical_trial", "rct", "open_label"},
    "open_label": {"open_label", "clinical_trial", "pk_study", "prospective"},
    "post_hoc": {"post_hoc", "rct", "clinical_trial"},
}


def canonicalize_design(text: str) -> str | None:
    t = norm(text)
    for key, canon in DESIGN_CANON.items():
        if key in t:
            return canon
    return None


# DOAC canonical names
def extract_doacs(text: str) -> set[str]:
    t = norm(text)
    found = set()
    if "apixaban" in t:
        found.add("apixaban")
    if "rivaroxaban" in t:
        found.add("rivaroxaban")
    if "dabigatran" in t:
        found.add("dabigatran")
    if "edoxaban" in t:
        found.add("edoxaban")
    if "betrixaban" in t:
        found.add("betrixaban")
    return found


# Indication concepts
INDICATION_CONCEPTS = {
    "af": ["af", "atrial fibrillation", "non-valvular atrial fibrillation", "nvaf"],
    "vte": [
        "vte",
        "venous thromboembolism",
        "treatment/prevention of vte",
        "treatment or prevention of venous thromboembolism",
        "vte treatmentprevention",
        "deep vein thrombosis",
        "pulmonary embolism",
        "dvt",
        "pe",
    ],
    "surgery": [
        "elective procedure",
        "elective surgery",
        "surgery",
        "perioperative",
        "hip replacement",
        "knee replacement",
        "orthopedic",
    ],
    "acs": ["acute coronary syndrome", "acs", "myocardial infarction", "mi"],
    "stroke_prevention": ["stroke prevention", "stroke", "cerebrovascular"],
    "not_reported": ["not reported", "nr", "not specified"],
}


def extract_indications(text: str) -> set[str]:
    t = norm(text)
    found = set()
    for concept, keywords in INDICATION_CONCEPTS.items():
        if any(kw in t for kw in keywords):
            found.add(concept)
    return found


# Subgroup concepts
SUBGROUP_CONCEPTS = {
    "ckd": [
        "chronic kidney disease",
        "ckd",
        "dialysis",
        "hemodialysis",
        "renal",
        "end-stage renal",
        "esrd",
        "kidney",
    ],
    "obesity": ["obes", "high body weight", "bmi", "bariatric", "morbidly obese"],
    "elderly": ["elderly", "geriatric", "older", "aged", "senior"],
    "pediatric": ["paediatric", "pediatric", "adolescent", "child", "neonat"],
    "drug_interaction": [
        "drug interaction",
        "drug-drug",
        "pharmacokinetic interaction",
        "cyp3a",
        "p-gp",
        "p-glycoprotein",
        "ddi",
    ],
    "genetic": [
        "genetic",
        "polymorphism",
        "pharmacogenetic",
        "genotype",
        "phenotype",
        "gene",
        "cyp",
        "abcb1",
        "ces1",
    ],
    "liver": ["hepatic", "liver", "cirrhosis"],
    "cancer": ["cancer", "oncology", "malignancy", "tumor"],
    "pregnancy": ["pregnancy", "pregnant", "breastfeeding", "lactation"],
    "mechanical_valve": [
        "mechanical heart valve",
        "mechanical valve",
        "prosthetic valve",
    ],
    "aps": ["antiphospholipid", "aps", "lupus anticoagulant"],
    "surgery": [
        "surgery",
        "surgical",
        "perioperative",
        "elective procedure",
        "hip fracture",
        "knee replacement",
        "hip replacement",
    ],
    "overdose": ["overdose", "supratherapeutic", "intoxication"],
    "compliance": ["compliance", "noncompliance", "adherence", "non-adherence"],
    "bleeding": ["bleeding", "hemorrhag", "haemorrhag"],
}


def extract_subgroups(text: str) -> set[str]:
    t = norm(text)
    found = set()
    for concept, keywords in SUBGROUP_CONCEPTS.items():
        if any(kw in t for kw in keywords):
            found.add(concept)
    return found


# Coagulation test concepts
COAG_CONCEPTS = {
    "pt": ["prothrombin time", "pt ", "pt;", "pt/", "pt)", "(pt", "pt,"],
    "aptt": ["aptt", "activated partial thromboplastin", "partial thromboplastin time"],
    "tt": ["thrombin time", "(tt", "tt;", "tt)", " tt "],
    "viscoelastic": [
        "viscoelastic",
        "rotem",
        "teg",
        "thromboelastograph",
        "thromboelastometry",
    ],
    "tga": ["thrombin generation", "tga"],
}


def extract_coag_concepts(text: str) -> set[str]:
    t = norm(text)
    found = set()
    for concept, keywords in COAG_CONCEPTS.items():
        if any(kw in t for kw in keywords):
            found.add(concept)
    return found


# Timing concepts
TIMING_CONCEPTS = {
    "peak": ["peak", "cmax", "2-4 hours", "2–4 hours", "post-dose", "2 hours after"],
    "trough": [
        "trough",
        "ctrough",
        "pre-dose",
        "prior to next dose",
        "just before next",
    ],
    "random": ["random", "non-timed", "unscheduled"],
    "steady_state": ["steady state", "steady-state", "multiple dose"],
    "pre_procedure": [
        "pre-procedure",
        "preoperative",
        "pre-operative",
        "before surgery",
        "before procedure",
    ],
    "auc": ["auc", "area under the curve"],
}


def extract_timing_concepts(text: str) -> set[str]:
    t = norm(text)
    found = set()
    for concept, keywords in TIMING_CONCEPTS.items():
        if any(kw in t for kw in keywords):
            found.add(concept)
    return found


# Clinical outcome concepts
OUTCOME_CONCEPTS = {
    "bleeding": [
        "bleeding",
        "hemorrhag",
        "haemorrhag",
        "hemostasis",
        "haemostasis",
        "isth bleeding",
        "barc",
        "major bleeding",
        "minor bleeding",
    ],
    "stroke_tia": [
        "stroke",
        "tia",
        "transient ischemic",
        "ischemic stroke",
        "cerebrovascular",
        "intracranial",
    ],
    "vte": [
        "dvt",
        "pe ",
        "pulmonary embolism",
        "deep vein thrombosis",
        "venous thromboembolism",
        "vte",
    ],
    "mortality": ["death", "mortality", "fatal"],
    "thrombosis": ["thrombosis", "thromboembolic", "systemic embolism"],
}


def extract_outcome_concepts(text: str) -> set[str]:
    t = norm(text)
    found = set()
    for concept, keywords in OUTCOME_CONCEPTS.items():
        if any(kw in t for kw in keywords):
            found.add(concept)
    return found


# Comparator assay concepts
COMPARATOR_CONCEPTS = {
    "pt": ["prothrombin time", " pt ", "pt;", "pt,", "(pt", "pt/inr"],
    "aptt": ["aptt", "activated partial thromboplastin"],
    "tt": ["thrombin time", " tt ", "tt;", "(tt"],
    "anti_xa_heparin": [
        "heparin calibrat",
        "anti-xa assay",
        "heparin anti-xa",
        "anti-xa using heparin",
        "heparin (ufh/lmwh) anti-xa",
        "anti xa",
        "anti-factor xa",
    ],
    "tga": ["thrombin generation"],
    "viscoelastic": ["viscoelastic", "rotem", "teg", "thromboelastograph"],
    "drvvt": ["drvvt", "dilute russell", "russells viper venom"],
    "ecarin": ["ecarin"],
}


def extract_comparator_concepts(text: str) -> set[str]:
    t = norm(text)
    found = set()
    for concept, keywords in COMPARATOR_CONCEPTS.items():
        if any(kw in t for kw in keywords):
            found.add(concept)
    return found


# Diagnostic performance concepts
DIAG_PERF_CONCEPTS = {
    "correlation": ["correlation", "spearman", "pearson", "kendall"],
    "regression": [
        "regression",
        "r²",
        "r2",
        "coefficient of determination",
        "linear regression",
    ],
    "sensitivity": ["sensitivity"],
    "specificity": ["specificity"],
    "roc_auc": ["roc", "auc", "area under the curve", "receiver operating"],
    "bland_altman": ["bland-altman", "bland altman"],
    "ppv_npv": ["positive predictive", "negative predictive", "ppv", "npv"],
    "kappa": ["kappa", "agreement", "concordance"],
    "passing_bablok": ["passing-bablok", "passing bablok", "deming regression"],
}


def extract_diag_perf_concepts(text: str) -> set[str]:
    t = norm(text)
    found = set()
    for concept, keywords in DIAG_PERF_CONCEPTS.items():
        if any(kw in t for kw in keywords):
            found.add(concept)
    return found


# ═══════════════════════════════════════════════
# Semantic comparison functions
# ═══════════════════════════════════════════════


def semantic_compare(rv_concepts: set, out_concepts: set) -> tuple[str, float, str]:
    """
    Compare two concept sets. Returns (level, score, detail).
    Score: 1.0 = perfect, 0.0 = complete mismatch.
    """
    if not rv_concepts and not out_concepts:
        return "both_empty", -1.0, ""  # -1 means exclude from scoring
    if not rv_concepts and out_concepts:
        return "extra", 0.25, f"LLM found: {out_concepts}"
    if rv_concepts and not out_concepts:
        return "missing", 0.0, f"Expected: {rv_concepts}"
    if rv_concepts == out_concepts:
        return "exact", 1.0, ""
    overlap = rv_concepts & out_concepts
    union = rv_concepts | out_concepts
    jaccard = len(overlap) / len(union)
    # Also check recall (did LLM find what human found?)
    recall = len(overlap) / len(rv_concepts) if rv_concepts else 0
    # And precision (did LLM avoid hallucinations?)
    precision = len(overlap) / len(out_concepts) if out_concepts else 0

    if recall == 1.0:
        # LLM found everything human found, maybe extras
        return "close", 0.85, f"Match + extras: {out_concepts - rv_concepts}"
    if recall >= 0.5 and precision >= 0.5:
        score = 0.5 + jaccard * 0.5
        return "partial", score, f"Human: {rv_concepts} | LLM: {out_concepts}"
    if overlap:
        score = jaccard * 0.5
        return (
            "partial",
            score,
            f"Overlap: {overlap} | Human-only: {rv_concepts - out_concepts} | LLM-only: {out_concepts - rv_concepts}",
        )
    return "mismatch", 0.0, f"Human: {rv_concepts} | LLM: {out_concepts}"


# ═══════════════════════════════════════════════
# Field-level comparators
# ═══════════════════════════════════════════════


def cmp_journal(rv: dict, out: dict) -> tuple[str, float, str, str, str]:
    rv_val = rv.get("Journal", "").strip()
    out_val = out.get("Journal", "").strip()
    if not rv_val and not out_val:
        return "both_empty", -1.0, "", rv_val, out_val
    if not rv_val:
        return "extra", 0.25, "", rv_val, out_val
    if not out_val:
        return "missing", 0.0, "", rv_val, out_val
    s = sim(rv_val, out_val)
    if s > 0.85:
        return "exact", 1.0, "", rv_val, out_val
    if s > 0.6:
        return "close", 0.75, f"Sim={s:.2f}", rv_val, out_val
    return "mismatch", 0.0, f"Sim={s:.2f}", rv_val, out_val


def cmp_year(rv: dict, out: dict) -> tuple[str, float, str, str, str]:
    rv_val = rv.get("Publication Year", "").strip()
    out_val = re.sub(r"\.0$", "", out.get("Publication Year", "").strip())
    if rv_val == out_val:
        return "exact", 1.0, "", rv_val, out_val
    if not rv_val and not out_val:
        return "both_empty", -1.0, "", rv_val, out_val
    return "mismatch", 0.0, "", rv_val, out_val


def cmp_country(rv: dict, out: dict) -> tuple[str, float, str, str, str]:
    rv_val = rv.get("Country in which the study conducted", "").strip()
    out_val = out.get("Country of First Author", "").strip()
    if not rv_val and not out_val:
        return "both_empty", -1.0, "", rv_val, out_val
    if not rv_val:
        return "extra", 0.25, "", rv_val, out_val
    if not out_val:
        return "missing", 0.0, "", rv_val, out_val
    # Normalize country names
    rv_n = norm(rv_val)
    out_n = norm(out_val)
    if rv_n == out_n:
        return "exact", 1.0, "", rv_val, out_val
    # Common aliases
    aliases = {
        "usa": "united states",
        "us": "united states",
        "uk": "united kingdom",
        "the netherlands": "netherlands",
        "holland": "netherlands",
        "south korea": "korea",
        "republic of korea": "korea",
    }
    rv_c = aliases.get(rv_n, rv_n)
    out_c = aliases.get(out_n, out_n)
    if rv_c == out_c:
        return "exact", 1.0, "", rv_val, out_val
    # One might be more specific (e.g., "Germany" vs "Germany, Austria")
    if rv_c in out_c or out_c in rv_c:
        return "close", 0.75, "", rv_val, out_val
    return "mismatch", 0.0, "", rv_val, out_val


def cmp_study_design(rv: dict, out: dict) -> tuple[str, float, str, str, str]:
    rv_val = rv.get("Study design", "").strip()
    out_val = out.get("Study Design", "").strip()
    if not rv_val and not out_val:
        return "both_empty", -1.0, "", rv_val, out_val
    if not rv_val:
        return "extra", 0.25, "", rv_val, out_val
    if not out_val:
        return "missing", 0.0, "", rv_val, out_val

    rv_canon = canonicalize_design(rv_val)
    out_canon = canonicalize_design(out_val)

    if rv_canon and out_canon:
        if rv_canon == out_canon:
            return "exact", 1.0, "", rv_val, out_val
        # Check compatibility groups
        compat = DESIGN_COMPAT.get(rv_canon, {rv_canon})
        if out_canon in compat:
            return "close", 0.7, f"'{rv_canon}' ≈ '{out_canon}'", rv_val, out_val
        return "mismatch", 0.0, f"'{rv_canon}' ≠ '{out_canon}'", rv_val, out_val

    # Fallback: string similarity
    s = sim(rv_val, out_val)
    if s > 0.7:
        return "close", 0.75, f"Sim={s:.2f}", rv_val, out_val
    return "mismatch", 0.0, f"Sim={s:.2f}", rv_val, out_val


def cmp_doacs(rv: dict, out: dict) -> tuple[str, float, str, str, str]:
    rv_val = rv.get("DOAC(s) Included (select all that apply)", "").strip()
    out_val = out.get("Patient population 1", "").strip()
    rv_set = extract_doacs(rv_val)
    out_set = extract_doacs(" ".join(parse_list(out_val)))
    level, score, detail = semantic_compare(rv_set, out_set)
    return level, score, detail, rv_val, out_val


def cmp_indications(rv: dict, out: dict) -> tuple[str, float, str, str, str]:
    rv_val = rv.get("Indication(s) (select all that apply)", "").strip()
    out_val = out.get("Patient population 2", "").strip()
    rv_set = extract_indications(rv_val)
    out_set = extract_indications(" ".join(parse_list(out_val)))
    level, score, detail = semantic_compare(rv_set, out_set)
    return level, score, detail, rv_val, out_val


def cmp_subgroups(rv: dict, out: dict) -> tuple[str, float, str, str, str]:
    rv_val = rv.get("Relevant Subgroups (select all that apply)", "").strip()
    out_val = out.get("Patient population 3", "").strip()
    rv_set = extract_subgroups(rv_val)
    out_set = extract_subgroups(" ".join(parse_list(out_val)))
    level, score, detail = semantic_compare(rv_set, out_set)
    return level, score, detail, rv_val, out_val


def _review_coag_concepts(rv: dict) -> set[str]:
    """Extract coag concepts from the review's Yes/No columns."""
    found = set()
    if (
        rv.get("Prothrombin time (PT; seconds or INR value)", "").strip().lower()
        == "yes"
    ):
        found.add("pt")
    if (
        rv.get("Activated partial thromboplastin time (aPTT; seconds)", "")
        .strip()
        .lower()
        == "yes"
    ):
        found.add("aptt")
    if rv.get("Viscoelastic Testing (TEG/ROTEM)", "").strip().lower() == "yes":
        found.add("viscoelastic")
    if (
        rv.get("Thrombin Generation Assay (TGA; see Analysis Plan for assay list)", "")
        .strip()
        .lower()
        == "yes"
    ):
        found.add("tga")
    return found


def cmp_coag_tests(rv: dict, out: dict) -> tuple[str, float, str, str, str]:
    rv_set = _review_coag_concepts(rv)
    # Output has two fields: conventional + global
    conv = out.get("Conventional Coagulation Tests Concurrently Reported", "").strip()
    glob = out.get("Global Coagulation Testing", "").strip()
    combined = " ".join(parse_list(conv) + parse_list(glob))
    out_set = extract_coag_concepts(combined)

    rv_display = ", ".join(sorted(rv_set)) if rv_set else "(none)"
    out_display = ", ".join(sorted(out_set)) if out_set else "(none)"
    level, score, detail = semantic_compare(rv_set, out_set)
    return level, score, detail, rv_display, out_display


def cmp_timing(rv: dict, out: dict) -> tuple[str, float, str, str, str]:
    rv_val = rv.get("Timing of Measurement (select all that apply)", "").strip()
    out_val = out.get(
        "Timing of DOAC level measurement relative to DOAC intake", ""
    ).strip()
    rv_set = extract_timing_concepts(rv_val)
    out_set = extract_timing_concepts(" ".join(parse_list(out_val)))
    level, score, detail = semantic_compare(rv_set, out_set)
    return level, score, detail, rv_val[:100], out_val[:100]


def cmp_thresholds(rv: dict, out: dict) -> tuple[str, float, str, str, str]:
    rv_val = rv.get(
        "Reported DOAC level concentration thresholds/cutoffs "
        "(if evaluate directly as part of the study, not just if "
        "mentioned as part of background/discussion)",
        "",
    ).strip()
    out_val = out.get(
        "Reported DOAC concentration thresholds/cutoffs (listed)", ""
    ).strip()
    rv_has = bool(rv_val)
    out_items = parse_list(out_val)
    out_has = bool(out_items)

    if not rv_has and not out_has:
        return "both_empty", -1.0, "", "", ""
    if rv_has and out_has:
        # Both report thresholds — count as match (detailed values hard to compare)
        return "exact", 1.0, "", rv_val[:80], out_val[:80]
    if rv_has and not out_has:
        return "missing", 0.0, "", rv_val[:80], ""
    return "extra", 0.25, "", "", out_val[:80]


def cmp_outcomes(rv: dict, out: dict) -> tuple[str, float, str, str, str]:
    """Compare clinical outcomes holistically."""
    # Review has separate Yes/No for bleeding, stroke, DVT/PE
    rv_set: set[str] = set()
    if rv.get("Bleeding/Hemostasis", "").strip().lower() == "yes":
        rv_set.add("bleeding")
    if rv.get("Stroke/TIA", "").strip().lower() == "yes":
        rv_set.add("stroke_tia")
    if rv.get("DVT/PE", "").strip().lower() == "yes":
        rv_set.add("vte")

    out_val = out.get("Clinical Outcomes", "").strip()
    out_set = extract_outcome_concepts(" ".join(parse_list(out_val)))

    rv_display = ", ".join(sorted(rv_set)) if rv_set else "(none reported)"
    out_display = ", ".join(sorted(out_set)) if out_set else "(none detected)"
    level, score, detail = semantic_compare(rv_set, out_set)
    return level, score, detail, rv_display, out_display


def cmp_comparator_assays(rv: dict, out: dict) -> tuple[str, float, str, str, str]:
    rv_val = rv.get("Comparator Assays", "").strip()
    out_val = out.get("Comparator Assays", "").strip()
    rv_set = extract_comparator_concepts(rv_val)
    out_set = extract_comparator_concepts(" ".join(parse_list(out_val)))
    level, score, detail = semantic_compare(rv_set, out_set)
    return level, score, detail, rv_val[:100], out_val[:100]


def cmp_diag_performance(rv: dict, out: dict) -> tuple[str, float, str, str, str]:
    rv_val = rv.get("Diagnostic Performance Parameters Reported", "").strip()
    # Output has both categorical and continuous
    cat = out.get("Diagnostic Performance Metrics - Categorical Cutoffs", "").strip()
    cont = out.get(
        "Diagnostic Performance Metrics - Continuous Relationships", ""
    ).strip()
    combined_out = " ".join(parse_list(cat) + parse_list(cont))

    rv_set = extract_diag_perf_concepts(rv_val)
    out_set = extract_diag_perf_concepts(combined_out)

    rv_display = rv_val[:100] if rv_val else "(none)"
    out_display = (cat[:50] + " | " + cont[:50]) if (cat or cont) else "(none)"
    level, score, detail = semantic_compare(rv_set, out_set)
    return level, score, detail, rv_display, out_display


# All field comparators with display names and categories
COMPARATORS = [
    ("Journal", "Meta & Design", cmp_journal),
    ("Publication Year", "Meta & Design", cmp_year),
    ("Country", "Meta & Design", cmp_country),
    ("Study Design", "Meta & Design", cmp_study_design),
    ("DOACs Included", "Population", cmp_doacs),
    ("Indications", "Population", cmp_indications),
    ("Relevant Subgroups", "Population", cmp_subgroups),
    ("Coagulation Tests", "Methods", cmp_coag_tests),
    ("Timing of Measurement", "Timing & Thresholds", cmp_timing),
    ("Thresholds/Cutoffs", "Timing & Thresholds", cmp_thresholds),
    ("Clinical Outcomes", "Clinical Outcomes", cmp_outcomes),
    ("Comparator Assays", "Diagnostic", cmp_comparator_assays),
    ("Diagnostic Performance", "Diagnostic", cmp_diag_performance),
]


# ═══════════════════════════════════════════════
# Run comparison
# ═══════════════════════════════════════════════


def run_comparison():
    review = load_csv(REVIEW_PATH)
    output = load_csv(OUTPUT_PATH)
    pairs = match_rows(review, output)

    results = []
    for rv, out in pairs:
        author = rv.get("Lead Author (First Name Initial, Last Name)", "").strip()
        year = rv.get("Publication Year", "").strip()
        label = f"{author.split()[-1] if author else '?'} {year}"

        for field_name, category, cmp_fn in COMPARATORS:
            if out is None:
                results.append(
                    (
                        label,
                        field_name,
                        category,
                        "unmatched",
                        0.0,
                        "No matching output row",
                        "",
                        "",
                    )
                )
            else:
                level, score, detail, rv_val, out_val = cmp_fn(rv, out)
                results.append(
                    (label, field_name, category, level, score, detail, rv_val, out_val)
                )

    return pairs, results


# ═══════════════════════════════════════════════
# HTML Report
# ═══════════════════════════════════════════════

MATCH_COLORS = {
    "exact": "#22c55e",
    "close": "#84cc16",
    "partial": "#eab308",
    "both_empty": "#94a3b8",
    "extra": "#60a5fa",
    "missing": "#f97316",
    "mismatch": "#ef4444",
    "unmatched": "#6b7280",
}

MATCH_LABELS = {
    "exact": "Exact Match",
    "close": "Close / Compatible",
    "partial": "Partial Overlap",
    "both_empty": "Both Empty",
    "extra": "LLM Found Extra",
    "missing": "LLM Missed",
    "mismatch": "Disagreement",
    "unmatched": "Unmatched Paper",
}


def generate_html(pairs, results):
    # ── Stats ──
    scored = [
        (label, fn, cat, ml, sc, detail, rv, ov)
        for label, fn, cat, ml, sc, detail, rv, ov in results
        if sc >= 0
    ]
    all_scores = [sc for *_, sc, _, _, _ in scored]
    overall = sum(all_scores) / len(all_scores) * 100 if all_scores else 0

    match_totals: dict[str, int] = {}
    for *_, ml, _, _, _, _ in results:
        match_totals[ml] = match_totals.get(ml, 0) + 1

    matched_count = sum(1 for _, out in pairs if out is not None)

    # Per-field stats
    field_stats: dict[str, dict] = {}
    for label, fn, cat, ml, sc, detail, rv, ov in results:
        if fn not in field_stats:
            field_stats[fn] = {"category": cat, "counts": {}, "scores": []}
        field_stats[fn]["counts"][ml] = field_stats[fn]["counts"].get(ml, 0) + 1
        if sc >= 0:
            field_stats[fn]["scores"].append(sc)

    # Per-category
    cat_stats: dict[str, list[float]] = {}
    for fn, fs in field_stats.items():
        cat = fs["category"]
        if cat not in cat_stats:
            cat_stats[cat] = []
        cat_stats[cat].extend(fs["scores"])

    # Per-paper
    paper_stats: dict[str, dict] = {}
    for label, fn, cat, ml, sc, detail, rv, ov in results:
        if label not in paper_stats:
            paper_stats[label] = {"scores": [], "counts": {}}
        paper_stats[label]["counts"][ml] = paper_stats[label]["counts"].get(ml, 0) + 1
        if sc >= 0:
            paper_stats[label]["scores"].append(sc)

    categories = list(dict.fromkeys(cat for _, _, cat, *_ in results))
    fields = list(dict.fromkeys(fn for _, fn, *_ in results))
    total_comparisons = len(results)

    # ── HTML ──
    h = []
    h.append("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IE-Mistral — Human vs LLM Extraction Report</title>
<style>
:root{--bg:#0f172a;--s1:#1e293b;--s2:#334155;--s3:#475569;--t1:#f8fafc;--t2:#e2e8f0;--t3:#94a3b8;--accent:#3b82f6;--green:#22c55e;--lime:#84cc16;--yellow:#eab308;--orange:#f97316;--red:#ef4444;--blue:#60a5fa;--gray:#6b7280;--slate:#94a3b8}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--t2);padding:2rem 3rem;line-height:1.6}
h1{font-size:2rem;color:var(--t1);margin-bottom:.3rem}
h2{font-size:1.35rem;color:var(--t1);margin:2.5rem 0 1rem;border-bottom:2px solid var(--s3);padding-bottom:.5rem}
h3{font-size:1.05rem;color:var(--t2);margin:1.5rem 0 .7rem}
.sub{color:var(--t3);margin-bottom:2rem;font-size:.95rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;margin:1.5rem 0}
.card{background:var(--s1);border:1px solid var(--s3);border-radius:14px;padding:1.3rem;text-align:center}
.card .label{font-size:.75rem;color:var(--t3);text-transform:uppercase;letter-spacing:.06em}
.card .val{font-size:2.2rem;font-weight:800;margin:.2rem 0}
.card .note{font-size:.82rem;color:var(--t3)}
.bar{display:flex;height:26px;border-radius:7px;overflow:hidden;margin:.6rem 0}
.bar div{display:flex;align-items:center;justify-content:center;font-size:.68rem;font-weight:700;color:#0f172a;min-width:2px;transition:width .3s}
table{width:100%;border-collapse:collapse;margin:1rem 0;font-size:.85rem}
th{background:var(--s2);text-align:left;padding:.6rem .8rem;font-size:.78rem;text-transform:uppercase;letter-spacing:.03em;color:var(--t3);position:sticky;top:0;z-index:1}
td{padding:.5rem .8rem;border-bottom:1px solid var(--s3)}
tr:hover td{background:var(--s1)}
.badge{display:inline-block;padding:2px 10px;border-radius:5px;font-size:.73rem;font-weight:700;color:#0f172a}
.pbar{display:inline-block;height:8px;border-radius:4px;vertical-align:middle;margin-right:6px}
.legend{display:flex;flex-wrap:wrap;gap:.9rem;margin:1rem 0}
.legend-i{display:flex;align-items:center;gap:.35rem;font-size:.82rem;color:var(--t3)}
.legend-d{width:13px;height:13px;border-radius:3px}
.scroll{max-height:600px;overflow-y:auto}
.methodology{background:var(--s1);border:1px solid var(--s3);border-radius:12px;padding:1.5rem;margin:1.5rem 0}
.methodology h3{margin-top:0}
.methodology li{margin-bottom:.3rem;color:var(--t3)}
.methodology code{background:var(--s2);padding:2px 6px;border-radius:3px;font-size:.82rem;color:var(--t2)}
footer{margin-top:3rem;padding-top:1rem;border-top:1px solid var(--s3);color:var(--t3);font-size:.78rem}
</style>
</head>
<body>
""")

    # ── Title ──
    h.append(f"""
<h1>Human vs LLM: Extraction Accuracy Report</h1>
<p class="sub">Semantic comparison of manual review (Covidence, {len(pairs)} papers) against Mistral OCR + LLM extraction pipeline</p>
""")

    # ── Methodology ──
    h.append("""
<div class="methodology">
<h3>Comparison Methodology</h3>
<ul>
<li><strong>Matching:</strong> Papers matched by title similarity + year + journal + author (handles empty titles via fallback signals)</li>
<li><strong>Semantic comparison:</strong> Each field is compared at the <em>concept level</em>, not keyword level. Both human and LLM values are mapped to canonical clinical/scientific concepts before comparison.</li>
<li><strong>Scoring:</strong> <code>Exact</code> = 1.0, <code>Close/Compatible</code> = 0.7–0.85, <code>Partial</code> = 0.25–0.75 (Jaccard-weighted), <code>Extra</code> = 0.25, <code>Missing/Disagree</code> = 0.0. <code>Both Empty</code> excluded from scoring.</li>
<li><strong>Study design:</strong> Uses compatibility groups (e.g., "Pharmacokinetic study" ≈ "Non-Randomized Observational Study" since PK studies are inherently observational).</li>
<li><strong>Clinical outcomes:</strong> Human's separate Yes/No flags (Bleeding, Stroke/TIA, DVT/PE) are unified into a concept set and compared against LLM's list extraction.</li>
<li><strong>Comparator assays &amp; coagulation tests:</strong> Both sides mapped to canonical assay concepts (PT, aPTT, TGA, anti-Xa, etc.) regardless of naming differences.</li>
</ul>
</div>
""")

    # ── Top cards ──
    acc_color = "--green" if overall >= 70 else "--yellow" if overall >= 50 else "--red"
    h.append(f"""
<div class="grid">
  <div class="card"><div class="label">Overall Semantic Accuracy</div>
    <div class="val" style="color:var({acc_color})">{overall:.1f}%</div>
    <div class="note">{len(all_scores)} scored comparisons</div></div>
  <div class="card"><div class="label">Papers Matched</div>
    <div class="val">{matched_count}<span style="font-size:1rem;color:var(--t3)">/{len(pairs)}</span></div>
    <div class="note">multi-signal matching</div></div>
  <div class="card"><div class="label">Fields Compared</div>
    <div class="val">{len(fields)}</div>
    <div class="note">{len(categories)} categories</div></div>
  <div class="card"><div class="label">Agreement Rate</div>
    <div class="val" style="color:var(--lime)">{(match_totals.get("exact", 0) + match_totals.get("close", 0)) / total_comparisons * 100:.0f}%</div>
    <div class="note">exact + close matches</div></div>
  <div class="card"><div class="label">Disagreement Rate</div>
    <div class="val" style="color:var(--red)">{(match_totals.get("mismatch", 0)) / total_comparisons * 100:.0f}%</div>
    <div class="note">semantic mismatches</div></div>
</div>
""")

    # ── Legend + bar ──
    h.append('<div class="legend">')
    for ml, color in MATCH_COLORS.items():
        cnt = match_totals.get(ml, 0)
        h.append(
            f'<div class="legend-i"><div class="legend-d" style="background:{color}"></div>{MATCH_LABELS[ml]} ({cnt})</div>'
        )
    h.append("</div>")

    total = sum(match_totals.values())
    h.append('<div class="bar">')
    for ml in [
        "exact",
        "close",
        "partial",
        "both_empty",
        "extra",
        "missing",
        "mismatch",
        "unmatched",
    ]:
        cnt = match_totals.get(ml, 0)
        if cnt > 0:
            pct = cnt / total * 100
            h.append(
                f'<div style="width:{pct}%;background:{MATCH_COLORS[ml]}" title="{MATCH_LABELS[ml]}: {cnt}">{cnt if pct > 3 else ""}</div>'
            )
    h.append("</div>")

    # ── Category Breakdown ──
    h.append("<h2>Accuracy by Category</h2>")
    h.append(
        "<table><thead><tr><th>Category</th><th>Accuracy</th><th>N</th><th>Distribution</th></tr></thead><tbody>"
    )
    for cat in categories:
        scores = cat_stats.get(cat, [])
        acc = sum(scores) / len(scores) * 100 if scores else 0
        color = (
            "var(--green)"
            if acc >= 70
            else "var(--yellow)"
            if acc >= 50
            else "var(--red)"
        )
        cat_counts: dict[str, int] = {}
        for _, fn, c, ml, *_ in results:
            if c == cat:
                cat_counts[ml] = cat_counts.get(ml, 0) + 1
        ct = sum(cat_counts.values())
        bar = ""
        for ml in [
            "exact",
            "close",
            "partial",
            "both_empty",
            "extra",
            "missing",
            "mismatch",
        ]:
            n = cat_counts.get(ml, 0)
            if n > 0:
                bar += f'<div style="width:{n / ct * 100}%;background:{MATCH_COLORS[ml]}" title="{MATCH_LABELS[ml]}: {n}"></div>'
        h.append(
            f'<tr><td style="font-weight:600">{esc(cat)}</td><td style="color:{color};font-weight:700">{acc:.1f}%</td><td>{len(scores)}</td><td><div class="bar" style="height:18px">{bar}</div></td></tr>'
        )
    h.append("</tbody></table>")

    # ── Field Breakdown ──
    h.append("<h2>Accuracy by Field</h2>")
    h.append(
        "<table><thead><tr><th>Field</th><th>Category</th><th>Accuracy</th><th>Exact</th><th>Close</th><th>Partial</th><th>Missed</th><th>Disagree</th><th>N/A</th></tr></thead><tbody>"
    )
    for fn in fields:
        fs = field_stats[fn]
        scores = fs["scores"]
        acc = sum(scores) / len(scores) * 100 if scores else 0
        color = (
            "var(--green)"
            if acc >= 70
            else "var(--yellow)"
            if acc >= 50
            else "var(--red)"
        )
        c = fs["counts"]
        h.append(
            f'<tr><td>{esc(fn)}</td><td style="color:var(--t3)">{esc(fs["category"])}</td>'
        )
        h.append(
            f'<td><span class="pbar" style="width:{acc * 0.6}px;background:{color[4:-1]}"></span>'
            f'<span style="color:{color};font-weight:700">{acc:.0f}%</span></td>'
        )
        h.append(
            f"<td>{c.get('exact', 0)}</td><td>{c.get('close', 0)}</td><td>{c.get('partial', 0)}</td>"
        )
        h.append(
            f'<td style="color:var(--orange)">{c.get("missing", 0)}</td><td style="color:var(--red)">{c.get("mismatch", 0)}</td>'
        )
        h.append(f"<td>{c.get('both_empty', 0)}</td></tr>")
    h.append("</tbody></table>")

    # ── Per-Paper ──
    h.append("<h2>Accuracy by Paper</h2>")
    h.append(
        '<div class="scroll"><table><thead><tr><th>Paper</th><th>Accuracy</th><th style="width:200px">Distribution</th><th>Exact</th><th>Close</th><th>Disagree</th><th>Missed</th></tr></thead><tbody>'
    )
    sorted_papers = sorted(
        paper_stats.items(),
        key=lambda x: sum(x[1]["scores"]) / len(x[1]["scores"])
        if x[1]["scores"]
        else 0,
    )
    for label, ps in sorted_papers:
        scores = ps["scores"]
        acc = sum(scores) / len(scores) * 100 if scores else 0
        color = (
            "var(--green)"
            if acc >= 70
            else "var(--yellow)"
            if acc >= 50
            else "var(--red)"
        )
        c = ps["counts"]
        ct = sum(c.values())
        bar = ""
        for ml in [
            "exact",
            "close",
            "partial",
            "both_empty",
            "extra",
            "missing",
            "mismatch",
        ]:
            n = c.get(ml, 0)
            if n > 0:
                bar += f'<div style="width:{n / ct * 100}%;background:{MATCH_COLORS[ml]}"></div>'
        h.append(
            f'<tr><td>{esc(label)}</td><td style="color:{color};font-weight:700">{acc:.0f}%</td>'
        )
        h.append(f'<td><div class="bar" style="height:14px">{bar}</div></td>')
        h.append(f"<td>{c.get('exact', 0)}</td><td>{c.get('close', 0)}</td>")
        h.append(
            f'<td style="color:var(--red)">{c.get("mismatch", 0)}</td><td style="color:var(--orange)">{c.get("missing", 0)}</td></tr>'
        )
    h.append("</tbody></table></div>")

    # ── Disagreements detail ──
    h.append("<h2>Detailed Disagreements</h2>")
    h.append(
        '<p class="sub">Where the LLM semantically disagreed with the human reviewer</p>'
    )
    h.append(
        '<div class="scroll"><table><thead><tr><th>Paper</th><th>Field</th><th>Human Review</th><th>LLM Extraction</th><th>Detail</th></tr></thead><tbody>'
    )
    mismatches = [
        (label, fn, rv, ov, detail)
        for label, fn, _, ml, _, detail, rv, ov in results
        if ml == "mismatch"
    ]
    for label, fn, rv, ov, detail in mismatches:
        h.append(
            f"<tr><td>{esc(label)}</td><td>{esc(fn)}</td>"
            f'<td style="color:var(--orange)">{esc(str(rv)[:150])}</td>'
            f'<td style="color:var(--blue)">{esc(str(ov)[:150])}</td>'
            f'<td style="color:var(--t3);font-size:.78rem">{esc(detail[:100])}</td></tr>'
        )
    h.append("</tbody></table></div>")

    # ── Missing detail ──
    missing_rows = [
        (label, fn, rv) for label, fn, _, ml, _, _, rv, _ in results if ml == "missing"
    ]
    if missing_rows:
        h.append("<h2>LLM Missed (Present in Human Review)</h2>")
        h.append(
            '<div class="scroll"><table><thead><tr><th>Paper</th><th>Field</th><th>Human Value</th></tr></thead><tbody>'
        )
        for label, fn, rv in missing_rows:
            h.append(
                f'<tr><td>{esc(label)}</td><td>{esc(fn)}</td><td style="color:var(--orange)">{esc(str(rv)[:200])}</td></tr>'
            )
        h.append("</tbody></table></div>")

    # ── Extra detail ──
    extra_rows = [
        (label, fn, ov) for label, fn, _, ml, _, _, _, ov in results if ml == "extra"
    ]
    if extra_rows:
        h.append("<h2>LLM Found Extra (Not in Human Review)</h2>")
        h.append(
            '<p class="sub">LLM extracted data the human reviewer left empty — may indicate LLM found relevant info or over-extracted</p>'
        )
        h.append(
            '<div class="scroll"><table><thead><tr><th>Paper</th><th>Field</th><th>LLM Value</th></tr></thead><tbody>'
        )
        for label, fn, ov in extra_rows:
            h.append(
                f'<tr><td>{esc(label)}</td><td>{esc(fn)}</td><td style="color:var(--blue)">{esc(str(ov)[:200])}</td></tr>'
            )
        h.append("</tbody></table></div>")

    # ── Key findings ──
    h.append("<h2>Key Findings</h2>")
    # Best and worst fields
    field_accs = []
    for fn in fields:
        scores = field_stats[fn]["scores"]
        if scores:
            field_accs.append((fn, sum(scores) / len(scores) * 100))
    field_accs.sort(key=lambda x: -x[1])
    best = field_accs[:3] if field_accs else []
    worst = field_accs[-3:] if len(field_accs) >= 3 else []

    h.append('<div class="grid">')
    h.append(
        '<div class="card" style="text-align:left"><div class="label">Strongest Fields</div>'
    )
    for fn, acc in best:
        h.append(
            f'<div style="margin:.3rem 0"><span style="color:var(--green);font-weight:700">{acc:.0f}%</span> {esc(fn)}</div>'
        )
    h.append("</div>")
    h.append(
        '<div class="card" style="text-align:left"><div class="label">Weakest Fields</div>'
    )
    for fn, acc in worst:
        color = (
            "var(--red)"
            if acc < 50
            else "var(--yellow)"
            if acc < 70
            else "var(--green)"
        )
        h.append(
            f'<div style="margin:.3rem 0"><span style="color:{color};font-weight:700">{acc:.0f}%</span> {esc(fn)}</div>'
        )
    h.append("</div>")

    mismatch_by_field: dict[str, int] = {}
    for _, fn, _, ml, *_ in results:
        if ml == "mismatch":
            mismatch_by_field[fn] = mismatch_by_field.get(fn, 0) + 1
    top_mismatch = sorted(mismatch_by_field.items(), key=lambda x: -x[1])[:5]
    h.append(
        '<div class="card" style="text-align:left"><div class="label">Most Disagreements</div>'
    )
    for fn, cnt in top_mismatch:
        h.append(
            f'<div style="margin:.3rem 0"><span style="color:var(--red);font-weight:700">{cnt}</span> {esc(fn)}</div>'
        )
    h.append("</div></div>")

    h.append("""
<footer>
  Generated by IE-Mistral comparison tool &bull; Semantic-level analysis &bull;
  Human source: Covidence export &bull; LLM source: df_annotations_v2.csv
</footer>
</body></html>""")
    return "\n".join(h)


# ═══════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════


def main():
    pairs, results = run_comparison()
    html_content = generate_html(pairs, results)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(html_content, encoding="utf-8")
    print(f"Report: {REPORT_PATH}")

    scored = [sc for *_, ml, sc, _, _, _ in results if sc >= 0]
    overall = sum(scored) / len(scored) * 100 if scored else 0
    print(f"Overall semantic accuracy: {overall:.1f}%")

    matched = sum(1 for _, out in pairs if out is not None)
    print(f"Papers matched: {matched}/{len(pairs)}")

    totals: dict[str, int] = {}
    for *_, ml, _, _, _, _ in results:
        totals[ml] = totals.get(ml, 0) + 1
    for ml, cnt in sorted(totals.items(), key=lambda x: -x[1]):
        print(f"  {MATCH_LABELS.get(ml, ml)}: {cnt}")


if __name__ == "__main__":
    main()
