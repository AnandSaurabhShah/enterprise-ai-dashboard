import {
  assertText,
  buildResult,
  createKeyValueSection,
  createListSection,
  createTextSection,
  detectIntent,
  detectLanguages,
  detectUrgency,
  excerpt,
  extractIdentifiers,
  extractTextFromFiles,
  normalizeWhitespace,
  parseInvoiceFields,
  sentimentBreakdown,
  splitLines,
  summarizeText,
  toNumber,
  topTerms,
  clamp,
} from "./analysis.js";

export async function handleCodeMixed(actionInput) {
  const text = normalizeWhitespace(actionInput.inputText);
  assertText(text, "Enter text to analyze.");

  const languageSignals = detectLanguages(text);
  const identifiers = extractIdentifiers(text);
  const intent = detectIntent(text);
  const urgency = detectUrgency(text);
  const entityCount = Object.values(identifiers).reduce((total, values) => total + values.length, 0);
  const nextStep = intent === "Billing" ? "Route to finance operations or AP support." : intent === "Compliance" ? "Flag compliance review and evidence capture." : "Assign to the relevant operations queue with context preserved.";

  return buildResult({
    headline: `${intent} intent detected with ${languageSignals.mixLevel.toLowerCase()}.`,
    summary: `The message shows ${languageSignals.languages.join(", ")} signals and reads as a ${urgency.toLowerCase()}-urgency ${intent.toLowerCase()} workflow request.`,
    metrics: [
      { label: "Dominant intent", value: intent },
      { label: "Urgency", value: urgency },
      { label: "Code-mix", value: languageSignals.mixLevel },
      { label: "Entities found", value: String(entityCount) },
    ],
    highlights: [
      `Channel context: ${actionInput.channel || "Not specified"}`,
      `Region context: ${actionInput.region || "Not specified"}`,
      `Top signals: ${topTerms(text, 5).join(", ") || "not enough lexical signal"}`,
    ],
    sections: [
      createListSection(
        "Language Signals",
        languageSignals.languages.map((language) => `${language} detected in the input stream`)
      ),
      createKeyValueSection("Detected Entities", {
        Aadhaar: identifiers.aadhaar.join(", ") || "None",
        PAN: identifiers.pan.join(", ") || "None",
        GSTIN: identifiers.gstin.join(", ") || "None",
        VAT: identifiers.vat.join(", ") || "None",
        Email: identifiers.email.join(", ") || "None",
        Ticket: identifiers.ticketIds.join(", ") || "None",
      }),
      createListSection("Suggested Workflow", [
        nextStep,
        "Preserve the original phrasing for agent handoff so multilingual nuance is not lost.",
        urgency === "Critical" ? "Escalate immediately and mark as breach-sensitive." : "Queue under standard triage with extracted intent attached.",
      ]),
    ],
  });
}

export async function handleSentiment(actionInput) {
  const text = normalizeWhitespace(actionInput.feedbackText);
  assertText(text, "Enter customer feedback to score sentiment.");

  const sentiment = sentimentBreakdown(text);
  const urgency = detectUrgency(text);
  const actionBias = sentiment.label === "Negative" ? "Save the account with a high-empathy response and clear owner." : sentiment.label === "Positive" ? "Capture advocacy potential and close the loop quickly." : "Acknowledge the concern and clarify the next milestone.";

  return buildResult({
    headline: `${sentiment.label} sentiment with ${sentiment.score}/100 customer health.`,
    summary: `The feedback shows ${sentiment.emotions.join(", ").toLowerCase()} and a ${urgency.toLowerCase()} urgency signal for a ${actionInput.customerTier || "customer"} account.`,
    metrics: [
      { label: "Sentiment score", value: `${sentiment.score}/100` },
      { label: "Label", value: sentiment.label },
      { label: "Primary emotion", value: sentiment.emotions[0] },
      { label: "Target response window", value: actionInput.responseWindow || "24 hours" },
    ],
    highlights: [
      `Emotion blend: ${sentiment.emotions.join(", ")}`,
      `Urgency signal: ${urgency}`,
      actionBias,
    ],
    sections: [
      createListSection("Response Recommendations", [
        actionBias,
        "Mirror the customer's level of detail and explicitly confirm ownership.",
        sentiment.label === "Negative" ? "Offer a concrete recovery step in the first reply." : "Summarize the improvement path in one line.",
      ]),
      createTextSection("Feedback Snapshot", excerpt(text, 320)),
    ],
  });
}

