import crypto from "node:crypto";

import {
  assertText,
  buildResult,
  createKeyValueSection,
  createListSection,
  createTableSection,
  createTextSection,
  createHash,
  excerpt,
  extractIdentifiers,
  extractTextFromFiles,
  isoNow,
  normalizeRecordName,
  normalizeWhitespace,
  parseLooseJson,
  toNumber,
  tokenize,
  topTerms,
  unique,
} from "./analysis.js";
import { readStore, writeStore } from "./storage.js";

async function readMemoryDocuments() {
  return readStore("rag-memory", []);
}

async function writeMemoryDocuments(value) {
  return writeStore("rag-memory", value);
}

async function readAuditEntries() {
  return readStore("audit-log", []);
}

async function writeAuditEntries(value) {
  return writeStore("audit-log", value);
}

export async function handleRagAdd(actionInput, files) {
  const extracted = await extractTextFromFiles(files);
  const content = normalizeWhitespace([actionInput.documentContent, extracted.text].filter(Boolean).join("\n\n"));
  assertText(content, "Add document content or upload a supported document file.");

  const documents = await readMemoryDocuments();
  const record = {
    id: crypto.randomUUID(),
    title: actionInput.documentTitle,
    category: actionInput.documentCategory || "General",
    content,
    excerpt: excerpt(content, 220),
    tokens: unique(tokenize(content)).slice(0, 60),
    createdAt: isoNow(),
  };

  documents.unshift(record);
  await writeMemoryDocuments(documents);

  return buildResult({
    headline: `Indexed ${record.title} into local memory.`,
    summary: `The document was tokenized and stored for lightweight semantic recall across future RAG searches.`,
    metrics: [
      { label: "Document ID", value: record.id.slice(0, 8) },
      { label: "Category", value: record.category },
      { label: "Tokens stored", value: String(record.tokens.length) },
      { label: "Total documents", value: String(documents.length) },
    ],
    highlights: [
      `Title: ${record.title}`,
      `Category: ${record.category}`,
      `Top terms: ${topTerms(content, 6).join(", ") || "not enough signal"}`,
    ],
    sections: [
      createTextSection("Stored Excerpt", record.excerpt),
      createListSection("Index Keywords", record.tokens.slice(0, 12)),
    ],
    notes: extracted.notes,
  });
}

export async function handleRagSearch(actionInput) {
  const query = normalizeWhitespace(actionInput.queryText);
  assertText(query, "Enter a memory search query.");

  const documents = await readMemoryDocuments();
  const queryTokens = unique(tokenize(query));
  const topK = toNumber(actionInput.topK, 5);
  const matches = documents
    .map((document) => {
      const overlap = queryTokens.filter((token) => document.tokens.includes(token)).length;
      const phraseBonus = document.content.toLowerCase().includes(query.toLowerCase()) ? 2 : 0;
      return {
        ...document,
        score: overlap + phraseBonus,
      };
    })
    .filter((document) => document.score > 0)
    .sort((left, right) => right.score - left.score)
    .slice(0, topK);

  return buildResult({
    headline: matches.length ? `Found ${matches.length} relevant memory matches.` : "No relevant memory matches found.",
    summary: matches.length
      ? `Search scored local documents using overlap across ${queryTokens.length} normalized query terms.`
      : "Try adding a document first or use more specific search terms.",
    metrics: [
      { label: "Query terms", value: String(queryTokens.length) },
      { label: "Matches", value: String(matches.length) },
      { label: "Indexed docs", value: String(documents.length) },
      { label: "Top K", value: String(topK) },
    ],
    highlights: matches.length
      ? matches.map((match) => `${match.title} (${match.score} overlap score)`)
      : ["No stored document shared enough overlap with the query."],
    sections: [
      createTableSection(
        "Top Matches",
        matches.map((match) => ({
          title: match.title,
          category: match.category,
          score: match.score,
          excerpt: match.excerpt,
        }))
      ),
    ],
  });
}

