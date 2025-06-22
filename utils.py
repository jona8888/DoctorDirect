import csv
from math import radians, cos, sin, sqrt, atan2

# Load ZIP → lat/lon from CSV into dictionary
import csv

def load_zip_coords(filename='uszips.csv'):
    zip_coords = {}
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                zip_code = row['zip'].strip().zfill(5)
                lat = float(row['lat'])
                lon = float(row['lng'])
                zip_coords[zip_code] = (lat, lon)
            except (ValueError, KeyError):
                continue  # Skip malformed rows
    return zip_coords


# Compute distance between two lat/lon points (Haversine formula)
def haversine(lat1, lon1, lat2, lon2):
    R = 3959  # Radius of Earth in miles
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))

# Find all ZIP codes within N miles
def find_nearby_zips(user_zip, radius, zip_coords):
    if user_zip not in zip_coords:
        return []

    lat1, lon1 = zip_coords[user_zip]
    nearby = []
    for zip_code, (lat2, lon2) in zip_coords.items():
        if haversine(lat1, lon1, lat2, lon2) <= radius:
            nearby.append(zip_code)
    return nearby
