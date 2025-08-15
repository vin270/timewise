from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
import os
from db import db
from models import UserModel, Session
from firebase_init import auth
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

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

ONLINE_WINDOW_SEC = int(os.getenv("ONLINE_WINDOW_SEC", "120"))

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
    now = datetime.now(timezone.utc)
    top_users = (UserModel.query
        .filter(UserModel.nickname.isnot(None))
        .order_by(UserModel.points.desc())
        .limit(10)
        .all())

    data = []
    for rank, u in enumerate(top_users, start=1):
        is_online = bool(u.last_seen and (now - u.last_seen).total_seconds() < ONLINE_WINDOW_SEC)
        data.append({
            'rank': rank,
            'nickname': u.nickname,
            'points': u.points,
            'online': is_online,  
            'last_seen_utc': u.last_seen.isoformat() if u.last_seen else None
        })
    return jsonify(data)

@app.route('/api/heartbeat', methods=['POST'])
def heartbeat():
    try:
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid token'}), 401

        token = auth_header.split(' ', 1)[1]
        try:
            uid = auth.verify_id_token(token)['uid']
        except Exception as e:
            print("Token verification error (heartbeat):", e)
            return jsonify({'error': 'Invalid token'}), 401

        # ensure user exists (race-safe)
        user = UserModel.query.filter_by(firebase_uid=uid).first()
        if not user:
            try:
                user = UserModel(firebase_uid=uid, points=0)
                db.session.add(user)
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                user = UserModel.query.filter_by(firebase_uid=uid).first()

        # update presence
        user.last_seen = datetime.now(timezone.utc)
        db.session.commit()

        return jsonify({'ok': True, 'last_seen_utc': user.last_seen.isoformat()})
    except Exception as e:
        db.session.rollback()
        print("Heartbeat handler error:", e)
        return jsonify({'error': 'Internal server error'}), 500

def compute_current_streak(user_id: int) -> int:
    # fetch session dates (UTC) in descending order
    rows = (
        db.session.query(func.date(Session.timestamp))
        .filter(Session.user_id == user_id)
        .order_by(func.date(Session.timestamp).desc())
        .all()
    )
    unique_days = [r[0] for r in rows]
    if not unique_days:
        return 0

    today = datetime.now(timezone.utc).date()
    start = today if today in unique_days else (today.replace(day=today.day) - timedelta(days=1))
    if start not in unique_days:
        return 0

    # walk backward day-by-day
    streak = 0
    d = start
    days_set = set(unique_days)
    while d in days_set:
        streak += 1
        d = d - timedelta(days=1)
    return streak

@app.route('/api/stats', methods=['GET'])
def stats():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({'error': 'Missing or invalid token'}), 401

    token = auth_header.split(" ")[1]
    try:
        uid = auth.verify_id_token(token)['uid']
    except Exception as e:
        print("Token verification error:", e)
        return jsonify({'error': 'Invalid token'}), 401

    user = UserModel.query.filter_by(firebase_uid=uid).first()
    if not user:
        user = get_or_create_user(uid)

    # totals
    total_sessions = Session.query.filter_by(user_id=user.id).count()
    last_session = (
        Session.query.filter_by(user_id=user.id)
        .order_by(Session.timestamp.desc())
        .first()
    )
    last_session_iso = last_session.timestamp.isoformat() if last_session else None

    # online = heartbeat in last 90s
    now = datetime.now(timezone.utc)
    online = bool(user.last_seen and (now - user.last_seen).total_seconds() < 90)

    streak = compute_current_streak(user.id)

    return jsonify({
        'nickname': user.nickname,
        'points': user.points,
        'total_sessions': total_sessions,
        'current_streak': streak,
        'last_session_utc': last_session_iso,
        'online': online,
        'last_seen_utc': user.last_seen.isoformat() if user.last_seen else None
    })

if __name__ == "__main__":
    app.run(debug=True)
