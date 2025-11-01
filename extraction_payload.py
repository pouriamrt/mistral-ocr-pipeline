from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

class ImageType(str, Enum):
    GRAPH = "graph"
    TEXT = "text"
    TABLE = "table"
    IMAGE = "image"

class Image(BaseModel):
    image_type: ImageType = Field(..., description="The type of the image. Must be one of 'graph', 'text', 'table' or 'image'.")
    description: str = Field(..., description="A description of the image.")
    

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

# -------------------------------
# 1) Bibliography & Study Design
# -------------------------------
class ExtractionMetaDesign(BaseModel):
    """
    Guidelines:
    1) Do not infer or guess. 2) Use null if unsure.
    3) Output only facts explicitly in the PDF.
    4) If ambiguous, set null (do not guess).
    5) Numeric values must be exact.
    6) Resolve conflicts by the clearest statement (title→early pages; patients→methods/results).
    7) Do not use external knowledge.
    8) Ignore References and Acknowledgments content.
    """
    # Journal & author info
    journal: Optional[str] = Field(default=None, alias="Journal", description="Single journal/publication name.")
    title: Optional[str] = Field(default=None, alias="Title", description="Title of the article.")
    journal_field_specialty: Optional[
        Literal[
            "Cardiology - cardiovascular medicine, electrophysiology, vascular medicine, cardiac surgery, and transplantation",
            "Hematology + Thrombosis/Haemostasis + Oncology - includes hematology/oncology, coagulation, thrombosis, thrombolysis, APS, and malignant hematology",
            "Pharmacology + Clinical Pharmacology + Pharmacy + Pharmacokinetics/Pharmacodynamics - includes pharmacogenetics, pharmacometrics, toxicology, drug metabolism, pharmacotherapy, pharmaceutics, and pharmacoeconomics",
            "Internal/General Medicine - general medicine, geriatrics, nephrology, endocrinology, respiratory, and emergency/internal medicine subspecialties",
            "Neurology + Neurosurgery - stroke, neuropharmacology, spine surgery, neurocritical care, and electrophysiology",
            "Anesthesiology + Critical Care + Perioperative/Trauma Medicine - pain management, intensive care, trauma and emergency surgery",
            "Pediatrics + Transplantation + Genetics - pediatric hematology/oncology, congenital and genetic medicine, transplantation",
            "Laboratory + Analytical + Clinical Chemistry Sciences - bioanalysis, mass spectrometry, chromatography, diagnostics, and biochemistry"
        ]
    ] = Field(default=None, alias="Journal Field/Specialty", description="Discipline/specialty of the journal.")
    publication_year: Optional[str] = Field(default=None, alias="Publication Year", description="Four-digit year (e.g., '2022').")
    affiliation_of_first_author: Optional[str] = Field(default=None, alias="Affiliation of First Author")
    country_of_first_author: Optional[str] = Field(default=None, alias="Country of First Author")

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
            "Other"
        ]
    ] = Field(default=None, alias="Study Design", description="Study design (controlled list).")
    study_design_sentence_from_text: Optional[str] = Field(
        default=None, alias="Study Design Sentence from Text",
        description="Exact sentence containing the study design."
    )

    model_config = ConfigDict(populate_by_name=True)


