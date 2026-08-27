from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import joblib
import os
import pandas as pd
from typing import List, Dict, Any

from database.connection import get_db, Base, engine
from database.models import Aircraft, Flight, MaintenanceEvent, SensorReading, Incident, RiskPrediction
from pipeline.features import extract_features
from agents.workflow import graph

app = FastAPI(
    title="AeroSafe AI - Aviation Safety Analytics & Risk Prediction",
    description="Backend API for predicting flight safety risks, analyzing maintenance logs, and retrieval-augmented safety explanations.",
    version="1.0.0"
)

# Load ML models on start
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pipeline", "models", "risk_classifier.pkl")
METADATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pipeline", "models", "model_metadata.pkl")

model = None
metadata = None

if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
if os.path.exists(METADATA_PATH):
    metadata = joblib.load(METADATA_PATH)

from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
def read_root():
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>AeroSafe AI API Online</h1>"


# Airline Prefix Mapping Helper
def get_airline_name(flight_number: str) -> str:
    prefix = flight_number[:2]
    mapping = {
        "AI": "Air India",
        "6E": "IndiGo",
        "UK": "Vistara",
        "SG": "SpiceJet",
        "G8": "GoFirst",
        "AS": "AeroSafe Airways"
    }
    return mapping.get(prefix, "AeroSafe Airways")

# 1. API to list flights
@app.get("/flights", response_model=List[Dict[str, Any]])
def list_flights(db: Session = Depends(get_db)):
    flights = db.query(Flight).all()
    result = []
    from pipeline.distances import get_distance, get_airport_name
    for f in flights:
        dist_km = get_distance(f.origin, f.destination)
        result.append({
            "id": f.id,
            "flight_number": f.flight_number,
            "airline_name": get_airline_name(f.flight_number),
            "origin": f.origin,
            "origin_full": get_airport_name(f.origin),
            "destination": f.destination,
            "destination_full": get_airport_name(f.destination),
            "departure_time": f.departure_time,
            "arrival_time": f.arrival_time,
            "flight_duration_hours": f.flight_duration_hours,
            "delay_minutes": f.delay_minutes,
            "status": f.status,
            "distance_km": dist_km,
            "aircraft_model": f.aircraft.model if f.aircraft else "Unknown"
        })
    return result

# 2. Get specific flight details & telemetry
@app.get("/flights/{flight_id}", response_model=Dict[str, Any])
def get_flight(flight_id: int, db: Session = Depends(get_db)):
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    
    # Get telemetry
    telemetries = db.query(SensorReading).filter(SensorReading.flight_id == flight_id).all()
    sensor_logs = [{
        "timestamp": t.timestamp,
        "engine_temp_c": t.engine_temp_c,
        "oil_pressure_psi": t.oil_pressure_psi,
        "vibration_amplitude_g": t.vibration_amplitude_g,
        "hydraulic_pressure_psi": t.hydraulic_pressure_psi,
        "fuel_flow_rate_gph": t.fuel_flow_rate_gph,
        "altitude_ft": t.altitude_ft
    } for t in telemetries]
    
    from pipeline.distances import get_distance, get_airport_name
    dist_km = get_distance(flight.origin, flight.destination)
    
    return {
        "id": flight.id,
        "flight_number": flight.flight_number,
        "airline_name": get_airline_name(flight.flight_number),
        "origin": flight.origin,
        "origin_full": get_airport_name(flight.origin),
        "destination": flight.destination,
        "destination_full": get_airport_name(flight.destination),
        "departure_time": flight.departure_time,
        "arrival_time": flight.arrival_time,
        "flight_duration_hours": flight.flight_duration_hours,
        "delay_minutes": flight.delay_minutes,
        "distance_km": dist_km,
        "aircraft_model": flight.aircraft.model if flight.aircraft else "Unknown",
        "telemetry": sensor_logs
    }

