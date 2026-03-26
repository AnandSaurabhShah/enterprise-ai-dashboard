from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import json
import hashlib
import time
from datetime import datetime
import asyncio
import uuid

app = FastAPI(title="Enterprise AI Platform API", version="1.0.0")

# Pydantic Models for Input/Output Validation
class CodeMixedInput(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)

class SentimentInput(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)

class MeetingInput(BaseModel):
    audio_path: str = Field(..., min_length=1)

class InvoiceInput(BaseModel):
    image_path: str = Field(..., min_length=1)

class KYCInput(BaseModel):
    document_text: str = Field(..., min_length=1, max_length=5000)

class SLAInput(BaseModel):
    service_data: Dict[str, Any] = Field(...)

class RAGInput(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)

class GSTINInput(BaseModel):
    vendor_name: str = Field(..., min_length=1, max_length=200)

class AuditInput(BaseModel):
    payload: Dict[str, Any] = Field(...)

class CodeMixedOutput(BaseModel):
    intent: str
    confidence: float
    language: str

class SentimentOutput(BaseModel):
    sentiment: str
    score: float
    language: str

class MeetingOutput(BaseModel):
    transcript: str
    tasks: List[str]
    summary: str

class InvoiceOutput(BaseModel):
    gstin: str
    hsn_codes: List[str]
    total_amount: float
    confidence: float

class KYCOutput(BaseModel):
    pan: str
    aadhaar: str
    entities: Dict[str, str]
    confidence: float

class SLAOutput(BaseModel):
    risk_score: float
    breach_probability: float
    factors: List[str]

class RAGOutput(BaseModel):
    answer: str
    sources: List[str]
    relevance: float

class GSTINOutput(BaseModel):
    matches: List[Dict[str, Any]]
    best_match: Dict[str, Any]
    confidence: float

class AuditOutput(BaseModel):
    hash: str
    merkle_root: str
    timestamp: str
    receipt: str

# Mock data and utilities
MOCK_VENDORS = [
    {"name": "Reliance Industries Limited", "gstin": "27AAACR1674C1ZV", "score": 0.95},
    {"name": "Tata Consultancy Services", "gstin": "27AAACT2915E1ZT", "score": 0.92},
    {"name": "Infosys Limited", "gstin": "29AAACI2915E1ZY", "score": 0.88},
]

