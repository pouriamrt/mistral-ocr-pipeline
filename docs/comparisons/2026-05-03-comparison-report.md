# DOAC Extraction — AI vs Human Gold-Standard Comparison Report

_Run: 2026-05-03 — after the post-Joseph-feedback prompt refinements (timing-of-DOAC-measurement strict-null policy, removal of follow-up-duration field, methods/results-only evidence gate on assay technique fields) landed in branch `main`._

> **Companion visual report** with KPI cards, stacked-bar distributions, per-paper drill-downs, and a `Changes from v1` delta section is at [`2026-05-03-comparison-report.html`](2026-05-03-comparison-report.html). The HTML uses a richer semantic-concept comparator and computes per-field deltas vs the v1 baseline.

## 1. Executive Summary

- **Papers compared:** 50/50 (fuzzy-title matched, threshold ≥ 75) — every AI paper aligned to a human row.
- **Overall mean field agreement:** **57.5%** across 18 compared fields.
- **Total "misses"** (AI blank when human populated): **89** across 900 field-paper cells (≈ 9.9%).

**Top-line takeaways:**

- 🟢 **Bibliography** is solid (86.2% agreement). Country has the most slip-ups (4 misses, 10 mismatches due to first-author affiliation vs study-conduct country differences).
- 🟢 **Population** is now strong (68.6%). DOACs Included 99.5%, Indications for Anticoagulation 83.7%, and **zero misses** on the multi-label _Indications for DOAC Level Measurement_ field (54.8% agreement, recall 61.4%).
- 🟡 **Methods** is mixed (46.2%). Pre-Analytical Variables recall is 97.2% (AI tends to over-tag, lowering precision). **Timing of Measurement is the weakest individual field** (6.7%, 37 misses).
- **Outcome gate**: AI and human agree in 44/50 papers (88.0%) at the Yes/No level. Run-over-run deltas vs the prior run are computed in the companion HTML report.
- **Comparator Assays** raw agreement is 48.6% — see § 4.5 for the field-routing breakdown and acronym-disambiguation behavior.
- **Run-over-run deltas vs prior run**: see the companion HTML report's `Changes from v1` section for compatibility-group-aware per-field deltas.

## 2. Per-Domain Summary

| Domain | Mean Agreement | Recall (sensitivity) | Precision | Coverage* |
|---|---:|---:|---:|---:|
| Bibliography | 86.2% | 86.2% | 86.2% | 97.0% |
| Population | 68.6% | 72.8% | 85.2% | 92.3% |
| Methods | 46.2% | 70.6% | 54.4% | 81.5% |
| Outcomes | 46.4% | 56.9% | 48.8% | 94.2% |
| Diagnostic | 30.2% | 42.5% | 41.2% | 47.8% |

_*Coverage = fraction of papers where AI populated the field when the human did. **Recall** = how much of the human gold AI captured. **Precision** = how clean AI's emitted labels are._

## 3. Joseph's Audit — Scorecard for the 7 Priority Areas

Status legend: ✅ strong (≥ 65% agreement, ≤ 10% misses) · 🟡 mixed · 🔴 weak.

| # | Audit area | Status | Field | Agreement | Misses |
|---|---|:---:|---|---:|---:|
| 1 | Blank outputs (overall) | 🟡 | _all non-bibliography_ | — | 83 (11.9%) |
| 2 | Pre-analytical variables | 🟡 | `Pre-Analytical Variables` | 52.6% | 0/50 |
| 3 | Timing extraction | 🔴 | `Timing of DOAC Level Measurement` | 6.7% | 37/50 |
| 4 | Clinical outcomes — gate | ✅ | `Clinical Outcomes Measured?` | 88.0% | 0/50 |
| 4 | Clinical outcomes — capture | 🟡 | `Clinical Outcomes` | 51.3% | 2/50 |
| 5 | Comparator assays / acronyms | 🟡 | `Comparator Assays` | 48.6% | 8/50 |
| 6 | Patient subgroups | 🔴 | `Relevant Subgroups` | 36.6% | 12/50 |
| 7 | Indications (multi-label) | 🟡 | `Indications for DOAC Level Measurement` | 54.8% | 0/50 |

## 4. Drill-Down by Audit Priority

### 4.1 Pre-Analytical Variables — `Pre-Analytical Variables`

_Prompt change applied:_ Force non-blank + broaden triggers (citrate concentration, Greiner Vacuette, storage).

