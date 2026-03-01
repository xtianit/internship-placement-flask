from models import db
from datetime import datetime


class Skill(db.Model):
    __tablename__ = 'skills'
    skill_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name     = db.Column(db.String(80), unique=True, nullable=False)


# Link table: one posting can require many skills
posting_skills = db.Table('posting_skills',
    db.Column('posting_id', db.BigInteger, db.ForeignKey('postings.posting_id'), primary_key=True),
    db.Column('skill_id',   db.Integer,    db.ForeignKey('skills.skill_id'),    primary_key=True),
)


class Posting(db.Model):
    __tablename__ = 'postings'

    posting_id      = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    employer_id     = db.Column(db.BigInteger, db.ForeignKey('employers.employer_id'), nullable=False)
    type            = db.Column(db.Enum('INTERNSHIP', 'JOB'), nullable=False)
    employment_type = db.Column(db.Enum('FULL_TIME','PART_TIME','CONTRACT','NYSC','SIWES','OTHER'), default='OTHER')
    title           = db.Column(db.String(200), nullable=False)
    description     = db.Column(db.Text, nullable=False)
    location        = db.Column(db.String(160))
    work_mode       = db.Column(db.Enum('ONSITE','REMOTE','HYBRID'), default='ONSITE')
    salary_min      = db.Column(db.Numeric(12, 2))
    salary_max      = db.Column(db.Numeric(12, 2))
    currency        = db.Column(db.String(3), default='NGN')
    deadline        = db.Column(db.Date, nullable=False)
    status          = db.Column(db.Enum('DRAFT','PUBLISHED','CLOSED'), default='PUBLISHED')
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    employer = db.relationship('Employer', backref='postings')
    skills   = db.relationship('Skill', secondary=posting_skills, backref='postings')
    def to_dict(self):
        deadline_val = self.deadline

        # If it's already a date object
        if deadline_val and hasattr(deadline_val, "isoformat"):
            deadline_val = deadline_val.isoformat()

        # If it's a string (bad old data)
        elif isinstance(deadline_val, str):
            deadline_val = deadline_val  # leave as-is

        else:
            deadline_val = None

        return {
            'id': self.posting_id,
            'company_name': self.employer.company_name if self.employer else None,
            'type': self.type,
            'employment_type': self.employment_type,
            'title': self.title,
            'description': self.description,
            'location': self.location,
            'work_mode': self.work_mode,
            'salary_min': float(self.salary_min) if self.salary_min else None,
            'salary_max': float(self.salary_max) if self.salary_max else None,
            'deadline': deadline_val,
            'status': self.status,
            'skills': [s.name for s in self.skills],
        }
        # def to_dict(self):
        deadline_val = self.deadline
        if deadline_val and hasattr(deadline_val, 'isoformat'):
            deadline_val = deadline_val.isoformat()
        return {
            'id':              self.posting_id,
            'company_name':    self.employer.company_name if self.employer else None,
            'type':            self.type,
            'employment_type': self.employment_type,
            'title':           self.title,
            'description':     self.description,
            'location':        self.location,
            'work_mode':       self.work_mode,
            'salary_min':      float(self.salary_min) if self.salary_min else None,
            'salary_max':      float(self.salary_max) if self.salary_max else None,
            'deadline':        self.deadline.isoformat() if self.deadline else None,
            'status':          self.status,
            'skills':          [s.name for s in self.skills],
        }