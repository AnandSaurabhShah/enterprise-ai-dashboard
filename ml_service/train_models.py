from __future__ import annotations

import itertools
import random
from pathlib import Path

import joblib
import numpy as np
from rapidfuzz import fuzz
from sklearn.ensemble import IsolationForest, RandomForestClassifier, RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline


BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"
RANDOM = random.Random(42)
COMMON_INDIAN_PREFIXES = [
    "ग्राहक संदेश:",
    "वॉइस नोट:",
    "विक्रेता अपडेट:",
    "வாடிக்கையாளர் குறிப்பு:",
    "వినియోగదారు సందేశం:",
    "ಗ್ರಾಹಕ ಅಪ್ಡೇಟ್:",
]
COMMON_INDIAN_SUFFIXES = [
    "कृपया आज देखें",
    "कृपया तुरंत बताएं",
    "இன்று சரிபார்க்கவும்",
    "దయచేసి వెంటనే చూడండి",
    "ಇಂದು ಪರಿಶೀಲಿಸಿ",
]

def _ensure_dirs() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def _save(name: str, model) -> None:
    joblib.dump(model, ARTIFACTS_DIR / f"{name}.joblib")


def _text_pipeline() -> Pipeline:
    return Pipeline(
        [
            (
                "features",
                FeatureUnion(
                    [
                        (
                            "word",
                            TfidfVectorizer(
                                ngram_range=(1, 2),
                                min_df=1,
                                max_features=3500,
                                sublinear_tf=True,
                                strip_accents="unicode",
                                dtype=np.float32,
                            ),
                        ),
                        (
                            "char",
                            TfidfVectorizer(
                                analyzer="char_wb",
                                ngram_range=(3, 5),
                                min_df=1,
                                max_features=4500,
                                sublinear_tf=True,
                                strip_accents="unicode",
                                dtype=np.float32,
                            ),
                        ),
                    ]
                ),
            ),
            ("clf", LogisticRegression(max_iter=1200, random_state=42, class_weight="balanced", C=3.0)),
        ]
    )


def _normalize_text(text: str) -> str:
    return " ".join(str(text).strip().split())


def _text_variants(text: str, prefixes: list[str], suffixes: list[str]) -> list[str]:
    base = _normalize_text(text).strip(" .!?")
    if not base:
        return []

    variants = {
        base,
        base.lower(),
        f"{base}.",
        f"{base}!",
        f"{base}?",
    }
    for prefix in prefixes:
        variants.add(f"{prefix} {base}")
    for suffix in suffixes:
        variants.add(f"{base} {suffix}")
    for prefix in prefixes[:4]:
        for suffix in suffixes[:4]:
            variants.add(f"{prefix} {base} {suffix}")
    return sorted({_normalize_text(item) for item in variants if item})


def _expand_labelled_texts(samples_by_label: dict[str, list[str]], prefixes: list[str], suffixes: list[str]) -> tuple[list[str], list[str]]:
    texts, labels = [], []
    for label, samples in samples_by_label.items():
        for sample in samples:
            for variant in _text_variants(sample, prefixes, suffixes):
                texts.append(variant)
                labels.append(label)
    return texts, labels


def _with_indian_context(prefixes: list[str], suffixes: list[str]) -> tuple[list[str], list[str]]:
    return prefixes + COMMON_INDIAN_PREFIXES, suffixes + COMMON_INDIAN_SUFFIXES