# ---------------------------------------
# 2) Population, Indications, Subgroups
# ---------------------------------------
class ExtractionPopulationIndications(BaseModel):
    """
    Guidelines:
    1) Do not infer or guess. 2) Use null if unsure.
    3) Output only facts explicitly in the PDF.
    4) If ambiguous, set null (do not guess).
    5) Numeric values must be exact.
    6) Resolve conflicts by the clearest statement (title→early pages; patients→methods/results).
    7) Do not use external knowledge.
    8) Ignore References and Acknowledgments content.
    """
    # Patient population
    total_patients: Optional[int] = Field(default=None, alias="Patient Population", description="Total number of patients.")
    total_patients_sentence_from_text: Optional[str] = Field(
        default=None, alias="Patient Population Sentence from Text",
        description="Exact sentence with total patients."
    )

    # DOACs included (measured)
    doacs_included: Optional[
        List[Literal["Apixaban", "Rivaroxaban", "Edoxaban", "Betrixaban", "Dabigatran"]]
    ] = Field(
        default=None, alias="Patient population 1",
        description=(
            "Include a DOAC ONLY if its level was actually measured in this study. "
            "Do not include DOACs only mentioned in Intro/Discussion/external citations."
        )
    )
    doacs_included_sentence_from_text: Optional[List[str]] = Field(
        default=None, alias="DOACs Included Sentence from Text",
        description="Exact sentences with the included DOACs."
    )

    # Indications for anticoagulation (must apply to measured population)
    indication_for_anticoagulation: Optional[
        List[Literal["AF", "Treatment of VTE", "Prevention of VTE", "Other", "Not Reported"]]
    ] = Field(
        default=None, alias="Patient population 2",
        description=(
            "Only include an indication (e.g., AF, VTE) if patients whose DOAC levels were measured had that indication."
        )
    )
    indication_for_anticoagulation_sentence_from_text: Optional[List[str]] = Field(
        default=None, alias="Indications for Anticoagulation Sentence from Text",
        description="Exact sentences with indications."
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
                "Genetic polymorphism (e.g., CYP polymorphism)"
            ]
        ]
    ] = Field(
        default=None, alias="Patient population 3",
        description=(
            "Include only if DOAC levels were measured in that subgroup within this study."
        )
    )
    relevant_subgroups_sentence_from_text: Optional[List[str]] = Field(
        default=None, alias="Relevant Subgroups Sentence from Text",
        description="Exact sentences with the relevant subgroups."
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
                "Risk prediction and clinical outcome association - Thrombosis"
            ]
        ]
    ] = Field(
        default=None, alias="Indications for DOAC Level Measurement",
        description=(
            "Flattened list of explicit reasons DOAC levels were measured in this study’s population. "
            "Include only if the manuscript explicitly states this purpose (not Background/Discussion only)."
        )
    )
    indications_for_doac_level_measurement_sentence_from_text: Optional[List[str]] = Field(
        default=None, alias="Indications for DOAC Level Measurement Sentence from Text",
        description="Exact sentences with the indications."
    )

    model_config = ConfigDict(populate_by_name=True)


