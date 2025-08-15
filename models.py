
from db import db
from sqlalchemy import CheckConstraint, func

class UserModel(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    firebase_uid = db.Column(db.String, unique=True, nullable=False, index=True)
    points = db.Column(db.Integer, nullable=False, server_default="0")
    nickname = db.Column(db.String, nullable=True)
    last_seen = db.Column(db.DateTime(timezone=True), nullable=True, index=True)  # NEW

class Session(db.Model):
    __tablename__ = 'sessions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.DateTime(timezone=True))  # you already pass UTC — keep tz=True
    duration = db.Column(db.Integer)



