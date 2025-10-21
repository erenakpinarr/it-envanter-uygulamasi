import re
import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import sqlite3
import pandas as pd
import ttkbootstrap as ttk

class MainWindow(tk.Tk): 
    def __init__(self, db_conn, user):
        """Ana uygulama penceresini başlatır."""
        super().__init__()
        
        self.db_conn = db_conn
        self.user = user 
        self.selected_item = None 
        
        try:
            self.style = ttk.Style(theme="litera") 
        except tk.TclError:
            print("Uyarı: 'litera' teması bulunamadı. Varsayılan ttk teması kullanılıyor.")
            self.style = ttk.Style() 

        self.sort_column = None 
        self.sort_reverse = False 
        
        self.init_ui() 
        self.setup_menu() 
        self.setup_styles()
        
    def init_ui(self):
        """Ana pencerenin arayüz elemanlarını (widget'lar) oluşturur ve grid ile yerleştirir."""
        self.title('IT Envanter Yönetim Sistemi')
        self.geometry('1200x650') 
        self.eval('tk::PlaceWindow . center') 

        self.main_frame = ttk.Frame(self, padding="10")
        self.main_frame.pack(fill='both', expand=True) 
        self.main_frame.columnconfigure(1, weight=1) 
        self.main_frame.rowconfigure(0, weight=1)    

        left_panel = ttk.Frame(self.main_frame, padding="10") 
        left_panel.grid(row=0, column=0, sticky='ns', padx=(0, 10))
        left_panel.columnconfigure(0, weight=0) 

        stats_frame = ttk.LabelFrame(left_panel, text="📊 İstatistikler", padding=(10, 8), bootstyle="info")
        stats_frame.grid(row=0, column=0, sticky='ew', pady=10) 
        stats_frame.columnconfigure(0, weight=0) 
        stats_frame.columnconfigure(1, weight=1) 

        try:
            emoji_font = ('Segoe UI Emoji', 10) 
        except tk.TclError:
            emoji_font = ('Helvetica', 10) 

        self.stats_labels = {} 
        icons = {'total': '📦', 'active': '✅', 'service': '🔧', 'storage': '📦', 'faulty': '❌', 'scrap': '🗑️'}
        labels_text_map = {'total': "Toplam: 0", 'active': "Aktif: 0", 'service': "Serviste: 0", 'storage': "Depoda: 0", 'faulty': "Arızalı: 0", 'scrap': "Hurda: 0"}
        
        row_index = 0
        for key, text in labels_text_map.items():
            icon_label = ttk.Label(stats_frame, text=icons.get(key, '▪'), font=emoji_font, anchor='center')
            icon_label.grid(row=row_index, column=0, sticky='e', padx=(0, 8))
            font_weight = 'bold' if key == 'total' else 'normal'
            text_label = ttk.Label(stats_frame, text=text, font=('Helvetica', 9, font_weight))
            text_label.grid(row=row_index, column=1, sticky='w') 
            self.stats_labels[key] = text_label 
            row_index += 1

        right_panel = ttk.Frame(self.main_frame)
        right_panel.grid(row=0, column=1, sticky='nsew') 
        right_panel.columnconfigure(0, weight=1) 
        right_panel.rowconfigure(1, weight=1) 

        button_toolbar = ttk.Frame(right_panel) 
        button_toolbar.grid(row=0, column=0, sticky='ew', pady=(0, 10)) 
        button_toolbar.columnconfigure(1, weight=1) 

        left_buttons_frame = ttk.Frame(button_toolbar)
        left_buttons_frame.grid(row=0, column=0, sticky='w')
        ttk.Button(left_buttons_frame, text="➕ Yeni Ekle", command=self.show_add_dialog, bootstyle='success', width=12).pack(side='left', padx=2)
        ttk.Button(left_buttons_frame, text="✏️ Düzenle", command=self.show_edit_dialog, bootstyle='primary', width=12).pack(side='left', padx=2)
        ttk.Button(left_buttons_frame, text="🗑️ Sil", command=self.delete_item, bootstyle='danger', width=10).pack(side='left', padx=2)
        ttk.Separator(button_toolbar, orient='vertical', bootstyle="secondary").grid(row=0, column=1, sticky='ns', padx=10, pady=5) 

        right_buttons_frame = ttk.Frame(button_toolbar)
        right_buttons_frame.grid(row=0, column=2, sticky='e') 
        ttk.Button(right_buttons_frame, text="🔄 Yenile", command=self.reset_filters_and_refresh, bootstyle='info-outline', width=10).pack(side='left', padx=2)
        ttk.Button(right_buttons_frame, text="📊 Excel'e Aktar", command=self.export_data, bootstyle='primary-outline', width=15).pack(side='left', padx=2)
        
        table_frame = ttk.Frame(right_panel)
        table_frame.grid(row=1, column=0, sticky='nsew') 
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        y_scrollbar = ttk.Scrollbar(table_frame, bootstyle="round-info") 
        y_scrollbar.grid(row=0, column=1, sticky='ns')
        x_scrollbar = ttk.Scrollbar(table_frame, orient='horizontal', bootstyle="round-info") 
        x_scrollbar.grid(row=1, column=0, sticky='ew')
        
        columns = ['Zimmet Sahibi', 'Ad', 'Kategori', 'Model', 'Marka', 'Seri No', 'Alım Tarihi', 'Durum', 'Konum']
        self.table = ttk.Treeview(table_frame, columns=columns, show='headings', yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set, selectmode='extended', bootstyle="info") 
        self.table.grid(row=0, column=0, sticky='nsew')
        y_scrollbar.config(command=self.table.yview)
        x_scrollbar.config(command=self.table.xview)
        
        column_widths = {'Zimmet Sahibi': 120, 'Ad': 180, 'Kategori': 100, 'Model': 120, 'Marka': 100, 'Seri No': 120, 'Alım Tarihi': 100, 'Durum': 120, 'Konum': 120}
        for col in columns:
            self.table.heading(col, text=col, anchor='w', command=lambda _col=col: self.sort_table(_col))
            self.table.column(col, width=column_widths[col], minwidth=60, anchor='w') 
            
        self.table.bind('<<TreeviewSelect>>', self.on_item_select) 
        
        self.detail_frame = ttk.LabelFrame(right_panel, text="Detaylar", padding="15", bootstyle="secondary") 
        self.detail_frame.grid(row=2, column=0, sticky='ew', pady=(10, 0)) # row=2
        self.detail_frame.columnconfigure(1, weight=1) 
        
        self.refresh_table() 
    
    def setup_menu(self):
        """Uygulamanın menü çubuğunu oluşturur."""
        self.menubar = tk.Menu(self)
        self.config(menu=self.menubar)
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="📁 Dosya", menu=self.file_menu)
        self.file_menu.add_command(label="📊 Dışa Aktar (Excel)", command=self.export_data, accelerator="Ctrl+E")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="🚪 Çıkış", command=self.quit, accelerator="Alt+F4")
        self.edit_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="✏️ Düzen", menu=self.edit_menu)
        self.edit_menu.add_command(label="➕ Yeni Ekle", command=self.show_add_dialog, accelerator="Ctrl+N")
        self.edit_menu.add_command(label="📝 Düzenle", command=self.show_edit_dialog, accelerator="Ctrl+E")
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="🗑️ Sil", command=self.delete_item, accelerator="Delete")
        
        self.view_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="👁️ Görünüm", menu=self.view_menu)
        self.view_menu.add_command(label="🔄 Yenile", command=self.reset_filters_and_refresh, accelerator="F5")

        self.help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="❓ Yardım", menu=self.help_menu)
        self.help_menu.add_command(label="📖 Kullanım Kılavuzu", command=self.show_help)
        self.help_menu.add_command(label="ℹ️ Hakkında", command=self.show_about)
        
        self.bind_all("<Control-n>", lambda e: self.show_add_dialog())
        self.bind_all("<Control-e>", lambda e: self.show_edit_dialog())
        self.bind_all("<Delete>", lambda e: self.delete_item())
        self.bind_all("<F5>", lambda e: self.reset_filters_and_refresh())
        
    def show_help(self):
        """Kullanım kılavuzu hakkında bir bilgi kutusu gösterir."""
        help_text = """
        🔍 IT Envanter Yönetim Sistemi Kullanım Kılavuzu
        -----------------------------------------------------
        ➕ Yeni Ekle (Ctrl+N): Yeni envanter öğesi ekler.
        📝 Düzenle (Ctrl+E): Seçili öğeyi düzenler.
        🗑️ Sil (Delete): Seçili öğeyi/öğeleri siler.  
        🔄 Yenile (F5 / Buton): Filtreleri ve sıralamayı sıfırlar.
        📊 Dışa Aktar: Görünen listeyi Excel'e aktarır.
        🖱️ Sıralama: Tablo başlıklarına tıklayarak sıralama yapılır.
        """
        messagebox.showinfo("Kullanım Kılavuzu", help_text)
    
    def show_about(self):
        """Uygulama hakkında bir bilgi kutusu gösterir."""
        about_text = "📦 IT Envanter Yönetim Sistemi v1.0\n© 2025"
        messagebox.showinfo("Hakkında", about_text)
    
    def setup_styles(self):
        """Uygulamada kullanılacak ek ttk widget stillerini tanımlar."""
        style = self.style 
        style.configure("TLabelframe.Label", font=('Helvetica', 9, 'bold')) 
        try: 
            primary_color = style.colors.primary
        except AttributeError: 
            primary_color = "#007bff" 
        style.configure("primary.TLabel", foreground=primary_color, font=('Helvetica', 9, 'bold')) 
        
        style.configure("Treeview.Heading", font=('Helvetica', 9, 'bold'), padding=5)
        style.configure("Treeview", rowheight=28) 
        style.configure("TButton", padding=5) 

    def reset_filters_and_refresh(self):
        """Toolbar'daki Yenile butonu için: Sıralamayı sıfırlar ve tabloyu yeniler."""
        self.sort_column = None; self.sort_reverse = False
        for c in self.table['columns']: 
            self.table.heading(c, text=c) 
        self.refresh_table() 
        
    def sort_table(self, col):
        """Tabloyu sütuna göre doğal sıralar."""
        def natural_sort_key(s_tuple):
            s = s_tuple[0] 
            if s is None or s == "": return (float('inf') if not reverse_order else float('-inf'),)
            s_lower = str(s).lower()
            parts = [int(p) if p.isdigit() else p for p in re.split(r'([0-9]+)', s_lower) if p]
            return tuple(parts)

        if self.sort_column == col: self.sort_reverse = not self.sort_reverse
        else: self.sort_column = col; self.sort_reverse = False
        reverse_order = self.sort_reverse

        try: items_to_sort = [(self.table.set(k, col), k) for k in self.table.get_children('')]
        except tk.TclError:
            try:
                col_idx = self.table['columns'].index(col)
                items_to_sort = [(self.table.set(k, f"#{col_idx + 1}"), k) for k in self.table.get_children('')]
            except Exception as e: print(f"Sıralama hatası ({col}): {e}"); return
        
        items_to_sort.sort(key=natural_sort_key, reverse=reverse_order)
        for idx, (val, k) in enumerate(items_to_sort): self.table.move(k, '', idx)

        arrow = ' ↓' if reverse_order else ' ↑'
        for c in self.table['columns']:
            text = c + arrow if c == col else c
            self.table.heading(c, text=text)
    
    def refresh_table(self):
        """Veritabanından verileri (filtresiz) çeker ve tabloyu yeniler."""
        self.table.delete(*self.table.get_children()) 
        cursor = self.db_conn.cursor()
        params = [] 

        query = "SELECT id, assigned_to, name, category, model, brand, serial_number, purchase_date, status, location FROM inventory_items"
        
        col_map = {'Zimmet Sahibi': 'assigned_to', 'Ad': 'name', 'Kategori': 'category', 'Model': 'model', 'Marka': 'brand', 'Seri No': 'serial_number', 'Alım Tarihi': 'purchase_date', 'Durum': 'status', 'Konum': 'location'}
        db_sort = col_map.get(self.sort_column) 
        order = "DESC" if self.sort_reverse else "ASC"
        query += f" ORDER BY {db_sort or 'name'} {order}" 
        
        try:
            cursor.execute(query, params) 
            items = cursor.fetchall()
            for item in items: self.table.insert('', 'end', iid=item[0], values=item[1:])
        except sqlite3.Error as e: print(f"DB Hata: {e}"); messagebox.showerror("Hata", f"Veri çekilemedi: {e}")

        self.update_statistics() 
        
        if self.sort_column:
            current_rev = self.sort_reverse
            self.sort_reverse = not current_rev 
            self.sort_table(self.sort_column) 
            self.sort_reverse = current_rev 

    def update_statistics(self):
        """Sol paneldeki istatistikleri günceller."""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM inventory_items")
            total_row = cursor.fetchone(); total_count = total_row[0] if total_row else 0 
            self.stats_labels['total'].config(text=f"Toplam: {total_count}")
            
            counts = {'Aktif Kullanımda': 0, 'Serviste': 0, 'Depoda': 0, 'Arızalı': 0, 'Hurda': 0}
            cursor.execute("SELECT status, COUNT(*) FROM inventory_items GROUP BY status")
            for status, count in cursor.fetchall():
                if status in counts: counts[status] = count
                elif status == 'Aktif': counts['Aktif Kullanımda'] += count
            
            self.stats_labels['active'].config(text=f"Aktif: {counts.get('Aktif Kullanımda', 0)}")
            self.stats_labels['service'].config(text=f"Serviste: {counts.get('Serviste', 0)}")
            self.stats_labels['storage'].config(text=f"Depoda: {counts.get('Depoda', 0)}")
            self.stats_labels['faulty'].config(text=f"Arızalı: {counts.get('Arızalı', 0)}")
            self.stats_labels['scrap'].config(text=f"Hurda: {counts.get('Hurda', 0)}")
        except sqlite3.Error as e: 
            print(f"İstatistik hatası: {e}")
    
    def on_item_select(self, event):
        """Tabloda öğe seçildiğinde detay panelini günceller."""
        selection = self.table.selection()
        for widget in self.detail_frame.winfo_children(): widget.destroy()
        if not selection: self.selected_item = None; return 
        try:
            item_id = selection[0] 
            cursor = self.db_conn.cursor()
            cursor.execute('''SELECT id, name, category, model, brand, serial_number, purchase_date, status, location, notes, assigned_to FROM inventory_items WHERE id = ?''', (item_id,))
            self.selected_item = cursor.fetchone() 
            if not self.selected_item: return 
            
            cols = ['id', 'name', 'category', 'model', 'brand', 'serial_number', 'purchase_date', 'status', 'location', 'notes', 'assigned_to']
            item_dict = dict(zip(cols, self.selected_item))
            d_map = [("Zimmet Sahibi:", 'assigned_to'), ("Ad:", 'name'), ("Kategori:", 'category'), ("Model:", 'model'), ("Marka:", 'brand'), ("Seri No:", 'serial_number'), ("Alım Tarihi:", 'purchase_date'), ("Durum:", 'status'), ("Konum:", 'location'), ("Notlar:", 'notes')]
            
            for i, (lbl, key) in enumerate(d_map):
                val = item_dict.get(key)
                ttk.Label(self.detail_frame, text=lbl, style='primary.TLabel').grid(row=i, column=0, sticky='ne', padx=5, pady=1) 
                val_lbl = ttk.Label(self.detail_frame, text=str(val or ""), anchor='w', wraplength=350) 
                val_lbl.grid(row=i, column=1, sticky='nw', padx=5, pady=1) 
        except Exception as e: print(f"HATA - Seçim: {e}"); messagebox.showerror("Hata", f"Detay alınamadı: {e}"); self.selected_item = None
    
    def show_add_dialog(self):
        """'Yeni Ekle' penceresini açar."""
        dialog = AddItemDialog(self) 
        self.wait_window(dialog)
        if dialog.result: 
            if not dialog.result.get('name') or not dialog.result.get('category'): messagebox.showerror("Hata", "Ad ve Kategori zorunludur!"); return
            cursor = self.db_conn.cursor()
            try:
                sql = '''INSERT INTO inventory_items (name, category, model, brand, serial_number, purchase_date, status, location, notes, assigned_to) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
                vals = (dialog.result['name'], dialog.result['category'], dialog.result.get('model', ''), dialog.result.get('brand', ''), dialog.result.get('serial_number', ''), dialog.result['purchase_date'], dialog.result.get('status', 'Aktif Kullanımda'), dialog.result.get('location', ''), dialog.result.get('notes', ''), dialog.result.get('assigned_to', ''))
                cursor.execute(sql, vals)
                self.db_conn.commit(); self.reset_filters_and_refresh(); messagebox.showinfo("Başarılı", "Öğe eklendi!")
            except sqlite3.IntegrityError: messagebox.showerror("Hata", "Seri numarası zaten mevcut!")
            except Exception as e: messagebox.showerror("Hata", f"Kayıt hatası: {e}")
        
    def show_edit_dialog(self):
        """'Düzenle' penceresini açar."""
        if not self.selected_item: messagebox.showwarning("Uyarı", "Önce bir öğe seçin!"); return
        dialog = EditItemDialog(self, self.selected_item) 
        self.wait_window(dialog)
        if dialog.result:
            cursor = self.db_conn.cursor()
            try:
                sql = '''UPDATE inventory_items SET name=?, category=?, model=?, brand=?, serial_number=?, purchase_date=?, status=?, location=?, notes=?, assigned_to=? WHERE id=?'''
                vals = (dialog.result['name'], dialog.result['category'], dialog.result['model'], dialog.result['brand'], dialog.result['serial_number'], dialog.result['purchase_date'], dialog.result['status'], dialog.result['location'], dialog.result['notes'], dialog.result['assigned_to'], self.selected_item[0])
                cursor.execute(sql, vals)
                self.db_conn.commit(); self.reset_filters_and_refresh(); messagebox.showinfo("Başarılı", "Öğe güncellendi!")
            except sqlite3.IntegrityError: messagebox.showerror("Hata", "Seri numarası zaten mevcut!")
            except Exception as e: messagebox.showerror("Hata", f"Güncelleme hatası: {e}")
    
    def delete_item(self):
        """Seçili öğeleri siler."""
        ids = self.table.selection() 
        if not ids: messagebox.showwarning("Uyarı", "Silinecek öğe(ler) seçin!"); return
        try:
            names = [f"'{self.table.item(i)['values'][1]}'" for n, i in enumerate(ids) if n < 5] 
            if len(ids) > 5: names.append("...")
            msg = f"{len(ids)} öğeyi silmek istediğinizden emin misiniz?\n({', '.join(names)})"
            if messagebox.askyesno("Onay", msg):
                cursor, deleted, errors = self.db_conn.cursor(), 0, []
                try:
                    for i in ids: cursor.execute('DELETE FROM inventory_items WHERE id = ?', (i,)); deleted += cursor.rowcount
                    self.db_conn.commit()
                except Exception as e: self.db_conn.rollback(); errors.append(f"DB Hata: {e}")
                finally:
                    self.selected_item = None; [w.destroy() for w in self.detail_frame.winfo_children()]
                    self.reset_filters_and_refresh() 
                    if not errors and deleted > 0: messagebox.showinfo("Başarılı", f"{deleted} öğe silindi!")
                    elif errors: messagebox.showerror("Hata", f"Hatalar:\n{chr(10).join(errors)}")
                    elif deleted == 0: messagebox.showwarning("Bilgi", "Öğeler bulunamadı.")
        except Exception as e: messagebox.showerror("Hata", f"Silme hatası: {e}")
            
    def export_data(self):
        """Görünen tabloyu (filtresiz/sıralı) Excel'e aktarır."""
        try:
            import pandas as pd
            cols = self.table['columns']; col_map = {'Zimmet Sahibi': 'assigned_to', 'Ad': 'name', 'Kategori': 'category', 'Model': 'model', 'Marka': 'brand', 'Seri No': 'serial_number', 'Alım Tarihi': 'purchase_date', 'Durum': 'status', 'Konum': 'location', 'Notlar':'notes'} 
            db_cols = [col_map.get(c) for c in cols if col_map.get(c)] 
            params = []

            query = f"SELECT {', '.join(db_cols)} FROM inventory_items"
            
            db_sort = col_map.get(self.sort_column)
            order = "DESC" if self.sort_reverse else "ASC"
            query += f" ORDER BY {db_sort or 'name'} {order}"
            
            df = pd.read_sql_query(query, self.db_conn, params=params) 
            df.columns = [c for c in cols if col_map.get(c)] 
            fname = f'envanter_raporu_{datetime.datetime.now():%Y%m%d_%H%M%S}.xlsx'
            df.to_excel(fname, index=False, sheet_name='Envanter')
            messagebox.showinfo("Başarılı", f"Veriler '{fname}' dosyasına aktarıldı!")
        except ImportError: messagebox.showerror("Hata", "Pandas gerekli!\n'pip install pandas'")
        except Exception as e: messagebox.showerror("Hata", f"Export hatası: {str(e)}")

#----------------------------------------------------------------------
# Dialog Pencereleri
#----------------------------------------------------------------------

class InventoryDialog(tk.Toplevel):
    """Yeni/Düzenle penceresi için temel sınıf."""
    def __init__(self, parent, title="Envanter Öğesi", item_data=None): 
        super().__init__(parent)
        self.parent = parent 
        self.item_data = item_data 
        self.result = None 
        self.title(title); self.geometry("500x700")
        
        # Ana pencerenin stilini (temasını) devralır
        s = ttk.Style()
        try:
            parent_theme = parent.style.theme_use() 
            s.theme_use(parent_theme) 
        except Exception:
             print("Uyarı: Dialog teması ana pencereden alınamadı.")
             
        main_frame = ttk.Frame(self, padding="20"); main_frame.pack(fill='both', expand=True)
        self.create_body(main_frame); self.create_buttons(main_frame) 
        self.transient(parent); self.grab_set(); self.parent.eval(f'tk::PlaceWindow {str(self)} center')
    
    def create_body(self, frame):
        """Form alanlarını oluşturur."""
        ttk.Label(frame, text="Envanter Bilgileri", font=('Helvetica', 12, 'bold')).pack(pady=(0, 20))
        form_frame = ttk.Frame(frame); form_frame.pack(fill='x', expand=True); self.fields = {} 
        self.add_field(form_frame, "name", "Cihaz Adı:", ttk.Entry)
        cats = ["Seçiniz..."] + sorted(["Bilgisayar", "Monitör", "Yazıcı", "Switch", "Güvenlik", "Sunucu", "UPS"])
        self.add_field(form_frame, "category", "Kategori:", ttk.Combobox, values=cats)
        self.add_field(form_frame, "model", "Model:", ttk.Entry)
        self.fields["category"].bind('<<ComboboxSelected>>', self.on_category_change)
        self.brand_cats = {"Bilgisayar": ["Dell", "HP", "Lenovo", "ASUS", "Acer", "MSI", "Apple", "Microsoft", "Gigabyte", "Casper", "Monster", "Huawei", "Toshiba", "Fujitsu", "Samsung", "Razer", "LG", "Sony", "Exa", "Izoly"], "Monitör": ["Samsung", "LG", "ASUS", "Dell", "HP", "BenQ", "ViewSonic", "AOC", "Philips", "MSI", "Acer", "Gigabyte", "Lenovo", "Huawei", "iiyama", "Eizo"], "Yazıcı": ["HP", "Canon", "Epson", "Brother", "Xerox", "Kyocera", "Lexmark", "Ricoh", "Pantum", "OKI", "Samsung", "Zebra", "Honeywell", "Datamax", "Konica Minolta"], "Switch": ["Cisco", "HP Aruba", "Juniper", "D-Link", "TP-Link", "Ubiquiti", "Zyxel", "MikroTik", "Netgear", "Dell Networking", "Extreme Networks", "Huawei", "Fortinet", "Mellanox"], "Güvenlik": ["Fortinet", "Palo Alto", "Cisco", "SonicWall", "WatchGuard", "Check Point", "Sophos", "Juniper", "Barracuda", "Zyxel", "Cyberom", "F5 Networks"], "Sunucu": ["Dell", "HP", "Lenovo", "IBM", "Fujitsu", "Supermicro", "Huawei", "Cisco (UCS)", "Oracle", "Inspur", "Hitachi", "NEC"], "UPS": ["APC", "Eaton", "PowerWalker", "CyberPower", "Vertiv", "Delta", "Tripp Lite", "Emerson", "Legrand", "Makelsan", "Inform", "Riello", "Socomec"]}
        self.add_field(form_frame, "brand", "Marka:", ttk.Combobox, values=["Seçiniz..."])
        self.add_field(form_frame, "serial_number", "Seri No:", ttk.Entry)
        stats = ["Seçiniz..."] + ["Aktif Kullanımda", "Depoda", "Serviste", "Arızalı", "Hurda"]
        self.add_field(form_frame, "status", "Durum:", ttk.Combobox, values=stats)
        locs = ["Seçiniz..."] + sorted(["IT", "Muhasebe", "Satış", "Yönetim", "Resepsiyon", "İnsan Kaynakları", "Pazarlama", "Üretim", "Depo", "Toplantı Odası", "Ortak Alan", "1. Kat", "2. Kat", "3. Kat"])
        self.add_field(form_frame, "location", "Departman:", ttk.Combobox, values=locs)
        self.add_field(form_frame, "assigned_to", "Zimmet Sahibi:", ttk.Entry)
        lbl_frame = ttk.Frame(form_frame); lbl_frame.pack(fill='x', pady=(10, 0))
        ttk.Label(lbl_frame, text="Notlar:").pack(anchor='w')
        self.fields["notes"] = tk.Text(form_frame, height=4, width=40, relief="solid", borderwidth=1) 
        try: font = ttk.Style().lookup('TEntry', 'font'); self.fields["notes"].configure(font=font)
        except: pass 
        self.fields["notes"].pack(fill='x', pady=(5, 10))
        if self.item_data: 
            f_map = {"name": 1, "category": 2, "model": 3, "brand": 4, "serial_number": 5, "status": 7, "location": 8, "notes": 9, "assigned_to": 10}
            for name, idx in f_map.items():
                val = str(self.item_data[idx] or ""); w = self.fields[name]
                if isinstance(w, ttk.Combobox): w.set(val or "Seçiniz...") 
                elif isinstance(w, ttk.Entry): w.insert(0, val)
                elif isinstance(w, tk.Text): w.insert('1.0', val)
            self.on_category_change() 
            self.fields["brand"].set(str(self.item_data[4] or "Seçiniz..."))
            self.fields["status"].set(str(self.item_data[7] or "Seçiniz..."))
            self.fields["location"].set(str(self.item_data[8] or "Seçiniz..."))
        else: [self.fields[k].set("Seçiniz...") for k in ["category", "brand", "status", "location"]]

    def add_field(self, parent, name, label, widget_class, **kwargs):
        """Form'a etiket ve widget ekler."""
        lbl_frame = ttk.Frame(parent); lbl_frame.pack(fill='x', pady=(10, 0))
        ttk.Label(lbl_frame, text=label).pack(anchor='w')
        if widget_class == ttk.Combobox: kwargs['state'] = 'readonly'
        widget = widget_class(parent, **kwargs)
        widget.pack(fill='x', pady=(5, 0)); self.fields[name] = widget
    
    def create_buttons(self, frame):
        """Kaydet/İptal butonlarını oluşturur."""
        btn_frame = ttk.Frame(frame); btn_frame.pack(fill='x', pady=(20, 0))
        ttk.Button(btn_frame, text="İptal", command=self.cancel, width=15, bootstyle="secondary").pack(side='right', padx=5) 
        ttk.Button(btn_frame, text="Kaydet", command=self.save, width=15, bootstyle="primary").pack(side='right')

    def cancel(self): self.result = None; self.destroy()
    
    def on_category_change(self, event=None):
        """Marka listesini kategoriye göre günceller."""
        cat, brand_wdg = self.fields["category"].get(), self.fields["brand"]
        curr_brand = brand_wdg.get()
        if cat in self.brand_cats:
            brands = ["Seçiniz..."] + sorted(self.brand_cats[cat])
            brand_wdg["values"] = brands
            if not self.item_data or curr_brand not in brands: brand_wdg.set("Seçiniz...")
        else: brand_wdg["values"] = ["Seçiniz..."]; brand_wdg.set("Seçiniz...")
            
    def save(self):
        """Form verilerini doğrular, toplar ve pencereyi kapatır."""
        name, cat = self.fields["name"].get().strip(), self.fields["category"].get()
        if not name or not cat or cat == "Seçiniz...": messagebox.showerror("Hata", "Ad ve Kategori zorunludur!"); return
        try:
            p_date = self.item_data[6] if self.item_data else datetime.date.today().strftime('%Y-%m-%d') 
            form_data = {k: self.fields[k].get().strip() if isinstance(self.fields[k], ttk.Entry) else self.fields[k].get() 
                         for k in self.fields if k != 'notes'}
            form_data['notes'] = self.fields['notes'].get('1.0', 'end-1c').strip()
            form_data['purchase_date'] = p_date 
            for key in ['brand', 'status', 'location']:
                if form_data[key] == "Seçiniz...": form_data[key] = ""
            if not form_data['status']: form_data['status'] = 'Aktif Kullanımda'
            self.result = {k: (v if v is not None else "") for k, v in form_data.items()}
            self.destroy() 
        except Exception as e: messagebox.showerror("Hata", f"Form hatası: {e}"); return

class AddItemDialog(InventoryDialog):
    """'Yeni Ekle' penceresi."""
    def __init__(self, parent): 
        super().__init__(parent, title="Yeni Envanter Ekle")

class EditItemDialog(InventoryDialog):
    """'Düzenle' penceresi."""
    def __init__(self, parent, item_data): 
        super().__init__(parent, title="Envanter Düzenle", item_data=item_data)

# --- Ana Uygulama Başlatma ---
if __name__ == '__main__':
    # Bu blok, dosyanın doğrudan çalıştırılması durumunda test için kullanılır.
    
    conn = sqlite3.connect('inventory_test.db') 
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, category TEXT NOT NULL,
        model TEXT, brand TEXT, serial_number TEXT UNIQUE, purchase_date TEXT,
        status TEXT, location TEXT, notes TEXT, assigned_to TEXT, last_updated_by TEXT )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'user' )''')
    try:
         cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('admin', 'admin', 'admin'))
    except sqlite3.IntegrityError: pass 
    conn.commit()
    
    test_user_info = (1, 'test', 'test', 'admin') 
    app = MainWindow(conn, test_user_info) 
    app.mainloop()
    if conn: conn.close(); print("DB Bağlantısı kapatıldı.")