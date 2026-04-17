from database import db

class Council(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    collectionName = db.Column(db.String(250), nullable=False)
    url = db.Column(db.String(250), nullable=False)
