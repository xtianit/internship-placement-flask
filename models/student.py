from models import db
from datetime import datetime


class Student(db.Model):
    __tablename__ = 'students'

    # student_id is the same number as the user_id in the users table
    student_id      = db.Column(db.BigInteger, db.ForeignKey('users.user_id'), primary_key=True)
    first_name      = db.Column(db.String(60), nullable=False)
    last_name       = db.Column(db.String(60), nullable=False)
    institution     = db.Column(db.String(150))
    department      = db.Column(db.String(150))
    level           = db.Column(db.String(30))
    graduation_year = db.Column(db.SmallInteger)
    bio             = db.Column(db.Text)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('student_profile', uselist=False))

    def to_dict(self):
        return {
            'id':              self.student_id,
            'first_name':      self.first_name,
            'last_name':       self.last_name,
            'email':           self.user.email if self.user else None,
            'institution':     self.institution,
            'department':      self.department,
            'level':           self.level,
            'graduation_year': self.graduation_year,
            'bio':             self.bio,
        }