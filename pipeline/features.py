import pandas as pd
import numpy as np

def extract_features(db_session):
    """
    Fetches raw flight data, maintenance frequency, sensor anomalies, and incidents 
    from the database and compiles a consolidated DataFrame for model training and inference.
    """
    # 1. Fetch Flights
    query_flights = "SELECT id, flight_number, aircraft_id, flight_duration_hours, delay_minutes FROM flights"
    df_flights = pd.read_sql_query(query_flights, db_session.bind)
    
    if df_flights.empty:
        return pd.DataFrame()

    # 2. Fetch Aircraft context
    query_aircraft = "SELECT id as aircraft_id, total_flight_hours, manufacture_year FROM aircraft"
    df_ac = pd.read_sql_query(query_aircraft, db_session.bind)
    df_flights = df_flights.merge(df_ac, on="aircraft_id", how="left")

    # 3. Calculate Maintenance Frequency & Cost per aircraft
    query_maint = """
        SELECT aircraft_id, 
               COUNT(id) as maint_count, 
               SUM(cost) as total_maint_cost 
        FROM maintenance_events 
        GROUP BY aircraft_id
    """
    df_maint = pd.read_sql_query(query_maint, db_session.bind)
    df_flights = df_flights.merge(df_maint, on="aircraft_id", how="left")
    df_flights["maint_count"] = df_flights["maint_count"].fillna(0)
    df_flights["total_maint_cost"] = df_flights["total_maint_cost"].fillna(0.0)

    # 4. Aggregated Sensor Readings (Average & Max/Min to catch spikes)
    query_sensors = """
        SELECT flight_id,
               AVG(engine_temp_c) as avg_temp,
               MAX(engine_temp_c) as max_temp,
               AVG(oil_pressure_psi) as avg_oil,
               MIN(oil_pressure_psi) as min_oil,
               AVG(vibration_amplitude_g) as avg_vib,
               MAX(vibration_amplitude_g) as max_vib,
               AVG(hydraulic_pressure_psi) as avg_hyd,
               MIN(hydraulic_pressure_psi) as min_hyd
        FROM sensor_readings
        GROUP BY flight_id
    """
    df_sensors = pd.read_sql_query(query_sensors, db_session.bind)
    df_flights = df_flights.merge(df_sensors, left_on="id", right_on="flight_id", how="left")

    # Fill sensor missing values with standard safe defaults if any flight lacks sensor readings
    df_flights["avg_temp"] = df_flights["avg_temp"].fillna(820.0)
    df_flights["max_temp"] = df_flights["max_temp"].fillna(820.0)
    df_flights["avg_oil"] = df_flights["avg_oil"].fillna(55.0)
    df_flights["min_oil"] = df_flights["min_oil"].fillna(55.0)
    df_flights["avg_vib"] = df_flights["avg_vib"].fillna(0.35)
    df_flights["max_vib"] = df_flights["max_vib"].fillna(0.35)
    df_flights["avg_hyd"] = df_flights["avg_hyd"].fillna(3000.0)
    df_flights["min_hyd"] = df_flights["min_hyd"].fillna(3000.0)

    # 5. Incident severity count (past incidents for this flight's aircraft)
    query_incidents = """
        SELECT f.aircraft_id, COUNT(i.id) as past_incidents
        FROM incidents i
        JOIN flights f ON i.flight_id = f.id
        GROUP BY f.aircraft_id
    """
    df_incidents = pd.read_sql_query(query_incidents, db_session.bind)
    df_flights = df_flights.merge(df_incidents, on="aircraft_id", how="left")
    df_flights["past_incidents"] = df_flights["past_incidents"].fillna(0)

    # 6. Engineer Safety Indicators
    # Anomalous sensor deviation indicators
    df_flights["temp_anomaly"] = (df_flights["max_temp"] > 900.0).astype(int)
    df_flights["oil_pressure_anomaly"] = (df_flights["min_oil"] < 40.0).astype(int)
    df_flights["vib_anomaly"] = (df_flights["max_vib"] > 0.8).astype(int)
    df_flights["hyd_anomaly"] = (df_flights["min_hyd"] < 2800.0).astype(int)
    
    # Combined operational risk score
    df_flights["operational_risk_score"] = (
        df_flights["temp_anomaly"] * 2.0 + 
        df_flights["oil_pressure_anomaly"] * 3.0 + 
        df_flights["vib_anomaly"] * 2.5 + 
        df_flights["hyd_anomaly"] * 2.0 +
        (df_flights["delay_minutes"] > 60).astype(int) * 1.0 +
        (df_flights["past_incidents"] > 0).astype(int) * 1.5
    )

    return df_flights

def label_risk(risk_score):
    """Deterministic labeling rule helper for synthetic risk prediction labeling."""
    if risk_score >= 6.0:
        return "Critical"
    elif risk_score >= 4.0:
        return "High"
    elif risk_score >= 1.5:
        return "Medium"
    else:
        return "Low"
