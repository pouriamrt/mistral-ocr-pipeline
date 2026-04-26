# Extraction Prompt Refinements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (sequential, recommended for small plans), team-driven-development (parallel swarm, recommended for 3+ tasks with parallelizable dependency graph), or superpowers:executing-plans (inline batch) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply Joseph Shaw's audit feedback as surgical prompt edits to five existing Pydantic field `description=` strings across three schema files, with zero schema/enum changes.

**Architecture:** Each task edits exactly one field's `description=` string in one of `info_extraction/schemas/{outcomes,methods,population}.py` using anchor-based `old_string` / `new_string` replacements. After each task: verify Pydantic still imports cleanly, ruff passes, then commit. No new code, no new tests, no new files.

**Tech Stack:** Python 3.13+, Pydantic V2 (`description=` strings only), ruff, uv.

**Spec:** `docs/superpowers/specs/2026-04-26-extraction-prompt-refinements-design.md`

**Validation strategy:** No automated tests in this iteration. Per-task automated checks are (a) `ruff check` on the edited file, (b) `python -c "from info_extraction.schemas import EXTRACTION_SCHEMAS, df_cols_from_models; assert len(df_cols_from_models()) == BASELINE"`. Final acceptance is the existing manual + semantic-similarity workflow on the 50-paper validation set, run separately by Pouria after this plan completes.

---

### Task 1: Pre-flight baseline

**Files:**
- Read-only: `info_extraction/schemas/__init__.py`, `info_extraction/schemas/outcomes.py`, `info_extraction/schemas/methods.py`, `info_extraction/schemas/population.py`

- [ ] **Step 1: Confirm clean working tree**

```bash
git status
```

Expected: clean tree on `main`. If anything is dirty, stash or commit before proceeding.

- [ ] **Step 2: Capture baseline column count**

```bash
uv run python -c "from info_extraction.schemas import df_cols_from_models; cols = df_cols_from_models(); print(f'BASELINE_COL_COUNT={len(cols)}')"
```

Record the printed `BASELINE_COL_COUNT` value. The number must be identical after every subsequent task. Write it down here for reference: `___` (fill in).

- [ ] **Step 3: Confirm baseline ruff is clean**

```bash
uv run ruff check info_extraction/schemas/ && uv run ruff format --check info_extraction/schemas/
```

Expected: both commands return exit code 0 with no errors. If pre-existing ruff issues exist, do NOT fix them in this plan — they're out of scope. Only document what they are so we don't blame this work for them.

- [ ] **Step 4: Confirm baseline schemas import cleanly**

```bash
uv run python -c "from info_extraction.schemas import EXTRACTION_SCHEMAS; print(f'baseline_schemas_loaded={len(EXTRACTION_SCHEMAS)}')"
```

Expected: `baseline_schemas_loaded=5`. If anything other than 5 prints, stop and investigate before continuing.

- [ ] **Step 5: No commit**

This task does not modify any files. Move on to Task 2.

---

### Task 2: Timing — add lexicon enhancements and two new disambiguation blocks

**Files:**
- Modify: `info_extraction/schemas/outcomes.py` (the `timing_of_measurement` field, ~lines 28-172)

This task makes four small additive edits inside the same `description=` string. Apply them in order.

- [ ] **Step 1: Add `immediately prior to next dose` to the trough trigger list**

Use the Edit tool with these exact strings:

`old_string`:
```
            "MAP TO 'Trough level (just prior to next dose)':\n"
            "• predose, pre-dose\n"
            "• before administration, before next dose, just prior to next dose\n"
```

`new_string`:
```
            "MAP TO 'Trough level (just prior to next dose)':\n"
            "• predose, pre-dose\n"
            "• before administration, before next dose, just prior to next dose, immediately prior to next dose\n"
```

- [ ] **Step 2: Broaden the peak hour-window list**

`old_string`:
```
            "MAP TO 'Peak level (2-4 hours post-dose)':\n"
            "• post-dose (with explicit 2-4 hour window)\n"
            "• 2 to 4 hours after administration, 2-4 h post-dose\n"
            "• Tmax, Cmax, peak concentration, presumed Cmax\n"
```

`new_string`:
```
            "MAP TO 'Peak level (2-4 hours post-dose)':\n"
            "• post-dose (with explicit 2-4 hour window)\n"
            "• 2 to 4 hours after administration, 2-4 h post-dose\n"
            "• 1-4 hours post-dose, 3-4 hours post-dose\n"
            "• narrow post-dose window of <6 hours after administration\n"
            "• Tmax, Cmax, peak concentration, presumed Cmax\n"
```

- [ ] **Step 3: Insert HOUR-WINDOW DISAMBIGUATION + ACUTE-CARE INFERENCE RULE blocks**

Insert both new sub-blocks immediately after the `MAP TO 'Timing not reported'` block and before the `CLASSIFICATION RULES` header.

