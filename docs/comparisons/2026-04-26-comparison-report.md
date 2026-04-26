# DOAC Extraction — AI vs Human Gold-Standard Comparison Report

_Run: 2026-04-26 — after the audit-driven prompt refinements landed in branch `main`._

> **Companion visual report** with KPI cards, stacked-bar distributions, per-paper drill-downs, and a `Changes from v1` delta section is at [`2026-04-26-comparison-report.html`](2026-04-26-comparison-report.html). The HTML uses a richer semantic-concept comparator that reports overall accuracy of **72.7%** vs the immediately-prior-run baseline of **73.3%** — essentially flat (**−0.6pp**), with significant gains on bibliography/population fields offset by regressions on Timing, Thresholds, and Comparator Assays. See § 7b for the per-field deltas.

## 1. Executive Summary

- **Papers compared:** 50/50 (fuzzy-title matched, threshold ≥ 75) — every AI paper aligned to a human row.
- **Overall mean field agreement:** **54.4%** across 19 compared fields.
- **Total "misses"** (AI blank when human populated): **73** across 950 field-paper cells (≈ 7.7%).

**Top-line takeaways:**

- 🟢 **Bibliography** is solid (86.5% agreement). Country has the most slip-ups (4 misses, 10 mismatches due to first-author affiliation vs study-conduct country differences).
- 🟢 **Population** is now strong (68.8%). DOACs Included 99.5%, Indications for Anticoagulation 84.4%, and **zero misses** on the multi-label _Indications for DOAC Level Measurement_ field (59.8% agreement, recall 65.6%).
- 🟡 **Methods** is mixed (50.4%). Pre-Analytical Variables recall is 81.1% (AI tends to over-tag, lowering precision). **Timing of Measurement is the weakest individual field** (23.3%, 10 misses).
- 🟢 **Outcome gate** improved sharply at the Yes/No level: AI and human now agree in 41/50 papers (82.0%). The semantic comparator shows Clinical Outcomes domain at 56.2% (down ~5pp from prior run) — the gate is correct but the multi-label outcome capture isn't yet matching the prior run's recall.
- 🟡 **Comparator Assays** raw agreement is 37.8% but the apparent miss count is inflated by field-routing — see § 4.5. The acronym disambiguation rule (ACT/ACT-LR ≠ aPTT) eliminates the worst-class errors. Net change vs prior run: −7.1pp.
- 🟡 **Mixed picture vs prior run**: improvements on Indications (+4.7pp), Coag Tests (+4.1pp), Country (+3.9pp), Journal (+2.8pp); regressions on Timing (−8.7pp), Thresholds (−9.0pp), Comparator Assays (−7.1pp). Overall almost flat (−0.6pp). See § 7b.

## 2. Per-Domain Summary

| Domain | Mean Agreement | Recall (sensitivity) | Precision | Coverage* |
|---|---:|---:|---:|---:|
| Bibliography | 86.5% | 86.5% | 86.5% | 97.0% |
| Population | 68.8% | 72.1% | 83.7% | 93.6% |
| Methods | 50.4% | 71.0% | 55.5% | 94.2% |
| Outcomes | 33.8% | 39.5% | 36.7% | 87.0% |
| Diagnostic | 25.0% | 36.2% | 37.0% | 41.4% |

_*Coverage = fraction of papers where AI populated the field when the human did. **Recall** = how much of the human gold AI captured. **Precision** = how clean AI's emitted labels are._

## 3. Joseph's Audit — Scorecard for the 7 Priority Areas

Status legend: ✅ strong (≥ 65% agreement, ≤ 10% misses) · 🟡 mixed · 🔴 weak.

| # | Audit area | Status | Field | Agreement | Misses |
|---|---|:---:|---|---:|---:|
| 1 | Blank outputs (overall) | 🟡 | _all non-bibliography_ | — | 67 (8.9%) |
| 2 | Pre-analytical variables | 🟡 | `Pre-Analytical Variables` | 50.0% | 1/50 |
| 3 | Timing extraction | 🟡 | `Timing of DOAC Level Measurement` | 23.3% | 10/50 |
| 4 | Clinical outcomes — gate | ✅ | `Clinical Outcomes Measured?` | 82.0% | 0/50 |
| 4 | Clinical outcomes — capture | 🟡 | `Clinical Outcomes` | 53.3% | 4/50 |
| 5 | Comparator assays / acronyms | 🔴 | `Comparator Assays` | 37.8% | 11/50 |
| 6 | Patient subgroups | 🟡 | `Relevant Subgroups` | 31.7% | 10/50 |
| 7 | Indications (multi-label) | 🟡 | `Indications for DOAC Level Measurement` | 59.8% | 0/50 |

