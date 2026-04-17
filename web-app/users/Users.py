from flask_login import UserMixin
from database import db
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    device_id = db.Column(db.String(250), unique=True, nullable=False)

    local_council_id = db.Column(
        db.Integer,
        db.ForeignKey("council.id"),
        nullable=False
    )

    UPRN = db.Column(db.Integer, nullable=False)

    council = db.relationship("Council")