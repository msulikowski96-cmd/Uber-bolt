import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    uber_access_token = db.Column(db.String(512), nullable=True)
    uber_refresh_token = db.Column(db.String(512), nullable=True)
    uber_token_expiry = db.Column(db.DateTime, nullable=True)
    
    @staticmethod
    def get_by_id(user_id):
        """Pobiera użytkownika po ID"""
        return User.query.get(int(user_id))
    
    @staticmethod
    def get_by_email(email):
        """Pobiera użytkownika po email"""
        return User.query.filter_by(email=email).first()
    
    @staticmethod
    def create(email, password):
        """Tworzy nowego użytkownika"""
        password_hash = generate_password_hash(password)
        
        try:
            user = User()
            user.email = email
            user.password_hash = password_hash
            db.session.add(user)
            db.session.commit()
            
            user_folder = f'user_data/{user.id}'
            os.makedirs(user_folder, exist_ok=True)
            
            with open(f'{user_folder}/kursy.txt', 'w', encoding='utf-8') as f:
                f.write('')
            
            with open(f'{user_folder}/cele.txt', 'w', encoding='utf-8') as f:
                f.write('cel_dzienny:300\nmin_stawka:30\n')
            
            return user
        except Exception:
            db.session.rollback()
            return None
    
    @staticmethod
    def verify_password(email, password):
        """Weryfikuje hasło użytkownika"""
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            return user
        return None

def get_user_folder(user_id):
    """Zwraca ścieżkę folderu użytkownika"""
    return f'user_data/{user_id}'

def init_db(app):
    """Inicjalizuje bazę danych"""
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
