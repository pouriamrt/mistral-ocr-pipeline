from typing import List, Optional, Literal, Type
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


def df_cols_from_model(model_cls: Type[BaseModel], use_alias: bool = True) -> List[str]:
    cols = []
    for name, field in model_cls.model_fields.items():
        col = field.alias if use_alias and getattr(field, "alias", None) else name
        cols.append(col)
    return cols


def df_cols_from_models(use_alias: bool = True) -> List[str]:
    models = [
        ExtractionMetaDesign,
        ExtractionPopulationIndications,
        ExtractionMethods,
        ExtractionOutcomes,
        ExtractionDiagnosticPerformance,
    ]
    seen, out = set(), []
    for cls in models:
        for col in df_cols_from_model(cls, use_alias=use_alias):
            if col not in seen:
                seen.add(col)
                out.append(col)
    return out


class ImageType(str, Enum):
    GRAPH = "graph"
    TEXT = "text"
    TABLE = "table"
    IMAGE = "image"


class Image(BaseModel):
    image_type: ImageType = Field(
        ...,
        description="The type of the image. Must be one of 'graph', 'text', 'table' or 'image'.",
    )
    description: str = Field(..., description="A description of the image.")


# -------------------------------
# 1) Bibliography & Study Design
# -------------------------------
class ExtractionMetaDesign(BaseModel):
    """
    Guidelines:
    1) Do not infer or guess.
    2) Use null if unsure.
    3) Output only facts explicitly in the PDF.
    4) If ambiguous, set null (do not guess).
    5) Numeric values must be exact.
    6) Resolve conflicts by the clearest statement (title→early pages; patients→methods/results).
    7) IGNORE external knowledge.
    8) Ignore Introduction/Background, References and Acknowledgments content.
    9) Focus on Methods and Results and Abstract sections.
    """

    # Journal & author info
    journal: Optional[str] = Field(
        default=None, alias="Journal", description="Single journal/publication name."
    )
    title: Optional[str] = Field(
        default=None, alias="Title", description="Title of the article."
    )
    journal_field_specialty: Optional[
        Literal[
            "Cardiology - cardiovascular medicine, electrophysiology, vascular medicine, cardiac surgery, and transplantation",
            "Hematology + Thrombosis/Haemostasis + Oncology - includes hematology/oncology, coagulation, thrombosis, thrombolysis, APS, and malignant hematology",
            "Pharmacology + Clinical Pharmacology + Pharmacy + Pharmacokinetics/Pharmacodynamics - includes pharmacogenetics, pharmacometrics, toxicology, drug metabolism, pharmacotherapy, pharmaceutics, and pharmacoeconomics",
            "Internal/General Medicine - general medicine, geriatrics, nephrology, endocrinology, respiratory, and emergency/internal medicine subspecialties",
            "Neurology + Neurosurgery - stroke, neuropharmacology, spine surgery, neurocritical care, and electrophysiology",
            "Anesthesiology + Critical Care + Perioperative/Trauma Medicine - pain management, intensive care, trauma and emergency surgery",
            "Pediatrics + Transplantation + Genetics - pediatric hematology/oncology, congenital and genetic medicine, transplantation",
            "Laboratory + Analytical + Clinical Chemistry Sciences - bioanalysis, mass spectrometry, chromatography, diagnostics, and biochemistry",
        ]
    ] = Field(
        default=None,
        alias="Journal Field/Specialty",
        description="Discipline/specialty of the journal.",
    )
    publication_year: Optional[str] = Field(
        default=None,
        alias="Publication Year",
        description="Four-digit year (e.g., '2022').",
    )
    affiliation_of_first_author: Optional[str] = Field(
        default=None, alias="Affiliation of First Author"
    )
    country_of_first_author: Optional[str] = Field(
        default=None, alias="Country of First Author"
    )

    # Study design
    study_design: Optional[
        Literal[
            "Randomized Controlled Trial",
            "Cohort Study",
            "Non-Randomized Experimental Study",
            "Non-Randomized Observational Study",
            "Cross-Sectional Study",
            "Case-Control Study",
            "Pharmacokinetic Study",
            "In Silico Simulation Analysis",
            "Systematic Review",
            "Qualitative Research",
            "Diagnostic Test Accuracy Study",
            "Case Series",
            "Case Report",
            "Other",
        ]
    ] = Field(
        default=None,
        alias="Study Design",
        description=(
            "CRITICAL: Use explicit hierarchy with definitions. Classify based on the PRIMARY goal of the study.\n\n"
            "Two-step process:\n"
            "Step 1 (Evidence): Quote exact sentences from Title/Abstract/Methods that describe the study design or primary goal.\n"
            "Step 2 (Decision): Based ONLY on those quoted sentences, apply the hierarchy below to classify.\n\n"
            "HIERARCHY (apply in order, stop at first match):\n"
            "1) If primary goal is to assess test performance vs reference standard (sensitivity/specificity, ROC/AUC, agreement/validation) "
            "   → 'Diagnostic Test Accuracy Study'\n"
            "2) Else if randomized groups (randomized, allocation, double-blind, placebo-controlled, trial registration) "
            "   → 'Randomized Controlled Trial'\n"
            "3) Else if prospective measurement of outcomes in a defined cohort without randomization (prospective/retrospective cohort, "
            "   follow-up, incidence, registry, time-to-event) → 'Cohort Study'\n"
            "4) Else if purely describing PK curves in a defined regimen (pharmacokinetic/PK, Cmax, AUC, half-life, sampling at trough/peak) "
            "   → 'Pharmacokinetic Study'\n"
            "5) Else if case-control design (case-control, matched controls, odds ratio, retrospective comparison) "
            "   → 'Case-Control Study'\n"
            "6) Else if cross-sectional design (cross-sectional, point prevalence, single time point, baseline-only measurement) "
            "   → 'Cross-Sectional Study'\n"
            "7) Else if interventional but no randomization (single-arm, open-label, pilot intervention, protocol evaluation) "
            "   → 'Non-Randomized Experimental Study'\n"
            "8) Else if systematic review/meta-analysis (PRISMA, pooled analysis, predefined inclusion criteria, literature search) "
            "   → 'Systematic Review'\n"
            "9) Else if modeling/simulation (population PK/PD, PBPK, Monte Carlo, virtual/simulated cohort) "
            "   → 'In Silico Simulation Analysis'\n"
            "10) Else if qualitative research (interviews/focus groups, thematic/framework analysis, perceptions/attitudes) "
            "    → 'Qualitative Research'\n"
            "11) Else if case series (multiple patients, no control, small N with tabulated individual data) "
            "    → 'Case Series'\n"
            "12) Else if case report (single patient/rare event with detailed narrative) "
            "    → 'Case Report'\n"
            "13) Else if observational/registry/chart review without assigned intervention "
            "    → 'Non-Randomized Observational Study'\n"
            "14) Else → 'Other'\n\n"
            "Common misclassifications to avoid:\n"
            "• Labeling a diagnostic test accuracy study as 'prospective observational cohort'.\n"
            "• Labeling a prospective cohort with PK/PD components as a pure 'pharmacokinetic study' "
            "  (if outcomes are measured, it's likely a Cohort Study, not Pharmacokinetic Study).\n\n"
            "Do not infer; use explicit language in Title/Abstract/Methods. If ambiguous, return null."
        ),
    )
    study_design_sentence_from_text: Optional[str] = Field(
        default=None,
        alias="Study Design Sentence from Text",
        description="Exact sentences or paragraph containing the study design.",
    )
    study_design_confidence_score: int = Field(
        default=0,
        alias="Study Design Confidence Score",
        description="Confidence score for the study design classification. A number between 0 and 100, where 0 is the lowest confidence and 100 is the highest confidence.",
        ge=0,
        le=100,
    )

    model_config = ConfigDict(populate_by_name=True)


