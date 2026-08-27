import sys
import os
# Adjust path to import correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import engine, Base, SessionLocal
from database.models import Aircraft, Flight, MaintenanceEvent, SensorReading, Incident
from pipeline.generator import (
    generate_aircraft_data,
    generate_flight_data,
    generate_maintenance_data,
    generate_sensor_data,
    generate_incidents_data
)

def seed_database():
    print("Initializing Database...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Clear existing tables to rebuild with updated Indian airports & airline mappings
        db.query(Incident).delete()
        db.query(SensorReading).delete()
        db.query(Flight).delete()
        db.query(MaintenanceEvent).delete()
        db.query(Aircraft).delete()
        db.commit()

        print("Generating aircraft data...")
        aircraft_dicts = generate_aircraft_data(12)
        aircraft_objs = [Aircraft(**a) for a in aircraft_dicts]
        db.add_all(aircraft_objs)
        db.commit()
        
        # Reload to get generated IDs
        aircrafts = db.query(Aircraft).all()
        ac_ids = [a.id for a in aircrafts]
        
        print("Generating maintenance events...")
        maint_dicts = generate_maintenance_data(ac_ids, 40)
        maint_objs = [MaintenanceEvent(**m) for m in maint_dicts]
        db.add_all(maint_objs)
        
        print("Generating flight events...")
        flight_dicts = generate_flight_data(ac_ids, 80)
        flight_objs = [Flight(**f) for f in flight_dicts]
        db.add_all(flight_objs)
        db.commit()
        
        # Reload flights
        flights = db.query(Flight).all()
        
        print("Generating sensor time series & incidents...")
        for fl in flights:
            sensor_dicts = generate_sensor_data(fl.id, fl.flight_duration_hours)
            sensor_objs = [SensorReading(**s) for s in sensor_dicts]
            db.add_all(sensor_objs)
            
        fl_ids = [f.id for f in flights]
        incident_dicts = generate_incidents_data(fl_ids, 10)
        incident_objs = [Incident(**i) for i in incident_dicts]
        db.add_all(incident_objs)
        
        db.commit()
        print("Database seeded successfully with synthetic data!")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
