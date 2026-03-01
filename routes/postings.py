from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db
from models.posting import Posting, Skill
from models.employer import Employer
from datetime import date

postings_bp = Blueprint('postings', __name__)


# GET /api/postings  (no login needed — public)
# Supports: ?search=python  ?type=INTERNSHIP  ?mode=REMOTE  ?per_page=6  ?page=1
@postings_bp.route('', methods=['GET'])
def get_postings():
    query = Posting.query.filter_by(status='PUBLISHED').filter(Posting.deadline >= date.today())

    if request.args.get('type'):
        query = query.filter_by(type=request.args.get('type'))
    if request.args.get('mode'):
        query = query.filter_by(work_mode=request.args.get('mode'))
    if request.args.get('search'):
        t = f"%{request.args.get('search')}%"
        query = query.filter(db.or_(Posting.title.ilike(t), Posting.description.ilike(t)))

    per_page = int(request.args.get('per_page', 12))
    page     = int(request.args.get('page', 1))
    total    = query.count()
    postings = query.order_by(Posting.created_at.desc()).offset((page-1)*per_page).limit(per_page).all()

    return jsonify({
        'postings': [p.to_dict() for p in postings],
        'total': total, 'page': page,
        'pages': (total + per_page - 1) // per_page,
    }), 200


# GET /api/postings/<id>  (no login needed)
@postings_bp.route('/<int:posting_id>', methods=['GET'])
def get_one(posting_id):
    return jsonify(Posting.query.get_or_404(posting_id).to_dict()), 200


# POST /api/postings  (employer must be logged in)
# Bootstrap sends: { title, type, employment_type, location, work_mode, salary_min, salary_max, deadline, description, status }
@postings_bp.route('', methods=['POST'])
@jwt_required()
def create_posting():
    user_id  = get_jwt_identity()
    employer = Employer.query.get(user_id)
    if not employer:
        return jsonify({'error': 'Only employers can create postings'}), 403

    data = request.get_json()
    for field in ['title', 'description', 'type', 'deadline']:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    p = Posting(
        employer_id     = employer.employer_id,
        type            = data['type'],
        employment_type = data.get('employment_type', 'OTHER'),
        title           = data['title'],
        description     = data['description'],
        location        = data.get('location', 'Nigeria'),
        work_mode       = data.get('work_mode', 'ONSITE'),
        salary_min      = data.get('salary_min'),
        salary_max      = data.get('salary_max'),
        currency        = 'NGN',
        deadline        = data['deadline'],
        status          = data.get('status', 'PUBLISHED'),
    )
    db.session.add(p)
    db.session.flush()

    for name in data.get('skills', []):
        skill = Skill.query.filter_by(name=name).first() or Skill(name=name)
        db.session.add(skill)
        p.skills.append(skill)

    db.session.commit()
    return jsonify(p.to_dict()), 201


# PUT /api/postings/<id>/close  (employer must be logged in)
@postings_bp.route('/<int:posting_id>/close', methods=['PUT'])
@jwt_required()
def close_posting(posting_id):
    user_id = get_jwt_identity()
    p = Posting.query.get_or_404(posting_id)
    if str(p.employer_id) != str(user_id):
        return jsonify({'error': 'Not authorised'}), 403
    p.status = 'CLOSED'
    db.session.commit()
    return jsonify(p.to_dict()), 200


# GET /api/postings/mine  (employer's own postings)
@postings_bp.route('/mine', methods=['GET'])
@jwt_required()
def my_postings():
    user_id  = get_jwt_identity()
    postings = Posting.query.filter_by(employer_id=user_id).order_by(Posting.created_at.desc()).all()
    return jsonify({'postings': [p.to_dict() for p in postings]}), 200