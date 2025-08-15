from db import db

class UserModel(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    firebase_uid = db.Column(db.String, unique=True, nullable=False)
    points = db.Column(db.Integer, default=0)
    nickname = db.Column(db.String, nullable=True) 


class Session(db.Model):
    __tablename__ = 'sessions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.DateTime)
    duration = db.Column(db.Integer)


