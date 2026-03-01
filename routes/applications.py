from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db
from models.application import Application
from models.posting import Posting
from models.student import Student
from models.employer import Employer
from utils.mailer import send_status_email

applications_bp = Blueprint('applications', __name__)


# POST /api/applications  (student must be logged in)
@applications_bp.route('', methods=['POST'])
@jwt_required()
def apply():
    user_id  = get_jwt_identity()
    student  = Student.query.get(user_id)
    if not student:
        return jsonify({'error': 'Only students can apply'}), 403

    data       = request.get_json()
    posting_id = data.get('posting_id')
    if not posting_id:
        return jsonify({'error': 'posting_id is required'}), 400

    if Application.query.filter_by(posting_id=posting_id, student_id=user_id).first():
        return jsonify({'error': 'You already applied to this posting'}), 409

    posting = Posting.query.get(posting_id)
    if not posting or posting.status != 'PUBLISHED':
        return jsonify({'error': 'Posting is not available'}), 404

    app = Application(
        posting_id=posting_id, student_id=user_id,
        resume_id=data.get('resume_id'), cover_letter=data.get('cover_letter'),
        status='SUBMITTED',
    )
    db.session.add(app)
    db.session.commit()
    return jsonify(app.to_dict()), 201


# GET /api/applications/my  (student sees their applications)
@applications_bp.route('/my', methods=['GET'])
@jwt_required()
def my_applications():
    user_id = get_jwt_identity()
    apps = Application.query.filter_by(student_id=user_id).order_by(Application.applied_at.desc()).all()
    return jsonify([a.to_dict() for a in apps]), 200


# DELETE /api/applications/<id>  (student withdraws)
@applications_bp.route('/<int:app_id>', methods=['DELETE'])
@jwt_required()
def withdraw(app_id):
    user_id = get_jwt_identity()
    app = Application.query.get_or_404(app_id)
    if str(app.student_id) != str(user_id):
        return jsonify({'error': 'Not authorised'}), 403
    app.status = 'WITHDRAWN'
    db.session.commit()
    return jsonify({'message': 'Application withdrawn'}), 200


# PUT /api/applications/<id>/status  (employer updates status)
@applications_bp.route('/<int:app_id>/status', methods=['PUT'])
@jwt_required()
def update_status(app_id):
    user_id = get_jwt_identity()
    app     = Application.query.get_or_404(app_id)
    posting = Posting.query.get(app.posting_id)
    if str(posting.employer_id) != str(user_id):
        return jsonify({'error': 'Not authorised'}), 403

    new_status = (request.get_json().get('status') or '').upper()
    allowed    = ['SUBMITTED','UNDER_REVIEW','SHORTLISTED','REJECTED','INTERVIEW','OFFERED','HIRED','WITHDRAWN']
    if new_status not in allowed:
        return jsonify({'error': f'Status must be one of: {allowed}'}), 400

    app.status = new_status
    db.session.commit()

    # ── Send email notification to student ──
    try:
        student = app.student
        email   = student.user.email      if (student and student.user) else None
        name    = student.user.first_name if (student and student.user) else "Applicant"
        company = posting.employer.company_name if (posting and posting.employer) else "the company"

        if email:
            # We get the mail object from Flask's internal memory (extensions)
            mail_obj = current_app.extensions.get('mail') 
            send_status_email(mail_obj, email, name, posting.title, company, new_status)
    except Exception as e:
        print(f"Email notification failed (non-critical): {e}")

    return jsonify(app.to_dict()), 200


# GET /api/applications/employer  (all applicants for employer's postings)
@applications_bp.route('/employer', methods=['GET'])
@jwt_required()
def employer_applicants():
    user_id  = get_jwt_identity()
    employer = Employer.query.get(user_id)
    if not employer:
        return jsonify({'error': 'Not an employer'}), 403

    posting_ids = [p.posting_id for p in Posting.query.filter_by(employer_id=user_id).all()]
    apps        = Application.query.filter(Application.posting_id.in_(posting_ids)).order_by(Application.applied_at.desc()).all()

    result = []
    for a in apps:
        d = a.to_dict()
        if a.student:
            d['student_name'] = f"{a.student.first_name} {a.student.last_name}"
            d['institution']  = a.student.institution
            d['department']   = a.student.department
        result.append(d)
    return jsonify({'applicants': result}), 200