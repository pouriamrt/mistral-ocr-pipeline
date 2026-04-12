"""Diagnostic Performance Metrics schema."""

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ------------------------------------
# 5) Diagnostic Performance Metrics
# ------------------------------------
class ExtractionDiagnosticPerformance(BaseModel):
    """
    Guidelines:
    0) Be thorough and detailed.
    1) Do not infer or guess.
    2) Use null if unsure.
    3) Select all applicable.
    4) Output only facts explicitly in the PDF.
    5) If ambiguous, set null (do not guess).
    6) Numeric values must be exact.
    7) Resolve conflicts by the clearest statement (title→early pages; patients→methods/results).
    8) IGNORE external knowledge.
    9) Ignore Introduction/Background, References and Acknowledgments content.
    10) Focus on Methods and Results and Abstract sections.
    """

    # Diagnostic performance metrics for categorical cutoffs
    diagnostic_performance_categorical: Optional[
        List[
            Literal[
                "Sensitivity",
                "Specificity",
                "Positive Predictive Value (PPV)",
                "Negative Predictive Value (NPV)",
            ]
        ]
    ] = Field(
        default=None,
        alias="Diagnostic Performance Metrics - Categorical Cutoffs",
        description=(
            "CRITICAL INCLUSION RULE: Count as Reported ONLY if ALL of the following are true:\n"
            "1) DOAC levels quantified using a reference method: DOAC-calibrated anti-Xa (ng/mL) OR LC-MS/MS\n"
            "2) Comparison to at least one comparator assay: PT/aPTT/dTT/TT, LMWH-calibrated anti-Xa (IU/mL), "
            "viscoelastic testing, or thrombin generation assays\n"
            "3) Numeric diagnostic performance results reported in Results/tables/figures/supplementary results:\n"
            "   - Sensitivity, specificity, PPV, NPV for detecting a DOAC concentration threshold (binary cutoff), OR\n"
            "   - 2×2 table enabling calculation of these metrics\n"
            "4) Results are from the study's own analysis (not just background mentions in Introduction/Discussion)\n\n"
            "Two-step process:\n"
            "Step 1 (Evidence): Quote exact sentences from Results/tables/figures that report sensitivity, specificity, "
            "PPV, or NPV with numeric values (%, proportion, or decimal) for categorical cutoffs comparing comparator "
            "assays to DOAC level thresholds. Include table/figure numbers and location.\n"
            "Step 2 (Decision): Based ONLY on those quoted sentences, classify which metrics were reported.\n\n"
            "KEY GUARDRAILS:\n"
            "• Evidence requirement: For every extracted metric, provide exact supporting quote + location (Table/Figure/Results). "
            "If no quote in Results/tables/figures → Not Reported\n"
            "• No inference: Do not infer or estimate cutoffs or metrics. Do not fill missing values.\n"
            "• Section rule: Ignore statements that only appear in Introduction/Discussion as background unless the paper "
            "also reports the study's own numeric results in Results/tables.\n"
            "• Analytical vs diagnostic: If 'sensitivity' or 'specificity' refers to assay validation (LOD/LOQ/interference), "
            "do not treat it as diagnostic performance.\n\n"
            "Comparator assays:\n"
            "• Coagulation tests: PT/INR, aPTT, dTT, TT\n"
            "• LMWH/heparin-calibrated anti-Xa (IU/mL) - NOT DOAC-calibrated\n"
            "• Viscoelastic testing: ROTEM, TEG, ClotPro, etc.\n"
            "• Thrombin generation assays: TGA, CAT, ETP, etc.\n\n"
            "IGNORE if:\n"
            "• Only correlation coefficients reported (use 'Continuous Relationships' field)\n"
            "• Only background mentions in Introduction/Discussion without numeric results\n"
            "• Analytical validation metrics (LOD/LOQ/interference) without clinical diagnostic performance\n"
            "• Comparison between two DOAC quantification methods (e.g., LC-MS vs calibrated anti-Xa) without comparator assay\n\n"
            "If the article does not clearly report categorical diagnostic performance metrics, leave null. Do NOT guess."
        ),
    )
    diagnostic_performance_categorical_sentence_from_text: Optional[List[str]] = Field(
        default=None,
        alias="Diagnostic Performance Metrics - Categorical Cutoffs Sentence from Text",
        description="Exact sentences or paragraph containing the categorical diagnostic performance metrics.",
    )

    # Diagnostic performance metrics for continuous relationships
    diagnostic_performance_continuous: Optional[
        List[
            Literal[
                "Spearman correlation coefficient",
                "Pearson correlation coefficient",
                "Linear Correlation - Not Specified",
                "R² (Coefficient of Determination)",
            ]
        ]
    ] = Field(
        default=None,
        alias="Diagnostic Performance Metrics - Continuous Relationships",
        description=(
            "GOAL:\n"
            "Identify which continuous numeric relationship metrics are reported between a comparator assay and DOAC concentration "
            "(measured by a reference method).\n\n"
            "ABSOLUTE SOURCE RESTRICTION (RESULTS-ONLY):\n"
            "Evidence may come ONLY from: Results text, Results tables, figures/figure captions, or supplementary Results.\n"
            "Mentions in Abstract/Introduction/Methods/Discussion do NOT count.\n\n"
            "GLOBAL INCLUSION (ALL MUST BE TRUE FOR ANY LABEL):\n"
            "1) DOAC concentration measured by a reference method: DOAC-calibrated anti-Xa (ng/mL or equivalent) OR LC-MS/MS.\n"
            "2) Comparator assay evaluated vs DOAC concentration (NOT DOAC method-vs-method).\n"
            "3) Numeric metric reported in allowed Results sources: r/rho/ρ/rs and/or R².\n"
            "4) Metric is from the study's own results (not background-only).\n\n"
            "EVIDENCE DISCIPLINE (MANDATORY, PER LABEL):\n"
            "- For EACH label you output, you MUST have ≥1 exact supporting quote + location for THAT specific label.\n"
            "- If no qualifying quotes exist for any label → output null.\n\n"
            "MUTUAL EXCLUSIVITY (HARD GATE):\n"
            "The correlation-type labels form a mutually exclusive set:\n"
            "  S = 'Spearman correlation coefficient'\n"
            "  P = 'Pearson correlation coefficient'\n"
            "  L = 'Linear Correlation - Not Specified'\n"
            "RULE: Output AT MOST ONE of {S, P, L}.\n"
            "FORBIDDEN COMBINATION (NON-NEGOTIABLE): If you output L, you MUST NOT output S or P.\n\n"
            "TWO-STAGE PROCEDURE (MANDATORY):\n"
            "Stage 1 — Evidence Harvest:\n"
            "  Collect all qualifying quotes from allowed Results sources that include:\n"
            "  (a) comparator assay term, AND\n"
            "  (b) a DOAC reference anchor (LC-MS/MS OR ng/mL for DOAC-calibrated anti-Xa), AND\n"
            "  (c) a numeric metric token: r OR rho/ρ OR rs OR R².\n"
            "Stage 2 — Label Emission using the decision algorithm below.\n\n"
            "DECISION ALGORITHM (STRICT, APPLY IN ORDER):\n"
            "Step B — Choose EXACTLY ONE correlation-type label (or none):\n"
            "  B1) If ANY qualifying quote explicitly says 'Spearman' OR uses rho/ρ OR rs (as the correlation coefficient) →\n"
            "      Output ONLY S.\n"
            "  B2) ELSE IF ANY qualifying quote explicitly says 'Pearson' OR 'Pearson r' →\n"
            "      Output ONLY P.\n"
            "  B3) ELSE IF ANY qualifying quote reports a numeric correlation as r (e.g., 'r = 0.72' or 'r=0.72') BUT does NOT name "
            "      Spearman/Pearson and does NOT use rho/ρ/rs →\n"
            "      Output ONLY L.\n"
            "  B4) ELSE output none of {S,P,L}.\n\n"
            "CONFLICT RESOLUTION (PREVENTS L WITH S/P):\n"
            "- If there exists ANY Spearman evidence anywhere in the harvested quotes, L is ILLEGAL.\n"
            "- If there exists ANY Pearson evidence anywhere in the harvested quotes (and no Spearman evidence), L is ILLEGAL.\n"
            "- L is permitted ONLY when there is correlation evidence (numeric r) AND there is ZERO evidence of Spearman AND ZERO evidence of Pearson.\n\n"
            "Step C — R² label (INDEPENDENT):\n"
            "- If ANY qualifying quote explicitly reports R² / R-squared / coefficient of determination → add 'R² (Coefficient of Determination)'.\n"
            "- R² may co-exist with the single chosen label from {S,P,L}.\n\n"
            "DISAMBIGUATION RULES:\n"
            "- Do NOT infer Spearman/Pearson from the presence of R².\n"
            "- Regression-only outputs (slope/intercept) without r/rho/ρ/rs do not justify S/P/L.\n"
            "- The word 'correlated' without numeric r/rho/R² does not qualify.\n"
            "- Ignore analytical validation metrics (LOD/LOQ/interference/precision) unless comparator-vs-DOAC numeric relationship is present.\n\n"
            "═══════════════════════════════════════════════\n"
            "IMPORTANT: REGRESSION-BASED ASSAY COMPARISON IS VALID EVIDENCE\n"
            "═══════════════════════════════════════════════\n"
            "Linear regression, r, R², and correlation coefficients between a comparator assay and DOAC concentration "
            "are valid assay-comparison evidence, even if the paper does not use the exact word 'correlation'. "
            "This behavior is CORRECT and must be PRESERVED.\n\n"
            "Specifically:\n"
            "- If a study reports R² from a regression of comparator assay values against DOAC concentration, "
            "  this IS valid diagnostic/performance evidence. Include 'R² (Coefficient of Determination)'.\n"
            "- If a study reports linear regression with r values comparing a comparator assay to DOAC levels, "
            "  this IS valid evidence for the appropriate correlation label.\n"
            "- The absence of the explicit word 'correlation' does NOT disqualify the evidence if numeric "
            "  r/R² values are reported in the context of assay-vs-DOAC comparison.\n"
            "- Regression-based assay comparison counts as valid diagnostic/performance evidence.\n"
            "═══════════════════════════════════════════════\n\n"
            "OUTPUT:\n"
            "Return only the labels supported by qualifying quotes and the rules above; otherwise null.\n"
            "Never output more than one of {S,P,L}. If L is present, S and P must be absent.\n"
        ),
    )
    diagnostic_performance_continuous_sentence_from_text: Optional[List[str]] = Field(
        default=None,
        alias="Diagnostic Performance Metrics - Continuous Relationships Sentence from Text",
        description="Exact sentences or paragraph containing the continuous diagnostic performance metrics.",
    )

    # Comparator assays used for diagnostic performance evaluation
    comparator_assays: Optional[
        List[
            Literal[
                "Coagulation testing - Prothrombin time (PT)",
                "Coagulation testing - Activated partial thromboplastin time (aPTT)",
                "Coagulation testing - Dilute thrombin time (dTT)",
                "Coagulation testing - Thrombin Time (TT)",
                "Anti-Xa assays with LMWH calibrators (IU/mL)",
                "Viscoelastic testing",
                "Thrombin generation assays",
            ]
        ]
    ] = Field(
        default=None,
        alias="Comparator Assays",
        description=(
            "GOAL:\n"
            "Identify which comparator assay categories were evaluated AGAINST DOAC concentration measured by a reference method, "
            "using the study's OWN numeric results (i.e., analyses actually performed in this study).\n\n"
            "ABSOLUTE SOURCE RESTRICTION (RESULTS-ONLY):\n"
            "You may use evidence ONLY from: Results section, Results tables, figures/figure captions, or supplementary Results.\n"
            "Mentions in Abstract/Introduction/Methods/Discussion do NOT count as evidence, even if assays or correlations are listed there.\n\n"
            "TWO-STAGE, QUOTE-FIRST PROCEDURE (MANDATORY):\n"
            "Stage 1 (Evidence Harvest):\n"
            "  - Produce ≥1 EXACT verbatim quote per selected category.\n"
            "  - Each quote MUST come from an allowed Results source and MUST satisfy E0 + E1–E3.\n"
            "Stage 2 (Category Selection):\n"
            "  - Select a category ONLY if Stage 1 produced a qualifying quote for it.\n"
            "If Stage 1 yields zero qualifying quotes for all categories → output null.\n\n"
            "GLOBAL HARD GATE (E0 + E1–E3 MUST ALL HOLD IN THE SAME QUOTE):\n"
            "E0) STUDY-EXECUTED COMPARATOR EVALUATION:\n"
            "    The quote must clearly indicate the assay was actually evaluated in this study's results "
            "(e.g., reported as measured, analyzed, compared, correlated, or used to classify samples in the Results).\n"
            "    Background commentary, hypotheses, literature context, or 'could be used' statements do NOT satisfy E0.\n"
            "E1) The quote explicitly names the assay or platform (no implicit or generic references).\n"
            "E2) The quote contains at least one qualifying numeric performance/relationship metric:\n"
            "    - Continuous: r, rho/ρ, rs, or R²\n"
            "    - Categorical: sensitivity, specificity, PPV, NPV, or a 2×2 table with numeric counts\n"
            "E3) The quote explicitly links that numeric metric to DOAC concentration measured by a reference method.\n"
            "    The reference method MUST be explicitly stated as:\n"
            "    - LC-MS/MS, OR\n"
            "    - DOAC-calibrated anti-Xa reported in ng/mL (or equivalent)\n"
            "If any of E0–E3 is missing → the category is FORBIDDEN.\n\n"
            "REFERENCE METHOD CLARIFICATION (IMPORTANT):\n"
            "- DOAC-calibrated anti-Xa in ng/mL is a reference method.\n"
            "- LMWH/heparin-calibrated anti-Xa reported in IU/mL or U/mL is a comparator assay.\n"
            "- Do NOT count comparisons between two reference methods (e.g., LC-MS/MS vs DOAC-calibrated anti-Xa).\n\n"
            "STRICT CATEGORY MAPPING (ONLY if explicitly named in the qualifying quote):\n"
            "• PT: 'prothrombin time', PT, INR, PTr.\n"
            "• aPTT: 'activated partial thromboplastin time', aPTT/APTT/PTT.\n"
            "• dTT: 'dilute thrombin time', dTT, 'diluted thrombin time', Hemoclot.\n"
            "• TT: 'thrombin time', TT (exclude dilute/dTT/Hemoclot).\n"
            "• Anti-Xa assays with LMWH calibrators (IU/mL): LMWH- or heparin-calibrated anti-Xa/anti-FXa reported as IU/mL or U/mL.\n"
            "  Do NOT treat DOAC-calibrated anti-Xa in ng/mL as a comparator.\n\n"
            "DISCUSSION-ONLY CORRELATION EXCLUSION (CRITICAL):\n"
            "- If PT/aPTT (or any assay) is mentioned ONLY in Discussion/Introduction/Methods as a possible correlate or comparison,\n"
            "  and there is NO qualifying Results quote satisfying E0–E3, then you MUST return null for that category.\n"
            "- Even if the Discussion contains numeric correlations, they do NOT count.\n\n"
            "HALLUCINATION FIREWALLS (NEGATIVE RULES):\n"
            "- Generic phrases such as 'coagulation assays', 'global coagulation tests', 'whole-blood testing', "
            "'point-of-care', or 'viscoelastic' WITHOUT explicit platform + numeric metric + reference-method linkage "
            "do NOT qualify for any category.\n"
            "- Listing assays as part of a laboratory panel or methods inventory does NOT constitute diagnostic evaluation.\n"
            "- Do NOT infer a category because it is commonly used in the field.\n"
            "- Absence of qualifying Results evidence overrides any mentions elsewhere.\n\n"
            "SPECIAL HARD GATE — VISCOELASTIC TESTING (NON-NEGOTIABLE):\n"
            "Select 'Viscoelastic testing' ONLY if ONE single quote (same quote) satisfies ALL conditions below:\n"
            "V1) Explicitly names a viscoelastic platform: ROTEM, TEG, ClotPro, Sonoclot, Quantra, or ReoRox.\n"
            "V2) Reports a numeric viscoelastic metric, such as:\n"
            "    - ROTEM: CT, CFT, MCF, A5/A10/A20, ML\n"
            "    - TEG: R time, K time, MA, α-angle, LY30\n"
            "    OR reports a numeric relationship metric (r, rho/ρ, R², %, or 2×2 counts) for those parameters.\n"
            "V3) Explicitly states that the metric is evaluated versus DOAC concentration measured by a reference method "
            "(must include 'LC-MS/MS', 'ng/mL', or explicit wording 'DOAC concentration/level').\n"
            "V4) Quote appears in Results text, Results tables, figures, or supplementary Results.\n"
            "If ANY of V1–V4 fails → DO NOT select 'Viscoelastic testing'.\n"
            "For example ['We assessed prothrombin time (PT) reagents and commercially available anti-Xa assays (Biophen) calibrated for rivaroxaban and heparin in comparison to liquid chromatography\u00e2\u20ac\u201cmass spectrometry (LC-MS/MS) measurements of rivaroxaban concentration in samples from patients on treatment with rivaroxaban for stroke prevention in atrial fibrillation.', 'The prothrombin time (PT) was measured using two reagents. The Thromborel S\u00c2\u00ae (Siemens Healthcare Diagnostics Products GmbH, Marburg, Germany) derived from human placenta and the Normotest\u00c2\u00ae (Technoclone GmbH, Vienna, Austria) of combined thromboplastin of rabbit brain and bovine plasma.', 'The BIOPHEN Heparin LRT\u00c2\u00ae assay was also calibrated with commercially available low molecular weight heparin (LMWH) calibrators in a separate run using a five-point calibration curve of the concentrations 0.00, 0.38, 0.77, 1.18, and 1.51 U/ml.'] is NOT a valid quote for 'Viscoelastic testing'.\n"
            "SPECIAL HARD GATE — THROMBIN GENERATION (TGA):\n"
            "Select 'Thrombin generation assays' ONLY if ONE single quote:\n"
            "- explicitly names thrombin generation (thrombin generation, TGA, CAT, ETP), AND\n"
            "- reports a qualifying numeric metric (r, rho/ρ, R², %, or 2×2 counts), AND\n"
            "- explicitly links it to DOAC concentration measured by a reference method (LC-MS/MS or DOAC-calibrated anti-Xa ng/mL), AND\n"
            "- appears in Results/tables/figures/supplementary Results.\n\n"
            "EXCLUSIONS (DO NOT COUNT AS DIAGNOSTIC PERFORMANCE):\n"
            "- Analytical validation only: LOD, LOQ, interference, precision, linearity, recovery.\n"
            "- Method-vs-method DOAC quantification without a comparator assay.\n"
            "- Any evidence located only outside allowed Results sources.\n\n"
            "For example ['The PD tests, including those for activated partial thromboplastin time (APTT) and prothrombin time (PT), were conducted within 2 h of sampling in the hospital laboratory department, which acquired ISO 15189 certification (Medical laboratories-requirements for quality and competence. International Organization for Standardization: Geneva, Switzerland, 2022).', 'The PD profiles are summarized in Table 2. There was no significant difference in PT (p = 0.685) or APTT (p = 0.662) between the patients using rivaroxaban and amiodarone concurrently and those using rivaroxaban alone.'] are NOT valid quotes for 'Coagulation testing - Prothrombin time (PT)' or 'Coagulation testing - Activated partial thromboplastin time (aPTT)'."
            "═══════════════════════════════════════════════\n"
            "IMPORTANT: REGRESSION-BASED ASSAY COMPARISON IS VALID EVIDENCE\n"
            "═══════════════════════════════════════════════\n"
            "Linear regression, r, R², and correlation coefficients between a comparator assay and DOAC "
            "concentration constitute valid evidence for comparator assay evaluation (satisfying E2). "
            "If a study reports R² or r values from comparing a comparator assay against DOAC levels "
            "measured by a reference method, this IS a qualifying numeric metric even if the paper does "
            "not use the word 'correlation' or 'diagnostic performance'. Regression-based assay comparison "
            "is valid evidence and should be captured.\n"
            "═══════════════════════════════════════════════\n\n"
            "OUTPUT RULE (NULL BIAS):\n"
            "Return ONLY categories that have ≥1 qualifying quote meeting E0-E3 (and special gates where applicable).\n"
            "If none qualify → return null.\n"
            "Do not guess. Do not infer. Evidence must be explicit.\n"
        ),
    )
    comparator_assays_sentence_from_text: Optional[List[str]] = Field(
        default=None,
        alias="Comparator Assays Sentence from Text",
        description="Exact sentences or paragraph identifying which comparator assays were used for diagnostic performance evaluation.",
    )

    # DOAC concentration cutoff evaluated for categorical diagnostic performance
    diagnostic_performance_categorical_cutoff_value: Optional[str] = Field(
        default=None,
        alias="Categorical Diagnostic Performance - Evaluated DOAC Cutoff",
        description=(
            "TASK:\n"
            "Extract the exact DOAC concentration cutoff value that was explicitly evaluated as part of a categorical diagnostic "
            "comparison, where Sensitivity, Specificity, PPV, and/or NPV are reported elsewhere.\n\n"
            "ABSOLUTE SOURCE RESTRICTION (RESULTS-ONLY):\n"
            "Use evidence ONLY from Results text, Results tables, figures/figure captions, or supplementary Results.\n"
            "Ignore Abstract, Introduction, Methods, Discussion, References, and Acknowledgments.\n\n"
            "GLOBAL HARD GATE (ALL CONDITIONS MUST BE MET):\n"
            "1) A DOAC concentration threshold is explicitly stated as a numeric value with unit ng/mL.\n"
            "2) The value is explicitly described as a cutoff or threshold used for categorical diagnostic performance evaluation\n"
            "   (sens/spec/PPV/NPV or a 2×2 table), not for assay calibration or measurement range.\n"
            "3) The categorical comparison is between a comparator assay and DOAC concentration measured by a reference method\n"
            "   (LC-MS/MS or DOAC-calibrated anti-Xa reported in ng/mL).\n"
            "If ANY condition fails → return null.\n\n"
            "WHAT TO RETURN:\n"
            "• Return the cutoff EXACTLY as written in the source (e.g., '30 ng/mL', '<30 ng/mL', '≥50 ng/mL').\n"
            "• If multiple cutoffs are mentioned, return ONLY the single cutoff used for the reported categorical metrics;\n"
            "  if no single primary cutoff is explicitly identifiable → return null.\n\n"
            "DO NOT RETURN (STRICT EXCLUSIONS):\n"
            "• Calibration values, assay measurement ranges, LOD/LOQ, or any values reported in IU/mL or U/mL.\n"
            "• Thresholds used only for assay setup, reagent calibration, or analytical validation.\n"
            "• Values mentioned solely in Abstract, Introduction, or Discussion.\n"
            "• Any inferred, estimated, derived, or averaged cutoff.\n\n"
            "EVIDENCE DISCIPLINE:\n"
            "The cutoff must be explicitly stated in Results text, tables, figures, or supplementary Results.\n"
            "If categorical diagnostic performance metrics are reported but the evaluated cutoff is not explicitly stated → return null.\n\n"
            "OUTPUT RULE:\n"
            "Return ONLY the exact cutoff value string or null. Do not infer, normalize, reinterpret, or guess."
        ),
    )
    diagnostic_performance_categorical_cutoff_value_sentence_from_text: Optional[
        str
    ] = Field(
        default=None,
        alias="Categorical Diagnostic Performance - Evaluated DOAC Cutoff Sentence from Text",
        description="Exact sentences or paragraph containing the DOAC concentration cutoff value that was evaluated as part of a categorical diagnostic comparison.",
    )

    model_config = ConfigDict(populate_by_name=True)
