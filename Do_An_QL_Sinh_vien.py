import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import mysql.connector

# ================= 1. CẤU HÌNH DATABASE =================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",       
    "database": "qlsv"
}

# ================= 2. HÀM KẾT NỐI DATABASE CHUNG =================
def run_sql(sql, params=(), fetch=False):
    """Hàm thực thi câu lệnh SQL"""
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

# ================= 3. GIAO DIỆN CHÍNH (MAIN APP) =================
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Phần mềm Quản lý Sinh Viên")
        self.geometry("900x550")
        self.center_window()

        # --- TẠO MENU BAR ---
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # 1. Menu Hệ thống
        sys_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Hệ thống", menu=sys_menu)
        sys_menu.add_command(label="Thông tin phần mềm", command=self.show_about)
        sys_menu.add_command(label="Hướng dẫn sử dụng", command=self.show_help)
        sys_menu.add_separator()
        sys_menu.add_command(label="Thoát", command=self.quit)

        # 2. Menu Quản lý
        manage_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Quản lý", menu=manage_menu)
        manage_menu.add_command(label="Khoa", command=lambda: self.show_frame("TabKhoa"))
        manage_menu.add_command(label="Lớp học", command=lambda: self.show_frame("TabLop"))
        manage_menu.add_command(label="Môn học", command=lambda: self.show_frame("TabMonHoc"))
        manage_menu.add_separator()
        manage_menu.add_command(label="Sinh viên", command=lambda: self.show_frame("TabSinhVien"))

        # 3. Menu Kết quả
        res_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Kết quả", menu=res_menu)
        res_menu.add_command(label="Bảng điểm", command=lambda: self.show_frame("TabDiem"))

        # --- KHUNG CHỨA NỘI DUNG (Tab) ---
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
        x = (self.winfo_screenwidth() - 900) // 2
        y = (self.winfo_screenheight() - 550) // 2
        self.geometry(f"+{x}+{y}")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        if hasattr(frame, "load_data"): frame.load_data()

    def show_about(self):
        messagebox.showinfo("Giới thiệu", "PHẦN MỀM QUẢN LÝ SINH VIÊN\n\nPhiên bản: 1.0\nTác giả: Huỳnh Hải Đăng và Trần Văn Hưởng\nLớp: DH25PM\n\nĐồ án môn học Python.")

    def show_help(self):
        messagebox.showinfo("Hướng dẫn", "Quy trình sử dụng:\n1. Vào menu 'Quản lý' -> Thêm Khoa.\n2. Thêm Lớp (chọn Khoa vừa tạo).\n3. Thêm Môn học.\n4. Thêm Sinh viên (chọn Lớp).\n5. Vào 'Kết quả' để nhập điểm.")

# ----------------------------------------------------------------------------------------------------------------------
# ================= 4. CÁC TAB CHỨC NĂNG =================
# ----------------------------------------------------------------------------------------------------------------------

class BaseTab(tk.Frame):
    def __init__(self, parent): 
        super().__init__(parent)
        self.title_font = ("Arial", 16, "bold")
    def add_title(self, text): 
        tk.Label(self, text=text, font=self.title_font, fg="#2c3e50").pack(pady=15)

