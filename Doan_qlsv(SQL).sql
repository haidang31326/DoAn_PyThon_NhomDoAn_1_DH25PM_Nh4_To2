create database qlsv
USE qlsv

-- Bảng Khoa
CREATE TABLE khoa (
    makhoa VARCHAR(10) PRIMARY KEY,
    tenkhoa VARCHAR(50)
);
ALTER TABLE sinhvien MODIFY malop CHAR(10);
select *from khoa
drop table khoa
-- Bảng Lớp
CREATE TABLE lop (
    malop CHAR(10) PRIMARY KEY,
    tenlop VARCHAR(100),
    makhoa VARCHAR(10),
    nienkhoa VARCHAR(10),
    FOREIGN KEY (makhoa) REFERENCES khoa(makhoa)
);
select *from lop
-- Bảng Sinh Vien
CREATE TABLE sinhvien (
	masv CHAR(10) PRIMARY KEY,
    holot VARCHAR(20),
    ten VARCHAR(20),
    gioitinh VARCHAR(10),
    ngaysinh DATE,
    malop VARCHAR(10),
    quequan VARCHAR(50),
    email VARCHAR(20),
    sdt VARCHAR(15),
    FOREIGN KEY (malop) REFERENCES lop(malop)
);

-- Bảng Môn học
CREATE TABLE monhoc (
    mamh VARCHAR(10) PRIMARY KEY,
    tenmh VARCHAR(20),
    sotinchi INT
);

-- Bảng Điểm
CREATE TABLE diem (
    masv CHAR(10),
    mamh VARCHAR(10),
    diemqt FLOAT,
    diemthi FLOAT,
    diemtb FLOAT AS ((diemqt + diemthi*2)/3) STORED,
    PRIMARY KEY (masv, mamh),
    FOREIGN KEY (masv) REFERENCES sinhvien(masv),
    FOREIGN KEY (mamh) REFERENCES monhoc(mamh)
);
drop table diem
select *from diem
drop table sinhvien

DROP DATABASE IF EXISTS qlsv;
