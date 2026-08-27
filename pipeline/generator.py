import random
import datetime

# Mock aircraft, routes, components, and notes
# Mock aircraft, routes, components, and notes
MODELS = ["Boeing 737-800", "Airbus A320neo", "Boeing 787-9", "Bombardier CRJ-900", "Airbus A350-900"]
AIRPORTS = ["JFK", "LAX", "ORD", "DFW", "ATL", "SFO", "MIA", "LHR", "CDG", "HND", "DEL", "BOM", "BLR", "MAA"]
COMPONENTS = ["Engine 1", "Engine 2", "Landing Gear", "Avionics", "Hydraulics", "Fuel System", "APU"]
ACTIONS = ["Inspection", "Repair", "Replacement", "Calibration"]
SEVERITIES = ["Minor", "Moderate", "Major"]
TECH_NOTES = [
    "Replaced hydraulic actuator seal due to minor weeping.",
    "Engine 1 blade inspection completed. No thermal fatigue detected.",
    "Landing gear retract cylinder micro-switch adjusted.",
    "Avionics software update completed to version 4.2.1.",
    "APU fuel control unit calibrated.",
    "Oxygen bottle pressure checked and refilled.",
    "Cabin pressurization valve inspected; seal replaced."
]

def generate_aircraft_data(num_aircraft=10):
    aircraft_list = []
    for i in range(num_aircraft):
        tail_number = f"N{random.randint(100, 999)}AS"
        model = random.choice(MODELS)
        manufacturer = "Boeing" if "Boeing" in model else "Airbus" if "Airbus" in model else "Bombardier"
        year = random.randint(2010, 2023)
        hours = random.uniform(1000.0, 35000.0)
        
        aircraft_list.append({
            "tail_number": tail_number,
            "model": model,
            "manufacturer": manufacturer,
            "manufacture_year": year,
            "total_flight_hours": hours,
            "last_maintenance_date": datetime.datetime.utcnow() - datetime.timedelta(days=random.randint(1, 90))
        })
    return aircraft_list

def generate_flight_data(aircraft_ids, num_flights=50):
    flights = []
    start_date = datetime.datetime.utcnow() - datetime.timedelta(days=120)
    airlines = ["AI", "6E", "UK", "SG", "G8", "AS"] # Air India, IndiGo, Vistara, SpiceJet, GoFirst, AeroSafe
    
    for i in range(num_flights):
        ac_id = random.choice(aircraft_ids)
        prefix = random.choice(airlines)
        flight_number = f"{prefix}{random.randint(100, 999)}"
        origin = random.choice(AIRPORTS)
        dest = random.choice(AIRPORTS)
        while dest == origin:
            dest = random.choice(AIRPORTS)
            
        dept = start_date + datetime.timedelta(days=random.randint(1, 110), hours=random.randint(0, 23))
        duration = random.uniform(1.0, 12.0)
        arr = dept + datetime.timedelta(hours=duration)
        
        # Inject realistic delays
        delay = 0.0
        if random.random() < 0.25: # 25% chance of delay
            delay = random.uniform(15.0, 180.0)
            
        flights.append({
            "flight_number": flight_number,
            "aircraft_id": ac_id,
            "origin": origin,
            "destination": dest,
            "departure_time": dept,
            "arrival_time": arr,
            "flight_duration_hours": duration,
            "delay_minutes": delay,
            "status": "Completed"
        })
    return flights

def generate_maintenance_data(aircraft_ids, num_events=30):
    maintenance = []
    for i in range(num_events):
        ac_id = random.choice(aircraft_ids)
        date = datetime.datetime.utcnow() - datetime.timedelta(days=random.randint(1, 120))
        component = random.choice(COMPONENTS)
        action = random.choice(ACTIONS)
        notes = random.choice(TECH_NOTES)
        cost = random.uniform(500.0, 12000.0)
        
        maintenance.append({
            "aircraft_id": ac_id,
            "event_date": date,
            "component_name": component,
            "action_taken": action,
            "technician_notes": notes,
            "cost": cost
        })
    return maintenance

def generate_sensor_data(flight_id, duration_hours):
    # Generates standard telemetry time-series
    readings = []
    steps = int(duration_hours * 2) # reading every 30 minutes
    if steps < 1:
        steps = 1
        
    start_time = datetime.datetime.utcnow() - datetime.timedelta(hours=duration_hours)
    
    # Base profiles for simulation
    anomaly = random.random() < 0.08 # 8% probability of simulating anomaly
    
    for step in range(steps):
        time_offset = start_time + datetime.timedelta(minutes=30 * step)
        
        # Base healthy distributions
        engine_temp = random.normalvariate(820.0, 15.0)
        oil_press = random.normalvariate(55.0, 4.0)
        vibration = random.normalvariate(0.35, 0.05)
        hydraulic = random.normalvariate(3000.0, 50.0)
        fuel_flow = random.normalvariate(2200.0, 150.0)
        altitude = 35000.0 if step > 0 and step < steps-1 else 10000.0
        
        # Inject anomalies
        if anomaly:
            factor = random.choice(["temp_spike", "pressure_drop", "high_vibration"])
            if factor == "temp_spike":
                engine_temp += random.uniform(80.0, 150.0)
            elif factor == "pressure_drop":
                oil_press -= random.uniform(15.0, 25.0)
            elif factor == "high_vibration":
                vibration += random.uniform(0.5, 0.9)
                
        readings.append({
            "flight_id": flight_id,
            "timestamp": time_offset,
            "engine_temp_c": round(engine_temp, 2),
            "oil_pressure_psi": round(oil_press, 2),
            "vibration_amplitude_g": round(vibration, 3),
            "hydraulic_pressure_psi": round(hydraulic, 2),
            "fuel_flow_rate_gph": round(fuel_flow, 2),
            "altitude_ft": round(altitude, 2)
        })
    return readings

def generate_incidents_data(flight_ids, num_incidents=5):
    incidents = []
    for i in range(num_incidents):
        fl_id = random.choice(flight_ids)
        date = datetime.datetime.utcnow() - datetime.timedelta(days=random.randint(1, 100))
        severity = random.choice(SEVERITIES)
        
        desc = ""
        if severity == "Minor":
            desc = "Cabin entertainment system electrical fault reported. Circuit breaker reset."
        elif severity == "Moderate":
            desc = "Minor fuel sensor mismatch observed mid-flight. Systems cross-checked, normal operation resumed."
        elif severity == "Major":
            desc = "Elevated engine vibration warning during descent. Precautionary emergency landing declared."
            
        incidents.append({
            "flight_id": fl_id,
            "incident_date": date,
            "severity_level": severity,
            "description": desc
        })
    return incidents
