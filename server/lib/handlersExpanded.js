import {
  assertText,
  buildResult,
  chooseColumn,
  clamp,
  compactText,
  complianceChecklist,
  contractRiskCatalog,
  createJsonSection,
  createKeyValueSection,
  createListSection,
  createTableSection,
  createTextSection,
  currency,
  detectUrgency,
  excerpt,
  extractIdentifiers,
  extractTextFromFiles,
  inferDimensionColumns,
  inferNumericColumns,
  keywordHits,
  negativeTerms,
  normalizeWhitespace,
  numericValue,
  parseInvoiceFields,
  parseStructuredRecords,
  percentage,
  positiveTerms,
  sentimentBreakdown,
  toNumber,
  topTerms,
} from "./analysis.js";
import { handleEInvoiceInputText } from "./handlersStateful.js";

export async function handleContractRisk(actionInput) {
  const text = normalizeWhitespace(actionInput.contractText);
  assertText(text, "Paste contract text to analyze risk.");

  const hits = contractRiskCatalog
    .map((risk) => ({
      ...risk,
      matched: risk.keywords.some((keyword) => compactText(text).toLowerCase().includes(keyword)),
    }))
    .filter((risk) => risk.matched);
  const score = clamp(hits.reduce((total, risk) => total + risk.score, 10), 0, 100);
  const band = score >= 75 ? "High" : score >= 45 ? "Moderate" : "Low";

  return buildResult({
    headline: `${band} contract risk detected.`,
    summary: `Clause scanning across the submitted ${actionInput.contractLanguage || "contract"} found ${hits.length} material risk markers for ${actionInput.jurisdiction || "the selected"} jurisdiction.`,
    metrics: [
      { label: "Risk score", value: `${score}/100` },
      { label: "Risk band", value: band },
      { label: "Jurisdiction", value: actionInput.jurisdiction || "Not specified" },
      { label: "Flagged clauses", value: String(hits.length) },
    ],
    highlights: hits.length ? hits.map((risk) => risk.label) : ["No major high-risk clause keywords were detected."],
    sections: [
      createListSection(
        "Flagged Clauses",
        hits.length ? hits.map((risk) => `${risk.label}: keywords ${risk.keywords.join(", ")}`) : ["No clause cluster crossed the current heuristic threshold."]
      ),
      createListSection("Recommended Legal Review", [
        "Confirm indemnity scope and liability caps.",
        "Review renewal and termination language for unilateral lock-in.",
        "Validate data transfer clauses against the operating jurisdiction.",
      ]),
      createTextSection("Contract Summary", excerpt(text, 420)),
    ],
  });
}

export async function handleEInvoice(actionInput, files) {
  const { text, extracted, parsed, identifiers } = await handleEInvoiceInputText(actionInput, files);
  const fields = parsed && typeof parsed === "object" ? parsed : parseInvoiceFields(text);
  const source = actionInput.invoiceSource || "India GST";
  const issues = [];

  if (!fields.invoiceNumber && fields.invoiceNumber !== "") {
    issues.push("Invoice number missing.");
  }
  if (source === "India GST" && identifiers.gstin.length === 0) {
    issues.push("Seller or buyer GSTIN was not detected.");
  }
  if (source === "EU VAT" && identifiers.vat.length === 0) {
    issues.push("VAT registration ID was not detected.");
  }

  const totalValue = numericValue(fields.total || fields.invoiceTotal || parsed?.total);
  if (totalValue === null) {
    issues.push("Invoice total is missing or not numeric.");
  }

  return buildResult({
    headline: issues.length ? `Validation completed with ${issues.length} issue(s).` : "Invoice payload passed the heuristic validation checks.",
    summary: `The ${source} pre-validator checked identifiers, totals, and core mandatory invoice markers before submission.`,
    metrics: [
      { label: "Source", value: source },
      { label: "Issues", value: String(issues.length) },
      { label: "GSTIN count", value: String(identifiers.gstin.length) },
      { label: "VAT count", value: String(identifiers.vat.length) },
    ],
    highlights: issues.length ? issues : ["No blocking issue detected in the current heuristic pass."],
    sections: [
      createJsonSection("Parsed Invoice Payload", parsed || fields),
    ],
    notes: extracted.notes,
  });
}