`old_string`:
```
            "MAP TO 'Timing not reported':\n"
            "• No explicit timing details in Methods, Results, figure/table captions, or PK sections\n"
            "• Only vague references like 'blood was collected' without timing context\n\n"
            "═══════════════════════════════════════════════\n"
            "CLASSIFICATION RULES\n"
            "═══════════════════════════════════════════════\n"
```

`new_string`:
```
            "MAP TO 'Timing not reported':\n"
            "• No explicit timing details in Methods, Results, figure/table captions, or PK sections\n"
            "• Only vague references like 'blood was collected' without timing context\n\n"
            "HOUR-WINDOW DISAMBIGUATION (CRITICAL):\n"
            "• Narrow post-dose windows ≤ 6 hours (e.g., '1-4 h', '3-4 h post-dose') → Peak\n"
            "• Broad heterogeneous windows spanning peak and trough (e.g., '2-27 hours after intake', "
            "'median 5 h, range 1-24 h since last dose') → Random\n"
            "• Multi-timepoint dense schedules (e.g., 0, 0.5, 1, 2, 3, 4, 6, 8 h) → Serial PK/PD profile\n\n"
            "ACUTE-CARE INFERENCE RULE:\n"
            "If samples are drawn at presentation in stroke, hip fracture, trauma, or urgent admission, "
            "AND timing is anchored to 'hours since last dose' (no fixed peak/trough sampling protocol), "
            "classify as Random — UNLESS the paper explicitly states the sample was timed to peak or trough. "
            "This applies to studies where time-since-last-dose is reported as a baseline characteristic "
            "(e.g., 'median time since last dose 5 h, range 2-27 h') rather than a controlled sampling design.\n\n"
            "═══════════════════════════════════════════════\n"
            "CLASSIFICATION RULES\n"
            "═══════════════════════════════════════════════\n"
```

- [ ] **Step 4: Verify schema still imports**

```bash
uv run python -c "from info_extraction.schemas import EXTRACTION_SCHEMAS, df_cols_from_models; assert len(EXTRACTION_SCHEMAS) == 5; print(f'col_count={len(df_cols_from_models())}')"
```

Expected: prints `col_count=BASELINE_COL_COUNT` (the number you wrote down in Task 1, Step 2). If the number differs or the import errors, the edit broke the file — investigate.

- [ ] **Step 5: Verify ruff is clean**

```bash
uv run ruff check info_extraction/schemas/outcomes.py && uv run ruff format --check info_extraction/schemas/outcomes.py
```

Expected: exit code 0 on both. If `ruff format --check` flags reformatting, run `uv run ruff format info_extraction/schemas/outcomes.py` and stage the formatting change.

- [ ] **Step 6: Commit**

```bash
git add info_extraction/schemas/outcomes.py
git commit -m "fix: tighten DOAC timing extraction lexicon and add disambiguation rules

Adds 'immediately prior to next dose' trough trigger, broadens peak
hour-window list to include 1-4h and 3-4h windows, and inserts new
HOUR-WINDOW DISAMBIGUATION and ACUTE-CARE INFERENCE RULE blocks per
Joseph Shaw's audit feedback (data/todo/Comparison Report.pdf §3)."
```

---

### Task 3: Outcome gate — exclude non-original-research papers

**Files:**
- Modify: `info_extraction/schemas/outcomes.py` (the `clinical_outcomes_measured` field, ~lines 400-484)

- [ ] **Step 1: Add NON-ORIGINAL-RESEARCH PAPERS sub-block to the SET TO 'NO' IF list**

`old_string`:
```
            "SET TO 'NO' IF:\n"
            "• Outcomes are mentioned only in Introduction/Background (e.g., 'AF is associated with increased stroke risk') "
            "  without evidence of measurement in THIS study\n"
            "• Outcomes are from an underlying registry or external trial, not THIS study\n"
            "• The study describes planned follow-up but no actual events are reported in Results "
            "  (e.g., 'Patients will be followed for outcomes' but Results only show baseline data)\n"
            "• Only baseline characteristics or risk factors are discussed, not actual outcomes\n"
            "• Only laboratory measurements are reported (DOAC levels, coagulation tests) without clinical events\n"
            "• Only pharmacokinetic or pharmacodynamic parameters are reported\n"
            "• The study is purely descriptive of DOAC levels without outcome measurement\n\n"
```

