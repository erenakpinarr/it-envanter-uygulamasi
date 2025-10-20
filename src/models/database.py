import sqlite3
import datetime
from pathlib import Path

def init_db():
    """Veritabanı bağlantısını oluşturur ve diğer modüllerle uyumlu tabloları kurar."""
    db_path = Path('inventory.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Kullanıcılar tablosu (main_window.py ile UYUMLU)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
    ''')
    
    # Envanter tablosu (main_window.py ile UYUMLU)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            model TEXT,
            brand TEXT,
            serial_number TEXT UNIQUE,
            purchase_date TEXT,
            status TEXT DEFAULT 'Aktif Kullanımda',
            location TEXT,
            notes TEXT,
            assigned_to TEXT,
            last_updated_by TEXT
        )
    ''')
    
    # Varsayılan admin kullanıcısı (admin/admin)
    try:
        cursor.execute('''
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
        ''', ('admin', 'admin', 'admin'))
    except sqlite3.IntegrityError:
        pass  # Kullanıcı zaten varsa geç
        
    # Varsayılan normal kullanıcı (user/user)
    try:
        cursor.execute('''
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
        ''', ('user', 'user', 'user'))
    except sqlite3.IntegrityError:
        pass  # Kullanıcı zaten varsa geç
    
    conn.commit()
    return conn

def get_user(conn, username, password):
    """Kullanıcıyı doğrular ve bilgilerini döndürür."""
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM users 
        WHERE username = ? AND password = ?
    ''', (username, password))
    return cursor.fetchone() # (id, username, password, role) tuple'ı döndürür

def add_inventory_item(conn, item_data):
    """Veritabanına yeni bir envanter öğesi ekler (main_window.py ile UYUMLU)."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO inventory_items 
        (name, category, model, brand, serial_number, purchase_date, status, location, notes, assigned_to)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        item_data.get('name'), # .get() kullanmak daha güvenlidir
        item_data.get('category'),
        item_data.get('model', ''),
        item_data.get('brand', ''),
        item_data.get('serial_number', ''),
        item_data.get('purchase_date'),
        item_data.get('status', 'Aktif Kullanımda'),
        item_data.get('location', ''),
        item_data.get('notes', ''),
        item_data.get('assigned_to', '') # assigned_to eklendi
    ))
    conn.commit()

def get_all_inventory(conn):
    """Tüm envanter öğelerini main_window.py'nin beklediği formatta çeker."""
    cursor = conn.cursor()
    # main_window.py'nin refresh_table'da kullandığı sorguyla eşleşir
    cursor.execute('''
        SELECT id, assigned_to, name, category, model, brand, 
               serial_number, purchase_date, status, location 
        FROM inventory_items
    ''')
    return cursor.fetchall()