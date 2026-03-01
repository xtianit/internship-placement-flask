
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models import db
from models.employer import Employer
from models.posting import Posting
from models.application import Application
from utils.mailer import send_status_email
from extensions import mail


employers_bp = Blueprint('employers', __name__)


@employers_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    user_id  = get_jwt_identity()
    employer = Employer.query.get(user_id)
    if not employer:
        return jsonify({'error': 'Not an employer'}), 403

    posting_ids  = [p.posting_id for p in Posting.query.filter_by(employer_id=user_id).all()]
    total_active = Posting.query.filter_by(employer_id=user_id, status='PUBLISHED').count()

    if not posting_ids:
        return jsonify({
            'stats': {'active_postings': 0, 'total_applications': 0, 'shortlisted': 0, 'hired': 0}
        }), 200

    total_apps  = Application.query.filter(Application.posting_id.in_(posting_ids)).count()
    shortlisted = Application.query.filter(Application.posting_id.in_(posting_ids), Application.status.in_(['SHORTLISTED','INTERVIEW'])).count()
    hired       = Application.query.filter(Application.posting_id.in_(posting_ids), Application.status.in_(['HIRED','OFFERED'])).count()

    return jsonify({
        'stats': {
            'active_postings':    total_active,
            'total_applications': total_apps,
            'shortlisted':        shortlisted,
            'hired':              hired,
        }
    }), 200


@employers_bp.route('/interviews', methods=['GET'])
@jwt_required()
def get_interviews():
    user_id    = get_jwt_identity()
    interviews = db.session.query(Application).join(Posting).filter(
        Posting.employer_id == user_id,
        Application.status  == 'INTERVIEW'
    ).all()

    result = []
    for app in interviews:
        student = app.student
        name    = "Unknown"
        if student:
            u = getattr(student, 'user', None)
            if u:
                if hasattr(u, 'first_name'):
                    name = f"{u.first_name} {u.last_name}"
                elif hasattr(u, 'name'):
                    name = u.name
                elif hasattr(u, 'email'):
                    name = u.email
            elif hasattr(student, 'first_name'):
                name = f"{student.first_name} {student.last_name}"

        result.append({
            'id':             app.application_id,
            'candidate_name': name,
            'position':       app.posting.title if app.posting else '—',
            'applied_at':     app.applied_at.isoformat() if app.applied_at else None,
            'status':         'interview',
        })
    return jsonify(result), 200


@employers_bp.route('/applications/<int:application_id>/interview', methods=['PUT'])
@jwt_required()
def move_to_interview(application_id):
    user_id = get_jwt_identity()

    application = db.session.query(Application).join(Posting).filter(
        Application.application_id == application_id,
        Posting.employer_id        == user_id
    ).first()

    if not application:
        return jsonify({'error': 'Application not found'}), 404

    if application.status == 'INTERVIEW':
        return jsonify({'error': 'Already in interview stage'}), 400

    allowed = ['SUBMITTED', 'UNDER_REVIEW', 'SHORTLISTED']
    if application.status not in allowed:
        return jsonify({'error': f'Cannot move to interview from {application.status}'}), 400

    application.status = 'INTERVIEW'
    db.session.commit()

    # ── Send interview invitation email to student ──
    try:
        student = application.student
        email   = student.user.email      if (student and student.user) else None
        name    = student.user.first_name if (student and student.user) else "Applicant"
        company = application.posting.employer.company_name if (application.posting and application.posting.employer) else "the company"
       
        if email:
            send_status_email(mail, email, name, application.posting.title, company, 'INTERVIEW')

    except Exception as e:
        print(f"Interview email failed (non-critical): {e}")

    return jsonify({'message': 'Moved to interview', 'id': application.application_id}), 200


@employers_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    employer = Employer.query.get(get_jwt_identity())
    if not employer:
        return jsonify({'error': 'Profile not found'}), 404
    return jsonify(employer.to_dict()), 200


@employers_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    employer = Employer.query.get(get_jwt_identity())
    if not employer:
        return jsonify({'error': 'Profile not found'}), 404
    data = request.get_json()
    for field in ['company_name','company_website','industry','company_size','location','about']:
        if field in data:
            setattr(employer, field, data[field])
    db.session.commit()
    return jsonify(employer.to_dict()), 200


@employers_bp.route('/postings', methods=['GET'])
@jwt_required()
def get_employer_postings():
    user_id  = get_jwt_identity()
    postings = Posting.query.filter_by(employer_id=user_id).all()
    return jsonify([p.to_dict() for p in postings]), 200


@employers_bp.route('/postings', methods=['POST'])
@jwt_required()
def create_posting():
    user_id      = get_jwt_identity()
    data         = request.get_json()
    deadline_str = data.get('deadline')
    deadline_obj = None

    if deadline_str:
        try:
            deadline_obj = datetime.strptime(deadline_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date. Use YYYY-MM-DD'}), 400

    new_posting = Posting(
        employer_id=user_id,
        title=data.get('title'),
        description=data.get('description'),
        location=data.get('location'),
        type=data.get('type', 'INTERNSHIP'),
        work_mode=data.get('work_mode', 'ONSITE'),
        salary_min=data.get('salary_min'),
        salary_max=data.get('salary_max'),
        deadline=deadline_obj,
        status=data.get('status', 'PUBLISHED')
    )
    db.session.add(new_posting)
    db.session.commit()
    return jsonify({'message': 'Posting created', 'posting': new_posting.to_dict()}), 201


@employers_bp.route('/postings/<int:posting_id>/close', methods=['PUT'])
@jwt_required()
def close_posting(posting_id):
    user_id = get_jwt_identity()
    posting = Posting.query.filter_by(posting_id=posting_id, employer_id=user_id).first()
    if not posting:
        return jsonify({'error': 'Posting not found'}), 404
    posting.status = 'CLOSED'
    db.session.commit()
    return jsonify({'message': 'Posting closed successfully', 'posting': posting.to_dict()}), 200


@employers_bp.route('/applicants', methods=['GET'])
@jwt_required()
def get_employer_applicants():
    user_id    = get_jwt_identity()
    applicants = db.session.query(Application).join(Posting).filter(
        Posting.employer_id == user_id
    ).all()

    result = []
    for app in applicants:
        student      = app.student
        student_name = f"{student.first_name} {student.last_name}" if student else "Unknown"
        result.append({
            'id':           app.application_id,
            'student_name': student_name,
            'job_title':    app.posting.title      if app.posting  else None,
            'institution':  student.institution     if student      else None,
            'department':   student.department      if student      else None,
            'applied_at':   app.applied_at.isoformat() if app.applied_at else None,
            'status':       app.status
        })

    return jsonify(result), 200