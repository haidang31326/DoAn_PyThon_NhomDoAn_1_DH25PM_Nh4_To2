# ql_sinhvien.py
# Python 3.x
# Yêu cầu: mysql-connector-python, tkcalendar
# pip install mysql-connector-python tkcalendar

import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import mysql.connector
from datetime import datetime

# ------------------ Cấu hình kết nối MySQL ------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",         # <-- thay bằng password của bạn
    "database": "qlsinhvien" # nếu chưa có, code sẽ cố gắng tạo
}

def connect_db(create_if_missing=True):
    """Kết nối tới MySQL. Nếu database chưa tồn tại, có thể tạo tự động."""
    cfg = DB_CONFIG.copy()
    dbname = cfg.pop("database")
    conn = mysql.connector.connect(**cfg)
    cur = conn.cursor()
    # tạo database nếu cần
    if create_if_missing:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {dbname} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.commit()
    conn.close()
    # kết nối tới database
    cfg2 = DB_CONFIG.copy()
    return mysql.connector.connect(**cfg2)

# ------------------ Tạo cấu trúc bảng nếu chưa tồn tại ------------------
def init_db():
    conn = connect_db()
    cur = conn.cursor()
    # tạo các bảng theo thứ tự an toàn
    cur.execute("""
    CREATE TABLE IF NOT EXISTS khoa (
        makhoa VARCHAR(10) PRIMARY KEY,
        tenkhoa VARCHAR(100) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS lop (
        malop VARCHAR(10) PRIMARY KEY,
        tenlop VARCHAR(100) NOT NULL,
        makhoa VARCHAR(10),
        nienkhoa VARCHAR(10),
        FOREIGN KEY (makhoa) REFERENCES khoa(makhoa) ON DELETE SET NULL ON UPDATE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    cur.execute("""
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
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS monhoc (
        mamh VARCHAR(10) PRIMARY KEY,
        tenmh VARCHAR(100) NOT NULL,
        sotinchi INT DEFAULT 0
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS diem (
        masv INT,
        mamh VARCHAR(10),
        diemqt FLOAT,
        diemthi FLOAT,
        diemtb FLOAT,
        PRIMARY KEY (masv, mamh),
        FOREIGN KEY (masv) REFERENCES sinhvien(masv) ON DELETE CASCADE ON UPDATE CASCADE,
        FOREIGN KEY (mamh) REFERENCES monhoc(mamh) ON DELETE CASCADE ON UPDATE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    conn.commit()
    cur.close()
    conn.close()

# ------------------ GUI chính ------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Quản lý Sinh viên - Tkinter + MySQL")
        self.geometry("1000x650")
        self.resizable(True, True)

        # Notebook chứa các tab
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True)

        # khởi tạo tab
        self.tab_khoa = TabKhoa(self.nb)
        self.tab_lop = TabLop(self.nb)
        self.tab_sv = TabSinhVien(self.nb)
        self.tab_mh = TabMonHoc(self.nb)
        self.tab_diem = TabDiem(self.nb)

        self.nb.add(self.tab_khoa, text="Khoa")
        self.nb.add(self.tab_lop, text="Lớp")
        self.nb.add(self.tab_sv, text="Sinh viên")
        self.nb.add(self.tab_mh, text="Môn học")
        self.nb.add(self.tab_diem, text="Điểm")

# ------------------ Tab Khoa ------------------
class TabKhoa(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()
        self.load_data()

    def build_ui(self):
        frm_top = ttk.Frame(self)
        frm_top.pack(fill="x", padx=8, pady=8)

        ttk.Label(frm_top, text="Mã khoa").grid(row=0, column=0, sticky="w")
        self.e_makhoa = ttk.Entry(frm_top, width=15); self.e_makhoa.grid(row=0, column=1, padx=4)
        ttk.Label(frm_top, text="Tên khoa").grid(row=0, column=2, sticky="w")
        self.e_tenkhoa = ttk.Entry(frm_top, width=40); self.e_tenkhoa.grid(row=0, column=3, padx=4)

        ttk.Button(frm_top, text="Thêm", command=self.add).grid(row=0, column=4, padx=4)
        ttk.Button(frm_top, text="Sửa", command=self.edit).grid(row=0, column=5, padx=4)
        ttk.Button(frm_top, text="Xóa", command=self.delete).grid(row=0, column=6, padx=4)
        ttk.Button(frm_top, text="Tải lại", command=self.load_data).grid(row=0, column=7, padx=4)

        # treeview
        cols = ("makhoa", "tenkhoa")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=15)
        for c in cols: self.tree.heading(c, text=c.upper())
        self.tree.pack(fill="both", expand=True, padx=8, pady=(0,8))
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def run_sql(self, sql, params=(), fetch=False):
        conn = connect_db()
        cur = conn.cursor()
        cur.execute(sql, params)
        res = None
        if fetch:
            res = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return res

    def load_data(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        rows = self.run_sql("SELECT makhoa, tenkhoa FROM khoa", fetch=True)
        for r in rows:
            self.tree.insert("", tk.END, values=r)

    def add(self):
        mak = self.e_makhoa.get().strip()
        ten = self.e_tenkhoa.get().strip()
        if not mak or not ten:
            messagebox.showwarning("Thiếu", "Nhập mã khoa và tên khoa")
            return
        try:
            self.run_sql("INSERT INTO khoa(makhoa, tenkhoa) VALUES (%s,%s)", (mak,ten))
            self.load_data()
            self.e_makhoa.delete(0, tk.END); self.e_tenkhoa.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def on_select(self, evt):
        sel = self.tree.selection()
        if not sel: return
        v = self.tree.item(sel[0])["values"]
        self.e_makhoa.delete(0, tk.END); self.e_makhoa.insert(0, v[0])
        self.e_tenkhoa.delete(0, tk.END); self.e_tenkhoa.insert(0, v[1])

    def edit(self):
        mak = self.e_makhoa.get().strip()
        ten = self.e_tenkhoa.get().strip()
        if not mak: messagebox.showwarning("Thiếu", "Chọn hoặc nhập mã khoa"); return
        try:
            self.run_sql("UPDATE khoa SET tenkhoa=%s WHERE makhoa=%s", (ten, mak))
            self.load_data()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def delete(self):
        mak = self.e_makhoa.get().strip()
        if not mak: messagebox.showwarning("Thiếu", "Chọn khoa để xóa"); return
        if not messagebox.askyesno("Xác nhận", f"Xóa khoa {mak}? (các lớp thuộc khoa sẽ bị NULL makhoa)"):
            return
        try:
            self.run_sql("DELETE FROM khoa WHERE makhoa=%s", (mak,))
            self.load_data()
            self.e_makhoa.delete(0, tk.END); self.e_tenkhoa.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

# ------------------ Tab Lớp ------------------
class TabLop(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()
        self.load_khoa_combobox()
        self.load_data()

    def build_ui(self):
        frm_top = ttk.Frame(self); frm_top.pack(fill="x", padx=8, pady=8)
        ttk.Label(frm_top, text="Mã lớp").grid(row=0,column=0); self.e_malop = ttk.Entry(frm_top, width=12); self.e_malop.grid(row=0,column=1,padx=4)
        ttk.Label(frm_top, text="Tên lớp").grid(row=0,column=2); self.e_tenlop = ttk.Entry(frm_top, width=25); self.e_tenlop.grid(row=0,column=3,padx=4)
        ttk.Label(frm_top, text="Khoa").grid(row=1,column=0); self.cbb_khoa = ttk.Combobox(frm_top,width=12); self.cbb_khoa.grid(row=1,column=1,padx=4)
        ttk.Label(frm_top, text="Niên khóa").grid(row=1,column=2); self.e_nienkhoa = ttk.Entry(frm_top, width=12); self.e_nienkhoa.grid(row=1,column=3,padx=4)

        ttk.Button(frm_top, text="Thêm", command=self.add).grid(row=0,column=4,padx=4)
        ttk.Button(frm_top, text="Sửa", command=self.edit).grid(row=0,column=5,padx=4)
        ttk.Button(frm_top, text="Xóa", command=self.delete).grid(row=0,column=6,padx=4)
        ttk.Button(frm_top, text="Tải lại", command=self.load_data).grid(row=0,column=7,padx=4)

        cols = ("malop","tenlop","makhoa","nienkhoa")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=14)
        for c in cols: self.tree.heading(c, text=c.upper())
        self.tree.pack(fill="both", expand=True, padx=8, pady=(0,8))
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def run_sql(self, sql, params=(), fetch=False):
        conn = connect_db()
        cur = conn.cursor()
        cur.execute(sql, params)
        res = None
        if fetch: res = cur.fetchall()
        conn.commit()
        cur.close(); conn.close()
        return res

    def load_khoa_combobox(self):
        rows = self.run_sql("SELECT makhoa FROM khoa", fetch=True)
        items = [r[0] for r in rows] if rows else []
        self.cbb_khoa['values'] = items

    def load_data(self):
        self.load_khoa_combobox()
        for r in self.tree.get_children(): self.tree.delete(r)
        rows = self.run_sql("SELECT malop, tenlop, makhoa, nienkhoa FROM lop", fetch=True)
        if rows:
            for r in rows: self.tree.insert("", tk.END, values=r)

    def add(self):
        malop = self.e_malop.get().strip()
        ten = self.e_tenlop.get().strip()
        makhoa = self.cbb_khoa.get().strip() or None
        nk = self.e_nienkhoa.get().strip()
        if not malop or not ten:
            messagebox.showwarning("Thiếu", "Nhập mã lớp và tên lớp"); return
        try:
            self.run_sql("INSERT INTO lop(malop, tenlop, makhoa, nienkhoa) VALUES (%s,%s,%s,%s)", (malop,ten,makhoa,nk))
            self.load_data()
            self.e_malop.delete(0, tk.END); self.e_tenlop.delete(0, tk.END); self.e_nienkhoa.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def on_select(self, evt):
        s = self.tree.selection(); 
        if not s: return
        v = self.tree.item(s[0])['values']
        self.e_malop.delete(0, tk.END); self.e_malop.insert(0, v[0])
        self.e_tenlop.delete(0, tk.END); self.e_tenlop.insert(0, v[1])
        self.cbb_khoa.set(v[2] or "")
        self.e_nienkhoa.delete(0, tk.END); self.e_nienkhoa.insert(0, v[3] or "")

    def edit(self):
        malop = self.e_malop.get().strip()
        ten = self.e_tenlop.get().strip()
        makhoa = self.cbb_khoa.get().strip() or None
        nk = self.e_nienkhoa.get().strip()
        if not malop: messagebox.showwarning("Thiếu", "Chọn mã lớp"); return
        try:
            self.run_sql("UPDATE lop SET tenlop=%s, makhoa=%s, nienkhoa=%s WHERE malop=%s", (ten, makhoa, nk, malop))
            self.load_data()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def delete(self):
        malop = self.e_malop.get().strip()
        if not malop: messagebox.showwarning("Thiếu", "Chọn lớp để xóa"); return
        if not messagebox.askyesno("Xác nhận", f"Xóa lớp {malop}? (sinh viên thuộc lớp sẽ bị NULL malop)"):
            return
        try:
            self.run_sql("DELETE FROM lop WHERE malop=%s", (malop,))
            self.load_data()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

# ------------------ Tab Sinh viên ------------------
class TabSinhVien(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()
        self.load_lop_combobox()
        self.load_data()

    def build_ui(self):
        frm = ttk.Frame(self); frm.pack(fill="x", padx=8, pady=8)
        # labels + entries
        labels = ["Mã SV (để trống để tự tăng)","Họ lót","Tên","Giới tính","Ngày sinh","Lớp","Quê quán","Email","SĐT"]
        for i, txt in enumerate(labels):
            ttk.Label(frm, text=txt).grid(row=i//3, column=(i%3)*2, sticky="w", padx=4, pady=2)
        self.e_masv = ttk.Entry(frm, width=10); self.e_masv.grid(row=0, column=1, padx=4)
        self.e_holot = ttk.Entry(frm, width=25); self.e_holot.grid(row=0, column=3, padx=4)
        self.e_ten = ttk.Entry(frm, width=15); self.e_ten.grid(row=0, column=5, padx=4)
        self.cbb_gioitinh = ttk.Combobox(frm, values=["Nam","Nữ","Khác"], width=12); self.cbb_gioitinh.grid(row=1, column=1, padx=4)
        self.de_ngaysinh = DateEntry(frm, date_pattern="yyyy-mm-dd", width=12); self.de_ngaysinh.grid(row=1, column=3, padx=4)
        self.cbb_lop = ttk.Combobox(frm, width=15); self.cbb_lop.grid(row=1, column=5, padx=4)
        self.e_que = ttk.Entry(frm, width=25); self.e_que.grid(row=2, column=1, padx=4)
        self.e_email = ttk.Entry(frm, width=25); self.e_email.grid(row=2, column=3, padx=4)
        self.e_sdt = ttk.Entry(frm, width=15); self.e_sdt.grid(row=2, column=5, padx=4)

        # Buttons
        btns = ttk.Frame(self); btns.pack(fill="x", padx=8)
        ttk.Button(btns, text="Thêm", command=self.add).pack(side="left", padx=4, pady=4)
        ttk.Button(btns, text="Sửa", command=self.edit).pack(side="left", padx=4)
        ttk.Button(btns, text="Xóa", command=self.delete).pack(side="left", padx=4)
        ttk.Button(btns, text="Tải lại", command=self.load_data).pack(side="left", padx=4)
        # search
        ttk.Label(btns, text="Tìm (tên/mã/lớp):").pack(side="left", padx=(20,4))
        self.e_search = ttk.Entry(btns, width=30); self.e_search.pack(side="left", padx=4)
        ttk.Button(btns, text="Tìm", command=self.search).pack(side="left", padx=4)
        ttk.Button(btns, text="Clear", command=self.clear_search).pack(side="left", padx=4)

        # treeview
        cols = ("masv","holot","ten","gioitinh","ngaysinh","malop","quequan","email","sdt")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=14)
        for c in cols: self.tree.heading(c, text=c.upper())
        self.tree.pack(fill="both", expand=True, padx=8, pady=(4,8))
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def run_sql(self, sql, params=(), fetch=False):
        conn = connect_db()
        cur = conn.cursor()
        cur.execute(sql, params)
        res = None
        if fetch: res = cur.fetchall()
        conn.commit()
        cur.close(); conn.close()
        return res

    def load_lop_combobox(self):
        rows = self.run_sql("SELECT malop FROM lop", fetch=True)
        items = [r[0] for r in rows] if rows else []
        self.cbb_lop['values'] = items

    def load_data(self):
        self.load_lop_combobox()
        for r in self.tree.get_children(): self.tree.delete(r)
        rows = self.run_sql("SELECT masv, holot, ten, gioitinh, ngaysinh, malop, quequan, email, sdt FROM sinhvien", fetch=True)
        if rows:
            for r in rows:
                self.tree.insert("", tk.END, values=r)

    def add(self):
        # masv optional
        masv = self.e_masv.get().strip()
        holot = self.e_holot.get().strip()
        ten = self.e_ten.get().strip()
        gioitinh = self.cbb_gioitinh.get().strip()
        ngs = self.de_ngaysinh.get_date().strftime("%Y-%m-%d")
        malop = self.cbb_lop.get().strip() or None
        que = self.e_que.get().strip()
        email = self.e_email.get().strip()
        sdt = self.e_sdt.get().strip()

        if not holot or not ten:
            messagebox.showwarning("Thiếu", "Nhập họ lót và tên"); return

        try:
            if masv:
                # cố gắng chèn có mã cụ thể
                self.run_sql("INSERT INTO sinhvien(masv, holot, ten, gioitinh, ngaysinh, malop, quequan, email, sdt) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                             (masv, holot, ten, gioitinh, ngs, malop, que, email, sdt))
            else:
                self.run_sql("INSERT INTO sinhvien(holot, ten, gioitinh, ngaysinh, malop, quequan, email, sdt) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                             (holot, ten, gioitinh, ngs, malop, que, email, sdt))
            self.load_data()
            self.clear_inputs()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def on_select(self, evt):
        s = self.tree.selection()
        if not s: return
        v = self.tree.item(s[0])['values']
        # masv, holot, ten, gioitinh, ngaysinh, malop, quequan, email, sdt
        self.e_masv.delete(0, tk.END); self.e_masv.insert(0, v[0])
        self.e_holot.delete(0, tk.END); self.e_holot.insert(0, v[1])
        self.e_ten.delete(0, tk.END); self.e_ten.insert(0, v[2])
        self.cbb_gioitinh.set(v[3] or "")
        try:
            self.de_ngaysinh.set_date(v[4])
        except:
            pass
        self.cbb_lop.set(v[5] or "")
        self.e_que.delete(0, tk.END); self.e_que.insert(0, v[6] or "")
        self.e_email.delete(0, tk.END); self.e_email.insert(0, v[7] or "")
        self.e_sdt.delete(0, tk.END); self.e_sdt.insert(0, v[8] or "")

    def clear_inputs(self):
        self.e_masv.delete(0, tk.END)
        self.e_holot.delete(0, tk.END)
        self.e_ten.delete(0, tk.END)
        self.cbb_gioitinh.set("")
        self.de_ngaysinh.set_date(datetime(2000,1,1))
        self.cbb_lop.set("")
        self.e_que.delete(0, tk.END); self.e_email.delete(0, tk.END); self.e_sdt.delete(0, tk.END)

    def edit(self):
        masv = self.e_masv.get().strip()
        if not masv:
            messagebox.showwarning("Thiếu", "Chọn sinh viên (mã) để sửa"); return
        holot = self.e_holot.get().strip(); ten = self.e_ten.get().strip()
        gioitinh = self.cbb_gioitinh.get().strip()
        ngs = self.de_ngaysinh.get_date().strftime("%Y-%m-%d")
        malop = self.cbb_lop.get().strip() or None
        que = self.e_que.get().strip(); email = self.e_email.get().strip(); sdt = self.e_sdt.get().strip()
        try:
            self.run_sql("UPDATE sinhvien SET holot=%s, ten=%s, gioitinh=%s, ngaysinh=%s, malop=%s, quequan=%s, email=%s, sdt=%s WHERE masv=%s",
                         (holot, ten, gioitinh, ngs, malop, que, email, sdt, masv))
            self.load_data()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def delete(self):
        masv = self.e_masv.get().strip()
        if not masv:
            messagebox.showwarning("Thiếu", "Chọn sinh viên để xóa"); return
        if not messagebox.askyesno("Xác nhận", f"Xóa sinh viên mã {masv}? (toàn bộ điểm sẽ bị xóa)"):
            return
        try:
            self.run_sql("DELETE FROM sinhvien WHERE masv=%s", (masv,))
            self.load_data(); self.clear_inputs()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def search(self):
        key = self.e_search.get().strip()
        if not key:
            self.load_data(); return
        q = "%" + key + "%"
        rows = self.run_sql("SELECT masv, holot, ten, gioitinh, ngaysinh, malop, quequan, email, sdt FROM sinhvien WHERE ten LIKE %s OR holot LIKE %s OR CAST(masv AS CHAR) LIKE %s OR malop LIKE %s",
                            (q,q,q,q), fetch=True)
        for r in self.tree.get_children(): self.tree.delete(r)
        if rows:
            for r in rows: self.tree.insert("", tk.END, values=r)

    def clear_search(self):
        self.e_search.delete(0, tk.END); self.load_data()

# ------------------ Tab Môn học ------------------
class TabMonHoc(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()
        self.load_data()

    def build_ui(self):
        frm = ttk.Frame(self); frm.pack(fill="x", padx=8, pady=8)
        ttk.Label(frm, text="Mã MH").grid(row=0,column=0); self.e_mamh = ttk.Entry(frm, width=12); self.e_mamh.grid(row=0,column=1,padx=4)
        ttk.Label(frm, text="Tên MH").grid(row=0,column=2); self.e_tenmh = ttk.Entry(frm, width=40); self.e_tenmh.grid(row=0,column=3,padx=4)
        ttk.Label(frm, text="Số TC").grid(row=0,column=4); self.e_tc = ttk.Entry(frm, width=6); self.e_tc.grid(row=0,column=5,padx=4)

        ttk.Button(frm, text="Thêm", command=self.add).grid(row=0,column=6,padx=4)
        ttk.Button(frm, text="Sửa", command=self.edit).grid(row=0,column=7,padx=4)
        ttk.Button(frm, text="Xóa", command=self.delete).grid(row=0,column=8,padx=4)
        ttk.Button(frm, text="Tải lại", command=self.load_data).grid(row=0,column=9,padx=4)

        cols = ("mamh","tenmh","sotinchi")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=14)
        for c in cols: self.tree.heading(c, text=c.upper())
        self.tree.pack(fill="both", expand=True, padx=8, pady=(4,8))
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def run_sql(self, sql, params=(), fetch=False):
        conn = connect_db(); cur = conn.cursor(); cur.execute(sql, params)
        res = None
        if fetch: res = cur.fetchall()
        conn.commit(); cur.close(); conn.close()
        return res

    def load_data(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        rows = self.run_sql("SELECT mamh, tenmh, sotinchi FROM monhoc", fetch=True)
        if rows:
            for r in rows: self.tree.insert("", tk.END, values=r)

    def add(self):
        mamh = self.e_mamh.get().strip(); ten = self.e_tenmh.get().strip()
        try:
            tc = int(self.e_tc.get().strip() or 0)
        except:
            messagebox.showwarning("Sai", "Số tín chỉ phải là số nguyên"); return
        if not mamh or not ten: messagebox.showwarning("Thiếu", "Nhập mã và tên môn"); return
        try:
            self.run_sql("INSERT INTO monhoc(mamh, tenmh, sotinchi) VALUES (%s,%s,%s)", (mamh,ten,tc))
            self.load_data(); self.e_mamh.delete(0,tk.END); self.e_tenmh.delete(0,tk.END); self.e_tc.delete(0,tk.END)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def on_select(self, evt):
        sel = self.tree.selection(); 
        if not sel: return
        v = self.tree.item(sel[0])['values']
        self.e_mamh.delete(0,tk.END); self.e_mamh.insert(0, v[0])
        self.e_tenmh.delete(0,tk.END); self.e_tenmh.insert(0, v[1])
        self.e_tc.delete(0,tk.END); self.e_tc.insert(0, v[2])

    def edit(self):
        mamh = self.e_mamh.get().strip(); ten = self.e_tenmh.get().strip()
        try:
            tc = int(self.e_tc.get().strip() or 0)
        except:
            messagebox.showwarning("Sai", "Số tín chỉ phải là số nguyên"); return
        if not mamh: messagebox.showwarning("Thiếu", "Chọn mã môn"); return
        try:
            self.run_sql("UPDATE monhoc SET tenmh=%s, sotinchi=%s WHERE mamh=%s", (ten, tc, mamh))
            self.load_data()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def delete(self):
        mamh = self.e_mamh.get().strip()
        if not mamh: messagebox.showwarning("Thiếu", "Chọn môn để xóa"); return
        if not messagebox.askyesno("Xác nhận", f"Xóa môn {mamh}? (các điểm liên quan sẽ bị xóa)"):
            return
        try:
            self.run_sql("DELETE FROM monhoc WHERE mamh=%s", (mamh,))
            self.load_data()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

# ------------------ Tab Điểm ------------------
class TabDiem(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()
        self.load_comboboxes()
        self.load_data()

    def build_ui(self):
        frm = ttk.Frame(self); frm.pack(fill="x", padx=8, pady=8)
        ttk.Label(frm, text="Mã SV").grid(row=0,column=0); self.cbb_masv = ttk.Combobox(frm, width=10); self.cbb_masv.grid(row=0,column=1,padx=4)
        ttk.Label(frm, text="Môn học").grid(row=0,column=2); self.cbb_mamh = ttk.Combobox(frm, width=12); self.cbb_mamh.grid(row=0,column=3,padx=4)
        ttk.Label(frm, text="Điểm QT").grid(row=0,column=4); self.e_diemqt = ttk.Entry(frm, width=8); self.e_diemqt.grid(row=0,column=5,padx=4)
        ttk.Label(frm, text="Điểm Thi").grid(row=0,column=6); self.e_diemthi = ttk.Entry(frm, width=8); self.e_diemthi.grid(row=0,column=7,padx=4)

        ttk.Button(frm, text="Thêm/Cập nhật", command=self.add_or_update).grid(row=0,column=8,padx=4)
        ttk.Button(frm, text="Xóa", command=self.delete).grid(row=0,column=9,padx=4)
        ttk.Button(frm, text="Tải", command=self.load_data).grid(row=0,column=10,padx=4)

        # filter
        f2 = ttk.Frame(self); f2.pack(fill="x", padx=8, pady=(0,6))
        ttk.Label(f2, text="Lọc theo lớp:").pack(side="left")
        self.cbb_filter_lop = ttk.Combobox(f2, width=12); self.cbb_filter_lop.pack(side="left", padx=4)
        ttk.Button(f2, text="Lọc", command=self.filter_by_class).pack(side="left", padx=4)
        ttk.Button(f2, text="Clear", command=self.load_data).pack(side="left", padx=4)

        cols = ("masv","mamh","diemqt","diemthi","diemtb")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=16)
        for c in cols: self.tree.heading(c, text=c.upper())
        self.tree.pack(fill="both", expand=True, padx=8, pady=(0,8))
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def run_sql(self, sql, params=(), fetch=False):
        conn = connect_db(); cur = conn.cursor(); cur.execute(sql, params)
        res = None
        if fetch: res = cur.fetchall()
        conn.commit(); cur.close(); conn.close()
        return res

    def load_comboboxes(self):
        # masv
        rows = self.run_sql("SELECT masv FROM sinhvien", fetch=True)
        self.cbb_masv['values'] = [r[0] for r in rows] if rows else []
        # mamh
        rows2 = self.run_sql("SELECT mamh FROM monhoc", fetch=True)
        self.cbb_mamh['values'] = [r[0] for r in rows2] if rows2 else []
        # lớp filter
        rows3 = self.run_sql("SELECT malop FROM lop", fetch=True)
        self.cbb_filter_lop['values'] = [r[0] for r in rows3] if rows3 else []

    def load_data(self):
        self.load_comboboxes()
        for r in self.tree.get_children(): self.tree.delete(r)
        rows = self.run_sql("SELECT masv, mamh, diemqt, diemthi, diemtb FROM diem", fetch=True)
        if rows:
            for r in rows: self.tree.insert("", tk.END, values=r)

    def add_or_update(self):
        masv = self.cbb_masv.get().strip(); mamh = self.cbb_mamh.get().strip()
        try:
            dq = float(self.e_diemqt.get().strip() or 0)
            dt = float(self.e_diemthi.get().strip() or 0)
        except:
            messagebox.showwarning("Sai", "Điểm phải là số"); return
        if not masv or not mamh:
            messagebox.showwarning("Thiếu", "Chọn mã sinh viên và mã môn"); return
        diemtb = (dq + dt*2)/3.0
        try:
            # upsert: nếu tồn tại thì cập nhật, không thì chèn
            existing = self.run_sql("SELECT 1 FROM diem WHERE masv=%s AND mamh=%s", (masv,mamh), fetch=True)
            if existing:
                self.run_sql("UPDATE diem SET diemqt=%s, diemthi=%s, diemtb=%s WHERE masv=%s AND mamh=%s", (dq,dt,diemtb,masv,mamh))
            else:
                self.run_sql("INSERT INTO diem(masv, mamh, diemqt, diemthi, diemtb) VALUES (%s,%s,%s,%s,%s)", (masv,mamh,dq,dt,diemtb))
            self.load_data()
            self.clear_inputs()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def on_select(self, evt):
        s = self.tree.selection(); 
        if not s: return
        v = self.tree.item(s[0])['values']
        self.cbb_masv.set(v[0]); self.cbb_mamh.set(v[1])
        self.e_diemqt.delete(0,tk.END); self.e_diemqt.insert(0, v[2] or 0)
        self.e_diemthi.delete(0,tk.END); self.e_diemthi.insert(0, v[3] or 0)

    def delete(self):
        masv = self.cbb_masv.get().strip(); mamh = self.cbb_mamh.get().strip()
        if not masv or not mamh: messagebox.showwarning("Thiếu", "Chọn bản ghi điểm để xóa"); return
        if not messagebox.askyesno("Xác nhận", f"Xóa điểm SV {masv} môn {mamh}?"):
            return
        try:
            self.run_sql("DELETE FROM diem WHERE masv=%s AND mamh=%s", (masv, mamh))
            self.load_data(); self.clear_inputs()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def clear_inputs(self):
        self.cbb_masv.set(""); self.cbb_mamh.set(""); self.e_diemqt.delete(0,tk.END); self.e_diemthi.delete(0,tk.END)

    def filter_by_class(self):
        malop = self.cbb_filter_lop.get().strip()
        if not malop:
            self.load_data(); return
        # lấy danh sách masv của lớp
        rows = self.run_sql("SELECT masv FROM sinhvien WHERE malop=%s", (malop,), fetch=True)
        if not rows:
            messagebox.showinfo("Thông báo", "Không có sinh viên trong lớp này")
            return
        masv_list = [str(r[0]) for r in rows]
        placeholders = ",".join(["%s"]*len(masv_list))
        query = f"SELECT masv, mamh, diemqt, diemthi, diemtb FROM diem WHERE masv IN ({placeholders})"
        rows2 = self.run_sql(query, tuple(masv_list), fetch=True)
        for r in self.tree.get_children(): self.tree.delete(r)
        if rows2:
            for r in rows2: self.tree.insert("", tk.END, values=r)

# ------------------ Chạy chương trình ------------------
if __name__ == "__main__":
    try:
        init_db()
    except Exception as e:
        messagebox.showerror("Lỗi DB init", str(e))
    app = App()
    app.mainloop()
