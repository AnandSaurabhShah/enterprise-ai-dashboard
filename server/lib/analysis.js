import crypto from "node:crypto";
import path from "node:path";
import pdf from "pdf-parse";

const stopwords = new Set([
  "a",
  "an",
  "and",
  "are",
  "as",
  "at",
  "be",
  "been",
  "by",
  "for",
  "from",
  "has",
  "have",
  "in",
  "is",
  "it",
  "its",
  "of",
  "on",
  "or",
  "that",
  "the",
  "their",
  "there",
  "this",
  "to",
  "was",
  "we",
  "with",
  "will",
  "you",
  "your",
  "our",
  "but",
  "not",
  "they",
  "them",
  "also",
  "need",
  "please",
  "hai",
  "ki",
  "ka",
  "ke",
  "aur",
]);

export const positiveTerms = ["great", "good", "helpful", "fast", "smooth", "resolved", "love", "excellent", "clear", "happy", "supportive", "responsive"];
export const negativeTerms = ["bad", "late", "angry", "frustrated", "delay", "broken", "issue", "confusing", "poor", "slow", "blocked", "upset", "escalate", "disappointed"];
export const urgencyTerms = ["urgent", "immediately", "asap", "today", "now", "priority", "blocked", "delay", "breach", "critical", "escalation"];
export const frustrationTerms = ["frustrated", "disappointed", "angry", "upset", "annoyed", "unhappy"];
export const delightTerms = ["great", "love", "excellent", "happy", "thankful", "impressed"];
export const confusionTerms = ["confused", "unclear", "not sure", "how", "why", "uncertain"];
export const trustTerms = ["reliable", "trust", "safe", "confident", "secure"];

export const intentKeywords = {
  Support: ["help", "issue", "error", "ticket", "problem", "support", "unable", "login", "status"],
  Billing: ["invoice", "billing", "payment", "refund", "gst", "vat", "tax", "charge"],
  Sales: ["quote", "pricing", "plan", "demo", "rfq", "proposal", "purchase"],
  Logistics: ["shipment", "delivery", "port", "eta", "route", "inventory", "vendor"],
  Compliance: ["policy", "audit", "kyc", "compliance", "gdpr", "dpdp", "rbi", "sebi"],
};

export const contractRiskCatalog = [
  { label: "Indemnity Exposure", score: 22, keywords: ["indemnify", "indemnity", "hold harmless"] },
  { label: "Exclusivity Constraint", score: 16, keywords: ["exclusive", "sole supplier", "sole rights"] },
  { label: "Auto-Renewal", score: 18, keywords: ["auto-renew", "automatic renewal", "renews automatically"] },
  { label: "Unlimited Liability", score: 25, keywords: ["unlimited liability", "liability shall not be limited"] },
  { label: "Broad Data Transfer", score: 14, keywords: ["cross-border transfer", "global data transfer", "data may be shared"] },
  { label: "Weak Termination Rights", score: 12, keywords: ["termination only for cause", "non-cancellable", "cannot terminate"] },
];

export const complianceChecklist = {
  RBI: ["encryption", "access control", "incident response", "retention", "audit log"],
  SEBI: ["governance", "retention", "surveillance", "access control", "business continuity"],
  DPDP: ["consent", "purpose limitation", "retention", "breach notification", "data principal"],
  GDPR: ["lawful basis", "retention", "data subject", "breach notification", "transfer"],
  "ISO 27001": ["access control", "risk assessment", "incident response", "supplier", "backup"],
};

export function isoNow() {
  return new Date().toISOString();
}

export function normalizeWhitespace(value = "") {
  return String(value).replace(/\r/g, "\n").replace(/[ \t]+/g, " ").replace(/\n{3,}/g, "\n\n").trim();
}

export function compactText(value = "") {
  return normalizeWhitespace(value).replace(/\n/g, " ");
}

export function splitLines(value = "") {
  return normalizeWhitespace(value)
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean);
}

export function splitSentences(value = "") {
  return compactText(value)
    .split(/(?<=[.!?])\s+/)
    .map((sentence) => sentence.trim())
    .filter(Boolean);
}

