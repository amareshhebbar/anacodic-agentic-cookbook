# Copyright 2026 Anacodic AI Labs — https://anacodicai.org
# SPDX-License-Identifier: Apache-2.0

"""The 20 clinical-retrieval benchmark questions, B01-M04.

These are clinical *topics* to retrieve papers about — not patient data — so
they ship here unmodified.

Each entry:
    id                 short code, grouped by domain (B=burn/trauma,
                       W=wound care, BR=breast surgery, H=hand surgery,
                       C=craniofacial, O=oncology, N=nerve regeneration,
                       T=tissue engineering, M=multi-domain)
    query              the natural-language question a retrieval system
                       is asked to answer
    expected_domains   which specialist domain(s) the question should route to
    required_keywords  terms a competent answer's supporting evidence should
                       contain at least one of
    min_evidence_level Oxford CEBM level the retrieved evidence should meet
    ground_truth_facts short factual statements used as the "expected_output"
                       reference for DeepEval's contextual recall / precision

Nothing here is medical advice. The questions exist to measure a retrieval
system, not to answer them yourself — see the repo-root README disclaimer.
"""

from __future__ import annotations

BENCHMARK_QUERIES = [
    # -- Burn / Trauma --------------------------------------------------------
    {
        "id": "B01",
        "query": "What is the recommended timing for skin grafting in deep partial thickness burns?",
        "expected_domains": ["burn_trauma"],
        "required_keywords": ["early excision", "grafting", "TBSA"],
        "min_evidence_level": "Level II",
        "ground_truth_facts": [
            "Early tangential excision within 48-72 hours is associated with reduced blood loss and shorter hospital stay",
            "Split-thickness skin graft is the standard coverage for excised burn wounds",
        ],
    },
    {
        "id": "B02",
        "query": "Parkland formula for fluid resuscitation in burns: evidence and alternatives",
        "expected_domains": ["burn_trauma"],
        "required_keywords": ["Parkland", "Ringer's lactate", "4 mL/kg/%TBSA"],
        "min_evidence_level": "Level II",
        "ground_truth_facts": [
            "Parkland formula: 4 mL/kg per % TBSA over 24 hours, half in first 8 hours",
            "Over-resuscitation risk (fluid creep) documented in multiple cohort studies",
        ],
    },
    # -- Wound Care -------------------------------------------------------------
    {
        "id": "W01",
        "query": "Negative pressure wound therapy for diabetic foot ulcers: outcomes evidence",
        "expected_domains": ["wound_care"],
        "required_keywords": ["NPWT", "VAC", "diabetic foot", "wound closure"],
        "min_evidence_level": "Level II",
        "ground_truth_facts": [
            "NPWT accelerates wound closure compared to standard dressings in diabetic foot ulcers",
            "Randomized controlled trials show reduced amputation rate",
        ],
    },
    {
        "id": "W02",
        "query": "NPUAP pressure injury staging system: classification and clinical application",
        "expected_domains": ["wound_care"],
        "required_keywords": ["Stage I", "Stage II", "Stage III", "Stage IV", "unstageable"],
        "min_evidence_level": "Level V",
        "ground_truth_facts": [
            "Four main stages plus unstageable and deep tissue injury categories",
            "Stage III: full-thickness tissue loss; Stage IV: exposed bone/tendon/muscle",
        ],
    },
    # -- Breast Surgery -----------------------------------------------------------
    {
        "id": "BR01",
        "query": "DIEP flap versus TRAM flap for breast reconstruction: complication rates",
        "expected_domains": ["breast_surgery"],
        "required_keywords": ["DIEP", "TRAM", "abdominal morbidity", "flap failure"],
        "min_evidence_level": "Level II",
        "ground_truth_facts": [
            "DIEP flap associated with lower abdominal morbidity compared to TRAM",
            "Free TRAM and DIEP flap have similar flap survival rates in meta-analyses",
        ],
    },
    {
        "id": "BR02",
        "query": "Capsular contracture after breast augmentation: prevention and treatment",
        "expected_domains": ["breast_surgery"],
        "required_keywords": ["Baker grade", "capsular contracture", "textured", "acellular dermal matrix"],
        "min_evidence_level": "Level III",
        "ground_truth_facts": [
            "Baker Grade III-IV requires surgical intervention",
            "Textured implants and ADM use associated with lower capsular contracture rates",
        ],
    },
    # -- Hand Surgery -------------------------------------------------------------
    {
        "id": "H01",
        "query": "Flexor tendon repair in zone II: surgical technique and rehabilitation protocol",
        "expected_domains": ["hand_surgery"],
        "required_keywords": ["zone II", "flexor tendon", "Verdan", "early active motion"],
        "min_evidence_level": "Level III",
        "ground_truth_facts": [
            "Zone II ('no man's land') requires careful primary repair of FDS and FDP tendons",
            "Early active motion protocols (e.g., Belfast protocol) associated with better outcomes",
        ],
    },
    {
        "id": "H02",
        "query": "Surgical treatment of Dupuytren's contracture: fasciectomy versus collagenase injection",
        "expected_domains": ["hand_surgery"],
        "required_keywords": ["Dupuytren", "fasciectomy", "collagenase", "recurrence"],
        "min_evidence_level": "Level II",
        "ground_truth_facts": [
            "Collagenase Clostridium histolyticum (Xiaflex) approved for metacarpophalangeal and PIP joint contracture",
            "Fasciectomy has lower recurrence rates but higher complication risk",
        ],
    },
    # -- Craniofacial -------------------------------------------------------------
    {
        "id": "C01",
        "query": "Optimal timing for cleft palate repair and speech outcomes",
        "expected_domains": ["craniofacial"],
        "required_keywords": ["cleft palate", "palatoplasty", "velopharyngeal", "speech"],
        "min_evidence_level": "Level II",
        "ground_truth_facts": [
            "Repair between 9-18 months associated with better speech outcomes",
            "Two-stage repair (soft palate early, hard palate later) shows comparable speech with less mid-face growth restriction",
        ],
    },
    {
        "id": "C02",
        "query": "Distraction osteogenesis for mandibular hypoplasia in Pierre Robin sequence",
        "expected_domains": ["craniofacial"],
        "required_keywords": ["distraction osteogenesis", "Pierre Robin", "mandibular", "airway"],
        "min_evidence_level": "Level III",
        "ground_truth_facts": [
            "Mandibular distraction osteogenesis avoids tracheostomy in most Pierre Robin cases",
            "Typical distraction rate: 1 mm/day with 7-day latency period",
        ],
    },
    # -- Oncology -----------------------------------------------------------------
    {
        "id": "O01",
        "query": "Sentinel lymph node biopsy for melanoma: indications and technique",
        "expected_domains": ["oncology"],
        "required_keywords": ["SLNB", "melanoma", "Breslow", "lymphoscintigraphy"],
        "min_evidence_level": "Level I",
        "ground_truth_facts": [
            "SLNB indicated for melanomas >1 mm Breslow thickness",
            "MSLT-I trial established prognostic value of SLNB",
        ],
    },
    {
        "id": "O02",
        "query": "Mohs micrographic surgery for basal cell carcinoma: recurrence rates",
        "expected_domains": ["oncology"],
        "required_keywords": ["Mohs", "BCC", "margin", "recurrence", "five-year"],
        "min_evidence_level": "Level II",
        "ground_truth_facts": [
            "5-year recurrence rate for Mohs surgery: ~1% for primary BCC",
            "Superior for high-risk facial locations compared to wide local excision",
        ],
    },
    # -- Nerve Regeneration ---------------------------------------------------------
    {
        "id": "N01",
        "query": "Sunderland classification of peripheral nerve injuries and prognosis",
        "expected_domains": ["nerve_regeneration"],
        "required_keywords": ["Sunderland", "axonotmesis", "neurotmesis", "recovery"],
        "min_evidence_level": "Level V",
        "ground_truth_facts": [
            "Sunderland Grade I (neuropraxia): full recovery expected",
            "Sunderland Grade V (neurotmesis): requires surgical repair, incomplete recovery",
        ],
    },
    {
        "id": "N02",
        "query": "Nerve transfer versus nerve graft for brachial plexus reconstruction",
        "expected_domains": ["nerve_regeneration"],
        "required_keywords": ["nerve transfer", "nerve graft", "brachial plexus", "reinnervation"],
        "min_evidence_level": "Level III",
        "ground_truth_facts": [
            "Nerve transfers avoid long regeneration distance, preferred for proximal injuries",
            "Spinal accessory to suprascapular nerve transfer: reliable for shoulder abduction restoration",
        ],
    },
    # -- Tissue Engineering ----------------------------------------------------------
    {
        "id": "T01",
        "query": "Acellular dermal matrix (ADM) in breast reconstruction: outcomes evidence",
        "expected_domains": ["tissue_engineering", "breast_surgery"],
        "required_keywords": ["ADM", "acellular dermal matrix", "AlloDerm", "seroma"],
        "min_evidence_level": "Level II",
        "ground_truth_facts": [
            "ADM use in direct-to-implant reconstruction allows single-stage procedure",
            "Higher seroma and infection rates reported with ADM versus no-ADM cohorts",
        ],
    },
    {
        "id": "T02",
        "query": "Platelet-rich plasma (PRP) for wound healing: systematic review evidence",
        "expected_domains": ["tissue_engineering", "wound_care"],
        "required_keywords": ["PRP", "platelet-rich plasma", "growth factors", "wound healing"],
        "min_evidence_level": "Level I",
        "ground_truth_facts": [
            "Heterogeneous evidence — systematic reviews show modest benefit for chronic wounds",
            "Standardization of PRP preparation protocols lacking across trials",
        ],
    },
    # -- Multi-domain ---------------------------------------------------------------
    {
        "id": "M01",
        "query": "Free flap failure rates and salvage in microsurgery: risk factors and outcomes",
        "expected_domains": ["breast_surgery", "oncology"],
        "required_keywords": ["free flap", "thrombosis", "salvage", "re-exploration"],
        "min_evidence_level": "Level II",
        "ground_truth_facts": [
            "Overall free flap failure rate: 1-5% in high-volume centers",
            "Re-exploration within 24 hours associated with ~50% salvage rate",
        ],
    },
    {
        "id": "M02",
        "query": "Effect of smoking on free flap outcomes and wound healing in plastic surgery",
        "expected_domains": ["burn_trauma", "wound_care"],
        "required_keywords": ["smoking", "complications", "wound healing", "nicotine"],
        "min_evidence_level": "Level II",
        "ground_truth_facts": [
            "Smoking associated with 2-3x higher wound complication rate",
            "Smoking cessation >=4 weeks before surgery reduces risk to near non-smoker levels",
        ],
    },
    {
        "id": "M03",
        "query": "Lymphedema surgical management: lymphovenous anastomosis versus vascularized lymph node transfer",
        "expected_domains": ["nerve_regeneration", "oncology"],
        "required_keywords": ["lymphedema", "lymphovenous anastomosis", "LVA", "VLNT"],
        "min_evidence_level": "Level III",
        "ground_truth_facts": [
            "LVA: microsurgical procedure bypassing blocked lymphatics to venous system",
            "VLNT: transfers lymph nodes to deficient region; suitable for advanced disease",
        ],
    },
    {
        "id": "M04",
        "query": "Perforator flap selection for complex trunk reconstruction: outcomes comparison",
        "expected_domains": ["breast_surgery", "general"],
        "required_keywords": ["perforator flap", "TPAP", "SEAP", "reconstruction"],
        "min_evidence_level": "Level III",
        "ground_truth_facts": [
            "Perforator flap selection based on perforator size and pedicle length",
            "Preoperative CT angiography improves flap planning outcomes",
        ],
    },
]