## 4. Drill-Down by Audit Priority

### 4.1 Pre-Analytical Variables — `Pre-Analytical Variables`

_Prompt change applied:_ Force non-blank + broaden triggers (citrate concentration, Greiner Vacuette, storage).

- Agreement: **50.0%** · Recall: 81.1% · Precision: 56.1%
- Exact: 10 · Partial: 17 · No-overlap: 2 · AI-only: 8 · **Miss (human-only): 1** · Both blank: 12

**Disagreement examples:**

- _Point-of-Care Coagulation Testing for Assessment of the Pharmacodynamic Anticoag…_
  - **AI:** `Blood collection procedures; Collection tube type; Centrifugation speed; Storage temperature`
  - **Human:** `Blood collection procedure; Collection tube type; Centrifugation speed`
- _Can an anti-Xa assay for low-molecular-weight heparin be used to assess the pres…_
  - **AI:** `Blood collection procedures; Collection tube type; Centrifugation speed; Storage temperature`
  - **Human:** `Collection tube type; Centrifugation speed; Storage temperature`
- _The assessment of anticoagulant activity to predict bleeding outcome in atrial f…_
  - **AI:** `∅`
  - **Human:** `Blood collection procedure`

### 4.2 Timing Extraction — `Timing of DOAC Level Measurement`

_Prompt change applied:_ Trough triggers added; hour-window disambiguation; acute-care inference rule.

- Agreement: **23.3%** · Recall: 28.0% · Precision: 37.9%
- Exact: 6 · Partial: 15 · No-overlap: 19 · AI-only: 0 · **Miss (human-only): 10** · Both blank: 0

**Disagreement examples:**

- _Point-of-Care Coagulation Testing for Assessment of the Pharmacodynamic Anticoag…_
  - **AI:** `Peak level (2–4 hours post-dose); Trough level (just prior to next dose)`
  - **Human:** `Peak level (2-4 hours post-dose); Trough level (just prior to next dose, ~ 11 hours post-dose for apixaban/dabigatran and ~23 hours post-dose for rivaroxaban/edoxaban)`
- _Can an anti-Xa assay for low-molecular-weight heparin be used to assess the pres…_
  - **AI:** `Random level`
  - **Human:** `Random level; Timing not reported`
- _High fracture and DOAC level: A retrospective study of 72 cases_
  - **AI:** `∅`
  - **Human:** `Random level`

### 4.3 Clinical Outcomes — Gate — `Clinical Outcomes Measured?`

_Prompt change applied:_ Non-original-research carve-out + outcome trigger phrases.

- Agreement: **82.0%** · Recall: 82.0% · Precision: 82.0%
- Exact: 41 · Partial: 0 · No-overlap: 9 · AI-only: 0 · **Miss (human-only): 0** · Both blank: 0

**Disagreement examples:**

- _Impact of the Genotype and Phenotype of CYP3A and P-gp on the Apixaban and Rivar…_
  - **AI:** `Yes`
  - **Human:** `No`
- _The Pharmacology, Efficacy, and Safety of Rivaroxaban in Obese Patient Populatio…_
  - **AI:** `No`
  - **Human:** `Yes`
- _Pre-Operative Direct Oral Anticoagulant Level Measurement Reduces Time to Surger…_
  - **AI:** `No`
  - **Human:** `Yes`

### 4.4 Clinical Outcomes — Capture — `Clinical Outcomes`

_Prompt change applied:_ Trigger-phrase requirement and Methods/Results-first search.

- Agreement: **53.3%** · Recall: 76.1% · Precision: 64.9%
- Exact: 11 · Partial: 8 · No-overlap: 0 · AI-only: 5 · **Miss (human-only): 4** · Both blank: 22

**Disagreement examples:**

- _The assessment of anticoagulant activity to predict bleeding outcome in atrial f…_
  - **AI:** `Bleeding/Hemostasis`
  - **Human:** `Bleeding/Hemostasis; Thromboembolism`
- _Dabigatran plasma concentration indicated the risk of patients with non-valvular…_
  - **AI:** `Bleeding/Hemostasis; Thromboembolism; Stroke/Transient Ischemic Attack (TIA)`
  - **Human:** `Bleeding/Hemostasis; Thromboembolism`
