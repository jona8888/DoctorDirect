from flask import Flask, request, jsonify, render_template
import requests
from utils import load_zip_coords, find_nearby_zips  

app = Flask(__name__)
zip_coords = load_zip_coords()

condition_to_specialty = {
    "diabetes": "Internal Medicine",
    "asthma": "Pulmonary Disease",
    "depression": "Psychiatry",
    "hypertension": "Cardiology",
    "back pain": "Orthopaedic Surgery",
    "anxiety": "Psychiatry",
    "covid": "Internal Medicine",
}

symptom_to_specialty = {
    "chest": "Cardiology",
    "heart": "Cardiology",
    "lung": "Pulmonary Disease",
    "breath": "Pulmonary Disease",
    "knee": "Orthopaedic Surgery",
    "shoulder": "Orthopaedic Surgery",
    "eye": "Ophthalmology",
    "ear": "Otolaryngology",
    "throat": "Otolaryngology",
    "skin": "Dermatology",
    "stomach": "Gastroenterology",
    "head": "Neurology",
    "brain": "Neurology",
    "pain": "General Practice",
    "fatigue": "Internal Medicine",
    "tired": "Internal Medicine",
    "sad": "Psychiatry",
    "anxiety": "Psychiatry",
    "depressed": "Psychiatry",
    "confused": "Neurology",
    "blurry": "Ophthalmology",
    "itch": "Dermatology"
}

@app.route('/')
def index():
    return render_template('index.html')  # Make sure index.html is in the templates folder

def format_zip(zip_code):
    zip_code = zip_code.strip()
    if len(zip_code) == 9 and zip_code.isdigit():
        return zip_code[:5] + "-" + zip_code[5:]
    return zip_code


@app.route('/lookup', methods=['GET'])
def lookup_doctors():
    condition = request.args.get('condition', '').lower()
    symptom = request.args.get('symptom', '').lower()
    zip_code = request.args.get('zip', '').strip()
    radius_str = request.args.get('radius', '10')

    try:
        radius = int(radius_str)
    except ValueError:
        radius = 10

    if not zip_code or zip_code not in zip_coords:
        return jsonify({"error": "Invalid or missing ZIP code"}), 400

    # Determine specialty from condition or symptom
    specialty = None
    if condition and condition in condition_to_specialty:
        specialty = condition_to_specialty[condition]
    elif symptom:
        for keyword, mapped_specialty in symptom_to_specialty.items():
            if keyword in symptom:
                specialty = mapped_specialty
                break


    if not specialty:
        return jsonify({"error": "Could not determine specialty from input"}), 400

    nearby_zips = find_nearby_zips(zip_code, radius, zip_coords)


    results = []
    for z in nearby_zips:
        url = f"https://npiregistry.cms.hhs.gov/api/?version=2.1&postal_code={z}&limit=50"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                for item in data.get("results", []):
                    taxonomies = item.get("taxonomies", [])
                    if any(specialty.lower() in t.get("desc", "").lower() for t in taxonomies):
                        basic = item.get("basic", {})
                        address = item.get("addresses", [{}])[0]
                        formatted_zip = format_zip(address.get('postal_code', ''))
                        results.append({
                            "name": f"{basic.get('first_name', '')} {basic.get('last_name', '')}".strip(),
                            "specialty": ", ".join(t.get("desc", "") for t in taxonomies),
                            "address": f"{address.get('address_1', '')}, {address.get('city', '')}, {address.get('state', '')} {formatted_zip}",
                            "phone": address.get("telephone_number", "")
                        })

            else:
                print(f"NPI API call failed for ZIP {z} with status {response.status_code}")
        except Exception as e:
            print(f"Error querying NPI API for ZIP {z}: {e}")

    if not results:
        return jsonify({"message": "No doctors found in the selected area."})

    return jsonify({"results": results})

if __name__ == '__main__':
    app.run(debug=True)
