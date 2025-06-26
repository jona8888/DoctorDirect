import sqlite3

def init_db():
    conn = sqlite3.connect('search_logs.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS search_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            condition TEXT,
            zip_code TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def log_search(condition, zip_code):
    conn = sqlite3.connect('search_logs.db')
    c = conn.cursor()
    c.execute('INSERT INTO search_logs (condition, zip_code) VALUES (?, ?)', (condition, zip_code))
    conn.commit()
    conn.close()

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    email    = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created  = db.Column(db.DateTime, server_default=db.func.now())
    
    favorites = db.relationship('Favorite', backref='user', lazy=True)

    def set_password(self, plain_pw):
        self.password = generate_password_hash(plain_pw)

    def check_password(self, plain_pw):
        return check_password_hash(self.password, plain_pw)

class Search(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    condition = db.Column(db.String(100))
    symptom = db.Column(db.String(100))
    zip_code = db.Column(db.String(10))
    radius = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

    user = db.relationship("User", backref="searches")


class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(120))
    specialty = db.Column(db.String(200))
    address = db.Column(db.String(300))
    phone = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, server_default=db.func.now())  # ✅ Add this line