def build_intent_model():
    classes = {
        "Support": [
            "login issue",
            "unable to sign in",
            "password reset not working",
            "access blocked for the user",
            "dashboard not loading",
            "api token invalid",
            "system throwing error on submit",
            "app keeps crashing after login",
            "sso failed for customer",
            "login nahin ho raha",
            "screen stuck after authentication",
            "need help with account access",
            "लॉगिन नहीं हो रहा और डैशबोर्ड अटक गया है",
            "எங்களால் உள்நுழைய முடியவில்லை, டாஷ்போர்ட் திறக்கவில்லை",
            "ದಯವಿಟ್ಟು ಸಹಾಯ ಮಾಡಿ, ಲಾಗಿನ್ ಕೆಲಸ ಮಾಡುತ್ತಿಲ್ಲ",
        ],
        "Billing": [
            "invoice status needed",
            "payment delayed for vendor",
            "refund request is pending",
            "credit note required",
            "gst mismatch in invoice",
            "vat details missing",
            "billing clarification needed",
            "duplicate charge dispute",
            "subscription renewal amount incorrect",
            "outstanding balance query",
            "invoice bhejo please",
            "payment receipt missing",
            "मुझे चालान की स्थिति चाहिए और भुगतान रसीद नहीं मिली",
            "கட்டண ரசீது இல்லை, இன்பாய்ஸ் நிலை வேண்டும்",
            "મને ઇન્વોઇસની સ્થિતિ જોઈએ અને રસીદ મળી નથી",
        ],
        "Sales": [
            "need pricing quote",
            "request product demo",
            "proposal needed for enterprise rollout",
            "commercial discussion for plan upgrade",
            "rfq response needed",
            "buy enterprise plan",
            "send capability deck",
            "schedule sales call",
            "proof of concept pricing",
            "quotation chahiye",
            "reseller partnership inquiry",
            "commercial proposal follow up",
            "कृपया एंटरप्राइज डेमो और प्राइसिंग कोट भेजिए",
            "என்டர்பிரைஸ் டெமோவும் விலைக் கோட்டும் வேண்டும்",
            "আমাদের জন্য ডেমো আর প্রাইসিং কোট পাঠান",
        ],
        "Logistics": [
            "shipment delay on buyer order",
            "eta update required",
            "warehouse transfer issue",
            "route planning problem",
            "dispatch stuck at port",
            "inventory movement blocked",
            "vendor delivery problem",
            "consignment not delivered",
            "freight cost issue",
            "delivery reschedule request",
            "order track karna hai",
            "port congestion alert",
            "पोर्ट जाम के कारण शिपमेंट देर से है, नया ETA बताइए",
            "போர்ட் நெரிசலால் சரக்கு தாமதமாகிறது, ETA வேண்டும்",
            "రవాణా ఆలస్యం అవుతోంది, తాజా ETA చెప్పండి",
        ],
        "Compliance": [
            "audit evidence needed",
            "policy review request",
            "kyc document check",
            "gdpr question from legal",
            "rbi compliance note",
            "dpdp update required",
            "iso 27001 control gap",
            "vendor due diligence review",
            "consent wording issue",
            "retention policy clarification",
            "compliance checklist bhejo",
            "tax registration verification",
            "कृपया डीपीडीपी नीति और ऑडिट साक्ष्य की समीक्षा करें",
            "ಜಿಡಿಪಿಆರ್ ಮತ್ತು ಕೇವೈಸಿ ದಾಖಲೆ ಪರಿಶೀಲನೆ ಬೇಕು",
            "कृपया अनुपालन चेकलिस्ट और KYC सत्यापन भेजें",
        ],
    }
    prefixes = [
        "customer says:",
        "client email:",
        "whatsapp note:",
        "voice transcript:",
        "agent summary:",
        "ticket update:",
    ]
    suffixes = [
        "please check today",
        "client is blocked",
        "need resolution by evening",
        "high priority",
        "jaldi batao",
        "kindly confirm the owner",
    ]
    prefixes, suffixes = _with_indian_context(prefixes, suffixes)
    texts, labels = _expand_labelled_texts(classes, prefixes, suffixes)
    model = _text_pipeline()
    model.fit(texts, labels)
    _save("intent_model", model)


def build_sentiment_model():
    classes = {
        "Positive": [
            "team was helpful and responsive",
            "great experience and smooth support",
            "billing got resolved quickly",
            "love the fast turnaround",
            "excellent service from the team",
            "issue was fixed without hassle",
            "very satisfied with the update",
            "support handled this professionally",
            "kaafi acha support tha",
            "the rollout went really well",
            "the team owned the issue and resolved it the same day",
            "billing looked messy at first but the agent clarified everything quickly",
            "the engineer stayed patient and the problem was fixed fast",
            "the case started rough but support recovered it cleanly",
            "the customer felt reassured after the rapid resolution",
            "टीम बहुत मददगार थी और समस्या जल्दी हल हो गई",
            "சேவை மிகவும் நல்லது, பிரச்சனை விரைவாக தீர்ந்தது",
        ],
        "Neutral": [
            "need update on the current status",
            "sharing feedback from the customer",
            "please confirm the invoice number",
            "this is an informational note",
            "we reviewed the current workflow",
            "requesting an update by tomorrow",
            "customer asked for the latest status",
            "adding context from the support call",
            "sending notes from today's discussion",
            "please verify whether this is expected",
            "thanks for the quick fix though the onboarding notes are still unclear",
            "the delay is noted but the case is now closed and under observation",
            "support replied promptly and we are waiting for the final confirmation",
            "sharing a balanced update after the issue was partially resolved",
            "the incident is stable for now and the team is monitoring the next step",
            "कृपया वर्तमान स्थिति का अपडेट साझा करें",
            "தற்போதைய நிலை பற்றிய புதுப்பிப்பு வேண்டும்",
        ],
        "Negative": [
            "frustrated with the delay",
            "billing is confusing and poor",
            "service is broken and slow",
            "customer is angry and upset",
            "very disappointed by the response",
            "still waiting with no ownership",
            "the issue remains unresolved",
            "team sounded dismissive and unhelpful",
            "bahut delay hua and no response",
            "completely unhappy with the experience",
            "the support engineer was polite but we are still blocked",
            "finance responded but the billing problem is still unresolved",
            "the call was courteous however the service is still failing",
            "the team tried to help but the customer is still frustrated",
            "the update sounded nice but nothing actually moved forward",
            "देरी से ग्राहक नाराज़ है और अब भी समाधान नहीं मिला",
            "சேவை மிகவும் மோசம், இன்னும் பதில் இல்லை",
        ],
    }
    prefixes = [
        "customer says:",
        "survey response:",
        "feedback note:",
        "voice of customer:",
        "email excerpt:",
    ]
    suffixes = [
        "please review",
        "for account manager follow-up",
        "from today's survey",
        "for quality review",
        "shared by the customer",
    ]
    prefixes, suffixes = _with_indian_context(prefixes, suffixes)
    texts, labels = _expand_labelled_texts(classes, prefixes, suffixes)
    model = _text_pipeline()
    model.fit(texts, labels)
    _save("sentiment_model", model)


