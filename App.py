from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from extensions import mail
from config import Config
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

# Load base config FIRST
app.config.from_object(Config)

# Mail config from .env — no hardcoded credentials
app.config['MAIL_SERVER']         = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT']           = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS']        = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USERNAME']       = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD']       = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

CORS(app, supports_credentials=True)
jwt = JWTManager(app)
mail.init_app(app)

from models import db
db.init_app(app)

from models.user        import User, Role
from models.student     import Student
from models.employer    import Employer
from models.posting     import Posting, Skill
from models.application import Application, Resume

from routes.auth         import auth_bp
from routes.postings     import postings_bp
from routes.applications import applications_bp
from routes.students     import students_bp
from routes.employers    import employers_bp

app.register_blueprint(auth_bp,         url_prefix='/api/auth')
app.register_blueprint(postings_bp,     url_prefix='/api/postings')
app.register_blueprint(applications_bp, url_prefix='/api/applications')
app.register_blueprint(students_bp,     url_prefix='/api/student')
app.register_blueprint(employers_bp,    url_prefix='/api/employer')

@app.route('/api/stats')
def stats():
    from datetime import date
    return jsonify({
        'students':  Student.query.count(),
        'postings':  Posting.query.filter_by(status='PUBLISHED')
                        .filter(Posting.deadline >= date.today()).count(),
        'companies': Employer.query.count(),
    }), 200

@app.cli.command('seed-roles')
def seed_roles():
    for name in ['ADMIN', 'STUDENT', 'EMPLOYER']:
        if not Role.query.filter_by(name=name).first():
            db.session.add(Role(name=name))
    db.session.commit()
    print('Roles seeded: ADMIN, STUDENT, EMPLOYER')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)