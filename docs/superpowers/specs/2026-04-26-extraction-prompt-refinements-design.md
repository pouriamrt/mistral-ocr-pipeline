# Extraction Prompt Refinements — Design

**Date:** 2026-04-26
**Author:** Pouria Mortezaagha
**Source feedback:** Joseph Shaw — `data/todo/Comparison Report.pdf` and `data/todo/Scoping Review Discussion.vtt` (meeting 2026-04-22), plus follow-up email on remaining human-vs-AI disagreements.

## Goal

Reduce factual extraction errors in the five domains where Joseph's audit found the largest human-vs-AI disagreements: timing of DOAC level measurement, clinical outcomes, comparator coagulation assays, pre-analytical variables, and indications for DOAC level measurement. All changes are surgical edits to existing Pydantic field `description=` strings — no schema changes, no new fields, no architectural changes.

## Scope

### In scope (5 prompt-only edits, zero schema changes)

| # | Field | File | Lines (approx) |
|---|-------|------|----------------|
| 1 | `timing_of_measurement` | `info_extraction/schemas/outcomes.py` | 28-172 |
| 2 | `clinical_outcomes_measured` + `clinical_outcomes` + `clinical_outcome_followup_flat` | `info_extraction/schemas/outcomes.py` | 400-712 |
| 3 | `coagulation_tests_concurrent` (aPTT acronym fix) | `info_extraction/schemas/methods.py` | 386-521 |
| 4 | `pre_analytical_variables` | `info_extraction/schemas/methods.py` | 291-373 |
| 5 | `indications_for_doac_level_measurement` | `info_extraction/schemas/population.py` | 168-311 |

### Out of scope (deliberately, per stakeholder decisions)

- **No "force 'Not reported'" enforcement** — null when the model genuinely doesn't find evidence remains acceptable. This deviates from Joseph's PDF report point #1; rationale is that empty cells reflect honest uncertainty and forced sentinels could mask real misses.
- **No new "Publication Type" field** — handle position/guidance/narrative/scoping papers via stronger anti-overcall language inside the existing outcome prompts only.
- **No new validator module / post-processing safety net** — keep the existing `post_processing/post_processing.py` LLM validator unchanged; do not add a separate sanity-check pass.
- **No drop of `clinical_outcome_followup_flat`** — keep the field, tighten the rules. (Joseph's verbal call to drop it is overridden in favor of his written report's tighter-rule guidance.)
- **No literal/enum changes** — only `description=` strings are edited. CSV/Parquet column structure stays identical, no migration needed for existing outputs.

### Verification only (no code change)

The following two patient-subgroup options Joseph asked us to verify are already in the schema:

- `"Elective procedure/surgery"` — `population.py:82`
- `"DOAC-associated bleeding + DOAC Reversal"` — `population.py:85`

Confirm to Joseph that any disagreement on these subgroups is genuine AI behavior, not a structural gap.

## Design

### 1. Timing extraction (`timing_of_measurement`)

The current prompt already has the lexicon (peak / trough / random / serial / residual / "Timing not reported") and section routing (Methods → PK sections → figure/table captions → Results → abstract → ignore Intro/Discussion). Edits are **additive** — no removals.

**1.1** In the `MAP TO 'Trough level (just prior to next dose)'` lexicon block, only one trigger is missing: add `immediately prior to next dose` to the existing top-of-block bullets. The other primary triggers (`predose`, `pre-dose`, `before next dose`, `just prior to next dose`, `before administration`) are already present at the top of the block.

**1.2** In the `MAP TO 'Peak level (2-4 hours post-dose)'` block: broaden the hour-window list. Add: `"1-4 hours post-dose"`, `"3-4 hours post-dose"`, `"narrow post-dose window of <6 hours after administration"`.

**1.3** Add a new `HOUR-WINDOW DISAMBIGUATION (CRITICAL)` sub-block immediately before the `CLASSIFICATION RULES` section:

```
HOUR-WINDOW DISAMBIGUATION (CRITICAL):
- Narrow post-dose windows ≤ 6 hours (e.g., "1-4 h", "3-4 h post-dose") → Peak
- Broad heterogeneous windows spanning peak and trough (e.g., "2-27 hours after intake",
  "median 5 h, range 1-24 h since last dose") → Random
- Multi-timepoint dense schedules (e.g., 0, 0.5, 1, 2, 3, 4, 6, 8 h) → Serial PK/PD profile
```

**1.4** Add a new `ACUTE-CARE INFERENCE RULE` sub-block after the hour-window block:

```
ACUTE-CARE INFERENCE RULE:
If samples are drawn at presentation in stroke, hip fracture, trauma, or urgent admission,
AND timing is anchored to "hours since last dose" (no fixed peak/trough sampling protocol),
classify as Random — UNLESS the paper explicitly states the sample was timed to peak or trough.
This applies to studies where time-since-last-dose is reported as a baseline characteristic
(e.g., "median time since last dose 5 h, range 2-27 h") rather than a controlled sampling design.
```