def build_meeting_model():
    labeled = {
        "action": [
            "Priya will update the pricing sheet by Friday",
            "Action item: send the vendor shortlist",
            "Rahul to confirm the revised SLA",
            "Need to close the contract draft tomorrow",
            "Asha will share the launch checklist",
            "Owner assigned to prepare the gst summary",
            "Finance must send the approved numbers today",
            "Please upload the audit evidence before noon",
            "कृपया शुक्रवार तक विक्रेता सूची भेज दें",
            "அடுத்த புதன்கிழமைக்குள் புதுப்பிக்கப்பட்ட விலைப்பட்டியல் அனுப்பவும்",
        ],
        "decision": [
            "We agreed to move the launch to next week",
            "Decision: onboard the Mumbai vendor first",
            "The team approved the new pricing tier",
            "It was confirmed that finance owns the signoff",
            "Everyone aligned on a phased rollout",
            "The steering group selected the standard plan",
            "The committee decided to pause the migration",
            "Consensus was to keep support in-house",
            "निर्णय: पहले मुंबई विक्रेता को ऑनबोर्ड किया जाएगा",
            "முடிவு: முதலில் சென்னை விற்பனையாளர் சேர்க்கப்படுவார்",
        ],
        "risk": [
            "Port congestion may delay the shipment",
            "There is a blocker around GST validation",
            "Risk: vendor readiness is still low",
            "Dependency on legal review could slow the rollout",
            "A data quality issue may affect reporting",
            "The integration team is understaffed this week",
            "Low inventory cover could impact next-day delivery",
            "Budget approval remains a major dependency",
            "जोखिम: GST सत्यापन लॉन्च में देरी कर सकता है",
            "ஆபத்து: துறைமுக நெரிசல் காரணமாக சரக்கு தாமதமாகலாம்",
        ],
        "note": [
            "The customer joined from Singapore",
            "Weekly review covered operations and billing updates",
            "The team discussed current progress",
            "Context was shared on recent support volume",
            "The group reviewed the dashboard snapshot",
            "A summary of open items was presented",
            "The meeting focused on onboarding readiness",
            "Participants introduced themselves at the start",
            "बैठक में वर्तमान प्रगति और लंबित कार्यों पर चर्चा हुई",
            "இன்றைய கூட்டத்தில் தற்போதைய நிலை மற்றும் அடுத்த படிகள் பகிரப்பட்டன",
        ],
    }
    prefixes = ["meeting note:", "transcript:", "minutes:", "speaker note:", "call summary:"]
    suffixes = ["for today's review", "during the weekly sync", "from the leadership meeting", "in the ops call"]
    prefixes, suffixes = _with_indian_context(prefixes, suffixes)
    texts, labels = _expand_labelled_texts(labeled, prefixes, suffixes)
    model = _text_pipeline()
    model.fit(texts, labels)
    _save("meeting_sentence_model", model)


