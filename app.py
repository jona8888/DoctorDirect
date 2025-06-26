from flask import Flask, request, jsonify, render_template
import requests
from utils import load_zip_coords, find_nearby_zips  
from db import db, User, Search
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session

app = Flask(__name__)

app.config["SECRET_KEY"] = "super-secret-key"  # change this to something secure
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///doctorapp.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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

from concurrent.futures import ThreadPoolExecutor, as_completed

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

    # Determine specialty
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

    def fetch_doctors(z):
        try:
            url = f"https://npiregistry.cms.hhs.gov/api/?version=2.1&postal_code={z}&limit=50"
            response = requests.get(url, timeout=5)
            doctors = []
            if response.status_code == 200:
                data = response.json()
                for item in data.get("results", []):
                    taxonomies = item.get("taxonomies", [])
                    if any(specialty.lower() in t.get("desc", "").lower() for t in taxonomies):
                        basic = item.get("basic", {})
                        address = item.get("addresses", [{}])[0]
                        formatted_zip = format_zip(address.get('postal_code', ''))
                        doctors.append({
                            "name": f"{basic.get('first_name', '')} {basic.get('last_name', '')}".strip(),
                            "specialty": ", ".join(t.get("desc", "") for t in taxonomies),
                            "address": f"{address.get('address_1', '')}, {address.get('city', '')}, {address.get('state', '')} {formatted_zip}",
                            "phone": address.get("telephone_number", "")
                        })
            return doctors
        except Exception as e:
            print(f"Error fetching ZIP {z}: {e}")
            return []

    # Parallel API requests
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_doctors, z) for z in nearby_zips]
        for future in as_completed(futures):
            results.extend(future.result())

    if not results:
        return jsonify({"message": "No doctors found in the selected area."})

    # Save search if logged in
    if current_user.is_authenticated:
        search_entry = Search(
            user_id=current_user.id,
            condition=condition or None,
            symptom=symptom or None,
            zip_code=zip_code,
            radius=radius
        )
        db.session.add(search_entry)
        db.session.commit()

    return jsonify({"results": results})


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "User already exists"}), 409

    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return jsonify({"message": "User registered and logged in"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    login_user(user)
    return jsonify({"message": "Logged in"}), 200

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out"}), 200

@app.route('/search_history')
@login_required
def search_history():
    searches = Search.query.filter_by(user_id=current_user.id).order_by(Search.timestamp.desc()).all()
    return jsonify([
        {
            "condition": s.condition,
            "symptom": s.symptom,
            "zip": s.zip_code,
            "radius": s.radius,
            "timestamp": s.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        } for s in searches
    ])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
