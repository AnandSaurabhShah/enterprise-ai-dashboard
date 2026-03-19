export const featureCatalog = [
  {
    id: "code-mixed",
    title: "Code-Mixed Understanding",
    category: "Indic-First NLP",
    description: "Analyze intent from Hinglish, Tanglish, and 40+ global mixed-language texts.",
    status: "live",
    actions: [
      {
        id: "analyze",
        label: "Analyze Intent",
        submitLabel: "Analyze Global Intent",
        description: "Detect language signals, business intent, urgency, and entities from multilingual text.",
        fields: [
          { name: "inputText", label: "Conversation Text", type: "textarea", placeholder: "Mujhe invoice status chahiye, but client also wants VAT details today.", required: true },
          { name: "channel", label: "Channel", type: "select", options: ["Support chat", "Email", "WhatsApp", "Voice transcript"], defaultValue: "Support chat" },
          { name: "region", label: "Region", type: "select", options: ["India", "SEA", "Middle East", "Europe", "North America"], defaultValue: "India" },
        ],
      },
    ],
  },
  {
    id: "sentiment",
    title: "Sentiment Analyzer",
    category: "Analytics",
    description: "Score customer feedback accurately across diverse cultural nuances.",
    status: "live",
    actions: [
      {
        id: "score",
        label: "Score Feedback",
        submitLabel: "Score Sentiment",
        description: "Measure sentiment, urgency, emotional tone, and recommended response intensity.",
        fields: [
          { name: "feedbackText", label: "Customer Feedback", type: "textarea", placeholder: "Service was fast but billing still feels confusing and the team sounded dismissive.", required: true },
          { name: "customerTier", label: "Customer Tier", type: "select", options: ["SMB", "Mid-market", "Enterprise"], defaultValue: "Mid-market" },
          { name: "responseWindow", label: "Response SLA", type: "select", options: ["Same day", "24 hours", "48 hours"], defaultValue: "24 hours" },
        ],
      },
    ],
  },
  {
    id: "meeting",
    title: "Meeting Intelligence",
    category: "Audio AI",
    description: "Extract action items and summaries from multi-accent global meetings.",
    status: "live",
    actions: [
      {
        id: "analyze",
        label: "Analyze Meeting",
        submitLabel: "Analyze Meeting",
        description: "Paste a transcript or upload a text/PDF file to extract decisions, owners, and next steps.",
        fields: [
          { name: "meetingGoal", label: "Meeting Goal", type: "text", placeholder: "Weekly delivery review" },
          { name: "transcriptText", label: "Transcript or Notes", type: "textarea", placeholder: "Asha: We need the vendor shortlist by Friday...", required: false },
          { name: "meetingFile", label: "Transcript File", type: "file", accept: ".txt,.md,.json,.csv,.pdf,.mp3,.wav,.m4a", required: false },
        ],
      },
    ],
  },
  {
    id: "invoice",
    title: "Invoice Parser",
    category: "OCR & Parsing",
    description: "Digitize and parse tabular data from global PDFs and handwritten challans.",
    status: "live",
    actions: [
      {
        id: "parse",
        label: "Parse Invoice",
        submitLabel: "Parse Invoice",
        description: "Upload a file or paste raw invoice text to extract amounts, parties, tax IDs, and line items.",
        fields: [
          { name: "invoiceContext", label: "Invoice Context", type: "select", options: ["Accounts payable", "Vendor onboarding", "Expense audit"], defaultValue: "Accounts payable" },
          { name: "invoiceText", label: "Raw Invoice Text", type: "textarea", placeholder: "Invoice #INV-2026-1042\nSupplier: Orbit Logistics\nTotal: 48,500 INR\nGSTIN: 27ABCDE1234F1Z5", required: false },
          { name: "invoiceFile", label: "Invoice File", type: "file", accept: ".txt,.md,.json,.csv,.pdf,.png,.jpg,.jpeg,.webp", required: false },
        ],
      },
    ],
  },
  {
    id: "kyc",
    title: "Global & Bharat KYC",
    category: "Compliance",
    description: "Automated entity extraction from Aadhaar, PAN, and Global Corporate IDs.",
    status: "live",
    actions: [
      {
        id: "extract",
        label: "Extract Entities",
        submitLabel: "Extract Global Entities",
        description: "Extract normalized IDs, names, locations, and identity risk flags from raw text.",
        fields: [
          { name: "rawIdentityText", label: "Identity Payload", type: "textarea", placeholder: "Name: Rohan Mehta\nPAN: ABCDE1234F\nAadhaar: 1234 5678 9012\nCompany ID: US-DE-889130", required: true },
          { name: "documentRegion", label: "Primary Jurisdiction", type: "select", options: ["India", "US", "EU", "Middle East", "Global mixed"], defaultValue: "India" },
        ],
      },
    ],
  },
  {
    id: "sla",
    title: "SLA Breach Predictor",
    category: "Predictive",
    description: "Predict risk of SLA breaches using classification models for high-volume support.",
    status: "live",
    actions: [
      {
        id: "predict",
        label: "Predict Risk",
        submitLabel: "Predict Risk",
        description: "Estimate breach risk using ticket priority, complexity, queue pressure, and first response times.",
        fields: [
          { name: "priority", label: "Priority", type: "select", options: ["Low", "Medium", "High", "Critical"], defaultValue: "Medium" },
          { name: "category", label: "Category", type: "select", options: ["Support", "Billing", "Technical", "Sales"], defaultValue: "Support" },
          { name: "customerTier", label: "Customer Tier", type: "select", options: ["Standard", "Premium", "Enterprise"], defaultValue: "Premium" },
          { name: "complexity", label: "Complexity", type: "select", options: ["Simple", "Moderate", "Complex"], defaultValue: "Moderate" },
          { name: "firstResponseMinutes", label: "First Response Delay (minutes)", type: "number", placeholder: "45" },
          { name: "backlogCount", label: "Open Queue Count", type: "number", placeholder: "18" },
        ],
      },
    ],
  },
  {
    id: "rag",
    title: "Enterprise RAG Memory",
    category: "Knowledge",
    description: "Embed and retrieve knowledge directly from corporate memory with billion-scale vector search.",
    status: "live",
    actions: [
      {
        id: "add-document",
        label: "Add Document",
        submitLabel: "Add Document To Memory",
        description: "Store a knowledge artifact in the local memory index with search-friendly tokens.",
        fields: [
          { name: "documentTitle", label: "Document Title", type: "text", placeholder: "APAC escalation policy", required: true },
          { name: "documentCategory", label: "Category", type: "text", placeholder: "Operations" },
          { name: "documentContent", label: "Document Content", type: "textarea", placeholder: "Escalate P1 incidents within 15 minutes to the regional lead...", required: false },
          { name: "documentFile", label: "Document File", type: "file", accept: ".txt,.md,.json,.csv,.pdf", required: false },
        ],
      },
      {
        id: "search",
        label: "Search Memory",
        submitLabel: "Search Memory",
        description: "Retrieve the most relevant indexed documents with overlap scoring and intent hints.",
        fields: [
          { name: "queryText", label: "Search Query", type: "text", placeholder: "How do we escalate APAC billing incidents?", required: true },
          { name: "topK", label: "Top Matches", type: "select", options: ["3", "5", "8"], defaultValue: "5" },
        ],
      },
    ],
  },
  {
    id: "gstin",
    title: "GSTIN & VAT Reconciliation",
    category: "Finance",
    description: "Reconcile Indian GSTIN and Global VAT supplier records using structured extraction.",
    status: "live",
    actions: [
      {
        id: "reconcile",
        label: "Reconcile Records",
        submitLabel: "Extract And Reconcile",
        description: "Cluster supplier records, extract tax IDs, and identify duplicates or likely mismatches.",
        fields: [
          { name: "companyName", label: "Target Company", type: "text", placeholder: "Orbit Logistics", required: true },
          { name: "supplierRecords", label: "Supplier Data", type: "textarea", placeholder: "Orbit Logistics Pvt Ltd | GSTIN 27ABCDE1234F1Z5 | Mumbai\nOrbit Logistics GmbH | VAT DE123456789", required: true },
          { name: "countryFocus", label: "Country Focus", type: "select", options: ["India", "Europe", "Global"], defaultValue: "Global" },
        ],
      },
    ],
  },
  {
    id: "audit",
    title: "Cryptographic Audit Trail",
    category: "Security",
    description: "Write and verify immutable audit trail entries compliant with DPDP and GDPR.",
    status: "live",
    actions: [
      {
        id: "write",
        label: "Write Entry",
        submitLabel: "Write Audit Entry",
        description: "Append an immutable entry to the local cryptographic chain.",
        fields: [
          { name: "actionType", label: "Action", type: "text", placeholder: "READ", required: true },
          { name: "actorId", label: "User ID", type: "text", placeholder: "ops.user.42", required: true },
          { name: "resourceUri", label: "Resource URI", type: "text", placeholder: "/vendors/ACME-1", required: true },
          { name: "auditPayload", label: "Reason / Metadata", type: "textarea", placeholder: "{\"reason\": \"support ticket #1234\"}", required: false },
        ],
      },
      {
        id: "verify",
        label: "Verify Chain",
        submitLabel: "Verify Chain",
        description: "Recompute chain hashes and confirm whether the local ledger remains intact.",
        fields: [],
      },
    ],
  },
  {
    id: "multilingual-risk",
    title: "Multilingual Contract Risk Analyzer",
    category: "Legal AI",
    description: "Detect clauses and risk scores across 22 Indic and 40+ global languages natively.",
    status: "beta",
    actions: [
      {
        id: "analyze",
        label: "Analyze Contract",
        submitLabel: "Analyze Contract Risk",
        description: "Review clause text for risk-heavy terms such as indemnity, exclusivity, auto-renewals, and data transfer gaps.",
        fields: [
          { name: "contractText", label: "Contract Text", type: "textarea", placeholder: "The agreement auto-renews yearly and grants exclusive reseller rights...", required: true },
          { name: "jurisdiction", label: "Jurisdiction", type: "select", options: ["India", "EU", "US", "Singapore", "Mixed"], defaultValue: "India" },
          { name: "contractLanguage", label: "Language", type: "select", options: ["English", "Hindi", "Tamil", "Bilingual", "Other"], defaultValue: "English" },
        ],
      },
    ],
  },
  {
    id: "smart-einvoice",
    title: "Smart e-Invoice Validator",
    category: "Tax Automation",
    description: "Automated pre-validation against Indian NIC and global tax authority endpoints.",
    status: "beta",
    actions: [
      {
        id: "validate",
        label: "Validate e-Invoice",
        submitLabel: "Validate e-Invoice",
        description: "Check tax IDs, totals, dates, and required fields before submission.",
        fields: [
          { name: "invoiceSource", label: "Invoice Source", type: "select", options: ["India GST", "EU VAT", "Global B2B"], defaultValue: "India GST" },
          { name: "invoicePayload", label: "Invoice JSON / Text", type: "textarea", placeholder: "{\"invoiceNumber\":\"INV-1001\",\"sellerGstin\":\"27ABCDE1234F1Z5\",\"total\":48500}", required: false },
          { name: "invoiceAttachment", label: "Invoice Attachment", type: "file", accept: ".txt,.json,.csv,.pdf,.png,.jpg,.jpeg,.webp", required: false },
        ],
      },
    ],
  },
  {
    id: "vendor-scorer",
    title: "Vendor Performance Scorer",
    category: "Procurement",
    description: "Continuously update vendor health metrics based on historic SLAs.",
    status: "beta",
    actions: [
      {
        id: "score",
        label: "Score Vendor",
        submitLabel: "Score Vendor",
        description: "Blend delivery, quality, support, and spend signals into a vendor health grade.",
        fields: [
          { name: "vendorName", label: "Vendor Name", type: "text", placeholder: "Orbit Logistics", required: true },
          { name: "onTimeRate", label: "On-Time Delivery %", type: "number", placeholder: "92" },
          { name: "defectRate", label: "Defect / Error %", type: "number", placeholder: "3" },
          { name: "ticketReopenRate", label: "Ticket Reopen %", type: "number", placeholder: "8" },
          { name: "quarterlySpend", label: "Quarterly Spend", type: "number", placeholder: "2500000" },
        ],
      },
    ],
  },
  {
    id: "self-healing",
    title: "Self-Healing Execution Engine",
    category: "Reliability",
    description: "Automatically retry and re-route failed external API calls.",
    status: "beta",
    actions: [
      {
        id: "simulate",
        label: "Generate Recovery Plan",
        submitLabel: "Generate Recovery Plan",
        description: "Create a retry, failover, and circuit-breaker plan for a failing service call.",
        fields: [
          { name: "serviceName", label: "Service Name", type: "text", placeholder: "payments-adapter", required: true },
          { name: "endpointUrl", label: "Endpoint URL", type: "text", placeholder: "https://api.partner.com/charge", required: true },
          { name: "failureRegion", label: "Failure Region", type: "select", options: ["ap-south-1", "eu-west-1", "us-east-1"], defaultValue: "ap-south-1" },
          { name: "httpStatus", label: "HTTP Status", type: "select", options: ["429", "500", "502", "503", "504"], defaultValue: "503" },
          { name: "criticality", label: "Criticality", type: "select", options: ["Low", "Medium", "High", "Critical"], defaultValue: "High" },
          { name: "retryCount", label: "Retries Already Attempted", type: "number", placeholder: "2" },
        ],
      },
    ],
  },
  {
    id: "multi-agent-ondc",
    title: "Multi-Agent ONDC Router",
    category: "Network Orchestration",
    description: "Dynamically negotiate and route requests across the Open Network for Digital Commerce (ONDC).",
    status: "beta",
    actions: [
      {
        id: "route",
        label: "Route Order",
        submitLabel: "Route Order",
        description: "Pick the best fulfillment lane based on city, category, value, urgency, and seller reach.",
        fields: [
          { name: "buyerCity", label: "Buyer City", type: "text", placeholder: "Mumbai", required: true },
          { name: "productCategory", label: "Product Category", type: "select", options: ["Electronics", "Fashion", "Groceries", "B2B supplies"], defaultValue: "B2B supplies" },
          { name: "orderValue", label: "Order Value", type: "number", placeholder: "18000" },
          { name: "deliveryWindow", label: "Delivery Window", type: "select", options: ["Same day", "Next day", "2-3 days", "Flexible"], defaultValue: "Next day" },
          { name: "sellerRegions", label: "Seller Regions", type: "textarea", placeholder: "Mumbai, Pune, Bengaluru, Delhi NCR", required: true },
        ],
      },
    ],
  },
  {
    id: "supply-chain-twin",
    title: "Supply Chain Digital Twin",
    category: "Simulation",
    description: "Live simulation of logistics bottlenecks, port congestions, and ETA adjustments.",
    status: "beta",
    actions: [
      {
        id: "simulate",
        label: "Simulate Network",
        submitLabel: "Simulate Network",
        description: "Evaluate route pressure, delay propagation, and adjusted ETAs from a network snapshot.",
        fields: [
          { name: "networkSnapshot", label: "Network Snapshot", type: "textarea", placeholder: "Lane: Nhava Sheva -> Bengaluru\nDelay: 14 hours\nInventory cover: 5 days\nPort congestion: High", required: true },
          { name: "priorityLane", label: "Priority Lane", type: "text", placeholder: "Mumbai -> Bengaluru" },
          { name: "inventoryDaysCover", label: "Inventory Days Cover", type: "number", placeholder: "5" },
        ],
      },
    ],
  },
  {
    id: "conv-bi",
    title: "Conversational BI Dashboard",
    category: "Analytics",
    description: "Talk to your data warehouse in plain English or Hindi to generate visuals.",
    status: "beta",
    actions: [
      {
        id: "query",
        label: "Ask Your Data",
        submitLabel: "Ask Your Data",
        description: "Provide a business question plus CSV/JSON data to generate an answer and lightweight chart hints.",
        fields: [
          { name: "businessQuestion", label: "Business Question", type: "text", placeholder: "Which region had the highest revenue growth?", required: true },
          { name: "datasetText", label: "Dataset", type: "textarea", placeholder: "region,revenue_prev,revenue_curr\nWest,120,160\nNorth,100,130", required: false },
          { name: "datasetFile", label: "Dataset File", type: "file", accept: ".csv,.json,.txt,.md", required: false },
        ],
      },
    ],
  },
  {
    id: "rfq-generator",
    title: "Automated RFQ Generator",
    category: "Procurement",
    description: "Draft comprehensive RFQs from basic requirement notes.",
    status: "beta",
    actions: [
      {
        id: "generate",
        label: "Generate RFQ",
        submitLabel: "Generate RFQ",
        description: "Convert requirement notes into scope, deliverables, evaluation criteria, and vendor questions.",
        fields: [
          { name: "requirementNotes", label: "Requirement Notes", type: "textarea", placeholder: "Need a multilingual contact center analytics platform for APAC support teams...", required: true },
          { name: "budgetBand", label: "Budget Band", type: "select", options: ["< 10L INR", "10L-50L INR", "50L-2Cr INR", "> 2Cr INR"], defaultValue: "10L-50L INR" },
          { name: "timelineWeeks", label: "Timeline (weeks)", type: "number", placeholder: "12" },
          { name: "mandatoryCapabilities", label: "Mandatory Capabilities", type: "textarea", placeholder: "SOC2, SSO, Hindi + English support, audit logging", required: false },
        ],
      },
    ],
  },
  {
    id: "compliance-scanner",
    title: "Regulatory Compliance Scanner",
    category: "Governance",
    description: "Real-time scanning of codebase against RBI, SEBI, and Global infosec policies.",
    status: "beta",
    actions: [
      {
        id: "scan",
        label: "Scan Artifact",
        submitLabel: "Scan Artifact",
        description: "Inspect pasted policy, config, or code text against a selected compliance lens.",
        fields: [
          { name: "policyFramework", label: "Framework", type: "select", options: ["RBI", "SEBI", "DPDP", "GDPR", "ISO 27001"], defaultValue: "RBI" },
          { name: "artifactType", label: "Artifact Type", type: "select", options: ["Policy", "Configuration", "Source code", "Process note"], defaultValue: "Policy" },
          { name: "artifactText", label: "Artifact Text", type: "textarea", placeholder: "Access logs are retained for 14 days and encryption is handled by the cloud provider...", required: false },
          { name: "artifactFile", label: "Artifact File", type: "file", accept: ".txt,.md,.json,.csv,.pdf", required: false },
        ],
      },
    ],
  },
  {
    id: "dynamic-pricing",
    title: "Dynamic Pricing Optimizer",
    category: "Revenue",
    description: "Adjust pricing tiers dynamically based on load and competitor APIs.",
    status: "beta",
    actions: [
      {
        id: "optimize",
        label: "Optimize Price",
        submitLabel: "Optimize Price",
        description: "Recommend a price based on demand, competition, inventory pressure, and conversion performance.",
        fields: [
          { name: "basePrice", label: "Current Price", type: "number", placeholder: "999" },
          { name: "competitorPrice", label: "Competitor Price", type: "number", placeholder: "949" },
          { name: "inventoryDays", label: "Inventory Days Remaining", type: "number", placeholder: "18" },
          { name: "demandLoad", label: "Demand Load %", type: "number", placeholder: "78" },
          { name: "conversionRate", label: "Conversion Rate %", type: "number", placeholder: "3.8" },
        ],
      },
    ],
  },
  {
    id: "employee-sentiment",
    title: "Employee Sentiment Pulse",
    category: "People Analytics",
    description: "Passive, privacy-preserving aggregation of team morale metrics.",
    status: "beta",
    actions: [
      {
        id: "pulse",
        label: "Measure Pulse",
        submitLabel: "Measure Pulse",
        description: "Aggregate anonymized team feedback into morale, burnout risk, and action themes.",
        fields: [
          { name: "teamName", label: "Team", type: "text", placeholder: "APAC Support", required: true },
          { name: "feedbackBatch", label: "Feedback Batch", type: "textarea", placeholder: "Workload has increased but leadership is responsive...\nNeed clearer weekend handoff ownership...", required: true },
          { name: "sampleSize", label: "Sample Size", type: "number", placeholder: "14" },
        ],
      },
    ],
  },
];

export const featureMap = Object.fromEntries(featureCatalog.map((feature) => [feature.id, feature]));

export const liveTools = featureCatalog.filter((feature) => feature.status === "live");

export const previewFeatures = featureCatalog.filter((feature) => feature.status === "beta");
