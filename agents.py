from langgraph import StateGraph, END
from langchain_groq import ChatGroq
from pydantic import BaseModel
from typing import Dict, Any, List
import json
import re
from datetime import datetime

class AgentState(BaseModel):
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    error_count: int = 0
    max_retries: int = 3
    reflection_needed: bool = False
    last_error: str = ""

class SelfHealingAgent:
    def __init__(self, groq_api_key: str = None):
        # Initialize Groq LLM for self-healing
        self.llm = ChatGroq(
            model="llama3-8b-8192",
            api_key=groq_api_key or "dummy-key",  # Will use env var in production
            temperature=0.1
        )
        
        # Create the state graph
        self.workflow = StateGraph(AgentState)
        
        # Add nodes
        self.workflow.add_node("process_input", self.process_input)
        self.workflow.add_node("validate_output", self.validate_output)
        self.workflow.add_node("reflection", self.reflection_node)
        self.workflow.add_node("retry", self.retry_node)
        
        # Add edges
        self.workflow.set_entry_point("process_input")
        self.workflow.add_edge("process_input", "validate_output")
        self.workflow.add_conditional_edges(
            "validate_output",
            self.decide_next_step,
            {
                "success": END,
                "reflection": "reflection",
                "retry": "retry"
            }
        )
        self.workflow.add_edge("reflection", "retry")
        self.workflow.add_edge("retry", "process_input")
        
        # Compile the graph
        self.app = self.workflow.compile()
    
    def process_input(self, state: AgentState) -> AgentState:
        """Main processing node for different agent types"""
        try:
            input_type = state.input_data.get("type", "")
            
            if input_type == "code_mixed":
                state.output_data = self._process_code_mixed(state.input_data)
            elif input_type == "sentiment":
                state.output_data = self._process_sentiment(state.input_data)
            elif input_type == "kyc":
                state.output_data = self._process_kyc(state.input_data)
            elif input_type == "sla":
                state.output_data = self._process_sla(state.input_data)
            elif input_type == "rag":
                state.output_data = self._process_rag(state.input_data)
            elif input_type == "gstin":
                state.output_data = self._process_gstin(state.input_data)
            elif input_type == "audit":
                state.output_data = self._process_audit(state.input_data)
            else:
                raise ValueError(f"Unknown input type: {input_type}")
                
            state.error_count = 0  # Reset on success
            state.reflection_needed = False
            
        except Exception as e:
            state.last_error = str(e)
            state.error_count += 1
            state.reflection_needed = True
            
        return state
    
    def validate_output(self, state: AgentState) -> AgentState:
        """Validate the output against expected schema"""
        try:
            output = state.output_data
            
            # Basic validation checks
            if not isinstance(output, dict):
                raise ValueError("Output must be a dictionary")
            
            # Type-specific validation
            input_type = state.input_data.get("type", "")
            
            if input_type == "code_mixed":
                self._validate_code_mixed_output(output)
            elif input_type == "sentiment":
                self._validate_sentiment_output(output)
            elif input_type == "kyc":
                self._validate_kyc_output(output)
            elif input_type == "sla":
                self._validate_sla_output(output)
            elif input_type == "rag":
                self._validate_rag_output(output)
            elif input_type == "gstin":
                self._validate_gstin_output(output)
            elif input_type == "audit":
                self._validate_audit_output(output)
                
            state.reflection_needed = False
            
        except Exception as e:
            state.last_error = f"Validation error: {str(e)}"
            state.reflection_needed = True
            
        return state
    
    def reflection_node(self, state: AgentState) -> AgentState:
        """Self-healing reflection node"""
        try:
            if state.error_count >= state.max_retries:
                state.output_data = {
                    "error": "Max retries exceeded",
                    "last_error": state.last_error,
                    "fallback_response": self._get_fallback_response(state.input_data)
                }
                return state
            
            # Use LLM to diagnose and suggest fixes
            reflection_prompt = f"""
            Error occurred: {state.last_error}
            Input data: {json.dumps(state.input_data, indent=2)}
            Error count: {state.error_count}
            
            Please analyze this error and suggest a fix. The error might be:
            1. Schema mismatch
            2. Data format issue  
            3. Missing required fields
            4. Invalid data types
            
            Provide a JSON response with:
            {{
                "diagnosis": "what went wrong",
                "suggested_fix": "how to fix it",
                "corrected_input": "the corrected input data"
            }}
            """
            
            # In production, this would call the actual LLM
            # For now, we'll implement simple self-healing logic
            
            diagnosis = self._diagnose_error(state.last_error, state.input_data)
            suggested_fix = diagnosis.get("fix", "Retry with default values")
            corrected_input = diagnosis.get("corrected_input", state.input_data)
            
            state.input_data = corrected_input
            state.last_error = f"Reflection: {diagnosis['issue']}"
            
        except Exception as e:
            state.last_error = f"Reflection error: {str(e)}"
            
        return state
    
    def retry_node(self, state: AgentState) -> AgentState:
        """Retry processing with corrected input"""
        return state
    
    def decide_next_step(self, state: AgentState) -> str:
        """Decide the next step based on current state"""
        if state.reflection_needed:
            if state.error_count == 1:
                return "reflection"
            elif state.error_count < state.max_retries:
                return "retry"
            else:
                # Max retries exceeded, return success with error info
                state.output_data = {
                    "error": "Max retries exceeded",
                    "last_error": state.last_error,
                    "fallback_response": self._get_fallback_response(state.input_data)
                }
                return "success"
        else:
            return "success"
    
    # Processing methods for different agent types
    def _process_code_mixed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        text = data.get("text", "").lower()
        
        # Enhanced intent classification with error handling
        intents = {
            "procurement": ["procurement", "karna", "buy", "purchase", "lena", "order"],
            "payment": ["payment", "bhugtan", "dena", "pay", "settle"],
            "compliance": ["compliance", "gst", "tax", "return", "file"],
            "inventory": ["inventory", "stock", "mal", "jama", "store"]
        }
        
        intent_scores = {}
        for intent, keywords in intents.items():
            score = sum(1 for keyword in keywords if keyword in text)
            intent_scores[intent] = score / len(keywords) if keywords else 0
        
        best_intent = max(intent_scores, key=intent_scores.get) if intent_scores else "unknown"
        confidence = max(intent_scores.values()) if intent_scores else 0.0
        
        return {
            "intent": best_intent if confidence > 0.1 else "unknown",
            "confidence": min(confidence, 1.0),
            "language": self._detect_language(text)
        }
    
    def _process_sentiment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        text = data.get("text", "").lower()
        
        positive_words = ["achha", "good", "excellent", "badhiya", "perfect", "great", "amazing"]
        negative_words = ["bad", "kharab", "slow", "problem", "issue", "terrible", "awful"]
        
        pos_count = sum(1 for word in positive_words if word in text.split())
        neg_count = sum(1 for word in negative_words if word in text.split())
        
        if pos_count > neg_count:
            sentiment = "positive"
            score = min((pos_count - neg_count) / max(len(text.split()), 1), 1.0)
        elif neg_count > pos_count:
            sentiment = "negative"
            score = max((pos_count - neg_count) / max(len(text.split()), 1), -1.0)
        else:
            sentiment = "neutral"
            score = 0.0
        
        return {
            "sentiment": sentiment,
            "score": score,
            "language": self._detect_language(text)
        }
    
    def _process_kyc(self, data: Dict[str, Any]) -> Dict[str, Any]:
        text = data.get("document_text", "")
        
        # Enhanced pattern matching
        pan_match = re.search(r'[A-Z]{5}[0-9]{4}[A-Z]{1}', text.upper())
        aadhaar_match = re.search(r'\d{4}[-\s]?\d{4}[-\s]?\d{4}', text.replace(' ', ''))
        
        pan = pan_match.group() if pan_match else ""
        aadhaar = aadhaar_match.group().replace(' ', '-') if aadhaar_match else ""
        
        entities = {
            "pan": pan,
            "aadhaar": aadhaar,
            "name": self._extract_name(text),
            "document_type": "identity_proof"
        }
        
        return {
            "pan": pan,
            "aadhaar": aadhaar,
            "entities": entities,
            "confidence": 0.85 if pan and aadhaar else 0.60
        }
    
    def _process_sla(self, data: Dict[str, Any]) -> Dict[str, Any]:
        service_data = data.get("service_data", {})
        
        response_time = service_data.get("response_time", 100)
        uptime = service_data.get("uptime", 99.0)
        ticket_count = service_data.get("ticket_count", 10)
        satisfaction = service_data.get("customer_satisfaction", 4.0)
        
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
        
        return {
            "risk_score": min(risk_score, 1.0),
            "breach_probability": min(risk_score, 1.0),
            "factors": factors
        }
    
    def _process_rag(self, data: Dict[str, Any]) -> Dict[str, Any]:
        query = data.get("query", "").lower()
        
        # Enhanced knowledge base
        knowledge = {
            "gst": "GST returns are due on the 20th of each month for MSMEs with turnover up to ₹5 crore.",
            "filing": "Quarterly GSTR-1 and monthly GSTR-3B filing is mandatory for registered businesses.",
            "due": "Late filing attracts penalty of ₹50 per day for GSTR-3B and ₹200 per day for GSTR-1.",
            "penalty": "Penalty for late GST filing can range from ₹50 to ₹200 per day depending on the form type."
        }
        
        answer = "Based on your query about GST compliance: "
        if any(keyword in query for keyword in ["gst", "return"]):
            answer += knowledge["gst"]
        elif "filing" in query:
            answer += knowledge["filing"]
        elif any(keyword in query for keyword in ["due", "deadline"]):
            answer += knowledge["due"]
        elif "penalty" in query:
            answer += knowledge["penalty"]
        else:
            answer = "I found information about GST compliance requirements for MSMEs. Please specify your query about filing dates, due amounts, or penalties."
        
        return {
            "answer": answer,
            "sources": ["GST Act 2017", "CBIC Circular No. 206/2023"],
            "relevance": 0.85
        }
    
    def _process_gstin(self, data: Dict[str, Any]) -> Dict[str, Any]:
        vendor_name = data.get("vendor_name", "").lower()
        
        vendors = [
            {"name": "Reliance Industries Limited", "gstin": "27AAACR1674C1ZV", "score": 0.95},
            {"name": "Tata Consultancy Services", "gstin": "27AAACT2915E1ZT", "score": 0.92},
            {"name": "Infosys Limited", "gstin": "29AAACI2915E1ZY", "score": 0.88},
        ]
        
        matches = []
        for vendor in vendors:
            # Enhanced similarity calculation
            vendor_words = set(vendor["name"].lower().split())
            input_words = set(vendor_name.split())
            
            intersection = vendor_words & input_words
            union = vendor_words | input_words
            
            similarity = len(intersection) / len(union) if union else 0
            
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
        
        return {
            "matches": matches,
            "best_match": best_match,
            "confidence": confidence
        }
    
    def _process_audit(self, data: Dict[str, Any]) -> Dict[str, Any]:
        import hashlib
        import uuid
        
        payload = data.get("payload", {})
        payload_str = json.dumps(payload, sort_keys=True)
        
        payload_hash = hashlib.sha256(payload_str.encode()).hexdigest()
        merkle_root = hashlib.sha256((payload_hash + str(uuid.uuid4())).encode()).hexdigest()
        
        return {
            "hash": payload_hash,
            "merkle_root": merkle_root,
            "timestamp": datetime.utcnow().isoformat(),
            "receipt": f"AUDIT_{uuid.uuid4().hex[:16]}"
        }
    
    # Helper methods
    def _detect_language(self, text: str) -> str:
        hinglish_words = ["mujhe", "hai", "karna", "bahut", "achha", "liye", "ke", "ka", "ki", "mein", "ko", "se", "par"]
        words = text.lower().split()
        hinglish_count = sum(1 for word in words if word in hinglish_words)
        
        if hinglish_count > len(words) * 0.3:
            return "mixed"
        elif hinglish_count > 0:
            return "hi"
        else:
            return "en"
    
    def _extract_name(self, text: str) -> str:
        # Simple name extraction - in production would use NER
        import re
        name_patterns = [
            r'Name[:\s]+([A-Za-z\s]+)',
            r'([A-Z][a-z]+\s[A-Z][a-z]+)',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        return "Unknown"
    
    def _diagnose_error(self, error: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simple error diagnosis logic"""
        error_lower = error.lower()
        
        if "validation" in error_lower:
            return {
                "issue": "Schema validation failed",
                "fix": "Ensure all required fields are present and correctly typed",
                "corrected_input": self._sanitize_input(input_data)
            }
        elif "type" in error_lower:
            return {
                "issue": "Data type mismatch",
                "fix": "Convert data to expected types",
                "corrected_input": self._convert_types(input_data)
            }
        elif "missing" in error_lower:
            return {
                "issue": "Missing required fields",
                "fix": "Add missing fields with default values",
                "corrected_input": self._add_defaults(input_data)
            }
        else:
            return {
                "issue": "Unknown error",
                "fix": "Retry with sanitized input",
                "corrected_input": self._sanitize_input(input_data)
            }
    
    def _sanitize_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize input data"""
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = value.strip()[:1000]  # Limit length
            else:
                sanitized[key] = value
        return sanitized
    
    def _convert_types(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert data types to expected formats"""
        converted = data.copy()
        
        # Convert string numbers to actual numbers
        if "service_data" in converted and isinstance(converted["service_data"], dict):
            for key, value in converted["service_data"].items():
                if isinstance(value, str) and value.isdigit():
                    converted["service_data"][key] = int(value)
                elif isinstance(value, str) and self._is_float(value):
                    converted["service_data"][key] = float(value)
        
        return converted
    
    def _add_defaults(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add default values for missing fields"""
        defaults = {
            "text": "",
            "vendor_name": "Unknown Vendor",
            "document_text": "",
            "query": "",
            "payload": {},
            "service_data": {
                "response_time": 100,
                "uptime": 99.0,
                "ticket_count": 10,
                "customer_satisfaction": 4.0
            }
        }
        
        for key, default_value in defaults.items():
            if key not in data:
                data[key] = default_value
        
        return data
    
    def _is_float(self, value: str) -> bool:
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def _get_fallback_response(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get fallback response when all retries fail"""
        input_type = input_data.get("type", "unknown")
        
        fallbacks = {
            "code_mixed": {"intent": "unknown", "confidence": 0.0, "language": "en"},
            "sentiment": {"sentiment": "neutral", "score": 0.0, "language": "en"},
            "kyc": {"pan": "", "aadhaar": "", "entities": {}, "confidence": 0.0},
            "sla": {"risk_score": 0.5, "breach_probability": 0.5, "factors": ["Unable to calculate"]},
            "rag": {"answer": "Unable to process query", "sources": [], "relevance": 0.0},
            "gstin": {"matches": [], "best_match": {}, "confidence": 0.0},
            "audit": {"hash": "", "merkle_root": "", "timestamp": "", "receipt": ""}
        }
        
        return fallbacks.get(input_type, {"error": "Unknown input type"})
    
    # Validation methods
    def _validate_code_mixed_output(self, output: Dict[str, Any]):
        required_fields = ["intent", "confidence", "language"]
        for field in required_fields:
            if field not in output:
                raise ValueError(f"Missing required field: {field}")
        
        if not isinstance(output["confidence"], (int, float)) or not (0 <= output["confidence"] <= 1):
            raise ValueError("Confidence must be a number between 0 and 1")
    
    def _validate_sentiment_output(self, output: Dict[str, Any]):
        required_fields = ["sentiment", "score", "language"]
        for field in required_fields:
            if field not in output:
                raise ValueError(f"Missing required field: {field}")
        
        valid_sentiments = ["positive", "negative", "neutral", "mixed"]
        if output["sentiment"] not in valid_sentiments:
            raise ValueError(f"Invalid sentiment: {output['sentiment']}")
        
        if not isinstance(output["score"], (int, float)) or not (-1 <= output["score"] <= 1):
            raise ValueError("Score must be a number between -1 and 1")
    
    def _validate_kyc_output(self, output: Dict[str, Any]):
        required_fields = ["pan", "aadhaar", "entities", "confidence"]
        for field in required_fields:
            if field not in output:
                raise ValueError(f"Missing required field: {field}")
        
        if not isinstance(output["entities"], dict):
            raise ValueError("Entities must be a dictionary")
    
    def _validate_sla_output(self, output: Dict[str, Any]):
        required_fields = ["risk_score", "breach_probability", "factors"]
        for field in required_fields:
            if field not in output:
                raise ValueError(f"Missing required field: {field}")
        
        if not isinstance(output["factors"], list):
            raise ValueError("Factors must be a list")
    
    def _validate_rag_output(self, output: Dict[str, Any]):
        required_fields = ["answer", "sources", "relevance"]
        for field in required_fields:
            if field not in output:
                raise ValueError(f"Missing required field: {field}")
        
        if not isinstance(output["sources"], list):
            raise ValueError("Sources must be a list")
    
    def _validate_gstin_output(self, output: Dict[str, Any]):
        required_fields = ["matches", "best_match", "confidence"]
        for field in required_fields:
            if field not in output:
                raise ValueError(f"Missing required field: {field}")
        
        if not isinstance(output["matches"], list):
            raise ValueError("Matches must be a list")
    
    def _validate_audit_output(self, output: Dict[str, Any]):
        required_fields = ["hash", "merkle_root", "timestamp", "receipt"]
        for field in required_fields:
            if field not in output:
                raise ValueError(f"Missing required field: {field}")
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the agent with input data"""
        initial_state = AgentState(
            input_data=input_data,
            output_data={},
            error_count=0,
            max_retries=3,
            reflection_needed=False,
            last_error=""
        )
        
        result = self.app.invoke(initial_state)
        return result.output_data
