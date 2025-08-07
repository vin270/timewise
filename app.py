from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize app
app = Flask(__name__)
CORS(app)

# Configure DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Init DB
db = SQLAlchemy(app)

# Simple test route
@app.route("/api/test")
def test():
    return {"message": "Flask is working!"}

if __name__ == "__main__":
    app.run(debug=True)