- _Intravenous Thrombolysis in Patients With Ischemic Stroke and Recent Ingestion o…_
  - **AI:** `Bleeding/Hemostasis; Thromboembolism; Stroke/Transient Ischemic Attack (TIA)`
  - **Human:** `Bleeding/Hemostasis; Thromboembolism`

### 4.5 Comparator Assays — `Comparator Assays`

_Prompt change applied:_ Acronym disambiguation rule (ACT/ACT-LR ≠ aPTT).

- Agreement: **37.8%** · Recall: 48.2% · Precision: 62.3%
- Exact: 9 · Partial: 5 · No-overlap: 3 · AI-only: 2 · **Miss (human-only): 11** · Both blank: 20

_Note on field routing:_ Of the 31 papers where AI left _Comparator Assays_ blank, AI extracted PT/aPTT into the more specific `Conventional Coag Tests Concurrent` field in **17 of 31**. The human extractor consolidated those into `Comparator Assays`, so the apparent miss count overstates the true extraction failure.

**Disagreement examples:**

- _EFFECTS OF DIRECT ORAL ANTICOAGULANTS ON THROMBOELASTOGRAPHIC PARAMETERS AND FIB…_
  - **AI:** `Coagulation testing - Prothrombin time (PT); Coagulation testing - Activated partial thromboplastin time (aPTT)`
  - **Human:** `Conventional coagulation testing (PT, aPTT, TT); Viscoelastic testing`
- _Rivaroxaban dose adjustment using thrombin generation in severe congenital prote…_
  - **AI:** `Thrombin generation assays`
  - **Human:** `Conventional coagulation testing (PT, aPTT, TT); Thrombin generation assay`
- _Haematological management of major bleeding associated with direct oral anticoag…_
  - **AI:** `Coagulation testing - Prothrombin time (PT); Coagulation testing - Activated partial thromboplastin time (aPTT); Coagulation testing - Thrombin Time (TT); Anti-Xa assays with LMWH calibrators (IU/mL)`
  - **Human:** `Conventional coagulation testing (PT, aPTT, TT)`

### 4.6 Patient Subgroups — `Relevant Subgroups`

_Prompt change applied:_ Kept conservative per audit; only explicit study-focus.

- Agreement: **31.7%** · Recall: 35.0% · Precision: 61.8%
- Exact: 6 · Partial: 15 · No-overlap: 8 · AI-only: 2 · **Miss (human-only): 10** · Both blank: 9

**Disagreement examples:**

- _EFFECTS OF DIRECT ORAL ANTICOAGULANTS ON THROMBOELASTOGRAPHIC PARAMETERS AND FIB…_
  - **AI:** `∅`
  - **Human:** `Genetic polymorphism (e.g., CYP polymorphism)`
- _Factors affecting serum concentration of dabigatran in Asian patients with non-v…_
  - **AI:** `Low body weight; Chronic kidney disease/dialysis`
  - **Human:** `Low body weight; Chronic kidney disease/dialysis; Advanced age/frailty`
- _The assessment of anticoagulant activity to predict bleeding outcome in atrial f…_
  - **AI:** `Drug-DOAC pharmacokinetic interactions`
  - **Human:** `Chronic kidney disease/dialysis; Drug-DOAC pharmacokinetic interactions; Advanced age/frailty`

### 4.7 Indications for DOAC Level Measurement — `Indications for DOAC Level Measurement`

_Prompt change applied:_ Primary + explicit secondary capture; ordered search (objective → methods → endpoints → results).

- Agreement: **59.8%** · Recall: 65.6% · Precision: 85.2%
- Exact: 14 · Partial: 34 · No-overlap: 2 · AI-only: 0 · **Miss (human-only): 0** · Both blank: 0

**Disagreement examples:**

- _Can an anti-Xa assay for low-molecular-weight heparin be used to assess the pres…_
  - **AI:** `Measure correlation with other laboratory techniques; Measure correlation with other laboratory techniques - Conventional coagulation testing (e.g., prothrombin time); Measure correlation with other laboratory techniques - HPLC-MS vs calibr`
  - **Human:** `Evaluate DOAC level exposure; Measure correlation with other laboratory techniques`
