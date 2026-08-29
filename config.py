import os

class Config:
    SECRET_KEY = 'my-secret-key-2024'
    
    # Используем SQLite для локальной разработки
    SQLALCHEMY_DATABASE_URI = 'sqlite:///rukedelu.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    BASE_PRICES = {
        'consultation': 1500,
        'document': 3000,
        'court': 8000,
        'government': 5000,
    }
    
    URGENCY_MULTIPLIER = 1.5
    COMMISSION_PERCENT = 15
