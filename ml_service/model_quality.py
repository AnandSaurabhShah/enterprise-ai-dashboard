from __future__ import annotations

import itertools
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from statistics import mean

import numpy as np
from rapidfuzz import fuzz
from sklearn.metrics import accuracy_score, precision_score

from runtime import Runtime, detect_languages_with_ai4bharat, ollama_status, top_keywords
from train_models import ARTIFACTS_DIR, _eta_impact, _pricing_multiplier, _route_score, _vendor_score, ensure_artifacts


MIN_ACCURACY = 0.85
MIN_PRECISION = 0.85
REPORT_PATH = ARTIFACTS_DIR / "model_quality_report.json"

TEXT_HOLDOUT_PREFIXES = [
    "desk note:",
    "partner escalation:",
    "field update:",
    "customer voice:",
]
TEXT_HOLDOUT_SUFFIXES = [
    "needs a clear owner",
    "review this in triage",
    "keep the response grounded",
]

INTENT_HOLDOUTS = {
    "Support": [
        "account recovery keeps looping back to the sign in screen",
        "users cannot open the workspace after the sso handshake",
        "otp verification expires before the login completes",
        "the admin portal returns an auth error for every access request",
        "the application shows a blank page right after the user signs in",
    ],
    "Billing": [
        "finance needs the missing remittance advice for the cleared payment",
        "the customer statement shows a duplicate debit that must be corrected",
        "we need a corrected tax invoice because the amount is off",
        "the refund has not landed and the receipt is still unavailable",
        "accounts payable needs the latest billing status and credit memo",
    ],
    "Sales": [
        "please send commercial terms for a broader rollout",
        "the buyer wants a capabilities deck and a discovery demo",
        "share a pricing proposal for the enterprise expansion",
        "we need a quote for a pilot with support and onboarding",
        "procurement is waiting for the commercial response package",
    ],
    "Logistics": [
        "carrier handoff stalled and the delivery eta slipped again",
        "warehouse transfer is blocked and dispatch cannot move",
        "the freight lane needs a revised route because the port is congested",
        "inventory movement is delayed and the shipment tracker is stale",
        "the consignment missed the promised slot and needs replanning",
    ],
    "Compliance": [
        "legal needs a review of consent language and retention controls",
        "please verify the kyc pack and the audit evidence trail",
        "risk wants a quick check on the gdpr and dpdp obligations",
        "governance asked for a control gap review before release",
        "the vendor due diligence memo needs a compliance pass",
    ],
}

SENTIMENT_HOLDOUTS = {
    "Positive": [
        "the handoff was smooth and the team closed the case quickly",
        "support stayed proactive and the customer left happy",
        "the service recovery felt fast, clear, and professional",
        "everyone appreciated the ownership and quick turnaround",
        "the rollout support was excellent from start to finish",
        "the issue began badly but the team recovered it quickly and professionally",
    ],
    "Neutral": [
        "sharing the latest account update for the daily review",
        "this message records the current status and next checkpoint",
        "please confirm the invoice reference for the open thread",
        "adding meeting notes so the owner has the right context",
        "sending a simple status note before tomorrow's follow up",
        "thanks for the quick fix though the onboarding notes are still unclear",
        "the delay is noted but the case is now closed and under observation",
    ],
    "Negative": [
        "the customer is upset because the issue is still unresolved",
        "the response was slow, confusing, and missed the main problem",
        "we are disappointed by the lack of ownership on this incident",
        "the delay is frustrating and the user still cannot proceed",
        "the experience felt broken and nobody answered in time",
        "the support engineer was polite but we are still blocked",
        "finance replied, however the billing problem is still unresolved",
    ],
}