export function tokenize(value = "") {
  return compactText(value)
    .toLowerCase()
    .split(/[^a-z0-9\u0900-\u097f\u0b80-\u0bff]+/u)
    .map((token) => token.trim())
    .filter((token) => token && !stopwords.has(token));
}

export function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

export function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

export function toNumber(value, fallback = 0) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
}

export function percentage(value, digits = 1) {
  return `${Number(value).toFixed(digits)}%`;
}

export function currency(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

export function excerpt(text, limit = 180) {
  const normalized = compactText(text);
  if (normalized.length <= limit) {
    return normalized;
  }

  return `${normalized.slice(0, limit).trim()}...`;
}

export function topTerms(text, limit = 6) {
  const counts = new Map();

  for (const token of tokenize(text)) {
    if (token.length < 3) {
      continue;
    }

    counts.set(token, (counts.get(token) || 0) + 1);
  }

  return [...counts.entries()]
    .sort((left, right) => right[1] - left[1])
    .slice(0, limit)
    .map(([token]) => token);
}

export function keywordHits(text, keywords) {
  const source = compactText(text).toLowerCase();
  return keywords.filter((keyword) => source.includes(keyword.toLowerCase())).length;
}

export function createHash(value) {
  return crypto.createHash("sha256").update(value).digest("hex");
}

export function detectLanguages(text) {
  const languages = [];

  if (/[a-z]/i.test(text)) {
    languages.push("English/Latin");
  }

  if (/[\u0900-\u097f]/u.test(text)) {
    languages.push("Hindi/Devanagari");
  }

  if (/[\u0b80-\u0bff]/u.test(text)) {
    languages.push("Tamil");
  }

  const lower = compactText(text).toLowerCase();
  if (!languages.includes("Hindi/Devanagari") && /\b(kya|nahi|hai|kripya|jaldi)\b/.test(lower)) {
    languages.push("Hindi (romanized)");
  }

  if (!languages.includes("Tamil") && /\b(vanakkam|ungal|illai|inga)\b/.test(lower)) {
    languages.push("Tamil (romanized)");
  }

  let mixLevel = "Single language";
  if (languages.length === 2) {
    mixLevel = "Moderate mix";
  }
  if (languages.length >= 3) {
    mixLevel = "High mix";
  }

  return {
    languages: languages.length ? languages : ["English/Latin"],
    mixLevel,
  };
}

export function detectIntent(text) {
  const source = compactText(text).toLowerCase();
  let bestIntent = "General Ops";
  let bestScore = 0;

  for (const [intent, keywords] of Object.entries(intentKeywords)) {
    const score = keywords.filter((keyword) => source.includes(keyword)).length;
    if (score > bestScore) {
      bestScore = score;
      bestIntent = intent;
    }
  }

  return bestIntent;
}

export function detectUrgency(text) {
  const hits = keywordHits(text, urgencyTerms);
  if (hits >= 3) {
    return "Critical";
  }
  if (hits === 2) {
    return "High";
  }
  if (hits === 1) {
    return "Medium";
  }
  return "Low";
}

export function extractIdentifiers(text) {
  const aadhaar = unique((text.match(/\b\d{4}\s?\d{4}\s?\d{4}\b/g) || []).map((value) => value.replace(/\s+/g, " ")));
  const pan = unique(text.match(/\b[A-Z]{5}\d{4}[A-Z]\b/g) || []);
  const gstin = unique(text.match(/\b\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]Z[A-Z0-9]\b/g) || []);
  const vat = unique(text.match(/\b(?:VAT|VATIN|TIN)\s*[:#-]?\s*[A-Z0-9-]{6,20}\b/gi) || []);
  const email = unique(text.match(/\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi) || []);
  const phone = unique(text.match(/\b(?:\+?\d{1,3}[- ]?)?\d{10}\b/g) || []);
  const invoiceNumbers = unique(text.match(/\b(?:INV|INVOICE|BILL)[-/# ]?[A-Z0-9-]{3,}\b/gi) || []);
  const ticketIds = unique(text.match(/\b(?:INC|TKT|CASE|SR)[- ]?\d{3,}\b/gi) || []);

  return {
    aadhaar,
    pan,
    gstin,
    vat,
    email,
    phone,
    invoiceNumbers,
    ticketIds,
  };
}

export function sentimentBreakdown(text) {
  const lower = compactText(text).toLowerCase();
  const positive = positiveTerms.filter((term) => lower.includes(term)).length;
  const negative = negativeTerms.filter((term) => lower.includes(term)).length;
  const rawScore = positive - negative;
  const normalizedScore = clamp(rawScore * 16 + 50, 0, 100);

  let label = "Neutral";
  if (normalizedScore >= 67) {
    label = "Positive";
  } else if (normalizedScore <= 40) {
    label = "Negative";
  }

  const emotions = [];
  if (keywordHits(lower, frustrationTerms) > 0) {
    emotions.push("Frustration");
  }
  if (keywordHits(lower, delightTerms) > 0) {
    emotions.push("Delight");
  }
  if (keywordHits(lower, confusionTerms) > 0) {
    emotions.push("Confusion");
  }
  if (keywordHits(lower, trustTerms) > 0) {
    emotions.push("Trust");
  }

  return {
    score: normalizedScore,
    label,
    emotions: emotions.length ? emotions : ["Neutral affect"],
  };
}

export function summarizeText(text, sentenceCount = 3) {
  const sentences = splitSentences(text);
  if (sentences.length <= sentenceCount) {
    return sentences.join(" ");
  }

  const keywords = topTerms(text, 8);
  const scored = sentences.map((sentence, index) => {
    const score = keywords.reduce((total, keyword) => total + (sentence.toLowerCase().includes(keyword) ? 1 : 0), 0);
    return { index, sentence, score };
  });

  return scored
    .sort((left, right) => right.score - left.score || left.index - right.index)
    .slice(0, sentenceCount)
    .sort((left, right) => left.index - right.index)
    .map((item) => item.sentence)
    .join(" ");
}

export function parseLooseJson(text) {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

export function parseStructuredRecords(rawText) {
  const text = normalizeWhitespace(rawText);
  if (!text) {
    return [];
  }

  const parsedJson = parseLooseJson(text);
  if (Array.isArray(parsedJson)) {
    return parsedJson.filter((record) => record && typeof record === "object");
  }
  if (parsedJson && typeof parsedJson === "object") {
    return [parsedJson];
  }

  const lines = splitLines(text);
  if (lines.length > 1 && lines[0].includes(",")) {
    const headers = lines[0].split(",").map((value) => value.trim());
    return lines.slice(1).map((line) => {
      const values = line.split(",").map((value) => value.trim());
      return headers.reduce((record, header, index) => {
        record[header] = values[index] ?? "";
        return record;
      }, {});
    });
  }

  return lines.map((line, index) => {
    const pipeParts = line.split("|").map((part) => part.trim()).filter(Boolean);
    if (pipeParts.length > 1) {
      return pipeParts.reduce((record, part, partIndex) => {
        const [left, right] = part.split(/:\s*/);
        if (right) {
          record[left.trim()] = right.trim();
        } else {
          record[`field_${partIndex + 1}`] = part;
        }
        return record;
      }, {});
    }

    if (line.includes(":")) {
      const [left, ...rest] = line.split(":");
      return { [left.trim()]: rest.join(":").trim() };
    }

    return { row: index + 1, value: line };
  });
}

export function numericValue(value) {
  const normalized = String(value).replace(/[^0-9.-]/g, "");
  const number = Number(normalized);
  return Number.isFinite(number) ? number : null;
}

export function inferNumericColumns(records) {
  if (!records.length) {
    return [];
  }

  const keys = Object.keys(records[0]);
  return keys.filter((key) => records.some((record) => numericValue(record[key]) !== null));
}

export function inferDimensionColumns(records) {
  if (!records.length) {
    return [];
  }

  const keys = Object.keys(records[0]);
  const numericColumns = new Set(inferNumericColumns(records));
  return keys.filter((key) => !numericColumns.has(key));
}

export function chooseColumn(question, columns) {
  const lower = question.toLowerCase();
  return columns.find((column) => lower.includes(column.toLowerCase())) || columns[0] || null;
}

export async function extractTextFromFiles(files = []) {
  if (!files.length) {
    return { text: "", notes: [] };
  }

  const extracted = [];
  const notes = [];

  for (const file of files) {
    const extension = path.extname(file.originalname || "").toLowerCase();

    try {
      if ([".txt", ".md", ".csv", ".json", ".log"].includes(extension)) {
        extracted.push(file.buffer.toString("utf8"));
        continue;
      }

      if (extension === ".pdf") {
        const parsed = await pdf(file.buffer);
        extracted.push(parsed.text || "");
        continue;
      }

      if ([".png", ".jpg", ".jpeg", ".webp"].includes(extension)) {
        const Tesseract = await import("tesseract.js");
        const result = await Tesseract.recognize(file.buffer, "eng");
        extracted.push(result.data.text || "");
        notes.push(`OCR extracted text from ${file.originalname}.`);
        continue;
      }

      if ([".mp3", ".wav", ".m4a"].includes(extension)) {
        notes.push(`Uploaded ${file.originalname}. Local mode does not transcribe audio yet, so paste a transcript for richer meeting analysis.`);
        continue;
      }

      notes.push(`Skipped unsupported file type for ${file.originalname}.`);
    } catch (error) {
      notes.push(`Could not parse ${file.originalname}: ${error.message}`);
    }
  }

  return {
    text: normalizeWhitespace(extracted.join("\n\n")),
    notes,
  };
}

export function createListSection(title, items) {
  return {
    title,
    type: "list",
    items,
  };
}

export function createKeyValueSection(title, items) {
  return {
    title,
    type: "keyValue",
    items: Array.isArray(items)
      ? items
      : Object.entries(items).map(([label, value]) => ({ label, value })),
  };
}

export function createTableSection(title, rows) {
  return {
    title,
    type: "table",
    rows,
  };
}

export function createTextSection(title, content) {
  return {
    title,
    type: "text",
    content,
  };
}

export function createJsonSection(title, content) {
  return {
    title,
    type: "json",
    content,
  };
}

export function buildResult({ headline, summary, metrics = [], highlights = [], sections = [], notes = [] }) {
  return {
    headline,
    summary,
    metrics,
    highlights,
    sections,
    notes,
    generatedAt: isoNow(),
  };
}

export function assertText(text, message) {
  if (!normalizeWhitespace(text)) {
    throw new Error(message);
  }
}

export function parseInvoiceFields(text) {
  const invoiceNumber = text.match(/\b(?:Invoice|INV|Bill)\s*(?:No\.?|#|Number)?\s*[:#-]?\s*([A-Z0-9-]{4,})\b/i)?.[1] || "Not found";
  const invoiceDate = text.match(/\b(?:Date|Invoice Date)\s*[:#-]?\s*([0-9]{1,2}[\/-][0-9]{1,2}[\/-][0-9]{2,4}|[A-Za-z]{3,9}\s+\d{1,2},\s+\d{4})\b/i)?.[1] || "Not found";
  const supplier = text.match(/\b(?:Supplier|Vendor|From)\s*[:#-]?\s*(.+)/i)?.[1]?.split("\n")[0]?.trim() || "Not found";
  const buyer = text.match(/\b(?:Buyer|Bill To|Customer)\s*[:#-]?\s*(.+)/i)?.[1]?.split("\n")[0]?.trim() || "Not found";
  const total = text.match(/\b(?:Total|Grand Total|Amount Due)\s*[:#-]?\s*(?:INR|Rs\.?|USD|EUR)?\s*([0-9,]+(?:\.\d{1,2})?)\b/i)?.[1] || "0";
  const subtotal = text.match(/\b(?:Subtotal|Taxable Amount)\s*[:#-]?\s*(?:INR|Rs\.?|USD|EUR)?\s*([0-9,]+(?:\.\d{1,2})?)\b/i)?.[1] || "0";
  const tax = text.match(/\b(?:Tax|GST|VAT|CGST|SGST|IGST)\s*[:#-]?\s*(?:INR|Rs\.?|USD|EUR)?\s*([0-9,]+(?:\.\d{1,2})?)\b/i)?.[1] || "0";

  return {
    invoiceNumber,
    invoiceDate,
    supplier,
    buyer,
    total,
    subtotal,
    tax,
  };
}

export function normalizeRecordName(value = "") {
  return compactText(value).toLowerCase().replace(/[^a-z0-9]/g, "");
}
