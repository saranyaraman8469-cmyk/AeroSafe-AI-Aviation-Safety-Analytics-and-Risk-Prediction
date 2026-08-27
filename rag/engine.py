import os
import json
import numpy as np
from config.settings import settings

# Load Local KB Documents
KB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kb_documents.json")

def load_kb():
    if os.path.exists(KB_PATH):
        with open(KB_PATH, "r") as f:
            return json.load(f)
    return []

# Simple keyword TF-IDF match / cosine-similarity mockup for embedding RAG
# to keep the environment lightweight and fully reproducible without requiring internet/huge models
def retrieve_relevant_context(query: str, top_k: int = 2) -> list:
    kb_docs = load_kb()
    if not kb_docs:
        return []
    
    # Calculate simple word overlap score as retrieval mechanism
    query_words = set(query.lower().split())
    scored_docs = []
    
    for doc in kb_docs:
        doc_words = set(doc["content"].lower().split() + doc["title"].lower().split())
        overlap = len(query_words.intersection(doc_words))
        scored_docs.append((overlap, doc))
        
    # Sort by overlap score descending
    scored_docs.sort(key=lambda x: x[0], reverse=True)
    return [doc for score, doc in scored_docs[:top_k]]

def generate_safety_explanation(risk_level: str, factors: dict, query_context: str = "") -> str:
    """
    Generates explainable AI details.
    Uses Google Gemini API if GEMINI_API_KEY is available,
    otherwise falls back to a deterministic, structured expert rule-engine explanation.
    """
    api_key = settings.GEMINI_API_KEY
    
    prompt = (
        f"AeroSafe AI System Alert:\n"
        f"Flight Risk Classification: {risk_level}\n"
        f"Contributing Safety Factors: {json.dumps(factors, indent=2)}\n"
        f"Retrieved Aviation Safety Procedures: {query_context}\n\n"
        f"Instructions: Draft a professional aviation safety advisory detailing the risks, "
        f"contributing factors, and specific maintenance/operational recommendations."
    )
    
    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return generate_fallback_explanation(risk_level, factors, query_context) + f"\n\n(Note: Gemini LLM call failed: {e})"
    else:
        return generate_fallback_explanation(risk_level, factors, query_context)

def generate_fallback_explanation(risk_level: str, factors: dict, query_context: str) -> str:
    """Expert rule-based fallback explaining contributing risk factors and referencing RAG documentation."""
    explanation_lines = [
        f"--- AeroSafe AI Safety Advisory [DETERMINISTIC ANALYSIS] ---",
        f"Predicted Operational Risk Level: {risk_level.upper()}",
        f"\nTriggered Anomalies / Factors:",
    ]
    
    has_triggers = False
    for factor, value in factors.items():
        if value > 0:
            explanation_lines.append(f"  - {factor}: Triggered (Value/Weight: {value})")
            has_triggers = True
            
    if not has_triggers:
        explanation_lines.append("  - No immediate flight telemetry anomalies or incident histories detected.")
        
    explanation_lines.append("\nSafety Documentation References:")
    if query_context:
        explanation_lines.append(f"  Context retrieved from RAG system:\n  {query_context}")
    else:
        explanation_lines.append("  No specific knowledge base context was queried or matched.")
        
    explanation_lines.append("\nRecommended Corrective Operations:")
    if risk_level in ["High", "Critical"]:
        explanation_lines.append("  [CRITICAL] Ground flight operations. Require complete component inspection and airworthiness release cert.")
    elif risk_level == "Medium":
        explanation_lines.append("  [WARNING] Monitor telemetry closely. Schedule preventive diagnostic checks before the next flight leg.")
    else:
        explanation_lines.append("  [INFO] Routine operations authorized. Normal flight schedule maintenance cycles apply.")
        
    return "\n".join(explanation_lines)