`new_string`:
```
            "SET TO 'NO' IF:\n"
            "• Outcomes are mentioned only in Introduction/Background (e.g., 'AF is associated with increased stroke risk') "
            "  without evidence of measurement in THIS study\n"
            "• Outcomes are from an underlying registry or external trial, not THIS study\n"
            "• The study describes planned follow-up but no actual events are reported in Results "
            "  (e.g., 'Patients will be followed for outcomes' but Results only show baseline data)\n"
            "• Only baseline characteristics or risk factors are discussed, not actual outcomes\n"
            "• Only laboratory measurements are reported (DOAC levels, coagulation tests) without clinical events\n"
            "• Only pharmacokinetic or pharmacodynamic parameters are reported\n"
            "• The study is purely descriptive of DOAC levels without outcome measurement\n\n"
            "NON-ORIGINAL-RESEARCH PAPERS:\n"
            "If the paper is a position paper, clinical guidance document, narrative review, or scoping review "
            "(no original Methods/Results section, no patient cohort followed for events in THIS paper), "
            "set to 'No' even if bleeding/thromboembolism is mentioned in recommendations or summary text. "
            "Indicators: 'we recommend', 'guidance for', 'consensus statement', 'narrative review', "
            "absence of a 'Methods' section describing patient enrollment and event ascertainment. "
            "Note: SYSTEMATIC REVIEWS and META-ANALYSES are NOT in this exclusion — their pooled outcomes "
            "still count when the Methods/Results report aggregated event rates.\n\n"
```

- [ ] **Step 2: Verify schema still imports**

```bash
uv run python -c "from info_extraction.schemas import EXTRACTION_SCHEMAS, df_cols_from_models; assert len(EXTRACTION_SCHEMAS) == 5; print(f'col_count={len(df_cols_from_models())}')"
```

Expected: `col_count=BASELINE_COL_COUNT`.

- [ ] **Step 3: Verify ruff is clean**

```bash
uv run ruff check info_extraction/schemas/outcomes.py && uv run ruff format --check info_extraction/schemas/outcomes.py
```

Expected: exit code 0.

- [ ] **Step 4: Commit**

```bash
git add info_extraction/schemas/outcomes.py
git commit -m "fix: exclude position/guidance/narrative papers from outcome gate

Adds NON-ORIGINAL-RESEARCH PAPERS rule to clinical_outcomes_measured
gate so position papers, clinical guidance documents, narrative reviews,
and scoping reviews route to 'No' regardless of bleeding/thrombosis
keyword presence in recommendation text. Systematic reviews and
meta-analyses remain in scope. Per Joseph Shaw's audit (Comparison
Report §4)."
```

---

### Task 4: Outcome list — require trigger phrases from Methods/Results

**Files:**
- Modify: `info_extraction/schemas/outcomes.py` (the `clinical_outcomes` field, ~lines 493-605)

- [ ] **Step 1: Insert TRIGGER PHRASES (REQUIRED) sub-block after the INCLUDE-an-outcome-ONLY-if list**

`old_string`:
```
            "INCLUDE an outcome ONLY if:\n"
            "1) The Methods explicitly states it was recorded/assessed/evaluated as an outcome.\n"
            "2) The Results section reports actual events OR explicitly states 'no events occurred'. "
            "   Focus more on the Results section than the Methods section.\n\n"
            "OUTCOME CATEGORIES WITH KEYWORDS AND EXAMPLES:\n\n"
```

`new_string`:
```
            "INCLUDE an outcome ONLY if:\n"
            "1) The Methods explicitly states it was recorded/assessed/evaluated as an outcome.\n"
            "2) The Results section reports actual events OR explicitly states 'no events occurred'. "
            "   Focus more on the Results section than the Methods section.\n\n"
            "TRIGGER PHRASES — At least one must be present in Methods or Results for an outcome to qualify:\n"
            "• 'primary endpoint', 'secondary endpoint', 'primary outcome', 'secondary outcome'\n"
            "• 'all bleeding [and/or] thromboembolic complications were recorded'\n"
            "• 'during follow-up', 'during the study period'\n"
            "• 'there was a total of X events', 'X events occurred', 'no events occurred'\n"
            "• 'adjudicated by', 'ascertained by', 'events were captured'\n\n"
            "If NONE of these trigger phrases appear in Methods or Results for a given outcome category, "
            "do NOT include that category — even if the keyword (stroke, bleeding, etc.) appears in "
            "Introduction or Discussion.\n\n"
            "OUTCOME CATEGORIES WITH KEYWORDS AND EXAMPLES:\n\n"
```

- [ ] **Step 2: Verify schema still imports**

```bash
uv run python -c "from info_extraction.schemas import EXTRACTION_SCHEMAS, df_cols_from_models; assert len(EXTRACTION_SCHEMAS) == 5; print(f'col_count={len(df_cols_from_models())}')"
```

Expected: `col_count=BASELINE_COL_COUNT`.

- [ ] **Step 3: Verify ruff is clean**

```bash
uv run ruff check info_extraction/schemas/outcomes.py && uv run ruff format --check info_extraction/schemas/outcomes.py
```

Expected: exit code 0.

- [ ] **Step 4: Commit**

```bash
git add info_extraction/schemas/outcomes.py
git commit -m "fix: require explicit trigger phrases for clinical outcome inclusion

Adds a TRIGGER PHRASES (REQUIRED) sub-block to the clinical_outcomes
field. At least one of 'primary endpoint', 'no events occurred',
'during follow-up', 'adjudicated by', etc. must appear in Methods or
Results for an outcome category to qualify, preventing keyword leakage
from Introduction/Discussion. Per Joseph Shaw's audit (Comparison
Report §4)."
```