# 3. Generate risk prediction for a flight using Scikit-Learn classifier
@app.post("/flights/{flight_id}/predict", response_model=Dict[str, Any])
def predict_flight_risk(flight_id: int, db: Session = Depends(get_db)):
    if not model or not metadata:
        raise HTTPException(status_code=500, detail="ML Pipeline model artifacts not loaded. Please train the model first.")
        
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
        
    # Extract features for all flights, filter for specific flight
    df_features = extract_features(db)
    flight_feat = df_features[df_features["id"] == flight_id]
    
    if flight_feat.empty:
        raise HTTPException(status_code=400, detail="Insufficient sensor or maintenance features to predict risk for this flight.")
        
    feature_names = metadata["feature_names"]
    X = flight_feat[feature_names]
    
    # Predict
    pred_class = model.predict(X)[0]
    # Predict Probabilities
    probs = model.predict_proba(X)[0]
    class_idx = metadata["classes"].index(pred_class)
    risk_score = float(probs[class_idx] * 10.0) # Scale score out of 10
    
    # Get top contributing factors
    factors = {}
    row_feat = X.iloc[0]
    importances = metadata["importances"]
    for k in feature_names:
        if "anomaly" in k or k == "past_incidents":
            if row_feat[k] > 0:
                factors[k] = float(row_feat[k] * importances[k])
                
    # Save Prediction Result to database
    db_pred = db.query(RiskPrediction).filter(RiskPrediction.flight_id == flight_id).first()
    if not db_pred:
        db_pred = RiskPrediction(
            flight_id=flight_id,
            predicted_risk_level=pred_class,
            risk_score=risk_score,
            contributing_factors=str(factors)
        )
        db.add(db_pred)
    else:
        db_pred.predicted_risk_level = pred_class
        db_pred.risk_score = risk_score
        db_pred.contributing_factors = str(factors)
        
    db.commit()
    db.refresh(db_pred)
    
    return {
        "flight_id": flight_id,
        "predicted_risk_level": pred_class,
        "risk_score": round(risk_score, 2),
        "contributing_factors": factors
    }

# 4. Trigger LangGraph Agentic Workflow for Explainable Safety Insight
@app.post("/flights/{flight_id}/safety-analysis", response_model=Dict[str, Any])
def run_agentic_safety_analysis(flight_id: int, db: Session = Depends(get_db)):
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
        
    # Get ML prediction
    db_pred = db.query(RiskPrediction).filter(RiskPrediction.flight_id == flight_id).first()
    if not db_pred:
        # Auto-predict if prediction doesn't exist yet
        pred_res = predict_flight_risk(flight_id, db)
        db_pred = db.query(RiskPrediction).filter(RiskPrediction.flight_id == flight_id).first()
        
    from sqlalchemy import text
    query_sensors = """
        SELECT MAX(engine_temp_c) as max_temp,
               MIN(oil_pressure_psi) as min_oil,
               MAX(vibration_amplitude_g) as max_vib,
               MIN(hydraulic_pressure_psi) as min_hyd
        FROM sensor_readings
        WHERE flight_id = :fid
    """
    sensor_summary = db.execute(
        text(query_sensors), 
        {"fid": flight_id}
    ).fetchone()
    
    telemetry_dict = {
        "max_temp": float(sensor_summary[0]) if sensor_summary and sensor_summary[0] else 820.0,
        "min_oil": float(sensor_summary[1]) if sensor_summary and sensor_summary[1] else 55.0,
        "max_vib": float(sensor_summary[2]) if sensor_summary and sensor_summary[2] else 0.35,
        "min_hyd": float(sensor_summary[3]) if sensor_summary and sensor_summary[3] else 3000.0
    }
    
    # Initialize LangGraph State
    initial_state = {
        "flight_id": flight_id,
        "raw_telemetry": telemetry_dict,
        "risk_prediction": db_pred.predicted_risk_level,
        "risk_score": db_pred.risk_score,
        "contributing_factors": eval(db_pred.contributing_factors) if db_pred.contributing_factors else {},
        "retrieved_docs": [],
        "safety_advisory": "",
        "warnings": []
    }
    
    # Run the compiled LangGraph workflow state machine
    final_output = graph.invoke(initial_state)
    
    # Update prediction record with explainable advisory
    db_pred.explanation = final_output.get("safety_advisory", "")
    db.commit()
    
    return {
        "flight_id": flight_id,
        "risk_level": db_pred.predicted_risk_level,
        "warnings": final_output.get("warnings", []),
        "retrieved_docs_count": len(final_output.get("retrieved_docs", [])),
        "safety_advisory": db_pred.explanation
    }