# ---------------------------------------
# 2) Population, Indications, Subgroups
# ---------------------------------------
class ExtractionPopulationIndications(BaseModel):
    """
    Guidelines:
    1) Do not infer or guess.
    2) Use null if unsure.
    3) Output only facts explicitly in the PDF.
    4) If ambiguous, set null (do not guess).
    5) Numeric values must be exact.
    6) Resolve conflicts by the clearest statement (title→early pages; patients→methods/results).
    7) IGNORE external knowledge.
    8) Ignore Introduction/Background, References and Acknowledgments content.
    9) Focus on Methods and Results and Abstract sections.
    """

    # Patient population
    total_patients: Optional[int] = Field(
        default=None,
        alias="Patient Population",
        description="Total number of patients.",
    )
    total_patients_sentence_from_text: Optional[str] = Field(
        default=None,
        alias="Patient Population Sentence from Text",
        description="Exact sentences or paragraph containing the total patients.",
    )

    # DOACs included (measured)
    doacs_included: Optional[
        List[Literal["Apixaban", "Rivaroxaban", "Edoxaban", "Betrixaban", "Dabigatran"]]
    ] = Field(
        default=None,
        alias="Patient population 1",
        description=(
            "Include a DOAC ONLY if its level was actually measured in this study. "
            "IGNORE DOACs only mentioned in Intro/Discussion/external citations."
        ),
    )
    doacs_included_sentence_from_text: Optional[List[str]] = Field(
        default=None,
        alias="DOACs Included Sentence from Text",
        description="Exact sentences or paragraph containing the included DOACs.",
    )

    # Indications for anticoagulation (must apply to measured population)
    indication_for_anticoagulation: Optional[
        List[Literal["AF", "VTE Treatment/Prevention", "Other", "Not Reported"]]
    ] = Field(
        default=None,
        alias="Patient population 2",
        description=(
            "Only include an indication (e.g., AF, VTE) if patients whose DOAC levels were measured had that indication."
        ),
    )
    indication_for_anticoagulation_sentence_from_text: Optional[List[str]] = Field(
        default=None,
        alias="Indications for Anticoagulation Sentence from Text",
        description="Exact sentences or paragraph containing the indications for anticoagulation.",
    )

    # Relevant subgroups (must be explicitly studied/measured)
    relevant_subgroups: Optional[
        List[
            Literal[
                "High body weight (obesity)",
                "Low body weight",
                "Chronic kidney disease/dialysis",
                "Bariatric surgery/malabsorption",
                "Drug-DOAC pharmacokinetic interactions",
                "Advanced age/frailty",
                "Elective procedure/surgery",
                "Urgent/emergent procedure/surgery",
                "Acute stroke/thrombolysis",
                "DOAC-associated bleeding + DOAC Reversal",
                "Genetic polymorphism (e.g., CYP polymorphism)",
            ]
        ]
    ] = Field(
        default=None,
        alias="Patient population 3",
        description=(
            "CRITICAL: Include a subgroup ONLY if at least ONE of these is true:\n"
            "1) The inclusion criteria explicitly restrict to that subgroup (e.g., 'patients with CKD stage 3–5').\n"
            "2) The study defines a pre-specified subgroup analysis (e.g., 'we analyzed outcomes separately in patients with body weight ≥120 kg').\n"
            "3) The title or objectives clearly state that subgroup (e.g., '...in patients with short bowel syndrome').\n\n"
            "EXPLICIT NEGATIVE RULE: IGNORE labeling a subgroup solely because:\n"
            "• The characteristic is reported in baseline tables or baseline characteristics.\n"
            "• The characteristic is mentioned in the Introduction or Background.\n"
            "• A single keyword appears without explicit subgroup analysis or restriction.\n"
            "• DOAC levels were measured but NOT stratified by that subgroup.\n\n"
            "Two-step process:\n"
            "Step 1 (Evidence): Quote the exact sentences from Methods/Results (NOT Introduction) that describe subgroup restriction or analysis.\n"
            "Step 2 (Decision): Based ONLY on those quoted sentences, classify the subgroup. If no explicit restriction/analysis exists, leave null.\n\n"
            "Subgroup-specific criteria (all require explicit restriction/analysis, NOT just keywords):\n"
            "1) High body weight (obesity) — Requires: inclusion criteria restricting to obese patients, OR explicit subgroup analysis by BMI/weight strata with measured levels.\n"
            "   Exclusions: BMI/weight in baseline table only; generic discussion of obesity without measured level stratification.\n\n"
            "2) Low body weight — Requires: inclusion criteria restricting to low-weight patients, OR explicit analysis comparing levels by weight strata (e.g., ≤60 kg vs >60 kg).\n"
            "   Exclusions: weight reported in baseline only; dose-label criteria mentioned without measured level analysis.\n\n"
            "3) Chronic kidney disease/dialysis — Requires: inclusion criteria restricting to CKD/dialysis patients, OR explicit analysis of levels by renal function strata (eGFR/CrCl stages).\n"
            "   Exclusions: creatinine/eGFR reported in baseline without level stratification; generic mention of 'renal impairment' in Introduction.\n\n"
            "4) Bariatric surgery/malabsorption — Requires: inclusion criteria restricting to post-bariatric patients, OR explicit pre/post-op level comparisons.\n"
            "   Exclusions: perioperative protocols without measured levels; generic discussion of malabsorption.\n\n"
            "5) Drug-DOAC pharmacokinetic interactions — Requires: inclusion criteria restricting to patients on interacting drugs, OR explicit comparison of levels with vs without comedication.\n"
            "   Exclusions: comedication listed in baseline without level comparison; generic DDI discussion.\n\n"
            "6) Advanced age/frailty — Requires: inclusion criteria restricting to elderly/frail patients, OR explicit analysis of levels by age/frailty strata.\n"
            "   Exclusions: age reported in baseline only; generic mention of 'elderly' in Introduction.\n\n"
            "7) Elective procedure/surgery — Requires: inclusion criteria restricting to elective surgery patients, OR explicit analysis of pre-op levels guiding timing.\n"
            "   Exclusions: protocols without measured pre-op levels; generic perioperative discussion.\n\n"
            "8) Urgent/emergent procedure/surgery — Requires: inclusion criteria restricting to urgent/emergent cases, OR explicit analysis of levels guiding proceed/cancel decisions.\n"
            "   Exclusions: emergent cases described without measured levels; generic emergency discussion.\n\n"
            "9) Acute stroke/thrombolysis — Requires: inclusion criteria restricting to stroke/thrombolysis patients, OR explicit use of levels to determine lytic eligibility.\n"
            "   Exclusions: stroke registries without levels; generic stroke discussion.\n\n"
            "10) DOAC-associated bleeding + DOAC Reversal — Requires: inclusion criteria restricting to bleeding/reversal patients, OR explicit analysis of pre/post-reversal levels.\n"
            "   Exclusions: bleeding described without measured levels; generic reversal discussion.\n\n"
            "11) Genetic polymorphism — Requires: inclusion criteria restricting to specific genotypes, OR explicit analysis of levels by genotype.\n"
            "   Exclusions: genotyping performed without level stratification; generic pharmacogenetics discussion.\n\n"
            "If ambiguous or no explicit restriction/analysis exists, leave null. IGNORE guessing based on keywords alone."
        ),
    )
    relevant_subgroups_sentence_from_text: Optional[List[str]] = Field(
        default=None,
        alias="Relevant Subgroups Sentence from Text",
        description="Exact sentences or paragraph containing the relevant subgroups.",
    )
    relevant_subgroups_confidence_score: int = Field(
        default=0,
        alias="Relevant Subgroups Confidence Score",
        description="Confidence score for the relevant subgroups classification. A number between 0 and 100, where 0 is the lowest confidence and 100 is the highest confidence.",
        ge=0,
        le=100,
    )

    # Indications for DOAC level measurement
    indications_for_doac_level_measurement: Optional[
        List[
            Literal[
                "Confirm adherence",
                "Evaluate DOAC level exposure - Bariatric surgery",
                "Evaluate DOAC level exposure - Drug-DOAC interaction",
                "Evaluate DOAC level exposure - Chronic kidney failure",
                "Evaluate DOAC level exposure - Obesity",
                "Evaluate DOAC level exposure - Residual DOAC level after elective interruption",
                "Identify predictors of DOAC level exposure - Cmax, Ctrough, AUC",
                "Guide clinical decision-making - Urgent surgery",
                "Guide clinical decision-making - Major bleeding and reversal agent administration",
                "Guide clinical decision-making - Thrombolysis",
                "Guide clinical decision-making - Guide dose adjustment",
                "Measure correlation with other laboratory techniques - Conventional coagulation testing (e.g., prothrombin time)",
                "Measure correlation with other laboratory techniques - HPLC-MS vs calibrated anti-Xa measurement",
                "Risk prediction and clinical outcome association - Bleeding",
                "Risk prediction and clinical outcome association - Thrombosis",
            ]
        ]
    ] = Field(
        default=None,
        alias="Indications for DOAC Level Measurement",
        description=(
            "CRITICAL: First answer the primary question: 'What was the main purpose for measuring DOAC levels in this study?'\n"
            "Then include ALL explicit reasons stated in Methods/Results (NOT Introduction/Discussion).\n\n"
            "Two-step process:\n"
            "Step 1 (Evidence): Quote exact sentences from Methods/Results that state why DOAC levels were measured. "
            "Look for purpose phrasing like 'measured to…', 'levels were used to…', 'we evaluated exposure…', "
            "'guided clinical decision', 'we assessed correlation...'.\n"
            "Step 2 (Decision): Based ONLY on those quoted sentences, classify the indication(s).\n\n"
            "Include an indication ONLY if:\n"
            "1) It is explicitly stated in Methods/Results (NOT just mentioned in passing in Introduction/Discussion).\n"
            "2) Patient samples were actually quantified in THIS study (not simulations, not external registries).\n"
            "3) It is central to the study objectives, not mentioned in passing.\n\n"
            "Do NOT over-label. Common errors to avoid:\n"
            "• Marking multiple overlapping indications (e.g., 'bleeding risk', 'thrombosis', 'CKD') when the study "
            "  is simply 'evaluate DOAC exposure/assay performance'.\n"
            "• Including indications mentioned only in Background/Discussion without explicit measurement purpose.\n"
            "• Inferring indications from baseline characteristics without explicit measurement rationale.\n\n"
            "Category-specific rules:\n"
            "1) Confirm adherence — Requires explicit statement that levels were used to verify/confirm intake. "
            "Exclusions: questionnaires/refill/pill count only.\n\n"
            "2) Evaluate DOAC level exposure (condition-specific) — Requires explicit analysis of levels in that condition:\n"
            "  2a) Bariatric surgery — explicit pre/post-op level comparisons or time-since-surgery analysis.\n"
            "  2b) Drug–DOAC interaction — explicit comparison of levels with vs without comedication.\n"
            "  2c) Chronic kidney failure — explicit level analysis by renal function strata.\n"
            "  2d) Obesity — explicit level analysis by BMI/weight groups.\n"
            "  2e) Residual level after elective interruption — explicit measurement of pre-procedure levels.\n\n"
            "3) Identify predictors of DOAC level exposure — Requires explicit regression/association analysis of levels with factors. "
            "Cmax/Ctrough/AUC: explicit PK parameters calculated from patient samples.\n\n"
            "4) Guide clinical decision-making — Requires explicit statement that levels directly informed care:\n"
            "  4a) Urgent surgery — timing guided by measured level.\n"
            "  4b) Major bleeding + reversal — pre/post-reversal levels used to guide reversal.\n"
            "  4c) Thrombolysis — eligibility determined by measured level.\n"
            "  4d) Guide dose adjustment — dose change explicitly based on measured concentration.\n\n"
            "5) Measure correlation with other laboratory techniques — Requires explicit quantitative correlation/validation. "
            "Exclusions: qualitative statements without numeric comparison.\n\n"
            "6) Risk prediction and clinical outcome association — Requires explicit association analysis of levels with outcomes. "
            "Exclusions: outcomes without measured concentrations.\n\n"
            "If the article does not clearly report the indication, do not guess. Leave null if unsure."
        ),
    )
    indications_for_doac_level_measurement_sentence_from_text: Optional[List[str]] = (
        Field(
            default=None,
            alias="Indications for DOAC Level Measurement Sentence from Text",
            description="Exact sentences or paragraph containing the indications for DOAC level measurement.",
        )
    )
    indications_for_doac_level_measurement_confidence_score: int = Field(
        default=0,
        alias="Indications for DOAC Level Measurement Confidence Score",
        description="Confidence score for the indications for DOAC level measurement classification. A number between 0 and 100, where 0 is the lowest confidence and 100 is the highest confidence.",
        ge=0,
        le=100,
    )

    model_config = ConfigDict(populate_by_name=True)