# ------------------------------------
# 3) Methods & Assays Blocks
# ------------------------------------
class ExtractionMethods(BaseModel):
    """
    Guidelines:
    1) Do not infer or guess. 2) Use null if unsure.
    3) Output only facts explicitly in the PDF.
    4) If ambiguous, set null (do not guess).
    5) Numeric values must be exact.
    6) Resolve conflicts by the clearest statement (title→early pages; patients→methods/results).
    7) Do not use external knowledge.
    8) Ignore References and Acknowledgments content.
    """
    # DOAC level measurement
    doac_level_measurement: Optional[
        List[
            Literal[
                # Apixaban
                "Apixaban - HPLC-MS (ng/mL)",
                "Apixaban - Calibrated anti-Xa level (ng/mL)",
                "Apixaban - Heparin (UFH/LMWH) anti-Xa level (IU/mL)",

                # Rivaroxaban
                "Rivaroxaban - HPLC-MS (ng/mL)",
                "Rivaroxaban - Calibrated anti-Xa level (ng/mL)",
                "Rivaroxaban - Heparin (UFH/LMWH) anti-Xa level (IU/mL)",

                # Edoxaban
                "Edoxaban - HPLC-MS (ng/mL)",
                "Edoxaban - Calibrated anti-Xa level (ng/mL)",
                "Edoxaban - Heparin (UFH/LMWH) anti-Xa level (IU/mL)",

                # Betrixaban
                "Betrixaban - HPLC-MS (ng/mL)",
                "Betrixaban - Calibrated anti-Xa level (ng/mL)",
                "Betrixaban - Heparin (UFH/LMWH) anti-Xa level (IU/mL)",

                # Dabigatran
                "Dabigatran - Thrombin Time (TT)",
                "Dabigatran - Dilute Thrombin Time (dTT)",
                "Dabigatran - Ecarin Clotting Time (ECT)",
                "Dabigatran - Ecarin Chromogenic Assay (ECA)",
            ]
        ]
    ] = Field(
        default=None,
        alias="DOAC Level Measurement",
        description=(
            "Flattened list of specific analytical DOAC level measurement methodology, "
            "each entry combines DOAC + method."
        )
    )
    doac_level_measurement_sentence_from_text: Optional[List[str]] = Field(
        default=None, alias="DOAC Level Measurement Sentence from Text",
        description="Exact sentences with the DOAC level measurement."
    )
    
    # Reagent Selection
    reagent_selection: Optional[List[str]] = Field( 
        default=None, alias="Reagent Selection", 
        description=( 
            "Narrative synthesis outlining the reagent systems (brand names) used " 
            "for DOAC level measurement, e.g., Stago’s STA-Liquid Anti-Xa, STA-Apixaban calibrator, etc." 
        ) 
    )
    
    # Pre-Analytical Variables
    pre_analytical_variables: Optional[
        List[
            Literal[
                "Blood collection procedures",
                "Collection tube type",
                "Centrifugation speed",
                "Storage temperature"
            ]
        ]
    ] = Field(
        default=None,
        alias="Pre-Analytical Variables",
        description=(
            "Pre-analytical variables actually applied to DOAC level measurement in this study "
            "(not background examples). Include only if used for the specimens measured.\n"
            "Examples:\n"
            "• Blood collection procedures → needle gauge / tourniquet\n"
            "• Collection tube type → e.g., 2.7% citrate BD\n"
            "• Centrifugation speed → e.g., 1500g\n"
            "• Storage temperature → e.g., -80°C"
        )
    )
    pre_analytical_variables_sentence_from_text: Optional[List[str]] = Field(
        default=None, alias="Pre-Analytical Variables Sentence from Text",
        description="Exact sentences with the pre-analytical variables."
    )


    # Conventional Coagulation Tests Concurrently Reported
    coagulation_tests_concurrent: Optional[
        List[
            Literal[
                "Prothrombin time (PT)",
                "Activated partial thromboplastin time (aPTT)"
            ]
        ]
    ] = Field(
        default=None,
        alias="Conventional Coagulation Tests Concurrently Reported",
        description=(
            "Conventional coagulation assays (PT, aPTT) that were reported together with "
            "DOAC level measurement in this study. Include only if used for the specimens measured."
        )
    )
    coagulation_tests_concurrent_sentence_from_text: Optional[List[str]] = Field(
        default=None, alias="Conventional Coagulation Tests Concurrently Reported Sentence from Text",
        description="Exact sentences with the conventional coagulation tests concurrently reported."
    )
    
    
    # Global Coagulation Testing
    global_coagulation_tests: Optional[
        List[
            Literal[
                "Viscoelastic testing (ROTEM/TEG)",
                "Thrombin Generation Assay (TGA)"
            ]
        ]
    ] = Field(
        default=None,
        alias="Global Coagulation Testing",
        description="Global coagulation assays reported in addition to DOAC level testing. Include only if used for the specimens measured."
    )
    global_coagulation_tests_sentence_from_text: Optional[List[str]] = Field(
        default=None, alias="Global Coagulation Testing Sentence from Text",
        description="Exact sentences with the global coagulation tests."
    )

    model_config = ConfigDict(populate_by_name=True)


