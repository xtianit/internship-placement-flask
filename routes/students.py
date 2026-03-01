from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db
from models.student import Student
from models.application import Resume

students_bp = Blueprint('students', __name__)


# GET /api/students/profile
@students_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    student = Student.query.get(get_jwt_identity())
    if not student:
        return jsonify({'error': 'Profile not found'}), 404
    return jsonify(student.to_dict()), 200


# PUT /api/students/profile
# Bootstrap sends: { first_name, last_name, institution, department, level, graduation_year, bio }
@students_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    student = Student.query.get(get_jwt_identity())
    if not student:
        return jsonify({'error': 'Profile not found'}), 404
    data = request.get_json()
    for field in ['first_name','last_name','institution','department','level','graduation_year','bio']:
        if field in data:
            setattr(student, field, data[field])
    db.session.commit()
    return jsonify(student.to_dict()), 200


# GET /api/students/resumes
@students_bp.route('/resumes', methods=['GET'])
@jwt_required()
def get_resumes():
    user_id = get_jwt_identity()
    resumes = Resume.query.filter_by(student_id=user_id).order_by(Resume.uploaded_at.desc()).all()
    return jsonify([r.to_dict() for r in resumes]), 200


# POST /api/students/resumes
# Bootstrap sends: { url: "https://drive.google.com/...", name: "My_CV.pdf" }
@students_bp.route('/resumes', methods=['POST'])
@jwt_required()
def add_resume():
    user_id = get_jwt_identity()
    data    = request.get_json()
    if not data.get('url') or not data.get('name'):
        return jsonify({'error': 'url and name are required'}), 400
    count  = Resume.query.filter_by(student_id=user_id).count()
    resume = Resume(student_id=user_id, file_url=data['url'], file_name=data['name'], version=count+1)
    db.session.add(resume)
    db.session.commit()
    return jsonify(resume.to_dict()), 201


# PUT /api/students/resumes/<id>/current  — mark one resume as default
@students_bp.route('/resumes/<int:resume_id>/current', methods=['PUT'])
@jwt_required()
def set_current(resume_id):
    user_id = get_jwt_identity()
    Resume.query.filter_by(student_id=user_id).update({'is_current': 0})
    resume = Resume.query.filter_by(resume_id=resume_id, student_id=user_id).first_or_404()
    resume.is_current = 1
    db.session.commit()
    return jsonify(resume.to_dict()), 200