export async function handleMeeting(actionInput, files) {
  const extracted = await extractTextFromFiles(files);
  const text = normalizeWhitespace([actionInput.transcriptText, extracted.text].filter(Boolean).join("\n\n"));
  const sourceLines = splitLines(text);
  const participants = [...new Set(
    sourceLines
      .map((line) => line.match(/^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*:/)?.[1])
      .filter(Boolean)
  )];
  const actionItems = [...new Set(
    sourceLines.filter((line) => /(?:action|todo|follow up|will|need to|by friday|by monday|next step)/i.test(line)).slice(0, 6)
  )];
  const decisions = [...new Set(sourceLines.filter((line) => /(?:decided|agreed|approved|confirmed)/i.test(line)).slice(0, 4))];
  const blockers = [...new Set(sourceLines.filter((line) => /(?:blocked|risk|delay|issue|dependency)/i.test(line)).slice(0, 4))];

  const fallbackSummary = actionInput.meetingGoal
    ? `Meeting assets were uploaded for ${actionInput.meetingGoal}, but a transcript was not available for full extraction.`
    : "Meeting assets were uploaded, but a transcript was not available for full extraction.";

  return buildResult({
    headline: text ? `Meeting summary generated for ${actionInput.meetingGoal || "uploaded session"}.` : "Meeting assets received.",
    summary: text ? summarizeText(text, 3) : fallbackSummary,
    metrics: [
      { label: "Participants", value: String(participants.length || files.length || 0) },
      { label: "Action items", value: String(actionItems.length) },
      { label: "Decisions", value: String(decisions.length) },
      { label: "Blockers", value: String(blockers.length) },
    ],
    highlights: [
      actionItems[0] || "No explicit action owners found in the transcript.",
      decisions[0] || "No hard decision phrase found.",
      blockers[0] || "No blocker language detected.",
    ],
    sections: [
      createListSection("Participants", participants.length ? participants : ["No explicit speaker labels detected"]),
      createListSection("Action Items", actionItems.length ? actionItems : ["Add clearer owner phrases like 'Asha will...' to improve action extraction."]),
      createListSection("Decisions", decisions.length ? decisions : ["No explicit decisions detected"]),
      createListSection("Risks & Blockers", blockers.length ? blockers : ["No blocker language detected"]),
    ],
    notes: extracted.notes,
  });
}

export async function handleInvoice(actionInput, files) {
  const extracted = await extractTextFromFiles(files);
  const text = normalizeWhitespace([actionInput.invoiceText, extracted.text].filter(Boolean).join("\n\n"));
  assertText(text, "Upload an invoice file or paste raw invoice text.");

  const fields = parseInvoiceFields(text);
  const identifiers = extractIdentifiers(text);
  const totals = {
    subtotal: toNumber(fields.subtotal.replace(/,/g, ""), 0),
    tax: toNumber(fields.tax.replace(/,/g, ""), 0),
    total: toNumber(fields.total.replace(/,/g, ""), 0),
  };
  const arithmeticCheck = Math.abs(totals.subtotal + totals.tax - totals.total) <= 2;
  const flags = [];

  if (!identifiers.gstin.length && !identifiers.vat.length) {
    flags.push("No GSTIN or VAT ID detected.");
  }
  if (fields.invoiceDate === "Not found") {
    flags.push("Invoice date is missing.");
  }
  if (!arithmeticCheck) {
    flags.push("Subtotal + tax does not closely match the total.");
  }

  return buildResult({
    headline: `Invoice ${fields.invoiceNumber} parsed for ${fields.supplier}.`,
    summary: `The parser extracted supplier, totals, and tax identifiers from the submitted invoice under the ${actionInput.invoiceContext || "default"} workflow.`,
    metrics: [
      { label: "Total", value: fields.total === "0" ? "Not found" : fields.total },
      { label: "Tax amount", value: fields.tax === "0" ? "Not found" : fields.tax },
      { label: "Tax IDs", value: String(identifiers.gstin.length + identifiers.vat.length) },
      { label: "Arithmetic check", value: arithmeticCheck ? "Passed" : "Needs review" },
    ],
    highlights: [
      fields.buyer !== "Not found" ? `Buyer detected: ${fields.buyer}` : "Buyer name was not confidently extracted.",
      identifiers.gstin[0] || identifiers.vat[0] || "No tax registration ID detected.",
      flags[0] || "Core invoice fields look internally consistent.",
    ],
    sections: [
      createKeyValueSection("Extracted Fields", {
        "Invoice number": fields.invoiceNumber,
        "Invoice date": fields.invoiceDate,
        Supplier: fields.supplier,
        Buyer: fields.buyer,
        Subtotal: fields.subtotal,
        Tax: fields.tax,
        Total: fields.total,
      }),
      createListSection("Validation Flags", flags.length ? flags : ["No major structural issues found."]),
      createTextSection("Parsed Invoice Snapshot", excerpt(text, 420)),
    ],
    notes: extracted.notes,
  });
}