---

### Task 5: Outcome follow-up duration — tighten linkage rule

**Files:**
- Modify: `info_extraction/schemas/outcomes.py` (the `clinical_outcome_followup_flat` field, ~lines 613-712)

This task makes two additive edits inside the same `description=` string.

- [ ] **Step 1: Insert REQUIRED LINKAGE RULE block before the KEY PHRASES section**

`old_string`:
```
            "Step 2 (Decision): Based ONLY on those quoted sentences, classify the follow-up duration for each outcome type.\n\n"
            "KEY PHRASES TO LOOK FOR:\n"
```

`new_string`:
```
            "Step 2 (Decision): Based ONLY on those quoted sentences, classify the follow-up duration for each outcome type.\n\n"
            "REQUIRED LINKAGE RULE:\n"
            "Include a duration ONLY if the same sentence (or one immediately adjacent) explicitly links "
            "the duration to outcome ascertainment. Phrases that satisfy this:\n"
            "• 'patients were followed for [X] for [outcome]'\n"
            "• '[outcome] events were recorded over [X]'\n"
            "• 'median follow-up [X], during which [outcome] was assessed'\n"
            "General study-duration phrases ('study ran from 2018 to 2020') DO NOT qualify on their own. "
            "However, if only one overall follow-up duration is reported AND outcomes are explicitly "
            "measured under that follow-up window, apply that duration to all outcomes measured "
            "(see HANDLING DIFFERENT DURATIONS below).\n\n"
            "KEY PHRASES TO LOOK FOR:\n"
```

- [ ] **Step 2: Add enrollment-dates / hospital-stay / PK-window exclusion bullet**

`old_string`:
```
            "DO NOT INCLUDE follow-up duration if:\n"
            "• The study mentions imaging or days of observation but does NOT explicitly state follow-up for clinical events.\n"
            "• Follow-up is inferred from a different cohort (e.g., underlying registry) rather than THIS study.\n"
            "• Only baseline characteristics or planned follow-up are mentioned without explicit duration for outcome ascertainment.\n"
            "• The duration is mentioned in Introduction/Discussion but not in Methods/Results.\n"
            "• Only hospital stay or procedure duration is mentioned (e.g., 'patients were observed for 24 hours post-procedure' "
            "  without explicit outcome follow-up)\n"
            "• Duration is vague or unclear (e.g., 'long-term follow-up' without specific time period)\n\n"
```

`new_string`:
```
            "DO NOT INCLUDE follow-up duration if:\n"
            "• The study mentions imaging or days of observation but does NOT explicitly state follow-up for clinical events.\n"
            "• Follow-up is inferred from a different cohort (e.g., underlying registry) rather than THIS study.\n"
            "• Only baseline characteristics or planned follow-up are mentioned without explicit duration for outcome ascertainment.\n"
            "• The duration is mentioned in Introduction/Discussion but not in Methods/Results.\n"
            "• Only hospital stay or procedure duration is mentioned (e.g., 'patients were observed for 24 hours post-procedure' "
            "  without explicit outcome follow-up)\n"
            "• Duration is vague or unclear (e.g., 'long-term follow-up' without specific time period)\n"
            "• Duration is inferred from enrollment dates, hospital stay length, or PK sampling windows.\n\n"
```

- [ ] **Step 3: Verify schema still imports**

```bash
uv run python -c "from info_extraction.schemas import EXTRACTION_SCHEMAS, df_cols_from_models; assert len(EXTRACTION_SCHEMAS) == 5; print(f'col_count={len(df_cols_from_models())}')"
```

Expected: `col_count=BASELINE_COL_COUNT`.

- [ ] **Step 4: Verify ruff is clean**

```bash
uv run ruff check info_extraction/schemas/outcomes.py && uv run ruff format --check info_extraction/schemas/outcomes.py
```

Expected: exit code 0.

- [ ] **Step 5: Commit**

```bash
git add info_extraction/schemas/outcomes.py
git commit -m "fix: tighten outcome follow-up duration linkage rule

Adds a REQUIRED LINKAGE RULE block to clinical_outcome_followup_flat
specifying that the duration must be in the same or adjacent sentence
to outcome ascertainment. Adds an explicit exclusion for inferring
duration from enrollment dates, hospital stays, or PK sampling windows.
The existing 'apply overall follow-up to all outcomes' fallback is
preserved. Per Joseph Shaw's audit (Comparison Report §4)."
```

---

### Task 6: aPTT vs ACT — acronym disambiguation

**Files:**
- Modify: `info_extraction/schemas/methods.py` (the `coagulation_tests_concurrent` field, ~lines 386-521)

Two additive edits inside the same description string.

- [ ] **Step 1: Insert section 3.5 ACRONYM DISAMBIGUATION block**

