import random
import datetime

# Airport short codes to Full Names including India
AIRPORT_NAMES = {
    "JFK": "John F. Kennedy International Airport (New York)",
    "LAX": "Los Angeles International Airport (Los Angeles)",
    "ORD": "O'Hare International Airport (Chicago)",
    "DFW": "Dallas/Fort Worth International Airport (Dallas)",
    "ATL": "Hartsfield-Jackson Atlanta International Airport (Atlanta)",
    "SFO": "San Francisco International Airport (San Francisco)",
    "MIA": "Miami International Airport (Miami)",
    "LHR": "London Heathrow Airport (London)",
    "CDG": "Charles de Gaulle Airport (Paris)",
    "HND": "Haneda Airport (Tokyo)",
    "DEL": "Indira Gandhi International Airport (New Delhi)",
    "BOM": "Chhatrapati Shivaji Maharaj International Airport (Mumbai)",
    "BLR": "Kempegowda International Airport (Bengaluru)",
    "MAA": "Chennai International Airport (Chennai)"
}

# Estimated distances between major airports (in kilometers)
AIRPORT_DISTANCES = {
    ("JFK", "LAX"): 3975.0, ("JFK", "ORD"): 1190.0, ("JFK", "DEL"): 11750.0, ("JFK", "BOM"): 12500.0,
    ("DEL", "BOM"): 1140.0, ("DEL", "BLR"): 1710.0, ("DEL", "MAA"): 1760.0, ("DEL", "LHR"): 6710.0,
    ("BOM", "BLR"): 840.0, ("BOM", "MAA"): 1030.0, ("BOM", "LHR"): 7200.0,
    ("BLR", "MAA"): 290.0, ("BLR", "LHR"): 8020.0,
    ("MAA", "LHR"): 8200.0,
    ("LAX", "DEL"): 12850.0,
    ("LHR", "DEL"): 6710.0
}

def get_distance(origin, destination):
    key = (origin, destination)
    rev_key = (destination, origin)
    if key in AIRPORT_DISTANCES:
        return AIRPORT_DISTANCES[key]
    if rev_key in AIRPORT_DISTANCES:
        return AIRPORT_DISTANCES[rev_key]
    return round(random.uniform(500.0, 5000.0), 1)

def get_airport_name(code):
    return AIRPORT_NAMES.get(code, f"{code} International Airport")