# ------------------------------------
# 4) Outcomes Blocks
# ------------------------------------
class ExtractionOutcomes(BaseModel):
    """
    Guidelines:
    1) Do not infer or guess. 2) Use null if unsure.
    3) Output only facts explicitly in the PDF.
    4) If ambiguous, set null (do not guess).
    5) Numeric values must be exact.
    6) Resolve conflicts by the clearest statement (title→early pages; patients→methods/results).
    7) Do not use external knowledge.
    8) Ignore References and Acknowledgments content.
    """
    # Timing of DOAC Level Measurement Relative to DOAC Intake
    timing_of_measurement: Optional[
        List[
            Literal[
                "Peak level (2–4 hours post-dose)",
                "Trough level (just prior to next dose)",
                "~11 hours post-dose for apixaban and dabigatran",
                "~23 hours post-dose for rivaroxaban and edoxaban",
                "Random level",
                "Timing not reported"
            ]
        ]
    ] = Field(
        default=None,
        alias="Timing of DOAC level measurement relative to DOAC intake",
        description="Categorical timing of DOAC level sampling relative to DOAC intake."
    )
    timing_of_measurement_sentence_from_text: Optional[List[str]] = Field(
        default=None, alias="Timing of DOAC Level Measurement Relative to DOAC Intake Sentence from Text",
        description="Exact sentences with the timing of DOAC level measurement relative to DOAC intake."
    )

    # Timing (hours since last dose)
    timing_relative_to_last_dose_hours: Optional[str] = Field(
        default=None,
        alias="Timing (hours since last dose)",
        description="If reported numerically: hours since last dose (e.g., median [IQR] or mean ± SD)."
    )
    
    
    
    # A) thresholds the paper LISTS anywhere in its methods/results
    thresholds_listed: Optional[
        List[
            Literal[
                "30 ng/mL",
                "50 ng/mL",
                "75 ng/mL",
                "100 ng/mL",
                "Other"
            ]
        ]
    ] = Field(
        default=None,
        alias="Reported DOAC concentration thresholds/cutoffs (listed)",
        description=(
            "Thresholds/cutoffs explicitly listed by the study (methods/results). "
            "Include only if stated for this study (not background)."
        )
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
                # Other
                "Other – Overall",
                "Other – Elective surgery",
                "Other – Emergency surgery",
                "Other – Major bleeding and anticoagulation reversal",
                "Other – Thrombolysis/acute stroke",
            ]
        ]
    ] = Field(
        default=None,
        alias="Thresholds used to inform clinical management",
        description=(
            "Flattened list of threshold × context pairs explicitly used by the study to guide care. "
            "Include only if the manuscript states the threshold was applied to clinical decisions."
        )
    )
    thresholds_used_for_management_sentence_from_text: Optional[List[str]] = Field(
        default=None, alias="Thresholds used to inform clinical management Sentence from Text",
        description="Exact sentences with the thresholds used to inform clinical management."
    )
    
    
    # Turnaround Time
    turnaround_time: Optional[str] = Field(
        default=None,
        alias="Reported turnaround time",
        description=(
            "Study-defined turnaround time for DOAC level reporting (e.g., time from "
            "sample receipt at the laboratory to release of result). "
            "Include only if clearly specified in this study’s Methods/Results."
        )
    )
    
    
    # Clinical Outcomes
    clinical_outcomes: Optional[
        List[
            Literal[
                "Bleeding/Hemostasis",
                "Thromboembolism",
                "Stroke/Transient Ischemic Attack (TIA)",
                "Pulmonary embolism (PE)",
                "Deep venous thrombosis (DVT)"
            ]
        ]
    ] = Field(
        default=None,
        alias="Clinical Outcomes",
        description="Clinical outcomes explicitly reported in this study."
    )
    clinical_outcomes_sentence_from_text: Optional[List[str]] = Field(
        default=None, alias="Clinical Outcomes Sentence from Text",
        description="Exact sentences with the clinical outcomes."
    )

    # ---- Per-outcome follow-up duration (verbatim) ----
    bleeding_followup_duration: Optional[str] = Field(
        default=None,
        alias="Bleeding/Hemostasis – follow-up duration",
        description="Verbatim duration for bleeding/hemostasis outcome ascertainment (e.g., '30 days', '6 months', 'median 12 [6–24] months'). Only if explicitly reported."
    )
    stroke_tia_followup_duration: Optional[str] = Field(
        default=None,
        alias="Thromboembolism - Stroke/TIA - follow-up duration",
        description="Verbatim duration for stroke/TIA outcome ascertainment. Only if explicitly reported."
    )
    pe_dvt_followup_duration: Optional[str] = Field(
        default=None,
        alias="Thromboembolism - PE/DVT - follow-up duration",
        description="Verbatim duration for PE/DVT outcome ascertainment. Only if explicitly reported."
    )

    # ---- Per-outcome definition notes (verbatim) ----
    bleeding_definition_note: Optional[str] = Field(
        default=None,
        alias="Bleeding/Hemostasis - definition note",
        description="Outcome definition as stated (e.g., 'ISTH major/minor', 'BARC 2–5', or 'not defined'). Verbatim/concise."
    )
    stroke_tia_definition_note: Optional[str] = Field(
        default=None,
        alias="Thromboembolism - Stroke/TIA - definition note",
        description="Outcome definition as stated (e.g., criteria used or 'not defined'). Verbatim/concise."
    )
    pe_dvt_definition_note: Optional[str] = Field(
        default=None,
        alias="Thromboembolism - PE/DVT - definition note",
        description="Outcome definition as stated (e.g., 'imaging-confirmed', specific criteria, or 'not defined'). Verbatim/concise."
    )
    
    model_config = ConfigDict(populate_by_name=True)