export async function handleGstin(actionInput) {
  const records = normalizeWhitespace(actionInput.supplierRecords)
    .split(/\n+/)
    .filter(Boolean)
    .map((line, index) => {
      const gstinMatch = line.match(/\b\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]Z[A-Z0-9]\b/);
      const vatMatch = line.match(/\b(?:DE|FR|ES|IT|NL|GB)[A-Z0-9]{8,14}\b/i);
      const name = line.split("|")[0]?.trim() || `Record ${index + 1}`;
      return {
        name,
        normalizedName: normalizeRecordName(name),
        taxId: gstinMatch?.[0] || vatMatch?.[0] || "Not found",
        raw: line,
      };
    });

  const target = normalizeRecordName(actionInput.companyName);
  const likelyMatches = records.filter((record) => record.normalizedName.includes(target) || target.includes(record.normalizedName));
  const duplicates = records.filter((record, index) => records.findIndex((candidate) => candidate.taxId === record.taxId && candidate.taxId !== "Not found") !== index);
  const unresolved = records.filter((record) => record.taxId === "Not found");

  return buildResult({
    headline: `Reconciliation completed for ${actionInput.companyName}.`,
    summary: `The record set was normalized across ${actionInput.countryFocus || "Global"} tax IDs and yielded ${likelyMatches.length} likely matches.`,
    metrics: [
      { label: "Records scanned", value: String(records.length) },
      { label: "Likely matches", value: String(likelyMatches.length) },
      { label: "Duplicates", value: String(duplicates.length) },
      { label: "Missing IDs", value: String(unresolved.length) },
    ],
    highlights: [
      likelyMatches[0]?.name ? `Strongest name match: ${likelyMatches[0].name}` : "No high-confidence supplier name match found.",
      duplicates[0]?.taxId ? `Duplicate tax ID detected: ${duplicates[0].taxId}` : "No duplicate tax ID detected.",
      unresolved[0]?.name ? `Missing tax ID: ${unresolved[0].name}` : "Every record has at least one detected tax ID.",
    ],
    sections: [
      createTableSection(
        "Supplier Records",
        records.map((record) => ({
          name: record.name,
          taxId: record.taxId,
          match: likelyMatches.some((candidate) => candidate.raw === record.raw) ? "Likely" : "Review",
        }))
      ),
    ],
  });
}

export async function handleAuditWrite(actionInput, _files, session) {
  const entries = await readAuditEntries();
  const payload = normalizeWhitespace(actionInput.auditPayload || "{}");
  const previousHash = entries.at(-1)?.hash || "GENESIS";
  const entry = {
    id: crypto.randomUUID(),
    timestamp: isoNow(),
    actorId: actionInput.actorId,
    actionType: actionInput.actionType,
    resourceUri: actionInput.resourceUri,
    payload,
    workspaceUser: session.email,
    previousHash,
  };

  entry.hash = createHash(JSON.stringify(entry));
  entries.push(entry);
  await writeAuditEntries(entries);

  return buildResult({
    headline: "Audit entry committed to the local chain.",
    summary: "A new immutable record was appended with hash chaining against the previous ledger state.",
    metrics: [
      { label: "Chain length", value: String(entries.length) },
      { label: "Actor", value: entry.actorId },
      { label: "Action", value: entry.actionType },
      { label: "Hash prefix", value: entry.hash.slice(0, 12) },
    ],
    highlights: [
      `Resource: ${entry.resourceUri}`,
      `Previous hash: ${previousHash.slice(0, 12)}`,
      `Recorded by session: ${session.email}`,
    ],
    sections: [
      createKeyValueSection("Committed Entry", {
        id: entry.id,
        timestamp: entry.timestamp,
        actor: entry.actorId,
        action: entry.actionType,
        resource: entry.resourceUri,
        hash: entry.hash,
      }),
      createTextSection("Payload", payload),
    ],
  });
}

export async function handleAuditVerify() {
  const entries = await readAuditEntries();
  let valid = true;
  let failureIndex = -1;

  for (let index = 0; index < entries.length; index += 1) {
    const current = entries[index];
    const previousHash = index === 0 ? "GENESIS" : entries[index - 1].hash;
    const candidate = { ...current, previousHash, hash: undefined };
    const recomputed = createHash(JSON.stringify(candidate));

    if (current.previousHash !== previousHash || current.hash !== recomputed) {
      valid = false;
      failureIndex = index;
      break;
    }
  }

  return buildResult({
    headline: valid ? "Audit chain is intact." : "Audit chain verification failed.",
    summary: valid
      ? `All ${entries.length} ledger entries recomputed successfully against their predecessor hash.`
      : `Entry ${failureIndex + 1} does not match its expected hash chain.`,
    metrics: [
      { label: "Entries verified", value: String(entries.length) },
      { label: "Chain status", value: valid ? "Valid" : "Invalid" },
      { label: "Failure index", value: failureIndex >= 0 ? String(failureIndex + 1) : "None" },
      { label: "Genesis hash", value: entries[0]?.previousHash || "GENESIS" },
    ],
    highlights: valid ? ["No tampering signal detected."] : [`Review entry ${failureIndex + 1} for tampering or serialization drift.`],
    sections: [
      createTableSection(
        "Ledger Snapshot",
        entries.slice(-10).map((entry) => ({
          timestamp: entry.timestamp,
          actorId: entry.actorId,
          actionType: entry.actionType,
          hash: entry.hash.slice(0, 16),
        }))
      ),
    ],
  });
}

export async function getStatefulSummary() {
  const [documents, audits] = await Promise.all([readMemoryDocuments(), readAuditEntries()]);
  return {
    indexedDocuments: documents.length,
    auditEntries: audits.length,
  };
}

export async function handleEInvoiceInputText(actionInput, files) {
  const extracted = await extractTextFromFiles(files);
  const text = normalizeWhitespace([actionInput.invoicePayload, extracted.text].filter(Boolean).join("\n\n"));
  assertText(text, "Add invoice JSON/text or upload an attachment for validation.");

  return {
    text,
    extracted,
    parsed: parseLooseJson(text),
    identifiers: extractIdentifiers(text),
  };
}