export async function handleVendorScore(actionInput) {
  const onTimeRate = clamp(toNumber(actionInput.onTimeRate, 0), 0, 100);
  const defectRate = clamp(toNumber(actionInput.defectRate, 0), 0, 100);
  const reopenRate = clamp(toNumber(actionInput.ticketReopenRate, 0), 0, 100);
  const spend = toNumber(actionInput.quarterlySpend, 0);
  const score = clamp(onTimeRate * 0.5 + (100 - defectRate) * 0.25 + (100 - reopenRate) * 0.15 + Math.min(spend / 100000, 10), 0, 100);
  const band = score >= 85 ? "Strategic" : score >= 70 ? "Preferred" : score >= 55 ? "Watchlist" : "At risk";

  return buildResult({
    headline: `${actionInput.vendorName} is rated ${band.toLowerCase()}.`,
    summary: `The vendor health score blends delivery reliability, quality leakage, support churn, and commercial scale into a ${Math.round(score)}/100 view.`,
    metrics: [
      { label: "Vendor score", value: `${Math.round(score)}/100` },
      { label: "Band", value: band },
      { label: "On-time rate", value: percentage(onTimeRate, 0) },
      { label: "Quarterly spend", value: currency(spend || 0) },
    ],
    highlights: [
      defectRate > 5 ? "Quality leakage is pulling down the vendor score." : "Quality performance is currently healthy.",
      reopenRate > 10 ? "Support reopens suggest post-delivery instability." : "Support performance looks stable.",
      band === "At risk" ? "Build a corrective action plan before renewal." : "Vendor can stay in the active pool with periodic monitoring.",
    ],
    sections: [
      createKeyValueSection("Input Metrics", {
        "On-time delivery": percentage(onTimeRate, 0),
        "Defect rate": percentage(defectRate, 0),
        "Ticket reopen rate": percentage(reopenRate, 0),
        "Quarterly spend": currency(spend || 0),
      }),
    ],
  });
}

export async function handleSelfHealing(actionInput) {
  const httpStatus = Number(actionInput.httpStatus || 503);
  const retryCount = toNumber(actionInput.retryCount, 0);
  const criticality = actionInput.criticality || "High";
  const backoff = [5, 20, 60].map((seconds) => `${seconds + retryCount * 5}s`);
  const reroute = actionInput.failureRegion === "ap-south-1" ? "eu-west-1" : "ap-south-1";
  const probability = clamp(88 - retryCount * 12 - (criticality === "Critical" ? 8 : 0) - (httpStatus >= 500 ? 6 : 0), 18, 92);

  return buildResult({
    headline: `Recovery plan generated for ${actionInput.serviceName}.`,
    summary: `The self-healing planner recommends staged retries plus regional failover from ${actionInput.failureRegion} based on the ${httpStatus} failure class.`,
    metrics: [
      { label: "HTTP status", value: String(httpStatus) },
      { label: "Criticality", value: criticality },
      { label: "Failover region", value: reroute },
      { label: "Recovery probability", value: percentage(probability, 0) },
    ],
    highlights: [
      `Retry schedule: ${backoff.join(" -> ")}`,
      `Open circuit after retry ${retryCount + 3} if failures persist.`,
      httpStatus === 429 ? "Throttle-sensitive failure detected; widen the backoff window." : "Server-side failure detected; shift traffic to the healthiest region.",
    ],
    sections: [
      createListSection("Execution Plan", [
        `Attempt retries with exponential backoff: ${backoff.join(", ")}`,
        `Reroute non-sticky traffic to ${reroute}`,
        "Emit a recovery event and capture the final outcome in audit logs.",
      ]),
      createKeyValueSection("Failure Context", {
        Service: actionInput.serviceName,
        Endpoint: actionInput.endpointUrl,
        Region: actionInput.failureRegion,
        Retries: retryCount,
      }),
    ],
  });
}

export async function handleOndc(actionInput) {
  const regions = normalizeWhitespace(actionInput.sellerRegions.replace(/,/g, "\n"))
    .split(/\n+/)
    .filter(Boolean);
  const buyerCity = compactText(actionInput.buyerCity);
  const deliveryWindow = actionInput.deliveryWindow || "Next day";
  const ranked = regions
    .map((region, index) => ({
      region,
      score: 90 - index * 8 + (region.toLowerCase().includes(buyerCity.toLowerCase()) ? 12 : 0) + (deliveryWindow === "Same day" ? 3 : 0),
    }))
    .sort((left, right) => right.score - left.score);
  const winner = ranked[0];

  return buildResult({
    headline: `Best ONDC route selected via ${winner?.region || "no seller region"}.`,
    summary: `Routing favored seller reach, buyer-city affinity, and the requested ${deliveryWindow.toLowerCase()} delivery window for a ${actionInput.productCategory.toLowerCase()} order.`,
    metrics: [
      { label: "Buyer city", value: actionInput.buyerCity },
      { label: "Order value", value: currency(toNumber(actionInput.orderValue, 0)) },
      { label: "Delivery window", value: deliveryWindow },
      { label: "Ranked sellers", value: String(ranked.length) },
    ],
    highlights: winner ? [`Top route score: ${winner.score}`, `Winning region: ${winner.region}`, "Use a negotiation agent to confirm inventory before final commitment."] : ["Add seller regions to compute a route."],
    sections: [
      createTableSection(
        "Route Ranking",
        ranked.map((record) => ({
          region: record.region,
          score: record.score,
        }))
      ),
      createListSection("Negotiation Flow", [
        "Check catalog availability and promised SLA for the top-ranked node.",
        "Verify delivery promise against buyer city and product category.",
        "Fallback to the next-ranked seller if inventory or SLA fails validation.",
      ]),
    ],
  });
}