MEETING_HOLDOUTS = {
    "action": [
        "Nina will circulate the revised risk register by Monday",
        "Please upload the approved forecast before the finance review",
        "Arun to send the onboarding checklist after lunch",
        "The support lead must close the open blocker today",
        "Owner assigned to draft the weekly delivery summary",
    ],
    "decision": [
        "Decision: start with the Chennai rollout and expand later",
        "The steering committee approved the standard renewal path",
        "We agreed to delay the launch until the controls are ready",
        "The group selected the managed support plan for phase one",
        "Consensus was to keep procurement in the main workflow",
    ],
    "risk": [
        "Risk: customs delay could push the delivery into next week",
        "The dependency on legal signoff may slow the release",
        "Low inventory cover might impact same day fulfilment",
        "A data mapping issue can affect the next dashboard refresh",
        "Vendor readiness remains a blocker for the pilot timeline",
    ],
    "note": [
        "The team reviewed the weekly dashboard and open items",
        "Participants shared a quick summary of current progress",
        "The meeting covered service metrics and account context",
        "The customer joined from the regional office for the update",
        "A short overview of the pending work was presented",
    ],
}

CONTRACT_HOLDOUTS = {
    "Low": [
        "Termination for convenience is allowed with written notice and liability stays capped.",
        "Subprocessor use needs approval, renewal is optional, and data use is limited to the service.",
        "The reseller arrangement is non exclusive and either side may exit with thirty days notice.",
        "Cross border transfers require customer approval and deletion is required after exit.",
        "Confidentiality is mutual, fees are capped, and suspension needs prior notice.",
    ],
    "Moderate": [
        "The agreement renews by default unless the buyer objects in advance.",
        "Exclusivity applies only to one product family for a fixed term.",
        "Data transfer to affiliates is allowed when internal safeguards are documented.",
        "Termination needs a long notice window and indemnity is capped for third party claims.",
        "Preferred territory rights apply for one year subject to annual review.",
    ],
    "High": [
        "The supplier gets perpetual exclusivity and the contract renews automatically every year.",
        "The customer accepts unlimited liability and cannot terminate for convenience.",
        "All customer data may be reused freely across affiliates worldwide without restriction.",
        "Mandatory renewal survives forever and broad transfer rights are granted globally.",
        "The contract removes liability caps while restricting exit options across all territories.",
    ],
}

COMPLIANCE_HOLDOUTS = {
    "Low": [
        "The control set documents encryption, access review, retention, breach notice, and audit logging.",
        "Lawful basis, retention, data subject rights, and supplier review are explicitly covered.",
        "Incident response, backups, privileged access, and governance testing are all defined.",
        "The framework includes consent, purpose limitation, recovery testing, and business continuity.",
        "Quarterly control evidence covers monitoring, retention, key rotation, and response drills.",
    ],
    "Moderate": [
        "Encryption and access control are defined, but retention guidance is thin.",
        "The policy includes consent language, though breach notification remains vague.",
        "Backups exist, but restoration testing is not consistently documented.",
        "Audit logging is present while supplier review and governance details need work.",
        "The artifact covers some controls but incident response ownership is incomplete.",
    ],
    "High": [
        "There is no encryption baseline, no access review, and no incident response process.",
        "The artifact lacks lawful basis, retention controls, and breach notification steps.",
        "Policies contain only generic statements with no named controls or owners.",
        "No audit logs are retained and no business continuity plan is defined.",
        "The document omits data subject rights, supplier controls, and recovery procedures.",
    ],
}

BI_HOLDOUTS = {
    "max": [
        "which segment delivered the peak revenue this quarter",
        "name the best performing geography by sales",
        "which market topped the latest revenue column",
        "show me the leader by current revenue",
    ],
    "min": [
        "which segment landed at the lowest revenue this quarter",
        "name the weakest geography by sales",
        "which market is at the bottom of the latest revenue column",
        "show me the laggard by current revenue",
    ],
    "compare": [
        "contrast west against north on the current revenue metric",
        "tell me how two regions stack up against each other",
        "compare europe and apac performance side by side",
        "which region is stronger when west is lined up with north",
    ],
    "trend": [
        "walk me through the month over month direction",
        "is the series rising or falling over time",
        "show the time trend for the revenue line",
        "explain the pattern across the months",
    ],
    "summary": [
        "give me a brief readout of this table",
        "what is the quick overview for this dataset",
        "summarize the uploaded rows for me",
        "tell me what the dataset broadly shows",
    ],
}

