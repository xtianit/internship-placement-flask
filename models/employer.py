from models import db
from datetime import datetime


class Employer(db.Model):
    __tablename__ = 'employers'

    employer_id     = db.Column(db.BigInteger, db.ForeignKey('users.user_id'), primary_key=True)
    company_name    = db.Column(db.String(180), nullable=False)
    company_website = db.Column(db.String(255))
    industry        = db.Column(db.String(100))
    company_size    = db.Column(db.String(30))
    location        = db.Column(db.String(150))
    about           = db.Column(db.Text)
    verified        = db.Column(db.SmallInteger, default=0)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('employer_profile', uselist=False))

    def to_dict(self):
        return {
            'id':           self.employer_id,
            'company_name': self.company_name,
            'industry':     self.industry,
            'location':     self.location,
            'about':        self.about,
            'verified':     bool(self.verified),
            'email':        self.user.email if self.user else None,
        }