export async function handleSupplyChain(actionInput) {
  const snapshot = normalizeWhitespace(actionInput.networkSnapshot);
  assertText(snapshot, "Add a network snapshot to simulate the supply chain.");

  const delayHours = toNumber(snapshot.match(/\b(\d+)\s*hours?\b/i)?.[1], 0);
  const coverDays = toNumber(actionInput.inventoryDaysCover || snapshot.match(/\b(\d+)\s*days?\b/i)?.[1], 0);
  const congestion = /high/i.test(snapshot) ? "High" : /medium/i.test(snapshot) ? "Medium" : "Low";
  const etaImpact = delayHours + (congestion === "High" ? 12 : congestion === "Medium" ? 6 : 2);
  const risk = etaImpact >= 24 || coverDays <= 3 ? "High" : etaImpact >= 12 || coverDays <= 6 ? "Moderate" : "Low";

  return buildResult({
    headline: `${risk} network disruption risk on ${actionInput.priorityLane || "the submitted lane"}.`,
    summary: `The digital twin estimated a ${etaImpact}-hour ETA impact with ${coverDays} days of inventory cover and ${congestion.toLowerCase()} congestion.`,
    metrics: [
      { label: "Delay hours", value: String(delayHours) },
      { label: "Congestion", value: congestion },
      { label: "Inventory cover", value: `${coverDays} days` },
      { label: "ETA impact", value: `${etaImpact} hours` },
    ],
    highlights: [
      risk === "High" ? "Low days of cover mean this disruption could turn into a stockout." : "Inventory cover still provides some recovery room.",
      actionInput.priorityLane ? `Priority lane: ${actionInput.priorityLane}` : "No priority lane specified.",
      "Use the simulation to resequence shipments before delays compound across nodes.",
    ],
    sections: [
      createListSection("Recommended Interventions", [
        "Pull forward shipments for the highest-demand SKUs.",
        congestion === "High" ? "Reroute away from the congested port or carrier if possible." : "Keep current lane but monitor next milestone closely.",
        "Increase communication cadence with downstream fulfillment teams.",
      ]),
      createTextSection("Snapshot Summary", excerpt(snapshot, 400)),
    ],
  });
}

export async function handleConversationalBi(actionInput, files) {
  const extracted = await extractTextFromFiles(files);
  const datasetText = normalizeWhitespace([actionInput.datasetText, extracted.text].filter(Boolean).join("\n\n"));
  assertText(datasetText, "Paste dataset rows or upload a CSV/JSON file.");

  const records = parseStructuredRecords(datasetText);
  if (!records.length) {
    throw new Error("No structured rows could be parsed from the dataset.");
  }

  const numericColumns = inferNumericColumns(records);
  const dimensionColumns = inferDimensionColumns(records);
  const question = actionInput.businessQuestion || "Summarize this dataset";
  const targetMetric = chooseColumn(question, numericColumns);
  const targetDimension = chooseColumn(question, dimensionColumns);
  const sorted = targetMetric
    ? [...records].sort((left, right) => (numericValue(right[targetMetric]) || 0) - (numericValue(left[targetMetric]) || 0))
    : records;
  const winner = sorted[0];

  let answer = "The dataset has been parsed successfully.";
  if (winner && targetMetric && targetDimension) {
    answer = `${winner[targetDimension]} leads on ${targetMetric} with ${winner[targetMetric]}.`;
  } else if (winner && targetMetric) {
    answer = `The highest ${targetMetric} value in the dataset is ${winner[targetMetric]}.`;
  }

  return buildResult({
    headline: "Conversational BI answer generated.",
    summary: answer,
    metrics: [
      { label: "Rows parsed", value: String(records.length) },
      { label: "Numeric fields", value: String(numericColumns.length) },
      { label: "Dimensions", value: String(dimensionColumns.length) },
      { label: "Primary metric", value: targetMetric || "Not inferred" },
    ],
    highlights: [
      `Question: ${question}`,
      targetDimension ? `Best grouping column: ${targetDimension}` : "No grouping column confidently inferred.",
      targetMetric ? `Suggested chart metric: ${targetMetric}` : "Add clearer numeric columns for richer analytics.",
    ],
    sections: [
      createTableSection("Top Rows", sorted.slice(0, 5)),
      createKeyValueSection("Chart Hint", {
        "Recommended chart": targetDimension && targetMetric ? "Bar chart" : "Table",
        Dimension: targetDimension || "First text column",
        Metric: targetMetric || "First numeric column",
      }),
    ],
    notes: extracted.notes,
  });
}