# ---------------------------------------------------------
# TAB 1: QUẢN LÝ KHOA
# ---------------------------------------------------------
class TabKhoa(BaseTab):
    def __init__(self, parent):
        super().__init__(parent); self.add_title("DANH MỤC KHOA")
        frm = tk.Frame(self); frm.pack(pady=10)
        
        tk.Label(frm, text="Mã Khoa:").grid(row=0, column=0)
        self.e_ma = tk.Entry(frm); self.e_ma.grid(row=0, column=1, padx=5)
        
        tk.Label(frm, text="Tên Khoa:").grid(row=0, column=2)
        self.e_ten = tk.Entry(frm, width=30); self.e_ten.grid(row=0, column=3, padx=5)
        
        btn = tk.Frame(self); btn.pack(pady=5)
        tk.Button(btn, text="Thêm", command=self.add, bg="#2ecc71").pack(side="left", padx=5)
        tk.Button(btn, text="Sửa", command=self.update, bg="#3498db").pack(side="left", padx=5)
        tk.Button(btn, text="Xóa", command=self.delete, bg="#e74c3c").pack(side="left", padx=5)
        
        self.tree = ttk.Treeview(self, columns=("ma","ten"), show="headings", height=8)
        self.tree.pack(padx=20, fill="x", expand=False)
        self.tree.heading("ma", text="MÃ"); self.tree.heading("ten", text="TÊN KHOA")
        self.tree.bind("<<TreeviewSelect>>", self.sel)

    def load_data(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in run_sql("SELECT * FROM khoa", fetch=True): self.tree.insert("", "end", values=r)
    
    def add(self): 
        ma = self.e_ma.get().strip(); ten = self.e_ten.get().strip()
        if not ma: messagebox.showwarning("Lỗi", "Chưa nhập Mã Khoa"); return
        
        if run_sql("SELECT makhoa FROM khoa WHERE makhoa=%s", (ma,), fetch=True):
             messagebox.showwarning("Lỗi", f"Mã Khoa '{ma}' đã tồn tại. Vui lòng chọn Sửa."); return
        
        if run_sql("INSERT INTO khoa VALUES (%s,%s)", (ma, ten)):
            self.load_data()
            messagebox.showinfo("Thông báo", "Đã thêm Khoa mới!")
        
    def update(self):
        ma = self.e_ma.get().strip(); ten = self.e_ten.get().strip()
        if not ma: messagebox.showwarning("Lỗi", "Chưa nhập Mã Khoa để sửa"); return
        
        sql = "UPDATE khoa SET tenkhoa = %s WHERE makhoa = %s"
        if run_sql(sql, (ten, ma)):
            self.load_data()
            messagebox.showinfo("Thông báo", "Đã cập nhật thông tin Khoa!")

    def delete(self): 
        ma = self.e_ma.get().strip()
        if run_sql("DELETE FROM khoa WHERE makhoa=%s", (ma,)): 
            self.load_data()
            self.e_ma.delete(0,tk.END); self.e_ten.delete(0,tk.END)
        
    def sel(self,e): 
        s=self.tree.selection()
        if s: 
            v=self.tree.item(s[0])['values']
            self.e_ma.delete(0,tk.END); self.e_ma.insert(0,v[0])
            self.e_ten.delete(0,tk.END); self.e_ten.insert(0,v[1])

# ---------------------------------------------------------
# TAB 2: QUẢN LÝ LỚP
# ---------------------------------------------------------
class TabLop(BaseTab):
    def __init__(self, parent):
        super().__init__(parent); self.add_title("QUẢN LÝ LỚP")
        frm_input = tk.Frame(self); frm_input.pack()
        
        tk.Label(frm_input, text="Mã Lớp:").grid(row=0, column=0); self.e_ma=tk.Entry(frm_input); self.e_ma.grid(row=0, column=1)
        tk.Label(frm_input, text="Tên Lớp:").grid(row=0, column=2); self.e_ten=tk.Entry(frm_input); self.e_ten.grid(row=0, column=3)
        
        tk.Label(frm_input, text="Khoa:").grid(row=1, column=0)
        self.cbb=ttk.Combobox(frm_input, postcommand=self.update_khoa, state="readonly") 
        self.cbb.grid(row=1, column=1)
        
        tk.Label(frm_input, text="Niên khóa:").grid(row=1, column=2); self.e_nk=tk.Entry(frm_input); self.e_nk.grid(row=1, column=3)
        
        btn = tk.Frame(self); btn.pack(pady=10)
        tk.Button(btn, text="Thêm", command=self.add, bg="#2ecc71").pack(side="left", padx=5)
        tk.Button(btn, text="Sửa", command=self.update, bg="#3498db").pack(side="left", padx=5)
        tk.Button(btn, text="Xóa", command=self.delete, bg="#e74c3c").pack(side="left", padx=5)
        
        self.tree=ttk.Treeview(self, columns=("m","t","k","n"), show="headings", height=8)
        self.tree.pack(padx=20, pady=10, fill="x", expand=False)
        for c,t in zip(("m","t","k","n"),("MÃ","TÊN","KHOA","NIÊN KHÓA")): self.tree.heading(c,text=t)
        self.tree.bind("<<TreeviewSelect>>", self.sel)

    def update_khoa(self):
        rows = run_sql("SELECT makhoa FROM khoa", fetch=True)
        self.cbb['values'] = [r[0] for r in rows] if rows else []

    def load_data(self):
        self.update_khoa()
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in run_sql("SELECT * FROM lop", fetch=True): self.tree.insert("", "end", values=r)

    def add(self):
        ma = self.e_ma.get().strip(); ten = self.e_ten.get().strip()
        makhoa = self.cbb.get().strip(); nk = self.e_nk.get().strip()
        
        if not makhoa: messagebox.showwarning("Lỗi", "Vui lòng chọn Khoa!"); return
        if not ma: messagebox.showwarning("Lỗi", "Chưa nhập Mã Lớp"); return
        
        if run_sql("SELECT malop FROM lop WHERE malop=%s", (ma,), fetch=True):
             messagebox.showwarning("Lỗi", f"Mã Lớp '{ma}' đã tồn tại. Vui lòng chọn Sửa."); return
        
        if run_sql("INSERT INTO lop VALUES (%s,%s,%s,%s)",(ma, ten, makhoa, nk)):
            self.load_data()
            messagebox.showinfo("Thông báo", "Đã thêm Lớp mới!")

    def update(self):
        ma = self.e_ma.get().strip(); ten = self.e_ten.get().strip()
        makhoa = self.cbb.get().strip(); nk = self.e_nk.get().strip()
        
        if not ma: messagebox.showwarning("Lỗi", "Chưa nhập Mã Lớp để sửa"); return
        
        sql = "UPDATE lop SET tenlop = %s, makhoa = %s, nienkhoa = %s WHERE malop = %s"
        if run_sql(sql, (ten, makhoa, nk, ma)):
            self.load_data()
            messagebox.showinfo("Thông báo", "Đã cập nhật thông tin Lớp!")

    def delete(self): 
        ma = self.e_ma.get().strip()
        if run_sql("DELETE FROM lop WHERE malop=%s",(ma,)):
            self.load_data()
            self.e_ma.delete(0,tk.END); self.e_ten.delete(0,tk.END); self.cbb.set(""); self.e_nk.delete(0,tk.END)
        
    def sel(self,e): 
        s=self.tree.selection()
        if s: 
            v=self.tree.item(s[0])['values']
            self.e_ma.delete(0,tk.END); self.e_ma.insert(0,v[0])
            self.e_ten.delete(0,tk.END); self.e_ten.insert(0,v[1])
            self.cbb.set(v[2])
            self.e_nk.delete(0,tk.END); self.e_nk.insert(0,v[3])

# ---------------------------------------------------------
# TAB 3: QUẢN LÝ MÔN HỌC
# ---------------------------------------------------------
class TabMonHoc(BaseTab):
    def __init__(self, parent):
        super().__init__(parent); self.add_title("QUẢN LÝ MÔN HỌC")
        frm = tk.Frame(self); frm.pack()
        
        tk.Label(frm, text="Mã MH:").pack(side="left"); self.e_ma=tk.Entry(frm); self.e_ma.pack(side="left")
        tk.Label(frm, text="Tên MH:").pack(side="left"); self.e_ten=tk.Entry(frm); self.e_ten.pack(side="left")
        tk.Label(frm, text="Số TC:").pack(side="left"); self.e_tc=tk.Spinbox(frm, from_=1, to=10, width=5); self.e_tc.pack(side="left")
        
        tk.Button(frm, text="Thêm", command=self.add, bg="#2ecc71").pack(side="left", padx=5)
        tk.Button(frm, text="Sửa", command=self.update, bg="#3498db").pack(side="left", padx=5)
        tk.Button(frm, text="Xóa", command=self.delete, bg="#c0392b").pack(side="left")
        
        self.tree=ttk.Treeview(self, columns=("m","t","tc"), show="headings", height=8)
        self.tree.pack(padx=20, pady=10, fill="x", expand=False)
        self.tree.heading("m",text="MÃ"); self.tree.heading("t",text="TÊN MÔN"); self.tree.heading("tc",text="TÍN CHỈ")
        self.tree.bind("<<TreeviewSelect>>", self.sel)
        
    def load_data(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in run_sql("SELECT * FROM monhoc", fetch=True): self.tree.insert("", "end", values=r)
        
    def add(self): 
        ma = self.e_ma.get().strip(); ten = self.e_ten.get().strip(); tc = self.e_tc.get()
        if not ma: messagebox.showwarning("Lỗi", "Chưa nhập Mã Môn học"); return
        
        if run_sql("SELECT mamh FROM monhoc WHERE mamh=%s", (ma,), fetch=True):
             messagebox.showwarning("Lỗi", f"Mã Môn học '{ma}' đã tồn tại. Vui lòng chọn Sửa."); return
        
        if run_sql("INSERT INTO monhoc VALUES (%s,%s,%s)",(ma, ten, tc)): 
            self.load_data()
            messagebox.showinfo("Thông báo", "Đã thêm Môn học mới!")
            
    def update(self):
        ma = self.e_ma.get().strip(); ten = self.e_ten.get().strip(); tc = self.e_tc.get()
        if not ma: messagebox.showwarning("Lỗi", "Chưa nhập Mã Môn học để sửa"); return
        
        sql = "UPDATE monhoc SET tenmh = %s, sotinchi = %s WHERE mamh = %s"
        if run_sql(sql, (ten, tc, ma)):
            self.load_data()
            messagebox.showinfo("Thông báo", "Đã cập nhật thông tin Môn học!")
        
    def delete(self): 
        ma = self.e_ma.get().strip()
        if run_sql("DELETE FROM monhoc WHERE mamh=%s",(ma,)):
            self.load_data()
            self.e_ma.delete(0,tk.END); self.e_ten.delete(0,tk.END); self.e_tc.delete(0,tk.END); self.e_tc.insert(0,"1")
        
    def sel(self,e): 
        s=self.tree.selection()
        if s: 
            v=self.tree.item(s[0])['values']
            self.e_ma.delete(0,tk.END); self.e_ma.insert(0,v[0])
            self.e_ten.delete(0,tk.END); self.e_ten.insert(0,v[1])
            self.e_tc.delete(0,tk.END); self.e_tc.insert(0,v[2])

# ---------------------------------------------------------
# TAB 4: HỒ SƠ SINH VIÊN (Có chức năng Tìm kiếm)
# ---------------------------------------------------------
class TabSinhVien(BaseTab):
    def __init__(self, parent):
        super().__init__(parent); self.add_title("HỒ SƠ SINH VIÊN")
        
        # --- 1. KHUNG NHẬP DỮ LIỆU ---
        frm_input = tk.Frame(self); frm_input.pack(pady=5)
        
        tk.Label(frm_input, text="Mã SV:").grid(row=0, column=0); self.e_ma = tk.Entry(frm_input); self.e_ma.grid(row=0, column=1)
        tk.Label(frm_input, text="Họ lót:").grid(row=0, column=2); self.e_ho=tk.Entry(frm_input); self.e_ho.grid(row=0, column=3)
        tk.Label(frm_input, text="Tên:").grid(row=0, column=4); self.e_ten=tk.Entry(frm_input); self.e_ten.grid(row=0, column=5)
        
        tk.Label(frm_input, text="Ngày sinh:").grid(row=1, column=0); self.e_ns=DateEntry(frm_input, date_pattern="yyyy-mm-dd"); self.e_ns.grid(row=1, column=1)
        tk.Label(frm_input, text="Giới tính:").grid(row=1, column=2); self.cbb_gt=ttk.Combobox(frm_input, values=["Nam","Nữ"]); self.cbb_gt.grid(row=1, column=3)
        
        tk.Label(frm_input, text="Lớp:").grid(row=1, column=4)
        self.cbb_lop=ttk.Combobox(frm_input, postcommand=self.update_lop, state="readonly")
        self.cbb_lop.grid(row=1, column=5)
        
        tk.Label(frm_input, text="Quê quán:").grid(row=2, column=0); self.e_que=tk.Entry(frm_input); self.e_que.grid(row=2, column=1)
        tk.Label(frm_input, text="Email:").grid(row=2, column=2); self.e_em=tk.Entry(frm_input); self.e_em.grid(row=2, column=3)
        tk.Label(frm_input, text="SĐT:").grid(row=2, column=4); self.e_sdt=tk.Entry(frm_input); self.e_sdt.grid(row=2, column=5)

        # --- 2. KHUNG NÚT CHỨC NĂNG CƠ BẢN ---
        btn = tk.Frame(self); btn.pack(pady=10)
        tk.Button(btn, text="Thêm", command=self.add, bg="#2ecc71").pack(side="left", padx=5)
        tk.Button(btn, text="Sửa", command=self.update, bg="#3498db").pack(side="left", padx=5)
        tk.Button(btn, text="Xóa", command=self.delete, bg="#c0392b").pack(side="left", padx=5)
        tk.Button(btn, text="Làm mới form", command=self.clear_form).pack(side="left", padx=5)
        
        # --- 3. KHUNG TÌM KIẾM ---
        frm_search = tk.Frame(self, bd=1, relief="groove", padx=10, pady=5)
        frm_search.pack(pady=5, fill="x", padx=20)
        
        tk.Label(frm_search, text="TÌM KIẾM:").pack(side="left", padx=5)
        self.e_search = tk.Entry(frm_search, width=30)
        self.e_search.pack(side="left", padx=5)
        
        self.cbb_search = ttk.Combobox(frm_search, values=["Mã SV", "Họ Tên", "Lớp"], width=10, state="readonly")
        self.cbb_search.current(0)
        self.cbb_search.pack(side="left", padx=5)
        
        tk.Button(frm_search, text="Tìm", command=self.search_sv, bg="#f39c12").pack(side="left", padx=5)
        tk.Button(frm_search, text="Xem Tất cả", command=self.load_data, bg="#95a5a6").pack(side="left", padx=5)

        # --- 4. TREEVIEW HIỂN THỊ DỮ LIỆU ---
        self.tree=ttk.Treeview(self, columns=("id","hl","t","gt","ns","l","qq","em","sdt"), show="headings", height=8)
        self.tree.pack(padx=20, pady=10, fill="x", expand=False)
        headers = ["Mã SV", "Họ lót", "Tên", "GT", "Ngày Sinh", "Lớp", "Quê", "Email", "SĐT"]
        for c, h in zip(self.tree["columns"], headers): self.tree.heading(c, text=h)
        self.tree.column("id", width=80)
        self.tree.bind("<<TreeviewSelect>>", self.sel)

    def update_lop(self):
        rows = run_sql("SELECT malop FROM lop", fetch=True)
        self.cbb_lop['values'] = [r[0] for r in rows] if rows else []

    def load_data(self):
        self.update_lop()
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in run_sql("SELECT * FROM sinhvien", fetch=True): self.tree.insert("", "end", values=r)

    def get_sv_data(self):
        return (
            self.e_ma.get().strip(), 
            self.e_ho.get().strip(), 
            self.e_ten.get().strip(), 
            self.cbb_gt.get().strip(), 
            self.e_ns.get(), 
            self.cbb_lop.get().strip(), 
            self.e_que.get().strip(), 
            self.e_em.get().strip(), 
            self.e_sdt.get().strip()
        )

    def add(self):
        ma, ho, ten, gt, ns, malop, que, email, sdt = self.get_sv_data()
        
        if not ma: messagebox.showwarning("Lỗi", "Chưa nhập Mã SV"); return
        if not malop: messagebox.showwarning("Lỗi", "Vui lòng chọn Lớp!"); return

        if run_sql("SELECT masv FROM sinhvien WHERE masv=%s", (ma,), fetch=True):
             messagebox.showwarning("Lỗi", f"Mã SV '{ma}' đã tồn tại. Vui lòng chọn Sửa."); return
        
        sql = "INSERT INTO sinhvien (masv, holot, ten, gioitinh, ngaysinh, malop, quequan, email, sdt) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        val = (ma, ho, ten, gt, ns, malop, que, email, sdt)
        
        if run_sql(sql, val):
            self.load_data(); self.clear_form(); messagebox.showinfo("Thành công", "Đã thêm Sinh viên!")

    def update(self):
        ma, ho, ten, gt, ns, malop, que, email, sdt = self.get_sv_data()

        if not ma: messagebox.showwarning("Lỗi", "Chưa nhập Mã SV để sửa"); return
        if not malop: messagebox.showwarning("Lỗi", "Vui lòng chọn Lớp!"); return
        
        sql = """UPDATE sinhvien SET holot=%s, ten=%s, gioitinh=%s, ngaysinh=%s, malop=%s, quequan=%s, email=%s, sdt=%s 
                 WHERE masv=%s"""
        val = (ho, ten, gt, ns, malop, que, email, sdt, ma)
        
        if run_sql(sql, val):
            self.load_data(); self.clear_form(); messagebox.showinfo("Thành công", "Đã cập nhật Sinh viên!")

    def delete(self):
        ma = self.e_ma.get().strip()
        if run_sql("DELETE FROM sinhvien WHERE masv=%s", (ma,)):
            self.load_data(); self.clear_form()

    def clear_form(self):
        for e in (self.e_ma, self.e_ho, self.e_ten, self.e_que, self.e_em, self.e_sdt): 
            e.delete(0, tk.END)
        self.cbb_gt.set(""); self.cbb_lop.set("")

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

    def search_sv(self):
        search_value = self.e_search.get().strip()
        search_by = self.cbb_search.get()
        
        if not search_value:
            messagebox.showwarning("Thông báo", "Vui lòng nhập từ khóa tìm kiếm."); return

        sql = "SELECT * FROM sinhvien WHERE 1=1 "
        params = []
        
        if search_by == "Mã SV":
            sql += "AND masv LIKE %s"
            params.append(f"%{search_value}%")
        elif search_by == "Họ Tên":
            sql += "AND (holot LIKE %s OR ten LIKE %s)"
            params.append(f"%{search_value}%")
            params.append(f"%{search_value}%")
        elif search_by == "Lớp":
            sql += "AND malop LIKE %s"
            params.append(f"%{search_value}%")

        results = run_sql(sql, tuple(params), fetch=True)
        
        for i in self.tree.get_children(): self.tree.delete(i)
        
        if results:
            for r in results: 
                self.tree.insert("", "end", values=r)
        else:
            messagebox.showinfo("Kết quả", "Không tìm thấy sinh viên nào phù hợp.")
            
# ---------------------------------------------------------
# TAB 5: BẢNG ĐIỂM
# ---------------------------------------------------------
class TabDiem(BaseTab):
    def __init__(self, parent):
        super().__init__(parent); self.add_title("QUẢN LÝ ĐIỂM")
        frm = tk.Frame(self); frm.pack()
        
        tk.Label(frm, text="Sinh viên (Mã):").grid(row=0, column=0)
        self.cbb_sv=ttk.Combobox(frm, width=30, postcommand=self.update_sv, state="readonly"); self.cbb_sv.grid(row=0, column=1)
        
        tk.Label(frm, text="Môn học:").grid(row=0, column=2)
        self.cbb_mh=ttk.Combobox(frm, postcommand=self.update_mh, state="readonly"); self.cbb_mh.grid(row=0, column=3)
        
        tk.Label(frm, text="Điểm QT:").grid(row=1, column=0); self.e_qt=tk.Entry(frm, width=10); self.e_qt.grid(row=1, column=1)
        tk.Label(frm, text="Điểm Thi:").grid(row=1, column=2); self.e_thi=tk.Entry(frm, width=10); self.e_thi.grid(row=1, column=3)
        
        tk.Button(frm, text="Lưu Điểm", command=self.save, bg="#f39c12").grid(row=1, column=4, padx=10)
        
        self.tree=ttk.Treeview(self, columns=("s","t","m","n","q","th","tb"), show="headings", height=8)
        self.tree.pack(padx=20, pady=10, fill="x", expand=False)
        for c,t in zip(("s","t","m","n","q","th","tb"),("Mã SV","Họ Tên","Mã MH","Môn","QT","Thi","TB (Tự tính)")): self.tree.heading(c,text=t)

    def update_sv(self):
        rows = run_sql("SELECT masv, holot, ten FROM sinhvien", fetch=True)
        self.cbb_sv['values'] = [f"{r[0]} - {r[1]} {r[2]}" for r in rows] if rows else []

    def update_mh(self):
        rows = run_sql("SELECT mamh, tenmh FROM monhoc", fetch=True)
        self.cbb_mh['values'] = [f"{r[0]} - {r[1]}" for r in rows] if rows else []

    def load_data(self):
        self.update_sv(); self.update_mh()
        for i in self.tree.get_children(): self.tree.delete(i)
        sql = """SELECT d.masv, CONCAT(s.holot,' ',s.ten), d.mamh, m.tenmh, d.diemqt, d.diemthi, d.diemtb 
                 FROM diem d JOIN sinhvien s ON d.masv=s.masv JOIN monhoc m ON d.mamh=m.mamh"""
        for r in run_sql(sql, fetch=True): self.tree.insert("", "end", values=r)

    def save(self):
        try:
            raw_sv = self.cbb_sv.get().strip(); raw_mh = self.cbb_mh.get().strip()
            if not raw_sv or not raw_mh:
                messagebox.showwarning("Lỗi", "Vui lòng chọn Sinh viên và Môn học!"); return
                
            masv = raw_sv.split(" - ")[0].strip(); mamh = raw_mh.split(" - ")[0].strip()
            qt = float(self.e_qt.get()); thi = float(self.e_thi.get())
            if not (0 <= qt <= 10 and 0 <= thi <= 10):
                messagebox.showwarning("Lỗi", "Điểm phải là số từ 0 đến 10."); return
            
            sql = "REPLACE INTO diem (masv, mamh, diemqt, diemthi) VALUES (%s, %s, %s, %s)"
            if run_sql(sql, (masv, mamh, qt, thi)):
                self.load_data(); 
                messagebox.showinfo("OK", "Đã lưu điểm!")
                self.e_qt.delete(0, tk.END); self.e_thi.delete(0, tk.END)
                self.cbb_sv.set(""); self.cbb_mh.set("")
        except ValueError:
            messagebox.showerror("Lỗi", "Điểm phải là giá trị số hợp lệ.")
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()