export async function handleKyc(actionInput) {
  const text = normalizeWhitespace(actionInput.rawIdentityText);
  assertText(text, "Paste KYC text to extract entities.");

  const identifiers = extractIdentifiers(text);
  const nameMatch = text.match(/\b(?:Name|Applicant|Customer)\s*[:#-]?\s*([A-Z][A-Za-z ]{2,})/i)?.[1] || "Not found";
  const country = actionInput.documentRegion || "Global mixed";
  const riskFlags = [];

  if (identifiers.aadhaar.length > 1) {
    riskFlags.push("Multiple Aadhaar-like numbers detected in one payload.");
  }
  if (identifiers.pan.length === 0 && country === "India") {
    riskFlags.push("Expected PAN missing for India-focused KYC.");
  }
  if (!identifiers.email.length && !identifiers.phone.length) {
    riskFlags.push("No direct contact detail detected.");
  }

  return buildResult({
    headline: `KYC extraction completed for ${nameMatch}.`,
    summary: `The payload was normalized for ${country} review and contains ${identifiers.aadhaar.length + identifiers.pan.length + identifiers.gstin.length + identifiers.vat.length} structured identity markers.`,
    metrics: [
      { label: "Name", value: nameMatch },
      { label: "Aadhaar IDs", value: String(identifiers.aadhaar.length) },
      { label: "PAN IDs", value: String(identifiers.pan.length) },
      { label: "Risk flags", value: String(riskFlags.length) },
    ],
    highlights: [
      identifiers.pan[0] || "No PAN detected",
      identifiers.aadhaar[0] || "No Aadhaar detected",
      riskFlags[0] || "No immediate formatting risk detected.",
    ],
    sections: [
      createKeyValueSection("Normalized Entities", {
        Name: nameMatch,
        Aadhaar: identifiers.aadhaar.join(", ") || "None",
        PAN: identifiers.pan.join(", ") || "None",
        GSTIN: identifiers.gstin.join(", ") || "None",
        VAT: identifiers.vat.join(", ") || "None",
        Email: identifiers.email.join(", ") || "None",
        Phone: identifiers.phone.join(", ") || "None",
      }),
      createListSection("Risk Flags", riskFlags.length ? riskFlags : ["No obvious format or completeness issues detected."]),
    ],
  });
}

export async function handleSla(actionInput) {
  const priorityWeight = { Low: 8, Medium: 18, High: 28, Critical: 38 }[actionInput.priority] || 18;
  const complexityWeight = { Simple: 6, Moderate: 14, Complex: 22 }[actionInput.complexity] || 14;
  const tierWeight = { Standard: 4, Premium: 10, Enterprise: 16 }[actionInput.customerTier] || 10;
  const backlogWeight = clamp(toNumber(actionInput.backlogCount, 0) * 0.9, 0, 20);
  const firstResponseWeight = clamp(toNumber(actionInput.firstResponseMinutes, 0) / 6, 0, 18);
  const totalScore = clamp(priorityWeight + complexityWeight + tierWeight + backlogWeight + firstResponseWeight, 0, 100);

  let riskBand = "Low";
  if (totalScore >= 75) {
    riskBand = "Critical";
  } else if (totalScore >= 55) {
    riskBand = "High";
  } else if (totalScore >= 35) {
    riskBand = "Moderate";
  }

  return buildResult({
    headline: `${riskBand} SLA breach risk predicted.`,
    summary: `Priority, complexity, queue pressure, and response delay combine into a ${totalScore}/100 breach score for the ${actionInput.category || "support"} queue.`,
    metrics: [
      { label: "Risk band", value: riskBand },
      { label: "Risk score", value: `${Math.round(totalScore)}/100` },
      { label: "First response", value: `${toNumber(actionInput.firstResponseMinutes, 0)} min` },
      { label: "Backlog", value: String(toNumber(actionInput.backlogCount, 0)) },
    ],
    highlights: [
      priorityWeight >= 28 ? "Ticket priority is materially increasing the breach probability." : "Priority is not the main risk driver.",
      backlogWeight >= 12 ? "Queue pressure is likely to be a breach amplifier." : "Queue pressure looks manageable.",
      riskBand === "Critical" ? "Escalate to a swarming queue or add experienced ownership immediately." : "Standard mitigation should still recover the SLA.",
    ],
    sections: [
      createKeyValueSection("Scoring Inputs", {
        Priority: actionInput.priority,
        Category: actionInput.category,
        Tier: actionInput.customerTier,
        Complexity: actionInput.complexity,
        "First response delay": `${toNumber(actionInput.firstResponseMinutes, 0)} minutes`,
        "Open backlog": toNumber(actionInput.backlogCount, 0),
      }),
      createListSection("Mitigation Plan", [
        riskBand === "Critical" ? "Reassign to the fastest available resolver pool." : "Confirm the next customer-facing update time.",
        "Reduce handoffs and assign a single accountable owner.",
        "Create an early-warning alert if the first response is already beyond policy thresholds.",
      ]),
    ],
  });
}