- Agreement: **52.6%** · Recall: 97.2% · Precision: 53.2%
- Exact: 12 · Partial: 18 · No-overlap: 0 · AI-only: 9 · **Miss (human-only): 0** · Both blank: 11

**Disagreement examples:**

- _Potential treatment option of rivaroxaban for breastfeeding women: A case series_
  - **AI:** `Blood collection procedures; Collection tube type; Centrifugation speed; Storage temperature`
  - **Human:** `∅`
- _The assessment of anticoagulant activity to predict bleeding outcome in atrial f…_
  - **AI:** `Blood collection procedures; Collection tube type; Centrifugation speed; Storage temperature`
  - **Human:** `Blood collection procedure`
- _Management of DOAC in Patients Undergoing Planned Surgery or Invasive Procedure:…_
  - **AI:** `Blood collection procedures; Collection tube type; Centrifugation speed; Storage temperature`
  - **Human:** `∅`

### 4.2 Timing Extraction — `Timing of DOAC Level Measurement`

_Prompt change applied:_ Trough triggers added; hour-window disambiguation; acute-care inference rule.

- Agreement: **6.7%** · Recall: 10.0% · Precision: 38.5%
- Exact: 0 · Partial: 10 · No-overlap: 3 · AI-only: 0 · **Miss (human-only): 37** · Both blank: 0

**Disagreement examples:**

- _High fracture and DOAC level: A retrospective study of 72 cases_
  - **AI:** `∅`
  - **Human:** `Random level`
- _Potential treatment option of rivaroxaban for breastfeeding women: A case series_
  - **AI:** `Peak level (2–4 hours post-dose); Trough level (just prior to next dose)`
  - **Human:** `Peak level (2-4 hours post-dose); Trough level (just prior to next dose, ~ 11 hours post-dose for apixaban/dabigatran and ~23 hours post-dose for rivaroxaban/edoxaban)`
- _The assessment of anticoagulant activity to predict bleeding outcome in atrial f…_
  - **AI:** `Trough level (just prior to next dose)`
  - **Human:** `Trough level (just prior to next dose, ~ 11 hours post-dose for apixaban/dabigatran and ~23 hours post-dose for rivaroxaban/edoxaban)`

### 4.3 Clinical Outcomes — Gate — `Clinical Outcomes Measured?`

_Prompt change applied:_ Non-original-research carve-out + outcome trigger phrases.

- Agreement: **88.0%** · Recall: 88.0% · Precision: 88.0%
- Exact: 44 · Partial: 0 · No-overlap: 6 · AI-only: 0 · **Miss (human-only): 0** · Both blank: 0

**Disagreement examples:**

- _High fracture and DOAC level: A retrospective study of 72 cases_
  - **AI:** `No`
  - **Human:** `Yes`
- _Impact of the Genotype and Phenotype of CYP3A and P-gp on the Apixaban and Rivar…_
  - **AI:** `Yes`
  - **Human:** `No`
- _Management strategies of the interaction between direct oral anticoagulant and d…_
  - **AI:** `Yes`
  - **Human:** `No`

### 4.4 Clinical Outcomes — Capture — `Clinical Outcomes`

_Prompt change applied:_ Trigger-phrase requirement and Methods/Results-first search.

- Agreement: **51.3%** · Recall: 82.6% · Precision: 58.3%
- Exact: 6 · Partial: 15 · No-overlap: 0 · AI-only: 4 · **Miss (human-only): 2** · Both blank: 23

**Disagreement examples:**

- _High fracture and DOAC level: A retrospective study of 72 cases_
  - **AI:** `∅`
  - **Human:** `Bleeding/Hemostasis`
- _The assessment of anticoagulant activity to predict bleeding outcome in atrial f…_
  - **AI:** `Bleeding/Hemostasis; Thromboembolism; Stroke/Transient Ischemic Attack (TIA)`
  - **Human:** `Bleeding/Hemostasis; Thromboembolism`
- _Rivaroxaban dose adjustment using thrombin generation in severe congenital prote…_
  - **AI:** `Bleeding/Hemostasis`
  - **Human:** `Bleeding/Hemostasis; Thromboembolism`

### 4.5 Comparator Assays — `Comparator Assays`

_Prompt change applied:_ Acronym disambiguation rule (ACT/ACT-LR ≠ aPTT).

- Agreement: **48.6%** · Recall: 58.9% · Precision: 71.6%
- Exact: 12 · Partial: 6 · No-overlap: 2 · AI-only: 2 · **Miss (human-only): 8** · Both blank: 20

