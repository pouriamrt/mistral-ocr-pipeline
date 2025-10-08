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
    

class ExtractionPayload(BaseModel):
    ######################################### Journal and Author information #########################################
    journal: Optional[str] = Field(
        default=None,
        alias="Journal",
        description="Single journal or publication name (only one value allowed)."
    )
    title: Optional[str] = Field(
        default=None,
        alias="Title",
        description="Title of the article."
    )
    journal_field_specialty: Optional[str] = Field(
        default=None,
        alias="Journal Field/Specialty",
        description="Discipline or specialty focus of the journal (e.g., Cardiology, Hematology)."
    )
    publication_year: Optional[str] = Field(
        default=None,
        alias="Publication Year",
        description="Four-digit publication year of the article (e.g., '2022')."
    )
    affiliation_of_first_author: Optional[str] = Field(
        default=None,
        alias="Affiliation of First Author",
        description="Institution/department of the first-listed author (verbatim if possible)."
    )
    country_of_first_author: Optional[str] = Field(
        default=None,
        alias="Country of First Author",
        description="Country associated with the first author’s affiliation."
    )
    
    ######################################### Study Design #########################################
    study_design: Optional[
        Literal[
            "Prospective/Retrospective/Cross-sectional",
            "Case Report",
            "Case Series",
            "Cohort (Interventional)",
            "Cohort (Observational)",
            "Randomized Controlled Trial",
            "Pharmacokinetic Analysis",
            "Other / Not specified",
        ]
    ] = Field(
        default=None, 
        alias="Study Design",
        description="Type of study design identified in the paper."
    )
    
    ######################################### Patient Population #########################################
    total_patients: Optional[int] = Field(
        default=None,
        alias="Patient Population",
        description="Total number of patients included in the study."
    )
    
    doacs_included: Optional[
        List[
            Literal[
                "Apixaban", "Rivaroxaban", "Edoxaban", "Betrixaban", "Dabigatran"]
            ]
        ] = Field(default=None, 
                  alias="Patient population 1", 
                  description="List of DOACs included in the study.")
    
    indication_for_anticoagulation: Optional[
        List[
            Literal[
                "AF",
                "Treatment of VTE",
                "Prevention of VTE",
                "Other",
                "Not Reported"
            ]
        ]
    ] = Field(
        default=None,
        alias="Patient population 2",
        description="List of indications for anticoagulation reported in the study."
    )
    
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
        default=None,
        alias="Patient population 3",
        description="Relevant patient subgroups or focus areas studied in the paper."
    )
    
    ######################################### Main Reasons #########################################
    main_reasons: Optional[
        List[
            Literal[
                "Confirm adherence",
                "Evaluate DOAC level exposure",
                "Identify predictors of DOAC level exposure",
                "Cmax, Ctrough, AUC",
                "Guide clinical decision-making",
                "Urgent surgery",
                "Major bleeding and reversal agent administration",
                "Thrombolysis",
                "Guide dose adjustment",
                "Measure correlation with other laboratory techniques",
                "Risk prediction and clinical outcome association"
            ]
        ]
    ] = Field(
        default=None,
        alias="Indications for DOAC Level Measurement",
        description="Primary reasons researchers measured DOAC levels in the study."
    )
    
    exposure_contexts: Optional[
        List[
            Literal[
                "Bariatric surgery",
                "Drug-DOAC interaction",
                "Chronic kidney failure",
                "Obesity",
                "Residual DOAC level after elective interruption",
                "Conventional coagulation testing (e.g., prothrombin time)",
                "HPLC-MS vs calibrated anti-Xa measurement",
                "Bleeding",
                "Thrombosis"
            ]
        ]
    ] = Field(
        default=None,
        alias="DOAC Level Exposure Contexts",
        description="Specific contexts or conditions related to DOAC level evaluation."
    )
    
    ######################################### Methodology ###########################################
    stratified_by: Optional[
        List[
            Literal[
                "Apixaban",
                "Rivaroxaban",
                "Edoxaban",
                "Betrixaban",
                "Dabigatran"
            ]
        ]
    ] = Field(
        default=None,
        alias="DOAC Level Measurement - Stratified by",
        description="List of DOACs for which level measurements were stratified."
    )

    measurement_methodology: Optional[
        List[
            Literal[
                "HPLC-MS (ng/mL)",
                "Calibrated anti-Xa level (ng/mL or IU/mL)",
                "Ecarin chromogenic assay",
                "Ecarin clotting time (ECT)",
                "Thrombin time (TT)",
                "Dilute thrombin time (dTT)"
            ]
        ]
    ] = Field(
        default=None,
        alias="DOAC Level Measurement - Methodology",
        description="Analytical methods used for measuring DOAC levels."
    )
    
    ######################################### Reagent Selection ###########################################
    reagent_selection: Optional[List[str]] = Field(
        default=None,
        alias="DOAC Level Measurement 1",
        description=(
            "Narrative synthesis outlining the reagent systems (brand names) used "
            "for DOAC level measurement, e.g., Stago’s STA-Liquid Anti-Xa, STA-Apixaban calibrator, etc."
        )
    )
    
    ######################################### Pre-analytical Variables ###########################################
    pre_analytical_variables: Optional[List[str]] = Field(
        default=None,
        alias="DOAC Level Measurement 2",
        description=(
            "Narrative synthesis of pre-analytical variables and assay conditions used "
            "for DOAC level measurement, e.g., blood collection procedures, "
            "collection tube types, centrifugation speed, and storage temperature."
        )
    )
    blood_collection_procedure: Optional[str] = Field(
        default=None,
        description="Details on blood collection method, such as needle gauge or tourniquet technique."
    )
    collection_tube_type: Optional[str] = Field(
        default=None,
        description="Type of collection tube used, e.g., 2.7% citrate Becton Dickinson."
    )
    centrifugation_speed: Optional[str] = Field(
        default=None,
        description="Centrifugation speed or protocol used before assay."
    )
    storage_temperature: Optional[str] = Field(
        default=None,
        description="Storage temperature for samples, e.g., -80°C."
    )
    
    ######################################### Coagulation Testing ###########################################
    tests_performed: Optional[
        List[
            Literal[
                "Prothrombin time (PT)",
                "Activated partial thromboplastin time (aPTT)",
                "Thrombin time (TT)"
            ]
        ]
    ] = Field(
        default=None,
        alias="Coagulation Testing",
        description="Coagulation tests performed overall and/or stratified by each DOAC."
    )
    stratified_by_doac: Optional[List[str]] = Field(
        default=None,
        description="List of DOACs for which coagulation testing results were stratified, e.g., apixaban, rivaroxaban, dabigatran."
    )
    
    ######################################### Timing of Measurement ###########################################
    timing_of_measurement: Optional[
        List[
            Literal[
                "Peak level (2-4 hours post-dose)",
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
        description="Reported timing of DOAC level measurement relative to dose administration."
    )
    
    ######################################### Dosing Regimen ###########################################
    dosing_regimen_peak: Optional[
        List[
            Literal[
                # Apixaban
                "10 mg po BID",
                "5 mg po BID",
                "2.5 mg po BID",
                # Rivaroxaban
                "15 mg po BID",
                "20 mg po OD",
                "15 mg po OD",
                "10 mg po OD",
                "2.5 mg po BID",
                # Edoxaban
                "60 mg po OD",
                "30 mg po OD",
                "15 mg po OD",
                # Dabigatran
                "150 mg po BID",
                "110 mg po BID"
            ]
        ]
    ] = Field(
        default=None,
        alias="Peak DOAC Level Result (measured 2-4 hours post-dose)",
        description="Dosing regimen associated with the measured DOAC peak level (2–4 hours post-dose)."
    )
    
    dosing_regimen_trough: Optional[
        List[
            Literal[
                # Apixaban
                "10 mg po BID",
                "5 mg po BID",
                "2.5 mg po BID",
                # Rivaroxaban
                "15 mg po BID",
                "20 mg po OD",
                "15 mg po OD",
                "10 mg po OD",
                "2.5 mg po BID",
                # Edoxaban
                "60 mg po OD",
                "30 mg po OD",
                "15 mg po OD",
                # Dabigatran
                "150 mg po BID",
                "110 mg po BID"
            ]
        ]
    ] = Field(
        default=None,
        alias = "Trough DOAC Level Result (measured just prior to next dose)",
        description="Dosing regimen associated with the measured DOAC trough level (just prior to next dose)."
    )

    ######################################### Thresholds ###########################################
    thresholds: Optional[
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
        alias="Reported DOAC concentration thresholds/cutoffs",
        description="Reported DOAC concentration thresholds or cutoffs, overall and stratified by indication for DOAC level testing."
    )
    
    
    ######################################### Turnaround Time ###########################################
    turnaround_time: Optional[str] = Field(
        default=None,
        alias="Reported turnaround time",
        description=(
            "Study-defined turnaround time, typically measured as the duration "
            "from sample receipt at the laboratory to release of result (e.g., '2 hours', 'within 24 hours')."
        )
    )
    
    ######################################### Clinical Outcomes ###########################################
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
        alias="Reported Clinical Outcome Estimates",
        description="Reported clinical outcome estimates observed or analyzed in the study."
    )
    
    
    ######################################### Associated Outcomes ###########################################
    associated_outcomes: Optional[
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
        alias="Associations Between DOAC Levels and Clinical Outcomes",
        description=(
            "Reported associations between DOAC concentration levels and specific clinical outcomes, "
            "such as bleeding, thrombosis, or thromboembolic events."
        )
    )
    
    ######################################### Assay Types ###########################################
    assay_types: Optional[
        List[
            Literal[
                "Coagulation testing",
                "Anti-Xa assays with LMWH calibrators (IU/mL)",
                "Viscoelastic testing",
                "Thrombin generation assays"
            ]
        ]
    ] = Field(
        default=None,
        alias="Diagnostic Performance of Comparator Assays",
        description="Main categories of diagnostic comparator assays evaluated in the study."
    )

    coagulation_subtests: Optional[
        List[
            Literal[
                "Prothrombin time",
                "Activated partial thromboplastin time",
                "Dilute thrombin time",
                "Thrombin time"
            ]
        ]
    ] = Field(
        default=None,
        description="Specific coagulation subtests performed under the coagulation testing category."
    )

    performance_metrics: Optional[
        List[
            Literal[
                "Sensitivity",
                "Specificity",
                "Positive predictive value",
                "Negative predictive value"
            ]
        ]
    ] = Field(
        default=None,
        description=(
            "Narrative synthesis of diagnostic test performance metrics reported "
            "for each comparator assay (e.g., coagulation testing vs DOAC level, "
            "LMWH-calibrated anti-Xa assay)."
        )
    )
            
    # allow population by field name or alias
    model_config = ConfigDict(populate_by_name=True)
