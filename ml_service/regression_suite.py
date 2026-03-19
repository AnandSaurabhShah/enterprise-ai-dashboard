from __future__ import annotations

from runtime import Runtime, read_store, write_store


def metric_value(result: dict, label: str) -> str:
    for metric in result.get("metrics", []):
        if metric.get("label") == label:
            return str(metric.get("value"))
    raise AssertionError(f"Metric {label!r} was not found in {result.get('headline')!r}")


def section(result: dict, title: str) -> dict:
    for item in result.get("sections", []):
        if item.get("title") == title:
            return item
    raise AssertionError(f"Section {title!r} was not found in {result.get('headline')!r}")


def section_items(result: dict, title: str) -> list[str]:
    return [str(item) for item in section(result, title).get("items", [])]


def parse_currency(value: str) -> int:
    digits = value.replace("INR", "").replace(",", "").strip()
    return int(float(digits))


class RegressionSuite:
    def __init__(self) -> None:
        self.runtime = Runtime.load()
        self.failures: list[str] = []
        self.checks = 0

    def check(self, condition: bool, message: str) -> None:
        self.checks += 1
        if not condition:
            self.failures.append(message)

    def infer(self, feature_id: str, action_id: str, inputs: dict) -> dict:
        return self.runtime.infer(feature_id, action_id, inputs, {})

    def run(self) -> None:
        original_rag = read_store("rag-memory", [])
        original_audit = read_store("audit-log", [])
        try:
            self.test_intent_model()
            self.test_language_coverage()
            self.test_sentiment_model()
            self.test_meeting_model()
            self.test_invoice_model()
            self.test_kyc_model()
            self.test_sla_model()
            self.test_gstin_model()
            self.test_audit_model()
            self.test_contract_model()
            self.test_einvoice_model()
            self.test_vendor_model()
            self.test_self_heal_model()
            self.test_route_model()
            self.test_supply_chain_model()
            self.test_bi_model()
            self.test_rfq_model()
            self.test_compliance_model()
            self.test_pricing_model()
            self.test_employee_sentiment_model()
        finally:
            write_store("rag-memory", original_rag)
            write_store("audit-log", original_audit)

        if self.failures:
            print("Regression suite failed:")
            for failure in self.failures:
                print(f"- {failure}")
            raise SystemExit(1)

        print(f"Regression suite passed with {self.checks} checks.")

    def test_intent_model(self) -> None:
        cases = [
            ("Billing", "Mujhe invoice status chahiye but payment receipt is missing today"),
            ("Support", "Login nahin ho raha and the dashboard is stuck after authentication"),
            ("Sales", "Need pricing quote and product demo for the enterprise rollout"),
            ("Logistics", "Port congestion is delaying the shipment and we need an ETA update"),
            ("Compliance", "Please review the DPDP policy wording and audit evidence gaps"),
            ("Billing", "मुझे चालान की स्थिति चाहिए और भुगतान रसीद नहीं मिली"),
            ("Logistics", "போர்ட் நெரிசலால் சரக்கு தாமதமாகிறது, ETA வேண்டும்"),
        ]
        for expected, text in cases:
            result = self.infer("code-mixed", "analyze", {"inputText": text, "channel": "Support chat", "region": "India"})
            self.check(metric_value(result, "Intent") == expected, f"Intent model misclassified {text!r}")

        mixed = self.infer(
            "code-mixed",
            "analyze",
            {"inputText": "Mujhe login issue hai but customer also wants invoice details", "channel": "WhatsApp", "region": "India"},
        )
        self.check(metric_value(mixed, "Code mix") != "Single language", "Code-mixed handler missed the mixed-language signal")

    def test_language_coverage(self) -> None:
        summary = self.runtime.summary()
        self.check(int(summary.get("supportedIndianLanguages", 0)) == 22, "Runtime summary did not expose all 22 scheduled Indian languages")

        hindi = self.infer("code-mixed", "analyze", {"inputText": "मुझे चालान की स्थिति चाहिए", "channel": "WhatsApp", "region": "India"})
        self.check("Devanagari script detected" in section_items(hindi, "Language Signals"), "Hindi script was not detected")
        self.check("Hindi" in section_items(hindi, "Indian Language Candidates"), "Hindi was missing from Indian language candidates")

        telugu = self.infer("code-mixed", "analyze", {"inputText": "చెల్లింపు రశీదు లేదు, ఇన్వాయిస్ స్థితి చెప్పండి", "channel": "Email", "region": "India"})
        self.check("Telugu" in section_items(telugu, "Indian Language Candidates"), "Telugu coverage was not exposed")

        tamil = self.infer("multilingual-risk", "analyze", {"contractText": "வாடிக்கையாளர் தரவு கட்டுப்பாடின்றி பகிரலாம், ஒப்பந்தத்தை முடிக்க முடியாது", "jurisdiction": "India", "contractLanguage": "Tamil"})
        self.check("Tamil" in section_items(tamil, "Indian Language Candidates"), "Tamil coverage was not exposed in the contract analyzer")
        self.check(len(section_items(hindi, "Supported Indian Languages")) == 22, "Supported Indian languages section was incomplete")

    def test_sentiment_model(self) -> None:
        cases = [
            ("Positive", "The team was helpful and the billing issue got resolved quickly."),
            ("Neutral", "Sharing the latest customer update for review by the support lead."),
            ("Negative", "The customer is angry because the service is still broken and no one owns it."),
        ]
        for expected, text in cases:
            result = self.infer("sentiment", "score", {"feedbackText": text, "customerTier": "Mid-market", "responseWindow": "24 hours"})
            self.check(metric_value(result, "Sentiment") == expected, f"Sentiment model misclassified {text!r}")

    def test_meeting_model(self) -> None:
        transcript = """Asha: Please send the vendor shortlist by Friday.
Rahul: Decision: onboard the Mumbai vendor first.
Mina: Risk: GST validation may delay the launch.
Note: The customer wants a daily progress update."""
        result = self.infer("meeting", "analyze", {"transcriptText": transcript, "meetingGoal": "Launch review"})
        self.check(int(metric_value(result, "Actions")) >= 1, "Meeting model missed the action item")
        self.check(int(metric_value(result, "Decisions")) >= 1, "Meeting model missed the decision")
        self.check(int(metric_value(result, "Risks")) >= 1, "Meeting model missed the risk")

        multilingual_transcript = """Asha: कृपया शुक्रवार तक विक्रेता सूची भेज दें।
Rahul: निर्णय: पहले मुंबई विक्रेता को ऑनबोर्ड किया जाएगा।
Mina: ஆபத்து: துறைமுக நெரிசல் காரணமாக சரக்கு தாமதமாகலாம்।"""
        multilingual = self.infer("meeting", "analyze", {"transcriptText": multilingual_transcript, "meetingGoal": "Launch review"})
        self.check(int(metric_value(multilingual, "Actions")) >= 1, "Meeting model missed a multilingual action item")
        self.check(int(metric_value(multilingual, "Decisions")) >= 1, "Meeting model missed a multilingual decision")
        self.check(int(metric_value(multilingual, "Risks")) >= 1, "Meeting model missed a multilingual risk")

    def test_invoice_model(self) -> None:
        valid_text = """Invoice No: INV-2026-1042
Date: 03/19/2026
Supplier: Orbit Logistics Pvt Ltd
Buyer: Nova Retail
Subtotal: 1000
Tax: 180
Total: 1180
GSTIN: 27ABCDE1234F1Z5"""
        result = self.infer("invoice", "parse", {"invoiceText": valid_text, "invoiceContext": "Accounts payable"})
        self.check(metric_value(result, "Validation") == "Valid", "Invoice model did not treat a complete invoice as valid")
        self.check(metric_value(result, "Arithmetic") == "Passed", "Invoice arithmetic check failed on a balanced invoice")

        invalid_text = "Supplier: Unknown\nTotal: 500"
        invalid = self.infer("invoice", "parse", {"invoiceText": invalid_text, "invoiceContext": "Expense audit"})
        self.check(metric_value(invalid, "Validation") != "Valid", "Invoice model treated a sparse invoice as valid")

    def test_kyc_model(self) -> None:
        clear = self.infer(
            "kyc",
            "extract",
            {
                "rawIdentityText": "Name: Rohan Mehta\nPAN: ABCDE1234F\nAadhaar: 1234 5678 9012\nEmail: rohan@example.com",
                "documentRegion": "India",
            },
        )
        self.check(metric_value(clear, "Risk") == "Clear", "KYC model did not clear a well-formed Indian identity payload")

        high_review = self.infer(
            "kyc",
            "extract",
            {"rawIdentityText": "Name: Rohan Mehta\nAadhaar: 1234 5678 9012\nAadhaar: 2222 3333 4444", "documentRegion": "India"},
        )
        self.check(metric_value(high_review, "Risk") == "High Review", "KYC model missed the duplicated Aadhaar high-review case")

    def test_sla_model(self) -> None:
        low = self.infer(
            "sla",
            "predict",
            {
                "priority": "Low",
                "category": "Support",
                "customerTier": "Standard",
                "complexity": "Simple",
                "firstResponseMinutes": 5,
                "backlogCount": 2,
            },
        )
        self.check(metric_value(low, "Risk band") == "Low", "SLA model overpredicted a low-risk ticket")

        critical = self.infer(
            "sla",
            "predict",
            {
                "priority": "Critical",
                "category": "Technical",
                "customerTier": "Enterprise",
                "complexity": "Complex",
                "firstResponseMinutes": 300,
                "backlogCount": 50,
            },
        )
        self.check(metric_value(critical, "Risk band") == "Critical", "SLA model underpredicted a critical-risk ticket")

    def test_gstin_model(self) -> None:
        result = self.infer(
            "gstin",
            "reconcile",
            {
                "companyName": "Orbit Logistics",
                "supplierRecords": "Orbit Logistics Pvt Ltd | GSTIN 27ABCDE1234F1Z5 | Mumbai\nStellar Payments | GSTIN 29ABCDE1234F1Z5 | Bengaluru",
                "countryFocus": "India",
            },
        )
        rows = section(result, "Supplier Match Scores")["rows"]
        self.check(rows[0]["decision"] == "Match", "GSTIN matcher did not rank the matching supplier first")

    def test_audit_model(self) -> None:
        write = self.infer(
            "audit",
            "write",
            {"actionType": "READ", "actorId": "ops.user.42", "resourceUri": "/vendors/ACME-1", "auditPayload": "{\"reason\":\"ticket-123\"}"},
        )
        self.check("committed" in write["headline"].lower(), "Audit write did not complete successfully")
        verify = self.infer("audit", "verify", {})
        self.check(metric_value(verify, "Status") == "Valid", "Audit verification failed after a clean write")

    def test_contract_model(self) -> None:
        high = self.infer(
            "multilingual-risk",
            "analyze",
            {
                "contractText": "The reseller has exclusive rights, unlimited liability, and the agreement auto-renews yearly.",
                "jurisdiction": "India",
                "contractLanguage": "English",
            },
        )
        self.check(metric_value(high, "Risk band") == "High", "Contract model missed a high-risk clause set")

        low = self.infer(
            "multilingual-risk",
            "analyze",
            {
                "contractText": "Either party may terminate with thirty days notice and liability is capped.",
                "jurisdiction": "India",
                "contractLanguage": "English",
            },
        )
        self.check(metric_value(low, "Risk band") == "Low", "Contract model overpredicted a low-risk clause set")

        hindi_high = self.infer(
            "multilingual-risk",
            "analyze",
            {
                "contractText": "ग्राहक पर असीमित देयता होगी और अनुबंध हर साल स्वतः नवीनीकृत होगा",
                "jurisdiction": "India",
                "contractLanguage": "Hindi",
            },
        )
        self.check(metric_value(hindi_high, "Risk band") == "High", "Contract model missed a high-risk Hindi clause set")

    def test_einvoice_model(self) -> None:
        payload = """Invoice No: INV-7001
Date: 03/19/2026
Supplier: Orbit Logistics
Buyer: Nova Retail
Total: 1180
GSTIN: 27ABCDE1234F1Z5"""
        result = self.infer("smart-einvoice", "validate", {"invoicePayload": payload, "invoiceSource": "India GST"})
        self.check(metric_value(result, "Validation") in {"Valid", "Review"}, "e-Invoice validator produced an unexpected validation class")

    def test_vendor_model(self) -> None:
        strong = self.infer(
            "vendor-scorer",
            "score",
            {"vendorName": "Orbit Logistics", "onTimeRate": 98, "defectRate": 1, "ticketReopenRate": 2, "quarterlySpend": 6000000},
        )
        self.check(metric_value(strong, "Band") == "Strategic", "Vendor model underpredicted a strong vendor")

        weak = self.infer(
            "vendor-scorer",
            "score",
            {"vendorName": "Slowline", "onTimeRate": 45, "defectRate": 18, "ticketReopenRate": 25, "quarterlySpend": 100000},
        )
        self.check(metric_value(weak, "Band") == "At risk", "Vendor model underpenalized a weak vendor")

    def test_self_heal_model(self) -> None:
        backoff = self.infer(
            "self-healing",
            "simulate",
            {"httpStatus": 429, "criticality": "Medium", "retryCount": 1, "failureRegion": "ap-south-1", "serviceName": "payments"},
        )
        self.check(metric_value(backoff, "Policy") == "Backoff Retry", "Self-healing model missed the rate-limit backoff case")

        breaker = self.infer(
            "self-healing",
            "simulate",
            {"httpStatus": 503, "criticality": "Critical", "retryCount": 4, "failureRegion": "ap-south-1", "serviceName": "payments"},
        )
        self.check(metric_value(breaker, "Policy") == "Circuit Break", "Self-healing model missed the circuit-break case")

    def test_route_model(self) -> None:
        result = self.infer(
            "multi-agent-ondc",
            "route",
            {
                "buyerCity": "Mumbai",
                "productCategory": "B2B supplies",
                "orderValue": 18000,
                "deliveryWindow": "Same day",
                "sellerRegions": "Delhi NCR, Mumbai, Pune",
            },
        )
        self.check("Mumbai" in result["headline"], "Route model did not prefer the city-matched urgent route")

    def test_supply_chain_model(self) -> None:
        high = self.infer(
            "supply-chain-twin",
            "simulate",
            {"networkSnapshot": "Delay: 24 hours\nPort congestion: High", "priorityLane": "Mumbai -> Bengaluru", "inventoryDaysCover": 2},
        )
        self.check(metric_value(high, "Risk") == "High", "Supply-chain model underpredicted a stressed network")

        low = self.infer(
            "supply-chain-twin",
            "simulate",
            {"networkSnapshot": "Delay: 6 hours\nPort congestion: Low", "priorityLane": "Delhi -> Jaipur", "inventoryDaysCover": 12},
        )
        self.check(metric_value(low, "Risk") == "Low", "Supply-chain model overpredicted a stable network")

    def test_bi_model(self) -> None:
        regional_dataset = "region,revenue_prev,revenue_curr\nWest,120,160\nNorth,100,130\nSouth,90,80"
        trend_dataset = "month,revenue\nJan,100\nFeb,120\nMar,150"

        max_result = self.infer("conv-bi", "query", {"businessQuestion": "Which region had the highest revenue_curr?", "datasetText": regional_dataset})
        self.check("West" in max_result["summary"], "BI model missed the max case")

        min_result = self.infer("conv-bi", "query", {"businessQuestion": "Which region had the lowest revenue_curr?", "datasetText": regional_dataset})
        self.check("South" in min_result["summary"], "BI model missed the min case")

        compare_result = self.infer("conv-bi", "query", {"businessQuestion": "Compare West and North on revenue_curr", "datasetText": regional_dataset})
        self.check("West" in compare_result["summary"] and "North" in compare_result["summary"], "BI compare answer did not mention both segments")

        trend_result = self.infer("conv-bi", "query", {"businessQuestion": "Show the monthly trend over time", "datasetText": trend_dataset})
        self.check("upward" in trend_result["summary"], "BI trend answer did not detect the upward trend")

        summary_result = self.infer("conv-bi", "query", {"businessQuestion": "Give me a quick summary of this dataset", "datasetText": trend_dataset})
        self.check("3 rows and 2 columns" in summary_result["summary"], "BI summary answer did not report the dataset shape")

        hindi_result = self.infer("conv-bi", "query", {"businessQuestion": "सबसे ज़्यादा revenue किस region का है", "datasetText": regional_dataset})
        self.check("West" in hindi_result["summary"], "BI model missed the Hindi max-query case")

    def test_rfq_model(self) -> None:
        contact_center = self.infer(
            "rfq-generator",
            "generate",
            {
                "requirementNotes": "Need a multilingual contact center analytics platform for APAC support teams with call transcripts and QA.",
                "budgetBand": "10L-50L INR",
                "timelineWeeks": 12,
                "mandatoryCapabilities": "Hindi support\nAudit logging",
            },
        )
        self.check(metric_value(contact_center, "Domain") == "contact-center", "RFQ domain model missed the contact-center requirement")

        hindi_contact_center = self.infer(
            "rfq-generator",
            "generate",
            {
                "requirementNotes": "हमें बहुभाषी contact center analytics और voice support चाहिए",
                "budgetBand": "10L-50L INR",
                "timelineWeeks": 10,
            },
        )
        self.check(metric_value(hindi_contact_center, "Domain") == "contact-center", "RFQ domain model missed the Hindi contact-center requirement")

        security = self.infer(
            "rfq-generator",
            "generate",
            {
                "requirementNotes": "Require audit logging, encryption, IAM, monitoring, and policy enforcement for regulated workloads.",
                "budgetBand": "50L-2Cr INR",
                "timelineWeeks": 16,
            },
        )
        self.check(metric_value(security, "Domain") == "security", "RFQ domain model missed the security requirement")

    def test_compliance_model(self) -> None:
        low = self.infer(
            "compliance-scanner",
            "scan",
            {
                "policyFramework": "DPDP",
                "artifactText": "The policy documents consent, purpose limitation, retention, breach notification, and data principal rights.",
            },
        )
        self.check(metric_value(low, "Risk") == "Low", "Compliance model overpredicted a strong DPDP artifact")

        high = self.infer(
            "compliance-scanner",
            "scan",
            {"policyFramework": "GDPR", "artifactText": "There is no lawful basis, no retention control, and no breach notification workflow."},
        )
        self.check(metric_value(high, "Risk") == "High", "Compliance model missed a weak GDPR artifact")

        hindi_low = self.infer(
            "compliance-scanner",
            "scan",
            {"policyFramework": "DPDP", "artifactText": "नीति में एन्क्रिप्शन, एक्सेस कंट्रोल, रिटेंशन और ब्रीच सूचना शामिल है"},
        )
        self.check(metric_value(hindi_low, "Risk") == "Low", "Compliance model missed a strong Hindi DPDP artifact")

    def test_pricing_model(self) -> None:
        increase = self.infer(
            "dynamic-pricing",
            "optimize",
            {"basePrice": 1000, "competitorPrice": 1200, "inventoryDays": 5, "demandLoad": 92, "conversionRate": 6.5},
        )
        self.check(parse_currency(metric_value(increase, "Recommended")) > parse_currency(metric_value(increase, "Current price")), "Pricing model did not raise price under strong-demand conditions")

        decrease = self.infer(
            "dynamic-pricing",
            "optimize",
            {"basePrice": 1000, "competitorPrice": 900, "inventoryDays": 40, "demandLoad": 20, "conversionRate": 2.0},
        )
        self.check(parse_currency(metric_value(decrease, "Recommended")) <= parse_currency(metric_value(decrease, "Current price")), "Pricing model did not ease price under weak-demand conditions")

    def test_employee_sentiment_model(self) -> None:
        healthy = self.infer(
            "employee-sentiment",
            "pulse",
            {"teamName": "APAC Support", "feedbackBatch": "Leadership was responsive and the team felt supported this sprint.", "sampleSize": 12},
        )
        self.check("healthy" in healthy["headline"].lower(), "Employee sentiment model underpredicted a healthy team pulse")

        at_risk = self.infer(
            "employee-sentiment",
            "pulse",
            {"teamName": "APAC Support", "feedbackBatch": "There is burnout, overload, weekend work, and a lot of stress with late night escalations.", "sampleSize": 12},
        )
        self.check("at risk" in at_risk["headline"].lower(), "Employee sentiment model missed the burnout-heavy pulse")


if __name__ == "__main__":
    RegressionSuite().run()