# ------------------------------------
# 3) Methods & Assays Blocks
# ------------------------------------
class ExtractionMethods(BaseModel):
    """
    Guidelines:
    1) Do not infer or guess.
    2) Use null if unsure.
    3) Output only facts explicitly in the PDF.
    4) If ambiguous, set null (do not guess).
    5) Numeric values must be exact.
    6) Resolve conflicts by the clearest statement (title→early pages; patients→methods/results).
    7) IGNORE external knowledge.
    8) Ignore Introduction/Background, References and Acknowledgments content.
    9) Focus on Methods and Results and Abstract sections.
    """

    doac_level_measurement: Optional[
        List[
            Literal[
                # Apixaban
                "Apixaban - HPLC-MS (ng/mL)",
                "Apixaban - Calibrated anti-Xa level (ng/mL)",
                "Apixaban - Heparin (UFH/LMWH) anti-Xa level (IU/mL)",
                "Apixaban - Qualitative/Point-of-Care (POCT)",
                "Apixaban - Other",
                # Rivaroxaban
                "Rivaroxaban - HPLC-MS (ng/mL)",
                "Rivaroxaban - Calibrated anti-Xa level (ng/mL)",
                "Rivaroxaban - Heparin (UFH/LMWH) anti-Xa level (IU/mL)",
                "Rivaroxaban - Qualitative/Point-of-Care (POCT)",
                "Rivaroxaban - Other",
                # Edoxaban
                "Edoxaban - HPLC-MS (ng/mL)",
                "Edoxaban - Calibrated anti-Xa level (ng/mL)",
                "Edoxaban - Heparin (UFH/LMWH) anti-Xa level (IU/mL)",
                "Edoxaban - Qualitative/Point-of-Care (POCT)",
                "Edoxaban - Other",
                # Betrixaban
                "Betrixaban - HPLC-MS (ng/mL)",
                "Betrixaban - Calibrated anti-Xa level (ng/mL)",
                "Betrixaban - Heparin (UFH/LMWH) anti-Xa level (IU/mL)",
                "Betrixaban - Qualitative/Point-of-Care (POCT)",
                "Betrixaban - Other",
                # Dabigatran
                "Dabigatran - HPLC-MS (ng/mL)",
                "Dabigatran - Thrombin Time (TT)",
                "Dabigatran - Dilute Thrombin Time (dTT)",
                "Dabigatran - Ecarin Clotting Time (ECT)",
                "Dabigatran - Ecarin Chromogenic Assay (ECA)",
                "Dabigatran - Qualitative/Point-of-Care (POCT)",
                "Dabigatran - Other",
            ]
        ]
    ] = Field(
        default=None,
        alias="DOAC Level Measurement",
        description=(
            "CRITICAL: Scan the ENTIRE Methods and Results sections for assay methodology terms. Return ALL methods that were actually used "
            "in THIS study to quantify DOAC levels (patient sample measurements only). IGNORE Background/Discussion.\n\n"
            "Two-step process:\n"
            "Step 1 (Evidence): Quote exact sentences from Methods and Results that describe the assay methods used. "
            "Scan for ALL synonyms and variants (see synonym map below).\n"
            "Step 2 (Decision): Based ONLY on those quoted sentences, classify ALL applicable methods.\n\n"
            "SYNONYM MAP FOR HPLC-MS/LC-MS (CRITICAL - scan for ALL variations):\n"
            "• HPLC-MS / HPLC-MS/MS / HPLC/MS / HPLC/MS/MS (with hyphens OR forward slashes)\n"
            "• LC-MS/MS / LC-MS / LC/MS / LC/MS/MS\n"
            "• UPLC-MS / UPLC-MS/MS / UPLC/MS / UPLC/MS/MS\n"
            "• High-performance liquid chromatography-mass spectrometry / high performance liquid chromatography mass spectrometry\n"
            "• Liquid chromatography-mass spectrometry / liquid chromatography mass spectrometry\n"
            "• Mass spectrometry / MS / tandem mass spectrometry / MS/MS\n"
            '• Any combination of "HPLC" or "LC" or "UPLC" with "MS" or "mass spectrometry"\n'
            "  → ALL map to 'HPLC-MS/LC-MS (ng/mL)'\n\n"
            "SYNONYM MAP FOR OTHER METHODS:\n"
            "• Calibrated anti-Xa / drug-specific anti-Xa / DOAC-specific anti-Xa / DiXaI / Biophen / "
            "STA-Liquid Anti-Xa + drug calibrator / TECHNOVIEW / HemosIL Liquid Anti-Xa + drug calibrators / "
            "Innovance Heparin anti-Xa with drug calibrators / COAMATIC / Berichrom / Rotachrom with drug calibrators "
            "  → 'Calibrated anti-Xa level (ng/mL)'\n"
            "• Heparin-calibrated anti-Xa / LMWH-calibrated / UFH-calibrated (without drug-specific calibration) "
            "  → 'Heparin (UFH/LMWH) anti-Xa level (IU/mL)'\n"
            "• For Dabigatran: Hemoclot / dTT / diluted thrombin time / HemosIL DTI / INNOVANCE DTI "
            "  → 'Dilute Thrombin Time (dTT)'\n"
            "• For Dabigatran: Ecarin Clotting Time / ECT / Ecarin Chromogenic Assay / ECA "
            "  → 'Ecarin Clotting Time (ECT)' or 'Ecarin Chromogenic Assay (ECA)'\n"
            "• For Dabigatran: Thrombin Time / TT (when used for dabigatran) "
            "  → 'Thrombin Time (TT)'\n\n"
            "Common errors to avoid:\n"
            "• CRITICAL: Missing HPLC-MS/LC-MS when clearly described in Methods (e.g., 'HPLC/MS was used', 'LC-MS/MS analysis', "
            "'measured by mass spectrometry'). Scan for ALL variations including forward slashes.\n"
            "• Partial recognition: identifying some methods but missing others in the same paragraph.\n"
            "• Including methods mentioned only in Background/Discussion without Methods description.\n\n"
            "Include ONLY if this method was actually used in THIS study to quantify DOAC level in patients. "
            "Exclude: background mentions of potential assays; assay description without patient sample quantification."
        ),
    )
    doac_level_measurement_sentence_from_text: Optional[List[str]] = Field(
        default=None,
        alias="DOAC Level Measurement Sentence from Text",
        description="Exact sentences or paragraph containing the DOAC level measurement.",
    )
    doac_level_measurement_confidence_score: int = Field(
        default=0,
        alias="DOAC Level Measurement Confidence Score",
        description="Confidence score for the DOAC level measurement classification. A number between 0 and 100, where 0 is the lowest confidence and 100 is the highest confidence.",
        ge=0,
        le=100,
    )

    doac_level_measurement_descriptors: Optional[
        List[
            Literal[
                # Apixaban
                "Apixaban - Calibrated anti-Xa assay (ng/mL)",
                "Apixaban - Heparin-calibrated anti-Xa assay (IU/mL)",
                "Apixaban - LC-MS/MS quantitative assay (ng/mL)",
                "Apixaban - Qualitative/Point-of-Care (POCT)",
                "Apixaban - Other",
                # Rivaroxaban
                "Rivaroxaban - Calibrated anti-Xa assay (ng/mL)",
                "Rivaroxaban - Heparin-calibrated anti-Xa assay (IU/mL)",
                "Rivaroxaban - LC-MS/MS quantitative assay (ng/mL)",
                "Rivaroxaban - Qualitative/Point-of-Care (POCT)",
                "Rivaroxaban - Other",
                # Edoxaban
                "Edoxaban - Calibrated anti-Xa assay (ng/mL)",
                "Edoxaban - Heparin-calibrated anti-Xa assay (IU/mL)",
                "Edoxaban - LC-MS/MS quantitative assay (ng/mL)",
                "Edoxaban - Qualitative/Point-of-Care (POCT)",
                "Edoxaban - Other",
                # Betrixaban
                "Betrixaban - Calibrated anti-Xa assay (ng/mL)",
                "Betrixaban - Heparin-calibrated anti-Xa assay (IU/mL)",
                "Betrixaban - LC-MS/MS quantitative assay (ng/mL)",
                "Betrixaban - Qualitative/Point-of-Care (POCT)",
                "Betrixaban - Other",
                # Dabigatran (FIIa)
                "Dabigatran - Dilute Thrombin Time (dTT) calibrated (ng/mL)",
                "Dabigatran - Ecarin Clotting Time (ECT) calibrated (ng/mL)",
                "Dabigatran - Ecarin Chromogenic Assay (ECA) calibrated (ng/mL)",
                "Dabigatran - Non-calibrated Thrombin Time (TT) (seconds)",
                "Dabigatran - LC-MS/MS quantitative assay (ng/mL)",
                "Dabigatran - Qualitative/Point-of-Care (POCT)",
                "Dabigatran - Other",
            ]
        ]
    ] = Field(
        default=None,
        alias="DOAC Level Measurement Descriptors",
        description=(
            "CRITICAL: Scan the ENTIRE Methods section for assay terms. Return ALL assay descriptors that were actually used "
            "in THIS study to quantify DOAC levels (patient sample measurements only). IGNORE Background/Discussion.\n\n"
            "Two-step process:\n"
            "Step 1 (Evidence): Quote exact sentences from Methods that describe the assay methods used. "
            "Scan for ALL synonyms and variants (see synonym map below).\n"
            "Step 2 (Decision): Based ONLY on those quoted sentences, classify ALL applicable methods.\n\n"
            "SYNONYM MAP (use to identify methods even if exact term not used):\n"
            "• LC-MS/MS / LC-MS / LC/MS / LC/MS/MS (with hyphens OR forward slashes)\n"
            "• UPLC-MS / UPLC-MS/MS / UPLC/MS / UPLC/MS/MS (with hyphens OR forward slashes)\n"
            "• HPLC-MS / HPLC-MS/MS / HPLC/MS / HPLC/MS/MS (with hyphens OR forward slashes) - CRITICAL: scan for forward slash variations\n"
            "• High-performance liquid chromatography-mass spectrometry / high performance liquid chromatography mass spectrometry\n"
            "• Liquid chromatography-mass spectrometry / liquid chromatography mass spectrometry\n"
            "• Mass spectrometry / MS / tandem mass spectrometry / MS/MS\n"
            '• Any combination of "HPLC" or "LC" or "UPLC" with "MS" or "mass spectrometry" (regardless of punctuation: hyphen, slash, or space)\n'
            "  → ALL map to 'LC-MS/MS quantitative assay (ng/mL)'\n"
            "• Hemoclot / dTT / diluted thrombin time / HemosIL DTI / INNOVANCE DTI "
            "  → 'Dilute Thrombin Time (dTT) calibrated (ng/mL)'\n"
            "• DiXaI / Biophen / calibrated anti-Xa / drug-specific anti-Xa / STA-Liquid Anti-Xa + drug calibrator / "
            "  TECHNOVIEW / HemosIL Liquid Anti-Xa + drug calibrators / Innovance Heparin anti-Xa with drug calibrators / "
            "  COAMATIC / Berichrom / Rotachrom with drug calibrators "
            "  → 'Calibrated anti-Xa assay (ng/mL)'\n"
            "• Heparin-calibrated anti-Xa / LMWH-calibrated / UFH-calibrated (without drug-specific calibration) "
            "  → 'Heparin-calibrated anti-Xa assay (IU/mL)'\n"
            "• Thrombograms / CAT / calibrated automated thrombography / thrombin generation "
            "  → Note: This is NOT a DOAC level measurement method; do NOT include here.\n"
            "• TEG / ROTEM / viscoelastic testing "
            "  → Note: This is NOT a DOAC level measurement method; do NOT include here.\n\n"
            "Definitions:\n"
            "• Calibrated anti-Xa assay (ng/mL) = DOAC-specific calibration materials were used.\n"
            "• Heparin-calibrated anti-Xa assay (IU/mL) = LMWH/UFH-calibrated assay used with NO drug-specific calibration.\n"
            "• LC-MS/MS quantitative assay (ng/mL) = mass-spectrometry-based direct concentration measurement of the DOAC.\n"
            "• Qualitative / Point-of-Care (POCT) = DOAC Dipstick or equivalent qualitative device.\n"
            "• Dilute Thrombin Time (dTT) calibrated (ng/mL) = dabigatran-specific calibrated clotting assay.\n"
            "• Ecarin-based assays (ng/mL) = calibrated dabigatran methods: ECT (clot-based) or ECA (chromogenic).\n"
            "• Non-calibrated TT (seconds) = qualitative TT index sensitive to dabigatran at low levels, NOT quantitative.\n\n"
            "Common errors to avoid:\n"
            "• CRITICAL: Missing HPLC-MS/LC-MS/UPLC-MS when clearly described in Methods. "
            "Scan for ALL variations including: HPLC-MS, HPLC/MS, HPLC-MS/MS, HPLC/MS/MS, LC-MS/MS, LC/MS, "
            "UPLC-MS, UPLC/MS, mass spectrometry, liquid chromatography-mass spectrometry, etc. "
            "If the Methods section describes using any form of liquid chromatography with mass spectrometry, "
            "this MUST be flagged as 'LC-MS/MS quantitative assay (ng/mL)'.\n"
            "• Missing TT (for dabigatran) when clearly described.\n"
            "• Partial recognition: identifying some methods (e.g., dTT, anti-Xa) but missing others (TT, LC-MS) in the same paragraph.\n"
            "• Including manufacturer names (e.g., Technoclone) as evidence of method use without explicit description.\n"
            "• Not recognizing forward slash variations (HPLC/MS) - these are equivalent to hyphenated forms (HPLC-MS).\n\n"
            "Include only methods actually applied to patient samples in THIS study. "
            "Exclude laboratory capabilities mentioned but NOT used, and exclude review-style brand lists unless performed."
        ),
    )
    doac_level_measurement_descriptors_sentence_from_text: Optional[List[str]] = Field(
        default=None,
        alias="DOAC Level Measurement Descriptors Sentence from Text",
        description="Exact sentences or paragraph containing the DOAC level measurement descriptors.",
    )

    # Pre-Analytical Variables
    pre_analytical_variables: Optional[
        List[
            Literal[
                "Blood collection procedures",
                "Collection tube type",
                "Centrifugation speed",
                "Storage temperature",
            ]
        ]
    ] = Field(
        default=None,
        alias="Pre-Analytical Variables",
        description=(
            "CRITICAL: Review the entire Methods section for explicit descriptions of pre-analytical variables relating to DOAC level measurement specimens. "
            "Include only when the procedures were specifically applied to specimens analyzed in THIS study (not background, review, or capability statements).\n\n"
            "Pre-analytical variables to flag (include only if used in THIS study):\n"
            "• Blood collection procedures (e.g., needle gauge, tourniquet technique)\n"
            "• Collection tube type (e.g., 2.7% citrate Becton Dickinson)\n"
            "• Centrifugation speed\n"
            "• Storage temperature (e.g., -80°C)\n\n"
            "Follow a strict two-step process:\n"
            "Step 1 – Evidence:\n"
            "  Quote the precise sentences from the Methods section describing collection, tube, centrifugation, or storage procedures for DOAC level specimens.\n"
            "Step 2 – Decision:\n"
            "  Flag a variable as present ONLY if there is explicit reporting for samples measured in THIS study.\n\n"
            "Detailed keyword guidance for identification (flag only if present in the Methods):\n\n"
            "1. Blood collection procedures:\n"
            "   Core indicator terms:\n"
            "     - venipuncture, phlebotomy\n"
            "     - blood draw, blood sampling, blood collection\n"
            "     - venous blood, peripheral venous blood\n"
            "     - antecubital vein, antecubital fossa\n"
            "     - butterfly needle\n"
            "     - needle gauge (e.g., 21-gauge, 22-gauge, 21G, 22G)\n"
            "     - tourniquet, tourniquet application\n"
            "     - vacutainer, vacuum collection system\n"
            "   Procedure/context phrases:\n"
            '     - "blood was collected from", "venous blood was drawn using"\n'
            '     - "single venipuncture", "single blood draw"\n'
            '     - "non-traumatic venipuncture"\n'
            '     - "without stasis", "minimal stasis"\n'
            '     - "fasting state", "after an overnight fast"\n'
            '     - "subject seated for X minutes before sampling", "supine for X minutes before sampling"\n'
            '     - time of day descriptors: "morning sample", "pre-dose", "trough sample"\n\n'
            "2. Collection tube type:\n"
            "   Core tube descriptors:\n"
            "     - collection tube, blood collection tube\n"
            "     - coagulation tube, citrate tube, blue-top tube\n"
            "     - plasma tube, serum tube, plain tube\n"
            "     - Vacutainer, BD Vacutainer, Sarstedt, Greiner, Monovette\n"
            "   Anticoagulant/additive keywords:\n"
            "     - sodium citrate, Na-citrate, citrated tube\n"
            "     - 3.2% citrate, 3.8% citrate, 0.109 mol/L citrate\n"
            "     - EDTA, K2EDTA, K3EDTA\n"
            "     - heparin, lithium heparin, Na-heparin\n"
            "     - no additive, additive-free, clot activator\n"
            "     - gel separator, serum separator tube (SST)\n"
            "   Typical phrases:\n"
            '     - "blood was collected into [X] tubes"\n'
            '     - "blood was drawn into 2.7 mL 3.2% sodium citrate tubes (Becton Dickinson)"\n'
            '     - "citrated plasma obtained from 3.2% sodium citrate Vacutainer tubes"\n\n'
            "3. Centrifugation speed:\n"
            "   Core process terms:\n"
            "     - centrifuge, centrifugation, spun, spin, spun down\n"
            "     - relative centrifugal force (RCF), g-force, ×g, x g\n"
            "     - rpm, revolutions per minute\n"
            "   Typical formats:\n"
            '     - "centrifuged at 1,500 × g for 10 min"\n'
            '     - "centrifuged at 2,500g for 15 minutes"\n'
            '     - "spun at 3,000 rpm for 10 min"\n'
            '     - "double centrifugation", "two-step centrifugation"\n'
            '     - "to obtain platelet-poor plasma (PPP)"\n'
            '     - "centrifuged at room temperature", "centrifuged at 4°C"\n\n'
            "4. Storage temperature:\n"
            "   Core temperature & storage terms:\n"
            "     - stored at, kept at, maintained at\n"
            "     - frozen at, immediately frozen, snap frozen\n"
            "     - refrigerated, kept at 4°C\n"
            "     - room temperature, ambient temperature, RT\n"
            "     - long-term storage, short-term storage\n"
            "     - aliquots, aliquoted and stored\n"
            "   Temperature formats:\n"
            '     - −80°C, -80°C, −70°C, -70°C, −20°C, -18°C, 4°C, 2–8°C, 20–25°C, "room temperature", "ambient"\n'
            "   Typical phrases:\n"
            '     - "plasma samples were aliquoted and stored at −80°C until analysis"\n'
            '     - "samples were kept at 4°C and analyzed within 4 hours"\n'
            '     - "serum was stored at −20°C before batch analysis"\n'
            '     - "samples were kept at room temperature"\n\n'
            "Common errors to avoid:\n"
            "• Overcounting: Do NOT flag if only mentioned in Background, Introduction, or as general lab capabilities rather than specimen-specific protocol.\n"
            "• Do NOT guess based on context or intuition if explicit Methods evidence is lacking; leave null if not reported."
        ),
    )
    pre_analytical_variables_sentence_from_text: Optional[List[str]] = Field(
        default=None,
        alias="Pre-Analytical Variables Sentence from Text",
        description="Exact sentences or paragraph containing the pre-analytical variables.",
    )
    pre_analytical_variables_confidence_score: int = Field(
        default=0,
        alias="Pre-Analytical Variables Confidence Score",
        description="Confidence score for the pre-analytical variables classification. A number between 0 and 100, where 0 is the lowest confidence and 100 is the highest confidence.",
        ge=0,
        le=100,
    )

    # Conventional Coagulation Tests Concurrently Reported
    coagulation_tests_concurrent: Optional[
        List[
            Literal[
                "Prothrombin time (PT)", "Activated partial thromboplastin time (aPTT)"
            ]
        ]
    ] = Field(
        default=None,
        alias="Conventional Coagulation Tests Concurrently Reported",
        description=(
            "CONVENTIONAL COAGULATION TESTING (PT and aPTT)\n"
            "------------------------------------------------\n"
            "This field captures whether conventional coagulation tests—specifically prothrombin time (PT) and/or activated partial thromboplastin time (aPTT)—"
            "were actually performed and reported on the same specimens as DOAC (direct oral anticoagulant) measurements in the study.\n\n"
            "GENERAL RULES:\n"
            "• Only count a test if the article explicitly describes *measurement* (not merely mentioning the test in background, introduction, or theory).\n"
            "• Ignore general mentions of 'PT' or 'aPTT' if there is no evidence that the test was performed on study samples.\n\n"
            "STRICT FILTERING CRITERIA (APPLIES REGARDLESS OF TECHNIQUE):\n\n"
            "1) SECTION RELEVANCE:\n"
            "   • Only count tests mentioned in 'Methods', 'Materials and Methods', 'Laboratory Methods', 'Study Procedures', 'Results', 'Outcomes', "
            "'Baseline characteristics', 'Laboratory results', or any text directly describing procedures/measurements for participants.\n"
            "   • Ignore mentions limited to Introduction, Background, or descriptions of general practice/guidelines.\n\n"
            "2) MEASUREMENT CONTEXT REQUIRED:\n"
            "   Only flag PT or aPTT as measured if the sentence (or one immediately before/after) includes verbs/phrases like:\n"
            "   • 'measured', 'was measured', 'were measured', 'determined', 'assessed', 'tested', 'performed',\n"
            "   • 'recorded', 'collected', 'obtained',\n"
            "   • 'available', 'included', 'reported' (when referring to baseline or follow-up laboratory values),\n"
            "   • or the test appears clearly as part of a tabulated list of baseline laboratory findings (e.g. “Table 1. Baseline laboratory parameters including PT, aPTT …”).\n\n"
            "3) IGNORE NON-MEASUREMENT MENTION:\n"
            "   • Do NOT count PT or aPTT if only mentioned in background—e.g., 'PT and aPTT are widely used to assess coagulation.'\n"
            "   • Do not infer measurement from listing as a general lab capability or guideline if not linked to study participants.\n"
            "   • LLM and human: Only flag as measured if description of actual lab testing on specific study samples appears in Methods/Results.\n\n"
            "PT (Prothrombin Time):\n"
            "----------------------\n"
            "Treat PT as measured if any of the following occurs in an appropriate section with measurement context:\n"
            "  - Full test names: 'prothrombin time', 'Quick prothrombin time', 'Quick test', 'Quick’s test'.\n"
            "  - Combined terms: 'PT/INR', 'PT‑INR', 'prothrombin time/INR', 'prothrombin time (PT)/international normalized ratio (INR)'.\n"
            "  - Abbreviations: 'prothrombin time (PT)' (→ subsequent 'PT'), 'PT (prothrombin time)'.\n"
            "  - Additional: 'prothrombin ratio', 'prothrombin activity' (especially if with 'Quick' or PT reagents).\n"
            "  - INR as proxy: If 'INR' is measured (without evidence that INR means something non-standard), this counts as PT measured since INR is derived from PT.\n"
            "  - PT-specific reagents: If a reagent below is named (+ appropriate verb), treat as PT measured, even if 'PT' not restated:\n"
            "    • Thromborel S (Dade/Siemens), Dade Innovin (Innovin), Neoplastin/STA‑Neoplastine family, STA‑NeoPTimal, Thrombotest, Normotest, RecombiPlasTin, "
            "Spinreact Prothrombin time reagent, Technoclot PT Owren, or any 'prothrombin time reagent containing thromboplastin.'\n"
            "  - Biochemical note: 'Thromboplastin' is a PT reagent, not aPTT. Only count aPTT if there is explicit mention of 'partial thromboplastin', 'aPTT', 'APTT', 'PTT' (clearly defined), or a specific aPTT reagent (see below).\n\n"
            "aPTT (Activated Partial Thromboplastin Time):\n"
            "--------------------------------------------\n"
            "Treat aPTT as measured ONLY IF any of these appear in a proper section with measurement context:\n"
            "  - Full names: 'activated partial thromboplastin time', 'partial thromboplastin time'.\n"
            "  - Abbreviations: 'aPTT', 'APTT', 'A‑PTT'.\n"
            "  - 'PTT' or 'partial thromboplastin time (PTT)' when the abbreviation is defined as such earlier in the article.\n"
            "  - Historical: 'kaolin‑cephalin clotting time', 'kaolin cephalin clotting time', 'KCCT'.\n"
            "  - aPTT-specific reagents: Dade Actin® reagents (all Actin APTT types), Pathromtin SL, STA-PTT Automate, STA Cephascreen, phrases like 'APTT reagent', 'activated PTT reagent'.\n"
            "    If any of these named plus measurement context → aPTT measured.\n"
            "  - If 'PTT' is only used and clearly defined as 'partial thromboplastin time', later occurrences with appropriate verbs count as aPTT measured.\n"
            "  - If 'PTT' is never defined, but found in a list with measurement verbs in Methods/Results, consider as aPTT measured if aLLM/human review finds context sufficient.\n"
            "  - *Never* count aPTT if the only word is 'thromboplastin' (without 'partial'), or if only PT reagent names appear.\n"
            "  - IGNORE background-only or generic mentions.\n\n"
            "IGNORE:\n"
            "  - Assume aPTT if only 'thromboplastin' or PT reagents are named.\n"
            "  - Assume both PT and aPTT were measured merely because one was.\n"
            "  - Guess: If there is no specific evidence in Methods/Results, leave null.\n\n"
            "APPLIES FOR ALL DOACS (overall and per drug):\n"
            "  - The rules above apply regardless of which DOACs (apixaban, rivaroxaban, edoxaban, betrixaban, dabigatran) are tested.\n"
            "  - Only fill this field if at least one of the explicit criteria is satisfied for a particular study or DOAC regimen."
        ),
    )
    coagulation_tests_concurrent_sentence_from_text: Optional[List[str]] = Field(
        default=None,
        alias="Conventional Coagulation Tests Concurrently Reported Sentence from Text",
        description="Exact sentences with the conventional coagulation tests concurrently reported.",
    )
    coagulation_tests_concurrent_confidence_score: int = Field(
        default=0,
        alias="Conventional Coagulation Tests Concurrently Reported Confidence Score",
        description="Confidence score for the conventional coagulation tests concurrently reported classification. A number between 0 and 100, where 0 is the lowest confidence and 100 is the highest confidence.",
        ge=0,
        le=100,
    )

    # Global Coagulation Testing
    global_coagulation_tests: Optional[
        List[
            Literal[
                "Viscoelastic testing (ROTEM/TEG)", "Thrombin Generation Assay (TGA)"
            ]
        ]
    ] = Field(
        default=None,
        alias="Global Coagulation Testing",
        description=(
            "CRITICAL: Scan the ENTIRE Methods section for global coagulation test terms. "
            "Include ONLY if explicitly described as performed on the same specimens as DOAC level measurement.\n\n"
            "Two-step process:\n"
            "Step 1 (Evidence): Quote exact sentences from Methods that describe which global coagulation tests were performed. "
            "Look for explicit descriptions of thrombin generation or viscoelastic testing.\n"
            "Step 2 (Decision): Based ONLY on those quoted sentences, classify the tests.\n\n"
            "SYNONYM MAP:\n"
            "• Thrombin generation / CAT / calibrated automated thrombography / thrombograms / TGA / "
            "  Technothrombin / Innovance ETP / ST Genesia "
            "  → 'Thrombin Generation Assay (TGA)'\n"
            "• TEG / thromboelastography / ROTEM / rotational thromboelastometry / viscoelastic testing / "
            "  ROTEM Delta / ROTEM Sigma / TEG 5000 / TEG 6s / Quantra / SEER Sonorheometry / ClotPro / "
            "  Sonoclot Analyzer "
            "  → 'Viscoelastic testing (ROTEM/TEG)'\n\n"
            "Include a test ONLY if:\n"
            "1) It is explicitly described in Methods as performed (not just mentioned in Discussion/Background).\n"
            "2) It was performed on the same specimens as DOAC level measurement.\n\n"
            "Common errors to avoid:\n"
            "• Missing thrombin generation (CAT) when explicitly described.\n"
            "• Misinterpreting manufacturer names (e.g., Technoclone) as evidence that thrombin generation or viscoelastic testing "
            "  was actually performed, without explicit description of the test.\n"
            "• Including tests mentioned only in Discussion/Background without Methods description.\n\n"
            "If the article does not clearly report which global tests were performed, leave null. Do NOT guess."
        ),
    )
    global_coagulation_tests_sentence_from_text: Optional[List[str]] = Field(
        default=None,
        alias="Global Coagulation Testing Sentence from Text",
        description="Exact sentences or paragraph containing the global coagulation tests.",
    )
    global_coagulation_tests_confidence_score: int = Field(
        default=0,
        alias="Global Coagulation Tests Confidence Score",
        description="Confidence score for the global coagulation tests classification. A number between 0 and 100, where 0 is the lowest confidence and 100 is the highest confidence.",
        ge=0,
        le=100,
    )

    model_config = ConfigDict(populate_by_name=True)


