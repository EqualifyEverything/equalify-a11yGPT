from a11yGPT_package import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash
from datetime import datetime
import secrets

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    api_token = db.Column(db.String(64), unique=True, nullable=False)
    credit_card = db.Column(db.String(16), nullable=True)
    monthly_budget = db.Column(db.Float, default=99.00, nullable=True)
    monthly_spend_records = db.relationship('MonthlySpend', back_populates='user', lazy=True)
    sessions = db.relationship('Session', back_populates='user', lazy=True)

    def get_current_month_spend(self):
        current_month = datetime.now().strftime('%Y-%m')
        monthly_spend = MonthlySpend.query.filter_by(user_id=self.id, month=current_month).first()
        if monthly_spend:
            return monthly_spend.spend
        return 0.0

    def __repr__(self):
        return f'<User {self.email}>'

class MonthlySpend(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # Format: YYYY-MM
    spend = db.Column(db.Float, nullable=False)

    user = db.relationship('User', back_populates='monthly_spend_records')

    def __repr__(self):
        return f'<MonthlySpend {self.month}: {self.spend}>'

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    results = db.Column(db.JSON, default={})
    status = db.Column(db.String(20), nullable=False, default='processing')

    user = db.relationship('User', back_populates='sessions')

    def __repr__(self):
        return f'<Session {self.id}>'

def generate_api_token():
    return secrets.token_hex(32)
