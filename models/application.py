from models import db
from datetime import datetime


class Resume(db.Model):
    __tablename__ = 'resumes'
    resume_id   = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    student_id  = db.Column(db.BigInteger, db.ForeignKey('students.student_id'), nullable=False)
    file_url    = db.Column(db.String(500), nullable=False)
    file_name   = db.Column(db.String(255), nullable=False)
    version     = db.Column(db.Integer, default=1)
    is_current  = db.Column(db.SmallInteger, default=0)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref='resumes')

    def to_dict(self):
        return {
            'id':          self.resume_id,
            'url':         self.file_url,
            'name':        self.file_name,
            'version':     self.version,
            'is_current':  bool(self.is_current),
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
        }


class Application(db.Model):
    __tablename__ = 'applications'

    application_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    posting_id     = db.Column(db.BigInteger, db.ForeignKey('postings.posting_id'), nullable=False)
    student_id     = db.Column(db.BigInteger, db.ForeignKey('students.student_id'), nullable=False)
    resume_id      = db.Column(db.BigInteger, db.ForeignKey('resumes.resume_id'), nullable=True)
    cover_letter   = db.Column(db.Text)
    status         = db.Column(
        db.Enum('SUBMITTED','UNDER_REVIEW','SHORTLISTED','REJECTED','INTERVIEW','OFFERED','HIRED','WITHDRAWN'),
        default='SUBMITTED'
    )
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    posting = db.relationship('Posting', backref='applications')
    student = db.relationship('Student', backref='applications')

    def to_dict(self):
        return {
            'id':           self.application_id,
            'posting_id':   self.posting_id,
            'student_id':   self.student_id,
            'status':       self.status.lower(),
            'applied_at':   self.applied_at.isoformat() if self.applied_at else None,
            'job_title':    self.posting.title if self.posting else None,
            'company_name': self.posting.employer.company_name if (self.posting and self.posting.employer) else None,
            'location':     self.posting.location if self.posting else None,
            'salary_min':   float(self.posting.salary_min) if (self.posting and self.posting.salary_min) else None,
        }