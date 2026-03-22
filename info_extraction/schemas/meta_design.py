"""Bibliography & Study Design schema."""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# -------------------------------
# 1) Bibliography & Study Design
# -------------------------------
class ExtractionMetaDesign(BaseModel):
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