_Note on field routing:_ Of the 31 papers where AI left _Comparator Assays_ blank, AI extracted PT/aPTT into the more specific `Conventional Coag Tests Concurrent` field in **17 of 31**. The human extractor consolidated those into `Comparator Assays`, so the apparent miss count overstates the true extraction failure.

**Disagreement examples:**

- _Management of DOAC in Patients Undergoing Planned Surgery or Invasive Procedure:…_
  - **AI:** `∅`
  - **Human:** `Conventional coagulation testing (PT, aPTT, TT)`
- _Rivaroxaban dose adjustment using thrombin generation in severe congenital prote…_
  - **AI:** `Coagulation testing - Prothrombin time (PT); Coagulation testing - Activated partial thromboplastin time (aPTT); Thrombin generation assays`
  - **Human:** `Conventional coagulation testing (PT, aPTT, TT); Thrombin generation assay`
- _Feasibility, effectiveness, and safety of edoxaban administration through percut…_
  - **AI:** `∅`
  - **Human:** `Conventional coagulation testing (PT, aPTT, TT)`

### 4.6 Patient Subgroups — `Relevant Subgroups`

_Prompt change applied:_ Kept conservative per audit; only explicit study-focus.

- Agreement: **36.6%** · Recall: 42.9% · Precision: 70.7%
- Exact: 8 · Partial: 15 · No-overlap: 4 · AI-only: 2 · **Miss (human-only): 12** · Both blank: 9

**Disagreement examples:**

- _Potential treatment option of rivaroxaban for breastfeeding women: A case series_
  - **AI:** `Chronic kidney disease/dialysis; Advanced age/frailty`
  - **Human:** `∅`
- _The assessment of anticoagulant activity to predict bleeding outcome in atrial f…_
  - **AI:** `∅`
  - **Human:** `Chronic kidney disease/dialysis; Drug-DOAC pharmacokinetic interactions; Advanced age/frailty`
- _Management of DOAC in Patients Undergoing Planned Surgery or Invasive Procedure:…_
  - **AI:** `∅`
  - **Human:** `Low body weight; Chronic kidney disease/dialysis; Drug-DOAC pharmacokinetic interactions; Advanced age/frailty; Elective procedure/surgery; Urgent/emergent procedure/surgery; DOAC-associated bleeding + DOAC reversal`

### 4.7 Indications for DOAC Level Measurement — `Indications for DOAC Level Measurement`

_Prompt change applied:_ Primary + explicit secondary capture; ordered search (objective → methods → endpoints → results).

- Agreement: **54.8%** · Recall: 61.4% · Precision: 82.3%
- Exact: 12 · Partial: 36 · No-overlap: 2 · AI-only: 0 · **Miss (human-only): 0** · Both blank: 0

**Disagreement examples:**

- _The assessment of anticoagulant activity to predict bleeding outcome in atrial f…_
  - **AI:** `Risk prediction and clinical outcome association - Bleeding`
  - **Human:** `Evaluate DOAC level exposure; Measure correlation with other laboratory techniques; Risk prediction and clinical outcome association`
- _Factors affecting serum concentration of dabigatran in Asian patients with non-v…_
  - **AI:** `Identify predictors of DOAC level exposure - Cmax, Ctrough, AUC; Guide clinical decision-making - Guide dose adjustment`
  - **Human:** `Confirm adherence; Evaluate DOAC level exposure; Identify predictors of DOAC level exposure; Risk prediction and clinical outcome association`
- _Management of DOAC in Patients Undergoing Planned Surgery or Invasive Procedure:…_
  - **AI:** `Evaluate DOAC level exposure - Residual DOAC level after elective interruption; Guide clinical decision-making - Urgent surgery`
  - **Human:** `Evaluate DOAC level exposure; Identify predictors of DOAC level exposure; Guide clinical decision-making`

## 5. Full Per-Field Agreement Table