def build_contract_model():
    classes = {
        "Low": [
            "Either party may terminate with thirty days notice and liability is capped",
            "Data use is limited to contracted services and renewal is optional",
            "Standard confidentiality and mutual obligations apply",
            "Subprocessors require written approval and deletion on exit",
            "The agreement allows suspension only with written notice",
            "Liability is limited to fees paid in the previous year",
            "Cross-border transfer needs explicit customer approval",
            "The reseller arrangement is non-exclusive and optional to renew",
            "कोई भी पक्ष तीस दिन की सूचना देकर समझौता समाप्त कर सकता है और देयता सीमित है",
            "ஒப்பந்தம் முடிக்க முன் எழுத்து மூலம் அறிவிப்பு தேவை, பொறுப்பு வரம்புடன் உள்ளது",
        ],
        "Moderate": [
            "The agreement renews automatically unless notice is given",
            "Cross-border transfer is permitted subject to policy review",
            "Supplier receives preferred territory rights for one year",
            "Termination requires a ninety-day notice period",
            "Indemnity applies to third-party claims with a capped liability",
            "Exclusivity applies only to one named product line",
            "The contract allows data transfer to affiliates with safeguards",
            "Annual renewal is automatic unless procurement objects",
            "समझौता स्वतः नवीनीकृत होगा जब तक पूर्व सूचना न दी जाए",
            "கொள்முதல் குழு எதிர்ப்பு தெரிவிக்காவிட்டால் ஒப்பந்தம் தானாக நீளும்",
        ],
        "High": [
            "The reseller has exclusive rights and the contract auto-renews yearly",
            "Customer must indemnify all claims with unlimited liability",
            "Data may be globally transferred without restriction and termination is not allowed",
            "Supplier gets perpetual exclusivity across all territories",
            "The agreement forbids termination for convenience and removes liability caps",
            "All customer data may be reused freely by affiliates worldwide",
            "Unlimited indemnity survives forever and renewal is mandatory",
            "The contract restricts exit while granting broad data transfer rights",
            "ग्राहक पर असीमित देयता होगी और अनुबंध हर साल स्वतः नवीनीकृत होगा",
            "வாடிக்கையாளர் தரவு கட்டுப்பாடின்றி பகிரலாம், ஒப்பந்தத்தை முடிக்க முடியாது",
        ],
    }
    prefixes = ["contract clause:", "legal text:", "agreement excerpt:", "draft says:"]
    suffixes = ["for review", "in this draft", "from the submitted agreement", "in the current contract"]
    prefixes, suffixes = _with_indian_context(prefixes, suffixes)
    texts, labels = _expand_labelled_texts(classes, prefixes, suffixes)
    model = _text_pipeline()
    model.fit(texts, labels)
    _save("contract_risk_model", model)


def build_compliance_model():
    classes = {
        "Low": [
            "Policy includes encryption access control incident response retention and audit log handling",
            "The process defines lawful basis retention breach notification and data subject rights",
            "Controls cover supplier reviews backups key rotation and privileged access",
            "The standard documents encryption consent retention and breach reporting",
            "Access review and incident response are tested quarterly",
            "The framework includes governance surveillance and business continuity controls",
            "नीति में एन्क्रिप्शन, एक्सेस कंट्रोल, रिटेंशन और ब्रीच सूचना शामिल है",
            "கொள்கையில் குறியாக்கம், அணுகல் கட்டுப்பாடு மற்றும் காப்பு நடைமுறை உள்ளது",
        ],
        "Moderate": [
            "The policy covers encryption and access control but retention needs work",
            "Some governance controls exist though incident response is incomplete",
            "The document defines retention but omits supplier review details",
            "Consent language exists though breach notification is vague",
            "Audit logging is present but monitoring is inconsistent",
            "Backups exist but restoration testing is not documented",
            "नीति में एन्क्रिप्शन है लेकिन रिटेंशन और सप्लायर समीक्षा स्पष्ट नहीं है",
            "கட்டுப்பாடுகள் சில உள்ளன, ஆனால் சம்பவ மறுமொழி முழுமையில்லை",
        ],
        "High": [
            "No audit logs are retained and there is no incident response process",
            "The document lacks consent retention and breach notification controls",
            "There is no encryption standard or access review process",
            "Policies are missing lawful basis and data subject rights",
            "No business continuity or vendor risk controls are defined",
            "The artifact contains only generic statements with no named controls",
            "कोई ऑडिट लॉग नहीं रखा जाता और ब्रीच सूचना प्रक्रिया भी नहीं है",
            "குறியாக்கம் இல்லை, அணுகல் ஆய்வு இல்லை, சம்பவ செயல்முறை இல்லை",
        ],
    }
    prefixes = ["policy excerpt:", "control note:", "artifact text:", "framework summary:"]
    suffixes = ["for the audit", "for control review", "in the submitted artifact", "for compliance validation"]
    prefixes, suffixes = _with_indian_context(prefixes, suffixes)
    texts, labels = _expand_labelled_texts(classes, prefixes, suffixes)
    model = _text_pipeline()
    model.fit(texts, labels)
    _save("compliance_model", model)


