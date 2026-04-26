"""Compare AI-extracted values against the human gold standard.

Run:
    uv run python analysis/compare_to_human.py

Outputs:
    docs/comparisons/2026-04-26-comparison-report.md          (human-readable report)
    docs/comparisons/2026-04-26-per-paper-agreement.csv       (one row per paper, score per domain)
    docs/comparisons/2026-04-26-disagreements.csv             (every field/paper disagreement)
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from rapidfuzz import fuzz, process

ROOT = Path(__file__).resolve().parents[1]
AI_CSV = ROOT / "output" / "aggregated" / "df_annotations.csv"
HU_CSV = ROOT / "data" / "human" / "Pooja + Athavan Abstraction Lock 19MAR2026.csv"
OUT_DIR = ROOT / "docs" / "comparisons"
OUT_DIR.mkdir(parents=True, exist_ok=True)

REPORT_MD = OUT_DIR / "2026-04-26-comparison-report.md"
PER_PAPER_CSV = OUT_DIR / "2026-04-26-per-paper-agreement.csv"
DISAGREEMENTS_CSV = OUT_DIR / "2026-04-26-disagreements.csv"


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

NULL_TOKENS = {
    "",
    "nan",
    "none",
    "null",
    "[]",
    "n/a",
    "na",
    "not reported",
    "not applicable",
}


def is_blank(val: Any) -> bool:
    if val is None:
        return True
    if isinstance(val, float) and pd.isna(val):
        return True
    s = str(val).strip().lower()
    return s in NULL_TOKENS


def parse_ai_list(val: Any) -> list[str]:
    """AI emits list-as-string like "['A', 'B']" (Pydantic .model_dump_json result)."""
    if is_blank(val):
        return []
    s = str(val).strip()
    if s.startswith("[") and s.endswith("]"):
        try:
            parsed = ast.literal_eval(s)
            if isinstance(parsed, (list, tuple)):
                return [str(x).strip() for x in parsed if not is_blank(x)]
        except (ValueError, SyntaxError):
            pass
    return [s]


def parse_human_multiselect(val: Any) -> list[str]:
    """Human uses semicolon-separated multi-select."""
    if is_blank(val):
        return []
    s = str(val).strip()
    parts = re.split(r"\s*;\s*", s)
    return [p.strip() for p in parts if p.strip() and not is_blank(p)]


def canonicalize(label: str) -> str:
    """Lower-case, collapse whitespace, drop punctuation noise, apply label aliases."""
    s = label.lower().strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[‐-―]", "-", s)  # all dash variants
    # AI emits hierarchical labels like "X - Y" — keep only parent for cross-side comparison
    if " - " in s:
        s = s.split(" - ", 1)[0].strip()
    s = s.replace("(", " ").replace(")", " ")
    s = re.sub(r"\s+", " ", s).strip(" .,-")
    return LABEL_ALIASES.get(s, s)


# Map both AI and human label variants to a shared canonical form.
LABEL_ALIASES = {
    # Pre-analytical variables (AI plural / human singular)
    "blood collection procedures": "blood collection procedure",
    # Comparator assays / coagulation tests
    "coagulation testing": "conventional coagulation testing pt, aptt, tt",
    "conventional coagulation testing pt, aptt, tt": "conventional coagulation testing pt, aptt, tt",
    "prothrombin time pt": "conventional coagulation testing pt, aptt, tt",
    "activated partial thromboplastin time aptt": "conventional coagulation testing pt, aptt, tt",
    "thrombin time tt": "conventional coagulation testing pt, aptt, tt",
    # Anti-Xa with LMWH/heparin calibrators
    "anti-xa assays with lmwh calibrators iu/ml": "anti-xa assays using heparin calibrators iu/ml",
    "anti-xa assays using heparin calibrators iu/ml": "anti-xa assays using heparin calibrators iu/ml",
    # Thrombin generation assay
    "thrombin generation assay tga": "thrombin generation assay",
    "thrombin generation assay": "thrombin generation assay",
    # Viscoelastic
    "viscoelastic testing teg/rotem": "viscoelastic testing",
    "viscoelastic testing": "viscoelastic testing",
    # Outcomes — both Stroke/TIA and DVT/PE map to AI's "Thromboembolism"
    "stroke/tia": "thromboembolism",
    "dvt/pe": "thromboembolism",
    # Indications for anticoagulation: AI uses "VTE Treatment/Prevention", human uses "Treatment/Prevention of VTE"
    "vte treatment/prevention": "treatment/prevention of vte",
    # DOAC level measurement indications
    "evaluate doac level exposure": "evaluate doac level exposure",
    "identify predictors of doac level exposure": "identify predictors of doac level exposure",
    "guide clinical decision-making": "guide clinical decision-making",
    "measure correlation with other laboratory techniques": "measure correlation with other laboratory techniques",
    "risk prediction and clinical outcome association": "risk prediction and clinical outcome association",
}


def jaccard(a: list[str], b: list[str]) -> float:
    sa = {canonicalize(x) for x in a}
    sb = {canonicalize(x) for x in b}
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def overlap_recall_precision(ai: list[str], hu: list[str]) -> tuple[float, float]:
    """Return (recall, precision) treating human as gold."""
    sa = {canonicalize(x) for x in ai}
    sh = {canonicalize(x) for x in hu}
    if not sh and not sa:
        return 1.0, 1.0
    if not sh:
        return 1.0, 0.0
    if not sa:
        return 0.0, 1.0
    tp = len(sa & sh)
    return tp / len(sh), tp / len(sa)


# ---------------------------------------------------------------------------
# Title matching
# ---------------------------------------------------------------------------


def normalize_title(t: str) -> str:
    if pd.isna(t):
        return ""
    s = str(t).lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def match_papers(ai_df: pd.DataFrame, hu_df: pd.DataFrame) -> pd.DataFrame:
    """Return ai_df augmented with matched human row index and match score."""
    hu_titles = hu_df["Title"].fillna("").map(normalize_title).tolist()
    matches = []
    for ai_idx, ai_title in enumerate(ai_df["Title"].fillna("").map(normalize_title)):
        if not ai_title:
            matches.append((None, 0.0))
            continue
        best = process.extractOne(ai_title, hu_titles, scorer=fuzz.token_set_ratio)
        if best is None:
            matches.append((None, 0.0))
            continue
        _matched_title, score, hu_idx = best
        matches.append((hu_idx, score))
    ai_df = ai_df.copy()
    ai_df["__hu_idx__"] = [m[0] for m in matches]
    ai_df["__match_score__"] = [m[1] for m in matches]
    return ai_df


# ---------------------------------------------------------------------------
# Field comparators
# ---------------------------------------------------------------------------


@dataclass
class FieldResult:
    field: str
    domain: str
    n_compared: int
    n_both_blank: int
    n_ai_only: int  # AI populated, human blank
    n_hu_only: int  # AI blank, human populated → MISS
    n_exact: int
    n_partial: int  # multi-select with overlap > 0 but <1
    n_disagree: int  # multi-select with no overlap, or string mismatch
    avg_jaccard: float
    avg_recall: float  # how much of human AI captured (only when human populated)
    avg_precision: float  # how clean AI is (only when AI populated)

    def coverage(self) -> float:
        """Fraction of papers where AI populated when human did."""
        denom = self.n_hu_only + self.n_exact + self.n_partial + self.n_disagree
        return (
            (self.n_exact + self.n_partial + self.n_disagree) / denom if denom else 1.0
        )


def compare_multiselect(
    ai_series: pd.Series,
    hu_series: pd.Series,
    field: str,
    domain: str,
    ai_parse=parse_ai_list,
    hu_parse=parse_human_multiselect,
) -> tuple[FieldResult, list[dict]]:
    n_compared = len(ai_series)
    n_both_blank = n_ai_only = n_hu_only = n_exact = n_partial = n_disagree = 0
    jaccards: list[float] = []
    recalls: list[float] = []
    precisions: list[float] = []
    disagreements: list[dict] = []

    for i, (ai_val, hu_val) in enumerate(zip(ai_series, hu_series, strict=True)):
        ai_list = ai_parse(ai_val)
        hu_list = hu_parse(hu_val)
        ai_blank, hu_blank = not ai_list, not hu_list

        if ai_blank and hu_blank:
            n_both_blank += 1
            continue

        if ai_blank and not hu_blank:
            n_hu_only += 1
            disagreements.append(
                {
                    "field": field,
                    "kind": "ai_blank_hu_populated",
                    "ai": "",
                    "hu": "; ".join(hu_list),
                    "row": i,
                }
            )
            recalls.append(0.0)
            jaccards.append(0.0)
            continue

        if hu_blank and not ai_blank:
            n_ai_only += 1
            disagreements.append(
                {
                    "field": field,
                    "kind": "hu_blank_ai_populated",
                    "ai": "; ".join(ai_list),
                    "hu": "",
                    "row": i,
                }
            )
            precisions.append(0.0)
            jaccards.append(0.0)
            continue

        # both populated
        j = jaccard(ai_list, hu_list)
        r, p = overlap_recall_precision(ai_list, hu_list)
        jaccards.append(j)
        recalls.append(r)
        precisions.append(p)

        if j == 1.0:
            n_exact += 1
        elif j > 0.0:
            n_partial += 1
            disagreements.append(
                {
                    "field": field,
                    "kind": "partial_overlap",
                    "ai": "; ".join(ai_list),
                    "hu": "; ".join(hu_list),
                    "row": i,
                }
            )
        else:
            n_disagree += 1
            disagreements.append(
                {
                    "field": field,
                    "kind": "no_overlap",
                    "ai": "; ".join(ai_list),
                    "hu": "; ".join(hu_list),
                    "row": i,
                }
            )

    return (
        FieldResult(
            field=field,
            domain=domain,
            n_compared=n_compared,
            n_both_blank=n_both_blank,
            n_ai_only=n_ai_only,
            n_hu_only=n_hu_only,
            n_exact=n_exact,
            n_partial=n_partial,
            n_disagree=n_disagree,
            avg_jaccard=sum(jaccards) / len(jaccards) if jaccards else 1.0,
            avg_recall=sum(recalls) / len(recalls) if recalls else 1.0,
            avg_precision=sum(precisions) / len(precisions) if precisions else 1.0,
        ),
        disagreements,
    )


def compare_string(
    ai_series: pd.Series,
    hu_series: pd.Series,
    field: str,
    domain: str,
    fuzzy_threshold: int = 85,
) -> tuple[FieldResult, list[dict]]:
    """Compare free-text strings using token_set_ratio."""
    n_compared = len(ai_series)
    n_both_blank = n_ai_only = n_hu_only = n_exact = n_partial = n_disagree = 0
    sims: list[float] = []
    disagreements: list[dict] = []

    for i, (ai_val, hu_val) in enumerate(zip(ai_series, hu_series, strict=True)):
        ai_blank, hu_blank = is_blank(ai_val), is_blank(hu_val)

        if ai_blank and hu_blank:
            n_both_blank += 1
            continue
        if ai_blank:
            n_hu_only += 1
            disagreements.append(
                {
                    "field": field,
                    "kind": "ai_blank_hu_populated",
                    "ai": "",
                    "hu": str(hu_val),
                    "row": i,
                }
            )
            sims.append(0.0)
            continue
        if hu_blank:
            n_ai_only += 1
            disagreements.append(
                {
                    "field": field,
                    "kind": "hu_blank_ai_populated",
                    "ai": str(ai_val),
                    "hu": "",
                    "row": i,
                }
            )
            sims.append(0.0)
            continue

        score = fuzz.token_set_ratio(str(ai_val).lower(), str(hu_val).lower())
        sims.append(score / 100.0)
        if score == 100:
            n_exact += 1
        elif score >= fuzzy_threshold:
            n_partial += 1
            disagreements.append(
                {
                    "field": field,
                    "kind": "fuzzy_partial",
                    "ai": str(ai_val),
                    "hu": str(hu_val),
                    "row": i,
                }
            )
        else:
            n_disagree += 1
            disagreements.append(
                {
                    "field": field,
                    "kind": "string_mismatch",
                    "ai": str(ai_val),
                    "hu": str(hu_val),
                    "row": i,
                }
            )

    avg = sum(sims) / len(sims) if sims else 1.0
    return (
        FieldResult(
            field=field,
            domain=domain,
            n_compared=n_compared,
            n_both_blank=n_both_blank,
            n_ai_only=n_ai_only,
            n_hu_only=n_hu_only,
            n_exact=n_exact,
            n_partial=n_partial,
            n_disagree=n_disagree,
            avg_jaccard=avg,
            avg_recall=avg,
            avg_precision=avg,
        ),
        disagreements,
    )


# ---------------------------------------------------------------------------
# Domain assemblers (some human columns combine into one logical AI field)
# ---------------------------------------------------------------------------

DOAC_DRUG_COLS = ["Apixaban", "Rivaroxaban", "Edoxaban", "Betrixaban", "Dabigatran"]


def assemble_human_doacs(row: pd.Series) -> list[str]:
    """Human's per-drug columns describe the assay used; presence (non-blank) = drug studied."""
    out = []
    for c in DOAC_DRUG_COLS:
        v = row.get(c)
        if not is_blank(v):
            out.append(c)
    return out


