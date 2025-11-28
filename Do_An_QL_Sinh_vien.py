import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import mysql.connector
from datetime import datetime

DB_CONFIG = {
    "host": "localhost",
    "user": "root",        
    "password": "",       
    "database": "qlsinhvien"
}

def connect_db(create_if_missing=True):
    cfg = DB_CONFIG.copy()
    dbname = cfg.pop("database") 
    
    if create_if_missing:
        try:
            with mysql.connector.connect(**cfg) as temp_conn:
                with temp_conn.cursor() as temp_cur:
                    sql = f"CREATE DATABASE IF NOT EXISTS {dbname}" 
                    temp_cur.execute(sql)
                    print(f" Đã tạo database: {dbname}")
        except mysql.connector.Error as err:
            print(f"Lỗi khi cố tạo database: {err}")
            return None

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Lỗi kết nối chính thức: {err}")
        return None

def init_db():
    conn = connect_db(create_if_missing=True)
    if conn is None:
        return
    cur = conn.cursor()
    # Khoa -> Lop -> SinhVien -> MonHoc -> Diem
    tables = {}

    tables['khoa'] = """
            CREATE TABLE IF NOT EXISTS khoa (
            makhoa VARCHAR(10) PRIMARY KEY,
            tenkhoa VARCHAR(100) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    tables['lop'] = """
            CREATE TABLE IF NOT EXISTS lop (
            malop VARCHAR(10) PRIMARY KEY,
            tenlop VARCHAR(100) NOT NULL,
            makhoa VARCHAR(10),
            nienkhoa VARCHAR(10),
            FOREIGN KEY (makhoa) REFERENCES khoa(makhoa) ON DELETE SET NULL ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    tables['sinhvien'] = """
            CREATE TABLE IF NOT EXISTS sinhvien (
            masv INT PRIMARY KEY AUTO_INCREMENT,
            holot VARCHAR(100),
            ten VARCHAR(50),
            gioitinh VARCHAR(10),
            ngaysinh DATE,
            malop VARCHAR(10),
            quequan VARCHAR(100),
            email VARCHAR(100),
            sdt VARCHAR(15),
            FOREIGN KEY (malop) REFERENCES lop(malop) ON DELETE SET NULL ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    tables['monhoc'] = """
        CREATE TABLE IF NOT EXISTS monhoc (
            mamh VARCHAR(10) PRIMARY KEY,
            tenmh VARCHAR(100) NOT NULL,
            sotinchi INT DEFAULT 0
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    tables['diem'] = """
        CREATE TABLE IF NOT EXISTS diem (
            masv INT,
            mamh VARCHAR(10),
            diemqt DECIMAL(4,2),   -- Sửa FLOAT thành DECIMAL cho chuẩn
            diemthi DECIMAL(4,2),
            diemtb DECIMAL(4,2),
            PRIMARY KEY (masv, mamh),
            FOREIGN KEY (masv) REFERENCES sinhvien(masv) ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (mamh) REFERENCES monhoc(mamh) ON DELETE CASCADE ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    try:
        for name , sql_cmd in tables.items():
            cur.execute(sql_cmd)
            print(f"--> Đã kiểm tra/tạo bảng: {name}")
        conn.commit()
        print("--> DA tao xong tat ca bang")
    except mysql.connector.Error as err:
        print(f"Lỗi khi tạo bảng: {err}")
    conn.close()
    cur.close()
    

#ung dung chinh
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Quản lý Sinh viên - Tkinter + MySQL")

        self.center_window(900, 600)
        self.resizable(True, True)

        # Notebook chứa các tab
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True,padx= 5 ,pady=5)

        # khởi tạo tab
        self.tab_khoa = TabKhoa(self.nb)
        self.tab_lop = TabLop(self.nb)
        self.tab_sv = TabSinhVien(self.nb)
        self.tab_mh = TabMonHoc(self.nb)
        self.tab_diem = TabDiem(self.nb)
        # thêm tab vào notebook
        self.nb.add(self.tab_khoa, text="Khoa")
        self.nb.add(self.tab_lop, text="Lớp")
        self.nb.add(self.tab_sv, text="Sinh viên")
        self.nb.add(self.tab_mh, text="Môn học")
        self.nb.add(self.tab_diem, text="Điểm")
    def center_window(self, width, height):
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - width ) // 2
        y = (screen_h - height) // 2
        self.geometry(f"{screen_w}x{screen_h}+{x}+{y}")


#Tab Khoa 
class TabKhoa(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()
        self.load_data()

    def build_ui(self):
        frm_top = ttk.Frame(self)
        frm_top.pack(fill="x", padx=8, pady=8)

        # Hàng nhập liệu
        ttk.Label(frm_top, text="Mã khoa").grid(row=0, column=0, sticky="w")
        self.e_makhoa = ttk.Entry(frm_top, width=15)
        self.e_makhoa.grid(row=0, column=1, padx=4)

        ttk.Label(frm_top, text="Tên khoa").grid(row=0, column=2, sticky="w")
        self.e_tenkhoa = ttk.Entry(frm_top, width=40)
        self.e_tenkhoa.grid(row=0, column=3, padx=4)

        # Hàng nút bấm
        ttk.Button(frm_top, text="Thêm", command=self.add).grid(row=0, column=4, padx=4)
        ttk.Button(frm_top, text="Sửa", command=self.edit).grid(row=0, column=5, padx=4)
        ttk.Button(frm_top, text="Xóa", command=self.delete).grid(row=0, column=6, padx=4)
        ttk.Button(frm_top, text="Làm mới", command=self.reset_form).grid(row=0, column=7, padx=4)

        # Bảng danh sách
        cols = ("makhoa", "tenkhoa")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=15)
        
        self.tree.heading("makhoa", text="MÃ KHOA")
        self.tree.heading("tenkhoa", text="TÊN KHOA")
        
        # Thêm thanh cuộn 
        scrolly = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrolly.set)
        
        self.tree.pack(side="left", fill="both", expand=True, padx=(8,0), pady=(0,8))
        scrolly.pack(side="right", fill="y", pady=(0,8)) 

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    #HÀM TỐI ƯU
    def run_sql(self, sql, params=(), fetch=False):
        try:
            conn = connect_db()
            if conn is None: return None
            cur = conn.cursor()
            cur.execute(sql, params)
            
            if fetch:
                res = cur.fetchall()
                conn.close()
                return res
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            messagebox.showerror("Lỗi CSDL", str(e))
            return None

    def reset_form(self):

        self.e_makhoa.config(state="normal") 
        self.e_makhoa.delete(0, tk.END)
        self.e_tenkhoa.delete(0, tk.END)
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())

    #CÁC CHỨC NĂNG CHÍNH
    def load_data(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        
        # Nạp dữ liệu mới
        rows = self.run_sql("SELECT makhoa, tenkhoa FROM khoa", fetch=True)
        if rows:
            for r in rows:
                self.tree.insert("", tk.END, values=r)

    def on_select(self, evt):
        sel = self.tree.selection()
        if not sel: return
        
        v = self.tree.item(sel[0])["values"]
        
        self.reset_form()
        
        # Điền dữ liệu
        self.e_makhoa.insert(0, v[0])
        self.e_tenkhoa.insert(0, v[1])
        
        self.e_makhoa.config(state="readonly")

    def add(self):
        mak = self.e_makhoa.get().strip()
        ten = self.e_tenkhoa.get().strip()
        
        if not mak or not ten:
            messagebox.showwarning("Nhập đủ Mã và Tên khoa")
            return
            
        if self.run_sql("INSERT INTO khoa(makhoa, tenkhoa) VALUES (%s,%s)", (mak, ten)):
            messagebox.showinfo("Thêm mới thành công")
            self.load_data()
            self.reset_form()

    def edit(self):
        mak = self.e_makhoa.get() 
        ten = self.e_tenkhoa.get().strip()
        
        if not mak:
            messagebox.showwarning("Chưa chọn dòng nào để sửa")
            return
            
        if self.run_sql("UPDATE khoa SET tenkhoa=%s WHERE makhoa=%s", (ten, mak)):
            messagebox.showinfo("Cập nhật thành công!")
            self.load_data()
            self.reset_form()

    def delete(self):
        mak = self.e_makhoa.get()
        if not mak:
            messagebox.showwarning("Chưa chọn dòng nào để xóa")
            return
            
        if messagebox.askyesno("xac nhan",f"Bạn có chắc muốn xóa khoa: {mak}"):
            if self.run_sql("DELETE FROM khoa WHERE makhoa=%s", (mak,)):
                messagebox.showinfo("Đã xóa!")
                self.load_data()
                self.reset_form()

#Tab Lớp
class TabLop(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()
        self.load_khoa_combobox() 
        self.load_data()          

    def build_ui(self):
       
        frm_top = ttk.Frame(self)
        frm_top.pack(fill="x", padx=8, pady=8)

        
        ttk.Label(frm_top, text="Mã lớp").grid(row=0, column=0)
        self.e_malop = ttk.Entry(frm_top, width=12)
        self.e_malop.grid(row=0, column=1, padx=4)

        ttk.Label(frm_top, text="Tên lớp").grid(row=0, column=2)
        self.e_tenlop = ttk.Entry(frm_top, width=25)
        self.e_tenlop.grid(row=0, column=3, padx=4)

        
        ttk.Button(frm_top, text="Thêm", command=self.add).grid(row=0, column=4, padx=4)
        ttk.Button(frm_top, text="Sửa", command=self.edit).grid(row=0, column=5, padx=4)
        ttk.Button(frm_top, text="Xóa", command=self.delete).grid(row=0, column=6, padx=4)
        ttk.Button(frm_top, text="Làm mới", command=self.reset_form).grid(row=0, column=7, padx=4)

        
        ttk.Label(frm_top, text="Khoa").grid(row=1, column=0)
        self.cbb_khoa = ttk.Combobox(frm_top, width=12, state="readonly") # readonly để chỉ chọn, ko gõ bậy
        self.cbb_khoa.grid(row=1, column=1, padx=4)

        ttk.Label(frm_top, text="Niên khóa").grid(row=1, column=2)
        self.e_nienkhoa = ttk.Entry(frm_top, width=12)
        self.e_nienkhoa.grid(row=1, column=3, padx=4)

        
        cols = ("malop", "tenlop", "makhoa", "nienkhoa")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=14)
        
        
        for c in cols: 
            self.tree.heading(c, text=c.upper())
            self.tree.column(c, width=100) 

        
        scrolly = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrolly.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(8,0), pady=(0,8))
        scrolly.pack(side="right", fill="y", pady=(0,8)) 

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    #CÁC HÀM
    def run_sql(self, sql, params=(), fetch=False):
        try:
            conn = connect_db()
            if conn is None: return None
            cur = conn.cursor()
            cur.execute(sql, params)
            
            if fetch:
                res = cur.fetchall()
                conn.close()
                return res
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            messagebox.showerror("Lỗi SQL", str(e))
            return None

    def reset_form(self):
        self.e_malop.config(state="normal")
        self.e_malop.delete(0, tk.END)
        self.e_tenlop.delete(0, tk.END)
        self.cbb_khoa.set("")
        self.e_nienkhoa.delete(0, tk.END)
        try:
            self.tree.selection_remove(self.tree.selection())
        except: pass

    def load_khoa_combobox(self):
        rows = self.run_sql("SELECT makhoa FROM khoa", fetch=True)
        if rows:
            items = [r[0] for r in rows]
            self.cbb_khoa['values'] = items

    def load_data(self):
        self.load_khoa_combobox()
        
        for r in self.tree.get_children(): 
            self.tree.delete(r)
            
        rows = self.run_sql("SELECT malop, tenlop, makhoa, nienkhoa FROM lop", fetch=True)
        if rows:
            for r in rows: 
                self.tree.insert("", tk.END, values=r)

    def on_select(self, evt):
        s = self.tree.selection()
        if not s: return
        
        v = self.tree.item(s[0])['values']
        
        self.reset_form()
        
        self.e_malop.insert(0, v[0])
        self.e_tenlop.insert(0, v[1])
        self.cbb_khoa.set(v[2] or "") 
        self.e_nienkhoa.insert(0, v[3] or "")
        
        self.e_malop.config(state="readonly")

    def add(self):
        malop = self.e_malop.get().strip()
        ten = self.e_tenlop.get().strip()
        makhoa = self.cbb_khoa.get().strip() or None
        nk = self.e_nienkhoa.get().strip()

        if not malop or not ten:
            messagebox.showwarning("Nhập Mã lớp và Tên lớp")
            return

        sql = "INSERT INTO lop(malop, tenlop, makhoa, nienkhoa) VALUES (%s,%s,%s,%s)"
        if self.run_sql(sql, (malop, ten, makhoa, nk)):
            messagebox.showinfo("Thêm lớp mới xong!")
            self.load_data()
            self.reset_form() 

    def edit(self):
        
        malop = self.e_malop.get() 
        
        if not malop:
            messagebox.showwarning("Chưa chọn lớp cần sửa")
            return

        ten = self.e_tenlop.get().strip()
        makhoa = self.cbb_khoa.get().strip() or None
        nk = self.e_nienkhoa.get().strip()

        sql = "UPDATE lop SET tenlop=%s, makhoa=%s, nienkhoa=%s WHERE malop=%s"
        if self.run_sql(sql, (ten, makhoa, nk, malop)):
            messagebox.showinfo("Cập nhật xong!")
            self.load_data()
            self.reset_form()

    def delete(self):
        malop = self.e_malop.get()
        if not malop:
            messagebox.showwarning("Chưa chọn lớp cần xóa")
            return
            
        if messagebox.askyesno("Xác nhận", f"Xóa lớp {malop}?"):
            sql = "DELETE FROM lop WHERE malop=%s"
            if self.run_sql(sql, (malop,)):
                messagebox.showinfo("Đã xóa", "Xóa thành công!")
                self.load_data()
                self.reset_form()

#Tab Sinh viên

class TabSinhVien(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()
        self.load_lop_combobox()
        self.load_data()

    def build_ui(self):
    
        frm = ttk.LabelFrame(self, text="Thông tin Sinh viên") 
        frm.pack(fill="x", padx=8, pady=8)

        ttk.Label(frm, text="Mã SV (Auto)").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.e_masv = ttk.Entry(frm, width=12)
        self.e_masv.grid(row=0, column=1, padx=4)

        ttk.Label(frm, text="Họ lót").grid(row=0, column=2, sticky="w", padx=4)
        self.e_holot = ttk.Entry(frm, width=25)
        self.e_holot.grid(row=0, column=3, padx=4)

        ttk.Label(frm, text="Tên").grid(row=0, column=4, sticky="w", padx=4)
        self.e_ten = ttk.Entry(frm, width=15)
        self.e_ten.grid(row=0, column=5, padx=4)

        ttk.Label(frm, text="Giới tính").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        self.cbb_gioitinh = ttk.Combobox(frm, values=["Nam", "Nữ", "Khác"], width=10, state="readonly")
        self.cbb_gioitinh.grid(row=1, column=1, padx=4)

        ttk.Label(frm, text="Ngày sinh").grid(row=1, column=2, sticky="w", padx=4)

        self.de_ngaysinh = DateEntry(frm, width=23, date_pattern='yyyy-mm-dd',state="readonly") 
        self.de_ngaysinh.grid(row=1, column=3, padx=4)

        ttk.Label(frm, text="Lớp").grid(row=1, column=4, sticky="w", padx=4)
        self.cbb_lop = ttk.Combobox(frm, width=13, state="readonly")
        self.cbb_lop.grid(row=1, column=5, padx=4)

        
        ttk.Label(frm, text="Quê quán").grid(row=2, column=0, sticky="w", padx=4, pady=4)
        self.e_que = ttk.Entry(frm, width=12)
        self.e_que.grid(row=2, column=1, padx=4)

        ttk.Label(frm, text="Email").grid(row=2, column=2, sticky="w", padx=4)
        self.e_email = ttk.Entry(frm, width=25)
        self.e_email.grid(row=2, column=3, padx=4)

        ttk.Label(frm, text="SĐT").grid(row=2, column=4, sticky="w", padx=4)
        self.e_sdt = ttk.Entry(frm, width=15)
        self.e_sdt.grid(row=2, column=5, padx=4)

        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=8)

        ttk.Button(btns, text="Thêm", command=self.add).pack(side="left", padx=4)
        ttk.Button(btns, text="Sửa", command=self.edit).pack(side="left", padx=4)
        ttk.Button(btns, text="Xóa", command=self.delete).pack(side="left", padx=4)
        ttk.Button(btns, text="Làm mới", command=self.reset_form).pack(side="left", padx=4) # Thay cho Tải lại

        ttk.Label(btns, text="|   Tìm kiếm:").pack(side="left", padx=(20, 5))
        self.e_search = ttk.Entry(btns, width=25)
        self.e_search.pack(side="left", padx=5)
        
        self.e_search.bind("<Return>", lambda event: self.search()) 
        
        ttk.Button(btns, text="Tìm", command=self.search).pack(side="left", padx=2)
        ttk.Button(btns, text="Hủy tìm", command=self.load_data).pack(side="left", padx=2)

        # TREEVIEW
        cols = ("masv", "holot", "ten", "gioitinh", "ngaysinh", "malop", "quequan", "email", "sdt")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=12)
        
        headers = ["Mã SV", "Họ lót", "Tên", "Giới", "Ngày sinh", "Lớp", "Quê", "Email", "SĐT"]
        for col, h in zip(cols, headers):
            self.tree.heading(col, text=h)
            
        self.tree.column("masv", width=60, anchor="center")
        self.tree.column("gioitinh", width=60, anchor="center")
        self.tree.column("ngaysinh", width=90, anchor="center")
        self.tree.column("malop", width=80, anchor="center")

        scrolly = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrolly.set)
        
        self.tree.pack(side="left", fill="both", expand=True, padx=(8,0), pady=5)
        scrolly.pack(side="right", fill="y", pady=5)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    #HÀM
    def run_sql(self, sql, params=(), fetch=False):
        try:
            conn = connect_db()
            if conn is None: return None
            cur = conn.cursor()
            cur.execute(sql, params)
            if fetch:
                res = cur.fetchall()
                conn.close(); return res
            conn.commit(); conn.close(); return True
        except Exception as e:
            messagebox.showerror("Lỗi SQL", str(e))
            return None

    def reset_form(self):
        self.e_masv.config(state="normal") 
        self.e_masv.delete(0, tk.END)
        self.e_holot.delete(0, tk.END)
        self.e_ten.delete(0, tk.END)
        self.cbb_gioitinh.set("")
        self.de_ngaysinh.set_date(datetime.now()) 
        self.cbb_lop.set("")
        self.e_que.delete(0, tk.END)
        self.e_email.delete(0, tk.END)
        self.e_sdt.delete(0, tk.END)
        self.e_search.delete(0, tk.END) 
        try: self.tree.selection_remove(self.tree.selection())
        except: pass

    #CHỨC NĂNG CHÍNH
    def load_lop_combobox(self):
        rows = self.run_sql("SELECT malop FROM lop", fetch=True)
        if rows: self.cbb_lop['values'] = [r[0] for r in rows]

    def load_data(self):
        self.load_lop_combobox()
        for r in self.tree.get_children(): self.tree.delete(r)
        
        sql = "SELECT masv, holot, ten, gioitinh, ngaysinh, malop, quequan, email, sdt FROM sinhvien ORDER BY masv DESC"
        rows = self.run_sql(sql, fetch=True)
        if rows:
            for r in rows: self.tree.insert("", tk.END, values=r)

    def search(self):
        keyword = self.e_search.get().strip()
        if not keyword:
            self.load_data()
            return

        sql = """
            SELECT masv, holot, ten, gioitinh, ngaysinh, malop, quequan, email, sdt 
            FROM sinhvien 
            WHERE ten LIKE %s OR masv LIKE %s OR malop LIKE %s
        """
        search_val = f"%{keyword}%" 
        
        rows = self.run_sql(sql, (search_val, search_val, search_val), fetch=True)
        
        for r in self.tree.get_children(): 
            self.tree.delete(r)
        if rows:
            for r in rows: 
                self.tree.insert("", tk.END, values=r)
        else:
            messagebox.showinfo("Không tìm thấy sinh viên nào!")

    def on_select(self, evt):
        s = self.tree.selection()
        if not s: return
        v = self.tree.item(s[0])['values']
        
        self.reset_form() 

        self.e_masv.insert(0, v[0])
        self.e_masv.config(state="readonly") 
        
        self.e_holot.insert(0, v[1])
        self.e_ten.insert(0, v[2])
        self.cbb_gioitinh.set(v[3] or "")
        
        try:
            self.de_ngaysinh.set_date(v[4])
        except:
            self.de_ngaysinh.set_date(datetime.now())

        self.cbb_lop.set(v[5] or "")
        self.e_que.insert(0, v[6] or "")
        self.e_email.insert(0, v[7] or "")
        self.e_sdt.insert(0, v[8] or "")

    def add(self):
        masv = self.e_masv.get().strip() 
        holot = self.e_holot.get().strip()
        ten = self.e_ten.get().strip()
        gioitinh = self.cbb_gioitinh.get()
        ngs = self.de_ngaysinh.get_date().strftime("%Y-%m-%d")
        malop = self.cbb_lop.get() or None
        que = self.e_que.get().strip()
        email = self.e_email.get().strip()
        sdt = self.e_sdt.get().strip()

        if not ten: 
            messagebox.showwarning("Vui lòng nhập Tên sinh viên")
            return

        try:
            if masv: 
                sql = "INSERT INTO sinhvien(masv, holot, ten, gioitinh, ngaysinh, malop, quequan, email, sdt) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                params = (masv, holot, ten, gioitinh, ngs, malop, que, email, sdt)
            else: 
                sql = "INSERT INTO sinhvien(holot, ten, gioitinh, ngaysinh, malop, quequan, email, sdt) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
                params = (holot, ten, gioitinh, ngs, malop, que, email, sdt)

            if self.run_sql(sql, params):
                messagebox.showinfo("Thêm sinh viên mới xong!")
                self.load_data()
                self.reset_form()
        except Exception as e:
            messagebox.showerror("Lỗi thêm", str(e))

    def edit(self):
        masv = self.e_masv.get()
        if not masv:
            messagebox.showwarning("Chưa chọn sinh viên để sửa")
            return
            
        holot = self.e_holot.get().strip()
        ten = self.e_ten.get().strip()
        gioitinh = self.cbb_gioitinh.get()
        ngs = self.de_ngaysinh.get_date().strftime("%Y-%m-%d")
        malop = self.cbb_lop.get() or None
        que = self.e_que.get().strip()
        email = self.e_email.get().strip()
        sdt = self.e_sdt.get().strip()

        sql = """UPDATE sinhvien SET holot=%s, ten=%s, gioitinh=%s, ngaysinh=%s, 
                 malop=%s, quequan=%s, email=%s, sdt=%s WHERE masv=%s"""
        params = (holot, ten, gioitinh, ngs, malop, que, email, sdt, masv)
        
        if self.run_sql(sql, params):
            messagebox.showinfo("Cập nhật thành công!")
            self.load_data()
            self.reset_form()

    def delete(self):
        masv = self.e_masv.get()
        if not masv: return
        
        if messagebox.askyesno("Xóa", f"Xóa sinh viên có mã {masv}?"):
            if self.run_sql("DELETE FROM sinhvien WHERE masv=%s", (masv,)):
                messagebox.showinfo("OK", "Đã xóa sinh viên!")
                self.load_data()
                self.reset_form()

#Tab Môn học
class TabMonHoc(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()
        self.load_data()

    def build_ui(self):
        frm = ttk.Frame(self)
        frm.pack(fill="x", padx=8, pady=8)

        # Mã MH
        ttk.Label(frm, text="Mã MH").grid(row=0, column=0, sticky="w")
        self.e_mamh = ttk.Entry(frm, width=12)
        self.e_mamh.grid(row=0, column=1, padx=4)

        # Tên MH
        ttk.Label(frm, text="Tên MH").grid(row=0, column=2, sticky="w")
        self.e_tenmh = ttk.Entry(frm, width=30) # Tăng width xíu cho rộng rãi
        self.e_tenmh.grid(row=0, column=3, padx=4)

        # Số tín chỉ
        ttk.Label(frm, text="Số TC").grid(row=0, column=4, sticky="w")
        self.e_tc = ttk.Entry(frm, width=6)
        self.e_tc.grid(row=0, column=5, padx=4)

        # Các nút chức năng
        ttk.Button(frm, text="Thêm", command=self.add).grid(row=0, column=6, padx=4)
        ttk.Button(frm, text="Sửa", command=self.edit).grid(row=0, column=7, padx=4)
        ttk.Button(frm, text="Xóa", command=self.delete).grid(row=0, column=8, padx=4)
        ttk.Button(frm, text="Làm mới", command=self.reset_form).grid(row=0, column=9, padx=4)

        #TREEVIEW
        cols = ("mamh", "tenmh", "sotinchi")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=14)
        
        # Đặt tên cột
        self.tree.heading("mamh", text="MÃ MH")
        self.tree.heading("tenmh", text="TÊN MÔN HỌC")
        self.tree.heading("sotinchi", text="SỐ TC")
        
        self.tree.column("mamh", width=100, anchor="center")
        self.tree.column("sotinchi", width=80, anchor="center")
        self.tree.column("tenmh", width=300)

        scrolly = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrolly.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(8,0), pady=(4,8))
        scrolly.pack(side="right", fill="y", pady=(4,8))

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    #HÀM
    def run_sql(self, sql, params=(), fetch=False):
        try:
            conn = connect_db()
            if conn is None: return None
            cur = conn.cursor()
            cur.execute(sql, params)
            if fetch:
                res = cur.fetchall()
                conn.close(); return res
            conn.commit(); conn.close(); return True
        except Exception as e:
            messagebox.showerror("Lỗi SQL", str(e))
            return None

    def reset_form(self):
        """Xóa trắng form và MỞ KHÓA mã môn"""
        self.e_mamh.config(state="normal") # Mở khóa trước khi xóa
        self.e_mamh.delete(0, tk.END)
        self.e_tenmh.delete(0, tk.END)
        self.e_tc.delete(0, tk.END)
        try: 
            self.tree.selection_remove(self.tree.selection())
        except: 
            pass

    def load_data(self):
        for r in self.tree.get_children(): 
            self.tree.delete(r)
        
        rows = self.run_sql("SELECT mamh, tenmh, sotinchi FROM monhoc", fetch=True)
        if rows:
            for r in rows: self.tree.insert("", tk.END, values=r)

    def on_select(self, evt):
        sel = self.tree.selection()
        if not sel: return
        v = self.tree.item(sel[0])['values']
        
        self.reset_form()

        self.e_mamh.insert(0, v[0])
        self.e_tenmh.insert(0, v[1])
        self.e_tc.insert(0, v[2])
        
        self.e_mamh.config(state="readonly")

    def add(self):
        mamh = self.e_mamh.get().strip()
        ten = self.e_tenmh.get().strip()
        
        try:
            tc_str = self.e_tc.get().strip()
            tc = int(tc_str) if tc_str else 0
            if tc < 0: 
                raise ValueError 
        except:
            messagebox.showwarning("Lỗi nhập liệu", "Số tín chỉ phải là số nguyên dương!")
            return

        if not mamh or not ten:
            messagebox.showwarning("Thiếu", "Vui lòng nhập Mã môn và Tên môn")
            return
        sql = "INSERT INTO monhoc(mamh, tenmh, sotinchi) VALUES (%s, %s, %s)"
        if self.run_sql(sql, (mamh, ten, tc)):
            messagebox.showinfo("Thành công", "Đã thêm môn học mới!")
            self.load_data()
            self.reset_form()

    def edit(self):
        mamh = self.e_mamh.get()
        if not mamh:
            messagebox.showwarning("Lỗi", "Chưa chọn môn để sửa")
            return

        ten = self.e_tenmh.get().strip()
        try:
            tc = int(self.e_tc.get().strip() or 0)
            if tc < 0: raise ValueError
        except:
            messagebox.showwarning("Lỗi", "Số tín chỉ phải là số nguyên dương!")
            return

        sql = "UPDATE monhoc SET tenmh=%s, sotinchi=%s WHERE mamh=%s"
        if self.run_sql(sql, (ten, tc, mamh)):
            messagebox.showinfo("Thành công", "Cập nhật xong!")
            self.load_data()
            self.reset_form()

    def delete(self):
        mamh = self.e_mamh.get()
        if not mamh:
            messagebox.showwarning("Lỗi", "Chưa chọn môn để xóa")
            return

        if messagebox.askyesno("Cảnh báo", f"Xóa môn {mamh}"):
            if self.run_sql("DELETE FROM monhoc WHERE mamh=%s", (mamh,)):
                messagebox.showinfo("Đã xóa", "Xóa thành công!")
                self.load_data()
                self.reset_form()

#Tab Điểm
class TabDiem(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()
        self.load_comboboxes() 
        self.load_data()       

    def build_ui(self):
        frm = ttk.LabelFrame(self, text="Nhập Điểm")
        frm.pack(fill="x", padx=8, pady=8)

        ttk.Label(frm, text="Sinh Viên:").grid(row=0, column=0, sticky="w", padx=5)
        self.cbb_masv = ttk.Combobox(frm, width=25, state="readonly") 
        self.cbb_masv.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frm, text="Môn Học:").grid(row=0, column=2, sticky="w", padx=5)
        self.cbb_mamh = ttk.Combobox(frm, width=25, state="readonly")
        self.cbb_mamh.grid(row=0, column=3, padx=5, pady=5)

        # Hàng 2: Nhập điểm
        ttk.Label(frm, text="Điểm Quá trình:").grid(row=1, column=0, sticky="w", padx=5)
        self.e_diemqt = ttk.Entry(frm, width=10)
        self.e_diemqt.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frm, text="Điểm Thi:").grid(row=1, column=2, sticky="w", padx=5)
        self.e_diemthi = ttk.Entry(frm, width=10)
        self.e_diemthi.grid(row=1, column=3, padx=5, pady=5)

        # Hàng 3: Nút bấm
        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=2, column=0, columnspan=4, pady=10)
        
        ttk.Button(btn_frame, text="Lưu Điểm (Thêm/Sửa)", command=self.save_score).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Xóa", command=self.delete).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Làm mới", command=self.reset_form).pack(side="left", padx=5)

        f_filter = ttk.LabelFrame(self, text="Bộ Lọc")
        f_filter.pack(fill="x", padx=8, pady=(0, 8))
        
        ttk.Label(f_filter, text="Xem điểm của Lớp:").pack(side="left", padx=5)
        self.cbb_filter_lop = ttk.Combobox(f_filter, width=15, state="readonly")
        self.cbb_filter_lop.pack(side="left", padx=5)
        
        ttk.Button(f_filter, text="Lọc ngay", command=self.filter_by_class).pack(side="left", padx=5)
        ttk.Button(f_filter, text="Hiện tất cả", command=self.load_data).pack(side="left", padx=5)

        #TREEVIEW
        cols = ("masv", "tensv", "mamh", "tenmh", "diemqt", "diemthi", "diemtb")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=14)
        
        headers = ["Mã SV", "Họ Tên", "Mã MH", "Tên Môn", "Đ.QT", "Đ.Thi", "Đ.TB"]
        for col, h in zip(cols, headers):
            self.tree.heading(col, text=h)
            
        self.tree.column("masv", width=60, anchor="center")
        self.tree.column("mamh", width=60, anchor="center")
        self.tree.column("diemqt", width=50, anchor="center")
        self.tree.column("diemthi", width=50, anchor="center")
        self.tree.column("diemtb", width=50, anchor="center")
        self.tree.column("tensv", width=150)
        self.tree.column("tenmh", width=150)

        scrolly = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrolly.set)
        
        self.tree.pack(side="left", fill="both", expand=True, padx=(8,0), pady=5)
        scrolly.pack(side="right", fill="y", pady=5)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    #HÀM HỖ TRỢ
    def run_sql(self, sql, params=(), fetch=False):
        try:
            conn = connect_db()
            if conn is None: return None
            cur = conn.cursor()
            cur.execute(sql, params)
            if fetch:
                res = cur.fetchall()
                conn.close(); return res
            conn.commit(); conn.close(); return True
        except Exception as e:
            messagebox.showerror("Lỗi SQL", str(e))
            return None

    def reset_form(self):
        self.cbb_masv.set("")
        self.cbb_masv.config(state="readonly") 
        self.cbb_mamh.set("")
        self.cbb_mamh.config(state="readonly")
        self.e_diemqt.delete(0, tk.END)
        self.e_diemthi.delete(0, tk.END)
        try: self.tree.selection_remove(self.tree.selection())
        except: pass

    def load_comboboxes(self):
        sql_sv = "SELECT masv, holot, ten FROM sinhvien"
        rows_sv = self.run_sql(sql_sv, fetch=True)
        if rows_sv:
            self.cbb_masv['values'] = [f"{r[0]} - {r[1]} {r[2]}" for r in rows_sv]

        sql_mh = "SELECT mamh, tenmh FROM monhoc"
        rows_mh = self.run_sql(sql_mh, fetch=True)
        if rows_mh:
            self.cbb_mamh['values'] = [f"{r[0]} - {r[1]}" for r in rows_mh]

        sql_lop = "SELECT malop FROM lop"
        rows_lop = self.run_sql(sql_lop, fetch=True)
        if rows_lop:
            self.cbb_filter_lop['values'] = [r[0] for r in rows_lop]

    def load_data(self):
        for r in self.tree.get_children(): 
            self.tree.delete(r)

        sql = """
            SELECT d.masv, CONCAT(s.holot, ' ', s.ten), 
                   d.mamh, m.tenmh, 
                   d.diemqt, d.diemthi, d.diemtb
            FROM diem d
            JOIN sinhvien s ON d.masv = s.masv
            JOIN monhoc m ON d.mamh = m.mamh
        """
        rows = self.run_sql(sql, fetch=True)
        if rows:
            for r in rows: self.tree.insert("", tk.END, values=r)

    def filter_by_class(self):
        malop = self.cbb_filter_lop.get().strip()
        if not malop:
            self.load_data(); 
            return 

        sql = """
            SELECT d.masv, CONCAT(s.holot, ' ', s.ten), 
                   d.mamh, m.tenmh, 
                   d.diemqt, d.diemthi, d.diemtb
            FROM diem d
            JOIN sinhvien s ON d.masv = s.masv
            JOIN monhoc m ON d.mamh = m.mamh
            WHERE s.malop = %s
        """
        for r in self.tree.get_children(): 
            self.tree.delete(r)
        rows = self.run_sql(sql, (malop,), fetch=True)
        if rows:
            for r in rows: 
                self.tree.insert("", tk.END, values=r)
        else:
            messagebox.showinfo("Lớp này chưa có điểm")

    def save_score(self):
        raw_sv = self.cbb_masv.get()
        raw_mh = self.cbb_mamh.get()

        if not raw_sv or not raw_mh:
            messagebox.showwarning("Vui lòng chọn Sinh viên và Môn học")
            return

        masv = raw_sv.split(" - ")[0].strip()
        mamh = raw_mh.split(" - ")[0].strip()

        try:
            dqt = float(self.e_diemqt.get().strip() or 0)
            dthi = float(self.e_diemthi.get().strip() or 0)
            if not (0 <= dqt <= 10) or not (0 <= dthi <= 10):
                raise ValueError 
        except:
            messagebox.showwarning("Điểm phải là số từ 0 đến 10")
            return

        dtb = round((dqt + dthi*2) / 3, 2)

        try:
            check_sql = "SELECT 1 FROM diem WHERE masv=%s AND mamh=%s"
            exists = self.run_sql(check_sql, (masv, mamh), fetch=True)

            if exists:
                sql = "UPDATE diem SET diemqt=%s, diemthi=%s, diemtb=%s WHERE masv=%s AND mamh=%s"
                msg = "Cập nhật điểm thành công!"
                self.run_sql(sql, (dqt, dthi, dtb, masv, mamh))
            else:
                sql = "INSERT INTO diem(masv, mamh, diemqt, diemthi, diemtb) VALUES (%s, %s, %s, %s, %s)"
                msg = "Nhập điểm mới thành công!"
                self.run_sql(sql, (masv, mamh, dqt, dthi, dtb))
            
            messagebox.showinfo(msg)
            self.load_data()
            self.reset_form()

        except Exception as e:
            messagebox.showerror("Lỗi Lưu", str(e))

    def delete(self):
        raw_sv = self.cbb_masv.get()
        raw_mh = self.cbb_mamh.get()
        if not raw_sv or not raw_mh: return

        masv = raw_sv.split(" - ")[0].strip()
        mamh = raw_mh.split(" - ")[0].strip()

        if messagebox.askyesno("Xóa", f"Xóa điểm môn {mamh} của SV {masv}"):
            sql = "DELETE FROM diem WHERE masv=%s AND mamh=%s"
            if self.run_sql(sql, (masv, mamh)):
                messagebox.showinfo("Đã xóa điểm")
                self.load_data()
                self.reset_form()

    def on_select(self, evt):
        sel = self.tree.selection()
        if not sel: return
        v = self.tree.item(sel[0])['values']
        
        self.reset_form()
 
        self.cbb_masv.set(f"{v[0]} - {v[1]}") 
        self.cbb_mamh.set(f"{v[2]} - {v[3]}")

        self.e_diemqt.insert(0, v[4])
        self.e_diemthi.insert(0, v[5])
        
        self.cbb_masv.config(state="disabled") 
        self.cbb_mamh.config(state="disabled")

#Chạy chương trình
if __name__ == "__main__":
    try:
        init_db()
    except Exception as e:
        messagebox.showerror("Lỗi DB init", str(e))
    app = App()
    app.mainloop()
