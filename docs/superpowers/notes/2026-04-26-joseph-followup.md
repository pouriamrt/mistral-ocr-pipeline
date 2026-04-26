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