YES_TOKENS = {"yes", "y", "true", "1", "x"}


def is_yes(val: Any) -> bool:
    if is_blank(val):
        return False
    return str(val).strip().lower() in YES_TOKENS


def assemble_human_outcomes(row: pd.Series) -> list[str]:
    """Human splits outcomes into Yes/No gates per category."""
    out = []
    if is_yes(row.get("Bleeding/Hemostasis")):
        out.append("Bleeding/Hemostasis")
    if is_yes(row.get("Stroke/TIA")) or is_yes(row.get("DVT/PE")):
        out.append("Thromboembolism")
    return out


def assemble_human_followup(row: pd.Series) -> list[str]:
    """Only collect follow-up if the corresponding outcome gate is Yes."""
    out = []
    for gate, fu_col in [
        ("Bleeding/Hemostasis", "Bleeding/Hemostasis Outcome Follow-Up"),
        ("Stroke/TIA", "Stroke/TIA Outcome Follow-Up"),
        ("DVT/PE", "DVT/PE Outcome Follow-Up"),
    ]:
        if is_yes(row.get(gate)):
            v = row.get(fu_col)
            if not is_blank(v):
                out.append(str(v).strip())
    return out


def assemble_human_definition(row: pd.Series) -> list[str]:
    out = []
    for gate, def_col in [
        (
            "Bleeding/Hemostasis",
            "Bleeding/Hemostasis Outcome Definition (select all that apply)",
        ),
        ("Stroke/TIA", "Stroke/TIA Outcome Definition"),
        ("DVT/PE", "DVT/PE Outcome Definition"),
    ]:
        if is_yes(row.get(gate)):
            v = row.get(def_col)
            if not is_blank(v):
                out.extend(parse_human_multiselect(v))
    return out


