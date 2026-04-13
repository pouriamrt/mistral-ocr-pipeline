"""Outcomes schema."""

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ------------------------------------
# 4) Outcomes Blocks
# ------------------------------------
class ExtractionOutcomes(BaseModel):
    """
    Guidelines:
    0) Be thorough and detailed.
    1) Do not infer or guess.
    2) Use null if unsure.
    3) Select all applicable.
    4) Output only facts explicitly in the text.
    5) If ambiguous, set null (do not guess).
    6) Numeric values must be exact.
    7) Resolve conflicts by the clearest statement (title→early pages; patients→methods/results).
    8) IGNORE external knowledge.
    9) Ignore Introduction/Background, References and Acknowledgments content.
    10) Focus on Methods and Results and Abstract sections.
    """

    # Timing of DOAC Level Measurement Relative to DOAC Intake
    timing_of_measurement: Optional[
        List[
            Literal[
                "Peak level (2–4 hours post-dose)",
                "Trough level (just prior to next dose)",
                "Residual level after interruption / pre-procedural",
                "Serial PK/PD profile",
                "Random level",
                "Timing not reported",
            ]
        ]
    ] = Field(
        default=None,
        alias="Timing of DOAC level measurement relative to DOAC intake",
        description=(
            "GOAL: Extract the timing of DOAC blood-sample collection relative to drug intake, "
            "as described in the study's own Methods, Results, figure/table captions, or pharmacokinetic sections.\n\n"
            "═══════════════════════════════════════════════\n"
            "SECTION ROUTING (MANDATORY SEARCH ORDER)\n"
            "═══════════════════════════════════════════════\n"
            "You MUST search for timing information in the following order. Do NOT skip any step.\n"
            "1) METHODS section: look for 'Sample collection', 'Blood sampling', 'Pharmacokinetic sampling', "
            "'Study procedures', 'Laboratory methods' subsections.\n"
            "2) PHARMACOKINETIC / PK SECTIONS: look for concentration-time descriptions, sampling schedules, "
            "PK profile descriptions, dosing-interval sampling.\n"
            "3) FIGURE AND TABLE CAPTIONS: look for protocol figures, timeline diagrams, sampling-schedule tables, "
            "concentration-time curve legends. Timing information in captions counts as valid evidence.\n"
            "4) RESULTS section: look for explicit timing statements, PK results tables, sampling descriptions.\n"
            "5) ABSTRACT METHODS: use as backup ONLY if none of the above sections contain timing information.\n"
            "6) IGNORE Introduction, Background, Discussion, and References for timing classification entirely.\n\n"
            "CRITICAL: If timing information appears ONLY in figure/table captions or PK subsections, "
            "it is still valid. Do NOT leave timing blank just because it is absent from the main prose.\n\n"
            "═══════════════════════════════════════════════\n"
            "PRELIMINARY STEP: STUDY GENRE CLASSIFICATION\n"
            "═══════════════════════════════════════════════\n"
            "Before extracting timing, determine the study genre from the title, abstract, and methods:\n"
            "A) Clinical outcome cohort or trial (patients followed for clinical events)\n"
            "B) PK/PD study (concentration-time profiles, serial sampling)\n"
            "C) Assay validation / diagnostic accuracy study\n"
            "D) Mechanistic / laboratory study\n"
            "E) Case report / case series\n"
            "F) Perioperative / urgent-procedure study\n"
            "Genre-specific timing rules:\n"
            "- Genre B (PK/PD): Look for serial sampling schedules. If multiple timed samples are collected "
            "(e.g., 0, 0.5, 1, 2, 3, 4, 6, 8, 12, 24 h), classify as 'Serial PK/PD profile'. "
            "If ONLY peak and trough are reported from the serial data, classify both separately.\n"
            "- Genre F (Perioperative): If samples are drawn after planned DOAC interruption before surgery, "
            "classify as 'Residual level after interruption / pre-procedural', NOT 'Random level'. "
            "Only classify as 'Random level' if timing is truly unrelated to any dosing schedule.\n"
            "- Genre E (Case reports): Narrative timing descriptions are valid if they specify when the sample "
            "was drawn relative to the last dose.\n\n"
            "═══════════════════════════════════════════════\n"
            "TIMING LEXICON (PHRASE-TO-CATEGORY MAPPING)\n"
            "═══════════════════════════════════════════════\n"
            "Use this lexicon to map phrases found in the paper to timing categories.\n\n"
            "MAP TO 'Trough level (just prior to next dose)':\n"
            "• predose, pre-dose\n"
            "• before administration, before next dose, just prior to next dose\n"
            "• Cmin, Ctrough, C_trough, trough concentration, trough level\n"
            "• residual level (ONLY when explicitly linked to next-dose timing in steady-state)\n"
            "• 24 hours after last intake (for once-daily DOACs)\n"
            "• 12 hours after last intake (for twice-daily DOACs, e.g., apixaban, dabigatran BID)\n"
            "• just before next scheduled dose\n"
            "• minimum concentration, nadir concentration\n"
            "• end-of-dosing-interval sample\n\n"
            "MAP TO 'Peak level (2-4 hours post-dose)':\n"
            "• post-dose (with explicit 2-4 hour window)\n"
            "• 2 to 4 hours after administration, 2-4 h post-dose\n"
            "• Tmax, Cmax, peak concentration, presumed Cmax\n"
            "• T1, T2, T3, T4 (ONLY if explicitly defined as Tmax window or 2-4 h post-dose)\n"
            "• maximum concentration\n"
            "• peak level\n\n"
            "MAP TO 'Residual level after interruption / pre-procedural':\n"
            "• residual level after temporary interruption\n"
            "• pre-procedural level, pre-operative level, pre-surgical level\n"
            "• level measured before surgery/procedure after DOAC interruption\n"
            "• level after dose withholding, level after planned drug cessation\n"
            "• just before surgery, just before procedure, just before ablation\n"
            "• sample taken after interruption of DOAC therapy\n"
            "• perioperative DOAC measurement after drug hold\n"
            "• residual anticoagulant activity prior to intervention\n"
            "NOTE: This category is for samples drawn after a PLANNED interruption of DOAC therapy "
            "before an elective or semi-urgent procedure. It differs from 'Trough' because the sample is "
            "NOT at steady-state next-dose timing but after an extended drug-free interval.\n\n"
            "MAP TO 'Serial PK/PD profile':\n"
            "• concentration-time profile, PK profile, pharmacokinetic profile\n"
            "• multiple timed samples, serial blood sampling\n"
            "• sampling at 0, 0.5, 1, 2, 3, 4, 6, 8, 12, 24 hours (or similar schedule)\n"
            "• Tmax/Tmin bins, time-concentration curve\n"
            "• AUC sampling, rich PK sampling, intensive sampling\n"
            "• dose-interval sampling with multiple time points\n"
            "NOTE: Use this when the study collected MULTIPLE timed samples to characterize the full "
            "concentration-time curve, NOT when only peak and/or trough were measured.\n\n"
            "MAP TO 'Random level':\n"
            "• routine-care sample, discarded sample, leftover sample\n"
            "• at presentation, at admission, at time of event\n"
            "• genuinely heterogeneous/unknown timing windows not binned by the study\n"
            "• clock-time-based sampling with NO linkage to last/next dose (e.g., 'samples from 8-10 am')\n"
            "• samples drawn according to immediate clinical need (emergency/urgent contexts)\n"
            "• timing described only as 'at time of visit' or 'at clinic appointment' with no dosing linkage\n\n"
            "MAP TO 'Timing not reported':\n"
            "• No explicit timing details in Methods, Results, figure/table captions, or PK sections\n"
            "• Only vague references like 'blood was collected' without timing context\n\n"
            "═══════════════════════════════════════════════\n"
            "CLASSIFICATION RULES\n"
            "═══════════════════════════════════════════════\n"
            "1) Extract timing ONLY from the sections listed in SECTION ROUTING above.\n"
            "2) Apply the TIMING LEXICON to map phrases to categories.\n"
            "3) Do NOT infer timing from DOAC class, manufacturer recommendations, or PK patterns.\n"
            "4) If a study collects samples at MULTIPLE timings (e.g., both peak and trough), "
            "select ALL applicable categories.\n"
            "5) If a study uses serial PK sampling AND also reports peak/trough from that data, "
            "select 'Serial PK/PD profile' (the broader category).\n"
            "6) For systematic reviews/meta-analyses, annotate timing only if the Methods/Results "
            "specifically describe timing categories for the included studies.\n\n"
            "CRITICAL DISTINCTION: RESIDUAL vs TROUGH vs RANDOM:\n"
            "• TROUGH = steady-state, regular dosing, sample just before the next scheduled dose.\n"
            "• RESIDUAL = sample after a planned interruption before a procedure (drug withheld for hours/days).\n"
            "• RANDOM = timing uncontrolled or dictated by urgent clinical events with no dosing-interval linkage.\n"
            "A paper that describes 'pre-procedural samples after DOAC interruption' is RESIDUAL, not random.\n"
            "A paper that describes 'samples drawn at emergency presentation' is RANDOM.\n"
            "A paper that describes 'predose samples at steady state' is TROUGH.\n\n"
            "COMMON ERROR MODES TO AVOID:\n"
            "• Omitting timing when it only appears in figure captions or PK subsections.\n"
            "• Labeling residual/pre-procedural samples as 'Random' when interruption was planned.\n"
            "• Collapsing serial PK schedules to 'Random' or leaving blank.\n"
            "• Failing to map Cmin/Ctrough/predose terms to 'Trough'.\n"
            "• Failing to map Cmax/Tmax/post-dose terms to 'Peak'.\n"
            "• Assigning 'Timing not reported' before checking figure/table captions and PK sections.\n\n"
            "OUTPUT:\n"
            "Return all applicable timing categories. If truly no timing information exists "
            "after searching all required sections, return ['Timing not reported']. "
            "Quote supporting phrases in the companion sentence field."
        ),
    )
    timing_of_measurement_sentence_from_text: Optional[List[str]] = Field(
        default=None,
        alias="Timing of DOAC Level Measurement Relative to DOAC Intake Sentence from Text",
        description="Exact sentences or paragraph containing the timing of DOAC level measurement relative to DOAC intake.",
    )
    timing_of_measurement_confidence_score: Optional[int] = Field(
        default=None,
        alias="Timing of DOAC Level Measurement Relative to DOAC Intake Confidence Score",
        description="Confidence score for the timing of DOAC level measurement relative to DOAC intake classification. How confident is the model in the classification? A number between 0 and 100, where 0 is the lowest confidence and 100 is the highest confidence.",
    )

    # A) thresholds the paper LISTS anywhere in its methods/results
    thresholds_listed: Optional[
        List[Literal["30 ng/mL", "50 ng/mL", "75 ng/mL", "100 ng/mL", "Other"]]
    ] = Field(
        default=None,
        alias="Reported DOAC concentration thresholds/cutoffs (listed)",
        description=(
            "STRICT INCLUSION: Only extract numeric DOAC concentration thresholds/cutoffs that are "
            "explicitly and unambiguously listed as thresholds for THIS study in the Methods or Results sections. "
            "Do NOT infer or assume the existence of a threshold based on background information, external references, figure axes, or general discussion.\n\n"
            "DEFINITION OF A THRESHOLD/CUTOFF:\n"
            "A threshold is a specific numeric DOAC concentration value (with units) that is used to:\n"
            "• Define groups or categories (e.g., 'patients with levels ≥30 ng/mL' vs '<30 ng/mL')\n"
            "• Determine eligibility or exclusion criteria (e.g., 'surgery proceeded if level <50 ng/mL')\n"
            "• Classify outcomes or risk (e.g., 'high exposure defined as >100 ng/mL')\n"
            "• Set decision points for analysis (e.g., 'we stratified by 30 ng/mL cutoff')\n"
            "• Define safety limits (e.g., 'thrombolysis withheld if level >50 ng/mL')\n\n"
            "Two-step process:\n"
            "Step 1 (Evidence): Directly quote exact sentences from the Methods/Results in which a specific numeric threshold is clearly defined or applied to this study's data, analysis, or procedures. "
            "Also check table legends, figure captions, and footnotes in Methods/Results sections.\n"
            "Step 2 (Decision): Only assign a threshold if you find such a quoted sentence containing an explicit numeric threshold with units (e.g., '30 ng/mL', '50 ng/mL') in the eligible sections.\n\n"
            "INCLUDE a threshold if and only if ALL of the following are TRUE:\n"
            "1) The numeric value AND units (e.g., 'ng/mL') are clearly stated in Methods/Results.\n"
            "2) The threshold is used to define eligibility, analysis groups, clinical actions, or results for THIS study.\n"
            "3) The sentence (or table/figure legend) is from the Methods or Results of THIS manuscript (not from Introduction, Discussion, supplementary, or background/references).\n"
            "4) The threshold is not merely a reference to an external guideline, prior study, or general literature. "
            "Apply only if the threshold is applied or explicitly discussed as relevant in THIS study context.\n\n"
            "KEY PHRASES THAT INDICATE A THRESHOLD:\n"
            "Look for phrases like:\n"
            "• 'threshold of [X] ng/mL', 'cutoff of [X] ng/mL', 'cut-off of [X] ng/mL'\n"
            "• 'levels ≥[X] ng/mL', 'levels >[X] ng/mL', 'levels <[X] ng/mL', 'levels ≤[X] ng/mL'\n"
            "• 'above [X] ng/mL', 'below [X] ng/mL', 'exceeding [X] ng/mL'\n"
            "• 'stratified by [X] ng/mL', 'grouped by [X] ng/mL', 'categorized by [X] ng/mL'\n"
            "• 'high exposure defined as >[X] ng/mL', 'low exposure defined as <[X] ng/mL'\n"
            "• 'safety threshold of [X] ng/mL', 'target level of [X] ng/mL'\n"
            "• 'ROC analysis identified [X] ng/mL as optimal cutoff'\n"
            "• 'patients with concentrations above/below [X] ng/mL'\n\n"
            "WHERE TO LOOK FOR THRESHOLDS:\n"
            "• Methods section: 'We defined high exposure as >100 ng/mL', 'Patients were stratified by 30 ng/mL cutoff'\n"
            "• Results section: 'ROC analysis identified 50 ng/mL as optimal threshold', 'Bleeding risk increased above 75 ng/mL'\n"
            "• Table legends/footnotes: 'Table 2. Outcomes stratified by DOAC level threshold (30 ng/mL)'\n"
            "• Figure captions: 'Figure 1. Kaplan-Meier curves for patients above and below 50 ng/mL threshold'\n"
            "• Statistical analysis descriptions: 'Multivariable analysis using 30 ng/mL as cutoff'\n\n"
            "THRESHOLD VALUES:\n"
            "• '30 ng/mL' - if the study explicitly lists 30 ng/mL as a threshold/cutoff\n"
            "• '50 ng/mL' - if the study explicitly lists 50 ng/mL as a threshold/cutoff\n"
            "• '75 ng/mL' - if the study explicitly lists 75 ng/mL as a threshold/cutoff\n"
            "• '100 ng/mL' - if the study explicitly lists 100 ng/mL as a threshold/cutoff\n"
            "• 'Other' - if a numeric threshold is applied in the study but is NOT exactly one of 30, 50, 75, or 100 ng/mL "
            "(e.g., 25 ng/mL, 40 ng/mL, 60 ng/mL, 80 ng/mL, 150 ng/mL, etc.)\n\n"
            "DO NOT INCLUDE (these are NOT thresholds):\n"
            "• Reference ranges or normal values (e.g., 'typical on-treatment levels range from 50-200 ng/mL')\n"
            "• Pharmacokinetic summary statistics (e.g., 'mean Cmax was 150 ng/mL', 'median trough was 45 ng/mL')\n"
            "• Individual patient values or case descriptions (e.g., 'Patient 1 had a level of 80 ng/mL')\n"
            "• Manufacturer-recommended ranges or product insert information\n"
            "• Values mentioned only in Introduction/Background as general knowledge\n"
            "• Values from external studies cited without application to THIS study\n"
            "• Figure axes or scales (unless explicitly labeled as thresholds in the legend)\n"
            "• Descriptive statistics without threshold context (e.g., 'levels ranged from 10 to 200 ng/mL')\n\n"
            "EXAMPLES OF WHAT TO INCLUDE:\n"
            "✓ 'We stratified patients by DOAC level using a 30 ng/mL cutoff' → Include '30 ng/mL'\n"
            "✓ 'Surgery was delayed if DOAC level exceeded 50 ng/mL' → Include '50 ng/mL'\n"
            "✓ 'ROC analysis identified 75 ng/mL as the optimal threshold for predicting bleeding' → Include '75 ng/mL'\n"
            "✓ 'High exposure was defined as concentrations >100 ng/mL' → Include '100 ng/mL'\n"
            "✓ 'Patients were grouped into <25 ng/mL and ≥25 ng/mL' → Include 'Other' (25 ng/mL is not in the list)\n\n"
            "EXAMPLES OF WHAT TO EXCLUDE:\n"
            "✗ 'Previous studies have used 30 ng/mL as a threshold' (mentioned in Introduction only) → Exclude\n"
            "✗ 'Mean DOAC level was 85 ng/mL' (descriptive statistic, not a threshold) → Exclude\n"
            "✗ 'DOAC levels ranged from 10 to 200 ng/mL' (range, not a threshold) → Exclude\n"
            "✗ 'The manufacturer recommends monitoring at levels above 150 ng/mL' (external reference) → Exclude\n"
            "✗ 'Figure 1 shows DOAC levels (x-axis: 0-200 ng/mL)' (axis scale, not a threshold) → Exclude\n\n"
            "Be conservative: If you are not certain a threshold was directly listed and used in this study's Methods/Results, LEAVE THIS FIELD NULL. "
            "Err on the side of under-reporting, not over-reporting. Only include thresholds that are explicitly defined or applied in THIS study."
        ),
    )
    thresholds_listed_confidence_score: Optional[int] = Field(
        default=None,
        alias="Reported DOAC concentration thresholds/cutoffs (listed) Confidence Score",
        description="Confidence score for the reported DOAC concentration thresholds/cutoffs (listed) classification. How confident is the model in the classification? A number between 0 and 100, where 0 is the lowest confidence and 100 is the highest confidence.",
    )

    # B) thresholds USED to inform CLINICAL MANAGEMENT, flattened as threshold × context
    thresholds_used_for_management: Optional[
        List[
            Literal[
                # 30
                "30 ng/mL – Overall",
                "30 ng/mL – Elective surgery",
                "30 ng/mL – Emergency surgery",
                "30 ng/mL – Major bleeding and anticoagulation reversal",
                "30 ng/mL – Thrombolysis/acute stroke",
                # 50
                "50 ng/mL – Overall",
                "50 ng/mL – Elective surgery",
                "50 ng/mL – Emergency surgery",
                "50 ng/mL – Major bleeding and anticoagulation reversal",
                "50 ng/mL – Thrombolysis/acute stroke",
                # 75
                "75 ng/mL – Overall",
                "75 ng/mL – Elective surgery",
                "75 ng/mL – Emergency surgery",
                "75 ng/mL – Major bleeding and anticoagulation reversal",
                "75 ng/mL – Thrombolysis/acute stroke",
                # 100
                "100 ng/mL – Overall",
                "100 ng/mL – Elective surgery",
                "100 ng/mL – Emergency surgery",
                "100 ng/mL – Major bleeding and anticoagulation reversal",
                "100 ng/mL – Thrombolysis/acute stroke",
            ]
        ]
    ] = Field(
        default=None,
        alias="Thresholds used to inform clinical management",
        description=(
            "CRITICAL: This field tracks thresholds used to GUIDE CLINICAL DECISIONS (management), NOT thresholds used "
            "to evaluate associations with clinical outcomes.\n\n"
            "KEY DISTINCTION:\n"
            "• Clinical MANAGEMENT = thresholds used to guide care decisions (surgery timing, reversal administration, thrombolysis eligibility, dose adjustment)\n"
            "• Clinical OUTCOMES = thresholds used to evaluate associations (bleeding risk, thrombosis risk, outcome prediction)\n"
            "• Analysis/Performance = thresholds used for statistical analysis (ROC cut-offs, sensitivity/specificity, stratification for analysis)\n\n"
            "Two-step process:\n"
            "Step 1 (Evidence): Quote exact sentences from Methods/Results that describe how the threshold was used "
            "to guide clinical decisions. Look for explicit action-oriented statements.\n"
            "Step 2 (Decision): Based ONLY on those quoted sentences, classify the threshold × context pair.\n\n"
            "KEY PHRASES THAT INDICATE MANAGEMENT USE:\n"
            "Look for action verbs and decision-making language:\n"
            "• 'Surgery was delayed/postponed if level >[X] ng/mL'\n"
            "• 'Surgery proceeded/was performed if level <[X] ng/mL'\n"
            "• 'Thrombolysis was withheld/contraindicated if level exceeded [X] ng/mL'\n"
            "• 'Thrombolysis was administered/allowed if level <[X] ng/mL'\n"
            "• 'Reversal was administered/given when level was >[X] ng/mL'\n"
            "• 'Dose was adjusted/reduced based on level >[X] ng/mL'\n"
            "• 'Patients with level <[X] ng/mL were cleared for surgery'\n"
            "• 'Level >[X] ng/mL was considered safe for thrombolysis'\n"
            "• 'Protocol required level <[X] ng/mL before proceeding'\n"
            "• 'Clinical decision was based on threshold of [X] ng/mL'\n\n"
            "INCLUDE a threshold × context pair ONLY if:\n"
            "1) The manuscript explicitly states the threshold was applied to guide clinical decisions "
            "   (surgery timing, reversal administration, thrombolysis eligibility, dose adjustment, etc.).\n"
            "2) The threshold was used in actual clinical decision-making, not just for analysis/performance evaluation.\n"
            "3) The statement appears in Methods (describing the protocol) or Results (describing what was done).\n\n"
            "DO NOT INCLUDE (these are NOT management decisions):\n"
            "• Analysis/Performance: 'ROC analysis identified [X] ng/mL as optimal cutoff' → This is for analysis, not management\n"
            "• Outcome Associations: 'Bleeding risk was higher at levels >100 ng/mL' → This evaluates outcomes, not guides decisions\n"
            "• Stratification for Analysis: 'Patients were stratified by [X] ng/mL for statistical analysis' → This is analysis, not management\n"
            "• Descriptive: 'Mean level in bleeding group was 120 ng/mL' → This describes outcomes, not guides decisions\n"
            "• Hypothetical: 'Levels >50 ng/mL might require reversal' (without evidence it was actually used) → Not actually applied\n"
            "• Background Only: 'Previous studies used [X] ng/mL as threshold' (mentioned in Introduction only) → Not used in THIS study\n\n"
            "CONTEXT CATEGORIES WITH EXAMPLES:\n\n"
            "1) 'Overall' - General clinical management without specific context:\n"
            "   Examples:\n"
            "   • 'DOAC level >30 ng/mL was considered high and required clinical intervention'\n"
            "   • 'Levels <50 ng/mL were considered safe for general procedures'\n"
            "   • 'Clinical management was guided by threshold of 75 ng/mL'\n"
            "   • Generic statements about using thresholds for clinical decision-making without specifying surgery/reversal/thrombolysis\n\n"
            "2) 'Elective surgery' - Threshold used to guide timing/clearance for planned procedures:\n"
            "   Examples:\n"
            "   • 'Elective surgery was delayed if DOAC level >30 ng/mL'\n"
            "   • 'Patients with level <50 ng/mL were cleared for elective procedures'\n"
            "   • 'Pre-operative DOAC level <30 ng/mL was required before scheduled surgery'\n"
            "   • 'Elective surgery protocol required level <50 ng/mL'\n"
            "   Keywords: elective, planned, scheduled, pre-operative, pre-procedural\n\n"
            "3) 'Emergency surgery' - Threshold used to guide proceed/cancel decisions for urgent procedures:\n"
            "   Examples:\n"
            "   • 'Emergency surgery proceeded if level <50 ng/mL'\n"
            "   • 'Urgent surgery was delayed if level exceeded 30 ng/mL'\n"
            "   • 'Trauma surgery was performed when level <75 ng/mL'\n"
            "   • 'Emergency procedure protocol used 50 ng/mL threshold'\n"
            "   Keywords: emergency, urgent, emergent, trauma, unplanned, acute surgery\n\n"
            "4) 'Major bleeding and anticoagulation reversal' - Threshold used to guide reversal administration:\n"
            "   Examples:\n"
            "   • 'Reversal was administered when DOAC level >30 ng/mL'\n"
            "   • 'Andexanet alfa was given if level exceeded 50 ng/mL'\n"
            "   • 'Reversal protocol required level >30 ng/mL in setting of major bleeding'\n"
            "   • 'Idarucizumab was administered when dabigatran level >50 ng/mL'\n"
            "   Keywords: reversal, antidote, andexanet, idarucizumab, PCC, aPCC, major bleeding, hemorrhage\n\n"
            "5) 'Thrombolysis/acute stroke' - Threshold used to determine lytic eligibility:\n"
            "   Examples:\n"
            "   • 'Thrombolysis was withheld if DOAC level >50 ng/mL'\n"
            "   • 'Alteplase was administered if level <30 ng/mL'\n"
            "   • 'Thrombolysis eligibility required level <50 ng/mL'\n"
            "   • 'Acute stroke protocol used 30 ng/mL threshold for lytic administration'\n"
            "   Keywords: thrombolysis, alteplase, tenecteplase, rtPA, tPA, acute stroke, lytic, lysis\n\n"
            "EXAMPLES OF WHAT TO INCLUDE:\n"
            "✓ 'Surgery was delayed if level >30 ng/mL' → Include '30 ng/mL – Elective surgery' (if elective) or 'Emergency surgery' (if emergency)\n"
            "✓ 'Thrombolysis was withheld if level exceeded 50 ng/mL' → Include '50 ng/mL – Thrombolysis/acute stroke'\n"
            "✓ 'Reversal was administered when level was >30 ng/mL' → Include '30 ng/mL – Major bleeding and anticoagulation reversal'\n"
            "✓ 'Clinical protocol required level <50 ng/mL before any invasive procedure' → Include '50 ng/mL – Overall'\n\n"
            "EXAMPLES OF WHAT TO EXCLUDE:\n"
            "✗ 'ROC analysis identified 50 ng/mL as optimal threshold' → Exclude (analysis, not management)\n"
            "✗ 'Bleeding risk was higher at levels >100 ng/mL' → Exclude (outcome association, not management)\n"
            "✗ 'Patients were stratified by 30 ng/mL for statistical analysis' → Exclude (analysis, not management)\n"
            "✗ 'Previous studies used 50 ng/mL as threshold for surgery' → Exclude (background, not used in THIS study)\n\n"
            "If the article does not clearly state that thresholds were used to inform clinical management, leave null. Do NOT guess. "
            "Only include thresholds that explicitly guided clinical decisions in THIS study."
        ),
    )
    thresholds_used_for_management_sentence_from_text: Optional[List[str]] = Field(
        default=None,
        alias="Thresholds used to inform clinical management Sentence from Text",
        description="Exact sentences or paragraph confirming that the thresholds were used to inform clinical management.",
    )
    thresholds_used_for_management_confidence_score: Optional[int] = Field(
        default=None,
        alias="Thresholds used to inform clinical management Confidence Score",
        description="Confidence score for the thresholds used to inform clinical management classification. How confident is the model in the classification? A number between 0 and 100, where 0 is the lowest confidence and 100 is the highest confidence.",
    )

    # Turnaround Time
    turnaround_time: Optional[str] = Field(
        default=None,
        alias="Reported turnaround time",
        description=(
            "Include ONLY if THIS manuscript explicitly reports a study-defined turnaround time for DOAC "
            "level reporting (e.g., time from sample receipt at laboratory → result availability). "
            "Record the verbatim value (minutes / hours / days).\n\n"
            "Important distinctions:\n"
            "• TRUE clinical turnaround time = same-day actionable reporting (typically minutes to hours; e.g. 30–90 min).\n"
            "• Research / batch processing turnaround = results returned ≥1 day (e.g., 1–7 days; mailed/central lab processing).\n\n"
            "Do NOT infer. Do NOT convert. Use the exact phrase/number from the Methods/Results. "
            "If multiple turnaround times are reported (e.g., DOAC vs coagulation tests), record the DOAC turnaround only."
        ),
    )

    # Clinical Outcomes Measured?
    clinical_outcomes_measured: Optional[Literal["Yes", "No"]] = Field(
        default=None,
        alias="Clinical outcomes measured?",
        description=(
            "CRITICAL GATE for ALL clinical outcome fields. This field controls whether ANY outcome-related fields should be populated.\n\n"
            "DEFINITION OF CLINICAL OUTCOMES:\n"
            "Clinical outcomes are actual clinical events that occurred during the study period, including:\n"
            "• Bleeding events (major bleeding, clinically relevant non-major bleeding, intracranial hemorrhage, GI bleeding, etc.)\n"
            "• Thromboembolic events (stroke, TIA, DVT, PE, systemic embolism, myocardial infarction, etc.)\n"
            "• Mortality (all-cause, cardiovascular, fatal bleeding)\n"
            "• Other clinical events (hospitalization, emergency department visits, etc.)\n\n"
            "NOT considered clinical outcomes:\n"
            "• Laboratory values (DOAC levels, coagulation tests, etc.) - these are measurements, not outcomes\n"
            "• Baseline characteristics or risk factors\n"
            "• Pharmacokinetic parameters (Cmax, AUC, etc.)\n"
            "• Assay performance metrics (sensitivity, specificity, etc.)\n"
            "• Adverse events without clinical significance (e.g., minor lab abnormalities)\n\n"
            "Two-step process:\n"
            "Step 1 (Evidence): Search Methods and Results sections ONLY (NOT Introduction, Abstract, or Discussion). "
            "Quote exact sentences that state the study recorded/assessed/evaluated clinical events.\n"
            "Step 2 (Decision): Based ONLY on those quoted sentences, classify as 'Yes' or 'No'.\n\n"
            "SET TO 'YES' ONLY IF BOTH CONDITIONS ARE MET:\n\n"
            "Condition 1: Methods explicitly state that clinical events were recorded/assessed/evaluated as outcomes.\n"
            "Look for phrases like:\n"
            "• 'we recorded', 'we assessed', 'we evaluated', 'we monitored'\n"
            "• 'primary endpoint', 'secondary endpoint', 'primary outcome', 'secondary outcome'\n"
            "• 'outcomes included', 'outcomes were', 'we defined events as...'\n"
            "• 'bleeding events were recorded', 'thrombotic events were assessed'\n"
            "• 'follow-up for clinical events', 'patients were followed for [outcome]'\n"
            "• 'adjudication of outcomes', 'outcome assessment', 'event ascertainment'\n\n"
            "Condition 2: Results section reports actual clinical events OR explicitly states 'no events occurred'.\n"
            "Look for:\n"
            "• Actual event counts (e.g., '5 major bleeding events occurred', '2 strokes were observed')\n"
            "• Event rates or percentages (e.g., 'bleeding rate was 3.2%', 'no thrombotic events occurred')\n"
            "• Explicit statements of zero events (e.g., 'no bleeding events', 'no thrombotic complications')\n"
            "• Tables or figures showing clinical events\n"
            "• Time-to-event analyses (e.g., 'Kaplan-Meier curves for bleeding events')\n\n"
            "EXAMPLES OF 'YES' SCENARIOS:\n"
            "✓ Methods: 'We recorded major bleeding events according to ISTH criteria.' "
            "Results: 'Three major bleeding events occurred during follow-up.' → YES\n"
            "✓ Methods: 'Primary endpoint was stroke or systemic embolism.' "
            "Results: 'No stroke or systemic embolism events occurred.' → YES (explicit zero events)\n"
            "✓ Methods: 'Patients were followed for 6 months for bleeding and thrombosis.' "
            "Results: 'Bleeding events occurred in 5 patients (2.1%).' → YES\n"
            "✓ Methods: 'We assessed clinical outcomes including major bleeding and stroke.' "
            "Results: 'Table 2 shows clinical outcomes. Major bleeding: 3 events.' → YES\n\n"
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
            "EXAMPLES OF 'NO' SCENARIOS:\n"
            "✗ Methods: 'DOAC levels were measured.' Results: 'Mean DOAC level was 85 ng/mL.' "
            "  (No mention of clinical events) → NO\n"
            "✗ Introduction: 'DOACs reduce stroke risk in AF.' Methods: 'We measured DOAC levels.' "
            "  Results: 'DOAC levels ranged from 10-200 ng/mL.' (No outcomes measured) → NO\n"
            "✗ Methods: 'Patients will be followed for bleeding events.' "
            "  Results: 'Baseline characteristics are shown in Table 1.' (No events reported) → NO\n"
            "✗ Methods: 'We evaluated DOAC level variability.' "
            "  Results: 'Coefficient of variation was 45%.' (No clinical events) → NO\n"
            "✗ Methods: 'We assessed correlation between DOAC levels and PT.' "
            "  Results: 'Spearman correlation was 0.65.' (No clinical outcomes) → NO\n\n"
            "EDGE CASES:\n"
            "• If Methods describe outcome measurement but Results only show baseline data with no events reported "
            "  and no explicit 'no events occurred' statement → Set to 'No' (outcomes were planned but not actually measured/reported)\n"
            "• If Results mention 'outcomes' but they refer to laboratory outcomes (e.g., 'DOAC level outcomes') "
            "  rather than clinical events → Set to 'No'\n"
            "• If the study is a case report/series describing clinical events that occurred (not measured prospectively), "
            "  but Methods/Results describe these events → Set to 'Yes'\n"
            "• If Results state 'no events occurred' or 'zero events' explicitly → Set to 'Yes' "
            "  (outcomes were measured, result was zero)\n\n"
            "CONSISTENCY RULE:\n"
            "If this field = 'No', then ALL outcome-related fields MUST be null:\n"
            "• clinical_outcomes → null\n"
            "• clinical_outcome_followup_flat → null\n"
            "• clinical_outcome_definition_flat → null\n\n"
            "If this field = 'Yes', then at least one outcome-related field should be populated.\n\n"
            "If unclear after checking Methods and Results, set to null and leave all outcome-related fields null. "
            "Be conservative: only set to 'Yes' if there is clear evidence that clinical events were actually measured and reported."
        ),
    )
    clinical_outcomes_measured_confidence_score: Optional[int] = Field(
        default=None,
        alias="Clinical Outcomes Measured Confidence Score",
        description="Confidence score for the clinical outcomes measured classification. How confident is the model in the classification? A number between 0 and 100, where 0 is the lowest confidence and 100 is the highest confidence.",
    )

    # Clinical Outcomes
    clinical_outcomes: Optional[
        List[
            Literal[
                "Bleeding/Hemostasis",
                "Thromboembolism",
                "Stroke/Transient Ischemic Attack (TIA)",
                "Pulmonary embolism (PE)",
                "Deep venous thrombosis (DVT)",
            ]
        ]
    ] = Field(
        default=None,
        alias="Clinical Outcomes",
        description=(
            "CRITICAL: Only populate if 'Clinical outcomes measured?' = 'Yes'. "
            "If 'Clinical outcomes measured?' = 'No', this field MUST be null.\n\n"
            "Two-step process:\n"
            "Step 1 (Evidence): Quote exact sentences from Methods AND Results (NOT Introduction/Discussion) "
            "that describe the outcome being measured and reported.\n"
            "Step 2 (Decision): Based ONLY on those quoted sentences, classify the outcome type(s). "
            "You may select multiple outcomes if the study measured more than one type.\n\n"
            "INCLUDE an outcome ONLY if:\n"
            "1) The Methods explicitly states it was recorded/assessed/evaluated as an outcome.\n"
            "2) The Results section reports actual events OR explicitly states 'no events occurred'. "
            "   Focus more on the Results section than the Methods section.\n\n"
            "OUTCOME CATEGORIES WITH KEYWORDS AND EXAMPLES:\n\n"
            "1) 'Bleeding/Hemostasis':\n"
            "   Keywords to look for:\n"
            "   • Major bleeding, clinically relevant non-major bleeding (CRNMB), minor bleeding\n"
            "   • Intracranial hemorrhage (ICH), gastrointestinal (GI) bleeding, retroperitoneal bleeding\n"
            "   • Fatal bleeding, life-threatening bleeding, severe bleeding\n"
            "   • Bleeding events, hemorrhagic events, bleeding complications\n"
            "   • ISTH major bleeding, BARC bleeding, TIMI bleeding, GUSTO bleeding\n"
            "   • Hemorrhage, hemostasis, bleeding episodes\n\n"
            "   Examples of what to include:\n"
            "   ✓ 'Major bleeding events were recorded according to ISTH criteria. Three major bleeding events occurred.'\n"
            "   ✓ 'Bleeding outcomes: 5 GI bleeds, 2 intracranial hemorrhages'\n"
            "   ✓ 'No major bleeding events occurred during follow-up'\n\n"
            "2) 'Thromboembolism':\n"
            "   Keywords to look for:\n"
            "   • Thromboembolism, thromboembolic events, thrombotic events\n"
            "   • Arterial thromboembolism (ATE), venous thromboembolism (VTE)\n"
            "   • Systemic embolism, peripheral embolism\n"
            "   • Recurrent thrombosis, thrombotic complications\n"
            "   • Myocardial infarction (MI), acute coronary syndrome\n\n"
            "   Examples of what to include:\n"
            "   ✓ 'Thromboembolic events were assessed. Two systemic embolisms occurred.'\n"
            "   ✓ 'Primary endpoint was thromboembolism. No events occurred.'\n"
            "   ✓ 'VTE events: 3 DVT, 2 PE'\n\n"
            "3) 'Stroke/Transient Ischemic Attack (TIA)':\n"
            "   Keywords to look for:\n"
            "   • Stroke, ischemic stroke, hemorrhagic stroke\n"
            "   • Transient ischemic attack, TIA\n"
            "   • Cerebrovascular accident (CVA)\n"
            "   • Stroke events, stroke outcomes\n\n"
            "   Examples of what to include:\n"
            "   ✓ 'Stroke and TIA were primary outcomes. Four strokes and two TIAs occurred.'\n"
            "   ✓ 'Cerebrovascular events: 3 ischemic strokes, 1 hemorrhagic stroke'\n"
            "   ✓ 'No stroke or TIA events occurred'\n\n"
            "4) 'Pulmonary embolism (PE)':\n"
            "   Keywords to look for:\n"
            "   • Pulmonary embolism, PE\n"
            "   • Acute PE, recurrent PE\n"
            "   • PE events, PE outcomes\n\n"
            "   Examples of what to include:\n"
            "   ✓ 'Pulmonary embolism was assessed. Two PE events occurred.'\n"
            "   ✓ 'VTE outcomes included PE. One PE was diagnosed.'\n"
            "   ✓ 'No pulmonary embolism events occurred'\n\n"
            "5) 'Deep venous thrombosis (DVT)':\n"
            "   Keywords to look for:\n"
            "   • Deep venous thrombosis, DVT\n"
            "   • Deep vein thrombosis\n"
            "   • DVT events, DVT outcomes\n"
            "   • Lower extremity DVT, upper extremity DVT\n\n"
            "   Examples of what to include:\n"
            "   ✓ 'DVT was evaluated. Three DVT events occurred.'\n"
            "   ✓ 'VTE outcomes: 2 DVT, 1 PE'\n"
            "   ✓ 'No DVT events were observed'\n\n"
            "CLASSIFICATION GUIDANCE:\n"
            "• If the study reports 'VTE' or 'venous thromboembolism' without specifying PE vs DVT, "
            "  you may need to check if they report both separately or as a combined outcome.\n"
            "• If 'stroke' and 'TIA' are reported separately, include 'Stroke/Transient Ischemic Attack (TIA)'.\n"
            "• If 'bleeding' is reported with subtypes (major, minor, etc.), include 'Bleeding/Hemostasis'.\n"
            "• If 'thromboembolism' is reported as a general category, include 'Thromboembolism'.\n\n"
            "DO NOT INCLUDE outcomes if:\n"
            "• They appear only in Introduction/Background (e.g., 'AF is associated with increased stroke risk') "
            "  without evidence of measurement in THIS study\n"
            "• They are from an underlying registry or external trial, not THIS study\n"
            "• Only baseline descriptions or planned follow-up are mentioned without actual events in Results\n"
            "• Generic risk statements exist without explicit outcome measurement\n"
            "• Only laboratory values are reported (e.g., 'bleeding time' as a lab test, not clinical bleeding events)\n"
            "• Only imaging findings without clinical events (e.g., 'asymptomatic DVT on screening ultrasound' "
            "  may or may not count - check if it's reported as a clinical outcome)\n\n"
            "EXAMPLES OF WHAT TO INCLUDE:\n"
            "✓ Methods: 'We recorded major bleeding events.' Results: 'Three major bleeding events occurred.' "
            "  → Include 'Bleeding/Hemostasis'\n"
            "✓ Methods: 'Primary endpoint was stroke or systemic embolism.' Results: 'Two strokes occurred.' "
            "  → Include 'Stroke/Transient Ischemic Attack (TIA)' and 'Thromboembolism'\n"
            "✓ Methods: 'VTE events (DVT and PE) were assessed.' Results: 'Table 3 shows VTE outcomes: 2 DVT, 1 PE.' "
            "  → Include 'Pulmonary embolism (PE)' and 'Deep venous thrombosis (DVT)'\n"
            "✓ Methods: 'Bleeding and thrombotic events were recorded.' Results: 'No events occurred.' "
            "  → Include 'Bleeding/Hemostasis' and 'Thromboembolism'\n\n"
            "EXAMPLES OF WHAT TO EXCLUDE:\n"
            "✗ Introduction: 'DOACs reduce stroke risk.' Methods: 'We measured DOAC levels.' "
            "  Results: 'Mean level was 85 ng/mL.' → Exclude (no outcomes measured)\n"
            "✗ Methods: 'Patients will be followed for bleeding.' Results: 'Baseline characteristics shown.' "
            "  → Exclude (no events reported, only planned)\n"
            "✗ Methods: 'We assessed bleeding time (laboratory test).' Results: 'Mean bleeding time was 5 minutes.' "
            "  → Exclude (laboratory test, not clinical bleeding event)\n\n"
            "If no clinical outcomes were measured (gate = 'No'), leave this field null. "
            "If multiple outcomes were measured, select all applicable categories."
        ),
    )
    clinical_outcomes_sentence_from_text: Optional[List[str]] = Field(
        default=None,
        alias="Clinical Outcomes Sentence from Text",
        description="Exact sentences or paragraph confirming that the outcome(s) were measured and reported in this study.",
    )

    # ---- Per-outcome follow-up duration (verbatim) ----
    clinical_outcome_followup_flat: Optional[
        List[
            Literal[
                # Bleeding / Hemostasis
                "Bleeding/Hemostasis – ≤1 month",
                "Bleeding/Hemostasis – 1 month to ≤3 months",
                "Bleeding/Hemostasis – >3 months to ≤6 months",
                "Bleeding/Hemostasis – >6 months to ≤1 year",
                "Bleeding/Hemostasis – >1 year",
                # Thromboembolism – Stroke/TIA
                "Thromboembolism – Stroke/TIA – ≤1 month",
                "Thromboembolism – Stroke/TIA – 1 month to ≤3 months",
                "Thromboembolism – Stroke/TIA – >3 months to ≤6 months",
                "Thromboembolism – Stroke/TIA – >6 months to ≤1 year",
                "Thromboembolism – Stroke/TIA – >1 year",
                # Thromboembolism – PE/DVT
                "Thromboembolism – PE/DVT – ≤1 month",
                "Thromboembolism – PE/DVT – 1 month to ≤3 months",
                "Thromboembolism – PE/DVT – >3 months to ≤6 months",
                "Thromboembolism – PE/DVT – >6 months to ≤1 year",
                "Thromboembolism – PE/DVT – >1 year",
            ]
        ]
    ] = Field(
        default=None,
        alias="Clinical Outcome - follow-up duration",
        description=(
            "CRITICAL: Only populate if 'Clinical outcomes measured?' = 'Yes'. "
            "If 'Clinical outcomes measured?' = 'No', this field MUST be null.\n\n"
            "This field captures the follow-up duration for each clinical outcome that was measured. "
            "Follow-up duration is the time period during which clinical events were actively monitored and recorded.\n\n"
            "Two-step process:\n"
            "Step 1 (Evidence): Quote exact sentences from Methods AND Results (NOT Introduction/Discussion) "
            "that explicitly describe how long patients were followed for clinical events.\n"
            "Step 2 (Decision): Based ONLY on those quoted sentences, classify the follow-up duration for each outcome type.\n\n"
            "KEY PHRASES TO LOOK FOR:\n"
            "• 'Patients were followed for [X]...' (e.g., 'Patients were followed for 6 months')\n"
            "• 'Follow-up period was [X]...' (e.g., 'Follow-up period was 30 days')\n"
            "• 'Observation period of [X]...' (e.g., 'Observation period of 3 months')\n"
            "• 'Outcomes were assessed at [X]...' (e.g., 'Outcomes were assessed at 1 year')\n"
            "• 'Follow-up duration of [X]...' (e.g., 'Follow-up duration of 12 months')\n"
            "• 'Median follow-up was [X]...' (e.g., 'Median follow-up was 8.5 months')\n"
            "• 'Mean follow-up was [X]...' (e.g., 'Mean follow-up was 6.2 months')\n"
            "• 'Patients were monitored for [X]...' (e.g., 'Patients were monitored for 90 days')\n"
            "• 'Study duration was [X]...' (e.g., 'Study duration was 1 year')\n"
            "• 'Events were recorded during [X]...' (e.g., 'Events were recorded during 6-month follow-up')\n\n"
            "DURATION CATEGORIES:\n"
            "Map the reported duration to the closest category:\n"
            "• '≤1 month' = up to 1 month (e.g., 7 days, 2 weeks, 30 days, 1 month)\n"
            "• '1 month to ≤3 months' = more than 1 month up to 3 months (e.g., 6 weeks, 2 months, 90 days, 3 months)\n"
            "• '>3 months to ≤6 months' = more than 3 months up to 6 months (e.g., 4 months, 5 months, 180 days, 6 months)\n"
            "• '>6 months to ≤1 year' = more than 6 months up to 1 year (e.g., 9 months, 12 months, 1 year, 365 days)\n"
            "• '>1 year' = more than 1 year (e.g., 18 months, 2 years, 24 months, 730 days)\n\n"
            "INCLUDE a follow-up duration ONLY if:\n"
            "1) The outcome was explicitly measured (see 'Clinical outcomes' field).\n"
            "2) There is an explicit description of follow-up duration in Methods or Results.\n"
            "3) The duration is clearly linked to outcome ascertainment (not just general study duration).\n\n"
            "HANDLING DIFFERENT DURATIONS:\n"
            "• If all outcomes have the same follow-up duration: Select one duration for each outcome type.\n"
            "• If different outcomes have different durations: Select the appropriate duration for each outcome type separately.\n"
            "  Example: 'Bleeding events were assessed at 30 days, while thrombotic events were assessed at 6 months.'\n"
            "  → Include 'Bleeding/Hemostasis – ≤1 month' and 'Thromboembolism – >3 months to ≤6 months'\n"
            "• If only one overall follow-up duration is reported: Apply that duration to all outcomes measured.\n"
            "• If median/mean follow-up is reported: Use that value to classify (e.g., 'median follow-up 8.5 months' → '>6 months to ≤1 year')\n\n"
            "EXAMPLES OF WHAT TO INCLUDE:\n"
            "✓ 'Patients were followed for 6 months for bleeding and thrombotic events.' "
            "  Outcomes: Bleeding/Hemostasis, Thromboembolism → Include 'Bleeding/Hemostasis – >3 months to ≤6 months' "
            "  and 'Thromboembolism – >3 months to ≤6 months'\n"
            "✓ 'Follow-up period was 30 days. Major bleeding events were recorded.' "
            "  → Include 'Bleeding/Hemostasis – ≤1 month'\n"
            "✓ 'Stroke outcomes were assessed at 1 year, while bleeding was assessed at 3 months.' "
            "  → Include 'Thromboembolism – Stroke/TIA – >6 months to ≤1 year' and 'Bleeding/Hemostasis – 1 month to ≤3 months'\n"
            "✓ 'Median follow-up was 8.5 months. VTE events (DVT and PE) were recorded.' "
            "  → Include 'Thromboembolism – PE/DVT – >6 months to ≤1 year'\n\n"
            "DO NOT INCLUDE follow-up duration if:\n"
            "• The study mentions imaging or days of observation but does NOT explicitly state follow-up for clinical events.\n"
            "• Follow-up is inferred from a different cohort (e.g., underlying registry) rather than THIS study.\n"
            "• Only baseline characteristics or planned follow-up are mentioned without explicit duration for outcome ascertainment.\n"
            "• The duration is mentioned in Introduction/Discussion but not in Methods/Results.\n"
            "• Only hospital stay or procedure duration is mentioned (e.g., 'patients were observed for 24 hours post-procedure' "
            "  without explicit outcome follow-up)\n"
            "• Duration is vague or unclear (e.g., 'long-term follow-up' without specific time period)\n\n"
            "EXAMPLES OF WHAT TO EXCLUDE:\n"
            "✗ 'Patients were followed for DOAC level measurement.' (No mention of outcome follow-up duration) → Exclude\n"
            "✗ 'Study duration was 1 year, but outcomes were not systematically assessed.' → Exclude\n"
            "✗ 'Previous studies followed patients for 6 months.' (Background only, not THIS study) → Exclude\n"
            "✗ 'Patients were observed in the hospital for 48 hours.' (Hospital stay, not outcome follow-up) → Exclude\n"
            "✗ 'Long-term outcomes were assessed.' (Vague, no specific duration) → Exclude\n\n"
            "EDGE CASES:\n"
            "• If follow-up is reported as a range (e.g., '3-6 months'), use the upper bound (→ '>3 months to ≤6 months').\n"
            "• If follow-up is reported in days, convert to months: 30 days = 1 month, 90 days = 3 months, 180 days = 6 months, 365 days = 1 year.\n"
            "• If follow-up is reported as 'up to [X]', use that value (e.g., 'up to 1 year' → '>6 months to ≤1 year').\n"
            "• If multiple follow-up timepoints are reported (e.g., 'assessed at 30 days, 3 months, and 1 year'), "
            "  use the longest duration for which outcomes were assessed.\n"
            "• If 'ongoing follow-up' or 'follow-up continues' is mentioned, look for the maximum reported duration or latest assessment timepoint.\n\n"
            "If duration is not explicitly reported for an outcome, do NOT select any value for that outcome. "
            "If multiple outcomes have different durations, include multiple literals. "
            "Do NOT infer, map, or approximate. ONLY assign when the study directly reports both outcome measurement AND explicit follow-up duration."
        ),
    )
    clinical_outcome_followup_sentence_from_text: Optional[List[str]] = Field(
        default=None,
        alias="Clinical Outcome - follow-up duration Sentence from Text",
        description="Exact sentences or paragraph containing the clinical outcome follow-up duration.",
    )

    # ---- Per-outcome definition notes (verbatim) ----
    clinical_outcome_definition_flat: Optional[
        List[
            Literal[
                # Bleeding / Hemostasis
                "Bleeding/Hemostasis – ISTH Major Bleeding (General Definition)",
                "Bleeding/Hemostasis – ISTH Major Bleeding (Surgical Studies)",
                "Bleeding/Hemostasis – ISTH Clinically Relevant Non-Major Bleeding (CRNMB)",
                "Bleeding/Hemostasis – BARC",
                "Bleeding/Hemostasis – TIMI",
                "Bleeding/Hemostasis – GUSTO",
                "Bleeding/Hemostasis – WHO",
                "Bleeding/Hemostasis – EORTC",
                "Bleeding/Hemostasis – CRUSADE",
                "Bleeding/Hemostasis – ACUITY/HORIZONS",
                "Bleeding/Hemostasis – Other definition",
                "Bleeding/Hemostasis – Not defined/not described",
                # Stroke / TIA
                "Thromboembolism – Stroke/TIA – Defined",
                "Thromboembolism – Stroke/TIA – Not defined/not described",
                # PE / DVT
                "Thromboembolism – PE/DVT – Defined",
                "Thromboembolism – PE/DVT – Not defined/not described",
            ]
        ]
    ] = Field(
        default=None,
        alias="Clinical Outcome - definition",
        description=(
            "CRITICAL: Only populate if 'Clinical outcomes measured?' = 'Yes'. "
            "If 'Clinical outcomes measured?' = 'No', this field MUST be null.\n\n"
            "Two-step process:\n"
            "Step 1 (Evidence): Quote exact sentences from Methods (NOT Introduction/Discussion) "
            "that explicitly define the outcome. Look for phrases like 'Major bleeding was defined as...', "
            "'Stroke was defined as...', 'We used the ISTH definition...', 'Outcomes were adjudicated according to...'.\n"
            "Step 2 (Decision): Based ONLY on those quoted sentences, classify the definition.\n\n"
            "Include an outcome definition ONLY if:\n"
            "1) The outcome was explicitly measured (see 'Clinical outcomes' field).\n"
            "2) The paper gives at least one sentence beginning with explicit definition language "
            "   (e.g., 'Major bleeding was defined as...', 'Stroke was defined as...', "
            "   'We used the [ISTH/BARC/TIMI/etc.] definition...').\n\n"
            "For Bleeding/Hemostasis: Pick the exact definition taxonomy used (ISTH, BARC, TIMI, etc.). "
            "If a specific taxonomy is cited but not detailed, select that taxonomy. "
            "If no taxonomy is cited and no explicit definition is given, select 'Not defined/not described'.\n\n"
            "For Stroke/TIA and PE/DVT: Choose 'Defined' only if the study clearly cites:\n"
            "• Objective clinical criteria (e.g., NIHSS, modified Rankin Scale).\n"
            "• Imaging criteria (e.g., CT/MRI findings).\n"
            "• Formal guideline/adjudication standard (e.g., WHO, TOAST classification).\n"
            "If no explicit criteria or standard is cited, select 'Not defined/not described'.\n\n"
            "Do NOT assign any value if:\n"
            "• The outcome was only mentioned narratively in Background/Introduction AND not measured in Results.\n"
            "• The study reported the outcome but did not provide ANY definition or diagnostic criteria.\n"
            "• Definitions are mentioned in Discussion but not in Methods.\n"
            "• The study infers follow-up or definitions where the study doesn't actually define outcomes.\n\n"
            "Multiple selections allowed if multiple outcome domains in THIS study each have explicit definitions."
        ),
    )
    clinical_outcome_definition_sentence_from_text: Optional[List[str]] = Field(
        default=None,
        alias="Clinical Outcome - definition Sentence from Text",
        description="Exact sentences or paragraph confirming that the outcome(s) were measured and reported in this study.",
    )

    model_config = ConfigDict(populate_by_name=True)