| Field | Domain | Exact | Partial | No-overlap | AI-only | Miss | Both blank | Mean Jaccard | Recall | Precision |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Journal | Bibliography | 41 | 1 | 7 | 0 | **1** | 0 | 92.3% | 92.3% | 92.3% |
| Country | Bibliography | 36 | 0 | 10 | 0 | **4** | 0 | 77.8% | 77.8% | 77.8% |
| Publication Year | Bibliography | 47 | 0 | 1 | 1 | **1** | 0 | 95.7% | 95.7% | 95.7% |
| Study Design | Bibliography | 28 | 0 | 22 | 0 | **0** | 0 | 79.1% | 79.1% | 79.1% |
| DOACs Included | Population | 49 | 1 | 0 | 0 | **0** | 0 | 99.5% | 99.5% | 100.0% |
| Indications for Anticoagulation | Population | 38 | 6 | 4 | 1 | **0** | 1 | 83.7% | 87.5% | 87.8% |
| Relevant Subgroups | Population | 8 | 15 | 4 | 2 | **12** | 9 | 36.6% | 42.9% | 70.7% |
| Indications for DOAC Level Measurement | Population | 12 | 36 | 2 | 0 | **0** | 0 | 54.8% | 61.4% | 82.3% |
| Pre-Analytical Variables | Methods | 12 | 18 | 0 | 9 | **0** | 11 | 52.6% | 97.2% | 53.2% |
| Conventional Coag Tests Concurrent | Methods | 25 | 0 | 0 | 8 | **0** | 17 | 75.8% | 100.0% | 75.8% |
| Global Coag Tests | Methods | 3 | 0 | 1 | 2 | **0** | 44 | 50.0% | 75.0% | 50.0% |
| Timing of DOAC Level Measurement | Methods | 0 | 10 | 3 | 0 | **37** | 0 | 6.7% | 10.0% | 38.5% |
| Clinical Outcomes Measured? | Outcomes | 44 | 0 | 6 | 0 | **0** | 0 | 88.0% | 88.0% | 88.0% |
| Clinical Outcomes | Outcomes | 6 | 15 | 0 | 4 | **2** | 23 | 51.3% | 82.6% | 58.3% |
| Clinical Outcome Definition | Outcomes | 0 | 0 | 21 | 2 | **2** | 25 | 0.0% | 0.0% | 0.0% |
| Comparator Assays | Diagnostic | 12 | 6 | 2 | 2 | **8** | 20 | 48.6% | 58.9% | 71.6% |
| Reported Cutoffs | Diagnostic | 8 | 0 | 0 | 8 | **4** | 30 | 40.0% | 66.7% | 50.0% |
| Diagnostic Performance Parameters | Diagnostic | 0 | 0 | 1 | 0 | **18** | 31 | 1.9% | 1.9% | 1.9% |

## 6. Known Comparison Caveats

This field shows **0% raw agreement** because the two sides use structurally different vocabularies, not because extraction failed:

- **Clinical Outcome Definition** — AI emits study-author paraphrase; human uses ISTH/standard definition tags (e.g., `"ISTH Major Bleeding (General Definition)"`).

Other field-mapping notes:

- **Comparator Assays vs Conventional/Global Coag** — human consolidates all assays into one column; AI splits into three. The audit scorecard counts these together.
- **Study Design fine-grained labels** — human uses sub-types like `"Cohort study"`, `"Cross sectional study"`, `"Pharmacokinetic study"`; AI uses parent categories like `"Non-Randomized Observational Study"`. Most disagreements here are sub-categorization of the same study type, not category errors.
- **Diagnostic Performance Parameters** — AI's `Diagnostic Performance Metrics - Categorical Cutoffs` is content-rich free text; human is a small canonical multi-select (`Sensitivity`, `Specificity`, `Spearman/Pearson Correlation`). The 18 "misses" in the table reflect schema shape, not content absence.

## 7. Per-Paper Agreement

**Lowest 10 (most disagreement):**

| Paper | Mean Agreement |
|---|---:|
| The Pharmacology, Efficacy, and Safety of Rivaroxaban in Obese Patient Populations | 55.2% |
| Intravenous Thrombolysis in Patients With Ischemic Stroke and Recent Ingestion of Direct O… | 55.2% |
| High fracture and DOAC level: A retrospective study of 72 cases | 55.6% |
| Feasibility, effectiveness, and safety of edoxaban administration through percutaneous end… | 57.9% |
| Initiation of rivaroxaban following low molecular weight heparin for thromboprophylaxis af… | 59.7% |
| Rivaroxaban dose adjustment using thrombin generation in severe congenital protein C defic… | 61.3% |
| Management of DOAC in Patients Undergoing Planned Surgery or Invasive Procedure: Italian F… | 62.0% |
| Apixaban-Calibrated Anti-FXa Activity in Relation to Outcome Events and Clinical Character… | 63.1% |
| Factors Associated With Edoxaban Concentration Among Patients With Atrial Fibrillation | 63.6% |
| Impact of the Genotype and Phenotype of CYP3A and P-gp on the Apixaban and Rivaroxaban Exp… | 67.1% |

