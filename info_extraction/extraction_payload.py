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
            "CRITICAL: Classify based on the PRIMARY goal of the study by matching the best-fitting design type.\n\n"
            "Two-step process:\n"
            "Step 1 (Evidence): Quote exact sentences from Title/Abstract/Methods that describe the study design or primary goal.\n"
            "Step 2 (Decision): Based ONLY on those quoted sentences, match the study to the best-fitting design type below using the keywords and abstract features as cues.\n\n"
            "STUDY DESIGN DEFINITIONS WITH LLM CUES:\n\n"
            "1) Randomized Controlled Trial (RCT) - Experimental design where patients are randomly assigned to interventions (e.g., different DOAC dosing strategies or reversal protocols) to evaluate outcomes such as bleeding or thromboembolism.\n"
            "   LLM cues:\n"
            "   • Keywords: randomized, double-blind, placebo-controlled, parallel group, allocation, trial registration.\n"
            "   • Abstract features: mentions randomization, intervention, control arm, intention-to-treat, primary endpoint.\n\n"
            "2) Cohort Study - Observational study that follows a group of patients on DOACs over time, comparing outcomes across exposure levels (e.g., low vs high plasma concentrations).\n"
            "   LLM cues:\n"
            "   • Keywords: prospective cohort, retrospective cohort, follow-up, incidence, outcome comparison, registry.\n"
            "   • Abstract features: followed for X months/years, time-to-event, hazard ratio, baseline characteristics.\n\n"
            "3) Non-Randomized Experimental Study - Interventional design without randomization- e.g., pilot studies adjusting DOAC dose based on plasma level or evaluating perioperative protocols.\n"
            "   LLM cues:\n"
            "   • Keywords: single-arm, non-randomized, open-label, pilot intervention, dose adjustment, protocol evaluation.\n"
            "   • Abstract features: intervention applied to all participants; lacks control group but tests feasibility or outcomes.\n\n"
            "4) Non-Randomized Observational Study - Broad category including registry analyses and chart reviews describing DOAC level testing and related outcomes.\n"
            "   LLM cues:\n"
            "   • Keywords: observational, registry, chart review, real-world, clinical practice, retrospective analysis.\n"
            '   • Abstract features: no assigned intervention; observational tone; phrases like "data were collected" or "reviewed medical records."\n\n'
            "5) Cross-Sectional Study - Snapshot design assessing DOAC levels and clinical/lab parameters at a single time point to describe variability or correlates.\n"
            "   LLM cues:\n"
            "   • Keywords: cross-sectional, point prevalence, single time point, surveyed, baseline measurements.\n"
            '   • Abstract features: lacks longitudinal component; uses "assessed at baseline" or "measured once."\n\n'
            "6) Case-Control Study - Retrospective comparison of patients with and without an outcome (e.g., major bleeding) to evaluate associations with DOAC levels or drug interactions.\n"
            "   LLM cues:\n"
            "   • Keywords: case-control, matched controls, odds ratio, retrospective comparison, risk factors.\n"
            '   • Abstract features: phrases like "cases were matched to controls", "identified patients with", "association tested."\n\n'
            "7) Pharmacokinetic Study - Quantitative assessment of DOAC absorption, distribution, metabolism, and excretion in clinical populations (not healthy volunteers).\n"
            "   LLM cues:\n"
            "   • Keywords: pharmacokinetic, PK analysis, Cmax, AUC, half-life, LC-MS, chromogenic anti-Xa.\n"
            "   • Abstract features: structured PK terminology, plasma concentration–time curves, sampling at trough/peak.\n\n"
            "8) In Silico Simulation Analysis - Computational modeling or virtual population simulation predicting DOAC plasma concentrations, dose-response, or outcome risk.\n"
            "   LLM cues:\n"
            "   • Keywords: modeling, simulation, population PK/PD model, Monte Carlo, physiologically-based pharmacokinetic (PBPK).\n"
            '   • Abstract features: simulation-based methodology, phrases like "virtual cohort," "simulated concentrations," "parameter estimation."\n\n'
            "9) Systematic Review - Structured synthesis using predefined search and inclusion criteria; may include meta-analysis of DOAC level–outcome relationships.\n"
            "   LLM cues:\n"
            "   • Keywords: systematic review, meta-analysis, pooled analysis, PRISMA, literature search.\n"
            '   • Abstract features: "We searched MEDLINE/EMBASE", "studies were included if", "data were pooled."\n\n'
            "10) Qualitative Research - Explores clinician or patient perceptions regarding DOAC testing, barriers, or implementation strategies.\n"
            "    LLM cues:\n"
            "    • Keywords: qualitative, interviews, focus groups, thematic analysis, perceptions, attitudes.\n"
            '    • Abstract features: non-numeric outcomes, narrative findings, mentions of "themes" or "framework analysis."\n\n'
            "11) Diagnostic Test Accuracy Study - Assesses performance of DOAC assays (e.g., anti-Xa vs LC-MS) using sensitivity, specificity, and ROC analyses.\n"
            "    LLM cues:\n"
            "    • Keywords: sensitivity, specificity, ROC curve, AUC, agreement, validation, reference standard.\n"
            "    • Abstract features: comparison between two assays; statistical test performance metrics.\n\n"
            "12) Case Series - Descriptive summaries of multiple patients where DOAC levels were measured for management decisions (e.g., perioperative bleeding).\n"
            "    LLM cues:\n"
            "    • Keywords: case series, clinical experience, retrospective report, N = small number (<20).\n"
            "    • Abstract features: several case descriptions; no control group; summary tables of individual patient data.\n\n"
            "13) Case Report - Detailed single-patient description illustrating unique clinical use or pharmacokinetic observation related to DOAC levels.\n"
            "    LLM cues:\n"
            "    • Keywords: case report, single patient, present a case, we describe, rare event.\n"
            "    • Abstract features: single subject; anecdotal tone; structured sections (background, case, discussion).\n\n"
            "14) Other - Hybrid or methodological studies not fitting standard designs, e.g., assay validation, modeling linked to limited clinical data, or mixed-methods frameworks.\n"
            "    LLM cues:\n"
            "    • Keywords: validation, analytical performance, method development, mixed methods, technical note.\n"
            "    • Abstract features: focus on assay technique, algorithm development, or commentary integrating quantitative and qualitative elements.\n\n"
            "CLASSIFICATION INSTRUCTIONS:\n"
            "Review all 14 design types above and select the one that best matches the study based on the keywords and abstract features present in the quoted evidence. "
            "Match the design type that most closely aligns with the study's primary goal and methodology as described in Title/Abstract/Methods.\n\n"
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
    study_design_confidence_score: Optional[int] = Field(
        default=None,
        alias="Study Design Confidence Score",
        description="Confidence score for the study design classification. How confident is the model in the classification? A number between 0 and 100, where 0 is the lowest confidence and 100 is the highest confidence.",
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
        description="Total number of patients that were included in the actual study and not just mentioned in the Introduction/Background.",
    )
    total_patients_sentence_from_text: Optional[str] = Field(
        default=None,
        alias="Patient Population Sentence from Text",
        description="Exact sentences or paragraph containing the total patients that were included in the actual study.",
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
            "Subgroup-specific criteria with LLM cues (all require explicit restriction/analysis, NOT just keywords):\n\n"
            "1) High body weight (obesity)\n"
            '   • Positive keywords: obesity; obese; high body weight; BMI ≥30, ≥35, ≥40 kg/m²; morbid/severe obesity; weight >120 kg; "extreme body weight"; "super-obese".\n'
            '   • Signals: dosing in obesity; "on-treatment concentrations in obese patients"; "anti-Xa calibration in high BMI".\n'
            '   • Exclusions: "weight‐adjusted dose" with no level data; obesity only in baseline table.\n'
            "   • Edge cases: post-bariatric obesity → classify here and bariatric if both are explicitly analyzed.\n\n"
            "2) Low body weight\n"
            "   • Positive keywords: low body weight; underweight; ≤60 kg, <50 kg, ≤45 kg; cachexia; sarcopenia.\n"
            "   • Signals: reduced dose criteria met due to weight; level comparisons by ≤60 vs >60 kg.\n"
            "   • Exclusions: dose label criteria mentioned but no levels.\n\n"
            "3) Chronic kidney disease/dialysis\n"
            "   • Positive keywords: CKD; chronic renal impairment; eGFR, CrCl (Cockcroft-Gault), KDIGO stages; ESRD, ESKD; hemodialysis, peritoneal dialysis.\n"
            '   • Signals: trough/peak levels by renal strata; "accumulation"; dialysis timing vs level; dialyzability.\n'
            '   • Exclusions: creatinine reported without renal stratification; anti-Xa "activity" not calibrated to DOAC.\n\n'
            "4) Bariatric surgery/malabsorption\n"
            '   • Positive keywords: bariatric; Roux-en-Y, sleeve gastrectomy, gastric bypass, biliopancreatic diversion, duodenal switch; short-bowel; celiac; Crohn\'s with resection; malabsorption; "altered absorption".\n'
            "   • Signals: pre-/post-op DOAC levels; AUC/peak comparisons; time since surgery.\n"
            "   • Exclusions: perioperative thromboprophylaxis without DOAC levels.\n\n"
            "5) Drug–DOAC pharmacokinetic interactions\n"
            '   • Positive keywords: P-glycoprotein (P-gp), CYP3A4 inhibitors/inducers; "DDI", "drug interaction"; comedications affecting DOAC exposure.\n'
            "   • Inhibitors list: amiodarone, verapamil, diltiazem, dronedarone, ketoconazole, itraconazole, posaconazole, voriconazole, ritonavir/cobicistat, clarithromycin, erythromycin, azole antifungals, cyclosporine, tacrolimus.\n"
            "   • Inducers list: rifampin, carbamazepine, phenytoin, phenobarbital, primidone, St. John's wort.\n"
            "   • Signals: level shift with the comedication present vs absent; dose adjustment with measured levels.\n"
            "   • Exclusions: claims-data bleeding risk without levels.\n\n"
            "6) Advanced age/frailty\n"
            '   • Positive keywords: elderly; ≥75, ≥80, octogenarian, nonagenarian; "advanced age"; "geriatric"; frailty, Clinical Frailty Scale, Rockwood, HFRS.\n'
            "   • Signals: levels by age strata; frailty index vs levels; dose-reduction criteria age component analyzed with levels.\n"
            "   • Exclusions: age only in baseline.\n\n"
            "7) Elective procedure/surgery\n"
            "   • Positive keywords: elective surgery; planned invasive procedure; neuraxial anesthesia; perioperative management; hold time, residual level threshold (e.g., 30 or 50 ng/mL) before procedure.\n"
            "   • Signals: pre-op DOAC levels guiding timing; correlation of level with bleeding in elective setting.\n"
            "   • Exclusions: protocols without actual measured pre-op levels.\n\n"
            "8) Urgent/emergent procedure/surgery\n"
            "   • Positive keywords: urgent surgery; emergent operation; trauma surgery; unplanned procedure; hip fracture surgery within 24–48 h; emergency endoscopy.\n"
            "   • Signals: rapid level testing; decision to proceed based on level; time-to-surgery vs level.\n"
            "   • Exclusions: emergent procedures described without any level measurement or level-guided decision-making.\n\n"
            "9) Acute stroke/thrombolysis\n"
            '   • Positive keywords: acute ischemic stroke; thrombolysis; alteplase, tenecteplase; rtPA, tPA; mechanical thrombectomy; "lytic eligibility"; "safe level for lysis"; "residual DOAC concentration".\n'
            "   • Signals: threshold levels used to qualify for lysis; association of levels with hemorrhagic transformation or outcomes; use of calibrated anti-Xa or LC-MS/MS in stroke protocol.\n"
            "   • Exclusions: stroke registry data without measured DOAC levels; thrombolysis outcomes reported without level quantification; hypothetical modeling of thresholds; review or guideline papers.\n\n"
            "10) DOAC-associated bleeding + DOAC reversal\n"
            '    • Positive keywords: major bleeding; life-threatening bleeding; intracranial hemorrhage; gastrointestinal bleed; retroperitoneal bleed; andexanet alfa; idarucizumab; PCC; aPCC; ciraparantag; "reversal".\n'
            "    • Signals: level at presentation; pre- and post-reversal levels; correlation between baseline concentration and hemostatic efficacy; quantified residual level after reversal.\n"
            "    • Exclusions: studies of bleeding or reversal without DOAC level measurement; in vitro or animal-only models; single case reports lacking numeric level data; non-DOAC reversal (e.g., warfarin, heparin).\n\n"
            "11) Genetic polymorphism (e.g., CYP polymorphism)\n"
            "    • Positive keywords: pharmacogenetics; pharmacogenomics; genetic polymorphism; single nucleotide polymorphism; SNP; genotype; allele; rs identifiers; CYP3A4, CYP3A5, CYP2J2, ABCB1 (P-gp), CES1, UGT, SLCO1B1.\n"
            "    • Signals: measured DOAC concentrations stratified by genotype; associations between genotype and PK metrics (AUC, trough, peak, clearance); genotype as determinant of level variability.\n"
            "    • Exclusions: genotyping without DOAC level data; simulations or models without patient measurement; review-only papers; animal or cell-based studies.\n\n"
            "If ambiguous or no explicit restriction/analysis exists, leave null. IGNORE guessing based on keywords alone."
        ),
    )
    relevant_subgroups_sentence_from_text: Optional[List[str]] = Field(
        default=None,
        alias="Relevant Subgroups Sentence from Text",
        description="Exact sentences or paragraph containing the relevant subgroups.",
    )
    relevant_subgroups_confidence_score: Optional[int] = Field(
        default=None,
        alias="Relevant Subgroups Confidence Score",
        description="Confidence score for the relevant subgroups classification. How confident is the model in the classification? A number between 0 and 100, where 0 is the lowest confidence and 100 is the highest confidence.",
    )

    # Indications for DOAC level measurement
    indications_for_doac_level_measurement: Optional[
        List[
            Literal[
                "Confirm adherence",
                "Evaluate DOAC level exposure",
                "Evaluate DOAC level exposure - Bariatric surgery",
                "Evaluate DOAC level exposure - Drug-DOAC interaction",
                "Evaluate DOAC level exposure - Chronic kidney failure",
                "Evaluate DOAC level exposure - Obesity",
                "Evaluate DOAC level exposure - Residual DOAC level after elective interruption",
                "Identify predictors of DOAC level exposure",
                "Identify predictors of DOAC level exposure - Cmax, Ctrough, AUC",
                "Guide clinical decision-making",
                "Guide clinical decision-making - Urgent surgery",
                "Guide clinical decision-making - Major bleeding and reversal agent administration",
                "Guide clinical decision-making - Thrombolysis",
                "Guide clinical decision-making - Guide dose adjustment",
                "Measure correlation with other laboratory techniques",
                "Measure correlation with other laboratory techniques - Conventional coagulation testing (e.g., prothrombin time)",
                "Measure correlation with other laboratory techniques - HPLC-MS vs calibrated anti-Xa measurement",
                "Risk prediction and clinical outcome association",
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
            "Step 2 (Decision): Based ONLY on those quoted sentences, classify the indication(s). "
            "CRITICAL RULE FOR MAIN CATEGORIES VS SUBCATEGORIES: "
            "For each category group (e.g., 'Evaluate DOAC level exposure' and its subcategories), you MUST select EITHER the main category OR its subcategory(ies), NEVER BOTH. "
            "If ANY subcategory applies (e.g., 'Evaluate DOAC level exposure - Bariatric surgery'), select ONLY that subcategory and DO NOT select the main category (e.g., 'Evaluate DOAC level exposure'). "
            "Only select the main category if NO subcategory applies to the study. "
            "This rule applies to all category groups: "
            "'Evaluate DOAC level exposure' vs its subcategories (2a-2e), "
            "'Identify predictors of DOAC level exposure' vs 'Cmax, Ctrough, AUC' (3a), "
            "'Guide clinical decision-making' vs its subcategories (4a-4d), "
            "'Measure correlation with other laboratory techniques' vs its subcategories (5a-5b), "
            "'Risk prediction and clinical outcome association' vs its subcategories (6a-6b).\n\n"
            "Include an indication ONLY if:\n"
            "1) It is explicitly stated in Methods/Results (NOT just mentioned in passing in Introduction/Discussion).\n"
            "2) Patient samples were actually quantified in THIS study (not simulations, not external registries).\n"
            "3) It is central to the study objectives, not mentioned in passing.\n\n"
            "Do NOT over-label. Common errors to avoid:\n"
            "• Marking multiple overlapping indications (e.g., 'bleeding risk', 'thrombosis', 'CKD') when the study "
            "  is simply 'evaluate DOAC exposure/assay performance'.\n"
            "• Including indications mentioned only in Background/Discussion without explicit measurement purpose.\n"
            "• Inferring indications from baseline characteristics without explicit measurement rationale.\n"
            "• Selecting both a main category and its subcategory - if a subcategory applies, select ONLY the subcategory, NOT the main category.\n\n"
            "INDICATION-SPECIFIC CRITERIA WITH LLM CUES:\n\n"
            "1) Confirm adherence\n"
            '   • Positive keywords: adherence; compliance; persistence; medication adherence; missed dose; "verify adherence"; "confirm drug intake"; "confirm last intake"; "determine if patient took DOAC"; "evaluate compliance using plasma concentration."\n'
            "   • Signals: DOAC levels used to confirm or refute recent ingestion; trough/undetectable levels interpreted as non-adherence; comparison of self-report vs measured level.\n"
            "   • Exclusions: adherence inferred from questionnaires, prescription refill, or pill count only; discussion of adherence without measured concentration.\n\n"
            "2) Evaluate DOAC level exposure (main category - use ONLY if none of subcategories 2a-2e apply)\n"
            '   • Positive keywords (general): pharmacokinetic evaluation; drug exposure; variability in plasma concentration; on-treatment levels; steady-state levels; "evaluate exposure to DOACs."\n'
            "   • Signals: measured DOAC levels reported to assess typical or altered exposure under specific conditions.\n"
            "   • Exclusions: studies modeling exposure without patient data; population PK simulations only; reviews summarizing prior exposure data.\n"
            "   • IMPORTANT: If the study fits any subcategory (2a-2e), select ONLY that subcategory and do NOT select this main category.\n\n"
            "2a) Evaluate DOAC level exposure - Bariatric surgery\n"
            "   • Positive keywords: bariatric; Roux-en-Y; sleeve gastrectomy; gastric bypass; biliopancreatic diversion; duodenal switch; short-bowel; malabsorption.\n"
            "   • Signals: comparison of pre-/post-surgery DOAC levels; AUC/peak/trough measurement after bariatric procedures; exposure change over time after surgery.\n"
            "   • Exclusions: bariatric cohorts without measured levels; pharmacologic dosing discussions without plasma concentration data.\n\n"
            "2b) Evaluate DOAC level exposure - Drug-DOAC interaction\n"
            "   • Positive keywords: drug interaction; DDI; P-glycoprotein (P-gp); CYP3A4/5 inhibitors or inducers; comedications (amiodarone, verapamil, ketoconazole, rifampin, etc.).\n"
            "   • Signals: measured DOAC levels compared between patients with and without interacting drugs; level change correlated with co-therapy presence.\n"
            "   • Exclusions: interaction risk inferred from prescribing data only; no plasma level data.\n\n"
            "2c) Evaluate DOAC level exposure - Chronic kidney failure\n"
            '   • Positive keywords: CKD; renal impairment; ESRD; hemodialysis; eGFR; CrCl; renal dysfunction; "kidney failure."\n'
            "   • Signals: levels measured across renal function strata; evaluation of accumulation or clearance; exposure compared by renal stage.\n"
            "   • Exclusions: renal function reported but no stratified level data; simulation models without direct measurement.\n\n"
            "2d) Evaluate DOAC level exposure - Obesity\n"
            "   • Positive keywords: obesity; high BMI; morbid obesity; weight >120 kg; BMI ≥ 40 kg/m².\n"
            "   • Signals: measured levels or AUC compared by BMI/weight group; exposure or concentration-time profiles analyzed in obese cohort.\n"
            "   • Exclusions: obesity only noted as baseline descriptor; no level analysis.\n\n"
            "2e) Evaluate DOAC level exposure - Residual DOAC level after elective interruption\n"
            '   • Positive keywords: residual level; elective surgery; pre-operative; perioperative; drug interruption; "hold time"; "timing of last dose."\n'
            "   • Signals: measured pre-procedure DOAC levels after planned interruption; determination of safe residual concentration (<30–50 ng/mL) before elective intervention.\n"
            "   • Exclusions: surgical timing protocols without actual level measurement; modeled pharmacokinetics only.\n\n"
            "3) Identify predictors of DOAC level exposure (main category - use ONLY if subcategory 3a does not apply)\n"
            "   • Positive keywords: predictors; determinants; covariates; factors influencing levels; regression analysis; variability; exposure predictors.\n"
            "   • Signals: multivariable or correlation analysis linking demographics, renal function, body weight, age, or genetics to DOAC levels.\n"
            "   • Exclusions: predictors of bleeding or thrombosis only (without concentration analysis); descriptive level summaries without predictor analysis.\n"
            "   • IMPORTANT: If the study fits subcategory 3a (Cmax, Ctrough, AUC), select ONLY that subcategory and do NOT select this main category.\n\n"
            "3a) Identify predictors of DOAC level exposure - Cmax, Ctrough, AUC\n"
            '   • Positive keywords: Cmax; Ctrough; AUC; Tmax; "area under the curve"; "steady-state concentration"; "PK profile."\n'
            "   • Signals: direct calculation or reporting of these pharmacokinetic parameters; time-concentration curves.\n"
            "   • Exclusions: papers referencing Cmax/AUC from product labels or models only; no actual measurement in patients.\n\n"
            "4) Guide clinical decision-making (main category - use ONLY if none of subcategories 4a-4d apply)\n"
            '   • Positive keywords (general): clinical management; decision-making; "used to guide therapy"; "used to guide clinical action"; therapeutic drug monitoring.\n'
            "   • Signals: DOAC level result directly influenced a diagnostic or therapeutic decision.\n"
            "   • Exclusions: levels measured for research reporting only; results not used to inform care.\n"
            "   • IMPORTANT: If the study fits any subcategory (4a-4d), select ONLY that subcategory and do NOT select this main category.\n\n"
            "4a) Guide clinical decision-making - Urgent surgery\n"
            "   • Positive keywords: urgent/emergency surgery; trauma; unplanned operation; hip fracture; emergency endoscopy.\n"
            "   • Signals: level testing performed to guide surgical timing or determine fitness for procedure.\n"
            "   • Exclusions: emergent procedures with no level assessment.\n\n"
            "4b) Guide clinical decision-making - Major bleeding and reversal agent administration\n"
            "   • Positive keywords: bleeding; hemorrhage; intracranial hemorrhage; GI bleed; andexanet alfa; idarucizumab; PCC; reversal; antidote.\n"
            "   • Signals: level measured to guide or assess reversal efficacy; correlation between baseline level and hemostatic outcome.\n"
            "   • Exclusions: bleeding management without level data; in-vitro or animal models only.\n\n"
            "4c) Guide clinical decision-making - Thrombolysis\n"
            '   • Positive keywords: acute ischemic stroke; thrombolysis; alteplase; tenecteplase; rtPA; thrombectomy; "lytic eligibility."\n'
            "   • Signals: DOAC level testing to determine eligibility for thrombolysis or mechanical thrombectomy.\n"
            "   • Exclusions: stroke outcomes reported without any level testing.\n\n"
            "4d) Guide clinical decision-making - Guide dose adjustment\n"
            '   • Positive keywords: dose adjustment; dose increase; dose reduction; "dose modification based on plasma concentration"; "individualized dosing."\n'
            "   • Signals: measured level used to justify dose change or confirm appropriateness of reduced/standard dose.\n"
            "   • Exclusions: simulation of dosing algorithms; labeling guidance discussion only.\n\n"
            "5) Measure correlation with other laboratory techniques (main category - use ONLY if none of subcategories 5a-5b apply)\n"
            "   • Positive keywords (general): correlation; comparison; concordance; validation; method comparison.\n"
            "   • Signals: direct statistical or graphical correlation between DOAC concentration and another lab test.\n"
            "   • Exclusions: qualitative statements about potential correlation without numeric data.\n"
            "   • IMPORTANT: If the study fits any subcategory (5a-5b), select ONLY that subcategory and do NOT select this main category.\n\n"
            "5a) Measure correlation with other laboratory techniques - Conventional coagulation testing (e.g., prothrombin time)\n"
            "   • Positive keywords: PT; INR; aPTT; thrombin time; dTT; ECT; ROTEM; viscoelastic testing.\n"
            "   • Signals: comparison of these results vs measured DOAC concentration.\n"
            "   • Exclusions: routine coagulation testing without comparison to levels.\n\n"
            "5b) Measure correlation with other laboratory techniques - HPLC-MS vs calibrated anti-Xa measurement\n"
            '   • Positive keywords: LC-MS/MS; HPLC; "mass spectrometry"; "chromogenic anti-Xa"; "calibrated anti-Xa assay"; "method comparison."\n'
            "   • Signals: comparison or validation of LC-MS/MS against calibrated anti-Xa or other quantification methods.\n"
            "   • Exclusions: method described but not compared or correlated; analytical validation without clinical samples.\n\n"
            "6) Risk prediction and clinical outcome association (main category - use ONLY if none of subcategories 6a-6b apply)\n"
            "   • Positive keywords: outcome; prognosis; prediction; correlation with outcomes; bleeding risk; thrombotic risk; clinical association.\n"
            "   • Signals: DOAC levels analyzed in relation to patient outcomes (bleeding, thrombosis, mortality, etc.); thresholds or ROC analysis used for risk discrimination.\n"
            "   • Exclusions: outcome studies lacking measured concentrations; modeling or registries without lab data.\n"
            "   • IMPORTANT: If the study fits any subcategory (6a-6b), select ONLY that subcategory and do NOT select this main category.\n\n"
            "6a) Risk prediction and clinical outcome association - Bleeding\n"
            "   • Positive keywords: bleeding; hemorrhage; major bleeding; ISTH major bleeding; intracranial hemorrhage; GI bleed.\n"
            "   • Signals: measured DOAC level associated with bleeding occurrence or severity.\n"
            "   • Exclusions: reported bleeding rates without concentration analysis.\n\n"
            "6b) Risk prediction and clinical outcome association - Thrombosis\n"
            '   • Positive keywords: thrombosis; stroke; VTE; DVT; PE; ischemic event; "recurrent thrombosis."\n'
            "   • Signals: association between DOAC level (or subtherapeutic concentration) and thrombotic events.\n"
            "   • Exclusions: thrombosis reported without measured DOAC levels.\n\n"
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
    indications_for_doac_level_measurement_confidence_score: Optional[int] = Field(
        default=None,
        alias="Indications for DOAC Level Measurement Confidence Score",
        description="Confidence score for the indications for DOAC level measurement classification. How confident is the model in the classification? A number between 0 and 100, where 0 is the lowest confidence and 100 is the highest confidence.",
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
            "METHOD CLASSIFICATIONS AND KEY DISTINCTIONS:\n\n"
            "FOR FACTOR XA INHIBITORS (Apixaban, Rivaroxaban, Edoxaban, Betrixaban):\n\n"
            "1) HPLC-MS/LC-MS/MS (ng/mL) - Analytical reference standard:\n"
            "   • Directly measures drug mass for all DOACs, providing the most precise quantification.\n"
            "   • Reports in ng/mL (absolute concentration).\n"
            "   • Used for research and specialized laboratories; may be referenced as the gold standard or validation method.\n\n"
            "2) Calibrated anti-Xa level (ng/mL) - Drug-specific chromogenic assay:\n"
            "   • Drug-specific chromogenic anti-Xa assays that quantify plasma concentration by measuring inhibition of standardized FXa reaction.\n"
            "   • Uses calibrators and controls SPECIFIC to each DOAC agent (apixaban, rivaroxaban, edoxaban, or betrixaban).\n"
            "   • Reports in ng/mL (absolute drug concentration).\n"
            "   • CRITICAL DISTINCTION: These are DIFFERENT from heparin-calibrated anti-Xa assays. "
            "Look for explicit mention of DOAC-specific calibrators or drug-specific calibration.\n\n"
            "3) Heparin (UFH/LMWH) anti-Xa level (IU/mL) - Heparin-calibrated assay:\n"
            "   • Routinely used for monitoring UFH or LMWH, NOT designed for DOACs.\n"
            "   • Reports in IU/mL (heparin activity units), NOT absolute DOAC concentration.\n"
            "   • CRITICAL DISTINCTION: Results in IU/mL cannot be accurately converted to DOAC levels (ng/mL). "
            "These assays use heparin standards, not DOAC-specific calibrators.\n"
            "   • May show variable under- or overestimation of DOAC levels depending on reagent and analyzer.\n\n"
            "FOR DIRECT THROMBIN INHIBITORS (Dabigatran):\n\n"
            "1) HPLC-MS/LC-MS/MS (ng/mL) - Analytical reference standard:\n"
            "   • Directly measures dabigatran and its metabolites with high precision.\n"
            "   • May be used to establish or validate clot-based assay calibration.\n\n"
            "2) Dilute Thrombin Time (dTT) - Quantitative assay:\n"
            "   • Uses sample dilution and drug-specific calibrators to yield linear results.\n"
            "   • Reports in ng/mL (absolute drug concentration).\n"
            "   • More reliable than TT for therapeutic-level quantification.\n\n"
            "3) Ecarin Clotting Time (ECT) - Quantitative assay:\n"
            "   • Activates prothrombin via ecarin to form meizothrombin, which is inhibited in proportion to dabigatran concentration.\n"
            "   • Provides wide dynamic range and high specificity.\n"
            "   • Reports in ng/mL (absolute drug concentration).\n\n"
            "4) Ecarin Chromogenic Assay (ECA) - Quantitative assay:\n"
            "   • Similar to ECT but uses chromogenic rather than clot-based detection.\n"
            "   • Activates prothrombin via ecarin to form meizothrombin.\n"
            "   • Provides wide dynamic range and high specificity.\n"
            "   • Reports in ng/mL (absolute drug concentration).\n\n"
            "5) Thrombin Time (TT) - Qualitative/semi-quantitative:\n"
            "   • Very sensitive to dabigatran but becomes unmeasurable at therapeutic levels (ceiling effect).\n"
            "   • May not provide reliable quantitative results at typical therapeutic concentrations.\n"
            "   • May be reported in seconds or as a qualitative indicator.\n\n"
            "SYNONYM MAP FOR HPLC-MS/LC-MS (CRITICAL - scan for ALL variations):\n"
            "• HPLC-MS / HPLC-MS/MS / HPLC/MS / HPLC/MS/MS (with hyphens OR forward slashes)\n"
            "• LC-MS/MS / LC-MS / LC/MS / LC/MS/MS\n"
            "• UPLC-MS / UPLC-MS/MS / UPLC/MS / UPLC/MS/MS\n"
            "• High-performance liquid chromatography-mass spectrometry / high performance liquid chromatography mass spectrometry\n"
            "• Liquid chromatography-mass spectrometry / liquid chromatography mass spectrometry\n"
            "• Mass spectrometry / MS / tandem mass spectrometry / MS/MS\n"
            '• Any combination of "HPLC" or "LC" or "UPLC" with "MS" or "mass spectrometry"\n'
            "  → ALL map to '[DOAC] - HPLC-MS (ng/mL)'\n\n"
            "SYNONYM MAP FOR CALIBRATED ANTI-XA (drug-specific, ng/mL):\n"
            "• Calibrated anti-Xa / drug-specific anti-Xa / DOAC-specific anti-Xa\n"
            "• Chromogenic anti-Xa assay with [drug] calibrators / [drug]-calibrated anti-Xa\n"
            "• DiXaI / Biophen / STA-Liquid Anti-Xa + drug calibrator / TECHNOVIEW / "
            "HemosIL Liquid Anti-Xa + drug calibrators / Innovance Heparin anti-Xa with drug calibrators / "
            "COAMATIC / Berichrom / Rotachrom with drug calibrators\n"
            "• Look for explicit mention of 'drug-specific calibrators', 'apixaban calibrators', 'rivaroxaban calibrators', etc.\n"
            "  → Maps to '[DOAC] - Calibrated anti-Xa level (ng/mL)'\n\n"
            "SYNONYM MAP FOR HEPARIN-CALIBRATED ANTI-XA (IU/mL):\n"
            "• Heparin-calibrated anti-Xa / LMWH-calibrated anti-Xa / UFH-calibrated anti-Xa\n"
            "• Anti-Xa assay calibrated for heparin / heparin standard\n"
            "• Reports in IU/mL (NOT ng/mL) - this is the key indicator\n"
            "• CRITICAL: If the method reports in IU/mL or uses heparin/LMWH calibrators (not DOAC-specific), "
            "this is heparin-calibrated, NOT drug-specific calibrated anti-Xa\n"
            "  → Maps to '[DOAC] - Heparin (UFH/LMWH) anti-Xa level (IU/mL)'\n\n"
            "SYNONYM MAP FOR DABIGATRAN ASSAYS:\n"
            "• Hemoclot / dTT / diluted thrombin time / HemosIL DTI / INNOVANCE DTI / dilute TT\n"
            "  → Maps to 'Dabigatran - Dilute Thrombin Time (dTT)'\n"
            "• Ecarin Clotting Time / ECT / ecarin clotting assay\n"
            "  → Maps to 'Dabigatran - Ecarin Clotting Time (ECT)'\n"
            "• Ecarin Chromogenic Assay / ECA / ecarin chromogenic\n"
            "  → Maps to 'Dabigatran - Ecarin Chromogenic Assay (ECA)'\n"
            "• Thrombin Time / TT (when used specifically for dabigatran quantification)\n"
            "  → Maps to 'Dabigatran - Thrombin Time (TT)'\n\n"
            "METHOD APPLICABILITY BY DOAC (based on clinical practice):\n"
            "• Apixaban, Rivaroxaban, Edoxaban, Betrixaban: HPLC-MS, Calibrated anti-Xa (ng/mL), Heparin anti-Xa (IU/mL)\n"
            "• Dabigatran: HPLC-MS, dTT, ECT, ECA, TT, aPTT\n\n"
            "Common errors to avoid:\n"
            "• CRITICAL: Missing HPLC-MS/LC-MS when clearly described in Methods (e.g., 'HPLC/MS was used', 'LC-MS/MS analysis', "
            "'measured by mass spectrometry'). Scan for ALL variations including forward slashes.\n"
            "• CONFUSING calibrated anti-Xa (ng/mL, drug-specific) with heparin-calibrated anti-Xa (IU/mL): "
            "Look for units (ng/mL vs IU/mL) and explicit mention of drug-specific vs heparin calibrators.\n"
            "• Partial recognition: identifying some methods but missing others in the same paragraph.\n"
            "• Including methods mentioned only in Background/Discussion without Methods description.\n"
            "• For dabigatran: confusing TT (may become unmeasurable at therapeutic levels) with dTT (quantitative with calibrators).\n\n"
            "Include ONLY if this method was actually used in THIS study to quantify DOAC level in patients. "
            "Exclude: background mentions of potential assays; assay description without patient sample quantification; "
            "in vitro spiking experiments only (unless performed on patient-derived samples)."
        ),
    )
    doac_level_measurement_sentence_from_text: Optional[List[str]] = Field(
        default=None,
        alias="DOAC Level Measurement Sentence from Text",
        description="Exact sentences or paragraph containing the DOAC level measurement.",
    )
    doac_level_measurement_confidence_score: Optional[int] = Field(
        default=None,
        alias="DOAC Level Measurement Confidence Score",
        description="Confidence score for the DOAC level measurement classification. How confident is the model in the classification? A number between 0 and 100, where 0 is the lowest confidence and 100 is the highest confidence.",
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
            "Scan for ALL synonyms, variants, and manufacturer/product names (see detailed maps below).\n"
            "Step 2 (Decision): Based ONLY on those quoted sentences, classify ALL applicable methods.\n\n"
            "ASSAY CLASSIFICATIONS BY DOAC:\n\n"
            "FOR FACTOR XA INHIBITORS (Apixaban, Rivaroxaban, Edoxaban, Betrixaban):\n\n"
            "1) Calibrated anti-Xa assay (ng/mL) - Drug-specific chromogenic assays:\n"
            "   These use DOAC-specific calibrators and report in ng/mL (absolute drug concentration).\n\n"
            "   APIXABAN-specific products:\n"
            "   • STA-Liquid Anti-Xa + STA-Apixaban Calibrator\n"
            "   • BIOPHEN DiXaI / DiXaL + apixaban calibrators\n"
            "   • TECHNOVIEW Apixaban\n"
            "   • HemosIL Liquid Anti-Xa + apixaban calibrators\n"
            "   • Innovance Heparin anti-Xa with apixaban calibrators\n"
            "   • COAMATIC / Berichrom / Rotachrom + apixaban calibrators\n\n"
            "   RIVAROXABAN-specific products:\n"
            "   • STA-Liquid Anti-Xa + STA-Rivaroxaban Calibrator\n"
            "   • BIOPHEN DiXaI / DiXaL + rivaroxaban calibrators\n"
            "   • TECHNOVIEW Rivaroxaban\n"
            "   • HemosIL Liquid Anti-Xa + rivaroxaban calibrators\n"
            "   • Innovance Heparin anti-Xa with rivaroxaban calibrators\n"
            "   • COAMATIC / Berichrom / Rotachrom + rivaroxaban calibrators\n\n"
            "   EDOXABAN-specific products:\n"
            "   • STA-Liquid Anti-Xa + STA-Edoxaban Calibrator\n"
            "   • Innovance anti-Xa with edoxaban calibrators\n"
            "   • BIOPHEN anti-Xa with edoxaban calibrators\n\n"
            "   BETRIXABAN-specific products (rarely available):\n"
            "   • BIOPHEN DiXaI adapted for betrixaban\n"
            "   • STA anti-Xa systems adapted for betrixaban\n\n"
            "2) Heparin-calibrated anti-Xa assay (IU/mL):\n"
            "   • LMWH/UFH-calibrated assays WITHOUT DOAC-specific calibration\n"
            "   • Reports in IU/mL (heparin activity units), NOT absolute DOAC concentration\n"
            "   • CRITICAL: These are different from drug-specific calibrated anti-Xa assays\n\n"
            "3) LC-MS/MS quantitative assay (ng/mL):\n"
            "   • Mass-spectrometry-based direct measurement of DOAC concentration\n"
            "   • Analytical reference standard method\n\n"
            "4) Qualitative/Point-of-Care (POCT):\n"
            "   • DOAC Dipstick or equivalent qualitative device\n\n"
            "FOR DIRECT THROMBIN INHIBITORS (Dabigatran):\n\n"
            "1) Dilute Thrombin Time (dTT) calibrated (ng/mL):\n"
            "   • Uses sample dilution and drug-specific calibrators\n"
            "   • Products: Hemoclot Thrombin Inhibitor (HTI), HemosIL DTI, INNOVANCE DTI\n"
            "   • Reports in ng/mL (absolute drug concentration)\n\n"
            "2) Ecarin Clotting Time (ECT) calibrated (ng/mL):\n"
            "   • Activates prothrombin via ecarin to form meizothrombin\n"
            "   • Clot-based assay with wide dynamic range and high specificity\n"
            "   • Reports in ng/mL (absolute drug concentration)\n\n"
            "3) Ecarin Chromogenic Assay (ECA) calibrated (ng/mL):\n"
            "   • Similar to ECT but uses chromogenic rather than clot-based detection\n"
            "   • Products: STA-ECA II, ECA-T\n"
            "   • Reports in ng/mL (absolute drug concentration)\n\n"
            "4) Non-calibrated Thrombin Time (TT) (seconds):\n"
            "   • Very sensitive but becomes unmeasurable at therapeutic levels (ceiling effect)\n"
            "   • Qualitative sensitivity only at low drug levels, NOT quantitative\n"
            "   • Reports in seconds, not ng/mL\n\n"
            "5) LC-MS/MS quantitative assay (ng/mL):\n"
            "   • Reference method for dabigatran and metabolites\n"
            "   • Direct measurement with high precision\n\n"
            "6) Qualitative/Point-of-Care (POCT):\n"
            "   • DOAC Dipstick or equivalent qualitative device\n\n"
            "SYNONYM MAP FOR LC-MS/MS (CRITICAL - scan for ALL variations):\n"
            "• LC-MS/MS / LC-MS / LC/MS / LC/MS/MS (with hyphens OR forward slashes)\n"
            "• UPLC-MS / UPLC-MS/MS / UPLC/MS / UPLC/MS/MS (with hyphens OR forward slashes)\n"
            "• HPLC-MS / HPLC-MS/MS / HPLC/MS / HPLC/MS/MS (with hyphens OR forward slashes)\n"
            "• High-performance liquid chromatography-mass spectrometry / high performance liquid chromatography mass spectrometry\n"
            "• Liquid chromatography-mass spectrometry / liquid chromatography mass spectrometry\n"
            "• Mass spectrometry / MS / tandem mass spectrometry / MS/MS\n"
            '• Any combination of "HPLC" or "LC" or "UPLC" with "MS" or "mass spectrometry" (regardless of punctuation: hyphen, slash, or space)\n'
            "  → ALL map to '[DOAC] - LC-MS/MS quantitative assay (ng/mL)'\n\n"
            "SYNONYM MAP FOR CALIBRATED ANTI-XA (drug-specific, ng/mL):\n"
            "• Calibrated anti-Xa / drug-specific anti-Xa / DOAC-specific anti-Xa\n"
            "• Chromogenic anti-Xa assay with [drug] calibrators / [drug]-calibrated anti-Xa\n"
            "• Any of the manufacturer/product names listed above for each specific DOAC\n"
            "• Look for explicit mention of 'drug-specific calibrators', '[drug] calibrators', or specific product names\n"
            "  → Maps to '[DOAC] - Calibrated anti-Xa assay (ng/mL)'\n\n"
            "SYNONYM MAP FOR HEPARIN-CALIBRATED ANTI-XA (IU/mL):\n"
            "• Heparin-calibrated anti-Xa / LMWH-calibrated anti-Xa / UFH-calibrated anti-Xa\n"
            "• Anti-Xa assay calibrated for heparin / heparin standard\n"
            "• Reports in IU/mL (NOT ng/mL) - this is the key indicator\n"
            "• CRITICAL: If the method reports in IU/mL or uses heparin/LMWH calibrators (not DOAC-specific), "
            "this is heparin-calibrated, NOT drug-specific calibrated anti-Xa\n"
            "  → Maps to '[DOAC] - Heparin-calibrated anti-Xa assay (IU/mL)'\n\n"
            "SYNONYM MAP FOR DABIGATRAN ASSAYS:\n"
            "• Hemoclot / Hemoclot Thrombin Inhibitor / HTI / dTT / diluted thrombin time / dilute TT\n"
            "• HemosIL DTI / INNOVANCE DTI\n"
            "  → Maps to 'Dabigatran - Dilute Thrombin Time (dTT) calibrated (ng/mL)'\n"
            "• Ecarin Clotting Time / ECT / ecarin clotting assay\n"
            "  → Maps to 'Dabigatran - Ecarin Clotting Time (ECT) calibrated (ng/mL)'\n"
            "• Ecarin Chromogenic Assay / ECA / STA-ECA II / ECA-T / ecarin chromogenic\n"
            "  → Maps to 'Dabigatran - Ecarin Chromogenic Assay (ECA) calibrated (ng/mL)'\n"
            "• Thrombin Time / TT (when used specifically for dabigatran, reports in seconds, not ng/mL)\n"
            "  → Maps to 'Dabigatran - Non-calibrated Thrombin Time (TT) (seconds)'\n\n"
            "EXCLUSIONS (do NOT include these as DOAC level measurement methods):\n"
            "• Thrombograms / CAT / calibrated automated thrombography / thrombin generation\n"
            "• TEG / ROTEM / viscoelastic testing\n"
            "• PT / aPTT (unless explicitly used to quantify DOAC levels, which is rare)\n\n"
            "Common errors to avoid:\n"
            "• CRITICAL: Missing HPLC-MS/LC-MS/UPLC-MS when clearly described in Methods. "
            "Scan for ALL variations including: HPLC-MS, HPLC/MS, HPLC-MS/MS, HPLC/MS/MS, LC-MS/MS, LC/MS, "
            "UPLC-MS, UPLC/MS, mass spectrometry, liquid chromatography-mass spectrometry, etc.\n"
            "• CONFUSING calibrated anti-Xa (ng/mL, drug-specific) with heparin-calibrated anti-Xa (IU/mL): "
            "Look for units (ng/mL vs IU/mL) and explicit mention of drug-specific vs heparin calibrators.\n"
            "• Missing manufacturer/product names: If a specific product is mentioned (e.g., 'STA-Liquid Anti-Xa with apixaban calibrators'), "
            "this indicates calibrated anti-Xa assay, not heparin-calibrated.\n"
            "• For dabigatran: confusing TT (qualitative, seconds) with dTT (quantitative, ng/mL with calibrators).\n"
            "• Partial recognition: identifying some methods but missing others in the same paragraph.\n"
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
            "DETAILED KEYWORD GUIDANCE FOR IDENTIFICATION (flag only if present in the Methods):\n\n"
            "1. Blood collection procedures:\n"
            "   Core indicator terms:\n"
            "   • venipuncture\n"
            "   • phlebotomy\n"
            "   • blood draw / blood sampling / blood collection\n"
            "   • venous blood / peripheral venous blood\n"
            "   • antecubital vein / antecubital fossa\n"
            "   • butterfly needle\n"
            "   • needle gauge / 21‑gauge / 22‑gauge / 21G / 22G\n"
            "   • tourniquet / tourniquet application\n"
            "   • vacutainer / vacuum collection system\n"
            "   Procedure/context phrases:\n"
            '   • "blood was collected from"\n'
            '   • "venous blood was drawn using"\n'
            '   • "single venipuncture" / "single blood draw"\n'
            '   • "non‑traumatic venipuncture"\n'
            '   • "without stasis" / "minimal stasis"\n'
            '   • "fasting state" / "after an overnight fast"\n'
            '   • "subject seated / supine for X minutes before sampling"\n'
            '   • "time of day of blood collection" ("morning sample", "pre‑dose", "trough sample")\n\n'
            "2. Collection tube type:\n"
            "   Core tube descriptors:\n"
            "   • collection tube / blood collection tube\n"
            '   • coagulation tube / citrate tube / "blue‑top tube"\n'
            "   • plasma tube / serum tube / plain tube\n"
            "   • Vacutainer / BD Vacutainer\n"
            "   • Sarstedt / Greiner / Monovette (manufacturer names)\n"
            "   Anticoagulant / additive keywords:\n"
            "   • sodium citrate / Na‑citrate / citrated tube\n"
            "   • 3.2% citrate / 3.8% citrate / 0.109 mol/L citrate\n"
            "   • EDTA / K2EDTA / K3EDTA\n"
            "   • heparin / lithium heparin / Na‑heparin\n"
            '   • "no additive" / "additive‑free" / "clot activator"\n'
            '   • "gel separator" / serum separator tube (SST)\n'
            "   Typical phrases:\n"
            '   • "blood was collected into [X] tubes"\n'
            '   • "blood was drawn into 2.7 mL 3.2% sodium citrate tubes (Becton Dickinson)"\n'
            '   • "citrated plasma obtained from 3.2% sodium citrate Vacutainer tubes"\n\n'
            "3. Centrifugation speed:\n"
            "   Core process terms:\n"
            "   • centrifuge / centrifugation\n"
            "   • spun / spin / spun down\n"
            "   • relative centrifugal force / RCF\n"
            "   • g‑force / ×g / x g\n"
            "   • rpm / revolutions per minute\n"
            "   Typical formats:\n"
            '   • "centrifuged at 1,500 × g for 10 min"\n'
            '   • "centrifuged at 2,500g for 15 minutes"\n'
            '   • "spun at 3,000 rpm for 10 min"\n'
            '   • "double centrifugation" / "two‑step centrifugation"\n'
            '   • "to obtain platelet‑poor plasma (PPP)"\n'
            '   • "centrifuged at room temperature" / "centrifuged at 4°C"\n\n'
            "4. Storage temperature:\n"
            "   Core temperature + storage terms:\n"
            "   • stored at / kept at / maintained at\n"
            "   • frozen at / immediately frozen / snap frozen\n"
            "   • refrigerated / kept at 4°C\n"
            "   • room temperature / ambient temperature / RT\n"
            "   • long‑term storage / short‑term storage\n"
            "   • aliquots / aliquoted and stored\n"
            "   Temperature formats:\n"
            "   • −80°C / -80°C\n"
            "   • −70°C / -70°C\n"
            "   • −20°C / -18°C\n"
            "   • 4°C / 2–8°C\n"
            '   • 20–25°C / "room temperature" / "ambient"\n'
            "   Typical phrases:\n"
            '   • "plasma samples were aliquoted and stored at −80°C until analysis"\n'
            '   • "samples were kept at 4°C and analyzed within 4 hours"\n'
            '   • "serum was stored at −20°C before batch analysis"\n'
            '   • "samples were kept at room temperature"\n\n'
            "Common errors to avoid:\n"
            "• Overcounting: Do NOT flag if only mentioned in Background, Introduction, or as general lab capabilities rather than specimen-specific protocol.\n"
            "• Do NOT guess based on context or intuition if explicit Methods evidence is lacking; leave null if not reported.\n"
            "• Ensure the variable is explicitly described for DOAC level measurement specimens, not just general laboratory procedures."
        ),
    )
    pre_analytical_variables_sentence_from_text: Optional[List[str]] = Field(
        default=None,
        alias="Pre-Analytical Variables Sentence from Text",
        description="Exact sentences or paragraph containing the pre-analytical variables.",
    )
    pre_analytical_variables_confidence_score: Optional[int] = Field(
        default=None,
        alias="Pre-Analytical Variables Confidence Score",
        description="Confidence score for the pre-analytical variables classification. How confident is the model in the classification? A number between 0 and 100, where 0 is the lowest confidence and 100 is the highest confidence.",
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
            "CRITICAL: Only count tests actually measured in the study. Apply strict filtering criteria below.\n\n"
            "STRICT FILTERING CRITERIA - THREE-STEP PROCESS:\n\n"
            "STEP 1: SECTION RELEVANCE FILTER\n"
            "Restrict to Methods/Results sections only. Count mentions as relevant ONLY if they appear:\n"
            "• Under headings such as 'Methods', 'Materials and Methods', 'Laboratory Methods', 'Study Procedures', "
            "'Results', 'Outcomes', 'Baseline characteristics', 'Laboratory results', etc.\n"
            "• Or in text that clearly describes what was done to the study participants or what was measured at baseline/follow-up.\n"
            "• EXPLICITLY IGNORE: Introduction, Background, or descriptions of general practice/guidelines without measurement context.\n\n"
            "STEP 2: MEASUREMENT CONTEXT REQUIRED\n"
            "Only count PT/aPTT as measured if the sentence (or one immediately before/after) contains at least ONE of the following:\n"
            "• 'measured', 'was measured', 'were measured'\n"
            "• 'determined', 'assessed', 'tested', 'performed'\n"
            "• 'recorded', 'collected', 'obtained'\n"
            "• 'available', 'included', 'reported' (when referring to baseline or follow-up lab values)\n"
            "• Or appears in a description of a table of baseline labs (e.g., 'Table 1. Baseline laboratory parameters including PT, aPTT …')\n\n"
            "STEP 3: EXPLICITLY IGNORE INTRODUCTION/BACKGROUND-ONLY MENTIONS\n"
            "Do NOT count PT or aPTT if mentioned only in:\n"
            "• General background (e.g., 'PT and aPTT are widely used to assess coagulation')\n"
            "• Description of standard practice, guidelines, or prior literature\n"
            "• Without measurement context as defined in Step 2\n\n"
            "INSTRUCT THE LLM EXPLICITLY:\n"
            "'Only count PT or aPTT if the authors describe actually measuring it on the study participants (including baseline labs or monitoring). "
            "Ignore mentions in Introduction or general background.'\n\n"
            "PT (PROTHROMBIN TIME) - KEYWORDS AND RULES:\n"
            "-------------------------------------------\n\n"
            "2.1. Strong PT Keywords (Test Names)\n"
            "Flag PT as measured if any of the following appear in Methods/Results with measurement context:\n\n"
            "Full names:\n"
            "• 'prothrombin time'\n"
            "• 'Quick prothrombin time', 'Quick test', 'Quick's test' (Quick PT is a standard PT method)\n\n"
            "Combined terms:\n"
            "• 'PT/INR', 'PT‑INR', 'prothrombin time/INR', 'prothrombin time (PT)/international normalized ratio (INR)'\n\n"
            "Abbreviations (when clearly defined in the article):\n"
            "• 'prothrombin time (PT)' → subsequent 'PT'\n"
            "• 'PT (prothrombin time)'\n\n"
            "Additional strong indicators:\n"
            "• 'prothrombin ratio'\n"
            "• 'prothrombin activity' (especially if combined with 'Quick' or PT reagents)\n\n"
            "2.2. INR as a PT Proxy\n"
            "INR is essentially specific to PT. If an article says in Methods/Results:\n"
            "• 'INR was measured', 'we determined INR', 'baseline INR', 'we recorded INR', and\n"
            "• there is no contrary indication that 'INR' is being used in some nonstandard way,\n"
            "→ Treat this as PT measured, since INR is defined as a standardized transformation of the PT.\n"
            "RULE: If 'INR' appears with measurement verbs in Methods/Results, flag PT = yes (even if 'PT' is not explicitly written).\n\n"
            "2.3. PT-Specific Reagents: Positive List\n"
            "Many papers only name the reagent. The following are PT reagents (thromboplastin-based) and should count as PT, not aPTT, "
            "when in measurement context:\n\n"
            "From Siemens/Sysmex/Stago and others:\n"
            "• Thromborel S (Dade/Siemens) – PT reagent\n"
            "• Dade Innovin (Innovin) – recombinant thromboplastin PT reagent\n"
            "• Neoplastin / Néoplastine / Neoplastine CI Plus / STA‑Neoplastine – PT reagents\n"
            "• STA‑NeoPTimal – PT/INR reagent\n"
            "• Thrombotest – PT (Quick/Owren type)\n"
            "• Normotest / Normotest Automated / Normotest® – PT (combined thromboplastin)\n"
            "• RecombiPlasTin / RecombiPlasTin 2G – PT reagent\n"
            "• Spinreact Prothrombin time reagent\n"
            "• Technoclot PT Owren – PT reagent replacing Thrombotest/Normotest\n"
            "• Generic phrases like 'prothrombin time reagent containing thromboplastin and calcium chloride'\n\n"
            "RULE: If any of these reagent names occur in Methods/Results with measurement verbs or explicit mention of clotting time, "
            "classify PT measured, even if the text doesn't restate 'PT' in that sentence.\n\n"
            "2.4. Thromboplastin and PT (Critical Biochemical Point)\n"
            "KEY BIOCHEMICAL POINT: Thromboplastin reagents are standard for PT, NOT for aPTT. PT testing requires a thromboplastin reagent "
            "(tissue factor + phospholipid + Ca²⁺).\n\n"
            "Simple word rule:\n"
            "• 'thromboplastin' by itself does NOT imply aPTT.\n"
            "• If 'thromboplastin' appears in the context of:\n"
            "  - Thromborel S, Innovin, Neoplastin, Thrombotest, Normotest, Technoclot PT, etc., or\n"
            "  - 'prothrombin time reagent'\n"
            "  → treat this as PT, NOT aPTT.\n\n"
            "CRITICAL RULE TO PREVENT MISCLASSIFICATION:\n"
            "Only count aPTT if the text includes 'partial thromboplastin', 'aPTT', 'APTT', 'PTT' (clearly defined as partial thromboplastin time), "
            "or an explicit aPTT reagent name. The word 'thromboplastin' alone is NEVER sufficient for aPTT.\n\n"
            "aPTT (ACTIVATED PARTIAL THROMBOPLASTIN TIME) - KEYWORDS AND RULES:\n"
            "-------------------------------------------------------------------\n\n"
            "3.1. Strong aPTT Keywords (Test Names)\n"
            "Flag aPTT as measured if any of these appear in Methods/Results with measurement context:\n\n"
            "Full names:\n"
            "• 'activated partial thromboplastin time'\n"
            "• 'partial thromboplastin time'\n\n"
            "Abbreviations:\n"
            "• 'aPTT', 'APTT', 'A‑PTT'\n"
            "• 'PTT' or 'partial thromboplastin time (PTT)' when clearly defined as such\n\n"
            "Historical synonyms (less common, but relevant in older literature):\n"
            "• 'kaolin‑cephalin clotting time', 'kaolin cephalin clotting time', 'KCCT'\n\n"
            "3.2. aPTT-Specific Reagents: Positive List\n"
            "These reagents are aPTT reagents and should be treated as aPTT, NOT PT, if used to measure a clotting time:\n\n"
            "From Siemens/Sysmex/others:\n"
            "• Dade Actin® reagents (all 'Actin' APTT formulations):\n"
            "  - Dade Actin® Activated Cephaloplastin\n"
            "  - Dade Actin FS Activated PTT\n"
            "  - Dade Actin FSL Activated PTT\n"
            "• Pathromtin® SL – APTT reagent\n"
            "• STA‑PTT Automate – APTT reagent\n"
            "• STA Cephascreen – APTT reagent\n"
            "• Phrases like 'APTT reagent', 'activated PTT reagent'\n\n"
            "RULE: If any of these aPTT reagents are mentioned in Methods/Results with measurement verbs "
            "(e.g., 'aPTT was measured using Pathromtin SL'), classify aPTT measured.\n\n"
            "3.3. Handling 'PTT' Alone\n"
            "'PTT' alone is ambiguous in pure text, but in clinical/lab contexts it almost always means partial thromboplastin time.\n\n"
            "Practical rules:\n"
            "1. If the article at any point defines the abbreviation:\n"
            "   • 'partial thromboplastin time (PTT)' or 'activated partial thromboplastin time (aPTT)'\n"
            "   → then any subsequent 'PTT'/'aPTT' in Methods/Results with measurement context → aPTT measured.\n"
            "2. If the only occurrence is something like 'PT/INR and PTT were measured', and earlier they defined 'PTT' as partial thromboplastin time, "
            "   treat as PT = yes, aPTT = yes.\n"
            "3. If 'PTT' is never defined and occurs in a single generic list without context, interpret cautiously; "
            "   if found in Methods/Results with measurement verbs, consider as aPTT measured if context is sufficient.\n\n"
            "3.4. Negative/Ambiguous Cases for aPTT\n"
            "Do NOT classify as aPTT if:\n"
            "• Only 'thromboplastin' is mentioned without 'partial'.\n"
            "• Only PT reagents (Thromborel S, Innovin, Neoplastin, Thrombotest, Normotest, etc.) are named.\n"
            "• aPTT is mentioned only in a phrase like 'Routine coagulation tests such as PT and aPTT are widely used…' in the Introduction, "
            "  with no measurement context in Methods/Results.\n\n"
            "COMMON ERRORS TO AVOID:\n"
            "• Do NOT assume aPTT if only 'thromboplastin' or PT reagents are named.\n"
            "• Do NOT assume both PT and aPTT were measured merely because one was.\n"
            "• Do NOT guess: If there is no specific evidence in Methods/Results, leave null.\n\n"
            "APPLIES FOR ALL DOACS (overall and per drug):\n"
            "• The rules above apply regardless of which DOACs (apixaban, rivaroxaban, edoxaban, betrixaban, dabigatran) are tested.\n"
            "• Only fill this field if at least one of the explicit criteria is satisfied for a particular study or DOAC regimen."
        ),
    )
    coagulation_tests_concurrent_sentence_from_text: Optional[List[str]] = Field(
        default=None,
        alias="Conventional Coagulation Tests Concurrently Reported Sentence from Text",
        description="Exact sentences with the conventional coagulation tests concurrently reported.",
    )
    coagulation_tests_concurrent_confidence_score: Optional[int] = Field(
        default=None,
        alias="Conventional Coagulation Tests Concurrently Reported Confidence Score",
        description="Confidence score for the conventional coagulation tests concurrently reported classification. How confident is the model in the classification? A number between 0 and 100, where 0 is the lowest confidence and 100 is the highest confidence.",
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
            "Look for explicit descriptions of thrombin generation or viscoelastic testing, including specific platform names.\n"
            "Step 2 (Decision): Based ONLY on those quoted sentences, classify the tests.\n\n"
            "GLOBAL COAGULATION TEST CLASSIFICATIONS:\n\n"
            "1) Viscoelastic testing (ROTEM/TEG) - Viscoelastic Testing (VET) Platforms:\n"
            "   These tests assess whole blood clot formation and strength using viscoelastic properties.\n\n"
            "   VET Platform Names and Synonyms:\n"
            "   • ROTEM / rotational thromboelastometry:\n"
            "     - ROTEM Delta\n"
            "     - ROTEM Sigma\n"
            "   • TEG / thromboelastography:\n"
            "     - TEG 5000\n"
            "     - TEG 6s\n"
            "   • Quantra (SEER Sonorheometry)\n"
            "   • ClotPro (multi-channel viscoelastic analyzer)\n"
            "   • Sonoclot Analyzer (impedance-based clot signature)\n"
            "   • Generic terms: viscoelastic testing, viscoelastic analysis, whole blood coagulation testing\n\n"
            "2) Thrombin Generation Assay (TGA) - Thrombin Generation Assay Platforms:\n"
            "   These tests measure the capacity of plasma to generate thrombin over time.\n\n"
            "   TGA Platform Names and Synonyms:\n"
            "   • CAT / calibrated automated thrombography / calibrated automated thrombogram\n"
            "   • Technothrombin\n"
            "   • Innovance ETP\n"
            "   • ST Genesia\n"
            "   • Generic terms: thrombin generation, thrombin generation assay, TGA, thrombograms, "
            "thrombin potential, endogenous thrombin potential (ETP)\n\n"
            "DETAILED SYNONYM MAP:\n\n"
            "For Viscoelastic testing (ROTEM/TEG):\n"
            "• ROTEM / rotational thromboelastometry / ROTEM Delta / ROTEM Sigma\n"
            "• TEG / thromboelastography / TEG 5000 / TEG 6s\n"
            "• Quantra / SEER Sonorheometry\n"
            "• ClotPro / multi-channel viscoelastic analyzer\n"
            "• Sonoclot Analyzer / impedance-based clot signature\n"
            "• viscoelastic testing / viscoelastic analysis / whole blood coagulation testing\n"
            "  → ALL map to 'Viscoelastic testing (ROTEM/TEG)'\n\n"
            "For Thrombin Generation Assay (TGA):\n"
            "• CAT / calibrated automated thrombography / calibrated automated thrombogram\n"
            "• Technothrombin\n"
            "• Innovance ETP\n"
            "• ST Genesia\n"
            "• thrombin generation / thrombin generation assay / TGA / thrombograms\n"
            "• thrombin potential / endogenous thrombin potential / ETP\n"
            "  → ALL map to 'Thrombin Generation Assay (TGA)'\n\n"
            "INCLUDE A TEST ONLY IF:\n"
            "1) It is explicitly described in Methods as performed (not just mentioned in Discussion/Background).\n"
            "2) It was performed on the same specimens as DOAC level measurement.\n"
            "3) The specific platform name OR generic test type is mentioned with measurement context.\n\n"
            "MEASUREMENT CONTEXT REQUIRED:\n"
            "Look for verbs/phrases indicating the test was actually performed:\n"
            "• 'measured', 'was measured', 'were measured', 'determined', 'assessed', 'tested', 'performed'\n"
            "• 'recorded', 'collected', 'obtained', 'analyzed'\n"
            "• 'using [platform name]', 'measured with [platform name]'\n\n"
            "Common errors to avoid:\n"
            "• Missing thrombin generation (CAT/TGA) when explicitly described with platform names like Technothrombin, Innovance ETP, or ST Genesia.\n"
            "• Missing viscoelastic testing when platform names like Quantra, ClotPro, or Sonoclot are mentioned.\n"
            "• Misinterpreting manufacturer names (e.g., Technoclone) as evidence that thrombin generation or viscoelastic testing "
            "  was actually performed, without explicit description of the test.\n"
            "• Including tests mentioned only in Discussion/Background without Methods description.\n"
            "• Confusing TGA platforms with other coagulation tests: TGA is specifically thrombin generation, not PT/aPTT or other assays.\n"
            "• Not recognizing platform-specific names: if 'ROTEM Delta' or 'TEG 5000' is mentioned, this indicates viscoelastic testing.\n\n"
            "APPLIES FOR ALL DOACS:\n"
            "• The rules above apply regardless of which DOACs (apixaban, rivaroxaban, edoxaban, betrixaban, dabigatran) are tested.\n"
            "• Both viscoelastic testing and thrombin generation assays can be used with any DOAC.\n\n"
            "If the article does not clearly report which global tests were performed, leave null. Do NOT guess."
        ),
    )
    global_coagulation_tests_sentence_from_text: Optional[List[str]] = Field(
        default=None,
        alias="Global Coagulation Testing Sentence from Text",
        description="Exact sentences or paragraph containing the global coagulation tests.",
    )
    global_coagulation_tests_confidence_score: Optional[int] = Field(
        default=None,
        alias="Global Coagulation Tests Confidence Score",
        description="Confidence score for the global coagulation tests classification. How confident is the model in the classification? A number between 0 and 100, where 0 is the lowest confidence and 100 is the highest confidence.",
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