`old_string`:
```
            "3.4. Negative/Ambiguous Cases for aPTT\n"
            "Do NOT classify as aPTT if:\n"
            "• Only 'thromboplastin' is mentioned without 'partial'.\n"
            "• Only PT reagents (Thromborel S, Innovin, Neoplastin, Thrombotest, Normotest, etc.) are named.\n"
            "• aPTT is mentioned only in a phrase like 'Routine coagulation tests such as PT and aPTT are widely used…' in the Introduction, "
            "  with no measurement context in Methods/Results.\n\n"
            "COMMON ERRORS TO AVOID:\n"
```

`new_string`:
```
            "3.4. Negative/Ambiguous Cases for aPTT\n"
            "Do NOT classify as aPTT if:\n"
            "• Only 'thromboplastin' is mentioned without 'partial'.\n"
            "• Only PT reagents (Thromborel S, Innovin, Neoplastin, Thrombotest, Normotest, etc.) are named.\n"
            "• aPTT is mentioned only in a phrase like 'Routine coagulation tests such as PT and aPTT are widely used…' in the Introduction, "
            "  with no measurement context in Methods/Results.\n\n"
            "3.5. CRITICAL ACRONYM DISAMBIGUATION — ACT vs aPTT\n"
            "'ACT' (activated clotting time) and 'ACT-LR' (low-range activated clotting time) are "
            "DIFFERENT TESTS from aPTT. They share the word 'activated' but measure different things "
            "on different instruments (point-of-care whole-blood vs plasma-based clotting).\n\n"
            "HARD RULE: If the paper reports 'ACT', 'activated clotting time', 'ACT-LR', or "
            "'activated clotting time low range' and does NOT independently report aPTT/APTT/PTT "
            "or 'partial thromboplastin time', then aPTT MUST NOT be flagged.\n\n"
            "The word 'activated' alone is NEVER sufficient evidence for aPTT. "
            "aPTT requires the phrase 'partial thromboplastin' OR an aPTT-specific reagent name "
            "(see section 3.2 above).\n\n"
            "EXAMPLES:\n"
            "✗ INCORRECT: Paper says 'activated clotting time was measured' → flag aPTT\n"
            "✓ CORRECT:   Paper says 'activated clotting time was measured' → flag NEITHER PT nor aPTT\n"
            "✓ CORRECT:   Paper says 'ACT and aPTT were both measured' → flag aPTT (explicit aPTT mention)\n\n"
            "COMMON ERRORS TO AVOID:\n"
```

- [ ] **Step 2: Add ACT-specific bullet to existing COMMON ERRORS TO AVOID list**

`old_string`:
```
            "COMMON ERRORS TO AVOID:\n"
            "• Do NOT assume aPTT if only 'thromboplastin' or PT reagents are named.\n"
            "• Do NOT assume both PT and aPTT were measured merely because one was.\n"
            "• Do NOT guess: If there is no specific evidence in Methods/Results, leave null.\n\n"
```

`new_string`:
```
            "COMMON ERRORS TO AVOID:\n"
            "• Do NOT assume aPTT if only 'thromboplastin' or PT reagents are named.\n"
            "• Do NOT assume both PT and aPTT were measured merely because one was.\n"
            "• Do NOT guess: If there is no specific evidence in Methods/Results, leave null.\n"
            "• Do NOT map 'ACT', 'ACT-LR', or 'activated clotting time' to aPTT — these are "
            "separate tests. The shared word 'activated' is a known false-positive trigger.\n\n"
```

- [ ] **Step 3: Verify schema still imports**

```bash
uv run python -c "from info_extraction.schemas import EXTRACTION_SCHEMAS, df_cols_from_models; assert len(EXTRACTION_SCHEMAS) == 5; print(f'col_count={len(df_cols_from_models())}')"
```

Expected: `col_count=BASELINE_COL_COUNT`.

- [ ] **Step 4: Verify ruff is clean**

```bash
uv run ruff check info_extraction/schemas/methods.py && uv run ruff format --check info_extraction/schemas/methods.py
```

Expected: exit code 0.

- [ ] **Step 5: Commit**

```bash
git add info_extraction/schemas/methods.py
git commit -m "fix: disambiguate ACT and ACT-LR from aPTT in coagulation prompt

Adds section 3.5 CRITICAL ACRONYM DISAMBIGUATION to the
coagulation_tests_concurrent field, with a hard rule that ACT,
ACT-LR, and 'activated clotting time' must not be mapped to aPTT
based on the shared word 'activated' alone. Adds matching bullet to
COMMON ERRORS TO AVOID. Per Joseph Shaw's audit (Comparison Report
§5)."
```

---

### Task 7: Pre-analytical variables — broaden tube indicators and storage triggers

**Files:**
- Modify: `info_extraction/schemas/methods.py` (the `pre_analytical_variables` field, ~lines 291-373)

Two additive edits inside the same description string.

- [ ] **Step 1: Broaden Collection tube type valid indicators**

