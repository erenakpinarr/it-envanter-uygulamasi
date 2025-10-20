import tkinter as tk
import sqlite3
from .views.login import LoginWindow

def setup_database():
    """Veritabanı bağlantısını oluşturur ve gerekli tabloları (inventory_items, users) kurar."""
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    
    # Envanter tablosunu oluştur
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        model TEXT,
        brand TEXT,
        serial_number TEXT UNIQUE,
        purchase_date TEXT,
        status TEXT,
        location TEXT,
        notes TEXT,
        assigned_to TEXT,
        last_updated_by TEXT
    )
    ''')
    
    # Kullanıcılar (users) tablosunu oluştur
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user' 
    )
    ''')
    
    # Başlangıçta bir admin kullanıcısı ekle (varsa hata vermez)
    try:
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                       ('admin', 'admin', 'admin'))
    except sqlite3.IntegrityError:
        # Kullanıcı zaten varsa devam et
        pass

    conn.commit() # Değişiklikleri veritabanına kaydet
    return conn # Veritabanı bağlantı nesnesini döndür

def main():
    """Uygulamanın ana giriş noktası."""
    # Veritabanı bağlantısını başlat
    db_conn = setup_database()
    
    # Giriş penceresini oluştur ve başlat
    root = LoginWindow(db_conn)
    root.mainloop() # Tkinter olay döngüsünü başlat
    
    # Program kapanırken veritabanı bağlantısını kapat
    if db_conn:
        db_conn.close()
        print("Veritabanı bağlantısı kapatıldı.")

# Bu script doğrudan çalıştırıldığında main() fonksiyonunu çağır
if __name__ == '__main__':
    main()