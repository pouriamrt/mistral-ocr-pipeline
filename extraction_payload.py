from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator
from enum import Enum

class ImageType(str, Enum):
    GRAPH = "graph"
    TEXT = "text"
    TABLE = "table"
    IMAGE = "image"

class Image(BaseModel):
    image_type: ImageType = Field(..., description="The type of the image. Must be one of 'graph', 'text', 'table' or 'image'.")
    description: str = Field(..., description="A description of the image.")

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
    ] = Field(
        default=None, 
        alias="Study Design", 
        description=(
            "Study design (controlled list).\n\n"
            "Classification rule (to prevent overuse of 'Non-Randomized Observational Study'):\n"
            "• Always pick the most specific applicable category first. Use 'Non-Randomized Observational Study' ONLY when none of the specific designs below fit.\n"
            "• If multiple cues appear, resolve by this specificity priority:\n"
            "   RCT > Diagnostic Test Accuracy > Pharmacokinetic > Case-Control > Cohort > Cross-Sectional > "
            "   Non-Randomized Experimental > Non-Randomized Observational > Case Series > Case Report > "
            "   In Silico Simulation Analysis > Systematic Review > Qualitative Research > Other.\n"
            "• Do not infer; use explicit language in Title/Abstract/Methods. If ambiguous, return null.\n\n"
            "Disambiguation cues (non-exhaustive):\n"
            "• Randomized Controlled Trial: randomized, allocation, double-blind, placebo-controlled, trial registration, intention-to-treat, control arm, primary endpoint.\n"
            "• Cohort Study: prospective/retrospective cohort, follow-up, incidence, registry, time-to-event, hazard ratio, baseline characteristics.\n"
            "• Non-Randomized Experimental Study: interventional but no randomization; single-arm, open-label, pilot intervention, protocol evaluation, dose adjustment.\n"
            "• Non-Randomized Observational Study: observational/registry/chart review, real-world, retrospective analysis; no assigned intervention.\n"
            "• Cross-Sectional Study: cross-sectional, point prevalence, single time point, surveyed, baseline-only measurement.\n"
            "• Case-Control Study: case-control, matched controls, odds ratio, retrospective comparison, 'cases were matched to controls'.\n"
            "• Pharmacokinetic Study: pharmacokinetic/PK, Cmax, AUC, half-life, sampling at trough/peak, LC-MS/chromogenic anti-Xa.\n"
            "• In Silico Simulation Analysis: modeling/simulation, population PK/PD, PBPK, Monte Carlo, virtual/simulated cohort.\n"
            "• Systematic Review: systematic review/meta-analysis, PRISMA, pooled analysis, predefined inclusion criteria, literature search.\n"
            "• Qualitative Research: qualitative, interviews/focus groups, thematic/framework analysis, perceptions/attitudes.\n"
            "• Diagnostic Test Accuracy Study: sensitivity/specificity, ROC/AUC, agreement/validation vs reference standard, assay comparison (e.g., LC-MS vs anti-Xa).\n"
            "• Case Series: case series/clinical experience; multiple patients, no control, small N with tabulated individual data.\n"
            "• Case Report: case report/single patient/rare event with detailed narrative.\n"
            "• Other: hybrid/methodological (validation, method development, mixed methods) not fitting above.\n"
        ),
    )
    study_design_cues_detected: Optional[List[str]] = Field(
        default=None,
        alias="Study Design - cues detected",
        description=(
            "Verbatim keywords/phrases found that support the chosen design "
            "(e.g., 'randomized', 'matched controls', 'ROC AUC 0.91', 'Cmax/AUC'). "
            "Use null if not clearly present."
        )
    )
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
            "Include a subgroup ONLY if DOAC levels were measured within that subgroup in THIS study "
            "(e.g., calibrated anti-Xa, LC/LC-MS/MS, thrombin-based assays for dabigatran). "
            "Do NOT infer. If ambiguous, leave null. If multiple subgroups are analyzed and measured, "
            "return all that apply.\n\n"

            "General exclusions for ALL subgroups: (a) Mentioned only in baseline characteristics without level stratification; "
            "(b) Protocols/guidelines/hypothetical modeling without patient-level measurements; "
            "(c) Claims/registry outcomes without measured DOAC levels; "
            "(d) In vitro/animal-only data.\n\n"

            "Subgroup-specific cues:\n"
            "1) High body weight (obesity)\n"
            "   Positive keywords: obesity/obese, high body weight, BMI ≥30/≥35/≥40 kg/m², morbid/severe obesity, weight >120 kg, "
            "   'extreme body weight', 'super-obese'.\n"
            "   Signals: dosing/PK in obesity; on-treatment concentrations in obese patients; anti-Xa calibration in high BMI.\n"
            "   Exclusions: weight-adjusted dose discussed but no measured levels; obesity only appears in baseline table.\n"
            "   Edge: post-bariatric obesity → classify here AND Bariatric if BOTH are explicitly analyzed with measured levels.\n\n"

            "2) Low body weight\n"
            "   Positive keywords: low body weight, underweight, ≤60 kg, <50 kg, ≤45 kg, cachexia, sarcopenia.\n"
            "   Signals: level comparisons by ≤60 vs >60 kg; reduced dose criteria analyzed with measured levels.\n"
            "   Exclusions: only dose-label criteria mentioned; no measured levels.\n\n"

            "3) Chronic kidney disease/dialysis\n"
            "   Positive keywords: CKD, renal impairment, eGFR, CrCl (Cockcroft-Gault), KDIGO stages, ESRD/ESKD, hemodialysis, peritoneal dialysis.\n"
            "   Signals: trough/peak levels by renal strata; accumulation; timing vs dialysis; dialyzability.\n"
            "   Exclusions: creatinine reported without renal stratification; anti-Xa 'activity' not calibrated to DOAC.\n\n"

            "4) Bariatric surgery/malabsorption\n"
            "   Positive keywords: bariatric (Roux-en-Y, sleeve, bypass, BPD/DS), short-bowel, celiac, Crohn’s with resection, malabsorption, "
            "   'altered absorption'.\n"
            "   Signals: pre-/post-op levels, AUC/peak comparisons, time since surgery.\n"
            "   Exclusions: perioperative thromboprophylaxis without DOAC levels.\n\n"

            "5) Drug-DOAC pharmacokinetic interactions\n"
            "   Positive keywords: P-gp, CYP3A4 inhibitors/inducers, DDI/drug interaction; named comedications (e.g., amiodarone, verapamil, "
            "   diltiazem, dronedarone, ketoconazole/itraconazole/posaconazole/voriconazole, ritonavir/cobicistat, clarithromycin/erythromycin, "
            "   cyclosporine/tacrolimus; inducers: rifampin, carbamazepine, phenytoin, phenobarbital, primidone, St. John’s wort).\n"
            "   Signals: level shift present vs absent; dose adjustment guided by measured levels.\n"
            "   Exclusions: claims-data risk without level measurements.\n\n"

            "6) Advanced age/frailty\n"
            "   Positive keywords: elderly, ≥75/≥80, octogenarian, nonagenarian, geriatric, frailty (CFS/Rockwood/HFRS).\n"
            "   Signals: levels by age strata; frailty index vs levels; dose-reduction age criterion analyzed with levels.\n"
            "   Exclusions: age appears only in baseline; no level stratification.\n\n"

            "7) Elective procedure/surgery\n"
            "   Positive keywords: elective surgery, planned procedure, neuraxial anesthesia, perioperative management, hold time, "
            "   residual level thresholds (e.g., 30 or 50 ng/mL).\n"
            "   Signals: pre-op levels guiding timing/clearance; correlation of level with bleeding in ELECTIVE setting.\n"
            "   Exclusions: protocols without measured pre-op levels.\n\n"

            "8) Urgent/emergent procedure/surgery\n"
            "   Positive keywords: urgent/emergent surgery, trauma, unplanned procedure, hip fracture ≤24–48 h, emergency endoscopy.\n"
            "   Signals: rapid level testing; proceed/cancel decisions based on level; time-to-surgery vs level.\n"
            "   Exclusions: emergent cases described but no measured levels guiding care.\n\n"

            "9) Acute stroke/thrombolysis\n"
            "   Positive keywords: acute ischemic stroke, thrombolysis (alteplase/tenecteplase, rtPA/tPA), thrombectomy, lytic eligibility, "
            "   residual concentration.\n"
            "   Signals: thresholds used to qualify/deny lysis; associations with hemorrhagic transformation/outcomes; calibrated anti-Xa or LC-MS/MS in protocol.\n"
            "   Exclusions: stroke registries without levels; lysis outcomes without level quantification; modeling/guidelines only.\n\n"

            "10) DOAC-associated bleeding + DOAC Reversal\n"
            "   Positive keywords: major/life-threatening bleeding, ICH, GI bleed, retroperitoneal; andexanet alfa, idarucizumab, PCC/aPCC, ciraparantag, reversal.\n"
            "   Signals: level at presentation; pre-/post-reversal levels; baseline concentration vs hemostatic efficacy; quantified residual level after reversal.\n"
            "   Exclusions: bleeding/reversal studies without level measurements; in vitro/animal; single case without numeric level.\n\n"

            "11) Genetic polymorphism (e.g., CYP polymorphism)\n"
            "   Positive keywords: pharmacogenetics/pharmacogenomics, SNP/rs identifiers, genotype/allele; CYP3A4/3A5/2J2, ABCB1 (P-gp), CES1, UGT, SLCO1B1.\n"
            "   Signals: levels stratified by genotype; genotype associations with PK metrics (AUC, trough, peak, clearance).\n"
            "   Exclusions: genotyping without measured DOAC levels; simulations only; review-only; animal/cell studies.\n"
        ),
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
            "Return ALL explicit reasons the study measured DOAC levels, as stated in Methods/Results. "
            "Include ONLY if patient samples were actually quantified in THIS study. "
            "Exclude Background/Discussion-only rationale, simulations without patient data, and registries with no level measurements.\n\n"

            "General cues for inclusion: purpose phrasing like 'measured to…', 'levels were used to…', "
            "'we evaluated exposure…', 'guided clinical decision', with numeric concentrations or calibrated anti-Xa/LC-MS/MS results.\n\n"

            "Category cues:\n"
            "1) Confirm adherence — Keywords: adherence/compliance/persistence, missed dose, verify/confirm intake/last dose. "
            "Signals: trough/undetectable levels used to confirm/refute ingestion; compare self-report vs measured level. "
            "Exclusions: questionnaires/refill/pill count only.\n\n"

            "2) Evaluate DOAC level exposure (condition-specific):\n"
            "  2a) Bariatric surgery — bariatric, Roux-en-Y, sleeve, bypass, BPD/DS, short-bowel, malabsorption. "
            "      Signals: pre/post-op levels, AUC/peak/trough vs time since surgery. Exclusions: dosing talk only.\n"
            "  2b) Drug–DOAC interaction — DDI, P-gp, CYP3A4/5 inhibitors/inducers (e.g., amiodarone, azoles, ritonavir; rifampin, carbamazepine). "
            "      Signals: level shift with/without comedication. Exclusions: prescribing data only.\n"
            "  2c) Chronic kidney failure — CKD, eGFR/CrCl strata, ESRD/ESKD, hemo/peritoneal dialysis. "
            "      Signals: accumulation/clearance by renal stage; timing vs dialysis. Exclusions: creatinine without level strata.\n"
            "  2d) Obesity — BMI ≥40, weight >120 kg, morbid/severe obesity. Signals: levels/AUC vs BMI groups. "
            "      Exclusions: baseline only.\n"
            "  2e) Residual level after elective interruption — residual/pre-op level, hold time, timing of last dose. "
            "      Signals: measured pre-procedure level to meet <30–50 ng/mL threshold. Exclusions: timing protocols without levels.\n\n"

            "3) Identify predictors of DOAC level exposure — predictors/determinants/covariates, regression/association of levels with factors. "
            "Exclusions: predictors of outcomes without concentration analysis.\n"
            "  3a) Cmax, Ctrough, AUC — explicit PK parameters (Cmax/Ctrough/AUC/Tmax) calculated from patient samples; exclude label/simulation-only.\n\n"

            "4) Guide clinical decision-making — therapeutic drug monitoring; levels directly inform care. "
            "Exclusions: levels measured for research reporting only.\n"
            "  4a) Urgent surgery — emergency/trauma/hip fracture/endoscopy timing guided by measured level.\n"
            "  4b) Major bleeding + reversal — ICH/GI bleed; andexanet/idarucizumab/PCC; pre/post-reversal levels; efficacy vs baseline level.\n"
            "  4c) Thrombolysis — acute ischemic stroke; alteplase/tenecteplase eligibility determined by measured level.\n"
            "  4d) Guide dose adjustment — dose increase/reduction explicitly based on measured concentration.\n\n"

            "5) Measure correlation with other laboratory techniques — quantitative correlation/validation vs another test. "
            "Exclusions: qualitative statements without numeric comparison.\n"
            "  5a) Conventional coagulation testing — PT/INR, aPTT, TT/dTT, ECT, ROTEM/viscoelastic vs measured DOAC concentration.\n"
            "  5b) HPLC-MS vs calibrated anti-Xa measurement — method comparison/validation using clinical samples.\n\n"

            "6) Risk prediction and clinical outcome association — levels associated with outcomes, thresholds/ROC used. "
            "Exclusions: outcomes without measured concentrations.\n"
            "  6a) Bleeding — ISTH major, ICH, GI bleeding vs level.\n"
            "  6b) Thrombosis — stroke/VTE/DVT/PE vs level."
        ),
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
            "Flattened list of specific analytical DOAC level measurement methodology, "
            "each entry combines DOAC + method. "
            "Include ONLY if this method was actually used in THIS study to quantify DOAC level in patients. "
            "Exclude: background mentions of potential assays; assay description without patient sample quantification."
        ),
    )
    doac_level_measurement_sentence_from_text: Optional[List[str]] = Field(
        default=None, alias="DOAC Level Measurement Sentence from Text",
        description="Exact sentences with the DOAC level measurement."
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
            "Return ALL assay descriptor(s) that were actually used in THIS study to quantify the DOAC level "
            "(patient sample measurements only). Do NOT infer from Background/Discussion.\n\n"

            "Definitions:\n"
            "• Calibrated anti-Xa assay (ng/mL) = DOAC-specific calibration materials were used.\n"
            "  Common systems: Stago STA-Liquid Anti-Xa + drug calibrator; BIOPHEN DiXaI/DiXaL + drug calibrators; "
            "  TECHNOVIEW (drug-specific); HemosIL Liquid Anti-Xa + drug calibrators; Innovance Heparin anti-Xa with drug calibrators; "
            "  COAMATIC / Berichrom / Rotachrom with drug calibrators.\n\n"

            "• Heparin-calibrated anti-Xa assay (IU/mL) = LMWH/UFH-calibrated assay used with NO drug-specific calibration.\n\n"

            "• LC-MS/MS quantitative assay (ng/mL) = mass-spectrometry-based direct concentration measurement "
            "of the DOAC (reference standard method).\n\n"

            "• Qualitative / Point-of-Care (POCT) = DOAC Dipstick or equivalent qualitative device.\n\n"

            "• Dilute Thrombin Time (dTT) calibrated (ng/mL) = dabigatran-specific calibrated clotting assay "
            "(e.g., Hemoclot Thrombin Inhibitor / HemosIL DTI / INNOVANCE DTI).\n\n"

            "• Ecarin-based assays (ng/mL) = calibrated dabigatran methods: ECT (clot-based) or ECA (chromogenic) "
            "(e.g., STA-ECA II / ECA-T).\n\n"

            "• Non-calibrated TT (seconds) = qualitative TT index sensitive to dabigatran at low levels, NOT quantitative.\n\n"

            "Include only methods actually applied to patient samples in THIS study. "
            "Exclude laboratory capabilities mentioned but NOT used, and exclude review-style brand lists unless performed."
        ),
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
                "Trough level - ~11 hours post-dose for apixaban and dabigatran",
                "Trough level - ~23 hours post-dose for rivaroxaban and edoxaban",
                "Random level",
                "Timing not reported"
            ]
        ]
    ] = Field(
        default=None,
        alias="Timing of DOAC level measurement relative to DOAC intake",
        description=(
            "Timing category EXACTLY as stated in the study.\n\n"
            "Interpretation rules:\n"
            "• ‘Peak level’ = 2–4h post-dose.\n"
            "• The ~11h (apixaban/dabigatran) and ~23h (rivaroxaban/edoxaban) literals are BOTH considered trough timing "
            "and must not be placed under a separate category.\n"
            "• ‘Random level’ = timing reported but unclear whether peak or trough.\n"
            "• ‘Timing not reported’ = no timing provided in Methods/Results.\n\n"
            "Select ALL that apply if a study measured multiple timepoints."
        )
    )
    @field_validator("timing_of_measurement", mode="after")
    def _dedupe_trough_variants(cls, v):
        if not v:
            return v
        s = set(v)
        specific = {
            "Trough level - ~11 hours post-dose for apixaban and dabigatran",
            "Trough level - ~23 hours post-dose for rivaroxaban and edoxaban",
        }
        generic = "Trough level (just prior to next dose)"
        # If any specific trough is present, drop the generic trough
        if s & specific and generic in s:
            s.remove(generic)
        # Return in original order, filtered
        return [x for x in v if x in s]
    
    timing_of_measurement_sentence_from_text: Optional[List[str]] = Field(
        default=None, alias="Timing of DOAC Level Measurement Relative to DOAC Intake Sentence from Text",
        description="Exact sentences with the timing of DOAC level measurement relative to DOAC intake."
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
    thresholds_used_for_management_other_category_details: Optional[List[str]] = Field(
        default=None,
        alias="Thresholds used to inform clinical management - Other category details",
        description=(
            "ONLY populate this if the study reports a threshold used for clinical decision-making that "
            "does NOT fall into any pre-specified threshold category.\n\n"
            "Extract the *exact sentence(s)* or *verbatim clause* from the Methods/Results that describe the "
            "non-standard threshold (e.g., surgical team used 30–40 ng/mL for neuraxial anesthesia despite "
            "not specifying calibrated assay criteria).\n\n"
            "These verbatim extracts will later be exported and grouped in Excel to characterize the ‘Other’ "
            "bucket for narrative synthesis — so preserve wording precisely, no interpretation or rewriting."
        ),
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
        description=(
            "Outcomes that were explicitly measured in THIS study (described in Methods and reported in Results). "
            "Do NOT include outcomes only mentioned in Introduction/Discussion."
        )
    )
    clinical_outcomes_sentence_from_text: Optional[List[str]] = Field(
        default=None, alias="Clinical Outcomes Sentence from Text",
        description="Exact sentences confirming that the outcome(s) were measured and reported in this study."
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
            "Select ONLY if BOTH conditions are true in THIS study:\n"
            "1) The outcome (Bleeding, Stroke/TIA, PE/DVT) was explicitly measured as an endpoint "
            "   (i.e., described in Methods AND reported in Results — NOT just mentioned in Introduction/Discussion).\n"
            "2) The follow-up window for outcome ascertainment was explicitly reported (e.g., '30 days', '3 months').\n\n"
            "Choose the single literal that matches the outcome + duration category. "
            "If duration not reported → do NOT select any value for that outcome. "
            "If multiple outcomes in the same study report different durations → include multiple literals.\n\n"
            "Do NOT infer, map, or approximate. ONLY assign when the study directly reports both outcome + duration."
        )
    )
    clinical_outcome_followup_sentence_from_text: Optional[List[str]] = Field(
        default=None, alias="Clinical Outcome - follow-up duration Sentence from Text",
        description="Exact sentences with the clinical outcome follow-up duration."
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
            "Select ONLY if the study explicitly defined how this outcome was adjudicated.\n"
            "Bleeding/Hemostasis → pick the exact definition taxonomy used.\n"
            "Stroke/TIA and PE/DVT → choose 'Defined' only if the study clearly cites objective clinical "
            "and/or imaging criteria or formal guideline/adjudication standard.\n\n"
            "Do NOT assign any value if:\n"
            "• The outcome was only mentioned narratively (e.g., in Background) AND not measured in Results.\n"
            "• The study reported the outcome but did not provide ANY definition or diagnostic criteria.\n\n"
            "Multiple selections allowed if multiple outcome domains in THIS study each have explicit definitions."
        ),
    )
    clinical_outcome_definition_sentence_from_text: Optional[List[str]] = Field(
        default=None, alias="Clinical Outcome - definition Sentence from Text",
        description="Exact sentences with the clinical outcome definition."
    )
    
    model_config = ConfigDict(populate_by_name=True)