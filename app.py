from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime, timezone
import os


from db import db
from models import UserModel, Session
from firebase_init import auth

from sqlalchemy.exc import IntegrityError

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


def get_or_create_user(uid: str) -> UserModel:
    user = UserModel.query.filter_by(firebase_uid=uid).first()
    if user:
        return user
    user = UserModel(firebase_uid=uid, points=0, nickname=None)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        user = UserModel.query.filter_by(firebase_uid=uid).first()
    return user

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

    # To ensure user exists 
    user = UserModel.query.filter_by(firebase_uid=uid).first()
    if not user:
        user = get_or_create_user(uid)

    new_session = Session(
        user_id=user.id,
        timestamp=datetime.now(timezone.utc),
        duration=25 
    )
    user.points += 1
    db.session.add(new_session)
    db.session.commit()

    return jsonify({'message': 'Session logged!', 'points': user.points})



@app.route('/api/setnickname', methods=['POST'])
def setnickname():
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

    data = request.get_json()
    nickname = data.get('nickname', '').strip()

    if not nickname:
        return jsonify({'error': 'Missing nickname'}), 400

    user = UserModel.query.filter_by(firebase_uid=uid).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user.nickname = nickname
    db.session.commit()

    return jsonify({'message': 'Nickname updated', 'nickname': nickname})


@app.route('/api/me', methods=['GET'])
def get_me():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({'error': 'Missing or invalid token'}), 401

    token = auth_header.replace("Bearer ", "")

    try:
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']
    except Exception as e:
        print("Token verification error:", e)
        return jsonify({'error': 'Invalid token'}), 401

    user = UserModel.query.filter_by(firebase_uid=uid).first()
    if not user:
        user = get_or_create_user(uid)
        return jsonify({'nickname': user.nickname, 'points': user.points})

    return jsonify({'nickname': user.nickname, 'points': user.points})

@app.route('/api/leaderboard', methods=['GET'])
def leaderboard():
    top_users = UserModel.query \
        .filter(UserModel.nickname.isnot(None)) \
        .order_by(UserModel.points.desc()) \
        .limit(10) \
        .all()

    data = []
    for rank, u in enumerate(top_users, start=1):
        data.append({
            'rank':     rank,
            'nickname': u.nickname,
            'points':   u.points
        })

    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True)
