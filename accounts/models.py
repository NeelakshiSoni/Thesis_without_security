

from app import db
class Account(db.Model):
    number = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer) 
    balance = db.Column(db.Integer)

    def __repr__(self):
        return '<Account number %r>' % (self.number)