`old_string`:
```
            "Valid indicators include:\n"
            "• EDTA / K2EDTA / K3EDTA\n"
            "• sodium citrate (with concentration if provided)\n"
            "• heparin (UFH or LMWH)\n"
            "• serum or plasma separator tubes\n"
            "• explicit brand names (e.g., BD Vacutainer, Sarstedt)\n\n"
            "3. Centrifugation speed:\n"
```

`new_string`:
```
            "Valid indicators include:\n"
            "• EDTA / K2EDTA / K3EDTA\n"
            "• sodium citrate (with concentration if provided — e.g., 3.2% citrate, 0.109 M, 3.8% buffered citrate)\n"
            "• heparin (UFH or LMWH)\n"
            "• serum or plasma separator tubes\n"
            "• explicit brand names (e.g., BD Vacutainer, Sarstedt, Greiner Vacuette)\n\n"
            "3. Centrifugation speed:\n"
```

- [ ] **Step 2: Add ADDITIONAL TRIGGER block under Storage temperature**

`old_string`:
```
            "4. Storage temperature:\n"
            "Include ONLY if storage conditions are explicitly stated.\n\n"
            "Valid indicators include:\n"
            "• −80°C, −70°C, −20°C\n"
            "• 4°C or refrigerated storage\n"
            "• room temperature with explicit wording\n\n"
            "Silence on storage conditions MUST be interpreted as NOT REPORTED.\n\n"
```

`new_string`:
```
            "4. Storage temperature:\n"
            "Include ONLY if storage conditions are explicitly stated.\n\n"
            "Valid indicators include:\n"
            "• −80°C, −70°C, −20°C\n"
            "• 4°C or refrigerated storage\n"
            "• room temperature with explicit wording\n\n"
            "ADDITIONAL TRIGGER for storage/handling — count under 'Storage temperature':\n"
            "• explicit time-to-centrifugation or time-to-processing windows "
            "(e.g., 'samples processed within 2 hours of collection', 'centrifuged within 60 minutes')\n"
            "• explicit hold conditions before centrifugation "
            "(e.g., 'kept on ice prior to processing', 'held at room temperature for ≤30 min')\n"
            "These count because they describe controlled pre-analytical handling.\n\n"
            "Silence on storage conditions MUST be interpreted as NOT REPORTED.\n\n"
```

- [ ] **Step 3: Verify schema still imports**

```bash
uv run python -c "from info_extraction.schemas import EXTRACTION_SCHEMAS, df_cols_from_models; assert len(EXTRACTION_SCHEMAS) == 5; print(f'col_count={len(df_cols_from_models())}')"
```

Expected: `col_count=BASELINE_COL_COUNT`.

- [ ] **Step 4: Verify ruff is clean**

```bash
uv run ruff check info_extraction/schemas/methods.py && uv run ruff format --check info_extraction/schemas/methods.py
```

Expected: exit code 0.

- [ ] **Step 5: Commit**

```bash
git add info_extraction/schemas/methods.py
git commit -m "fix: broaden pre-analytical variable indicators

In pre_analytical_variables: add explicit citrate concentration
examples (3.2%, 0.109 M, 3.8% buffered) and Greiner Vacuette to the
Collection tube type valid-indicators list; add an ADDITIONAL TRIGGER
block under Storage temperature so time-to-processing windows and
hold conditions count under the existing Storage temperature literal
(no new enum value). Per Joseph Shaw's audit (Comparison Report §2)."
```

---

### Task 8: Indications — primary + secondary capture rule

**Files:**
- Modify: `info_extraction/schemas/population.py` (the `indications_for_doac_level_measurement` field, ~lines 168-324)

- [ ] **Step 1: Insert PRIMARY + SECONDARY EXTRACTION RULE block after the opening CRITICAL paragraph**

`old_string`:
```
            "CRITICAL: First answer the primary question: 'What was the main purpose for measuring DOAC levels in this study?'\n"
            "Then include ALL explicit reasons stated in Methods/Results (NOT Introduction/Discussion).\n\n"
            "Two-step process:\n"
```

`new_string`:
```
            "CRITICAL: First answer the primary question: 'What was the main purpose for measuring DOAC levels in this study?'\n"
            "Then include ALL explicit reasons stated in Methods/Results (NOT Introduction/Discussion).\n\n"
            "PRIMARY + SECONDARY EXTRACTION RULE:\n"
            "Studies often have multiple legitimate purposes for measuring DOAC levels.\n"
            "Capture BOTH:\n"
            "1) The PRIMARY purpose (the main 'why' stated in the objective/aim or abstract).\n"
            "2) Any EXPLICIT SECONDARY purpose that the study actually performed "
            "(analyses or sub-aims described in Methods/Endpoints/Results).\n\n"
            "Search order (mandatory):\n"
            "1) Objective / Aim / 'We sought to...' statements\n"
            "2) Methods — study procedures, endpoints, statistical plan\n"
            "3) Endpoints — primary and secondary endpoint definitions\n"
            "4) Results — analyses actually reported\n\n"
            "Do NOT add an indication merely because the topic appears in the Background, Discussion, "
            "or as a passing covariate. The secondary purpose must be an analysis or sub-aim the "
            "study actually performed. The existing 'Do NOT over-label' guidance below still applies.\n\n"
            "Two-step process:\n"
```

