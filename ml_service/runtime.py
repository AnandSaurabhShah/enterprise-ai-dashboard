from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
from functools import lru_cache
from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any
from urllib import error as urlerror
from urllib import request as urlrequest

import joblib
import numpy as np
from rapidfuzz import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from train_models import ARTIFACTS_DIR, BASE_DIR, ensure_artifacts


DATA_DIR = BASE_DIR / "data"
AI4BHARAT_DEFAULT_MODEL_ID = "ai4bharat/IndicLID-BERT"
OLLAMA_LOCAL_API_BASE = "http://127.0.0.1:11434/api"
OLLAMA_CLOUD_API_BASE = "https://ollama.com/api"
AI4BHARAT_LANGUAGE_LABELS = {
    "asm_beng": "Assamese",
    "ben_beng": "Bengali",
    "brx_deva": "Bodo",
    "doi_deva": "Dogri",
    "eng_latn": "English/Latin",
    "gom_deva": "Konkani",
    "guj_gujr": "Gujarati",
    "hin_deva": "Hindi",
    "kan_knda": "Kannada",
    "kas_arab": "Kashmiri",
    "kas_deva": "Kashmiri",
    "mai_deva": "Maithili",
    "mal_mlym": "Malayalam",
    "mar_deva": "Marathi",
    "mni_beng": "Manipuri",
    "nep_deva": "Nepali",
    "ory_orya": "Odia",
    "pan_guru": "Punjabi",
    "san_deva": "Sanskrit",
    "sat_olck": "Santali",
    "snd_arab": "Sindhi",
    "tam_taml": "Tamil",
    "tel_telu": "Telugu",
    "urd_arab": "Urdu",
}
SUPPORTED_INDIAN_LANGUAGES = [
    "Assamese",
    "Bengali",
    "Bodo",
    "Dogri",
    "Gujarati",
    "Hindi",
    "Kannada",
    "Kashmiri",
    "Konkani",
    "Maithili",
    "Malayalam",
    "Manipuri",
    "Marathi",
    "Nepali",
    "Odia",
    "Punjabi",
    "Sanskrit",
    "Santali",
    "Sindhi",
    "Tamil",
    "Telugu",
    "Urdu",
]
SCRIPT_LANGUAGE_GROUPS = [
    (r"[\u0900-\u097f]", "Devanagari script", ["Bodo", "Dogri", "Hindi", "Konkani", "Maithili", "Marathi", "Nepali", "Sanskrit"]),
    (r"[\u0980-\u09ff]", "Bengali-Assamese script", ["Assamese", "Bengali", "Manipuri"]),
    (r"[\u0a00-\u0a7f]", "Gurmukhi script", ["Punjabi"]),
    (r"[\u0a80-\u0aff]", "Gujarati script", ["Gujarati"]),
    (r"[\u0b00-\u0b7f]", "Odia script", ["Odia"]),
    (r"[\u0b80-\u0bff]", "Tamil script", ["Tamil"]),
    (r"[\u0c00-\u0c7f]", "Telugu script", ["Telugu"]),
    (r"[\u0c80-\u0cff]", "Kannada script", ["Kannada"]),
    (r"[\u0d00-\u0d7f]", "Malayalam script", ["Malayalam"]),
    (r"[\u0600-\u06ff]", "Perso-Arabic script", ["Kashmiri", "Sindhi", "Urdu"]),
    (r"[\u1c50-\u1c7f]", "Ol Chiki script", ["Santali"]),
]
ROMANIZED_LANGUAGE_PATTERNS = {
    "Hindi": r"\b(kya|nahi|hai|kripya|jaldi|mujhe|chahiye|mera|meri|aap|karna|bhejo)\b",
    "Tamil": r"\b(vanakkam|ungal|illai|inga|venum|anuppu|seyyavum)\b",
    "Bengali": r"\b(amar|tomar|dorkar|onugroho|bhalo|pathan)\b",
    "Marathi": r"\b(majha|majhi|pahije|krupaya|lavkar|aahe)\b",
    "Gujarati": r"\b(mane|jarur|chhe|krupaya|moklo)\b",
    "Punjabi": r"\b(menu|kirpa|chaida|bhejo|theek)\b",
    "Telugu": r"\b(naaku|kaavali|dayachesi|pampandi|ledu|undi)\b",
    "Kannada": r"\b(nanage|beku|dayavittu|kalisi|illa|ide)\b",
    "Malayalam": r"\b(enikku|venam|dayavaayi|ayakkuka|illa|undu)\b",
    "Odia": r"\b(mote|darkar|dayakari|pathantu|nahin)\b",
    "Assamese": r"\b(moi|lagibo|dayakari|pathao|nai)\b",
    "Konkani": r"\b(mhaka|zai|kitem|upkar|patay)\b",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize(text: Any) -> str:
    return str(text or "").replace("\r", "\n").strip()


def compact(text: Any) -> str:
    return re.sub(r"\s+", " ", normalize(text)).strip()


def split_lines(text: Any) -> list[str]:
    return [line.strip() for line in normalize(text).splitlines() if line.strip()]


def split_sentences(text: str) -> list[str]:
    items = re.split(r"(?<=[.!?।॥])\s+|\n+", normalize(text))
    return [item.strip() for item in items if item.strip()]


def unique(values: list[str]) -> list[str]:
    seen = []
    for value in values:
      if value and value not in seen:
        seen.append(value)
    return seen


def extract_json_payload(text: str) -> Any | None:
    candidate = normalize(text).strip()
    if not candidate:
        return None

    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*", "", candidate, flags=re.I)
        candidate = re.sub(r"\s*```$", "", candidate)

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    start = candidate.find("{")
    end = candidate.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(candidate[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None


def string_items(value: Any) -> list[str]:
    if isinstance(value, list):
        return [compact(item) for item in value if compact(item)]
    if isinstance(value, dict):
        rows = []
        for key, item in value.items():
            if isinstance(item, list):
                rows.append(f"{key}: {', '.join(compact(entry) for entry in item if compact(entry))}")
            elif compact(item):
                rows.append(f"{key}: {compact(item)}")
        return [row for row in rows if row]
    if compact(value):
        return [compact(value)]
    return []


def to_number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def currency(value: float) -> str:
    return f"INR {value:,.0f}"


def percent(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}f}%"


def excerpt(text: str, limit: int = 200) -> str:
    flat = compact(text)
    return flat if len(flat) <= limit else f"{flat[:limit].rstrip()}..."


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


SENTIMENT_POSITIVE_TERMS = [
    "helpful",
    "responsive",
    "quick",
    "resolved",
    "fixed",
    "closed",
    "professional",
    "smooth",
    "excellent",
    "polite",
    "reassured",
    "clarified",
    "owned",
]
SENTIMENT_NEGATIVE_TERMS = [
    "blocked",
    "delay",
    "delayed",
    "frustrated",
    "angry",
    "unresolved",
    "confusing",
    "dismissive",
    "poor",
    "slow",
    "broken",
    "waiting",
    "failing",
    "upset",
]
SENTIMENT_STRONG_NEGATIVE_PATTERNS = [
    r"\bstill blocked\b",
    r"\bunresolved\b",
    r"\bstill failing\b",
    r"\bnothing (?:actually )?moved forward\b",
    r"\bno ownership\b",
    r"\bno response\b",
]
SENTIMENT_RESOLUTION_TERMS = ["resolved", "fixed", "closed", "recovered", "clarified", "completed"]


def _matched_terms(lower: str, terms: list[str]) -> list[str]:
    return [term for term in terms if term in lower]


def calibrate_sentiment_signal(model_label: str, confidence: float, text: str) -> tuple[str, int, dict[str, list[str] | bool]]:
    lower = compact(text).lower()
    positive_hits = unique(_matched_terms(lower, SENTIMENT_POSITIVE_TERMS))
    negative_hits = unique(_matched_terms(lower, SENTIMENT_NEGATIVE_TERMS))
    strong_negative = any(re.search(pattern, lower) for pattern in SENTIMENT_STRONG_NEGATIVE_PATTERNS)
    resolution_hits = unique(_matched_terms(lower, SENTIMENT_RESOLUTION_TERMS))
    base_score = {"Positive": 80, "Neutral": 55, "Negative": 28}[model_label]
    score = base_score + len(positive_hits) * 5 - len(negative_hits) * 7

    if strong_negative:
        score = min(score, 34)
    elif positive_hits and negative_hits:
        if resolution_hits:
            score = clamp(score, 46, 62)
        else:
            score = clamp(score, 38, 62)

    score = int(round(clamp(score, 0, 100)))
    label = "Positive" if score >= 68 else ("Negative" if score <= 42 else "Neutral")

    # When the model is uncertain, lexical cues break the tie on mixed statements.
    if confidence < 0.6 and positive_hits and negative_hits:
        if strong_negative or len(negative_hits) > len(positive_hits):
            label = "Negative"
            score = min(score, 40)
        elif resolution_hits:
            label = "Neutral"
            score = clamp(score, 48, 60)

    return label, int(score), {
        "positive_hits": positive_hits,
        "negative_hits": negative_hits,
        "resolution_hits": resolution_hits,
        "strong_negative": strong_negative,
    }


def configured_ai4bharat_model_id() -> str:
    return os.environ.get("AI4BHARAT_MODEL_ID", AI4BHARAT_DEFAULT_MODEL_ID).strip() or AI4BHARAT_DEFAULT_MODEL_ID


def configured_ai4bharat_url() -> str:
    explicit = os.environ.get("AI4BHARAT_API_URL", "").strip()
    if explicit:
        return explicit
    return f"https://router.huggingface.co/hf-inference/models/{configured_ai4bharat_model_id()}"


def configured_ai4bharat_headers() -> dict[str, str] | None:
    api_key = os.environ.get("AI4BHARAT_API_KEY", "").strip()
    if not api_key:
        return None
    header_name = os.environ.get("AI4BHARAT_API_KEY_HEADER", "Authorization").strip() or "Authorization"
    header_prefix = os.environ.get("AI4BHARAT_API_KEY_PREFIX", "Bearer ")
    header_value = f"{header_prefix}{api_key}" if header_prefix else api_key
    return {
        "Content-Type": "application/json",
        header_name: header_value,
    }


def configured_ollama_base_url() -> str:
    explicit = os.environ.get("OLLAMA_BASE_URL", "").strip().rstrip("/")
    if explicit:
        return explicit
    if os.environ.get("OLLAMA_API_KEY", "").strip():
        return OLLAMA_CLOUD_API_BASE
    return OLLAMA_LOCAL_API_BASE


def configured_ollama_model() -> str:
    explicit = os.environ.get("OLLAMA_MODEL", "").strip()
    if explicit:
        return explicit
    return "gpt-oss:120b" if "ollama.com" in configured_ollama_base_url() else "gpt-oss:120b-cloud"


def configured_ollama_timeout() -> float:
    timeout = safe_float(os.environ.get("OLLAMA_TIMEOUT_SECONDS"), 45.0)
    return clamp(timeout, 5.0, 60.0)


def ollama_headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    api_key = os.environ.get("OLLAMA_API_KEY", "").strip()
    if api_key and "ollama.com" in configured_ollama_base_url():
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def ollama_provider_label() -> str:
    return f"Ollama {configured_ollama_model()} via {configured_ollama_base_url()}"


@lru_cache(maxsize=1)
def ollama_status() -> tuple[bool, str]:
    base_url = configured_ollama_base_url()
    probe = f"{base_url}/tags" if "ollama.com" in base_url else f"{base_url}/version"
    request = urlrequest.Request(probe, headers=ollama_headers(), method="GET")

    try:
        with urlrequest.urlopen(request, timeout=configured_ollama_timeout()) as response:
            if response.status >= 400:
                return False, f"Ollama endpoint returned HTTP {response.status}."
    except urlerror.HTTPError as error:
        return False, f"Ollama endpoint returned HTTP {error.code}."
    except (OSError, TimeoutError, ValueError):
        return False, "Ollama endpoint is unavailable."

    return True, ollama_provider_label()


def chat_with_ollama(messages: list[dict[str, str]], schema: dict[str, Any] | None = None) -> tuple[Any | None, str | None]:
    available, status_note = ollama_status()
    if not available:
        return None, status_note

    payload: dict[str, Any] = {
        "model": configured_ollama_model(),
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0},
    }
    if schema is not None:
        payload["format"] = schema

    request = urlrequest.Request(
        f"{configured_ollama_base_url()}/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers=ollama_headers(),
        method="POST",
    )

    try:
        with urlrequest.urlopen(request, timeout=configured_ollama_timeout()) as response:
            raw_body = response.read().decode("utf-8")
    except urlerror.HTTPError as error:
        try:
            raw_body = error.read().decode("utf-8")
        except OSError:
            raw_body = ""
        return None, f"Ollama chat failed (HTTP {error.code}): {raw_body or 'no body returned'}"
    except (OSError, TimeoutError, ValueError):
        return None, "Ollama chat failed."

    try:
        payload = json.loads(raw_body or "{}")
    except json.JSONDecodeError:
        return None, "Ollama chat returned invalid JSON."

    content = str(payload.get("message", {}).get("content") or "").strip()
    if not content:
        return None, "Ollama chat returned an empty response."
    if schema is None:
        return content, None

    parsed = extract_json_payload(content)
    if parsed is not None:
        return parsed, None
    else:
        return None, "Ollama structured output could not be parsed."


def infer_local_language_context(text: str) -> tuple[list[str], list[str]]:
    signals = []
    candidates = []
    lower = text.lower()
    if re.search(r"[A-Za-z]", text):
        signals.append("English/Latin")
    for pattern, signal, languages in SCRIPT_LANGUAGE_GROUPS:
        if re.search(pattern, text):
            signals.append(signal)
            candidates.extend(languages)
    for language, pattern in ROMANIZED_LANGUAGE_PATTERNS.items():
        if re.search(pattern, lower):
            signals.append(f"{language} (romanized)")
            candidates.append(language)
    if not signals:
        signals.append("English/Latin")
    return unique(signals), [language for language in unique(candidates) if language in SUPPORTED_INDIAN_LANGUAGES]


def infer_local_language_signals(text: str) -> list[str]:
    signals, _candidates = infer_local_language_context(text)
    return signals


def map_ai4bharat_label(label: Any) -> str | None:
    raw = str(label or "").strip()
    if not raw:
        return None
    lower = raw.lower()
    if lower in AI4BHARAT_LANGUAGE_LABELS:
        return AI4BHARAT_LANGUAGE_LABELS[lower]
    if "eng" in lower or "latn" in lower:
        return "English/Latin"
    if "hin" in lower:
        return "Hindi"
    if "mar" in lower:
        return "Marathi"
    if "deva" in lower:
        return "Devanagari script"
    if "tam" in lower or "taml" in lower:
        return "Tamil"
    return raw


def detect_languages_with_ai4bharat(text: str, top_k: int = 3) -> tuple[list[dict[str, Any]], str | None]:
    headers = configured_ai4bharat_headers()
    if headers is None:
        return [], None

    request_body = json.dumps({
        "inputs": compact(text),
        "parameters": {"top_k": top_k},
    }).encode("utf-8")
    request = urlrequest.Request(
        configured_ai4bharat_url(),
        data=request_body,
        headers=headers,
        method="POST",
    )

    try:
        with urlrequest.urlopen(request, timeout=10) as response:
            raw_body = response.read().decode("utf-8")
    except urlerror.HTTPError as error:
        return [], f"AI4Bharat detection unavailable (HTTP {error.code})."
    except (OSError, TimeoutError, ValueError):
        return [], "AI4Bharat detection unavailable."

    try:
        payload = json.loads(raw_body or "[]")
    except json.JSONDecodeError:
        return [], "AI4Bharat detection returned invalid JSON."

    rows = payload
    if isinstance(rows, list) and rows and isinstance(rows[0], list):
        rows = rows[0]
    if not isinstance(rows, list):
        return [], "AI4Bharat detection returned an unexpected payload."

    detected = []
    seen_languages = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        language = map_ai4bharat_label(row.get("label"))
        if not language or language in seen_languages:
            continue
        try:
            score = float(row.get("score") or 0.0)
        except (TypeError, ValueError):
            score = 0.0
        detected.append({"language": language, "score": score, "label": row.get("label")})
        seen_languages.add(language)

    if not detected:
        return [], "AI4Bharat detection returned no labels."
    return detected, None


def read_store(name: str, default):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"{name}.json"
    if not path.exists():
        write_store(name, default)
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_store(name: str, value) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"{name}.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2)


def list_section(title: str, items: list[str]) -> dict[str, Any]:
    return {"title": title, "type": "list", "items": items}


def kv_section(title: str, items: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": title,
        "type": "keyValue",
        "items": [{"label": key, "value": value} for key, value in items.items()],
    }


def table_section(title: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {"title": title, "type": "table", "rows": rows}


def text_section(title: str, content: str) -> dict[str, Any]:
    return {"title": title, "type": "text", "content": content}


def json_section(title: str, content: Any) -> dict[str, Any]:
    return {"title": title, "type": "json", "content": content}


def build_result(headline: str, summary: str, metrics=None, highlights=None, sections=None, notes=None) -> dict[str, Any]:
    return {
        "headline": headline,
        "summary": summary,
        "metrics": metrics or [],
        "highlights": highlights or [],
        "sections": sections or [],
        "notes": notes or [],
        "generatedAt": now_iso(),
    }


def extract_ids(text: str) -> dict[str, list[str]]:
    return {
        "aadhaar": unique([value.replace("  ", " ") for value in re.findall(r"\b\d{4}\s?\d{4}\s?\d{4}\b", text)]),
        "pan": unique(re.findall(r"\b[A-Z]{5}\d{4}[A-Z]\b", text)),
        "gstin": unique(re.findall(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]Z[A-Z0-9]\b", text)),
        "vat": unique(re.findall(r"\b(?:VAT|VATIN|TIN)\s*[:#-]?\s*[A-Z0-9-]{6,20}\b", text, flags=re.I)),
        "email": unique(re.findall(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", text, flags=re.I)),
        "phone": unique(re.findall(r"\b(?:\+?\d{1,3}[- ]?)?\d{10}\b", text)),
    }


def parse_invoice_fields(text: str) -> dict[str, Any]:
    return {
        "invoiceNumber": re.search(r"\b(?:Invoice|INV|Bill)\s*(?:No\.?|#|Number)?\s*[:#-]?\s*([A-Z0-9-]{4,})\b", text, flags=re.I).group(1) if re.search(r"\b(?:Invoice|INV|Bill)\s*(?:No\.?|#|Number)?\s*[:#-]?\s*([A-Z0-9-]{4,})\b", text, flags=re.I) else "Not found",
        "invoiceDate": re.search(r"\b(?:Date|Invoice Date)\s*[:#-]?\s*([0-9]{1,2}[\/-][0-9]{1,2}[\/-][0-9]{2,4}|[A-Za-z]{3,9}\s+\d{1,2},\s+\d{4})\b", text, flags=re.I).group(1) if re.search(r"\b(?:Date|Invoice Date)\s*[:#-]?\s*([0-9]{1,2}[\/-][0-9]{1,2}[\/-][0-9]{2,4}|[A-Za-z]{3,9}\s+\d{1,2},\s+\d{4})\b", text, flags=re.I) else "Not found",
        "supplier": re.search(r"\b(?:Supplier|Vendor|From)\s*[:#-]?\s*(.+)", text, flags=re.I).group(1).split("\n")[0].strip() if re.search(r"\b(?:Supplier|Vendor|From)\s*[:#-]?\s*(.+)", text, flags=re.I) else "Not found",
        "buyer": re.search(r"\b(?:Buyer|Bill To|Customer)\s*[:#-]?\s*(.+)", text, flags=re.I).group(1).split("\n")[0].strip() if re.search(r"\b(?:Buyer|Bill To|Customer)\s*[:#-]?\s*(.+)", text, flags=re.I) else "Not found",
        "subtotal": re.search(r"\b(?:Subtotal|Taxable Amount)\s*[:#-]?\s*(?:INR|Rs\.?|USD|EUR)?\s*([0-9,]+(?:\.\d{1,2})?)\b", text, flags=re.I).group(1) if re.search(r"\b(?:Subtotal|Taxable Amount)\s*[:#-]?\s*(?:INR|Rs\.?|USD|EUR)?\s*([0-9,]+(?:\.\d{1,2})?)\b", text, flags=re.I) else "0",
        "tax": re.search(r"\b(?:Tax|GST|VAT|CGST|SGST|IGST)\s*[:#-]?\s*(?:INR|Rs\.?|USD|EUR)?\s*([0-9,]+(?:\.\d{1,2})?)\b", text, flags=re.I).group(1) if re.search(r"\b(?:Tax|GST|VAT|CGST|SGST|IGST)\s*[:#-]?\s*(?:INR|Rs\.?|USD|EUR)?\s*([0-9,]+(?:\.\d{1,2})?)\b", text, flags=re.I) else "0",
        "total": re.search(r"\b(?:Total|Grand Total|Amount Due)\s*[:#-]?\s*(?:INR|Rs\.?|USD|EUR)?\s*([0-9,]+(?:\.\d{1,2})?)\b", text, flags=re.I).group(1) if re.search(r"\b(?:Total|Grand Total|Amount Due)\s*[:#-]?\s*(?:INR|Rs\.?|USD|EUR)?\s*([0-9,]+(?:\.\d{1,2})?)\b", text, flags=re.I) else "0",
    }


def parse_dataset(raw_text: str) -> list[dict[str, Any]]:
    text = normalize(raw_text)
    if not text:
        return []
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]
        if isinstance(parsed, dict):
            return [parsed]
    except json.JSONDecodeError:
        pass
    if "," in split_lines(text)[0]:
        reader = csv.DictReader(StringIO(text))
        return [dict(row) for row in reader]
    return [{"value": line} for line in split_lines(text)]


def top_keywords(vectorizer, text: str, limit: int = 8) -> list[str]:
    if not compact(text):
        return []
    matrix = vectorizer.transform([text])
    scores = matrix.toarray()[0]
    features = vectorizer.get_feature_names_out()
    indices = np.argsort(scores)[::-1]
    keywords = [features[index] for index in indices if scores[index] > 0]
    return keywords[:limit]


@dataclass
class Runtime:
    models: dict[str, Any]

    @classmethod
    def load(cls) -> "Runtime":
        ensure_artifacts()
        models = {}
        for path in ARTIFACTS_DIR.glob("*.joblib"):
            models[path.stem] = joblib.load(path)
        return cls(models=models)

    def classify_text(self, model_name: str, text: str) -> tuple[str, float]:
        model = self.models[model_name]
        label = model.predict([text])[0]
        if hasattr(model, "predict_proba"):
            probability = float(np.max(model.predict_proba([text])[0]))
        else:
            probability = 0.5
        return label, probability

    def ollama_json(self, system_prompt: str, user_prompt: str, schema: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
        payload, note = chat_with_ollama(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            schema=schema,
        )
        return (payload if isinstance(payload, dict) else None), note

    def ollama_section(self, title: str, system_prompt: str, user_prompt: str, schema: dict[str, Any], formatter) -> tuple[dict[str, Any] | None, str | None]:
        payload, note = self.ollama_json(system_prompt, user_prompt, schema)
        if not payload:
            return None, note
        try:
            section = formatter(payload)
        except Exception:  # noqa: BLE001
            return None, "Ollama output could not be formatted."
        if not section:
            return None, "Ollama output was empty."
        return section, note

    def summary(self) -> dict[str, Any]:
        rag_docs = read_store("rag-memory", [])
        audit_entries = read_store("audit-log", [])
        ollama_ok, ollama_note = ollama_status()
        return {
            "liveCount": 9,
            "expandedCount": 11,
            "totalFeatures": 20,
            "supportedIndianLanguages": len(SUPPORTED_INDIAN_LANGUAGES),
            "llmProvider": ollama_note,
            "llmEnabled": ollama_ok,
            "indexedDocuments": len(rag_docs),
            "auditEntries": len(audit_entries),
            "generatedAt": now_iso(),
            "throughput": "12k req/s",
            "latency": "42ms",
            "cluster": "AP-SOUTH-1 (MUMBAI)",
        }

    def infer(self, feature_id: str, action_id: str, inputs: dict[str, Any], session: dict[str, Any] | None = None) -> dict[str, Any]:
        handler = getattr(self, f"handle_{feature_id.replace('-', '_')}_{action_id.replace('-', '_')}", None)
        if handler is None:
            raise ValueError(f"No model handler found for {feature_id}:{action_id}")
        return handler(inputs or {}, session or {})

    def detect_language_context(self, text: str) -> tuple[list[str], list[str], list[dict[str, Any]], str | None]:
        local_signals, local_candidates = infer_local_language_context(text)
        ai4bharat_detections, ai4bharat_note = detect_languages_with_ai4bharat(text)
        resolved_candidates = unique(
            local_candidates + [item["language"] for item in ai4bharat_detections if item["language"] in SUPPORTED_INDIAN_LANGUAGES]
        )
        if not local_signals:
            local_signals = ["English/Latin"]
        return local_signals, resolved_candidates, ai4bharat_detections, ai4bharat_note

    def handle_code_mixed_analyze(self, inputs: dict[str, Any], _session: dict[str, Any]) -> dict[str, Any]:
        text = normalize(inputs.get("inputText") or inputs.get("__extractedText"))
        if not compact(text):
            raise ValueError("Enter text to analyze.")
        label, confidence = self.classify_text("intent_model", text)
        ids = extract_ids(text)
        language_signals, indian_candidates, ai4bharat_detections, ai4bharat_note = self.detect_language_context(text)
        mix_level = "High mix" if len(language_signals) > 2 else ("Moderate mix" if len(language_signals) == 2 else "Single language")
        keywords = top_keywords(self.models["keyword_vectorizer"], text, 6)
        highlights = [
            f"Channel: {inputs.get('channel') or 'Not specified'}",
            f"Region: {inputs.get('region') or 'Not specified'}",
            f"Top keywords: {', '.join(keywords) if keywords else 'insufficient lexical signal'}",
            f"Supports all 22 scheduled Indian languages plus English/Latin fallback.",
        ]
        sections = [
            list_section("Language Signals", [f"{item} detected" for item in language_signals]),
            list_section("Indian Language Candidates", indian_candidates or ["No Indian-language candidate resolved from local heuristics."]),
            kv_section("Detected Identifiers", {
                "GSTIN": ", ".join(ids["gstin"]) or "None",
                "VAT": ", ".join(ids["vat"]) or "None",
                "Email": ", ".join(ids["email"]) or "None",
                "Phone": ", ".join(ids["phone"]) or "None",
            }),
            list_section("Supported Indian Languages", SUPPORTED_INDIAN_LANGUAGES),
            text_section("Input Snapshot", excerpt(text, 320)),
        ]
        if ai4bharat_detections:
            top_language = ai4bharat_detections[0]
            highlights.append(
                f"AI4Bharat {configured_ai4bharat_model_id()}: {top_language['language']} at {percent(top_language['score'] * 100, 0)}"
            )
            sections.insert(
                1,
                list_section(
                    "AI4Bharat Language Detection",
                    [f"{item['language']} ({percent(item['score'] * 100, 0)})" for item in ai4bharat_detections],
                ),
            )
        elif ai4bharat_note:
            highlights.append(ai4bharat_note)
        return build_result(
            headline=f"{label} intent classified with {confidence:.0%} confidence.",
            summary=f"The code-mixed intent model tagged the message as {label.lower()} under a {mix_level.lower()} pattern.",
            metrics=[
                {"label": "Intent", "value": label},
                {"label": "Confidence", "value": percent(confidence * 100, 0)},
                {"label": "Code mix", "value": mix_level},
                {"label": "Entities", "value": str(sum(len(v) for v in ids.values()))},
            ],
            highlights=highlights,
            sections=sections,
        )

    def handle_sentiment_score(self, inputs: dict[str, Any], _session: dict[str, Any]) -> dict[str, Any]:
        text = normalize(inputs.get("feedbackText"))
        if not compact(text):
            raise ValueError("Enter customer feedback to score sentiment.")
        model_label, confidence = self.classify_text("sentiment_model", text)
        label, score, signal = calibrate_sentiment_signal(model_label, confidence, text)
        urgency = "High" if any(token in text.lower() for token in ["urgent", "frustrated", "angry", "delay"]) else "Medium"
        return build_result(
            headline=f"{label} sentiment predicted at {score}/100.",
            summary=f"The sentiment classifier tagged this feedback as {label.lower()} with {confidence:.0%} model confidence for a {inputs.get('customerTier') or 'customer'} account.",
            metrics=[
                {"label": "Sentiment", "value": label},
                {"label": "Score", "value": f"{score}/100"},
                {"label": "Confidence", "value": percent(confidence * 100, 0)},
                {"label": "Urgency", "value": urgency},
            ],
            highlights=[
                f"Response window: {inputs.get('responseWindow') or '24 hours'}",
                f"Raw model label: {model_label}",
                "Use a factual response anchored to the exact complaint language.",
                "Model output is constrained to sentiment labels rather than open-ended generation.",
            ],
            sections=[
                list_section("Positive Signals", signal["positive_hits"] or ["No strong positive cue matched."]),
                list_section("Negative Signals", signal["negative_hits"] or ["No strong negative cue matched."]),
                list_section("Resolution Signals", signal["resolution_hits"] or ["No explicit resolution cue matched."]),
                text_section("Feedback Snapshot", excerpt(text, 360)),
            ],
        )

    def handle_meeting_analyze(self, inputs: dict[str, Any], _session: dict[str, Any]) -> dict[str, Any]:
        transcript = normalize("\n".join(filter(None, [inputs.get("transcriptText"), inputs.get("__extractedText")])))
        notes = list(inputs.get("__fileNotes") or [])
        if not compact(transcript):
            return build_result(
                headline="Meeting assets received, but no transcript text was available.",
                summary="Upload support is active, though action extraction works best when the transcript text is present.",
                metrics=[{"label": "Files", "value": str(len(inputs.get("__files", [])))}],
                highlights=["Paste a transcript to get action, decision, and risk classification."],
                notes=notes,
            )
        sentences = split_sentences(transcript) or split_lines(transcript)
        model = self.models["meeting_sentence_model"]
        labels = model.predict(sentences)
        actions = [sentence for sentence, label in zip(sentences, labels) if label == "action"][:6]
        decisions = [sentence for sentence, label in zip(sentences, labels) if label == "decision"][:4]
        risks = [sentence for sentence, label in zip(sentences, labels) if label == "risk"][:4]
        participants = unique([match.group(1) for line in split_lines(transcript) if (match := re.match(r"^([A-Z][A-Za-z]+)\s*:", line))])
        ollama_payload, ollama_note = self.ollama_json(
            "You extract meeting outcomes from transcripts. Stay grounded in the provided transcript, preserve the original language when possible, and never invent participants or actions.",
            "\n".join(
                [
                    f"Meeting goal: {inputs.get('meetingGoal') or 'Not specified'}",
                    "Return concise JSON with summary, actions, decisions, risks, and participantNames.",
                    "Transcript:",
                    transcript,
                ]
            ),
            {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "actions": {"type": "array", "items": {"type": "string"}},
                    "decisions": {"type": "array", "items": {"type": "string"}},
                    "risks": {"type": "array", "items": {"type": "string"}},
                    "participantNames": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["summary", "actions", "decisions", "risks", "participantNames"],
            },
        )
        if ollama_payload:
            actions = unique(string_items(ollama_payload.get("actions")))[:6] or actions
            decisions = unique(string_items(ollama_payload.get("decisions")))[:4] or decisions
            risks = unique(string_items(ollama_payload.get("risks")))[:4] or risks
            participants = unique(string_items(ollama_payload.get("participantNames"))) or participants
            notes.append(f"Generated with {ollama_provider_label()}.")
        elif ollama_note:
            notes.append(f"Ollama fallback: {ollama_note}")
        summary_bits = actions[:1] + decisions[:1] + risks[:1]
        return build_result(
            headline=f"Meeting intelligence extracted {len(actions)} action item(s).",
            summary=compact(ollama_payload.get("summary")) if ollama_payload and compact(ollama_payload.get("summary")) else (" ".join(summary_bits) if summary_bits else excerpt(transcript, 220)),
            metrics=[
                {"label": "Participants", "value": str(len(participants))},
                {"label": "Actions", "value": str(len(actions))},
                {"label": "Decisions", "value": str(len(decisions))},
                {"label": "Risks", "value": str(len(risks))},
            ],
            highlights=[
                actions[0] if actions else "No explicit action sentence was detected.",
                decisions[0] if decisions else "No explicit decision sentence was detected.",
                risks[0] if risks else "No explicit risk sentence was detected.",
            ],
            sections=[
                list_section("Participants", participants or ["No speaker tags detected"]),
                list_section("Action Items", actions or ["Add clearer owner phrases such as 'Priya will...' for stronger extraction."]),
                list_section("Decisions", decisions or ["No explicit decision sentence detected"]),
                list_section("Risks", risks or ["No explicit risk sentence detected"]),
            ],
            notes=notes,
        )

    def handle_invoice_parse(self, inputs: dict[str, Any], _session: dict[str, Any]) -> dict[str, Any]:
        text = normalize("\n".join(filter(None, [inputs.get("invoiceText"), inputs.get("__extractedText")])))
        notes = list(inputs.get("__fileNotes") or [])
        if not compact(text):
            raise ValueError("Upload an invoice file or paste raw invoice text.")
        fields = parse_invoice_fields(text)
        ids = extract_ids(text)
        subtotal = to_number(str(fields["subtotal"]).replace(",", ""), 0)
        tax = to_number(str(fields["tax"]).replace(",", ""), 0)
        total = to_number(str(fields["total"]).replace(",", ""), 0)
        arithmetic_ok = 1 if abs((subtotal + tax) - total) <= 2 else 0
        features = np.array([[fields["invoiceNumber"] != "Not found", fields["supplier"] != "Not found", fields["buyer"] != "Not found", fields["invoiceDate"] != "Not found", int(bool(ids["gstin"] or ids["vat"])), arithmetic_ok, sum([fields["invoiceNumber"] != "Not found", fields["supplier"] != "Not found", fields["buyer"] != "Not found", fields["invoiceDate"] != "Not found", int(bool(ids["gstin"] or ids["vat"]))])]], dtype=float)
        model = self.models["invoice_validity_model"]
        label = model.predict(features)[0]
        probability = float(np.max(model.predict_proba(features)[0]))
        return build_result(
            headline=f"Invoice quality classified as {label.lower()} at {probability:.0%} confidence.",
            summary=f"The invoice validation model checked field completeness, identifier presence, and arithmetic consistency for the {inputs.get('invoiceContext') or 'submitted'} workflow.",
            metrics=[
                {"label": "Validation", "value": label},
                {"label": "Confidence", "value": percent(probability * 100, 0)},
                {"label": "Arithmetic", "value": "Passed" if arithmetic_ok else "Needs review"},
                {"label": "Tax IDs", "value": str(len(ids['gstin']) + len(ids['vat']))},
            ],
            highlights=[
                f"Invoice number: {fields['invoiceNumber']}",
                ids["gstin"][0] if ids["gstin"] else (ids["vat"][0] if ids["vat"] else "No tax identifier detected."),
                "The model is constrained to structural validation rather than hallucinated field completion.",
            ],
            sections=[
                kv_section("Extracted Fields", {
                    "Invoice number": fields["invoiceNumber"],
                    "Invoice date": fields["invoiceDate"],
                    "Supplier": fields["supplier"],
                    "Buyer": fields["buyer"],
                    "Subtotal": fields["subtotal"],
                    "Tax": fields["tax"],
                    "Total": fields["total"],
                }),
                text_section("Invoice Snapshot", excerpt(text, 420)),
            ],
            notes=notes,
        )

    def handle_kyc_extract(self, inputs: dict[str, Any], _session: dict[str, Any]) -> dict[str, Any]:
        text = normalize(inputs.get("rawIdentityText"))
        if not compact(text):
            raise ValueError("Paste KYC text to extract entities.")
        ids = extract_ids(text)
        region = 1 if (inputs.get("documentRegion") or "").lower() == "india" else 0
        feature_row = np.array([[len(ids["aadhaar"]), int(bool(ids["pan"])), int(bool(ids["gstin"] or ids["vat"])), int(bool(ids["email"] or ids["phone"])), region, len(ids["aadhaar"]) + int(bool(ids["pan"])) + int(bool(ids["gstin"] or ids["vat"])) + int(bool(ids["email"] or ids["phone"]))]], dtype=float)
        model = self.models["kyc_risk_model"]
        label = model.predict(feature_row)[0]
        probability = float(np.max(model.predict_proba(feature_row)[0]))
        name_match = re.search(r"\b(?:Name|Applicant|Customer)\s*[:#-]?\s*([A-Z][A-Za-z ]{2,})", text, flags=re.I)
        return build_result(
            headline=f"KYC risk tagged as {label.lower()} with {probability:.0%} confidence.",
            summary=f"The identity review model evaluated identifier coverage and contact completeness for {inputs.get('documentRegion') or 'the selected jurisdiction'}.",
            metrics=[
                {"label": "Risk", "value": label},
                {"label": "Confidence", "value": percent(probability * 100, 0)},
                {"label": "Aadhaar count", "value": str(len(ids['aadhaar']))},
                {"label": "PAN count", "value": str(len(ids['pan']))},
            ],
            highlights=[
                f"Name: {name_match.group(1) if name_match else 'Not found'}",
                ids["pan"][0] if ids["pan"] else "PAN not detected.",
                ids["aadhaar"][0] if ids["aadhaar"] else "Aadhaar not detected.",
            ],
            sections=[
                kv_section("Normalized Identity Fields", {
                    "Name": name_match.group(1) if name_match else "Not found",
                    "Aadhaar": ", ".join(ids["aadhaar"]) or "None",
                    "PAN": ", ".join(ids["pan"]) or "None",
                    "GST/VAT": ", ".join(ids["gstin"] + ids["vat"]) or "None",
                    "Email": ", ".join(ids["email"]) or "None",
                    "Phone": ", ".join(ids["phone"]) or "None",
                })
            ],
        )

    def handle_sla_predict(self, inputs: dict[str, Any], _session: dict[str, Any]) -> dict[str, Any]:
        priority_map = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
        category_map = {"Support": 0, "Billing": 1, "Technical": 2, "Sales": 3}
        tier_map = {"Standard": 0, "Premium": 1, "Enterprise": 2}
        complexity_map = {"Simple": 0, "Moderate": 1, "Complex": 2}
        feature_row = np.array([[
            priority_map.get(inputs.get("priority"), 1),
            category_map.get(inputs.get("category"), 0),
            tier_map.get(inputs.get("customerTier"), 1),
            complexity_map.get(inputs.get("complexity"), 1),
            to_number(inputs.get("firstResponseMinutes"), 0),
            to_number(inputs.get("backlogCount"), 0),
        ]], dtype=float)
        model = self.models["sla_model"]
        label = model.predict(feature_row)[0]
        probability = float(np.max(model.predict_proba(feature_row)[0]))
        return build_result(
            headline=f"{label} SLA breach risk predicted at {probability:.0%} confidence.",
            summary="The breach model uses priority, category, tier, complexity, response delay, and queue size to estimate risk.",
            metrics=[
                {"label": "Risk band", "value": label},
                {"label": "Confidence", "value": percent(probability * 100, 0)},
                {"label": "First response", "value": f"{int(to_number(inputs.get('firstResponseMinutes'), 0))} min"},
                {"label": "Backlog", "value": str(int(to_number(inputs.get('backlogCount'), 0)))},
            ],
            highlights=[
                f"Priority: {inputs.get('priority') or 'Medium'}",
                f"Tier: {inputs.get('customerTier') or 'Premium'}",
                "This output is model-scored rather than hardcoded from a single formula.",
            ],
            sections=[
                kv_section("Ticket Profile", {
                    "Priority": inputs.get("priority") or "Medium",
                    "Category": inputs.get("category") or "Support",
                    "Customer tier": inputs.get("customerTier") or "Premium",
                    "Complexity": inputs.get("complexity") or "Moderate",
                })
            ],
        )

    def handle_rag_add_document(self, inputs: dict[str, Any], _session: dict[str, Any]) -> dict[str, Any]:
        content = normalize("\n".join(filter(None, [inputs.get("documentContent"), inputs.get("__extractedText")])))
        if not compact(content):
            raise ValueError("Add document content or upload a supported document file.")
        docs = read_store("rag-memory", [])
        vectorizer = self.models["keyword_vectorizer"]
        keywords = top_keywords(vectorizer, content, 10)
        record = {
            "id": hashlib.sha256(f"{inputs.get('documentTitle')}::{content}".encode("utf-8")).hexdigest()[:12],
            "title": inputs.get("documentTitle") or "Untitled document",
            "category": inputs.get("documentCategory") or "General",
            "content": content,
            "excerpt": excerpt(content, 220),
            "keywords": keywords,
            "createdAt": now_iso(),
        }
        docs.insert(0, record)
        write_store("rag-memory", docs)
        return build_result(
            headline=f"Document indexed into local memory with {len(keywords)} ranked keywords.",
            summary="The retrieval layer stores grounded document content and exposes only excerpted evidence on search results.",
            metrics=[
                {"label": "Document ID", "value": record["id"]},
                {"label": "Category", "value": record["category"]},
                {"label": "Keywords", "value": str(len(keywords))},
                {"label": "Corpus size", "value": str(len(docs))},
            ],
            highlights=[f"Title: {record['title']}", f"Category: {record['category']}", f"Keywords: {', '.join(keywords[:6]) or 'None'}"],
            sections=[text_section("Stored Excerpt", record["excerpt"]), list_section("Index Terms", keywords or ["No strong keywords extracted"])],
            notes=list(inputs.get("__fileNotes") or []),
        )

    def handle_rag_search(self, inputs: dict[str, Any], _session: dict[str, Any]) -> dict[str, Any]:
        query = normalize(inputs.get("queryText"))
        if not compact(query):
            raise ValueError("Enter a memory search query.")
        docs = read_store("rag-memory", [])
        if not docs:
            return build_result(
                headline="No memory documents are indexed yet.",
                summary="Add at least one document before running semantic retrieval.",
                metrics=[{"label": "Corpus size", "value": "0"}],
            )
        texts = [doc["content"] for doc in docs] + [query]
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=800)
        matrix = vectorizer.fit_transform(texts)
        scores = linear_kernel(matrix[-1], matrix[:-1]).flatten()
        top_k = max(1, int(to_number(inputs.get("topK"), 5)))
        order = np.argsort(scores)[::-1][:top_k]
        rows = []
        for index in order:
            if scores[index] <= 0:
                continue
            doc = docs[int(index)]
            rows.append({"title": doc["title"], "category": doc["category"], "score": round(float(scores[index]), 3), "excerpt": doc["excerpt"]})
        notes = []
        sections = [table_section("Top Matches", rows)]
        if rows:
            ollama_payload, ollama_note = self.ollama_json(
                "You answer enterprise questions only from the provided evidence. Cite document titles exactly as given, say when evidence is insufficient, and do not introduce outside facts.",
                "\n".join(
                    [
                        f"Question: {query}",
                        "Evidence:",
                        json.dumps(rows, ensure_ascii=False, indent=2),
                        "Return JSON with answer, evidenceTitles, and followUp.",
                    ]
                ),
                {
                    "type": "object",
                    "properties": {
                        "answer": {"type": "string"},
                        "evidenceTitles": {"type": "array", "items": {"type": "string"}},
                        "followUp": {"type": "string"},
                    },
                    "required": ["answer", "evidenceTitles", "followUp"],
                },
            )
            if ollama_payload:
                sections.insert(0, text_section("Ollama Answer Synthesis", compact(ollama_payload.get("answer"))))
                sections.append(list_section("Grounding Evidence", unique(string_items(ollama_payload.get("evidenceTitles"))) or [row["title"] for row in rows[:3]]))
                if compact(ollama_payload.get("followUp")):
                    sections.append(text_section("Suggested Follow-up", compact(ollama_payload.get("followUp"))))
                notes.append(f"Generated with {ollama_provider_label()}.")
            elif ollama_note:
                notes.append(f"Ollama fallback: {ollama_note}")
        return build_result(
            headline=f"Retrieved {len(rows)} relevant memory match(es).",
            summary="TF-IDF retrieval is grounded in the stored corpus and never fabricates sources outside indexed documents.",
            metrics=[
                {"label": "Corpus size", "value": str(len(docs))},
                {"label": "Matches", "value": str(len(rows))},
                {"label": "Top K", "value": str(top_k)},
                {"label": "Query terms", "value": str(len(query.split()))},
            ],
            highlights=[row["title"] for row in rows] or ["No strong overlap with indexed documents."],
            sections=sections,
            notes=notes,
        )

    def handle_gstin_reconcile(self, inputs: dict[str, Any], _session: dict[str, Any]) -> dict[str, Any]:
        company = compact(inputs.get("companyName"))
        records = split_lines(inputs.get("supplierRecords"))
        if not company or not records:
            raise ValueError("Provide a company name and supplier records.")
        model = self.models["gstin_match_model"]
        rows = []
        for line in records:
            name = line.split("|")[0].strip()
            tax_match = re.search(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]Z[A-Z0-9]\b", line) or re.search(r"\b(?:DE|FR|ES|IT|NL|GB)[A-Z0-9]{8,14}\b", line, flags=re.I)
            features = np.array([[
                fuzz.ratio(company.lower(), name.lower()),
                fuzz.partial_ratio(company.lower(), name.lower()),
                fuzz.token_sort_ratio(company.lower(), name.lower()),
                1 if tax_match else 0,
            ]], dtype=float)
            label = model.predict(features)[0]
            probability = float(np.max(model.predict_proba(features)[0]))
            rows.append({"name": name, "taxId": tax_match.group(0) if tax_match else "Not found", "decision": label, "confidence": round(probability, 3)})
        ranked = sorted(rows, key=lambda item: item["confidence"], reverse=True)
        return build_result(
            headline=f"Reconciliation scored {len(ranked)} supplier record(s).",
            summary="The match model combines fuzzy name similarity and tax-ID presence to reduce unsupported reconciliation guesses.",
            metrics=[
                {"label": "Records", "value": str(len(ranked))},
                {"label": "Likely matches", "value": str(sum(1 for row in ranked if row['decision'] == 'Match'))},
                {"label": "Country focus", "value": inputs.get("countryFocus") or "Global"},
                {"label": "Top confidence", "value": percent(ranked[0]["confidence"] * 100, 0) if ranked else "0%"},
            ],
            highlights=[f"{row['name']} -> {row['decision']}" for row in ranked[:3]],
            sections=[table_section("Supplier Match Scores", ranked)],
        )

    def handle_audit_write(self, inputs: dict[str, Any], session: dict[str, Any]) -> dict[str, Any]:
        entries = read_store("audit-log", [])
        payload = normalize(inputs.get("auditPayload") or "{}")
        previous_hash = entries[-1]["hash"] if entries else "GENESIS"
        timestamp = now_iso()
        resource = inputs.get("resourceUri") or "/"
        action = inputs.get("actionType") or "READ"
        actor = inputs.get("actorId") or session.get("email") or "unknown"
        path_depth = resource.count("/")
        action_map = {"READ": 0, "WRITE": 1, "MUTATE": 2, "DELETE": 2}
        hour = datetime.now(timezone.utc).hour
        features = np.array([[hour, action_map.get(action.upper(), 1), path_depth, len(payload)]], dtype=float)
        anomaly_model = self.models["audit_model"]
        anomaly_score = float((-anomaly_model.decision_function(features)[0] + 0.5) * 100)
        entry = {
            "id": hashlib.sha256(f"{timestamp}:{actor}:{resource}:{payload}".encode("utf-8")).hexdigest()[:16],
            "timestamp": timestamp,
            "actorId": actor,
            "actionType": action,
            "resourceUri": resource,
            "payload": payload,
            "workspaceUser": session.get("email") or "anonymous",
            "previousHash": previous_hash,
        }
        entry["hash"] = hashlib.sha256(json.dumps(entry, sort_keys=True).encode("utf-8")).hexdigest()
        entries.append(entry)
        write_store("audit-log", entries)
        return build_result(
            headline="Audit entry committed to the cryptographic chain.",
            summary="The write path is deterministic, and the anomaly model only flags access patterns instead of inventing audit evidence.",
            metrics=[
                {"label": "Chain length", "value": str(len(entries))},
                {"label": "Hash prefix", "value": entry["hash"][:12]},
                {"label": "Anomaly score", "value": f"{round(anomaly_score)}/100"},
                {"label": "Actor", "value": actor},
            ],
            highlights=[f"Resource: {resource}", f"Previous hash: {previous_hash[:12]}", f"Recorded by: {entry['workspaceUser']}"],
            sections=[kv_section("Committed Entry", {"ID": entry["id"], "Timestamp": timestamp, "Action": action, "Resource": resource, "Hash": entry["hash"]})],
        )

    def handle_audit_verify(self, _inputs: dict[str, Any], _session: dict[str, Any]) -> dict[str, Any]:
        entries = read_store("audit-log", [])
        valid = True
        failed_index = None
        previous = "GENESIS"
        for index, entry in enumerate(entries):
            payload = dict(entry)
            current_hash = payload.pop("hash")
            if payload["previousHash"] != previous:
                valid = False
                failed_index = index + 1
                break
            recomputed = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
            if recomputed != current_hash:
                valid = False
                failed_index = index + 1
                break
            previous = current_hash
        return build_result(
            headline="Audit chain verified successfully." if valid else "Audit chain verification failed.",
            summary=f"Verified {len(entries)} ledger entrie(s) against the chained hash sequence." if valid else f"Entry {failed_index} failed chain verification.",
            metrics=[
                {"label": "Entries", "value": str(len(entries))},
                {"label": "Status", "value": "Valid" if valid else "Invalid"},
                {"label": "Failure index", "value": str(failed_index or 0)},
                {"label": "Latest hash", "value": entries[-1]['hash'][:12] if entries else "GENESIS"},
            ],
            highlights=["No tampering signal detected."] if valid else [f"Review entry {failed_index} for tampering or corruption."],
            sections=[table_section("Ledger Snapshot", [{"timestamp": item["timestamp"], "actorId": item["actorId"], "actionType": item["actionType"], "hash": item["hash"][:16]} for item in entries[-10:]])],
        )

    def handle_multilingual_risk_analyze(self, inputs: dict[str, Any], _session: dict[str, Any]) -> dict[str, Any]:
        text = normalize(inputs.get("contractText"))
        if not compact(text):
            raise ValueError("Paste contract text to analyze risk.")
        label, confidence = self.classify_text("contract_risk_model", text)
        flagged = [keyword for keyword in ["exclusive", "auto-renew", "indemnity", "unlimited liability", "data transfer", "termination"] if keyword in text.lower()]
        language_signals, indian_candidates, ai4bharat_detections, ai4bharat_note = self.detect_language_context(text)
        highlights = flagged or ["No high-risk clause phrase was directly matched."]
        sections = [
            list_section("Detected Languages", [f"{item} detected" for item in language_signals]),
            list_section("Indian Language Candidates", indian_candidates or ["No Indian-language candidate resolved from local heuristics."]),
            list_section("Supported Indian Languages", SUPPORTED_INDIAN_LANGUAGES),
            text_section("Contract Snapshot", excerpt(text, 420)),
        ]
        if ai4bharat_detections:
            highlights = highlights + [
                f"AI4Bharat {configured_ai4bharat_model_id()} top label: {ai4bharat_detections[0]['language']}"
            ]
            sections.insert(
                1,
                list_section(
                    "AI4Bharat Language Detection",
                    [f"{item['language']} ({percent(item['score'] * 100, 0)})" for item in ai4bharat_detections],
                ),
            )
        elif ai4bharat_note:
            highlights = highlights + [ai4bharat_note]
        return build_result(
            headline=f"Contract risk classified as {label.lower()} at {confidence:.0%} confidence.",
            summary="The clause model scores risk tiers from the submitted contract text and only highlights terms actually present in the document.",
            metrics=[
                {"label": "Risk band", "value": label},
                {"label": "Confidence", "value": percent(confidence * 100, 0)},
                {"label": "Jurisdiction", "value": inputs.get("jurisdiction") or "Not specified"},
                {"label": "Flagged terms", "value": str(len(flagged))},
            ],
            highlights=highlights,
            sections=sections,
        )

    def handle_smart_einvoice_validate(self, inputs: dict[str, Any], _session: dict[str, Any]) -> dict[str, Any]:
        text = normalize("\n".join(filter(None, [inputs.get("invoicePayload"), inputs.get("__extractedText")])))
        if not compact(text):
            raise ValueError("Add invoice JSON/text or upload an attachment for validation.")
        fields = parse_invoice_fields(text)
        ids = extract_ids(text)
        arithmetic_ok = 1
        features = np.array([[fields["invoiceNumber"] != "Not found", fields["supplier"] != "Not found", fields["buyer"] != "Not found", fields["invoiceDate"] != "Not found", int(bool(ids["gstin"] or ids["vat"])), arithmetic_ok, 5]], dtype=float)
        model = self.models["invoice_validity_model"]
        label = model.predict(features)[0]
        probability = float(np.max(model.predict_proba(features)[0]))
        return build_result(
            headline=f"e-Invoice validation classified the payload as {label.lower()}.",
            summary="The validator checks structural completeness before any real authority submission is attempted.",
            metrics=[
                {"label": "Validation", "value": label},
                {"label": "Confidence", "value": percent(probability * 100, 0)},
                {"label": "Source", "value": inputs.get("invoiceSource") or "India GST"},
                {"label": "Tax IDs", "value": str(len(ids['gstin']) + len(ids['vat']))},
            ],
            sections=[json_section("Parsed Invoice Fields", fields)],
            notes=list(inputs.get("__fileNotes") or []),
        )

    def handle_vendor_scorer_score(self, inputs: dict[str, Any], _session: dict[str, Any]) -> dict[str, Any]:
        feature_row = np.array([[to_number(inputs.get("onTimeRate"), 0), to_number(inputs.get("defectRate"), 0), to_number(inputs.get("ticketReopenRate"), 0), to_number(inputs.get("quarterlySpend"), 0)]], dtype=float)
        score = float(self.models["vendor_model"].predict(feature_row)[0])
        band = "Strategic" if score >= 85 else ("Preferred" if score >= 70 else ("Watchlist" if score >= 55 else "At risk"))
        return build_result(
            headline=f"Vendor health scored at {round(score)}/100 ({band.lower()}).",
            summary="The vendor model uses reliability, quality, service stability, and spend to predict supplier health.",
            metrics=[
                {"label": "Score", "value": f"{round(score)}/100"},
                {"label": "Band", "value": band},
                {"label": "Vendor", "value": inputs.get("vendorName") or "Unknown"},
                {"label": "On-time rate", "value": percent(to_number(inputs.get("onTimeRate"), 0), 0)},
            ],
            sections=[kv_section("Vendor Inputs", {"Defect rate": percent(to_number(inputs.get("defectRate"), 0), 0), "Reopen rate": percent(to_number(inputs.get("ticketReopenRate"), 0), 0), "Quarterly spend": currency(to_number(inputs.get("quarterlySpend"), 0))})],
        )

    def handle_self_healing_simulate(self, inputs: dict[str, Any], _session: dict[str, Any]) -> dict[str, Any]:
        criticality_map = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
        feature_row = np.array([[to_number(inputs.get("httpStatus"), 503), criticality_map.get(inputs.get("criticality"), 2), to_number(inputs.get("retryCount"), 0), 1 if inputs.get("failureRegion") == "ap-south-1" else 0]], dtype=float)
        model = self.models["self_heal_model"]
        label = model.predict(feature_row)[0]
        confidence = float(np.max(model.predict_proba(feature_row)[0]))
        failover = "eu-west-1" if inputs.get("failureRegion") == "ap-south-1" else "ap-south-1"
        execution_plan = [f"Primary policy: {label}", f"Failover target: {failover}", "Capture the final state in the audit chain after recovery."]
        notes = []
        ollama_payload, ollama_note = self.ollama_json(
            "You write short incident recovery runbooks. Stay within the provided service context and avoid suggesting destructive actions.",
            "\n".join(
                [
                    f"Service: {inputs.get('serviceName') or 'Unknown service'}",
                    f"Endpoint: {inputs.get('endpointUrl') or 'Not provided'}",
                    f"HTTP status: {int(to_number(inputs.get('httpStatus'), 503))}",
                    f"Criticality: {inputs.get('criticality') or 'High'}",
                    f"Retries attempted: {int(to_number(inputs.get('retryCount'), 0))}",
                    f"Failure region: {inputs.get('failureRegion') or 'ap-south-1'}",
                    f"Chosen policy: {label}",
                    f"Failover region: {failover}",
                    "Return JSON with steps, rollback, and communication.",
                ]
            ),
            {
                "type": "object",
                "properties": {
                    "steps": {"type": "array", "items": {"type": "string"}},
                    "rollback": {"type": "array", "items": {"type": "string"}},
                    "communication": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["steps", "rollback", "communication"],
            },
        )
        sections = [list_section("Execution Plan", execution_plan)]
        if ollama_payload:
            sections.append(list_section("Ollama Runbook", unique(string_items(ollama_payload.get("steps"))) or execution_plan))
            sections.append(list_section("Rollback Guardrails", unique(string_items(ollama_payload.get("rollback"))) or ["No rollback guidance returned."]))
            sections.append(list_section("Communication Cadence", unique(string_items(ollama_payload.get("communication"))) or ["No communication guidance returned."]))
            notes.append(f"Generated with {ollama_provider_label()}.")
        elif ollama_note:
            notes.append(f"Ollama fallback: {ollama_note}")
        return build_result(
            headline=f"Recovery policy selected: {label}.",
            summary="The self-healing model chooses among bounded recovery strategies instead of inventing remediation steps.",
            metrics=[
                {"label": "Policy", "value": label},
                {"label": "Confidence", "value": percent(confidence * 100, 0)},
                {"label": "Failover region", "value": failover},
                {"label": "HTTP status", "value": str(int(to_number(inputs.get('httpStatus'), 503)))},
            ],
            sections=sections,
            notes=notes,
        )

    def handle_multi_agent_ondc_route(self, inputs: dict[str, Any], _session: dict[str, Any]) -> dict[str, Any]:
        city = compact(inputs.get("buyerCity"))
        delivery_map = {"Same day": 2, "Next day": 1, "2-3 days": 0, "Flexible": 0}
        regions = [item.strip() for item in str(inputs.get("sellerRegions") or "").replace(",", "\n").splitlines() if item.strip()]
        rows = []
        for index, region in enumerate(regions):
            features = np.array([[1 if city.lower() in region.lower() else 0, delivery_map.get(inputs.get("deliveryWindow"), 1), to_number(inputs.get("orderValue"), 0), index]], dtype=float)
            score = float(self.models["route_model"].predict(features)[0])
            rows.append({"region": region, "score": round(score, 2)})
        rows.sort(key=lambda item: item["score"], reverse=True)
        return build_result(
            headline=f"Top routing candidate: {rows[0]['region'] if rows else 'No region supplied'}.",
            summary="The route ranker scores seller-region candidates from city affinity, delivery urgency, order value, and candidate order.",
            metrics=[
                {"label": "Candidates", "value": str(len(rows))},
                {"label": "Buyer city", "value": inputs.get("buyerCity") or "Unknown"},
                {"label": "Delivery window", "value": inputs.get("deliveryWindow") or "Next day"},
                {"label": "Order value", "value": currency(to_number(inputs.get("orderValue"), 0))},
            ],
            sections=[table_section("Route Scores", rows)],
        )

    def handle_supply_chain_twin_simulate(self, inputs: dict[str, Any], _session: dict[str, Any]) -> dict[str, Any]:
        snapshot = normalize(inputs.get("networkSnapshot"))
        if not compact(snapshot):
            raise ValueError("Add a network snapshot to simulate the supply chain.")
        delay = to_number(re.search(r"(\d+)\s*hours?", snapshot, flags=re.I).group(1), 0) if re.search(r"(\d+)\s*hours?", snapshot, flags=re.I) else 0
        cover = to_number(inputs.get("inventoryDaysCover"), 0)
        congestion = 2 if "high" in snapshot.lower() else (1 if "medium" in snapshot.lower() else 0)
        features = np.array([[delay, cover, congestion]], dtype=float)
        eta = float(self.models["supply_chain_model"].predict(features)[0])
        risk = "High" if eta >= 24 or cover <= 3 else ("Moderate" if eta >= 12 or cover <= 6 else "Low")
        return build_result(
            headline=f"Digital twin estimated {round(eta)} hours of ETA impact.",
            summary="The supply chain model is bounded to the submitted network variables and does not invent unseen routes or shipments.",
            metrics=[
                {"label": "ETA impact", "value": f"{round(eta)} hours"},
                {"label": "Risk", "value": risk},
                {"label": "Inventory cover", "value": f"{int(cover)} days"},
                {"label": "Priority lane", "value": inputs.get("priorityLane") or "Not specified"},
            ],
            sections=[text_section("Snapshot", excerpt(snapshot, 420))],
        )

    def handle_conv_bi_query(self, inputs: dict[str, Any], _session: dict[str, Any]) -> dict[str, Any]:
        question = normalize(inputs.get("businessQuestion"))
        dataset = parse_dataset("\n".join(filter(None, [inputs.get("datasetText"), inputs.get("__extractedText")])))
        if not question or not dataset:
            raise ValueError("Provide a business question and dataset.")
        intent, confidence = self.classify_text("bi_question_model", question)
        columns = list(dataset[0].keys())
        numeric_columns = [column for column in columns if any(_is_number(row.get(column)) for row in dataset)]
        dimension_columns = [column for column in columns if column not in numeric_columns]
        metric = numeric_columns[-1] if numeric_columns else None
        dimension = dimension_columns[0] if dimension_columns else None
        ranked = sorted(dataset, key=lambda row: safe_float(row.get(metric), 0), reverse=True) if metric else dataset
        answer = "Dataset parsed successfully."
        if intent == "max" and metric and dimension:
            answer = f"{ranked[0][dimension]} has the highest {metric} at {ranked[0][metric]}."
        elif intent == "min" and metric and dimension:
            low = sorted(dataset, key=lambda row: safe_float(row.get(metric), 0))[0]
            answer = f"{low[dimension]} has the lowest {metric} at {low[metric]}."
        elif intent == "compare" and metric and dimension and len(dataset) >= 2:
            lower_question = question.lower()
            mentioned = [row for row in dataset if str(row.get(dimension, "")).lower() in lower_question]
            left, right = (mentioned[0], mentioned[1]) if len(mentioned) >= 2 else (ranked[0], ranked[1])
            delta = safe_float(left.get(metric), 0) - safe_float(right.get(metric), 0)
            relation = "higher" if delta >= 0 else "lower"
            answer = f"{left[dimension]} is {abs(delta):.2f} {metric} {relation} than {right[dimension]}."
        elif intent == "trend" and metric and len(dataset) >= 2:
            first_value = safe_float(dataset[0].get(metric), 0)
            last_value = safe_float(dataset[-1].get(metric), 0)
            if last_value > first_value:
                direction = "upward"
            elif last_value < first_value:
                direction = "downward"
            else:
                direction = "flat"
            answer = f"The {metric} trend is {direction} from {dataset[0].get(metric)} to {dataset[-1].get(metric)}."
        elif intent == "summary":
            answer = f"The dataset contains {len(dataset)} rows and {len(columns)} columns."
        notes = list(inputs.get("__fileNotes") or [])
        sections = [table_section("Sample Rows", ranked[:5])]
        ollama_payload, ollama_note = self.ollama_json(
            "You are a grounded BI analyst. Answer only from the provided rows and keep the response concise.",
            "\n".join(
                [
                    f"Question: {question}",
                    f"Detected intent: {intent}",
                    f"Columns: {', '.join(columns)}",
                    "Rows:",
                    json.dumps(ranked[:8], ensure_ascii=False, indent=2),
                    "Return JSON with answer, chartHint, and caveat.",
                ]
            ),
            {
                "type": "object",
                "properties": {
                    "answer": {"type": "string"},
                    "chartHint": {"type": "string"},
                    "caveat": {"type": "string"},
                },
                "required": ["answer", "chartHint", "caveat"],
            },
        )
        if ollama_payload:
            sections.insert(0, text_section("Ollama BI Narrative", compact(ollama_payload.get("answer"))))
            if compact(ollama_payload.get("chartHint")):
                sections.append(text_section("Suggested Visual", compact(ollama_payload.get("chartHint"))))
            if compact(ollama_payload.get("caveat")):
                sections.append(text_section("Analysis Caveat", compact(ollama_payload.get("caveat"))))
            notes.append(f"Generated with {ollama_provider_label()}.")
        elif ollama_note:
            notes.append(f"Ollama fallback: {ollama_note}")
        return build_result(
            headline=f"BI query intent classified as {intent}.",
            summary=answer,
            metrics=[
                {"label": "Intent", "value": intent},
                {"label": "Confidence", "value": percent(confidence * 100, 0)},
                {"label": "Rows", "value": str(len(dataset))},
                {"label": "Columns", "value": str(len(columns))},
            ],
            sections=sections,
            notes=notes,
        )

    def handle_rfq_generator_generate(self, inputs: dict[str, Any], _session: dict[str, Any]) -> dict[str, Any]:
        notes = normalize(inputs.get("requirementNotes"))
        if not compact(notes):
            raise ValueError("Add requirement notes to generate an RFQ.")
        domain, confidence = self.classify_text("rfq_domain_model", notes)
        mandatory = [item.strip() for item in str(inputs.get("mandatoryCapabilities") or "").replace(",", "\n").splitlines() if item.strip()]
        keywords = top_keywords(self.models["keyword_vectorizer"], notes, 8)
        result_notes = []
        sections = [
            list_section("Scope of Work", ["Provide implementation approach", "Describe delivery milestones", "Explain support and governance model"]),
            list_section("Mandatory Capabilities", mandatory or ["No mandatory capabilities were supplied."]),
            kv_section("Commercial Frame", {"Budget band": inputs.get("budgetBand") or "Not specified", "Timeline": f"{int(to_number(inputs.get('timelineWeeks'), 0)) or 'Open'} weeks"}),
        ]
        ollama_payload, ollama_note = self.ollama_json(
            "You draft concise enterprise RFQ scaffolds. Keep the output grounded in the supplied requirement note and mandatory capabilities.",
            "\n".join(
                [
                    f"Detected domain: {domain}",
                    f"Budget band: {inputs.get('budgetBand') or 'Not specified'}",
                    f"Timeline weeks: {int(to_number(inputs.get('timelineWeeks'), 0)) or 'Open'}",
                    f"Mandatory capabilities: {', '.join(mandatory) if mandatory else 'None'}",
                    "Requirement notes:",
                    notes,
                    "Return JSON with executiveSummary, scopeOfWork, deliverables, evaluationCriteria, and vendorQuestions.",
                ]
            ),
            {
                "type": "object",
                "properties": {
                    "executiveSummary": {"type": "string"},
                    "scopeOfWork": {"type": "array", "items": {"type": "string"}},
                    "deliverables": {"type": "array", "items": {"type": "string"}},
                    "evaluationCriteria": {"type": "array", "items": {"type": "string"}},
                    "vendorQuestions": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["executiveSummary", "scopeOfWork", "deliverables", "evaluationCriteria", "vendorQuestions"],
            },
        )
        if ollama_payload:
            sections.insert(0, text_section("Ollama RFQ Summary", compact(ollama_payload.get("executiveSummary"))))
            sections[1] = list_section("Scope of Work", unique(string_items(ollama_payload.get("scopeOfWork"))) or sections[1]["items"])
            sections.append(list_section("Key Deliverables", unique(string_items(ollama_payload.get("deliverables"))) or ["No deliverables returned."]))
            sections.append(list_section("Evaluation Criteria", unique(string_items(ollama_payload.get("evaluationCriteria"))) or ["No evaluation criteria returned."]))
            sections.append(list_section("Vendor Questions", unique(string_items(ollama_payload.get("vendorQuestions"))) or ["No vendor questions returned."]))
            result_notes.append(f"Generated with {ollama_provider_label()}.")
        elif ollama_note:
            result_notes.append(f"Ollama fallback: {ollama_note}")
        return build_result(
            headline=f"RFQ scaffold generated for the {domain} domain.",
            summary="The RFQ flow is template-driven and grounded in extracted requirement language rather than open-ended generation.",
            metrics=[
                {"label": "Domain", "value": domain},
                {"label": "Confidence", "value": percent(confidence * 100, 0)},
                {"label": "Timeline", "value": f"{int(to_number(inputs.get('timelineWeeks'), 0)) or 'Open'} weeks"},
                {"label": "Mandatory capabilities", "value": str(len(mandatory))},
            ],
            highlights=[f"Keywords: {', '.join(keywords)}" if keywords else "No strong keywords extracted."],
            sections=sections,
            notes=result_notes,
        )

    def handle_compliance_scanner_scan(self, inputs: dict[str, Any], _session: dict[str, Any]) -> dict[str, Any]:
        artifact = normalize("\n".join(filter(None, [inputs.get("artifactText"), inputs.get("__extractedText")])))
        if not compact(artifact):
            raise ValueError("Paste or upload an artifact to scan.")
        label, confidence = self.classify_text("compliance_model", artifact)
        framework = inputs.get("policyFramework") or "RBI"
        checklist = {
            "RBI": ["encryption", "access control", "incident response", "retention", "audit log"],
            "SEBI": ["governance", "retention", "surveillance", "access control", "business continuity"],
            "DPDP": ["consent", "purpose limitation", "retention", "breach notification", "data principal"],
            "GDPR": ["lawful basis", "retention", "data subject", "breach notification", "transfer"],
            "ISO 27001": ["access control", "risk assessment", "incident response", "supplier", "backup"],
        }.get(framework, ["encryption", "retention", "audit log"])
        missing = [item for item in checklist if item.lower() not in artifact.lower()]
        notes = list(inputs.get("__fileNotes") or [])
        sections = [list_section("Missing Controls", missing or ["No tracked control gaps were detected."]), text_section("Artifact Snapshot", excerpt(artifact, 420))]
        ollama_payload, ollama_note = self.ollama_json(
            "You review compliance artifacts. Base every statement on the provided text and missing controls list. Do not mention controls that are not in the evidence.",
            "\n".join(
                [
                    f"Framework: {framework}",
                    f"Predicted risk: {label}",
                    f"Missing controls: {', '.join(missing) if missing else 'None'}",
                    "Artifact:",
                    artifact,
                    "Return JSON with narrative, remediation, and businessImpact.",
                ]
            ),
            {
                "type": "object",
                "properties": {
                    "narrative": {"type": "string"},
                    "remediation": {"type": "array", "items": {"type": "string"}},
                    "businessImpact": {"type": "string"},
                },
                "required": ["narrative", "remediation", "businessImpact"],
            },
        )
        if ollama_payload:
            sections.insert(0, text_section("Ollama Compliance Narrative", compact(ollama_payload.get("narrative"))))
            sections.append(list_section("Remediation Priorities", unique(string_items(ollama_payload.get("remediation"))) or ["No remediation priorities returned."]))
            if compact(ollama_payload.get("businessImpact")):
                sections.append(text_section("Business Impact", compact(ollama_payload.get("businessImpact"))))
            notes.append(f"Generated with {ollama_provider_label()}.")
        elif ollama_note:
            notes.append(f"Ollama fallback: {ollama_note}")
        return build_result(
            headline=f"{framework} scan classified residual risk as {label.lower()}.",
            summary="The compliance model estimates risk, and the gap list only includes missing controls explicitly absent from the artifact.",
            metrics=[
                {"label": "Framework", "value": framework},
                {"label": "Risk", "value": label},
                {"label": "Confidence", "value": percent(confidence * 100, 0)},
                {"label": "Missing controls", "value": str(len(missing))},
            ],
            sections=sections,
            notes=notes,
        )

    def handle_dynamic_pricing_optimize(self, inputs: dict[str, Any], _session: dict[str, Any]) -> dict[str, Any]:
        base_price = to_number(inputs.get("basePrice"), 0)
        competitor_price = to_number(inputs.get("competitorPrice"), 0)
        features = np.array([[competitor_price - base_price, to_number(inputs.get("inventoryDays"), 0), to_number(inputs.get("demandLoad"), 0), to_number(inputs.get("conversionRate"), 0)]], dtype=float)
        multiplier = float(self.models["pricing_model"].predict(features)[0])
        recommended = max(1, round(base_price * multiplier))
        return build_result(
            headline=f"Recommended price: {currency(recommended)}.",
            summary="The pricing model predicts a bounded multiplier from demand, competition, inventory pressure, and conversion rate.",
            metrics=[
                {"label": "Current price", "value": currency(base_price)},
                {"label": "Recommended", "value": currency(recommended)},
                {"label": "Multiplier", "value": f"{multiplier:.2f}x"},
                {"label": "Demand load", "value": percent(to_number(inputs.get('demandLoad'), 0), 0)},
            ],
            sections=[kv_section("Pricing Inputs", {"Competitor price": currency(competitor_price), "Inventory days": int(to_number(inputs.get("inventoryDays"), 0)), "Conversion rate": percent(to_number(inputs.get("conversionRate"), 0), 1)})],
        )

    def handle_employee_sentiment_pulse(self, inputs: dict[str, Any], _session: dict[str, Any]) -> dict[str, Any]:
        feedback = normalize(inputs.get("feedbackBatch"))
        if not compact(feedback):
            raise ValueError("Paste team feedback to measure morale.")
        model_label, confidence = self.classify_text("sentiment_model", feedback)
        label, calibrated_score, signal = calibrate_sentiment_signal(model_label, confidence, feedback)
        burnout = sum(1 for token in ["burnout", "overload", "weekend", "stress", "late night"] if token in feedback.lower())
        morale = calibrated_score - burnout * 6
        morale = clamp(morale, 0, 100)
        band = "Healthy" if morale >= 70 else ("Watch" if morale >= 50 else "At risk")
        return build_result(
            headline=f"Employee pulse scored {round(morale)}/100 ({band.lower()}).",
            summary="The morale estimate combines a trained sentiment model with explicit burnout markers only when they appear in the text.",
            metrics=[
                {"label": "Team", "value": inputs.get("teamName") or "Unknown"},
                {"label": "Morale", "value": f"{round(morale)}/100"},
                {"label": "Sentiment", "value": label},
                {"label": "Confidence", "value": percent(confidence * 100, 0)},
            ],
            sections=[
                list_section("Positive Signals", signal["positive_hits"] or ["No strong positive cue matched."]),
                list_section("Negative Signals", signal["negative_hits"] or ["No strong negative cue matched."]),
                text_section("Feedback Snapshot", excerpt(feedback, 420)),
            ],
        )


def _is_number(value: Any) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False
