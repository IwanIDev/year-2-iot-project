from flask_login import UserMixin
from database import db


class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    device_id = db.Column(db.String(250), unique=True, nullable=False)
    local_council = db.Column(db.String(250), nullable=False)
    points = db.Column(db.Integer, nullable=False, default=0)