export async function handleRfqGenerator(actionInput) {
  const notes = normalizeWhitespace(actionInput.requirementNotes);
  assertText(notes, "Add requirement notes to generate an RFQ.");

  const capabilities = normalizeWhitespace((actionInput.mandatoryCapabilities || "").replace(/,/g, "\n"))
    .split(/\n+/)
    .filter(Boolean);
  const themes = topTerms(notes, 8);

  return buildResult({
    headline: "RFQ draft generated from requirement notes.",
    summary: `The RFQ frames scope, evaluation criteria, and delivery expectations for a ${actionInput.budgetBand} procurement window over ${toNumber(actionInput.timelineWeeks, 0) || "an open"}-week timeline.`,
    metrics: [
      { label: "Budget band", value: actionInput.budgetBand },
      { label: "Timeline", value: `${toNumber(actionInput.timelineWeeks, 0) || "Open"} weeks` },
      { label: "Mandatory capabilities", value: String(capabilities.length) },
      { label: "Theme count", value: String(themes.length) },
    ],
    highlights: [
      `Top themes: ${themes.join(", ") || "general scope"}`,
      capabilities[0] ? `Mandatory capability: ${capabilities[0]}` : "No explicit mandatory capability provided.",
      "Use the generated structure as a first-pass RFQ skeleton.",
    ],
    sections: [
      createListSection("Scope of Work", [
        "Provide solution architecture and implementation plan.",
        "Describe rollout milestones, staffing, and support model.",
        "Specify reporting, auditability, and operational governance.",
      ]),
      createListSection("Evaluation Criteria", [
        "Functional fit against requirement themes.",
        "Security and compliance readiness.",
        "Delivery confidence within the stated timeline and budget band.",
      ]),
      createListSection("Mandatory Capabilities", capabilities.length ? capabilities : ["No mandatory capabilities were explicitly listed."]),
      createTextSection("Requirement Summary", excerpt(notes, 420)),
    ],
  });
}

export async function handleComplianceScanner(actionInput, files) {
  const extracted = await extractTextFromFiles(files);
  const artifact = normalizeWhitespace([actionInput.artifactText, extracted.text].filter(Boolean).join("\n\n"));
  assertText(artifact, "Paste or upload an artifact to scan.");

  const framework = actionInput.policyFramework || "RBI";
  const requiredTerms = complianceChecklist[framework] || complianceChecklist.RBI;
  const missing = requiredTerms.filter((term) => !compactText(artifact).toLowerCase().includes(term.toLowerCase()));
  const present = requiredTerms.filter((term) => compactText(artifact).toLowerCase().includes(term.toLowerCase()));
  const riskBand = missing.length >= 3 ? "High" : missing.length >= 1 ? "Moderate" : "Low";

  return buildResult({
    headline: `${framework} compliance scan completed with ${riskBand.toLowerCase()} residual risk.`,
    summary: `The scanner checked the submitted ${actionInput.artifactType.toLowerCase()} against ${requiredTerms.length} heuristic ${framework} control themes.`,
    metrics: [
      { label: "Framework", value: framework },
      { label: "Present controls", value: String(present.length) },
      { label: "Missing controls", value: String(missing.length) },
      { label: "Risk band", value: riskBand },
    ],
    highlights: missing.length ? missing.map((term) => `Missing: ${term}`) : ["All tracked control themes were mentioned in the artifact."],
    sections: [
      createListSection("Controls Found", present.length ? present : ["No tracked control phrase was detected."]),
      createListSection("Controls Missing", missing.length ? missing : ["No tracked gap found in the current heuristic scan."]),
      createTextSection("Artifact Snapshot", excerpt(artifact, 420)),
    ],
    notes: extracted.notes,
  });
}

