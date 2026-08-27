from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database.connection import Base
import datetime

class Aircraft(Base):
    __tablename__ = "aircraft"

    id = Column(Integer, primary_key=True, index=True)
    tail_number = Column(String(50), unique=True, index=True, nullable=False)
    model = Column(String(100), nullable=False)
    manufacturer = Column(String(100), nullable=False)
    manufacture_year = Column(Integer, nullable=False)
    total_flight_hours = Column(Float, default=0.0)
    last_maintenance_date = Column(DateTime, nullable=True)

    flights = relationship("Flight", back_populates="aircraft")
    maintenance_events = relationship("MaintenanceEvent", back_populates="aircraft")

class Flight(Base):
    __tablename__ = "flights"

    id = Column(Integer, primary_key=True, index=True)
    flight_number = Column(String(50), nullable=False)
    aircraft_id = Column(Integer, ForeignKey("aircraft.id"), nullable=False)
    origin = Column(String(50), nullable=False)
    destination = Column(String(50), nullable=False)
    departure_time = Column(DateTime, nullable=False)
    arrival_time = Column(DateTime, nullable=False)
    flight_duration_hours = Column(Float, nullable=False)
    delay_minutes = Column(Float, default=0.0)
    status = Column(String(50), default="Completed")  # Scheduled, Active, Completed, Cancelled

    aircraft = relationship("Aircraft", back_populates="flights")
    sensor_readings = relationship("SensorReading", back_populates="flight")
    incidents = relationship("Incident", back_populates="flight")
    predictions = relationship("RiskPrediction", back_populates="flight")

class MaintenanceEvent(Base):
    __tablename__ = "maintenance_events"

    id = Column(Integer, primary_key=True, index=True)
    aircraft_id = Column(Integer, ForeignKey("aircraft.id"), nullable=False)
    event_date = Column(DateTime, default=datetime.datetime.utcnow)
    component_name = Column(String(100), nullable=False)  # Engine, Landing Gear, Avionics, etc.
    action_taken = Column(String(100), nullable=False)  # Inspection, Repair, Replacement
    technician_notes = Column(Text, nullable=True)
    cost = Column(Float, default=0.0)

    aircraft = relationship("Aircraft", back_populates="maintenance_events")

class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    flight_id = Column(Integer, ForeignKey("flights.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    engine_temp_c = Column(Float, nullable=False)
    oil_pressure_psi = Column(Float, nullable=False)
    vibration_amplitude_g = Column(Float, nullable=False)
    hydraulic_pressure_psi = Column(Float, nullable=False)
    fuel_flow_rate_gph = Column(Float, nullable=False)
    altitude_ft = Column(Float, nullable=False)

    flight = relationship("Flight", back_populates="sensor_readings")

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    flight_id = Column(Integer, ForeignKey("flights.id"), nullable=True)
    incident_date = Column(DateTime, nullable=False)
    severity_level = Column(String(50), nullable=False)  # Minor, Moderate, Major, Critical
    description = Column(Text, nullable=False)

    flight = relationship("Flight", back_populates="incidents")

class RiskPrediction(Base):
    __tablename__ = "risk_predictions"

    id = Column(Integer, primary_key=True, index=True)
    flight_id = Column(Integer, ForeignKey("flights.id"), nullable=False)
    prediction_time = Column(DateTime, default=datetime.datetime.utcnow)
    predicted_risk_level = Column(String(50), nullable=False)  # Low, Medium, High, Critical
    risk_score = Column(Float, nullable=False)
    contributing_factors = Column(Text, nullable=True)  # JSON-formatted string of features and weights
    explanation = Column(Text, nullable=True)

    flight = relationship("Flight", back_populates="predictions")
