from typing import TypedDict, Dict, Any, List
from langgraph.graph import StateGraph, END
from rag.engine import retrieve_relevant_context, generate_safety_explanation

# Define State Structure
class AgentState(TypedDict):
    flight_id: int
    raw_telemetry: Dict[str, Any]
    risk_prediction: str
    risk_score: float
    contributing_factors: Dict[str, Any]
    retrieved_docs: List[Dict[str, Any]]
    safety_advisory: str
    warnings: List[str]

# 1. Anomaly Investigation Node
def anomaly_investigator(state: AgentState) -> Dict[str, Any]:
    telemetry = state.get("raw_telemetry", {})
    warnings = []
    
    # Check flight telemetry bounds
    if telemetry.get("max_temp", 0) > 900.0:
        warnings.append("High Temperature threshold exceeded (>900C)")
    if telemetry.get("min_oil", 100) < 40.0:
        warnings.append("Low Oil Pressure threshold breached (<40 PSI)")
    if telemetry.get("max_vib", 0) > 0.8:
        warnings.append("Elevated Rotor/Airframe Vibration detected (>0.8g)")
    if telemetry.get("min_hyd", 5000) < 2800.0:
        warnings.append("Hydraulic Actuation Pressure drop (<2800 PSI)")
        
    return {"warnings": warnings}

# 2. Knowledge Retrieval Node (RAG)
def knowledge_retriever(state: AgentState) -> Dict[str, Any]:
    warnings = state.get("warnings", [])
    retrieved = []
    
    # Query knowledge base using warning terms
    query_string = " ".join(warnings) if warnings else "standard flight safety"
    docs = retrieve_relevant_context(query_string, top_k=2)
    
    return {"retrieved_docs": docs}

# 3. Report Compiler Node
def report_compiler(state: AgentState) -> Dict[str, Any]:
    risk_prediction = state.get("risk_prediction", "Low")
    factors = state.get("contributing_factors", {})
    retrieved = state.get("retrieved_docs", [])
    
    doc_context = "\n".join([f"[{d['id']}] {d['title']}: {d['content']}" for d in retrieved])
    advisory = generate_safety_explanation(risk_prediction, factors, doc_context)
    
    return {"safety_advisory": advisory}

# Define conditional route based on risk level
def should_investigate(state: AgentState) -> str:
    # If prediction is Medium, High, or Critical, route to retrieval & explanations, otherwise finish
    risk = state.get("risk_prediction", "Low")
    if risk in ["Medium", "High", "Critical"]:
        return "investigate"
    return "finish"

# Build LangGraph StateMachine
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("investigator", anomaly_investigator)
workflow.add_node("retriever", knowledge_retriever)
workflow.add_node("compiler", report_compiler)

# Define Connections
workflow.set_entry_point("investigator")
workflow.add_edge("investigator", "retriever")
workflow.add_edge("retriever", "compiler")
workflow.add_edge("compiler", END)

# Compile Graph
graph = workflow.compile()
