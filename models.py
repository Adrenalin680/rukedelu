from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    user_type = db.Column(db.String(10), nullable=False)
    is_online = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Float, default=0.0)  # Средний рейтинг
    rating_count = db.Column(db.Integer, default=0)  # Количество оценок
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    balance = db.Column(db.Integer, default=0)
    
    # Для юристов
    specialization = db.Column(db.String(200))
    experience = db.Column(db.Integer)
    price_per_hour = db.Column(db.Integer)
    
    # Верификация юриста
    is_verified = db.Column(db.Boolean, default=False)
    verification_status = db.Column(db.String(20), default='pending')
    verification_comment = db.Column(db.String(500))
    
    orders_as_client = db.relationship('Order', foreign_keys='Order.client_id', backref='client', lazy=True)
    orders_as_lawyer = db.relationship('Order', foreign_keys='Order.lawyer_id', backref='lawyer', lazy=True)
    reviews_as_lawyer = db.relationship('Review', foreign_keys='Review.lawyer_id', backref='lawyer_review', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def update_rating(self, new_score):
        """Обновляет средний рейтинг юриста"""
        total = self.rating * self.rating_count + new_score
        self.rating_count += 1
        self.rating = round(total / self.rating_count, 1)
        return self.rating

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lawyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    service_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(200))
    date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    price = db.Column(db.Integer, nullable=False)
    is_urgent = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='pending')
    
    lawyer_confirmed = db.Column(db.Boolean, default=False)
    client_confirmed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    
    is_paid = db.Column(db.Boolean, default=False)
    amount_held = db.Column(db.Integer, default=0)
    
    commission = db.Column(db.Integer, default=0)
    lawyer_amount = db.Column(db.Integer, default=0)
    
    messages = db.relationship('Message', backref='order', lazy=True, cascade='all, delete-orphan')
    review = db.relationship('Review', backref='order', uselist=False, cascade='all, delete-orphan')

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(20))
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.String(200))

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    
    sender = db.relationship('User', backref='messages')

class LawyerDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    passport_path = db.Column(db.String(500))
    inn_path = db.Column(db.String(500))
    snils_path = db.Column(db.String(500))
    diploma_path = db.Column(db.String(500))
    photo_path = db.Column(db.String(500))
    
    lawyer_license_path = db.Column(db.String(500))
    registry_extract_path = db.Column(db.String(500))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='documents')

# ====== НОВАЯ МОДЕЛЬ: Отзывы и рейтинги ======
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False, unique=True)
    lawyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    score = db.Column(db.Integer, nullable=False)  # 1-10
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    client = db.relationship('User', foreign_keys=[client_id], backref='client_reviews')
