import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import mysql.connector

#CẤU HÌNH DATABASE
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",      
    "database": "qlsv"
}

#KẾT NỐI DATABASE
def run_sql(sql, params=(), fetch=False):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
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

#GIAO DIỆN CHÍNH
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Quản lý Sinh Viên")
        self.geometry("900x500")
        self.center_window()

        # TẠO MENU
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # Menu Hệ thống
        sys_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Hệ thống", menu=sys_menu)
        sys_menu.add_command(label="Thoát", command=self.quit)

        # Menu Quản lý
        manage_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Quản lý", menu=manage_menu)
        manage_menu.add_command(label="Khoa", command=lambda: self.show_frame("TabKhoa"))
        manage_menu.add_command(label="Lớp", command=lambda: self.show_frame("TabLop"))
        manage_menu.add_command(label="Môn học", command=lambda: self.show_frame("TabMonHoc"))
        manage_menu.add_separator()
        manage_menu.add_command(label="Sinh viên", command=lambda: self.show_frame("TabSinhVien"))

        # Menu Kết quả
        res_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Kết quả", menu=res_menu)
        res_menu.add_command(label="Bảng điểm", command=lambda: self.show_frame("TabDiem"))

        # KHUNG CHỨA TAB
        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        for F in (TabKhoa, TabLop, TabMonHoc, TabSinhVien, TabDiem):
            page_name = F.__name__
            frame = F(parent=self.container)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self.show_frame("TabSinhVien")

    def center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 1000) // 2
        y = (self.winfo_screenheight() - 600) // 2
        self.geometry(f"+{x}+{y}")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        if hasattr(frame, "load_data"): frame.load_data()

#CÁC TAB CHỨC NĂNG

class BaseTab(tk.Frame):
    def __init__(self, parent): 
        super().__init__(parent)
        self.title_font = ("Arial", 16, "bold")
    def add_title(self, text): 
        tk.Label(self, text=text, font=self.title_font, fg="#2c3e50").pack(pady=15)

