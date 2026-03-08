from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from extensions import mail
from config import Config
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

# Mail config using Environment Variables
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# supports_credentials allows React to send cookies/tokens
CORS(app, supports_credentials=True)
jwt = JWTManager(app)
mail.init_app(app)

from models import db
db.init_app(app)

# Import models to ensure they are created
from models.user import User, Role
from models.student import Student
from models.employer import Employer
from models.posting import Posting, Skill
from models.application import Application, Resume

# Import and Register Blueprints
from routes.auth import auth_bp
from routes.postings import postings_bp
from routes.applications import applications_bp
from routes.students import students_bp
from routes.employers import employers_bp

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(postings_bp, url_prefix='/api/postings')
app.register_blueprint(applications_bp, url_prefix='/api/applications')
app.register_blueprint(students_bp, url_prefix='/api/student')
app.register_blueprint(employers_bp, url_prefix='/api/employer')

# Ensure tables exist in Railway
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return jsonify({"status": "API is running", "message": "InternBridge Backend Live"}), 200

if __name__ == '__main__':
    # Use dynamic port for Render, default to 5000 for local
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