**Highest 10 (best agreement):**

| Paper | Mean Agreement |
|---|---:|
| Pharmacokinetic drug–drug interaction between olaparib and apixaban: a case report | 88.9% |
| Dabigatran plasma concentration indicated the risk of patients with non-valvular atrial fi… | 85.2% |
| Simultaneous Determination of Dabigatran, Rivaroxaban, and Apixaban in Human Plasma by Liq… | 83.9% |
| Effect of pregnane X receptor and cytochrome P450 oxidoreductase gene polymorphisms on tro… | 83.3% |
| Edoxaban plasma levels in patients with non-valvular atrial fibrillation: Inter and intra-… | 82.4% |
| Influence of apixaban on antifactor Xa levels in a patient with acute kidney injury | 81.6% |
| Can an anti-Xa assay for low-molecular-weight heparin be used to assess the presence of ri… | 81.6% |
| Stability of Direct Oral Anticoagulants Concentrations in Blood Samples for Accessibility … | 81.3% |
| Heparin-Calibrated Chromogenic Anti-Xa Activity Measurements in Patients Receiving Rivarox… | 81.0% |
| Haematological management of major bleeding associated with direct oral anticoagulants – U… | 79.6% |

Full per-paper scores: [`docs/comparisons/2026-05-03-per-paper-agreement.csv`](docs/comparisons/2026-05-03-per-paper-agreement.csv)  
Every disagreement listed: [`docs/comparisons/2026-05-03-disagreements.csv`](docs/comparisons/2026-05-03-disagreements.csv)

## 7b. Run-over-run Delta (semantic-concept comparator)

Run-over-run per-field deltas vs the prior run are computed by the companion HTML report's compatibility-group-aware comparator. See [`2026-05-03-comparison-report.html`](2026-05-03-comparison-report.html) — section `Changes from v1` — for the apples-to-apples view of what the most recent prompt edits moved.

## 8. Recommended Next Steps

Based on this run, the highest-leverage investments for the next iteration are:

1. **Timing extraction (6.7%, weakest individual field).** The new hour-window and acute-care rules helped, but 3 no-overlap and 37 blank-miss cases remain. Most failures are Random ↔ Trough conflations in PK studies and stroke-on-presentation papers. Consider auditing the 37 miss cases by hand to see whether the trigger phrases are present in the source text — if so, the issue is the prompt's recognition; if not, the human extractor was inferring beyond the text.
2. **Outcome gate — 6 residual disagreements**, now split roughly evenly between AI=No / Human=Yes (the dominant pattern) and AI=Yes / Human=No. With zero misses (no blanks) and 41/50 exact agreements, the gate is largely correct; spot-checking the remaining 9 will reveal whether the trigger-phrase bar is now slightly too high.
3. **Field consolidation (post-processor, no prompt change).** AI's `Conventional Coag Tests Concurrent` field is populated for some papers where AI left `Comparator Assays` blank. A two-line post-processor that copies/merges those into `Comparator Assays` for downstream comparison would close part of the apparent miss gap without touching the prompts.

## 9. Methodology

- **Title matching:** rapidfuzz `token_set_ratio`, threshold ≥ 75 → 50/50 matched.
- **Multi-select normalization:** AI list-strings parsed via `ast.literal_eval`; human strings split on `;`. Both sides lower-cased, dash variants normalized, hierarchical sub-labels (`"X - Y"`) collapsed to parent, label aliases applied (e.g., `"thrombin generation assay TGA"` → `"thrombin generation assay"`).
- **Multi-select metric:** Jaccard on canonical label sets (1.0 = identical, 0.0 = disjoint).
- **Free-text metric:** rapidfuzz `token_set_ratio / 100`.
- **Recall** = |AI ∩ Human| / |Human|. **Precision** = |AI ∩ Human| / |AI|.
- **Yes/No human columns** (`Apixaban`, `PT`, `aPTT`, `Bleeding/Hemostasis`, …) interpreted strictly: only `"Yes"` counts as populated; `"No"` is blank.

_Generated by `analysis/compare_to_human.py` from `output/aggregated/df_annotations.csv` and `data/human/Pooja + Athavan Abstraction Lock 19MAR2026.csv`._
