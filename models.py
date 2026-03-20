from datetime import datetime
from __main__ import db

class Reflection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    study_topic = db.Column(db.String(200),nullable=False)
    cheat_sheet = db.Column(db.Text,nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_saved = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"Reflection('{self.study_topic}', '{self.timestamp}')"