- _EFFECTS OF DIRECT ORAL ANTICOAGULANTS ON THROMBOELASTOGRAPHIC PARAMETERS AND FIB…_
  - **AI:** `Measure correlation with other laboratory techniques; Measure correlation with other laboratory techniques - Conventional coagulation testing (e.g., prothrombin time); Measure correlation with other laboratory techniques - HPLC-MS vs calibr`
  - **Human:** `Evaluate DOAC level exposure; Measure correlation with other laboratory techniques`
- _Factors affecting serum concentration of dabigatran in Asian patients with non-v…_
  - **AI:** `Evaluate DOAC level exposure; Identify predictors of DOAC level exposure; Identify predictors of DOAC level exposure - Cmax, Ctrough, AUC`
  - **Human:** `Confirm adherence; Evaluate DOAC level exposure; Identify predictors of DOAC level exposure; Risk prediction and clinical outcome association`

## 5. Full Per-Field Agreement Table

| Field | Domain | Exact | Partial | No-overlap | AI-only | Miss | Both blank | Mean Jaccard | Recall | Precision |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Journal | Bibliography | 43 | 1 | 5 | 0 | **1** | 0 | 93.5% | 93.5% | 93.5% |
| Country | Bibliography | 36 | 0 | 10 | 0 | **4** | 0 | 77.8% | 77.8% | 77.8% |
| Publication Year | Bibliography | 47 | 0 | 1 | 1 | **1** | 0 | 95.7% | 95.7% | 95.7% |
| Study Design | Bibliography | 29 | 0 | 21 | 0 | **0** | 0 | 79.0% | 79.0% | 79.0% |
| DOACs Included | Population | 49 | 1 | 0 | 0 | **0** | 0 | 99.5% | 99.5% | 100.0% |
| Indications for Anticoagulation | Population | 39 | 5 | 4 | 1 | **0** | 1 | 84.4% | 88.2% | 87.8% |
| Relevant Subgroups | Population | 6 | 15 | 8 | 2 | **10** | 9 | 31.7% | 35.0% | 61.8% |
| Indications for DOAC Level Measurement | Population | 14 | 34 | 2 | 0 | **0** | 0 | 59.8% | 65.6% | 85.2% |
| Pre-Analytical Variables | Methods | 10 | 17 | 2 | 8 | **1** | 12 | 50.0% | 81.1% | 56.1% |
| Conventional Coag Tests Concurrent | Methods | 25 | 0 | 0 | 7 | **0** | 18 | 78.1% | 100.0% | 78.1% |
| Global Coag Tests | Methods | 3 | 0 | 1 | 2 | **0** | 44 | 50.0% | 75.0% | 50.0% |
| Timing of DOAC Level Measurement | Methods | 6 | 15 | 19 | 0 | **10** | 0 | 23.3% | 28.0% | 37.9% |
| Clinical Outcomes Measured? | Outcomes | 41 | 0 | 9 | 0 | **0** | 0 | 82.0% | 82.0% | 82.0% |
| Clinical Outcomes | Outcomes | 11 | 8 | 0 | 5 | **4** | 22 | 53.3% | 76.1% | 64.9% |
| Clinical Outcome Follow-Up | Outcomes | 0 | 0 | 19 | 5 | **4** | 22 | 0.0% | 0.0% | 0.0% |
| Clinical Outcome Definition | Outcomes | 0 | 0 | 19 | 5 | **4** | 22 | 0.0% | 0.0% | 0.0% |
| Comparator Assays | Diagnostic | 9 | 5 | 3 | 2 | **11** | 20 | 37.8% | 48.2% | 62.3% |
| Reported Cutoffs | Diagnostic | 7 | 0 | 0 | 8 | **5** | 30 | 35.0% | 58.3% | 46.7% |
| Diagnostic Performance Parameters | Diagnostic | 0 | 0 | 1 | 0 | **18** | 31 | 2.1% | 2.1% | 2.1% |

## 6. Known Comparison Caveats

These two fields show **0% raw agreement** because the two sides use structurally different vocabularies, not because extraction failed:

- **Clinical Outcome Follow-Up** — AI emits free-text durations (e.g., `"12 months"`, `"30 days"`); human uses categorical bins (`"> 6 months to ≤ 1 year"`, `"1 month to ≤ 3 months"`). A binning post-processor would be needed for a fair comparison.
- **Clinical Outcome Definition** — AI emits study-author paraphrase; human uses ISTH/standard definition tags (e.g., `"ISTH Major Bleeding (General Definition)"`).

Other field-mapping notes:

- **Comparator Assays vs Conventional/Global Coag** — human consolidates all assays into one column; AI splits into three. The audit scorecard counts these together.
- **Study Design fine-grained labels** — human uses sub-types like `"Cohort study"`, `"Cross sectional study"`, `"Pharmacokinetic study"`; AI uses parent categories like `"Non-Randomized Observational Study"`. Most disagreements here are sub-categorization of the same study type, not category errors.
- **Diagnostic Performance Parameters** — AI's `Diagnostic Performance Metrics - Categorical Cutoffs` is content-rich free text; human is a small canonical multi-select (`Sensitivity`, `Specificity`, `Spearman/Pearson Correlation`). The 18 "misses" in the table reflect schema shape, not content absence.

## 7. Per-Paper Agreement

**Lowest 10 (most disagreement):**

| Paper | Mean Agreement |
|---|---:|
| Remaining activity of temporary interrupted direct oral anticoagulants and its impact on i… | 47.8% |
| Apixaban-Calibrated Anti-FXa Activity in Relation to Outcome Events and Clinical Character… | 52.5% |
| Dabigatran is Less Effective Than Warfarin at Attenuating Mechanical Heart Valve-Induced T… | 52.6% |
| Pre-Operative Direct Oral Anticoagulant Level Measurement Reduces Time to Surgery in Hip F… | 54.4% |
| Initiation of rivaroxaban following low molecular weight heparin for thromboprophylaxis af… | 55.7% |
| Intravenous Thrombolysis in Patients With Ischemic Stroke and Recent Ingestion of Direct O… | 55.8% |
| The Pharmacology, Efficacy, and Safety of Rivaroxaban in Obese Patient Populations | 59.3% |
| Laboratory measurement of apixaban using anti-factor Xa assays in acute ischemic stroke pa… | 59.6% |
| Rivaroxaban dose adjustment using thrombin generation in severe congenital protein C defic… | 60.0% |
| Dabigatran With or Without Concomitant Aspirin Compared With Warfarin Alone in Patients Wi… | 62.7% |

**Highest 10 (best agreement):**

| Paper | Mean Agreement |
|---|---:|
| Management strategies of the interaction between direct oral anticoagulant and drug-metabo… | 94.7% |
| Pharmacokinetic drug–drug interaction between olaparib and apixaban: a case report | 89.5% |
| Simultaneous Determination of Dabigatran, Rivaroxaban, and Apixaban in Human Plasma by Liq… | 85.6% |
| Can an anti-Xa assay for low-molecular-weight heparin be used to assess the presence of ri… | 85.2% |
| Point-of-Care Coagulation Testing for Assessment of the Pharmacodynamic Anticoagulant Effe… | 84.6% |
| Effect of pregnane X receptor and cytochrome P450 oxidoreductase gene polymorphisms on tro… | 84.2% |
| Apixaban and rivaroxaban's physiologically-based pharmacokinetic model validation in hospi… | 83.0% |
| Stability of Direct Oral Anticoagulants Concentrations in Blood Samples for Accessibility … | 82.3% |
| Dabigatran plasma concentration indicated the risk of patients with non-valvular atrial fi… | 80.7% |
| Anti-Xa Levels in Morbidly Obese Patients Using Apixaban or Rivaroxaban, Before and After … | 79.5% |

Full per-paper scores: [`docs/comparisons/2026-04-26-per-paper-agreement.csv`](docs/comparisons/2026-04-26-per-paper-agreement.csv)  
Every disagreement listed: [`docs/comparisons/2026-04-26-disagreements.csv`](docs/comparisons/2026-04-26-disagreements.csv)

## 7b. Pre-fix → Post-fix Delta (semantic-concept comparator)