def build_bi_model():
    classes = {
        "max": [
            "highest revenue",
            "top region by sales",
            "largest growth",
            "best performing region",
            "which market did best",
            "peak revenue this quarter",
            "leader by current revenue",
            "top current revenue",
            "best geography by sales",
            "sabse zyada revenue kis region ka hai",
            "सबसे ज़्यादा revenue किस region का है",
            "எந்த பிராந்தியத்தில் revenue அதிகம்",
        ],
        "min": [
            "lowest revenue",
            "worst region",
            "smallest margin",
            "least volume",
            "which market performed the worst",
            "bottom of the revenue column",
            "laggard by current revenue",
            "weakest geography by sales",
            "lowest current revenue",
            "sabse kam revenue kis region ka hai",
            "सबसे कम revenue किस region का है",
            "எந்த பிராந்தியத்தில் revenue குறைவு",
        ],
        "compare": [
            "compare west and north",
            "difference between two regions",
            "which is higher west or north",
            "compare apac and europe performance",
            "show comparison for two segments",
            "contrast west against north",
            "compare two regions side by side",
            "how do these regions stack up",
            "line up west with north on revenue",
            "west aur north ko compare karo",
            "west aur north ka comparison dikhao",
            "west மற்றும் north ஐ ஒப்பிடுங்கள்",
        ],
        "trend": [
            "trend over time",
            "growth month by month",
            "moving upward or downward",
            "show monthly trend",
            "is revenue increasing over time",
            "month over month direction",
            "rising or falling over time",
            "time trend for the metric",
            "pattern across the months",
            "month wise trend batao",
            "महीने के हिसाब से trend बताओ",
            "மாத வாரியாக trend காட்டுங்கள்",
        ],
        "summary": [
            "summarize the dataset",
            "overview of performance",
            "what does this data show",
            "give me a quick summary",
            "key takeaways from this table",
            "brief readout of this table",
            "quick overview for this dataset",
            "summarize the uploaded rows",
            "dataset broad overview",
            "dataset ka summary do",
            "dataset का summary दो",
            "இந்த dataset-க்கு summary கொடுங்கள்",
        ],
    }
    prefixes = ["business question:", "analyst asks:", "dashboard prompt:", "query:"]
    suffixes = ["for the latest report", "using the uploaded dataset", "for the business review"]
    prefixes, suffixes = _with_indian_context(prefixes, suffixes)
    texts, labels = _expand_labelled_texts(classes, prefixes, suffixes)
    model = _text_pipeline()
    model.fit(texts, labels)
    _save("bi_question_model", model)


def build_rfq_model():
    domains = {
        "analytics": [
            "need dashboard analytics and reporting platform",
            "want insights data visualization and executive reporting",
            "looking for kpi dashboards with drilldowns",
            "need metrics warehouse and visualization stack",
            "analytics platform for finance and sales leaders",
            "हमें डैशबोर्ड एनालिटिक्स और रिपोर्टिंग प्लेटफॉर्म चाहिए",
        ],
        "logistics": [
            "looking for shipment visibility and route planning",
            "need supply chain network tool",
            "want carrier tracking eta risk alerts and warehouse routing",
            "require logistics control tower for dispatch operations",
            "need freight planning and delivery visibility platform",
            "हमें शिपमेंट विज़िबिलिटी और रूट प्लानिंग प्लेटफॉर्म चाहिए",
        ],
        "security": [
            "require audit logging access control and encryption",
            "need governance risk and compliance platform",
            "looking for iam monitoring and policy enforcement",
            "security product with siem retention and investigation workflows",
            "need security controls for regulated workloads",
            "ऑडिट लॉगिंग, एन्क्रिप्शन और IAM वाला सुरक्षा प्लेटफॉर्म चाहिए",
        ],
        "contact-center": [
            "multilingual support analytics for customer service",
            "need voice and ticket intelligence",
            "contact center platform for transcripts qa and sentiment",
            "customer support analytics across calls chat and email",
            "need hindi and english support quality monitoring",
            "हमें बहुभाषी contact center analytics और voice support चाहिए",
            "பல்மொழி contact center analytics மற்றும் voice QA தேவை",
        ],
        "procurement": [
            "vendor performance and procurement workflow",
            "rfq automation for supplier onboarding",
            "need sourcing approval and supplier scorecards",
            "procurement suite for vendor lifecycle and rfq management",
            "tool for supplier discovery and purchase approvals",
            "supplier onboarding और RFQ automation वाला procurement tool चाहिए",
        ],
    }
    prefixes = ["rfq request:", "requirement note:", "buyer brief:", "procurement asks:"]
    suffixes = ["for next quarter", "for enterprise rollout", "for the submitted initiative", "for the new program"]
    prefixes, suffixes = _with_indian_context(prefixes, suffixes)
    texts, labels = _expand_labelled_texts(domains, prefixes, suffixes)
    model = _text_pipeline()
    model.fit(texts, labels)
    _save("rfq_domain_model", model)


