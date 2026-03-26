import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError
import json
from main import app

client = TestClient(app)

# Test Pydantic schemas for all 9 LIVE endpoints
class CodeMixedInput(BaseModel):
    text: str

class SentimentInput(BaseModel):
    text: str

class MeetingInput(BaseModel):
    audio_path: str

class InvoiceInput(BaseModel):
    image_path: str

class KYCInput(BaseModel):
    document_text: str

class SLAInput(BaseModel):
    service_data: dict

class RAGInput(BaseModel):
    query: str

class GSTINInput(BaseModel):
    vendor_name: str

class AuditInput(BaseModel):
    payload: dict

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
    tasks: list
    summary: str

class InvoiceOutput(BaseModel):
    gstin: str
    hsn_codes: list
    total_amount: float
    confidence: float

class KYCOutput(BaseModel):
    pan: str
    aadhaar: str
    entities: dict
    confidence: float

class SLAOutput(BaseModel):
    risk_score: float
    breach_probability: float
    factors: list

class RAGOutput(BaseModel):
    answer: str
    sources: list
    relevance: float

class GSTINOutput(BaseModel):
    matches: list
    best_match: dict
    confidence: float

class AuditOutput(BaseModel):
    hash: str
    merkle_root: str
    timestamp: str
    receipt: str

# Test 1: Code-Mixed Understanding
def test_code_mixed_endpoint():
    # Test valid Hinglish input
    response = client.post("/api/code-mixed", json={"text": "Mujhe procurement karna hai for raw materials"})
    assert response.status_code == 200
    
    output = CodeMixedOutput(**response.json())
    assert output.intent in ["procurement", "purchase", "sourcing"]
    assert 0 <= output.confidence <= 1
    assert output.language in ["hi", "en", "mixed"]
    
    # Test gibberish input
    response = client.post("/api/code-mixed", json={"text": "asdfghjkl qwertyuiop"})
    assert response.status_code == 422  # Should fail validation
    
    # Test empty input
    response = client.post("/api/code-mixed", json={"text": ""})
    assert response.status_code == 422

# Test 2: Cross-Lingual Sentiment Analyzer
def test_sentiment_endpoint():
    response = client.post("/api/sentiment", json={"text": "Product bahut achha hai but delivery slow"})
    assert response.status_code == 200
    
    output = SentimentOutput(**response.json())
    assert output.sentiment in ["positive", "negative", "neutral", "mixed"]
    assert -1 <= output.score <= 1
    assert output.language in ["hi", "en", "mixed"]

# Test 3: Autonomous Meeting Intelligence
def test_meeting_endpoint():
    response = client.post("/api/meeting", json={"audio_path": "test_meeting.wav"})
    assert response.status_code == 200
    
    output = MeetingOutput(**response.json())
    assert isinstance(output.transcript, str)
    assert isinstance(output.tasks, list)
    assert isinstance(output.summary, str)

# Test 4: Indic Vision-Language Invoice Parser
def test_invoice_endpoint():
    response = client.post("/api/invoice", json={"image_path": "test_invoice.png"})
    assert response.status_code == 200
    
    output = InvoiceOutput(**response.json())
    assert len(output.gstin) == 15  # GSTIN format
    assert isinstance(output.hsn_codes, list)
    assert output.total_amount >= 0
    assert 0 <= output.confidence <= 1

# Test 5: Corporate KYC NER Extractor
def test_kyc_endpoint():
    response = client.post("/api/kyc", json={"document_text": "PAN: ABCDE1234F, Aadhaar: 1234-5678-9012"})
    assert response.status_code == 200
    
    output = KYCOutput(**response.json())
    assert len(output.pan) == 10  # PAN format
    assert len(output.aadhaar) == 14  # Aadhaar format with dashes
    assert isinstance(output.entities, dict)
    assert 0 <= output.confidence <= 1

# Test 6: Agentic SLA Breach Predictor
def test_sla_endpoint():
    test_data = {
        "service_data": {
            "response_time": 150,
            "uptime": 99.5,
            "ticket_count": 25,
            "customer_satisfaction": 4.2
        }
    }
    response = client.post("/api/sla", json=test_data)
    assert response.status_code == 200
    
    output = SLAOutput(**response.json())
    assert 0 <= output.risk_score <= 1
    assert 0 <= output.breach_probability <= 1
    assert isinstance(output.factors, list)

# Test 7: Enterprise RAG Memory
def test_rag_endpoint():
    response = client.post("/api/rag", json={"query": "GST filing due dates for MSME"})
    assert response.status_code == 200
    
    output = RAGOutput(**response.json())
    assert isinstance(output.answer, str)
    assert isinstance(output.sources, list)
    assert 0 <= output.relevance <= 1

# Test 8: GSTIN Fuzzy-Matching Reconciler
def test_gstin_endpoint():
    response = client.post("/api/gstin", json={"vendor_name": "Reliance Industries Limited"})
    assert response.status_code == 200
    
    output = GSTINOutput(**response.json())
    assert isinstance(output.matches, list)
    assert isinstance(output.best_match, dict)
    assert 0 <= output.confidence <= 1

# Test 9: Zero-Cost Cryptographic Audit Trail
def test_audit_endpoint():
    test_payload = {"action": "invoice_processed", "amount": 15000, "vendor": "Test Corp"}
    response = client.post("/api/audit", json={"payload": test_payload})
    assert response.status_code == 200
    
    output = AuditOutput(**response.json())
    assert isinstance(output.hash, str)
    assert isinstance(output.merkle_root, str)
    assert isinstance(output.timestamp, str)
    assert isinstance(output.receipt, str)

# Test edge cases and error handling
def test_error_handling():
    # Test malformed JSON
    response = client.post("/api/code-mixed", data="invalid json")
    assert response.status_code == 422
    
    # Test missing required fields
    response = client.post("/api/sentiment", json={})
    assert response.status_code == 422
    
    # Test network latency simulation (should timeout gracefully)
    import time
    start_time = time.time()
    response = client.post("/api/rag", json={"query": "test"}, timeout=5.0)
    end_time = time.time()
    
    # Should either succeed quickly or timeout gracefully
    assert response.status_code in [200, 408, 500]
    assert end_time - start_time < 10  # Should not hang indefinitely

if __name__ == "__main__":
    pytest.main([__file__])
