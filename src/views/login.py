import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttk
from .main_window import MainWindow
import sqlite3

class LoginWindow(ttk.Window):
    def __init__(self, db_conn):
        """Uygulamanın giriş penceresini başlatır."""
        # Sabit bir tema ile pencereyi başlat
        super().__init__(themename="litera") 
        
        self.db_conn = db_conn
        self.init_ui()
        
    def init_ui(self):
        """Giriş penceresinin arayüz elemanlarını oluşturur ve yerleştirir."""
        self.title('IT Envanter Yönetimi - Giriş')
        self.eval('tk::PlaceWindow . center') # Pencereyi ortala
        self.geometry('420x350') 
        
        main_frame = ttk.Frame(self, padding="30 20") 
        main_frame.pack(expand=True, fill='both') 
        main_frame.columnconfigure(0, weight=1) 

        # Logo/Simge Alanı
        ttk.Label(main_frame, text="🏢", font=('Segoe UI Emoji', 24)).grid(row=0, column=0, pady=(0, 10))

        # Başlık
        ttk.Label(main_frame, text="IT Envanter Yönetimi", 
                  font=('Helvetica', 16, 'bold'), 
                  bootstyle="primary").grid(row=1, column=0, pady=(0, 25), sticky='ew')

        # Kullanıcı Adı Alanı
        user_frame = ttk.Frame(main_frame)
        user_frame.grid(row=2, column=0, pady=5, sticky='ew')
        user_frame.columnconfigure(1, weight=1) 
        ttk.Label(user_frame, text="👤 Kullanıcı:", width=10).grid(row=0, column=0, padx=(0, 10), sticky='w')
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(user_frame, textvariable=self.username_var, width=30, bootstyle="info") 
        self.placeholder_user = 'Kullanıcı Adı'
        username_entry.insert(0, self.placeholder_user)
        username_entry.bind("<FocusIn>", lambda event: self.on_focus_in(event, self.placeholder_user))
        username_entry.bind("<FocusOut>", lambda event: self.on_focus_out(event, self.placeholder_user))
        username_entry.grid(row=0, column=1, sticky='ew') 
        
        # Şifre Alanı
        pass_frame = ttk.Frame(main_frame)
        pass_frame.grid(row=3, column=0, pady=5, sticky='ew')
        pass_frame.columnconfigure(1, weight=1)
        ttk.Label(pass_frame, text="🔑 Şifre:", width=10).grid(row=0, column=0, padx=(0, 10), sticky='w')
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(pass_frame, textvariable=self.password_var, show="*", width=30, bootstyle="info")
        self.placeholder_pass = 'Şifre'
        password_entry.insert(0, self.placeholder_pass) 
        password_entry.bind("<FocusIn>", lambda event: self.on_focus_in(event, self.placeholder_pass, show_char="*"))
        password_entry.bind("<FocusOut>", lambda event: self.on_focus_out(event, self.placeholder_pass, show_char="*"))
        password_entry.grid(row=0, column=1, sticky='ew')

        # Enter tuşu ile giriş için olay bağlama
        username_entry.bind("<Return>", self.handle_login_event)
        password_entry.bind("<Return>", self.handle_login_event)
        
        # Giriş Butonu
        login_button = ttk.Button(main_frame, text="Giriş Yap", 
                                  command=self.handle_login, 
                                  bootstyle="success",
                                  width=20) 
        login_button.grid(row=4, column=0, pady=(25, 15))

        # Bilgi Etiketi
        info_label = ttk.Label(main_frame, text="Varsayılan: admin / admin", 
                             justify='center', font=('Helvetica', 9), 
                             bootstyle="secondary") 
        info_label.grid(row=5, column=0, pady=(10, 0))

        username_entry.focus_set()

    def on_focus_in(self, event, placeholder, show_char=None):
        """Giriş alanına odaklanıldığında placeholder'ı temizler ve stili değiştirir."""
        widget = event.widget
        widget.configure(bootstyle="primary") # Odak rengi
        if widget.get() == placeholder:
            widget.delete(0, tk.END)
            if show_char: widget.config(show=show_char)

    def on_focus_out(self, event, placeholder, show_char=None):
        """Odak kaybedildiğinde placeholder'ı geri yükler ve stili normale çevirir."""
        widget = event.widget
        widget.configure(bootstyle="info") # Normal renk
        if not widget.get():
            if show_char: widget.config(show="")
            widget.insert(0, placeholder)

    def handle_login_event(self, event):
        """Enter tuşuna basıldığında girişi tetikler."""
        self.handle_login() 

    def handle_login(self):
        """Giriş bilgilerini doğrular ve ana pencereyi açar."""
        username = self.username_var.get()
        password = self.password_var.get()
        
        if username == self.placeholder_user: username = ""
        if password == self.placeholder_pass: password = ""
            
        if not username or not password:
             messagebox.showwarning("Eksik Bilgi", "Kullanıcı adı ve şifre giriniz.")
             return
             
        try:
            cursor = self.db_conn.cursor() 
            cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
            user = cursor.fetchone()
        except sqlite3.Error as e:
             messagebox.showerror("Veritabanı Hatası", f"Giriş sırasında hata:\n{e}")
             return
            
        if user:
            print(f"Giriş başarılı: {user}") 
            self.withdraw() # Login penceresini gizle
            main_app = MainWindow(self.db_conn, user) 
            main_app.protocol("WM_DELETE_WINDOW", self.quit) # Ana pencere kapanınca uygulamayı kapat
        else:
            messagebox.showerror("Giriş Başarısız", "Hatalı kullanıcı adı veya şifre!")
            self.password_var.set("") # Başarısız girişte sadece şifreyi temizle