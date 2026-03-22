"""Methods & Assays schema."""

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ------------------------------------
# 3) Methods & Assays Blocks
# ------------------------------------
class ExtractionMethods(BaseModel):
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
            "TASK: Identify ALL assay methods ACTUALLY USED in THIS study to quantify DOAC levels in PATIENT-DERIVED samples.\n"
            "This is MULTI-LABEL: multiple methods may apply for the same DOAC. NEVER stop after finding one method.\n\n"
            "SCOPE RULES (HARD CONSTRAINTS):\n"
            "1) Use ONLY Methods and Results. IGNORE Background/Introduction/Discussion.\n"
            "2) Include ONLY if applied to patient samples (plasma/serum/whole blood from participants).\n"
            "3) Exclude purely theoretical mentions, future recommendations, or assay descriptions without use in this study.\n"
            "4) Exclude in vitro-only spiking experiments unless performed on patient-derived specimens and used to report patient levels.\n"
            "5) Do NOT infer. If not explicit, do not include.\n\n"
            "ANTI-EARLY-STOPPING (CRITICAL):\n"
            "If you identify LC-MS/HPLC-MS, you MUST continue scanning for additional assays (anti-Xa, dTT, ECT, etc.).\n"
            "LC-MS/HPLC-MS does NOT replace other assays. If both are used, return BOTH.\n\n"
            "REQUIRED TWO-STEP OUTPUT BEHAVIOR:\n"
            "Step 1 (Evidence): Extract verbatim sentences from Methods/Results that state measurement assays.\n"
            "Step 2 (Decision): Based ONLY on those sentences, select ALL matching labels from the allowed list.\n\n"
            "DOAC-SPECIFIC APPLICABILITY:\n"
            "• Factor Xa inhibitors (Apixaban, Rivaroxaban, Edoxaban, Betrixaban): HPLC-MS; calibrated anti-Xa (ng/mL); heparin-calibrated anti-Xa (IU/mL); POCT; Other.\n"
            "• Dabigatran: HPLC-MS; dTT; ECT; ECA; TT; POCT; Other.\n\n"
            "ROLE DOES NOT MATTER (INCLUDE ANYWAY):\n"
            "If an assay is used for quantification, correlation, validation, comparison, or PK profiling on patient samples, it COUNTS.\n\n"
            "DECISION CHECKLIST (RUN IN THIS ORDER FOR EACH DOAC MENTIONED):\n"
            "A) HPLC-MS/LC-MS/LC-MS/MS/UPLC-MS?  -> include '[DOAC] - HPLC-MS (ng/mL)'\n"
            "B) For Xa inhibitors: drug-calibrated anti-Xa in ng/mL? -> include '[DOAC] - Calibrated anti-Xa level (ng/mL)'\n"
            "C) For Xa inhibitors: heparin/LMWH/UFH-calibrated anti-Xa in IU/mL? -> include '[DOAC] - Heparin (UFH/LMWH) anti-Xa level (IU/mL)'\n"
            "D) For Dabigatran: dTT/Hemoclot/DTI assay (diluted thrombin time)? -> include 'Dabigatran - Dilute Thrombin Time (dTT)'\n"
            "E) For Dabigatran: ECT? -> include 'Dabigatran - Ecarin Clotting Time (ECT)'\n"
            "F) For Dabigatran: ECA? -> include 'Dabigatran - Ecarin Chromogenic Assay (ECA)'\n"
            "G) For Dabigatran: TT used for dabigatran assessment? -> include 'Dabigatran - Thrombin Time (TT)'\n"
            "H) POCT explicitly used? -> include '[DOAC] - Qualitative/Point-of-Care (POCT)'\n"
            "I) Any other explicit measurement method not covered above? -> include '[DOAC] - Other'\n\n"
            "KEY DISTINCTIONS (DO NOT CONFUSE):\n"
            "1) Calibrated anti-Xa (ng/mL) requires drug-specific calibration (explicit drug calibrators or DOAC-specific anti-Xa) and ng/mL.\n"
            "2) Heparin-calibrated anti-Xa uses UFH/LMWH standards and reports IU/mL.\n"
            "3) dTT is NOT TT. dTT includes dilution and typically a drug-specific calibrator (e.g., Hemoclot / DTI assays).\n\n"
            "SYNONYM MAP (MATCH ANY VARIANT):\n"
            "HPLC-MS bucket -> HPLC-MS, HPLC/MS, HPLC-MS/MS, HPLC/MS/MS, LC-MS, LC/MS, LC-MS/MS, LC/MS/MS, UPLC-MS, UPLC/MS, UPLC-MS/MS, UPLC/MS/MS, "
            "liquid chromatography mass spectrometry, high-performance liquid chromatography mass spectrometry, mass spectrometry, tandem mass spectrometry.\n"
            "Calibrated anti-Xa (ng/mL) -> drug-specific anti-Xa, DOAC-specific anti-Xa, [drug]-calibrated anti-Xa, chromogenic anti-Xa with [drug] calibrators, "
            "STA-Liquid Anti-Xa + drug calibrator, HemosIL Liquid Anti-Xa + drug calibrators, Biophen, DiXaI, COAMATIC with drug calibrators.\n"
            "Heparin anti-Xa (IU/mL) -> heparin-calibrated anti-Xa, LMWH-calibrated anti-Xa, UFH-calibrated anti-Xa, anti-Xa calibrated for heparin, units IU/mL.\n"
            "Dabigatran dTT -> dTT, diluted thrombin time, dilute thrombin time, dilute TT, Hemoclot, HemosIL DTI, INNOVANCE DTI.\n"
            "ECT -> ecarin clotting time, ECT.\n"
            "ECA -> ecarin chromogenic assay, ECA.\n"
            "TT -> thrombin time, TT.\n\n"
            "COMMON FAILURE MODES (AVOID):\n"
            "• Selecting only HPLC-MS when dTT/ECT/ECA/anti-Xa are also explicitly reported.\n"
            "• Treating LC-MS as a 'reference method' and dropping other assays. Include ALL.\n"
            "• Taking assay mentions from Discussion. Not allowed.\n\n"
            "OUTPUT:\n"
            "Return a list of ALL applicable labels from the allowed set. If no eligible patient-sample DOAC measurement is described, return null."
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
            "CRITICAL EXTRACTION TASK — READ CAREFULLY\n\n"
            "You must identify ONLY those pre-analytical variables that are "
            "EXPLICITLY AND UNAMBIGUOUSLY reported in the METHODS section "
            "for specimens actually used to measure DOAC plasma levels in THIS study.\n\n"
            "DEFAULT RULE (MANDATORY):\n"
            "Assume that NO pre-analytical variables are reported unless explicit "
            "Methods evidence clearly proves otherwise. Absence is the default.\n\n"
            "INCLUDE a variable ONLY when:\n"
            "• The procedure is described in the METHODS section (or equivalent), AND\n"
            "• It was applied to samples analyzed in THIS study (not background, review, or general lab capability), AND\n"
            "• There is explicit procedural detail specific to that variable.\n\n"
            "DO NOT infer, assume, generalize, or extrapolate.\n"
            "If explicit evidence is missing, DO NOT include the variable.\n\n"
            "TWO-STEP DECISION PROCESS (STRICTLY REQUIRED):\n\n"
            "STEP 1 — EVIDENCE CHECK:\n"
            "Search the METHODS for explicit, specimen-level descriptions of:\n"
            "• blood collection technique,\n"
            "• collection tube additives or manufacturers,\n"
            "• centrifugation conditions,\n"
            "• storage conditions.\n\n"
            "If the Methods do NOT explicitly state a procedure for a given variable, "
            "that variable MUST be excluded.\n\n"
            "STEP 2 — VARIABLE-SPECIFIC DECISION RULES:\n\n"
            "1. Blood collection procedures:\n"
            "Include ONLY if technique-level venipuncture details are explicitly reported.\n\n"
            "REQUIRED indicators (at least one must be present):\n"
            "• needle gauge (e.g., 21G, 22G)\n"
            "• tourniquet use or stasis description\n"
            "• venipuncture technique (e.g., single venipuncture, butterfly needle)\n"
            "• patient positioning or fasting state at blood draw\n"
            "• explicit phlebotomy protocol details\n\n"
            "IMPORTANT EXCLUSION RULE:\n"
            "Generic statements such as:\n"
            "• 'blood was collected'\n"
            "• 'peripheral blood samples'\n"
            "• 'venous blood was obtained'\n"
            "DO NOT qualify as blood collection procedures and MUST NOT be flagged.\n\n"
            "2. Collection tube type:\n"
            "Include ONLY if the tube additive and/or manufacturer is explicitly stated.\n\n"
            "Valid indicators include:\n"
            "• EDTA / K2EDTA / K3EDTA\n"
            "• sodium citrate (with concentration if provided)\n"
            "• heparin (UFH or LMWH)\n"
            "• serum or plasma separator tubes\n"
            "• explicit brand names (e.g., BD Vacutainer, Sarstedt)\n\n"
            "3. Centrifugation speed:\n"
            "Include ONLY if centrifugation conditions are explicitly reported.\n\n"
            "Required indicators:\n"
            "• relative centrifugal force (× g)\n"
            "• rpm values\n"
            "• duration of centrifugation\n\n"
            "Mentions of 'plasma was separated' WITHOUT centrifugation parameters "
            "DO NOT qualify and MUST NOT be flagged.\n\n"
            "4. Storage temperature:\n"
            "Include ONLY if storage conditions are explicitly stated.\n\n"
            "Valid indicators include:\n"
            "• −80°C, −70°C, −20°C\n"
            "• 4°C or refrigerated storage\n"
            "• room temperature with explicit wording\n\n"
            "Silence on storage conditions MUST be interpreted as NOT REPORTED.\n\n"
            "COMMON ERRORS TO AVOID (STRICTLY PROHIBITED):\n"
            "• Do NOT infer procedures based on standard laboratory practice\n"
            "• Do NOT count background or guideline statements\n"
            "• Do NOT assume missing details\n"
            "• Do NOT upcode variables based on partial or generic wording\n\n"
            "FINAL OUTPUT RULE:\n"
            "Return ONLY the variables that meet ALL criteria above.\n"
            "If none meet criteria, return null."
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
