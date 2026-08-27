import sys
import os
# Adjust path to import correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from database.connection import SessionLocal
from pipeline.features import extract_features, label_risk

# Model save directory
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
os.makedirs(MODEL_DIR, exist_ok=True)

def train_risk_model():
    print("Extracting features from database...")
    db = SessionLocal()
    df = extract_features(db)
    db.close()
    
    if df.empty or len(df) < 5:
        print("Not enough flight records to train ML pipeline. Ingest data first.")
        return

    # Add Target labels based on risk score indicator
    df["risk_level"] = df["operational_risk_score"].apply(label_risk)
    
    # Feature columns mapping
    feature_cols = [
        "flight_duration_hours", 
        "delay_minutes", 
        "total_flight_hours", 
        "manufacture_year", 
        "maint_count", 
        "total_maint_cost", 
        "avg_temp", 
        "max_temp", 
        "avg_oil", 
        "min_oil", 
        "avg_vib", 
        "max_vib", 
        "avg_hyd", 
        "min_hyd", 
        "past_incidents", 
        "temp_anomaly", 
        "oil_pressure_anomaly", 
        "vib_anomaly", 
        "hyd_anomaly",
        "operational_risk_score"
    ]
    
    X = df[feature_cols]
    y = df["risk_level"]
    
    # Perform clean train-test split (80/20) to prevent leakage
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"Dataset Split: {len(X_train)} train samples, {len(X_test)} test samples.")
    
    # Train Random Forest Classifier
    print("Training Random Forest Safety Risk Classifier...")
    model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42, class_weight="balanced")
    model.fit(X_train, y_train)
    
    # Evaluate model performance
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nModel Evaluation Metrics:")
    print(f"Accuracy: {accuracy:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # Feature Importance analysis
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    print("Top Influencing Factors:")
    for f in range(5):
        print(f"{f+1}. {feature_cols[indices[f]]} ({importances[indices[f]]:.4f})")
        
    # Save trained model pipeline and features columns metadata
    model_path = os.path.join(MODEL_DIR, "risk_classifier.pkl")
    metadata_path = os.path.join(MODEL_DIR, "model_metadata.pkl")
    
    joblib.dump(model, model_path)
    joblib.dump({
        "feature_names": feature_cols,
        "classes": model.classes_.tolist(),
        "importances": dict(zip(feature_cols, importances))
    }, metadata_path)
    
    print(f"\nModel artifacts successfully saved to {MODEL_DIR}")

if __name__ == "__main__":
    train_risk_model()
