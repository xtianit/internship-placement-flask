from models import db
from datetime import datetime


class Role(db.Model):
    __tablename__ = 'roles'
    role_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name    = db.Column(db.String(30), unique=True, nullable=False)
    # Rows seeded once:  1=ADMIN  2=STUDENT  3=EMPLOYER

    def to_dict(self):
        return {'role_id': self.role_id, 'name': self.name}


class User(db.Model):
    __tablename__ = 'users'
    user_id       = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    role_id       = db.Column(db.Integer, db.ForeignKey('roles.role_id'), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone         = db.Column(db.String(30))
    is_active     = db.Column(db.SmallInteger, default=1)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    role = db.relationship('Role', backref='users')

    def to_dict(self):
        return {
            'id':        self.user_id,
            'email':     self.email,
            'role_id':   self.role_id,
            'role_name': self.role.name if self.role else None,
        }