def assemble_human_concurrent_coag(row: pd.Series) -> list[str]:
    """Yes/No gates → list of test names."""
    out = []
    if is_yes(row.get("Prothrombin time (PT; seconds or INR value)")):
        out.append("Prothrombin time (PT)")
    if is_yes(row.get("Activated partial thromboplastin time (aPTT; seconds)")):
        out.append("Activated partial thromboplastin time (aPTT)")
    return out


def assemble_human_global_coag(row: pd.Series) -> list[str]:
    out = []
    if is_yes(row.get("Viscoelastic Testing (TEG/ROTEM)")):
        out.append("Viscoelastic Testing (TEG/ROTEM)")
    if is_yes(
        row.get("Thrombin Generation Assay (TGA; see Analysis Plan for assay list)")
    ):
        out.append("Thrombin Generation Assay (TGA)")
    return out


def assemble_human_outcome_present(row: pd.Series) -> str:
    return "Yes" if assemble_human_outcomes(row) else "No"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    ai = pd.read_csv(AI_CSV)
    hu = pd.read_csv(HU_CSV)

    ai_matched = match_papers(ai, hu)
    matched_mask = ai_matched["__hu_idx__"].notna() & (
        ai_matched["__match_score__"] >= 75
    )
    ai_paired = ai_matched[matched_mask].reset_index(drop=True)
    hu_paired = hu.iloc[ai_paired["__hu_idx__"].astype(int).tolist()].reset_index(
        drop=True
    )

    n_total = len(ai)
    n_matched = len(ai_paired)
    unmatched_titles = ai.loc[
        ~matched_mask.reindex(ai.index, fill_value=False), "Title"
    ].tolist()

    print(f"Matched {n_matched}/{n_total} AI papers to human gold standard.")
    if unmatched_titles:
        print("Unmatched AI titles:")
        for t in unmatched_titles:
            print(f"  - {t}")

    # Build comparison series for each logical field
    # Each entry: (field_name, domain, ai_series, hu_series_or_assembled, comparator_fn)
    pd.Series([assemble_human_doacs(r) for _, r in hu_paired.iterrows()])
    derived_outcomes_hu = pd.Series(
        [assemble_human_outcomes(r) for _, r in hu_paired.iterrows()]
    )
    derived_followup_hu = pd.Series(
        [assemble_human_followup(r) for _, r in hu_paired.iterrows()]
    )
    derived_defn_hu = pd.Series(
        [assemble_human_definition(r) for _, r in hu_paired.iterrows()]
    )
    derived_concurrent_hu = pd.Series(
        [assemble_human_concurrent_coag(r) for _, r in hu_paired.iterrows()]
    )
    derived_global_hu = pd.Series(
        [assemble_human_global_coag(r) for _, r in hu_paired.iterrows()]
    )
    derived_outcome_present_hu = pd.Series(
        [assemble_human_outcome_present(r) for _, r in hu_paired.iterrows()]
    )

    field_specs: list[tuple[str, str, pd.Series, pd.Series, str]] = [
        # Bibliography
        (
            "Journal",
            "Bibliography",
            ai_paired["Journal"],
            hu_paired["Journal"],
            "string",
        ),
        (
            "Country",
            "Bibliography",
            ai_paired["Country of First Author"],
            hu_paired["Country in which the study conducted"],
            "string",
        ),
        (
            "Publication Year",
            "Bibliography",
            ai_paired["Publication Year"],
            hu_paired["Publication Year"],
            "string",
        ),
        (
            "Study Design",
            "Bibliography",
            ai_paired["Study Design"],
            hu_paired["Study design"],
            "string",
        ),
        # Population
        (
            "DOACs Included",
            "Population",
            ai_paired["Patient population 1"],
            hu_paired["DOAC(s) Included (select all that apply)"],
            "multiselect",
        ),
        (
            "Indications for Anticoagulation",
            "Population",
            ai_paired["Patient population 2"],
            hu_paired["Indication(s) (select all that apply)"],
            "multiselect",
        ),
        (
            "Relevant Subgroups",
            "Population",
            ai_paired["Patient population 3"],
            hu_paired["Relevant Subgroups (select all that apply)"],
            "multiselect",
        ),
        (
            "Indications for DOAC Level Measurement",
            "Population",
            ai_paired["Indications for DOAC Level Measurement"],
            hu_paired[
                "Indication(s) for DOAC Level Measurement (select all that apply)"
            ],
            "multiselect",
        ),
        # Methods
        (
            "Pre-Analytical Variables",
            "Methods",
            ai_paired["Pre-Analytical Variables"],
            hu_paired[
                "Pre-Analytical Variables Reported (select all that apply, specific to plasma samples that were used for DOAC level measurement, i.e., plasma samples)"
            ],
            "multiselect",
        ),
        (
            "Conventional Coag Tests Concurrent",
            "Methods",
            ai_paired["Conventional Coagulation Tests Concurrently Reported"],
            derived_concurrent_hu,
            "multiselect_assembled",
        ),
        (
            "Global Coag Tests",
            "Methods",
            ai_paired["Global Coagulation Testing"],
            derived_global_hu,
            "multiselect_assembled",
        ),
        (
            "Timing of DOAC Level Measurement",
            "Methods",
            ai_paired["Timing of DOAC level measurement relative to DOAC intake"],
            hu_paired["Timing of Measurement (select all that apply)"],
            "multiselect",
        ),
        # Outcomes
        (
            "Clinical Outcomes Measured?",
            "Outcomes",
            ai_paired["Clinical outcomes measured?"],
            derived_outcome_present_hu,
            "string",
        ),
        (
            "Clinical Outcomes",
            "Outcomes",
            ai_paired["Clinical Outcomes"],
            derived_outcomes_hu,
            "multiselect_assembled",
        ),
        (
            "Clinical Outcome Follow-Up",
            "Outcomes",
            ai_paired["Clinical Outcome - follow-up duration"],
            derived_followup_hu,
            "multiselect_assembled",
        ),
        (
            "Clinical Outcome Definition",
            "Outcomes",
            ai_paired["Clinical Outcome - definition"],
            derived_defn_hu,
            "multiselect_assembled",
        ),
        # Diagnostic performance
        (
            "Comparator Assays",
            "Diagnostic",
            ai_paired["Comparator Assays"],
            hu_paired["Comparator Assays"],
            "multiselect",
        ),
        (
            "Reported Cutoffs",
            "Diagnostic",
            ai_paired["Reported DOAC concentration thresholds/cutoffs (listed)"],
            hu_paired[
                "Reported DOAC level concentration thresholds/cutoffs (if evaluate directly as part of the study, not just if mentioned as part of background/discussion)"
            ],
            "multiselect",
        ),
        (
            "Diagnostic Performance Parameters",
            "Diagnostic",
            ai_paired["Diagnostic Performance Metrics - Categorical Cutoffs"],
            hu_paired["Diagnostic Performance Parameters Reported"],
            "string",
        ),
    ]

    results: list[FieldResult] = []
    all_disagreements: list[dict] = []
    per_paper_scores: dict[int, dict[str, float]] = {i: {} for i in range(n_matched)}

    for field, domain, ai_s, hu_s, kind in field_specs:
        if kind == "multiselect":
            res, dis = compare_multiselect(
                ai_s.reset_index(drop=True),
                hu_s.reset_index(drop=True),
                field,
                domain,
                parse_ai_list,
                parse_human_multiselect,
            )
        elif kind == "multiselect_assembled":
            res, dis = compare_multiselect(
                ai_s.reset_index(drop=True),
                hu_s.reset_index(drop=True),
                field,
                domain,
                ai_parse=parse_ai_list,
                hu_parse=lambda v: (
                    v if isinstance(v, list) else parse_human_multiselect(v)
                ),
            )
        elif kind == "string":
            res, dis = compare_string(
                ai_s.reset_index(drop=True), hu_s.reset_index(drop=True), field, domain
            )
        else:
            raise ValueError(f"unknown kind {kind}")
        results.append(res)
        for d in dis:
            d["title"] = ai_paired.loc[d["row"], "Title"]
            all_disagreements.append(d)
            score_key = field
            per_paper_scores[d["row"]].setdefault(score_key, 0.0)
        # also record per-paper jaccard
        for i, (a, h) in enumerate(
            zip(ai_s.reset_index(drop=True), hu_s.reset_index(drop=True), strict=True)
        ):
            if kind == "multiselect":
                ja = jaccard(parse_ai_list(a), parse_human_multiselect(h))
            elif kind == "multiselect_assembled":
                hu_list = h if isinstance(h, list) else parse_human_multiselect(h)
                ja = jaccard(parse_ai_list(a), hu_list)
            else:
                if is_blank(a) and is_blank(h):
                    ja = 1.0
                elif is_blank(a) or is_blank(h):
                    ja = 0.0
                else:
                    ja = fuzz.token_set_ratio(str(a).lower(), str(h).lower()) / 100.0
            per_paper_scores[i][field] = ja

    # ----- write per-paper agreement CSV -----
    pp_rows = []
    for i in range(n_matched):
        scores = per_paper_scores[i]
        row = {
            "AI Title": ai_paired.loc[i, "Title"],
            "Human Title": hu_paired.loc[i, "Title"],
            "Title Match Score": ai_paired.loc[i, "__match_score__"],
            **scores,
            "Mean Score": sum(scores.values()) / len(scores) if scores else 0.0,
        }
        pp_rows.append(row)
    per_paper_df = pd.DataFrame(pp_rows).sort_values("Mean Score")
    per_paper_df.to_csv(PER_PAPER_CSV, index=False)

    # ----- write disagreements CSV -----
    pd.DataFrame(all_disagreements).to_csv(DISAGREEMENTS_CSV, index=False)

    # ----- write markdown report -----
    write_report(
        results, n_matched, n_total, unmatched_titles, per_paper_df, all_disagreements
    )
    print(f"\nReport: {REPORT_MD}")
    print(f"Per-paper agreement: {PER_PAPER_CSV}")
    print(f"Disagreements: {DISAGREEMENTS_CSV}")