def build_keyword_vectorizer():
    corpus = [
        "enterprise ai support billing logistics compliance audit governance pricing procurement supplier",
        "multilingual contract risk invoice kyc gst vat supplier reconciliation due diligence",
        "meeting intelligence action items summaries delivery vendor route inventory warehouse port congestion",
        "dynamic pricing conversion demand competitor inventory revenue analytics dashboard trend comparison",
        "contact center call transcript qa sentiment escalation ownership resolution csat churn",
        "rfq procurement sourcing onboarding approvals spend category buyer shortlist negotiation",
        "identity aadhaar pan company registration tax id verification legal policy retention",
        "हिंदी தமிழ் বাংলা ગુજરાતી ಕನ್ನಡ తెలుగు മലയാളം मराठी ਪੰਜਾਬੀ اردو অসমীয়া ଓଡ଼ିଆ",
    ]
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=600, sublinear_tf=True)
    vectorizer.fit(corpus)
    _save("keyword_vectorizer", vectorizer)


def build_invoice_model():
    rows, labels = [], []
    for has_invoice, has_supplier, has_buyer, has_date, has_tax_id, arithmetic_ok in itertools.product([0, 1], repeat=6):
        completeness = has_invoice + has_supplier + has_buyer + has_date + has_tax_id
        if completeness >= 5 and arithmetic_ok:
            label = "Valid"
        elif completeness >= 3:
            label = "Review"
        else:
            label = "Invalid"
        rows.append([has_invoice, has_supplier, has_buyer, has_date, has_tax_id, arithmetic_ok, completeness])
        labels.append(label)
    model = RandomForestClassifier(n_estimators=80, random_state=42)
    model.fit(np.array(rows), labels)
    _save("invoice_validity_model", model)


def build_kyc_model():
    rows, labels = [], []
    for aadhaar, pan, tax_id, contact, region_india in itertools.product([0, 1, 2], [0, 1], [0, 1], [0, 1], [0, 1]):
        completeness = min(aadhaar, 1) + pan + tax_id + contact
        if aadhaar > 1 or (region_india and pan == 0 and aadhaar >= 1):
            label = "High Review"
        elif completeness < 2 or contact == 0:
            label = "Review"
        else:
            label = "Clear"
        rows.append([aadhaar, pan, tax_id, contact, region_india, completeness])
        labels.append(label)
    model = RandomForestClassifier(n_estimators=80, random_state=42)
    model.fit(np.array(rows), labels)
    _save("kyc_risk_model", model)


def build_sla_model():
    rows, labels = [], []
    for priority in range(4):
        for category in range(4):
            for tier in range(3):
                for complexity in range(3):
                    for first_response in [5, 15, 30, 45, 90, 180, 300]:
                        for backlog in [2, 6, 12, 20, 35, 50]:
                            risk_score = priority * 18 + tier * 8 + complexity * 12 + min(first_response / 5, 24) + min(backlog, 24)
                            if risk_score >= 80:
                                label = "Critical"
                            elif risk_score >= 58:
                                label = "High"
                            elif risk_score >= 36:
                                label = "Moderate"
                            else:
                                label = "Low"
                            rows.append([priority, category, tier, complexity, first_response, backlog])
                            labels.append(label)
    model = RandomForestClassifier(n_estimators=120, random_state=42)
    model.fit(np.array(rows), labels)
    _save("sla_model", model)


def _vendor_score(on_time: float, defect: float, reopen: float, spend: float) -> float:
    spend_signal = min(spend / 1_000_000, 6)
    score = on_time * 0.5 + max(0, 100 - defect * 5) * 0.2 + max(0, 100 - reopen * 3) * 0.18 + spend_signal * 2
    return max(0, min(100, score))