RFQ_HOLDOUTS = {
    "analytics": [
        "need executive dashboards, metrics modeling, and drilldown reporting for leadership",
        "looking for a reporting stack with scorecards and analytical views",
        "the program needs warehouse metrics, dashboards, and business insights",
        "we want a decision support platform for kpi tracking and visualization",
    ],
    "logistics": [
        "need shipment visibility, eta risk alerts, and route control for dispatch teams",
        "looking for a logistics control tower with warehouse and carrier tracking",
        "the brief requires freight planning, handoff monitoring, and delivery routing",
        "we want network visibility for inventory movement and route planning",
    ],
    "security": [
        "need access control, encryption, audit evidence, and policy enforcement",
        "looking for governance, monitoring, and investigation workflows for regulated workloads",
        "the solution must cover iam, retention, and compliance monitoring",
        "we require security controls with surveillance and audit readiness",
    ],
    "contact-center": [
        "need transcript qa, sentiment tracking, and multilingual support analytics",
        "looking for a contact center intelligence layer across calls, chat, and email",
        "the requirement is voice analytics with service quality monitoring",
        "we want customer support insights for conversation review and coaching",
    ],
    "procurement": [
        "need supplier onboarding, sourcing approvals, and rfq workflow automation",
        "looking for vendor lifecycle management with scorecards and buyer approvals",
        "the suite should support procurement intake, supplier discovery, and rfq handling",
        "we want sourcing automation with supplier evaluation and approval routing",
    ],
}

OLLAMA_DOMAIN_CASES = [
    ("analytics", "Need dashboards, scorecards, and drilldown reporting for finance leaders."),
    ("logistics", "Need route planning, eta visibility, and carrier tracking for dispatch teams."),
    ("security", "Require encryption, iam, monitoring, and audit workflows for a regulated estate."),
    ("contact-center", "Need multilingual transcript QA and sentiment analytics for support."),
    ("procurement", "Need supplier onboarding, rfq management, and sourcing approvals."),
]


@dataclass
class ModelReport:
    name: str
    accuracy: float | None
    precision: float | None
    support: int
    status: str
    notes: list[str] = field(default_factory=list)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def _classification_report(name: str, y_true: list[str], y_pred: list[str], notes: list[str] | None = None) -> ModelReport:
    accuracy = float(accuracy_score(y_true, y_pred))
    precision = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
    status = "PASS" if accuracy >= MIN_ACCURACY and precision >= MIN_PRECISION else "FAIL"
    return ModelReport(name=name, accuracy=accuracy, precision=precision, support=len(y_true), status=status, notes=notes or [])


def _custom_report(name: str, accuracy: float | None, precision: float | None, support: int, notes: list[str] | None = None) -> ModelReport:
    if accuracy is None or precision is None:
        status = "SKIP"
    else:
        status = "PASS" if accuracy >= MIN_ACCURACY and precision >= MIN_PRECISION else "FAIL"
    return ModelReport(name=name, accuracy=accuracy, precision=precision, support=support, status=status, notes=notes or [])


def _dedupe_pairs(pairs: list[tuple[str, str]]) -> list[tuple[str, str]]:
    seen = set()
    deduped = []
    for label, text in pairs:
        key = (label, " ".join(text.split()))
        if key in seen:
            continue
        seen.add(key)
        deduped.append((label, key[1]))
    return deduped