- [ ] **Step 2: Verify schema still imports**

```bash
uv run python -c "from info_extraction.schemas import EXTRACTION_SCHEMAS, df_cols_from_models; assert len(EXTRACTION_SCHEMAS) == 5; print(f'col_count={len(df_cols_from_models())}')"
```

Expected: `col_count=BASELINE_COL_COUNT`.

- [ ] **Step 3: Verify ruff is clean**

```bash
uv run ruff check info_extraction/schemas/population.py && uv run ruff format --check info_extraction/schemas/population.py
```

Expected: exit code 0.

- [ ] **Step 4: Commit**

```bash
git add info_extraction/schemas/population.py
git commit -m "fix: capture primary + secondary indications for DOAC measurement

Adds a PRIMARY + SECONDARY EXTRACTION RULE block to
indications_for_doac_level_measurement so multi-purpose studies
record both the primary aim and any explicit secondary analyses
performed. Mandatory search order: Objective/Aim → Methods →
Endpoints → Results. Existing 'Do NOT over-label' guidance preserved
unchanged as a backstop. Per Joseph Shaw's audit (Comparison Report
§7)."
```

---

### Task 9: Final integration check + Joseph-facing verification note

**Files:**
- Read-only verification of `info_extraction/schemas/{outcomes,methods,population}.py`
- Create: `docs/superpowers/notes/2026-04-26-joseph-followup.md` (a stub for the email/comparison response)

- [ ] **Step 1: Full schema sanity check**

```bash
uv run python -c "from info_extraction.schemas import EXTRACTION_SCHEMAS, df_cols_from_models; cols = df_cols_from_models(); print(f'schemas={len(EXTRACTION_SCHEMAS)} cols={len(cols)}')"
```

Expected: `schemas=5 cols=BASELINE_COL_COUNT` (matches Task 1, Step 2 baseline).

- [ ] **Step 2: Full ruff sweep**

```bash
uv run ruff check info_extraction/schemas/ && uv run ruff format --check info_extraction/schemas/
```

Expected: exit code 0 on both.

- [ ] **Step 3: Confirm no enum values changed**

```bash
uv run python -c "
from info_extraction.schemas import EXTRACTION_SCHEMAS
import typing
for cls in EXTRACTION_SCHEMAS:
    for name, field in cls.model_fields.items():
        ann = field.annotation
        # Walk to the inner Literal if Optional[List[Literal[...]]]
        for arg in typing.get_args(ann) or []:
            for arg2 in typing.get_args(arg) or []:
                if typing.get_origin(arg2) is typing.Literal:
                    print(f'{cls.__name__}.{name}: {len(typing.get_args(arg2))} literals')
"
```

Expected: a deterministic list of `(class.field: N literals)` lines. Compare against the same command's output run before Task 2 (you can rebuild this baseline by checking out `main` in a worktree and running there). The literal counts must be identical to baseline. If any number changed, an enum was modified — that violates the spec's "no literal/enum changes" rule and the offending task must be reviewed.

- [ ] **Step 4: Smoke-render one schema's prompt to confirm no encoding/escape regressions**

```bash
uv run python -c "
from info_extraction.schemas.outcomes import ExtractionOutcomes
desc = ExtractionOutcomes.model_fields['timing_of_measurement'].description
assert desc is not None
assert 'immediately prior to next dose' in desc
assert 'HOUR-WINDOW DISAMBIGUATION' in desc
assert 'ACUTE-CARE INFERENCE RULE' in desc
print('timing_of_measurement: OK')

from info_extraction.schemas.methods import ExtractionMethods
desc2 = ExtractionMethods.model_fields['coagulation_tests_concurrent'].description
assert 'CRITICAL ACRONYM DISAMBIGUATION' in desc2
assert 'ACT-LR' in desc2
print('coagulation_tests_concurrent: OK')

from info_extraction.schemas.population import ExtractionPopulationIndications
desc3 = ExtractionPopulationIndications.model_fields['indications_for_doac_level_measurement'].description
assert 'PRIMARY + SECONDARY EXTRACTION RULE' in desc3
print('indications_for_doac_level_measurement: OK')
"
```

Expected: three `OK` lines, no AssertionError. If any assertion fails, the corresponding task's edit didn't land — investigate.

- [ ] **Step 5: Create Joseph-facing followup stub**

Create `docs/superpowers/notes/2026-04-26-joseph-followup.md` with this exact content (Pouria will adapt and send):