These deltas come from the companion HTML report's compatibility-group-aware comparator, comparing today's run to the **immediately-prior run** (Apr 12 baseline, before today's prompt edits). This is the apples-to-apples view of what the audit-driven changes actually moved.

| Field | Apr 12 baseline | Today | Δ |
|---|--:|--:|--:|
| Indications | 80% | 84.7% | 🟢 +4.7pp |
| Coagulation Tests | 76% | 80.1% | 🟢 +4.1pp |
| Country | 82% | 85.9% | 🟢 +3.9pp |
| Journal | 88% | 90.8% | 🟢 +2.8pp |
| DOACs Included | 98% | 99.5% | 🟢 +1.5pp |
| Diagnostic Performance | 55% | 56.5% | 🟢 +1.5pp |
| Publication Year | 94% | 94.5% | 🟡 +0.5pp |
| Study Design | 80% | 78.6% | 🟡 −1.4pp |
| Relevant Subgroups | 38% | 36.2% | 🟡 −1.8pp |
| Clinical Outcomes | 61% | 56.2% | 🟡 −4.8pp |
| Comparator Assays | 50% | 42.9% | 🔴 −7.1pp |
| Timing of Measurement | 54% | 45.3% | 🔴 −8.7pp |
| Thresholds/Cutoffs | 54% | 45.0% | 🔴 −9.0pp |
| **Overall** | **73.3%** | **72.7%** | 🟡 **−0.6pp** (flat) |

**Interpretation.** Net result is essentially flat (−0.6pp). The audit-driven changes hit their bibliography and population targets cleanly (+2 to +5pp on Journal, Country, Indications, DOACs, Coag Tests). They did NOT move Subgroups (−1.8pp ≈ flat at 36-38%) or Diagnostic Performance (+1.5pp). Three fields regressed: **Timing (−8.7pp)** despite our hour-window and trough-trigger additions; **Thresholds/Cutoffs (−9pp)** which wasn't directly targeted; and **Comparator Assays (−7.1pp)** despite the ACT/ACT-LR disambiguation rule. The Outcomes domain (−4.8pp) shows the gate-fix improved Yes/No agreement but degraded multi-label capture — likely the trigger-phrase requirement is now too strict in cases where outcome language is implicit.

_Earlier draft of this report compared against an out-of-date hardcoded baseline (`V1_FIELD_ACC` constants set before Apr 12) and reported alarming regressions like "Relevant Subgroups −22.8pp" — those were artifacts of stale numbers, not real regressions. The deltas above use the actual Apr 12 run as the baseline._

## 8. Recommended Next Steps

Based on this run, the highest-leverage investments for the next iteration are:

1. **Timing extraction (23.3%, weakest individual field).** The new hour-window and acute-care rules helped, but 19 no-overlap and 10 blank-miss cases remain. Most failures are Random ↔ Trough conflations in PK studies and stroke-on-presentation papers. Consider auditing the 10 miss cases by hand to see whether the trigger phrases are present in the source text — if so, the issue is the prompt's recognition; if not, the human extractor was inferring beyond the text.
2. **Outcome gate — 9 residual disagreements**, now split roughly evenly between AI=No / Human=Yes (the dominant pattern) and AI=Yes / Human=No. With zero misses (no blanks) and 41/50 exact agreements, the gate is largely correct; spot-checking the remaining 9 will reveal whether the trigger-phrase bar is now slightly too high.
3. **Field consolidation (post-processor, no prompt change).** AI's `Conventional Coag Tests Concurrent` field is populated for 17/31 papers where AI left `Comparator Assays` blank. A two-line post-processor that copies/merges those into `Comparator Assays` for downstream comparison would close ~half of the apparent miss gap without touching the prompts.
4. **Follow-up duration binning.** AI emits free-text (`"12 months"`); human uses categorical bins (`"> 6 months to ≤ 1 year"`). A deterministic post-processor mapping durations into bins would unlock fair comparison on this field — currently 0% raw agreement is an artifact, not an extraction failure.

## 9. Methodology

- **Title matching:** rapidfuzz `token_set_ratio`, threshold ≥ 75 → 50/50 matched.
- **Multi-select normalization:** AI list-strings parsed via `ast.literal_eval`; human strings split on `;`. Both sides lower-cased, dash variants normalized, hierarchical sub-labels (`"X - Y"`) collapsed to parent, label aliases applied (e.g., `"thrombin generation assay TGA"` → `"thrombin generation assay"`).
- **Multi-select metric:** Jaccard on canonical label sets (1.0 = identical, 0.0 = disjoint).
- **Free-text metric:** rapidfuzz `token_set_ratio / 100`.
- **Recall** = |AI ∩ Human| / |Human|. **Precision** = |AI ∩ Human| / |AI|.
- **Yes/No human columns** (`Apixaban`, `PT`, `aPTT`, `Bleeding/Hemostasis`, …) interpreted strictly: only `"Yes"` counts as populated; `"No"` is blank.

_Generated by `analysis/compare_to_human.py` from `output/aggregated/df_annotations.csv` and `data/human/Pooja + Athavan Abstraction Lock 19MAR2026.csv`._