def _expand_text_holdouts(samples_by_label: dict[str, list[str]]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for label, samples in samples_by_label.items():
        for sample in samples:
            base = " ".join(str(sample).strip().split()).strip(" .!?")
            variants = {
                base,
                f"{base}.",
                f"Subject: {base}",
                f"Please review: {base}",
                f"{base} and share the next action",
                f"{base} before the queue closes",
            }
            for prefix in TEXT_HOLDOUT_PREFIXES:
                variants.add(f"{prefix} {base}")
            for suffix in TEXT_HOLDOUT_SUFFIXES:
                variants.add(f"{base} | {suffix}")
            pairs.extend((label, variant) for variant in variants)
    return _dedupe_pairs(pairs)


def _vendor_band(score: float) -> str:
    if score >= 85:
        return "Strategic"
    if score >= 70:
        return "Preferred"
    if score >= 55:
        return "Watchlist"
    return "At risk"


def _pricing_band(multiplier: float) -> str:
    if multiplier >= 1.03:
        return "Increase"
    if multiplier <= 0.97:
        return "Decrease"
    return "Hold"


def _supply_chain_band(eta: float, cover: float) -> str:
    if eta >= 24 or cover <= 3:
        return "High"
    if eta >= 12 or cover <= 6:
        return "Moderate"
    return "Low"


def _evaluate_text_model(runtime: Runtime, model_name: str, samples_by_label: dict[str, list[str]], label: str) -> ModelReport:
    holdouts = _expand_text_holdouts(samples_by_label)
    y_true = [expected for expected, _text in holdouts]
    y_pred = [runtime.classify_text(model_name, text)[0] for _expected, text in holdouts]
    return _classification_report(label, y_true, y_pred, notes=[f"{len(samples_by_label)} classes scored on unseen templated holdouts."])


def evaluate_intent_model(runtime: Runtime) -> ModelReport:
    return _evaluate_text_model(runtime, "intent_model", INTENT_HOLDOUTS, "intent_model")


def evaluate_sentiment_model(runtime: Runtime) -> ModelReport:
    return _evaluate_text_model(runtime, "sentiment_model", SENTIMENT_HOLDOUTS, "sentiment_model")


def evaluate_meeting_model(runtime: Runtime) -> ModelReport:
    return _evaluate_text_model(runtime, "meeting_sentence_model", MEETING_HOLDOUTS, "meeting_sentence_model")


def evaluate_contract_model(runtime: Runtime) -> ModelReport:
    return _evaluate_text_model(runtime, "contract_risk_model", CONTRACT_HOLDOUTS, "contract_risk_model")


def evaluate_compliance_model(runtime: Runtime) -> ModelReport:
    return _evaluate_text_model(runtime, "compliance_model", COMPLIANCE_HOLDOUTS, "compliance_model")


def evaluate_bi_model(runtime: Runtime) -> ModelReport:
    return _evaluate_text_model(runtime, "bi_question_model", BI_HOLDOUTS, "bi_question_model")


def evaluate_rfq_model(runtime: Runtime) -> ModelReport:
    return _evaluate_text_model(runtime, "rfq_domain_model", RFQ_HOLDOUTS, "rfq_domain_model")


def evaluate_invoice_model(runtime: Runtime) -> ModelReport:
    rows = []
    labels = []
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
    predictions = runtime.models["invoice_validity_model"].predict(np.array(rows, dtype=float))
    return _classification_report("invoice_validity_model", labels, list(predictions))


def evaluate_kyc_model(runtime: Runtime) -> ModelReport:
    rows = []
    labels = []
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
    predictions = runtime.models["kyc_risk_model"].predict(np.array(rows, dtype=float))
    return _classification_report("kyc_risk_model", labels, list(predictions))


def evaluate_sla_model(runtime: Runtime) -> ModelReport:
    rows = []
    labels = []
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
    predictions = runtime.models["sla_model"].predict(np.array(rows, dtype=float))
    return _classification_report("sla_model", labels, list(predictions))


def evaluate_gstin_model(runtime: Runtime) -> ModelReport:
    rows = []
    labels = []
    groups = {
        "zenith": [
            "zenith retail",
            "zenith retail india",
            "zenith retail private limited",
            "zenith retail solutions",
        ],
        "harbor": [
            "harbor logistics",
            "harbor logistics india",
            "harbor logistics private limited",
            "harbor freight systems",
        ],
        "lattice": [
            "lattice payments",
            "lattice payment systems",
            "lattice payments india",
            "lattice pay technologies",
        ],
        "pine": [
            "pine procurement",
            "pine procurement services",
            "pine sourcing private limited",
            "pine supplier networks",
        ],
    }

    def add_case(company: str, candidate: str, same_tax: int, label: str) -> None:
        rows.append(
            [
                fuzz.ratio(company, candidate),
                fuzz.partial_ratio(company, candidate),
                fuzz.token_sort_ratio(company, candidate),
                same_tax,
            ]
        )
        labels.append(label)

    for variants in groups.values():
        for company, candidate in itertools.permutations(variants, 2):
            add_case(company, candidate, 1, "Match")
            add_case(company, candidate, 0, "Review")

    negative_pairs = [
        ("zenith retail", "harbor logistics"),
        ("zenith retail india", "zenon retail labs"),
        ("harbor freight systems", "pine procurement"),
        ("lattice payments", "lattice consulting"),
        ("pine supplier networks", "harbor procurement"),
    ]
    for company, candidate in negative_pairs:
        add_case(company, candidate, 0, "Review")
        add_case(company, candidate, 1, "Review")

    predictions = runtime.models["gstin_match_model"].predict(np.array(rows, dtype=float))
    return _classification_report("gstin_match_model", labels, list(predictions))


def evaluate_audit_model(runtime: Runtime) -> ModelReport:
    rows = []
    labels = []
    for hour in [8, 10, 12, 14, 16, 18]:
        for action in [0, 1, 2]:
            for depth in [1, 2, 3]:
                for payload in [50, 80, 120]:
                    rows.append([hour, action, depth, payload])
                    labels.append("Normal")
    for hour in [0, 1, 2, 3, 23]:
        for action in [1, 2]:
            for depth in [6, 7, 8]:
                for payload in [650, 850, 1000]:
                    rows.append([hour, action, depth, payload])
                    labels.append("Anomaly")
    raw_predictions = runtime.models["audit_model"].predict(np.array(rows, dtype=float))
    predictions = ["Anomaly" if prediction == -1 else "Normal" for prediction in raw_predictions]
    return _classification_report("audit_model", labels, predictions)


def evaluate_vendor_model(runtime: Runtime) -> ModelReport:
    rows = []
    expected_scores = []
    labels = []
    for on_time in [40, 55, 70, 85, 95]:
        for defect in [1, 4, 8, 12, 18]:
            for reopen in [1, 5, 10, 20, 30]:
                for spend in [100000, 500000, 2000000, 6000000]:
                    score = _vendor_score(on_time, defect, reopen, spend)
                    rows.append([on_time, defect, reopen, spend])
                    expected_scores.append(score)
                    labels.append(_vendor_band(score))
    predicted_scores = runtime.models["vendor_model"].predict(np.array(rows, dtype=float))
    predictions = [_vendor_band(score) for score in predicted_scores]
    mae = float(np.mean(np.abs(np.array(predicted_scores) - np.array(expected_scores))))
    return _classification_report("vendor_model", labels, predictions, notes=[f"Banding MAE={mae:.2f} score points."])


def evaluate_self_heal_model(runtime: Runtime) -> ModelReport:
    rows = []
    labels = []
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
    predictions = runtime.models["self_heal_model"].predict(np.array(rows, dtype=float))
    return _classification_report("self_heal_model", labels, list(predictions))


def evaluate_route_model(runtime: Runtime) -> ModelReport:
    candidate_sets = [
        lambda city: [f"{city} Central Hub", "Delhi NCR", "Pune DC", "Bengaluru FC"],
        lambda city: ["Ahmedabad FC", f"{city} Express Node", "Hyderabad DC", "Kolkata Hub"],
        lambda city: ["Jaipur FC", "Lucknow DC", f"{city} Warehouse", "Coimbatore FC"],
    ]
    total = 0
    correct = 0
    for city in ["Mumbai", "Delhi", "Chennai", "Pune", "Bengaluru"]:
        for urgency in [0, 1, 2]:
            for order_value in [800, 5000, 18000, 65000, 125000]:
                for factory in candidate_sets:
                    regions = factory(city)
                    expected_rows = []
                    predicted_rows = []
                    for index, region in enumerate(regions):
                        city_match = 1 if city.lower() in region.lower() else 0
                        expected_rows.append((region, _route_score(city_match, urgency, order_value, index)))
                        score = float(runtime.models["route_model"].predict(np.array([[city_match, urgency, order_value, index]], dtype=float))[0])
                        predicted_rows.append((region, score))
                    expected_top = max(expected_rows, key=lambda item: item[1])[0]
                    predicted_top = max(predicted_rows, key=lambda item: item[1])[0]
                    total += 1
                    if expected_top == predicted_top:
                        correct += 1
    accuracy = correct / total
    return _custom_report("route_model", accuracy, accuracy, total, notes=["Measured as top-choice routing accuracy across generated candidate sets."])


def evaluate_supply_chain_model(runtime: Runtime) -> ModelReport:
    rows = []
    labels = []
    expected_etas = []
    for delay in [0, 4, 8, 12, 18, 24, 36, 48, 60]:
        for cover in [1, 2, 3, 5, 7, 10, 14]:
            for congestion in [0, 1, 2]:
                eta = _eta_impact(delay, cover, congestion)
                rows.append([delay, cover, congestion])
                expected_etas.append(eta)
                labels.append(_supply_chain_band(eta, cover))
    predicted_etas = runtime.models["supply_chain_model"].predict(np.array(rows, dtype=float))
    predictions = [_supply_chain_band(eta, cover) for eta, (_delay, cover, _congestion) in zip(predicted_etas, rows)]
    mae = float(np.mean(np.abs(np.array(predicted_etas) - np.array(expected_etas))))
    return _classification_report("supply_chain_model", labels, predictions, notes=[f"Banding MAE={mae:.2f} hours."])


def evaluate_pricing_model(runtime: Runtime) -> ModelReport:
    rows = []
    labels = []
    expected_values = []
    for gap in [-250, -180, -80, -20, 0, 40, 120, 200, 250]:
        for inventory_days in [4, 8, 15, 25, 35, 45]:
            for demand in [20, 35, 50, 65, 80, 95]:
                for conversion in [1.2, 2.5, 3.5, 5.0, 6.8, 7.8]:
                    multiplier = _pricing_multiplier(gap, inventory_days, demand, conversion)
                    rows.append([gap, inventory_days, demand, conversion])
                    expected_values.append(multiplier)
                    labels.append(_pricing_band(multiplier))
    predicted_values = runtime.models["pricing_model"].predict(np.array(rows, dtype=float))
    predictions = [_pricing_band(value) for value in predicted_values]
    mae = float(np.mean(np.abs(np.array(predicted_values) - np.array(expected_values))))
    return _classification_report("pricing_model", labels, predictions, notes=[f"Banding MAE={mae:.3f} multiplier points."])


def evaluate_keyword_vectorizer(runtime: Runtime) -> ModelReport:
    cases = [
        ({"audit", "encryption", "access control"}, "We need audit logging, encryption, and access control for the regulated workload."),
        ({"warehouse", "port congestion", "route"}, "Port congestion is delaying the warehouse route and shipment plan."),
        ({"pricing", "conversion", "demand"}, "The pricing review focuses on conversion, demand, and competitor pressure."),
        ({"contact center", "transcript", "sentiment"}, "The contact center needs transcript QA and sentiment tracking."),
        ({"procurement", "supplier", "rfq"}, "Procurement needs supplier onboarding and RFQ workflow automation."),
    ]
    vectorizer = runtime.models["keyword_vectorizer"]
    accuracies = []
    precisions = []
    for expected, text in cases:
        predicted = top_keywords(vectorizer, text, 4)
        hits = len(expected.intersection(predicted))
        accuracies.append(1.0 if hits >= 2 else 0.0)
        precisions.append(hits / max(1, len(predicted)))
    return ModelReport(
        name="keyword_vectorizer",
        accuracy=float(mean(accuracies)),
        precision=float(mean(precisions)),
        support=len(cases),
        status="SKIP",
        notes=["Auxiliary featurizer benchmark only; it is excluded from the pass/fail quality gate because it does not emit class labels."],
    )


def evaluate_ai4bharat_api() -> ModelReport:
    cases = [
        ("Hindi", "मुझे भुगतान रसीद चाहिए।"),
        ("Tamil", "எங்களுக்கு புதிய விலைப்பட்டியல் வேண்டும்."),
        ("Telugu", "దయచేసి ఇన్వాయిస్ స్థితి చెప్పండి."),
        ("Bengali", "আমাদের ড্যাশবোর্ড আপডেট পাঠান।"),
        ("Gujarati", "મને ચુકવણીની રસીદ મોકલો."),
    ]
    detections, note = detect_languages_with_ai4bharat(cases[0][1])
    if not detections and note is None:
        return _custom_report("ai4bharat_language_api", None, None, 0, notes=["Skipped because AI4Bharat credentials are not configured."])

    y_true = []
    y_pred = []
    notes = []
    for expected, text in cases:
        detected, result_note = detect_languages_with_ai4bharat(text)
        if result_note and not detected:
            return _custom_report("ai4bharat_language_api", None, None, len(y_true), notes=[result_note])
        predicted = detected[0]["language"] if detected else "Unknown"
        y_true.append(expected)
        y_pred.append(predicted)
    if note:
        notes.append(note)
    return _classification_report("ai4bharat_language_api", y_true, y_pred, notes=notes)


def evaluate_ollama_api(runtime: Runtime) -> ModelReport:
    available, note = ollama_status()
    if not available:
        return _custom_report("ollama_domain_api", None, None, 0, notes=[note])

    schema = {
        "type": "object",
        "properties": {
            "domain": {
                "type": "string",
                "enum": ["analytics", "logistics", "security", "contact-center", "procurement"],
            }
        },
        "required": ["domain"],
    }
    y_true = []
    y_pred = []
    for expected, requirement_note in OLLAMA_DOMAIN_CASES:
        payload, error_note = runtime.ollama_json(
            "You classify enterprise solution requirements into one of five domains only and respond with strict JSON.",
            "\n".join(
                [
                    "Choose one domain from analytics, logistics, security, contact-center, procurement.",
                    f"Requirement note: {requirement_note}",
                ]
            ),
            schema,
        )
        prediction = payload.get("domain") if payload else "Unknown"
        if error_note and prediction == "Unknown":
            prediction = "Unknown"
        y_true.append(expected)
        y_pred.append(prediction)
    return _classification_report("ollama_domain_api", y_true, y_pred, notes=[f"Provider: {note}"])


def run() -> None:
    ensure_artifacts(force=True)
    runtime = Runtime.load()
    reports = [
        evaluate_intent_model(runtime),
        evaluate_sentiment_model(runtime),
        evaluate_meeting_model(runtime),
        evaluate_contract_model(runtime),
        evaluate_compliance_model(runtime),
        evaluate_bi_model(runtime),
        evaluate_rfq_model(runtime),
        evaluate_invoice_model(runtime),
        evaluate_kyc_model(runtime),
        evaluate_sla_model(runtime),
        evaluate_gstin_model(runtime),
        evaluate_audit_model(runtime),
        evaluate_vendor_model(runtime),
        evaluate_self_heal_model(runtime),
        evaluate_route_model(runtime),
        evaluate_supply_chain_model(runtime),
        evaluate_pricing_model(runtime),
        evaluate_keyword_vectorizer(runtime),
        evaluate_ai4bharat_api(),
        evaluate_ollama_api(runtime),
    ]

    payload = {
        "generatedAt": _utc_now(),
        "thresholds": {
            "minimumAccuracy": MIN_ACCURACY,
            "minimumPrecision": MIN_PRECISION,
        },
        "reports": [asdict(report) for report in reports],
    }
    REPORT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Quality report written to {REPORT_PATH}")
    for report in reports:
        print(
            f"{report.name}: status={report.status}, accuracy={_pct(report.accuracy)}, "
            f"precision={_pct(report.precision)}, support={report.support}"
        )
        for note in report.notes:
            print(f"  - {note}")

    failures = [report.name for report in reports if report.status == "FAIL"]
    if failures:
        print("Quality gate failed for:")
        for name in failures:
            print(f"- {name}")
        raise SystemExit(1)

    print("Quality gate passed for all scored models.")


if __name__ == "__main__":
    run()