# ------------------------------------
# 4) Outcomes Blocks
# ------------------------------------
class ExtractionOutcomes(BaseModel):
    """
    Guidelines:
    1) Do not infer or guess.
    2) Use null if unsure.
    3) Output only facts explicitly in the text.
    4) If ambiguous, set null (do not guess).
    5) Numeric values must be exact.
    6) Resolve conflicts by the clearest statement (title→early pages; patients→methods/results).
    7) IGNORE external knowledge.
    8) Ignore Introduction/Background, References and Acknowledgments content.
    9) Focus on Methods and Results and Abstract sections.
    """

    # Timing of DOAC Level Measurement Relative to DOAC Intake
    timing_of_measurement: Optional[
        List[
            Literal[
                "Peak level (2–4 hours post-dose)",
                "Trough level (just prior to next dose)",
                "Random level",
                "Timing not reported",
            ]
        ]
    ] = Field(
        default=None,
        alias="Timing of DOAC level measurement relative to DOAC intake",
        description=(
            "Extract ONLY explicit information regarding the timing of DOAC level measurement relative to drug intake, as clearly described in the METHODS or RESULTS sections of the article. "
            "Completely disregard information from Introduction, Background, or references, even if the timing is discussed there, unless it is also unambiguously stated in Methods/Results.\n\n"
            "Principles:\n"
            "1) Extract the timing ONLY if it is directly described in the study's own Methods or Results section (not from Introduction, Background, Discussion, or external references)."
            " NEVER assign a timing category based merely on context provided for interpretation, general pharmacologic knowledge, or background comments.\n"
            "2) If a study involves urgent or emergent situations (such as urgent surgery), and the Methods/Results specify that samples were collected at the moment when care/intervention was required (i.e., as-needed, not according to a dosing interval), classify as 'Random level'."
            " For example, blood draws taken immediately prior to emergency surgery or clinical event should be considered 'Random', NOT 'Peak' nor 'Trough', even if the background or introduction describes typical timing definitions for those terms.\n"
            "3) Do NOT infer or assume timing from context, DOAC class, manufacturer recommendations, or pharmacokinetic patterns—RESTRICT to what is expressly described for sample collection in THIS study."
            " If explicit linkage to last or next dose is missing, and the timepoint was dictated by urgent clinical events, classify as 'Random level'.\n"
            "4) If timing information is described in both Methods and Results, always prioritize the more detailed Methods description. If both are present and equivalent, you may select based on either, but cite the Methods first if possible.\n"
            "5) For systematic reviews/meta-analyses, annotate timing only if the paper's Methods/Results specifically describe the timing categories for the included studies (e.g., 'X studies used trough samples, 2 used peak samples').\n\n"
            "Classification options and definitions:\n"
            "• 'Peak level (2–4 hours post-dose)': Select ONLY if the paper EXPLICITLY reports blood samples were collected within 2–4 hours after the last DOAC dose, with clear reference to both the time interval AND relation to dose (e.g., 'samples were obtained 3 hours post-dose'). NEVER assign based on background context about what a 'peak' is—require direct evidence that THIS sample was collected at peak.\n"
            "• 'Trough level (just prior to next dose)': Select ONLY if the paper EXPLICITLY states samples were collected just before the next scheduled dose, or uses synonymous terms like 'pre-dose', 'trough level', or intervals that clearly correspond to trough (e.g., '12 hours after last apixaban dose').\n"
            "• 'Random level': Use ONLY if the Methods/Results specify a clock time unrelated to dosing (e.g., 'samples collected from 8 to 10 am') with NO linkage to last/next dose, OR (especially for urgent clinical contexts) when samples are drawn according to immediate clinical need (e.g., for emergency surgery), OR when Methods/Results are ambiguous and do not allow assignment to 'peak' or 'trough'. Even if the background/intro mentions typical peak/trough times, do NOT assign those labels unless the actual sample collection in THIS study matches those,\n"
            "• 'Timing not reported': Use if NO explicit timing details regarding sample collection relative to DOAC intake are present in the Methods/Results—even if timing is alluded to elsewhere, or if only generic/unspecific statements exist.\n\n"
            "Strict IGNORE and edge cases:\n"
            "• IGNORE timing hints, patterns, or labels from Introduction, Background, Discussion, or references for this field unless they are explicitly and clearly restated in the Methods/Results. Contextual discussion does not count as evidence for classification.\n"
            "• Do NOT classify as 'peak' or 'trough' based on typical timing descriptions given for context or referenced literature—require confirmation that sample timing in YOUR study directly matched those definitions.\n"
            "• If the Methods/Results state the timing was based on clinical need (e.g., samples drawn immediately prior to urgent procedure), always select 'Random level'.\n"
            "• Do NOT attempt to classify as 'random' if there is clear evidence the sample was drawn at 'peak' or 'trough' (as defined above)—but DO assign 'random' if sample timing was dictated by ad hoc clinical situations.\n"
            "• Err on the side of reporting 'Timing not reported' if explicit detail is lacking or ambiguous rather than guessing or assuming a category.\n\n"
            "Best Practices:\n"
            "• If the paper studies multiple timings (e.g., both peak and trough), select ALL relevant options provided that each is explicitly described.\n"
            "• Quote the precise phrases from the Methods/Results supporting assignment of each selected category (in the companion field).\n"
            "• Remain conservative: if explicitness is in doubt, leave this field null or select 'Timing not reported'."
        ),
    )
    timing_of_measurement_sentence_from_text: Optional[List[str]] = Field(
        default=None,
        alias="Timing of DOAC Level Measurement Relative to DOAC Intake Sentence from Text",
        description="Exact sentences or paragraph containing the timing of DOAC level measurement relative to DOAC intake.",
    )
    timing_of_measurement_confidence_score: int = Field(
        default=0,
        alias="Timing of DOAC Level Measurement Relative to DOAC Intake Confidence Score",
        description="Confidence score for the timing of DOAC level measurement relative to DOAC intake classification. A number between 0 and 100, where 0 is the lowest confidence and 100 is the highest confidence.",
        ge=0,
        le=100,
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
            "Two-step process:\n"
            "Step 1 (Evidence): Directly quote exact sentences from the Methods/Results in which a specific numeric threshold is clearly defined or applied to this study's data, analysis, or procedures.\n"
            "Step 2 (Decision): Only assign a threshold if you find such a quoted sentence containing an explicit numeric threshold with units (e.g., '30 ng/mL', '50 ng/mL') in the eligible sections.\n\n"
            "INCLUDE a threshold if and only if ALL of the following are TRUE:\n"
            "• The numeric value AND units (e.g., 'ng/mL') are clearly stated.\n"
            "• The threshold is used to define eligibility, analysis groups, clinical actions, or results for THIS study.\n"
            "• The sentence (or table/figure legend) is from the Methods or Results of THIS manuscript (not from introduction, discussion, supplementary, or background/references).\n"
            "• The threshold is not merely a reference to an external guideline, prior study, or general literature. Apply only if the threshold is applied or explicitly discussed as relevant in THIS study context.\n\n"
            "Use 'Other' if a numeric threshold is applied in the study but is not exactly one of 30, 50, 75, or 100 ng/mL.\n\n"
            "IGNORE if:\n"
            "• The only reference is from the Introduction, Background, Discussion, or external sources.\n"
            "• The threshold is cited in the context of previous work with no evidence it was relevant or used in THIS study.\n"
            "• The value appears in the study only as a reference range, PK summary, manufacturer insert, or generic literature background.\n\n"
            "Be conservative: If you are not certain a threshold was directly listed and used in this study’s Methods/Results, LEAVE THIS FIELD NULL. Err on the side of under-reporting, not over-reporting."
        ),
    )
    thresholds_listed_confidence_score: int = Field(
        default=0,
        alias="Reported DOAC concentration thresholds/cutoffs (listed) Confidence Score",
        description="Confidence score for the reported DOAC concentration thresholds/cutoffs (listed) classification. A number between 0 and 100, where 0 is the lowest confidence and 100 is the highest confidence.",
        ge=0,
        le=100,
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
            "to evaluate associations with clinical outcomes. Distinguish between:\n"
            "• Clinical MANAGEMENT = thresholds used to guide care (surgery timing, reversal, thrombolysis eligibility)\n"
            "• Clinical OUTCOMES = thresholds used to evaluate associations (bleeding risk, thrombosis risk)\n\n"
            "Two-step process:\n"
            "Step 1 (Evidence): Quote exact sentences from Methods/Results that describe how the threshold was used "
            "to guide clinical decisions. Look for explicit statements like:\n"
            "  - 'Surgery was delayed if level >30 ng/mL'\n"
            "  - 'Thrombolysis was withheld if level exceeded 50 ng/mL'\n"
            "  - 'Reversal was administered when level was >30 ng/mL'\n"
            "  - 'Patients with level <50 ng/mL proceeded to surgery'\n"
            "Step 2 (Decision): Based ONLY on those quoted sentences, classify the threshold × context pair.\n\n"
            "Include a threshold × context pair ONLY if:\n"
            "1) The manuscript explicitly states the threshold was applied to guide clinical decisions "
            "   (surgery timing, reversal administration, thrombolysis eligibility, dose adjustment, etc.).\n"
            "2) The threshold was used in actual clinical decision-making, not just for analysis/performance evaluation.\n\n"
            "IGNORE thresholds if:\n"
            "• They are used purely for analysis/performance (e.g., ROC cut-offs, sensitivity/specificity calculations).\n"
            "• They are used to evaluate associations with clinical outcomes (e.g., 'bleeding risk was higher at levels >100 ng/mL') "
            "   → These are outcome associations, not management decisions.\n"
            "• They are mentioned only as background or hypothetical thresholds without explicit application to clinical decisions.\n"
            "• They are proposed but not actually used to guide care in the study.\n\n"
            "Context categories:\n"
            "• 'Overall' = threshold used for general clinical management without specific context\n"
            "• 'Elective surgery' = threshold used to guide timing/clearance for planned procedures\n"
            "• 'Emergency surgery' = threshold used to guide proceed/cancel decisions for urgent procedures\n"
            "• 'Major bleeding and anticoagulation reversal' = threshold used to guide reversal administration\n"
            "• 'Thrombolysis/acute stroke' = threshold used to determine lytic eligibility\n\n"
            "If the article does not clearly state that thresholds were used to inform clinical management, leave null. Do NOT guess."
        ),
    )
    thresholds_used_for_management_sentence_from_text: Optional[List[str]] = Field(
        default=None,
        alias="Thresholds used to inform clinical management Sentence from Text",
        description="Exact sentences or paragraph confirming that the thresholds were used to inform clinical management.",
    )
    thresholds_used_for_management_confidence_score: int = Field(
        default=0,
        alias="Thresholds used to inform clinical management Confidence Score",
        description="Confidence score for the thresholds used to inform clinical management classification. A number between 0 and 100, where 0 is the lowest confidence and 100 is the highest confidence.",
        ge=0,
        le=100,
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
            "Two-step process:\n"
            "Step 1 (Evidence): Search Methods and Results sections ONLY (NOT Introduction, Abstract, or Discussion). "
            "Quote exact sentences that state the study recorded/assessed/evaluated clinical events.\n"
            "Step 2 (Decision): Based ONLY on those quoted sentences, classify.\n\n"
            "Set to 'Yes' ONLY if BOTH conditions are met:\n"
            "1) The Methods explicitly state that clinical events were recorded/assessed/evaluated as outcomes "
            "   (look for phrases like 'we recorded', 'we assessed', 'we evaluated', 'we defined events as...', "
            "   'primary/secondary endpoints', 'outcomes included').\n"
            "2) The Results section reports actual clinical events or explicitly states 'no events occurred'.\n\n"
            "Set to 'No' if:\n"
            "• Outcomes are mentioned only in Introduction/Background (e.g., 'AF is associated with increased stroke risk').\n"
            "• Outcomes are from an underlying registry or external trial, not THIS study.\n"
            "• The study describes planned follow-up but no actual events are reported in Results.\n"
            "• Only baseline characteristics or risk factors are discussed, not actual outcomes.\n\n"
            "CONSISTENCY RULE: If this field = 'No', then ALL outcome-related fields (clinical_outcomes, "
            "clinical_outcome_followup_flat, clinical_outcome_definition_flat) MUST be null/NA.\n\n"
            "If unclear after checking Methods and Results, set to null and leave all outcome-related fields null."
        ),
    )
    clinical_outcomes_measured_confidence_score: int = Field(
        default=0,
        alias="Clinical Outcomes Measured Confidence Score",
        description="Confidence score for the clinical outcomes measured classification. A number between 0 and 100, where 0 is the lowest confidence and 100 is the highest confidence.",
        ge=0,
        le=100,
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
            "Step 2 (Decision): Based ONLY on those quoted sentences, classify the outcome type.\n\n"
            "Include an outcome ONLY if:\n"
            "1) The Methods explicitly states it was recorded/assessed/evaluated as an outcome.\n"
            "2) The Results section reports actual events OR explicitly states 'no events occurred'. Focus more on the Results section than the Methods section.\n\n"
            "IGNORE outcomes if:\n"
            "• They appear only in Introduction/Background (e.g., 'AF is associated with increased stroke risk').\n"
            "• They are from an underlying registry or external trial, not THIS study.\n"
            "• Only baseline descriptions or planned follow-up are mentioned without actual events in Results.\n"
            "• Generic risk statements exist without explicit outcome measurement.\n\n"
            "If no clinical outcomes were measured (gate = 'No'), leave this field null."
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
            "Two-step process:\n"
            "Step 1 (Evidence): Quote exact sentences from Methods AND Results (NOT Introduction/Discussion) "
            "that explicitly describe how long patients were followed for clinical events. "
            "Look for phrases like 'Patients were followed for X...', 'Follow-up period was X...', "
            "'Observation period of X...', 'Outcomes were assessed at X...'.\n"
            "Step 2 (Decision): Based ONLY on those quoted sentences, classify the follow-up duration.\n\n"
            "Include a follow-up duration ONLY if:\n"
            "1) The outcome was explicitly measured (see 'Clinical outcomes' field).\n"
            "2) There is an explicit description of follow-up duration in Methods or Results "
            "   (e.g., 'Patients were followed for 6 months...', 'Follow-up was 30 days...').\n\n"
            "IGNORE follow-up duration if:\n"
            "• The study mentions imaging or days of observation but does NOT explicitly state follow-up for clinical events.\n"
            "• Follow-up is inferred from a different cohort (e.g., underlying registry) rather than THIS study.\n"
            "• Only baseline characteristics or planned follow-up are mentioned without explicit duration for outcome ascertainment.\n"
            "• The duration is mentioned in Introduction/Discussion but not in Methods/Results.\n\n"
            "If duration is not explicitly reported for an outcome, do NOT select any value for that outcome. "
            "If multiple outcomes have different durations, include multiple literals.\n\n"
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


# ------------------------------------
# 5) Diagnostic Performance Metrics
# ------------------------------------
class ExtractionDiagnosticPerformance(BaseModel):
    """
    Guidelines:
    1) Do not infer or guess.
    2) Use null if unsure.
    3) Output only facts explicitly in the PDF.
    4) If ambiguous, set null (do not guess).
    5) Numeric values must be exact.
    6) Resolve conflicts by the clearest statement (title→early pages; patients→methods/results).
    7) IGNORE external knowledge.
    8) Ignore Introduction/Background, References and Acknowledgments content.
    9) Focus on Methods and Results and Abstract sections.
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
            "CRITICAL: Only populate if the study reports diagnostic performance metrics for categorical cutoffs "
            "(e.g., ≥30 ng/mL vs <30 ng/mL) comparing a comparator assay to DOAC level measurement.\n\n"
            "Two-step process:\n"
            "Step 1 (Evidence): Quote exact sentences from Methods/Results that report sensitivity, specificity, "
            "PPV, or NPV for categorical cutoffs comparing comparator assays (PT, aPTT, TT, dTT, heparin-calibrated anti-Xa, "
            "viscoelastic testing, thrombin generation) to DOAC level thresholds.\n"
            "Step 2 (Decision): Based ONLY on those quoted sentences, classify which metrics were reported.\n\n"
            "Include a metric ONLY if:\n"
            "1) It is explicitly reported in Results (not just mentioned in Discussion/Background).\n"
            "2) It compares a comparator assay to a DOAC level threshold (e.g., 'sensitivity of PT >1.2× normal "
            "for detecting DOAC level ≥30 ng/mL was 85%').\n\n"
            "Common comparator assays:\n"
            "• Conventional coagulation tests: PT, aPTT, TT, dTT\n"
            "• Heparin-calibrated anti-Xa assays (IU/mL)\n"
            "• Viscoelastic testing (ROTEM/TEG)\n"
            "• Thrombin generation assays (TGA)\n\n"
            "IGNORE if:\n"
            "• Metrics are reported only for assay validation (e.g., LC-MS vs calibrated anti-Xa) without categorical cutoffs.\n"
            "• Only correlation coefficients are reported (those belong in 'Diagnostic Performance Metrics - Continuous Relationships').\n"
            "• Metrics are mentioned in Discussion but not explicitly reported in Results.\n\n"
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
            ]
        ]
    ] = Field(
        default=None,
        alias="Diagnostic Performance Metrics - Continuous Relationships",
        description=(
            "CRITICAL: Only populate if the study reports correlation coefficients comparing a comparator assay "
            "to DOAC level measurement as continuous variables.\n\n"
            "Two-step process:\n"
            "Step 1 (Evidence): Quote exact sentences from Methods/Results that report Spearman or Pearson "
            "correlation coefficients comparing comparator assays (PT, aPTT, TT, dTT, heparin-calibrated anti-Xa, "
            "viscoelastic testing, thrombin generation) to DOAC levels as continuous variables.\n"
            "Step 2 (Decision): Based ONLY on those quoted sentences, classify which correlation coefficient was reported.\n\n"
            "Include a correlation coefficient ONLY if:\n"
            "1) It is explicitly reported in Results with a numeric value (not just mentioned in Discussion/Background).\n"
            "2) It compares a comparator assay to DOAC levels as continuous variables (e.g., 'Spearman correlation "
            "between PT and rivaroxaban level was 0.65').\n\n"
            "Common comparator assays:\n"
            "• Conventional coagulation tests: PT, aPTT, TT, dTT\n"
            "• Heparin-calibrated anti-Xa assays (IU/mL)\n"
            "• Viscoelastic testing (ROTEM/TEG)\n"
            "• Thrombin generation assays (TGA)\n\n"
            "IGNORE if:\n"
            "• Only categorical metrics (sensitivity/specificity) are reported (those belong in 'Diagnostic Performance Metrics - Categorical Cutoffs').\n"
            "• Correlation is mentioned qualitatively without a numeric coefficient.\n"
            "• Correlation is mentioned in Discussion but not explicitly reported in Results.\n\n"
            "If the article does not clearly report continuous correlation coefficients, leave null. Do NOT guess."
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
            "CRITICAL: Only populate if the study reports diagnostic performance metrics comparing comparator assays "
            "to DOAC level measurement. This includes BOTH categorical cutoffs (sensitivity, specificity, PPV, NPV) "
            "AND continuous relationships (Spearman/Pearson correlation coefficients).\n\n"
            "Two-step process:\n"
            "Step 1 (Evidence): Quote exact sentences from Methods/Results that identify which comparator assays were evaluated. "
            "Look for:\n"
            "  - Categorical cutoffs: 'sensitivity of PT >1.2× normal for detecting DOAC level ≥30 ng/mL', "
            "'specificity of aPTT >40s for detecting DOAC level ≥50 ng/mL'\n"
            "  - Continuous relationships: 'Spearman correlation between PT and rivaroxaban level was 0.65', "
            "'Pearson correlation coefficient for aPTT vs apixaban concentration was 0.72'\n"
            "Step 2 (Decision): Based ONLY on those quoted sentences, classify which comparator assays were used.\n\n"
            "Include a comparator assay ONLY if:\n"
            "1) It is explicitly identified in Methods/Results as being evaluated for diagnostic performance.\n"
            "2) Diagnostic performance metrics are reported for that comparator assay:\n"
            "   - Categorical: sensitivity, specificity, PPV, or NPV for categorical cutoffs\n"
            "   - Continuous: Spearman or Pearson correlation coefficient\n"
            "3) The comparison is to DOAC level measurement (not assay validation like LC-MS vs calibrated anti-Xa).\n\n"
            "Comparator assay categories:\n"
            "• 'Coagulation testing - Prothrombin time (PT)' = PT/INR used as comparator\n"
            "• 'Coagulation testing - Activated partial thromboplastin time (aPTT)' = aPTT used as comparator\n"
            "• 'Coagulation testing - Dilute thrombin time (dTT)' = dTT used as comparator (for dabigatran)\n"
            "• 'Coagulation testing - Thrombin Time (TT)' = TT used as comparator (for dabigatran)\n"
            "• 'Anti-Xa assays with LMWH calibrators (IU/mL)' = Heparin-calibrated anti-Xa assays (not DOAC-specific) used as comparator\n"
            "• 'Viscoelastic testing' = ROTEM/TEG/viscoelastic testing used as comparator\n"
            "• 'Thrombin generation assays' = TGA/CAT/thrombin generation used as comparator\n\n"
            "IGNORE if:\n"
            "• Comparator assays are mentioned but no diagnostic performance metrics are reported.\n"
            "• The comparison is for assay validation (e.g., LC-MS vs calibrated anti-Xa) without diagnostic performance metrics.\n"
            "• Only qualitative statements about correlation exist without numeric metrics.\n\n"
            "If the article does not clearly identify which comparator assays were used for diagnostic performance evaluation, leave null. Do NOT guess."
        ),
    )
    comparator_assays_sentence_from_text: Optional[List[str]] = Field(
        default=None,
        alias="Comparator Assays Sentence from Text",
        description="Exact sentences or paragraph identifying which comparator assays were used for diagnostic performance evaluation.",
    )

    model_config = ConfigDict(populate_by_name=True)