#TAB KHOA
class TabKhoa(BaseTab):
    def __init__(self, parent):
        super().__init__(parent); self.add_title("QUẢN LÝ KHOA")
        frm = tk.Frame(self); frm.pack(pady=10)
        tk.Label(frm, text="Mã Khoa:").grid(row=0, column=0); self.e_ma = tk.Entry(frm); self.e_ma.grid(row=0, column=1, padx=5)
        tk.Label(frm, text="Tên Khoa:").grid(row=0, column=2); self.e_ten = tk.Entry(frm, width=30); self.e_ten.grid(row=0, column=3, padx=5)
        btn = tk.Frame(self); btn.pack(pady=5)
        tk.Button(btn, text="Thêm", command=self.add, bg="#2ecc71").pack(side="left", padx=5)
        tk.Button(btn, text="Xóa", command=self.delete, bg="#e74c3c").pack(side="left", padx=5)
        self.tree = ttk.Treeview(self, columns=("ma","ten"), show="headings", height=10); self.tree.pack(padx=20, fill="both", expand=True)
        self.tree.heading("ma", text="MÃ"); self.tree.heading("ten", text="TÊN KHOA")
        self.tree.bind("<<TreeviewSelect>>", self.sel)
    def load_data(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in run_sql("SELECT * FROM khoa", fetch=True): self.tree.insert("", "end", values=r)
    def add(self): run_sql("INSERT INTO khoa VALUES (%s,%s)", (self.e_ma.get(), self.e_ten.get())); self.load_data()
    def delete(self): run_sql("DELETE FROM khoa WHERE makhoa=%s", (self.e_ma.get(),)); self.load_data()
    def sel(self,e): 
        s=self.tree.selection()
        if s: v=self.tree.item(s[0])['values']; self.e_ma.delete(0,tk.END); self.e_ma.insert(0,v[0]); self.e_ten.delete(0,tk.END); self.e_ten.insert(0,v[1])

#TAB LỚP
class TabLop(BaseTab):
    def __init__(self, parent):
        super().__init__(parent); self.add_title("QUẢN LÝ LỚP")
        frm = tk.Frame(self); frm.pack()
        tk.Label(frm, text="Mã Lớp:").grid(row=0, column=0); self.e_ma=tk.Entry(frm); self.e_ma.grid(row=0, column=1)
        tk.Label(frm, text="Tên Lớp:").grid(row=0, column=2); self.e_ten=tk.Entry(frm); self.e_ten.grid(row=0, column=3)
        tk.Label(frm, text="Khoa:").grid(row=1, column=0); self.cbb=ttk.Combobox(frm); self.cbb.grid(row=1, column=1)
        tk.Label(frm, text="Niên khóa:").grid(row=1, column=2); self.e_nk=tk.Entry(frm); self.e_nk.grid(row=1, column=3)
        tk.Button(frm, text="Lưu/Sửa", command=self.save, bg="#3498db").grid(row=2, column=1, pady=10)
        tk.Button(frm, text="Xóa", command=self.delete, bg="#e74c3c").grid(row=2, column=2)
        self.tree=ttk.Treeview(self, columns=("m","t","k","n"), show="headings"); self.tree.pack(padx=20, pady=10, fill="both", expand=True)
        for c,t in zip(("m","t","k","n"),("MÃ","TÊN","KHOA","NIÊN KHÓA")): self.tree.heading(c,text=t)
        self.tree.bind("<<TreeviewSelect>>", self.sel)
    def load_data(self):
        self.cbb['values']=[r[0] for r in run_sql("SELECT makhoa FROM khoa", fetch=True)]
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in run_sql("SELECT * FROM lop", fetch=True): self.tree.insert("", "end", values=r)
    def save(self): run_sql("REPLACE INTO lop VALUES (%s,%s,%s,%s)",(self.e_ma.get(),self.e_ten.get(),self.cbb.get(),self.e_nk.get())); self.load_data()
    def delete(self): run_sql("DELETE FROM lop WHERE malop=%s",(self.e_ma.get(),)); self.load_data()
    def sel(self,e): 
        s=self.tree.selection()
        if s: v=self.tree.item(s[0])['values']; self.e_ma.delete(0,tk.END); self.e_ma.insert(0,v[0]); self.e_ten.delete(0,tk.END); self.e_ten.insert(0,v[1]); self.cbb.set(v[2]); self.e_nk.delete(0,tk.END); self.e_nk.insert(0,v[3])

#TAB MÔN HỌC
class TabMonHoc(BaseTab):
    def __init__(self, parent):
        super().__init__(parent); self.add_title("QUẢN LÝ MÔN HỌC")
        frm = tk.Frame(self); frm.pack()
        tk.Label(frm, text="Mã MH:").pack(side="left"); self.e_ma=tk.Entry(frm); self.e_ma.pack(side="left")
        tk.Label(frm, text="Tên MH:").pack(side="left"); self.e_ten=tk.Entry(frm); self.e_ten.pack(side="left")
        tk.Label(frm, text="Số TC:").pack(side="left"); self.e_tc=tk.Spinbox(frm, from_=1, to=10, width=5); self.e_tc.pack(side="left")
        tk.Button(frm, text="Lưu", command=self.save, bg="#e67e22").pack(side="left", padx=5)
        tk.Button(frm, text="Xóa", command=self.delete, bg="#c0392b").pack(side="left")
        self.tree=ttk.Treeview(self, columns=("m","t","tc"), show="headings"); self.tree.pack(padx=20, pady=10, fill="both", expand=True)
        self.tree.heading("m",text="MÃ"); self.tree.heading("t",text="TÊN MÔN"); self.tree.heading("tc",text="TÍN CHỈ")
        self.tree.bind("<<TreeviewSelect>>", self.sel)
    def load_data(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in run_sql("SELECT * FROM monhoc", fetch=True): self.tree.insert("", "end", values=r)
    def save(self): run_sql("REPLACE INTO monhoc VALUES (%s,%s,%s)",(self.e_ma.get(),self.e_ten.get(),self.e_tc.get())); self.load_data()
    def delete(self): run_sql("DELETE FROM monhoc WHERE mamh=%s",(self.e_ma.get(),)); self.load_data()
    def sel(self,e): 
        s=self.tree.selection()
        if s: v=self.tree.item(s[0])['values']; self.e_ma.delete(0,tk.END); self.e_ma.insert(0,v[0]); self.e_ten.delete(0,tk.END); self.e_ten.insert(0,v[1]); self.e_tc.delete(0,tk.END); self.e_tc.insert(0,v[2])

#TAB SINH VIÊN
class TabSinhVien(BaseTab):
    def __init__(self, parent):
        super().__init__(parent); self.add_title("HỒ SƠ SINH VIÊN")
        frm = tk.Frame(self); frm.pack()
        
        tk.Label(frm, text="Mã SV:").grid(row=0, column=0); 
        self.e_ma = tk.Entry(frm); self.e_ma.grid(row=0, column=1)

        tk.Label(frm, text="Họ lót:").grid(row=0, column=2); self.e_ho=tk.Entry(frm); self.e_ho.grid(row=0, column=3)
        tk.Label(frm, text="Tên:").grid(row=0, column=4); self.e_ten=tk.Entry(frm); self.e_ten.grid(row=0, column=5)
        
        tk.Label(frm, text="Ngày sinh:").grid(row=1, column=0); self.e_ns=DateEntry(frm, date_pattern="yyyy-mm-dd"); self.e_ns.grid(row=1, column=1)
        tk.Label(frm, text="Giới tính:").grid(row=1, column=2); self.cbb_gt=ttk.Combobox(frm, values=["Nam","Nữ"]); self.cbb_gt.grid(row=1, column=3)
        tk.Label(frm, text="Lớp:").grid(row=1, column=4); self.cbb_lop=ttk.Combobox(frm); self.cbb_lop.grid(row=1, column=5)
        
        tk.Label(frm, text="Quê quán:").grid(row=2, column=0); self.e_que=tk.Entry(frm); self.e_que.grid(row=2, column=1)
        tk.Label(frm, text="Email:").grid(row=2, column=2); self.e_em=tk.Entry(frm); self.e_em.grid(row=2, column=3)
        tk.Label(frm, text="SĐT:").grid(row=2, column=4); self.e_sdt=tk.Entry(frm); self.e_sdt.grid(row=2, column=5)

        btn = tk.Frame(self); btn.pack(pady=10)
        tk.Button(btn, text="Thêm / Sửa", command=self.save, bg="#27ae60").pack(side="left", padx=5)
        tk.Button(btn, text="Xóa", command=self.delete, bg="#c0392b").pack(side="left", padx=5)
        tk.Button(btn, text="Làm mới form", command=self.clear_form).pack(side="left", padx=5)

        self.tree=ttk.Treeview(self, columns=("id","hl","t","gt","ns","l","qq","em","sdt"), show="headings", height=10)
        self.tree.pack(padx=20, fill="both", expand=True)
        headers = ["Mã SV", "Họ lót", "Tên", "GT", "Ngày Sinh", "Lớp", "Quê", "Email", "SĐT"]
        for c, h in zip(self.tree["columns"], headers): self.tree.heading(c, text=h)
        self.tree.column("id", width=80)
        self.tree.bind("<<TreeviewSelect>>", self.sel)

    def load_data(self):
        self.cbb_lop['values']=[r[0] for r in run_sql("SELECT malop FROM lop", fetch=True)]
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in run_sql("SELECT * FROM sinhvien", fetch=True): self.tree.insert("", "end", values=r)

    def save(self):
        sql = "REPLACE INTO sinhvien (masv, holot, ten, gioitinh, ngaysinh, malop, quequan, email, sdt) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        val = (self.e_ma.get(), self.e_ho.get(), self.e_ten.get(), self.cbb_gt.get(), self.e_ns.get(), self.cbb_lop.get(), self.e_que.get(), self.e_em.get(), self.e_sdt.get())
        if run_sql(sql, val):
            self.load_data() 
            self.clear_form()
            messagebox.showinfo("Thành công", "Đã lưu sinh viên!")

    def delete(self):
        if run_sql("DELETE FROM sinhvien WHERE masv=%s", (self.e_ma.get(),)):
            self.load_data()
            self.clear_form()

    def clear_form(self):
        for e in (self.e_ma, self.e_ho, self.e_ten, self.e_que, self.e_em, self.e_sdt): e.delete(0, tk.END)

    def sel(self, e):
        s=self.tree.selection()
        if s: 
            v=self.tree.item(s[0])['values']
            self.e_ma.delete(0,tk.END); self.e_ma.insert(0,v[0])
            self.e_ho.delete(0,tk.END); self.e_ho.insert(0,v[1])
            self.e_ten.delete(0,tk.END); self.e_ten.insert(0,v[2])
            self.cbb_gt.set(v[3])
            try: self.e_ns.set_date(v[4])
            except: pass
            self.cbb_lop.set(v[5])
            self.e_que.delete(0,tk.END); self.e_que.insert(0,v[6])
            self.e_em.delete(0,tk.END); self.e_em.insert(0,v[7])
            self.e_sdt.delete(0,tk.END); self.e_sdt.insert(0,v[8])

#TAB ĐIỂM
class TabDiem(BaseTab):
    def __init__(self, parent):
        super().__init__(parent); self.add_title("QUẢN LÝ ĐIỂM")
        frm = tk.Frame(self); frm.pack()
        
        tk.Label(frm, text="Sinh viên (Mã):").grid(row=0, column=0); self.cbb_sv=ttk.Combobox(frm, width=30); self.cbb_sv.grid(row=0, column=1)
        tk.Label(frm, text="Môn học:").grid(row=0, column=2); self.cbb_mh=ttk.Combobox(frm); self.cbb_mh.grid(row=0, column=3)
        tk.Label(frm, text="Điểm QT:").grid(row=1, column=0); self.e_qt=tk.Entry(frm, width=10); self.e_qt.grid(row=1, column=1)
        tk.Label(frm, text="Điểm Thi:").grid(row=1, column=2); self.e_thi=tk.Entry(frm, width=10); self.e_thi.grid(row=1, column=3)
        
        tk.Button(frm, text="Lưu Điểm", command=self.save, bg="#f39c12").grid(row=1, column=4, padx=10)
        
        self.tree=ttk.Treeview(self, columns=("s","t","m","n","q","th","tb"), show="headings"); self.tree.pack(padx=20, pady=10, fill="both", expand=True)
        for c,t in zip(("s","t","m","n","q","th","tb"),("Mã SV","Họ Tên","Mã MH","Môn","QT","Thi","TB (Tự tính)")): self.tree.heading(c,text=t)

    def load_data(self):
        self.cbb_sv['values'] = [f"{r[0]} - {r[1]} {r[2]}" for r in run_sql("SELECT masv, holot, ten FROM sinhvien", fetch=True)]
        self.cbb_mh['values'] = [f"{r[0]} - {r[1]}" for r in run_sql("SELECT mamh, tenmh FROM monhoc", fetch=True)]
        
        for i in self.tree.get_children(): self.tree.delete(i)
        sql = """SELECT d.masv, CONCAT(s.holot,' ',s.ten), d.mamh, m.tenmh, d.diemqt, d.diemthi, d.diemtb 
                 FROM diem d JOIN sinhvien s ON d.masv=s.masv JOIN monhoc m ON d.mamh=m.mamh"""
        for r in run_sql(sql, fetch=True): self.tree.insert("", "end", values=r)

    def save(self):
        try:
            masv = self.cbb_sv.get().split(" - ")[0]
            mamh = self.cbb_mh.get().split(" - ")[0]
            qt = float(self.e_qt.get())
            thi = float(self.e_thi.get())
            
            sql = "REPLACE INTO diem (masv, mamh, diemqt, diemthi) VALUES (%s, %s, %s, %s)"
            run_sql(sql, (masv, mamh, qt, thi))
            
            self.load_data()
            messagebox.showinfo("OK", "Đã lưu điểm! Điểm TB đã được cập nhật.")
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()