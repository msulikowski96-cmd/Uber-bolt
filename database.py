import sqlite3
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import os

DATABASE = 'taxi_calculator.db'

def get_db():
    """Tworzy połączenie z bazą danych"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicjalizuje bazę danych"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

class User(UserMixin):
    """Model użytkownika"""
    def __init__(self, id, email):
        self.id = id
        self.email = email
    
    @staticmethod
    def get_by_id(user_id):
        """Pobiera użytkownika po ID"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, email FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return User(row['id'], row['email'])
        return None
    
    @staticmethod
    def get_by_email(email):
        """Pobiera użytkownika po email"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, email FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return User(row['id'], row['email'])
        return None
    
    @staticmethod
    def create(email, password):
        """Tworzy nowego użytkownika"""
        password_hash = generate_password_hash(password)
        
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (email, password_hash) VALUES (?, ?)',
                         (email, password_hash))
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Tworzenie folderów dla użytkownika
            user_folder = f'user_data/{user_id}'
            os.makedirs(user_folder, exist_ok=True)
            
            # Tworzenie początkowych plików
            with open(f'{user_folder}/kursy.txt', 'w', encoding='utf-8') as f:
                f.write('')
            
            with open(f'{user_folder}/cele.txt', 'w', encoding='utf-8') as f:
                f.write('cel_dzienny:300\nmin_stawka:30\n')
            
            return User(user_id, email)
        except sqlite3.IntegrityError:
            return None
    
    @staticmethod
    def verify_password(email, password):
        """Weryfikuje hasło użytkownika"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, email, password_hash FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        conn.close()
        
        if row and check_password_hash(row['password_hash'], password):
            return User(row['id'], row['email'])
        return None

def get_user_folder(user_id):
    """Zwraca ścieżkę folderu użytkownika"""
    return f'user_data/{user_id}'
