import firebase_admin
from firebase_admin import credentials, auth

cred = credentials.Certificate("firebase-adminsdk.json")
firebase_admin.initialize_app(cred)
