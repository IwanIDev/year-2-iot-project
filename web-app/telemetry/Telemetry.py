from database import db
from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import relationship

class Telemetry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deviceId = db.Column(db.String(250), db.ForeignKey("users.device_id"), nullable=False)
    user = db.relationship("Users", backref="telemetry")
    wasteType = db.Column(db.String(250), nullable=False)
    timestamp = db.Column(DateTime, nullable=False)