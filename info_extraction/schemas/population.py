"""Population, Indications, Subgroups schema."""

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------
# 2) Population, Indications, Subgroups
# ---------------------------------------
class ExtractionPopulationIndications(BaseModel):
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