def calculate_hash(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()

def detect_language(text: str) -> str:
    hinglish_words = ["mujhe", "hai", "karna", "bahut", "achha", "liye", "ke", "ka", "ki"]
    words = text.lower().split()
    hinglish_count = sum(1 for word in words if word in hinglish_words)
    
    if hinglish_count > len(words) * 0.3:
        return "mixed"
    elif hinglish_count > 0:
        return "hi"
    else:
        return "en"

# 1. Code-Mixed Understanding
@app.post("/api/code-mixed", response_model=CodeMixedOutput)
async def code_mixed_understanding(input_data: CodeMixedInput):
    try:
        text = input_data.text.lower()
        language = detect_language(text)
        
        # Simple intent classification
        intents = {
            "procurement": ["procurement", "karna", "buy", "purchase", "lena"],
            "payment": ["payment", "bhugtan", "dena", "pay"],
            "compliance": ["compliance", "gst", "tax", "return"],
            "inventory": ["inventory", "stock", "mal", "jama"]
        }
        
        intent_scores = {}
        for intent, keywords in intents.items():
            score = sum(1 for keyword in keywords if keyword in text)
            intent_scores[intent] = score / len(keywords)
        
        best_intent = max(intent_scores, key=intent_scores.get)
        confidence = max(intent_scores.values())
        
        return CodeMixedOutput(
            intent=best_intent if confidence > 0.1 else "unknown",
            confidence=min(confidence, 1.0),
            language=language
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. Cross-Lingual Sentiment Analyzer
@app.post("/api/sentiment", response_model=SentimentOutput)
async def sentiment_analysis(input_data: SentimentInput):
    try:
        text = input_data.text.lower()
        language = detect_language(text)
        
        positive_words = ["achha", "good", "excellent", "badhiya", "perfect"]
        negative_words = ["bad", "kharab", "slow", "problem", "issue"]
        
        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)
        
        if pos_count > neg_count:
            sentiment = "positive"
            score = min((pos_count - neg_count) / max(len(text.split()), 1), 1.0)
        elif neg_count > pos_count:
            sentiment = "negative"
            score = max((pos_count - neg_count) / max(len(text.split()), 1), -1.0)
        else:
            sentiment = "neutral"
            score = 0.0
        
        return SentimentOutput(
            sentiment=sentiment,
            score=score,
            language=language
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. Autonomous Meeting Intelligence
@app.post("/api/meeting", response_model=MeetingOutput)
async def meeting_intelligence(input_data: MeetingInput):
    try:
        # Mock transcription
        transcript = "Meeting discussed quarterly targets. Action items: 1. Review procurement process 2. Submit GST returns 3. Update inventory records"
        
        # Extract tasks
        tasks = [
            "Review procurement process",
            "Submit GST returns", 
            "Update inventory records"
        ]
        
        summary = "Team meeting focused on compliance and operational efficiency with 3 key action items identified."
        
        return MeetingOutput(
            transcript=transcript,
            tasks=tasks,
            summary=summary
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 4. Indic Vision-Language Invoice Parser
@app.post("/api/invoice", response_model=InvoiceOutput)
async def invoice_parser(input_data: InvoiceInput):
    try:
        # Mock OCR results
        return InvoiceOutput(
            gstin="27AAACR1674C1ZV",
            hsn_codes=["8471", "8517", "8421"],
            total_amount=15000.00,
            confidence=0.89
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 5. Corporate KYC NER Extractor
@app.post("/api/kyc", response_model=KYCOutput)
async def kyc_extractor(input_data: KYCInput):
    try:
        text = input_data.document_text
        
        # Simple pattern matching for PAN and Aadhaar
        import re
        pan_match = re.search(r'[A-Z]{5}[0-9]{4}[A-Z]{1}', text.upper())
        aadhaar_match = re.search(r'\d{4}[-\s]?\d{4}[-\s]?\d{4}', text.replace(' ', ''))
        
        pan = pan_match.group() if pan_match else ""
        aadhaar = aadhaar_match.group().replace(' ', '-') if aadhaar_match else ""
        
        entities = {
            "pan": pan,
            "aadhaar": aadhaar,
            "name": "Test User",
            "document_type": "identity_proof"
        }
        
        return KYCOutput(
            pan=pan,
            aadhaar=aadhaar,
            entities=entities,
            confidence=0.85 if pan and aadhaar else 0.60
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 6. Agentic SLA Breach Predictor
@app.post("/api/sla", response_model=SLAOutput)
async def sla_predictor(input_data: SLAInput):
    try:
        data = input_data.service_data
        
        # Simple risk calculation
        response_time = data.get("response_time", 100)
        uptime = data.get("uptime", 99.0)
        ticket_count = data.get("ticket_count", 10)
        satisfaction = data.get("customer_satisfaction", 4.0)
        
        # Risk factors
        factors = []
        risk_score = 0.0
        
        if response_time > 120:
            risk_score += 0.3
            factors.append("High response time")
        
        if uptime < 99.0:
            risk_score += 0.4
            factors.append("Low uptime")
        
        if ticket_count > 20:
            risk_score += 0.2
            factors.append("High ticket volume")
        
        if satisfaction < 3.5:
            risk_score += 0.1
            factors.append("Low customer satisfaction")
        
        breach_probability = min(risk_score, 1.0)
        
        return SLAOutput(
            risk_score=risk_score,
            breach_probability=breach_probability,
            factors=factors
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 7. Enterprise RAG Memory
@app.post("/api/rag", response_model=RAGOutput)
async def rag_memory(input_data: RAGInput):
    try:
        query = input_data.query.lower()
        
        # Mock knowledge base
        knowledge = {
            "gst": "GST returns are due on the 20th of each month for MSMEs with turnover up to ₹5 crore.",
            "filing": "Quarterly GSTR-1 and monthly GSTR-3B filing is mandatory for registered businesses.",
            "due": "Late filing attracts penalty of ₹50 per day for GSTR-3B and ₹200 per day for GSTR-1."
        }
        
        answer = "Based on your query about GST compliance: "
        if "gst" in query or "return" in query:
            answer += knowledge["gst"]
        elif "filing" in query:
            answer += knowledge["filing"]
        elif "due" in query or "penalty" in query:
            answer += knowledge["due"]
        else:
            answer = "I found information about GST compliance requirements for MSMEs. Please specify your query about filing dates, due amounts, or penalties."
        
        sources = ["GST Act 2017", "CBIC Circular No. 206/2023"]
        relevance = 0.85
        
        return RAGOutput(
            answer=answer,
            sources=sources,
            relevance=relevance
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 8. GSTIN Fuzzy-Matching Reconciler
@app.post("/api/gstin", response_model=GSTINOutput)
async def gstin_reconciler(input_data: GSTINInput):
    try:
        vendor_name = input_data.vendor_name.lower()
        
        # Simple fuzzy matching
        matches = []
        for vendor in MOCK_VENDORS:
            # Calculate simple similarity
            similarity = len(set(vendor_name.split()) & set(vendor["name"].lower().split())) / max(len(vendor_name.split()), len(vendor["name"].lower().split()))
            if similarity > 0.1:
                matches.append({
                    "name": vendor["name"],
                    "gstin": vendor["gstin"],
                    "similarity": similarity,
                    "score": vendor["score"]
                })
        
        matches.sort(key=lambda x: x["similarity"], reverse=True)
        best_match = matches[0] if matches else {}
        confidence = best_match.get("similarity", 0.0)
        
        return GSTINOutput(
            matches=matches,
            best_match=best_match,
            confidence=confidence
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 9. Zero-Cost Cryptographic Audit Trail
@app.post("/api/audit", response_model=AuditOutput)
async def audit_trail(input_data: AuditInput):
    try:
        payload_str = json.dumps(input_data.payload, sort_keys=True)
        
        # Calculate hash
        payload_hash = calculate_hash(payload_str)
        
        # Mock Merkle tree root
        merkle_root = calculate_hash(payload_hash + str(uuid.uuid4()))
        
        timestamp = datetime.utcnow().isoformat()
        receipt = f"AUDIT_{uuid.uuid4().hex[:16]}"
        
        return AuditOutput(
            hash=payload_hash,
            merkle_root=merkle_root,
            timestamp=timestamp,
            receipt=receipt
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/")
async def root():
    return {"message": "Enterprise AI Platform API", "status": "active"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)