def build_vendor_model():
    rows, targets = [], []
    for on_time in [45, 60, 75, 85, 92, 98]:
        for defect in [1, 3, 6, 10, 18]:
            for reopen in [1, 4, 8, 15, 25]:
                for spend in [100000, 500000, 1500000, 3000000, 8000000]:
                    rows.append([on_time, defect, reopen, spend])
                    targets.append(_vendor_score(on_time, defect, reopen, spend))
    for _ in range(250):
        on_time = RANDOM.randint(40, 99)
        defect = RANDOM.randint(0, 20)
        reopen = RANDOM.randint(0, 30)
        spend = RANDOM.randint(100000, 10000000)
        rows.append([on_time, defect, reopen, spend])
        targets.append(_vendor_score(on_time, defect, reopen, spend))
    model = RandomForestRegressor(n_estimators=120, random_state=42)
    model.fit(np.array(rows), np.array(targets))
    _save("vendor_model", model)


def build_self_heal_model():
    rows, labels = [], []
    for status in [429, 500, 502, 503, 504]:
        for criticality in range(4):
            for retries in range(5):
                for region_match in [0, 1]:
                    if retries >= 4:
                        label = "Circuit Break"
                    elif status == 429 and retries <= 2:
                        label = "Backoff Retry"
                    elif criticality >= 3 or (status in [503, 504] and retries >= 2) or (region_match == 0 and criticality >= 2):
                        label = "Regional Failover"
                    else:
                        label = "Retry Then Observe"
                    rows.append([status, criticality, retries, region_match])
                    labels.append(label)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(np.array(rows), labels)
    _save("self_heal_model", model)


def _route_score(city_match: int, delivery_urgency: int, order_value: float, region_rank: int) -> float:
    score = 62 + city_match * 20 + delivery_urgency * 6 + min(order_value / 20000, 8) - region_rank * 6
    if city_match == 0 and delivery_urgency == 2:
        score -= 4
    return score


def build_route_model():
    rows, targets = [], []
    for city_match in [0, 1]:
        for delivery_urgency in [0, 1, 2]:
            for order_value in [500, 5000, 18000, 60000, 120000]:
                for region_rank in [0, 1, 2, 3]:
                    rows.append([city_match, delivery_urgency, order_value, region_rank])
                    targets.append(_route_score(city_match, delivery_urgency, order_value, region_rank))
    for _ in range(200):
        city_match = RANDOM.randint(0, 1)
        delivery_urgency = RANDOM.randint(0, 2)
        order_value = RANDOM.randint(500, 150000)
        region_rank = RANDOM.randint(0, 4)
        rows.append([city_match, delivery_urgency, order_value, region_rank])
        targets.append(_route_score(city_match, delivery_urgency, order_value, region_rank))
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(np.array(rows), np.array(targets))
    _save("route_model", model)


def _eta_impact(delay_hours: float, cover_days: float, congestion: int) -> float:
    return delay_hours + congestion * 7 + max(0, 7 - cover_days) * 1.6


def build_supply_chain_model():
    rows, targets = [], []
    for delay_hours in [0, 6, 12, 24, 36, 48]:
        for cover_days in [1, 2, 4, 7, 12]:
            for congestion in [0, 1, 2]:
                rows.append([delay_hours, cover_days, congestion])
                targets.append(_eta_impact(delay_hours, cover_days, congestion))
    for _ in range(200):
        delay_hours = RANDOM.randint(0, 60)
        cover_days = RANDOM.randint(1, 15)
        congestion = RANDOM.randint(0, 2)
        rows.append([delay_hours, cover_days, congestion])
        targets.append(_eta_impact(delay_hours, cover_days, congestion))
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(np.array(rows), np.array(targets))
    _save("supply_chain_model", model)


def _pricing_multiplier(gap: float, inventory_days: float, demand: float, conversion: float) -> float:
    multiplier = 1 + ((demand - 50) / 100) * 0.18
    multiplier += 0.06 if inventory_days <= 10 else (-0.06 if inventory_days >= 30 else 0)
    multiplier += max(-0.1, min(0.1, gap / 800))
    multiplier += -0.05 if conversion < 3 else (0.03 if conversion > 6 else 0)
    return max(0.8, min(1.25, multiplier))


