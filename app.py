from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime, timezone
import os

from db import db
from models import UserModel, Session
from firebase_init import auth

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# Config
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Routes
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/test")
def test():
    return {"message": "Flask is working!"}

@app.route('/api/session', methods=['POST'])
def log_session():
    auth_header = request.headers.get('Authorization')

    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({'error': 'Missing or invalid token'}), 401

    token = auth_header.split(" ")[1]

    try:
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']
    except Exception as e:
        print("Token verification error:", e)
        return jsonify({'error': 'Invalid token'}), 401

    # Look for existing user
    user = UserModel.query.filter_by(firebase_uid=uid).first()

    if not user:
        try:
            user = UserModel(firebase_uid=uid, points=0)
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print("Error inserting user:", e)
            return jsonify({'error': 'User creation failed'}), 500

    # Create session
    new_session = Session(
        user_id=user.id,
        timestamp=datetime.now(timezone.utc),
        duration=25
    )
    user.points += 1
    db.session.add(new_session)
    db.session.commit()

    return jsonify({'message': 'Session logged!', 'points': user.points})


if __name__ == "__main__":
    app.run(debug=True)