### 2. Clinical outcomes cascade

#### 2.1 `clinical_outcomes_measured` (gate)

Strengthen anti-overcall for non-original-research papers without changing the `Yes`/`No` literal. Add a new sub-block under `SET TO 'NO' IF`:

```
NON-ORIGINAL-RESEARCH PAPERS:
If the paper is a position paper, clinical guidance document, narrative review, or scoping review
(no original Methods/Results section, no patient cohort followed for events in THIS paper),
set to 'No' even if bleeding/thromboembolism is mentioned in recommendations or summary text.
Indicators: "we recommend", "guidance for", "consensus statement", "narrative review",
absence of a "Methods" section describing patient enrollment and event ascertainment.
```

#### 2.2 `clinical_outcomes` (multi-label list)

Reinforce the "Methods + Results, not Introduction/Discussion" constraint. Add a `TRIGGER PHRASES (REQUIRED)` sub-block:

```
TRIGGER PHRASES — At least one must be present in Methods or Results for an outcome to qualify:
- "primary endpoint", "secondary endpoint", "primary outcome", "secondary outcome"
- "all bleeding [and/or] thromboembolic complications were recorded"
- "during follow-up", "during the study period"
- "there was a total of X events", "X events occurred", "no events occurred"
- "adjudicated by", "ascertained by", "events were captured"

If NONE of these trigger phrases appear in Methods or Results for a given outcome category,
do NOT include that category — even if the keyword (stroke, bleeding, etc.) appears in
Introduction or Discussion.
```

#### 2.3 `clinical_outcome_followup_flat` (per-outcome duration)

Tighten without changing the 15-literal enum.

Add a `REQUIRED LINKAGE RULE` near the top of the description:

```
REQUIRED LINKAGE RULE:
Include a duration ONLY if the same sentence (or one immediately adjacent) explicitly links
the duration to outcome ascertainment. Phrases that satisfy this:
- "patients were followed for [X] for [outcome]"
- "[outcome] events were recorded over [X]"
- "median follow-up [X], during which [outcome] was assessed"
General study-duration phrases ("study ran from 2018 to 2020") DO NOT qualify.
```

Add an explicit exclusion in the existing `DO NOT INCLUDE follow-up duration if` block:

```
- Do not infer duration from enrollment dates, hospital stay length, or PK sampling windows.
```

### 3. Comparator assays — aPTT vs ACT acronym fix (`coagulation_tests_concurrent`)

The existing prompt has good aPTT rules but is missing a hard ACT/ACT-LR exclusion that Joseph flagged as a clear factual error.

**3.1** Add a new sub-block immediately after the existing `3.4. Negative/Ambiguous Cases for aPTT` section:

```
3.5. CRITICAL ACRONYM DISAMBIGUATION — ACT vs aPTT
"ACT" (activated clotting time) and "ACT-LR" (low-range activated clotting time) are
DIFFERENT TESTS from aPTT. They share the word "activated" but measure different things
on different instruments (point-of-care whole-blood vs plasma-based clotting).

HARD RULE: If the paper reports "ACT", "activated clotting time", "ACT-LR", or
"activated clotting time low range" and does NOT independently report aPTT/APTT/PTT
or "partial thromboplastin time", then aPTT MUST NOT be flagged.

The word "activated" alone is NEVER sufficient evidence for aPTT.
aPTT requires the phrase "partial thromboplastin" OR an aPTT-specific reagent name
(see section 3.2 above).

EXAMPLES:
✗ INCORRECT: Paper says "activated clotting time was measured" → flag aPTT
✓ CORRECT:   Paper says "activated clotting time was measured" → flag NEITHER PT nor aPTT
✓ CORRECT:   Paper says "ACT and aPTT were both measured" → flag aPTT (explicit aPTT mention)
```

**3.2** Add one bullet to the existing `COMMON ERRORS TO AVOID` block:

```
- Do NOT map "ACT", "ACT-LR", or "activated clotting time" to aPTT — these are
  separate tests. The shared word "activated" is a known false-positive trigger.
```

### 4. Pre-analytical variables (`pre_analytical_variables`)

Per stakeholder decision, no schema change and no forced "Not reported" sentinel. The existing four-literal enum (`Blood collection procedures`, `Collection tube type`, `Centrifugation speed`, `Storage temperature`) is preserved. Two refinements:

**4.1** Broaden valid indicators in the `Collection tube type` block to capture citrate concentration explicitly:

```
Valid indicators include:
- EDTA / K2EDTA / K3EDTA
- sodium citrate (with concentration if provided — e.g., 3.2% citrate, 0.109 M, 3.8% buffered citrate)
- heparin (UFH or LMWH)
- serum or plasma separator tubes
- explicit brand names (e.g., BD Vacutainer, Sarstedt, Greiner Vacuette)
```

**4.2** Add an `ADDITIONAL TRIGGER for storage/handling` block under variable 4 (`Storage temperature`) so time-to-processing language counts under the existing literal rather than requiring a new enum value:

```
ADDITIONAL TRIGGER for storage/handling — count under "Storage temperature":
- explicit time-to-centrifugation or time-to-processing windows
  (e.g., "samples processed within 2 hours of collection", "centrifuged within 60 minutes")
- explicit hold conditions before centrifugation
  (e.g., "kept on ice prior to processing", "held at room temperature for ≤30 min")
These count because they describe controlled pre-analytical handling.
```

### 5. Indications for DOAC level measurement (`indications_for_doac_level_measurement`)

Add a `PRIMARY + SECONDARY EXTRACTION RULE` block at the top of the description, immediately after the opening `CRITICAL: First answer the primary question...` paragraph:

```
PRIMARY + SECONDARY EXTRACTION RULE:
Studies often have multiple legitimate purposes for measuring DOAC levels.
Capture BOTH:
1) The PRIMARY purpose (the main "why" stated in the objective/aim or abstract).
2) Any EXPLICIT SECONDARY purpose that the study actually performed
   (analyses or sub-aims described in Methods/Endpoints/Results).

Search order (mandatory):
1) Objective / Aim / "We sought to..." statements
2) Methods — study procedures, endpoints, statistical plan
3) Endpoints — primary and secondary endpoint definitions
4) Results — analyses actually reported

Do NOT add an indication merely because the topic appears in the Background, Discussion,
or as a passing covariate. The secondary purpose must be an analysis or sub-aim the
study actually performed.
```

The existing conservative anti-over-labeling guidance (`Do NOT over-label` block, ~line 218) is preserved unchanged — it backstops the new secondary-capture rule.

(No tightening of `Guide clinical decision-making` in this iteration — that was the "Both" option you did not select. Existing rules for category 4 stay as-is.)

### 6. Patient subgroup verification (no code change)

In the next response to Joseph, confirm:

- `"Elective procedure/surgery"` is a selectable subgroup option (`population.py:82`).
- `"DOAC-associated bleeding + DOAC Reversal"` is a selectable subgroup option (`population.py:85`).

Both options are already in the production schema; any disagreement on these between AI and human abstractors is genuine model behavior rather than a structural gap.

## Validation plan

1. After the prompt edits land, re-run the 50-paper validation set used for the comparison report.
2. Re-generate the comparison report to confirm:
   - aPTT false positives from ACT/activated clotting time → 0
   - Timing-blank rate decreases when papers describe peak/trough/random/serial samples
   - Clinical outcome false positives from Introduction/Discussion text decrease
   - Indications captures secondary purposes in multi-purpose studies
3. If the 50-paper improvements look acceptable, expand to the full 700+ paper corpus.

No automated test suite is added in this iteration. Validation is the existing manual + semantic-similarity workflow.

## Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Longer prompts may overflow Mistral OCR's context budget per chunk | Edits are additive but bounded — total per-field description growth is well under 1k tokens; prompts already include comparable-sized blocks |
| Rebalanced trough/peak triggers could misclassify edge cases | The lexicon ordering change is conservative — primary triggers are well-established trough phrasing (predose, pre-dose, before next dose) that Joseph confirmed clinically |
| Acute-care inference rule could over-apply "Random" in legitimate PK studies | The rule is gated on stroke/hip-fracture/trauma/urgent presentation context and is overridden by any explicit peak/trough sampling statement |
| `Guide clinical decision-making` tightening could miss legitimate decision-driven studies | The prompt explicitly lists three positive examples (surgery proceeded, reversal administered, thrombolysis eligibility) so the model has clear positive anchors |

## Reference: stakeholder decision log

- **Q1 — drop `clinical_outcome_followup_flat`?** Decision: **keep + tighten rules** (overrides verbal "drop" suggestion in meeting in favor of the written report's tighter-rule guidance).
- **Q2 — handle position/narrative/scoping papers via new field or stronger prompt?** Decision: **stronger prompt only** — no new "Publication Type" field.
- **Q3 — implement "no-blank rule" via schema, post-processing, or both?** Decision: **neither — empty stays empty when model doesn't find evidence**.
- **Q4 — indications: secondary capture, tighten `Guide clinical decision-making`, or both?** Decision: **secondary capture only** (selected via the recommended option which already includes both refinements bundled).
- **Q5 — approach option A/B/C?** Decision: **Option A — surgical prompt edits, schema-stable**.
