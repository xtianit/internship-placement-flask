from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from models import db
from models.user import User, Role
from models.student import Student
from models.employer import Employer
# from App import mail
from extensions import mail
import random

auth_bp = Blueprint('auth', __name__)

# Store reset codes temporarily in memory { email: code }
reset_codes = {}


# POST /api/auth/register
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'This email is already registered'}), 409

    role_id  = data.get('role_id', 2)
    new_user = User(
        email         = data['email'],
        password_hash = generate_password_hash(data['password']),
        phone         = data.get('phone'),
        role_id       = role_id,
    )
    db.session.add(new_user)
    db.session.flush()

    if role_id == 2:
        db.session.add(Student(
            student_id  = new_user.user_id,
            first_name  = data.get('first_name', ''),
            last_name   = data.get('last_name', ''),
            institution = data.get('institution'),
            department  = data.get('department'),
            level       = data.get('level'),
        ))
    elif role_id == 3:
        db.session.add(Employer(
            employer_id  = new_user.user_id,
            company_name = data.get('company_name', ''),
            industry     = data.get('industry'),
        ))

    db.session.commit()
    token = create_access_token(identity=str(new_user.user_id))
    return jsonify({'token': token, 'user': new_user.to_dict()}), 201


# POST /api/auth/login
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400

    user = User.query.filter_by(email=data['email']).first()

    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401

    if not user.is_active:
        return jsonify({'error': 'Account is deactivated'}), 403

    token = create_access_token(identity=str(user.user_id))
    return jsonify({'token': token, 'user': user.to_dict()}), 200


# POST /api/auth/forgot-password
# Frontend sends: { email }
# Generates a 6-digit code, emails it to the user, stores it in memory
@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data  = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    user = User.query.filter_by(email=email).first()

    if user:
        # Generate a fresh code for this request
        code = str(random.randint(100000, 999999))
        reset_codes[email] = code  # store it for verification

        # Get name
        name = "User"
        if hasattr(user, 'student') and user.student:
            name = user.student.first_name or "User"

        # Send the email
        try:
            from flask_mail import Message
            msg = Message(
                subject  = "InternBridge — Password Reset Code",
                recipients = [email],
                body = f"""Hi {name},

Your password reset code is: {code}

This code expires in 15 minutes. If you did not request this, ignore this email.

InternBridge Team"""
            )
            mail.send(msg)
            print(f"Reset code sent to {email}: {code}")
        except Exception as e:
            print(f"Mail failed: {e}")

    # Always return success to prevent email enumeration
    return jsonify({
        'message': 'If that email is registered, a reset code has been sent.',
        'code': reset_codes.get(email)  # dev mode — remove in production
    }), 200


# POST /api/auth/verify-code
# Frontend sends: { email, code }
@auth_bp.route('/verify-code', methods=['POST'])
def verify_code():
    data  = request.get_json()
    email = data.get('email')
    code  = str(data.get('code', ''))

    if not email or not code:
        return jsonify({'error': 'Email and code are required'}), 400

    stored = reset_codes.get(email)

    if not stored or stored != code:
        return jsonify({'error': 'Invalid or expired code'}), 400

    return jsonify({'message': 'Code verified'}), 200


# POST /api/auth/reset-password
# Frontend sends: { email, code, new_password }
@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data         = request.get_json()
    email        = data.get('email')
    code         = str(data.get('code', ''))
    new_password = data.get('new_password')

    if not email or not code or not new_password:
        return jsonify({'error': 'Email, code and new_password are required'}), 400

    if len(new_password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400

    stored = reset_codes.get(email)
    if not stored or stored != code:
        return jsonify({'error': 'Invalid or expired code'}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user.password_hash = generate_password_hash(new_password)
    db.session.commit()

    # Remove the used code so it can't be reused
    reset_codes.pop(email, None)

    return jsonify({'message': 'Password updated successfully'}), 200