export async function handleDynamicPricing(actionInput) {
  const basePrice = toNumber(actionInput.basePrice, 0);
  const competitorPrice = toNumber(actionInput.competitorPrice, 0);
  const inventoryDays = Math.max(toNumber(actionInput.inventoryDays, 0), 1);
  const demandLoad = clamp(toNumber(actionInput.demandLoad, 0), 0, 100);
  const conversionRate = clamp(toNumber(actionInput.conversionRate, 0), 0, 100);
  const demandAdjustment = ((demandLoad - 50) / 50) * 0.08;
  const inventoryAdjustment = inventoryDays <= 10 ? 0.06 : inventoryDays >= 30 ? -0.05 : 0;
  const competitionAdjustment = basePrice && competitorPrice ? clamp((competitorPrice - basePrice) / basePrice, -0.08, 0.08) : 0;
  const conversionAdjustment = conversionRate < 3 ? -0.04 : conversionRate > 6 ? 0.03 : 0;
  const multiplier = 1 + demandAdjustment + inventoryAdjustment + competitionAdjustment + conversionAdjustment;
  const recommendedPrice = Math.max(Math.round(basePrice * multiplier), 1);
  const delta = recommendedPrice - basePrice;

  return buildResult({
    headline: `Recommended price: ${currency(recommendedPrice)}.`,
    summary: `Pricing moved by ${currency(delta)} after balancing demand pressure, competitor positioning, inventory cover, and conversion efficiency.`,
    metrics: [
      { label: "Current price", value: currency(basePrice) },
      { label: "Recommended", value: currency(recommendedPrice) },
      { label: "Demand load", value: percentage(demandLoad, 0) },
      { label: "Inventory days", value: String(inventoryDays) },
    ],
    highlights: [
      competitorPrice ? `Competitor reference: ${currency(competitorPrice)}` : "No competitor reference provided.",
      delta >= 0 ? "The engine recommends a price increase." : "The engine recommends a price decrease.",
      conversionRate < 3 ? "Low conversion is a drag on pricing power." : "Conversion supports current pricing strength.",
    ],
    sections: [
      createKeyValueSection("Adjustment Drivers", {
        "Demand adjustment": percentage(demandAdjustment * 100, 1),
        "Inventory adjustment": percentage(inventoryAdjustment * 100, 1),
        "Competition adjustment": percentage(competitionAdjustment * 100, 1),
        "Conversion adjustment": percentage(conversionAdjustment * 100, 1),
      }),
    ],
  });
}

export async function handleEmployeeSentiment(actionInput) {
  const feedback = normalizeWhitespace(actionInput.feedbackBatch);
  assertText(feedback, "Paste team feedback to measure morale.");

  const sentiment = sentimentBreakdown(feedback);
  const burnoutSignals = keywordHits(feedback, ["burnout", "overload", "weekend", "late night", "tired", "stress"]);
  const recognitionSignals = keywordHits(feedback, ["supportive", "appreciate", "recognition", "leadership", "helpful"]);
  const positiveHits = keywordHits(feedback, positiveTerms);
  const negativeHits = keywordHits(feedback, negativeTerms);
  const moraleScore = clamp(sentiment.score + recognitionSignals * 5 - burnoutSignals * 8 + positiveHits * 2 - negativeHits * 2, 0, 100);
  const moraleBand = moraleScore >= 70 ? "Healthy" : moraleScore >= 50 ? "Watch" : "At risk";

  return buildResult({
    headline: `${actionInput.teamName} morale is ${moraleBand.toLowerCase()}.`,
    summary: `An anonymized pulse across ${toNumber(actionInput.sampleSize, 0) || "the submitted"} feedback batch indicates ${moraleBand.toLowerCase()} team sentiment with ${burnoutSignals} burnout markers and ${detectUrgency(feedback).toLowerCase()} urgency.`,
    metrics: [
      { label: "Morale score", value: `${Math.round(moraleScore)}/100` },
      { label: "Baseline sentiment", value: `${Math.round(sentiment.score)}/100` },
      { label: "Burnout markers", value: String(burnoutSignals) },
      { label: "Recognition markers", value: String(recognitionSignals) },
    ],
    highlights: [
      `Primary emotion: ${sentiment.emotions[0]}`,
      burnoutSignals > 0 ? "Workload-related language appears in the feedback." : "No strong burnout vocabulary detected.",
      "Treat this as a privacy-preserving team pulse, not an individual diagnostic.",
    ],
    sections: [
      createListSection("Suggested Actions", [
        burnoutSignals > 0 ? "Review workload balancing and handoff expectations." : "Maintain the current team operating rhythm.",
        "Close the loop by communicating one concrete action back to the team.",
        "Keep qualitative listening channels open after the pulse review.",
      ]),
      createTextSection("Feedback Snapshot", excerpt(feedback, 420)),
    ],
  });
}
