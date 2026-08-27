# AeroSafe AI — Aviation Safety Analytics & Risk Prediction

AeroSafe AI is an end-to-end, AI-powered aviation safety analytics platform. It processes flight telemetry records, aircraft maintenance logs, and schedules to identify potential safety risks, predict operational risk levels, and generate explainable diagnostics.

## Features
- **Relational DB Storage**: Structured tracking of flights, aircraft engines, maintenance diagnostics, and telemetries.
- **ML Classifier**: Scikit-Learn RandomForest classifier categorizes flights into Low, Medium, High, and Critical risk profiles.
- **RAG & GenAI Layer**: Integrates dynamic retrieval of aviation operating thresholds and regulations to generate explainable AI safety advisories.
- **LangGraph Agents**: Stateful multi-agent workflow orchestrating the telemetry investigation, document retrieval, and report compiling.
- **Sleek HUD Dashboard**: Premium dashboard interface with Dark/Light theme toggle and real-time radar tracking display.

## Quick Start (Local Run)

1. **Install requirements**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Seed synthetic aviation data**:
   ```bash
   python pipeline/ingest.py
   ```
3. **Train risk prediction model**:
   ```bash
   python pipeline/model.py
   ```
4. **Launch backend server**:
   ```bash
   python -m uvicorn api.main:app --port 8080 --reload
   ```
5. **Access Dashboard**:
   Open browser at `http://127.0.0.1:8080/`