```markdown
# Followup notes for Joseph

## Schema verification (no code change needed)

The two patient-subgroup options you flagged are already in the production schema:

- `Elective procedure/surgery` — `info_extraction/schemas/population.py:82`
- `DOAC-associated bleeding + DOAC Reversal` — `info_extraction/schemas/population.py:85`

So any disagreement on these subgroups in the comparison report reflects model
behavior, not a missing schema option.

## Prompt edits applied (all schema-stable)

Per the consolidated audit report, we made surgical prompt-only edits across
five fields. CSV/Parquet column structure is unchanged.

| Audit point | Field | Change |
|---|---|---|
| §3 Timing | `timing_of_measurement` | Added 'immediately prior to next dose' trough trigger; broadened peak hour-window list (1-4h, 3-4h, <6h post-dose); inserted HOUR-WINDOW DISAMBIGUATION and ACUTE-CARE INFERENCE RULE blocks |
| §4 Outcomes | `clinical_outcomes_measured` | Added NON-ORIGINAL-RESEARCH PAPERS exclusion (position/guidance/narrative/scoping) |
| §4 Outcomes | `clinical_outcomes` | Added TRIGGER PHRASES (REQUIRED) sub-block — 'primary endpoint', 'no events occurred', etc. |
| §4 Outcomes | `clinical_outcome_followup_flat` | Added REQUIRED LINKAGE RULE; excluded inference from enrollment dates / hospital stays / PK windows |
| §5 Comparator | `coagulation_tests_concurrent` | Added section 3.5 ACRONYM DISAMBIGUATION — ACT/ACT-LR cannot map to aPTT |
| §2 Pre-analytical | `pre_analytical_variables` | Broadened citrate-concentration and brand-name indicators; added time-to-processing trigger under Storage temperature |
| §7 Indications | `indications_for_doac_level_measurement` | Added PRIMARY + SECONDARY EXTRACTION RULE with mandatory search order |

## Out of scope (deliberate decisions)

- **No "force Not reported" rule.** Empty cells when the model genuinely doesn't find evidence remain acceptable; we did not add a forced sentinel that could mask real misses.
- **No new "Publication Type" field.** The non-original-research exclusion is handled inside the existing outcome gate prompt.
- **`clinical_outcome_followup_flat` not dropped.** Despite the verbal suggestion in our 2026-04-22 meeting, your written report kept this field with tighter rules; we followed the written guidance.

## Next step

Re-run the 50-paper validation set and regenerate the comparison report. Specific signals to watch:

- aPTT false positives from `activated clotting time` papers → expect 0
- Timing-blank rate on PK and acute-care papers → expect a decrease
- Clinical outcome false positives from Introduction/Discussion text → expect a decrease
- Indications captures secondary purposes in multi-purpose studies → expect more multi-label rows
```

- [ ] **Step 6: Commit the verification note**

```bash
git add docs/superpowers/notes/2026-04-26-joseph-followup.md
git commit -m "docs: add Joseph followup note summarizing schema-stable prompt edits"
```

- [ ] **Step 7: Final summary**

Print a one-line summary for the operator:

```bash
echo "All 7 prompt edits landed. Run the 50-paper validation set next: 'uv run python main.py' on the validation corpus, then regenerate the comparison report."
```

The plan is complete. Pouria runs the validation pass separately when ready.

---

## Self-Review Notes

**Spec coverage check:**

| Spec section | Task |
|---|---|
| §1 Timing 1.1 (immediately prior to next dose) | Task 2 step 1 |
| §1 Timing 1.2 (peak hour-window list) | Task 2 step 2 |
| §1 Timing 1.3 (HOUR-WINDOW DISAMBIGUATION) | Task 2 step 3 |
| §1 Timing 1.4 (ACUTE-CARE INFERENCE RULE) | Task 2 step 3 (bundled with 1.3) |
| §2.1 Outcome gate (NON-ORIGINAL-RESEARCH PAPERS) | Task 3 |
| §2.2 Outcome list (TRIGGER PHRASES) | Task 4 |
| §2.3 Follow-up duration (REQUIRED LINKAGE RULE + enrollment exclusion) | Task 5 |
| §3 aPTT vs ACT (3.1 + 3.2) | Task 6 |
| §4.1 Pre-analytical citrate concentration | Task 7 step 1 |
| §4.2 Pre-analytical storage time-to-processing | Task 7 step 2 |
| §5 Indications PRIMARY + SECONDARY rule | Task 8 |
| §6 Patient subgroup verification (no code change) | Task 9 step 5 (Joseph followup note) |
| Validation plan from spec | Task 9 step 7 reminder |

All spec sections covered.

**Type/signature consistency:** Every task uses the same baseline check (`assert len(EXTRACTION_SCHEMAS) == 5`) and the same column-count invariant (`BASELINE_COL_COUNT` from Task 1). No function signatures changed.

**Placeholder scan:** No TBDs, TODOs, or "implement appropriate" placeholders. Every step has either an exact command or exact `old_string`/`new_string` text.