def build_pricing_model():
    rows, targets = [], []
    for gap in [-200, -120, -50, 0, 50, 120, 200]:
        for inventory_days in [5, 12, 20, 35]:
            for demand in [30, 45, 55, 75, 92]:
                for conversion in [1.8, 3.2, 5.5, 7.0]:
                    rows.append([gap, inventory_days, demand, conversion])
                    targets.append(_pricing_multiplier(gap, inventory_days, demand, conversion))
    for _ in range(250):
        gap = RANDOM.randint(-250, 250)
        inventory_days = RANDOM.randint(3, 45)
        demand = RANDOM.randint(20, 100)
        conversion = RANDOM.uniform(1.0, 8.0)
        rows.append([gap, inventory_days, demand, conversion])
        targets.append(_pricing_multiplier(gap, inventory_days, demand, conversion))
    model = RandomForestRegressor(n_estimators=120, random_state=42)
    model.fit(np.array(rows), np.array(targets))
    _save("pricing_model", model)


def build_gstin_model():
    rows, labels = [], []
    groups = {
        "orbit": [
            "orbit logistics",
            "orbit logistics pvt ltd",
            "orbit logistics private limited",
            "orbit logistics india",
            "orbit logistics gmbh",
        ],
        "nova": [
            "nova retail",
            "nova retail private limited",
            "nova retail india",
            "nova retail solutions",
        ],
        "acme": [
            "acme supplies",
            "acme global supplies",
            "acme supplies private limited",
            "acme industrial supplies",
        ],
        "stellar": [
            "stellar payments",
            "stellar payments india",
            "stellar payment systems",
            "stellarpay technologies",
        ],
        "northline": [
            "northline warehousing",
            "northline warehousing services",
            "northline logistics parks",
            "northline storage solutions",
        ],
    }

    def add_row(target: str, candidate: str, same_tax: int, label: str) -> None:
        rows.append(
            [
                fuzz.ratio(target, candidate),
                fuzz.partial_ratio(target, candidate),
                fuzz.token_sort_ratio(target, candidate),
                same_tax,
            ]
        )
        labels.append(label)

    for variants in groups.values():
        for target, candidate in itertools.permutations(variants, 2):
            add_row(target, candidate, 1, "Match")
            add_row(target, candidate, 0, "Review")

    negative_pairs = [
        ("orbit logistics", "stellar payments"),
        ("orbit logistics", "northline warehousing"),
        ("nova retail", "acme supplies"),
        ("stellar payments", "acme industrial supplies"),
        ("northline logistics parks", "nova retail solutions"),
        ("orbit logistics india", "orbit global services"),
        ("nova retail india", "novel retail labs"),
    ]
    for target, candidate in negative_pairs:
        add_row(target, candidate, 0, "Review")
        add_row(target, candidate, 1, "Review")

    model = RandomForestClassifier(n_estimators=120, random_state=42)
    model.fit(np.array(rows), labels)
    _save("gstin_match_model", model)


def build_audit_model():
    rows = []
    for hour in [8, 10, 12, 14, 16, 18]:
        for action in [0, 1, 2]:
            rows.append([hour, action, 2, 80])
            rows.append([hour, action, 3, 120])
            rows.append([hour, action, 1, 60])
    rows.extend([[2, 2, 7, 900], [23, 1, 6, 700], [1, 2, 8, 1000], [3, 2, 7, 850]])
    model = IsolationForest(contamination=0.12, random_state=42)
    model.fit(np.array(rows))
    _save("audit_model", model)


def ensure_artifacts(force: bool = False) -> None:
    _ensure_dirs()
    required = [
        "intent_model.joblib",
        "sentiment_model.joblib",
        "meeting_sentence_model.joblib",
        "contract_risk_model.joblib",
        "compliance_model.joblib",
        "bi_question_model.joblib",
        "rfq_domain_model.joblib",
        "keyword_vectorizer.joblib",
        "invoice_validity_model.joblib",
        "kyc_risk_model.joblib",
        "sla_model.joblib",
        "vendor_model.joblib",
        "self_heal_model.joblib",
        "route_model.joblib",
        "supply_chain_model.joblib",
        "pricing_model.joblib",
        "gstin_match_model.joblib",
        "audit_model.joblib",
    ]
    if not force and all((ARTIFACTS_DIR / name).exists() for name in required):
        return

    build_intent_model()
    build_sentiment_model()
    build_meeting_model()
    build_contract_model()
    build_compliance_model()
    build_bi_model()
    build_rfq_model()
    build_keyword_vectorizer()
    build_invoice_model()
    build_kyc_model()
    build_sla_model()
    build_vendor_model()
    build_self_heal_model()
    build_route_model()
    build_supply_chain_model()
    build_pricing_model()
    build_gstin_model()
    build_audit_model()


if __name__ == "__main__":
    ensure_artifacts(force=True)
    print(f"Model artifacts written to {ARTIFACTS_DIR}")