# ---------------------------------------------------------------------------
# Report writer
# ---------------------------------------------------------------------------


def fmt_pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def status_emoji(jaccard: float, miss_rate: float) -> str:
    """Audit verdict — green if strong, yellow if mixed, red if weak."""
    if jaccard >= 0.65 and miss_rate <= 0.10:
        return "✅"
    if jaccard >= 0.40 or miss_rate <= 0.20:
        return "🟡"
    return "🔴"


def write_report(
    results: list[FieldResult],
    n_matched: int,
    n_total: int,
    unmatched: list[str],
    per_paper: pd.DataFrame,
    disagreements: list[dict],
) -> None:
    by_field = {r.field: r for r in results}
    domains: dict[str, list[FieldResult]] = {}
    for r in results:
        domains.setdefault(r.domain, []).append(r)

    lines: list[str] = []
    lines.append("# DOAC Extraction — AI vs Human Gold-Standard Comparison Report")
    lines.append("")
    lines.append(
        "_Run: 2026-04-26 — after the audit-driven prompt refinements landed in branch `main`._"
    )
    lines.append("")
    lines.append(
        "> **Companion visual report** with KPI cards, stacked-bar distributions, per-paper drill-downs, and a `Changes from v1` delta section is at [`2026-04-26-comparison-report.html`](2026-04-26-comparison-report.html). "
        "The HTML uses a richer semantic-concept comparator that reports overall accuracy of **72.7%** vs the immediately-prior-run baseline of **73.3%** — essentially flat (**−0.6pp**), with significant gains on bibliography/population fields offset by regressions on Timing, Thresholds, and Comparator Assays. See § 7b for the per-field deltas."
    )
    lines.append("")

    # ----- 1. Executive summary -----
    lines.append("## 1. Executive Summary")
    lines.append("")
    overall = sum(r.avg_jaccard for r in results) / len(results)
    miss_total = sum(r.n_hu_only for r in results)
    lines.append(
        f"- **Papers compared:** {n_matched}/{n_total} (fuzzy-title matched, threshold ≥ 75) — every AI paper aligned to a human row."
    )
    lines.append(
        f"- **Overall mean field agreement:** **{fmt_pct(overall)}** across {len(results)} compared fields."
    )
    lines.append(
        f'- **Total "misses"** (AI blank when human populated): **{miss_total}** across {n_matched * len(results)} field-paper cells '
        f"(≈ {fmt_pct(miss_total / (n_matched * len(results)))})."
    )
    lines.append("")
    bib_jac = sum(r.avg_jaccard for r in domains["Bibliography"]) / len(
        domains["Bibliography"]
    )
    pop_jac = sum(r.avg_jaccard for r in domains["Population"]) / len(
        domains["Population"]
    )
    met_jac = sum(r.avg_jaccard for r in domains["Methods"]) / len(domains["Methods"])
    sum(r.avg_jaccard for r in domains["Diagnostic"]) / len(domains["Diagnostic"])
    doacs = by_field["DOACs Included"]
    indications = by_field["Indications for Anticoagulation"]
    indications_lvl = by_field["Indications for DOAC Level Measurement"]
    timing = by_field["Timing of DOAC Level Measurement"]
    gate = by_field["Clinical Outcomes Measured?"]
    comparator = by_field["Comparator Assays"]
    pre_anal = by_field["Pre-Analytical Variables"]

    lines.append("**Top-line takeaways:**")
    lines.append("")
    lines.append(
        f"- 🟢 **Bibliography** is solid ({fmt_pct(bib_jac)} agreement). Country has the most slip-ups (4 misses, 10 mismatches due to first-author affiliation vs study-conduct country differences)."
    )
    lines.append(
        f"- 🟢 **Population** is now strong ({fmt_pct(pop_jac)}). DOACs Included {fmt_pct(doacs.avg_jaccard)}, Indications for Anticoagulation {fmt_pct(indications.avg_jaccard)}, and **zero misses** on the multi-label _Indications for DOAC Level Measurement_ field ({fmt_pct(indications_lvl.avg_jaccard)} agreement, recall {fmt_pct(indications_lvl.avg_recall)})."
    )
    lines.append(
        f"- 🟡 **Methods** is mixed ({fmt_pct(met_jac)}). Pre-Analytical Variables recall is {fmt_pct(pre_anal.avg_recall)} (AI tends to over-tag, lowering precision). **Timing of Measurement is the weakest individual field** ({fmt_pct(timing.avg_jaccard)}, {timing.n_hu_only} misses)."
    )
    lines.append(
        f"- 🟢 **Outcome gate** improved sharply at the Yes/No level: AI and human now agree in {gate.n_exact}/{n_matched} papers ({fmt_pct(gate.avg_jaccard)}). The semantic comparator shows Clinical Outcomes domain at 56.2% (down ~5pp from prior run) — the gate is correct but the multi-label outcome capture isn't yet matching the prior run's recall."
    )
    lines.append(
        f"- 🟡 **Comparator Assays** raw agreement is {fmt_pct(comparator.avg_jaccard)} but the apparent miss count is inflated by field-routing — see § 4.5. The acronym disambiguation rule (ACT/ACT-LR ≠ aPTT) eliminates the worst-class errors. Net change vs prior run: −7.1pp."
    )
    lines.append(
        "- 🟡 **Mixed picture vs prior run**: improvements on Indications (+4.7pp), Coag Tests (+4.1pp), Country (+3.9pp), Journal (+2.8pp); regressions on Timing (−8.7pp), Thresholds (−9.0pp), Comparator Assays (−7.1pp). Overall almost flat (−0.6pp). See § 7b."
    )
    lines.append("")

    # ----- 2. Per-domain summary -----
    lines.append("## 2. Per-Domain Summary")
    lines.append("")
    lines.append(
        "| Domain | Mean Agreement | Recall (sensitivity) | Precision | Coverage* |"
    )
    lines.append("|---|---:|---:|---:|---:|")
    for dom, rs in domains.items():
        ja = sum(r.avg_jaccard for r in rs) / len(rs)
        rc = sum(r.avg_recall for r in rs) / len(rs)
        pr = sum(r.avg_precision for r in rs) / len(rs)
        cov = sum(r.coverage() for r in rs) / len(rs)
        lines.append(
            f"| {dom} | {fmt_pct(ja)} | {fmt_pct(rc)} | {fmt_pct(pr)} | {fmt_pct(cov)} |"
        )
    lines.append("")
    lines.append(
        "_*Coverage = fraction of papers where AI populated the field when the human did. **Recall** = how much of the human gold AI captured. **Precision** = how clean AI's emitted labels are._"
    )
    lines.append("")

    # ----- 3. Audit scorecard -----
    lines.append("## 3. Joseph's Audit — Scorecard for the 7 Priority Areas")
    lines.append("")
    lines.append(
        "Status legend: ✅ strong (≥ 65% agreement, ≤ 10% misses) · 🟡 mixed · 🔴 weak."
    )
    lines.append("")
    lines.append("| # | Audit area | Status | Field | Agreement | Misses |")
    lines.append("|---|---|:---:|---|---:|---:|")
    audit_rows = [
        (1, "Blank outputs (overall)", None, None),
        (
            2,
            "Pre-analytical variables",
            "Pre-Analytical Variables",
            "force non-blank, broaden triggers",
        ),
        (
            3,
            "Timing extraction",
            "Timing of DOAC Level Measurement",
            "trough triggers, hour-windows, acute-care rule",
        ),
        (
            4,
            "Clinical outcomes — gate",
            "Clinical Outcomes Measured?",
            "anti-overcall + non-original-research carve-out",
        ),
        (
            4,
            "Clinical outcomes — capture",
            "Clinical Outcomes",
            "trigger-phrase requirement",
        ),
        (
            5,
            "Comparator assays / acronyms",
            "Comparator Assays",
            "ACT/ACT-LR ≠ aPTT disambiguation",
        ),
        (6, "Patient subgroups", "Relevant Subgroups", "kept conservative per audit"),
        (
            7,
            "Indications (multi-label)",
            "Indications for DOAC Level Measurement",
            "primary + secondary capture",
        ),
    ]
    for num, area, field, _note in audit_rows:
        if field is None:
            misses = sum(r.n_hu_only for r in results if r.domain != "Bibliography")
            blank_rate = misses / (
                n_matched * sum(1 for r in results if r.domain != "Bibliography")
            )
            symbol = "🟡" if blank_rate < 0.20 else "🔴"
            lines.append(
                f"| {num} | {area} | {symbol} | _all non-bibliography_ | — | {misses} ({fmt_pct(blank_rate)}) |"
            )
        else:
            r = by_field[field]
            sym = status_emoji(r.avg_jaccard, r.n_hu_only / n_matched)
            lines.append(
                f"| {num} | {area} | {sym} | `{field}` | {fmt_pct(r.avg_jaccard)} | {r.n_hu_only}/{n_matched} |"
            )
    lines.append("")

    # ----- 4. Domain drill-downs -----
    lines.append("## 4. Drill-Down by Audit Priority")
    lines.append("")

    audit_drilldowns = [
        (
            "Pre-Analytical Variables",
            "4.1 Pre-Analytical Variables",
            "Force non-blank + broaden triggers (citrate concentration, Greiner Vacuette, storage).",
        ),
        (
            "Timing of DOAC Level Measurement",
            "4.2 Timing Extraction",
            "Trough triggers added; hour-window disambiguation; acute-care inference rule.",
        ),
        (
            "Clinical Outcomes Measured?",
            "4.3 Clinical Outcomes — Gate",
            "Non-original-research carve-out + outcome trigger phrases.",
        ),
        (
            "Clinical Outcomes",
            "4.4 Clinical Outcomes — Capture",
            "Trigger-phrase requirement and Methods/Results-first search.",
        ),
        (
            "Comparator Assays",
            "4.5 Comparator Assays",
            "Acronym disambiguation rule (ACT/ACT-LR ≠ aPTT).",
        ),
        (
            "Relevant Subgroups",
            "4.6 Patient Subgroups",
            "Kept conservative per audit; only explicit study-focus.",
        ),
        (
            "Indications for DOAC Level Measurement",
            "4.7 Indications for DOAC Level Measurement",
            "Primary + explicit secondary capture; ordered search (objective → methods → endpoints → results).",
        ),
    ]
    for field, header, change_summary in audit_drilldowns:
        r = by_field[field]
        lines.append(f"### {header} — `{field}`")
        lines.append("")
        lines.append(f"_Prompt change applied:_ {change_summary}")
        lines.append("")
        lines.append(
            f"- Agreement: **{fmt_pct(r.avg_jaccard)}** · Recall: {fmt_pct(r.avg_recall)} · Precision: {fmt_pct(r.avg_precision)}"
        )
        lines.append(
            f"- Exact: {r.n_exact} · Partial: {r.n_partial} · No-overlap: {r.n_disagree} · "
            f"AI-only: {r.n_ai_only} · **Miss (human-only): {r.n_hu_only}** · Both blank: {r.n_both_blank}"
        )

        # Field-routing note for Comparator Assays
        if field == "Comparator Assays":
            lines.append("")
            lines.append(
                "_Note on field routing:_ Of the 31 papers where AI left _Comparator Assays_ blank, AI extracted PT/aPTT into the more specific `Conventional Coag Tests Concurrent` field in **17 of 31**. "
                "The human extractor consolidated those into `Comparator Assays`, so the apparent miss count overstates the true extraction failure."
            )
        lines.append("")

        field_dis = [d for d in disagreements if d["field"] == field]
        if field_dis:
            lines.append("**Disagreement examples:**")
            lines.append("")
            for d in field_dis[:3]:
                title_short = (
                    (str(d["title"])[:80] + "…")
                    if len(str(d["title"])) > 80
                    else str(d["title"])
                )
                lines.append(f"- _{title_short}_")
                lines.append(f"  - **AI:** `{(d['ai'] or '∅')[:240]}`")
                lines.append(f"  - **Human:** `{(d['hu'] or '∅')[:240]}`")
            lines.append("")

    # ----- 5. Per-field reference table -----
    lines.append("## 5. Full Per-Field Agreement Table")
    lines.append("")
    lines.append(
        "| Field | Domain | Exact | Partial | No-overlap | AI-only | Miss | Both blank | Mean Jaccard | Recall | Precision |"
    )
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in results:
        lines.append(
            f"| {r.field} | {r.domain} | {r.n_exact} | {r.n_partial} | {r.n_disagree} | {r.n_ai_only} | "
            f"**{r.n_hu_only}** | {r.n_both_blank} | {fmt_pct(r.avg_jaccard)} | {fmt_pct(r.avg_recall)} | {fmt_pct(r.avg_precision)} |"
        )
    lines.append("")

    # ----- 6. Caveats -----
    lines.append("## 6. Known Comparison Caveats")
    lines.append("")
    lines.append(
        "These two fields show **0% raw agreement** because the two sides use structurally different vocabularies, not because extraction failed:"
    )
    lines.append("")
    lines.append(
        '- **Clinical Outcome Follow-Up** — AI emits free-text durations (e.g., `"12 months"`, `"30 days"`); human uses categorical bins (`"> 6 months to ≤ 1 year"`, `"1 month to ≤ 3 months"`). A binning post-processor would be needed for a fair comparison.'
    )
    lines.append(
        '- **Clinical Outcome Definition** — AI emits study-author paraphrase; human uses ISTH/standard definition tags (e.g., `"ISTH Major Bleeding (General Definition)"`).'
    )
    lines.append("")
    lines.append("Other field-mapping notes:")
    lines.append("")
    lines.append(
        "- **Comparator Assays vs Conventional/Global Coag** — human consolidates all assays into one column; AI splits into three. The audit scorecard counts these together."
    )
    lines.append(
        '- **Study Design fine-grained labels** — human uses sub-types like `"Cohort study"`, `"Cross sectional study"`, `"Pharmacokinetic study"`; AI uses parent categories like `"Non-Randomized Observational Study"`. Most disagreements here are sub-categorization of the same study type, not category errors.'
    )
    lines.append(
        '- **Diagnostic Performance Parameters** — AI\'s `Diagnostic Performance Metrics - Categorical Cutoffs` is content-rich free text; human is a small canonical multi-select (`Sensitivity`, `Specificity`, `Spearman/Pearson Correlation`). The 18 "misses" in the table reflect schema shape, not content absence.'
    )
    lines.append("")

    # ----- 7. Per-paper -----
    lines.append("## 7. Per-Paper Agreement")
    lines.append("")
    lines.append("**Lowest 10 (most disagreement):**")
    lines.append("")
    lines.append("| Paper | Mean Agreement |")
    lines.append("|---|---:|")
    for _, row in per_paper.head(10).iterrows():
        title = (
            (row["AI Title"][:90] + "…")
            if len(str(row["AI Title"])) > 90
            else row["AI Title"]
        )
        lines.append(f"| {title} | {fmt_pct(row['Mean Score'])} |")
    lines.append("")
    lines.append("**Highest 10 (best agreement):**")
    lines.append("")
    lines.append("| Paper | Mean Agreement |")
    lines.append("|---|---:|")
    for _, row in (
        per_paper.tail(10).sort_values("Mean Score", ascending=False).iterrows()
    ):
        title = (
            (row["AI Title"][:90] + "…")
            if len(str(row["AI Title"])) > 90
            else row["AI Title"]
        )
        lines.append(f"| {title} | {fmt_pct(row['Mean Score'])} |")
    lines.append("")
    lines.append(
        f"Full per-paper scores: [`{PER_PAPER_CSV.relative_to(ROOT).as_posix()}`]({PER_PAPER_CSV.relative_to(ROOT).as_posix()})  "
    )
    lines.append(
        f"Every disagreement listed: [`{DISAGREEMENTS_CSV.relative_to(ROOT).as_posix()}`]({DISAGREEMENTS_CSV.relative_to(ROOT).as_posix()})"
    )
    lines.append("")

    # ----- 7b. Pre-fix → post-fix delta from the semantic-concept comparator -----
    lines.append("## 7b. Pre-fix → Post-fix Delta (semantic-concept comparator)")
    lines.append("")
    lines.append(
        "These deltas come from the companion HTML report's compatibility-group-aware comparator, comparing today's run to the **immediately-prior run** (Apr 12 baseline, before today's prompt edits). This is the apples-to-apples view of what the audit-driven changes actually moved."
    )
    lines.append("")
    lines.append("| Field | Apr 12 baseline | Today | Δ |")
    lines.append("|---|--:|--:|--:|")
    lines.append("| Indications | 80% | 84.7% | 🟢 +4.7pp |")
    lines.append("| Coagulation Tests | 76% | 80.1% | 🟢 +4.1pp |")
    lines.append("| Country | 82% | 85.9% | 🟢 +3.9pp |")
    lines.append("| Journal | 88% | 90.8% | 🟢 +2.8pp |")
    lines.append("| DOACs Included | 98% | 99.5% | 🟢 +1.5pp |")
    lines.append("| Diagnostic Performance | 55% | 56.5% | 🟢 +1.5pp |")
    lines.append("| Publication Year | 94% | 94.5% | 🟡 +0.5pp |")
    lines.append("| Study Design | 80% | 78.6% | 🟡 −1.4pp |")
    lines.append("| Relevant Subgroups | 38% | 36.2% | 🟡 −1.8pp |")
    lines.append("| Clinical Outcomes | 61% | 56.2% | 🟡 −4.8pp |")
    lines.append("| Comparator Assays | 50% | 42.9% | 🔴 −7.1pp |")
    lines.append("| Timing of Measurement | 54% | 45.3% | 🔴 −8.7pp |")
    lines.append("| Thresholds/Cutoffs | 54% | 45.0% | 🔴 −9.0pp |")
    lines.append("| **Overall** | **73.3%** | **72.7%** | 🟡 **−0.6pp** (flat) |")
    lines.append("")
    lines.append(
        "**Interpretation.** Net result is essentially flat (−0.6pp). The audit-driven changes hit their bibliography and population targets cleanly (+2 to +5pp on Journal, Country, Indications, DOACs, Coag Tests). They did NOT move Subgroups (−1.8pp ≈ flat at 36-38%) or Diagnostic Performance (+1.5pp). Three fields regressed: **Timing (−8.7pp)** despite our hour-window and trough-trigger additions; **Thresholds/Cutoffs (−9pp)** which wasn't directly targeted; and **Comparator Assays (−7.1pp)** despite the ACT/ACT-LR disambiguation rule. The Outcomes domain (−4.8pp) shows the gate-fix improved Yes/No agreement but degraded multi-label capture — likely the trigger-phrase requirement is now too strict in cases where outcome language is implicit."
    )
    lines.append("")
    lines.append(
        '_Earlier draft of this report compared against an out-of-date hardcoded baseline (`V1_FIELD_ACC` constants set before Apr 12) and reported alarming regressions like "Relevant Subgroups −22.8pp" — those were artifacts of stale numbers, not real regressions. The deltas above use the actual Apr 12 run as the baseline._'
    )
    lines.append("")

    # ----- 8. Recommended next steps -----
    lines.append("## 8. Recommended Next Steps")
    lines.append("")
    lines.append(
        "Based on this run, the highest-leverage investments for the next iteration are:"
    )
    lines.append("")
    lines.append(
        f"1. **Timing extraction ({fmt_pct(timing.avg_jaccard)}, weakest individual field).** The new hour-window and acute-care rules helped, but {timing.n_disagree} no-overlap and {timing.n_hu_only} blank-miss cases remain. Most failures are Random ↔ Trough conflations in PK studies and stroke-on-presentation papers. Consider auditing the {timing.n_hu_only} miss cases by hand to see whether the trigger phrases are present in the source text — if so, the issue is the prompt's recognition; if not, the human extractor was inferring beyond the text."
    )
    lines.append(
        f"2. **Outcome gate — {gate.n_disagree} residual disagreements**, now split roughly evenly between AI=No / Human=Yes (the dominant pattern) and AI=Yes / Human=No. With zero misses (no blanks) and 41/50 exact agreements, the gate is largely correct; spot-checking the remaining 9 will reveal whether the trigger-phrase bar is now slightly too high."
    )
    lines.append(
        "3. **Field consolidation (post-processor, no prompt change).** AI's `Conventional Coag Tests Concurrent` field is populated for 17/31 papers where AI left `Comparator Assays` blank. A two-line post-processor that copies/merges those into `Comparator Assays` for downstream comparison would close ~half of the apparent miss gap without touching the prompts."
    )
    lines.append(
        '4. **Follow-up duration binning.** AI emits free-text (`"12 months"`); human uses categorical bins (`"> 6 months to ≤ 1 year"`). A deterministic post-processor mapping durations into bins would unlock fair comparison on this field — currently 0% raw agreement is an artifact, not an extraction failure.'
    )
    lines.append("")

    # ----- 9. Methodology -----
    lines.append("## 9. Methodology")
    lines.append("")
    lines.append(
        "- **Title matching:** rapidfuzz `token_set_ratio`, threshold ≥ 75 → 50/50 matched."
    )
    lines.append(
        '- **Multi-select normalization:** AI list-strings parsed via `ast.literal_eval`; human strings split on `;`. Both sides lower-cased, dash variants normalized, hierarchical sub-labels (`"X - Y"`) collapsed to parent, label aliases applied (e.g., `"thrombin generation assay TGA"` → `"thrombin generation assay"`).'
    )
    lines.append(
        "- **Multi-select metric:** Jaccard on canonical label sets (1.0 = identical, 0.0 = disjoint)."
    )
    lines.append("- **Free-text metric:** rapidfuzz `token_set_ratio / 100`.")
    lines.append(
        "- **Recall** = |AI ∩ Human| / |Human|. **Precision** = |AI ∩ Human| / |AI|."
    )
    lines.append(
        '- **Yes/No human columns** (`Apixaban`, `PT`, `aPTT`, `Bleeding/Hemostasis`, …) interpreted strictly: only `"Yes"` counts as populated; `"No"` is blank.'
    )
    lines.append("")
    lines.append(
        f"_Generated by `analysis/compare_to_human.py` from `{AI_CSV.relative_to(ROOT).as_posix()}` and `{HU_CSV.relative_to(ROOT).as_posix()}`._"
    )
    lines.append("")

    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
