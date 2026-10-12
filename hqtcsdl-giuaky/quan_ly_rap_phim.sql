-- =====================================================================
-- Đề tài: Quản lý đặt vé rạp chiếu phim
-- Học phần: Hệ quản trị cơ sở dữ liệu - Kiểm tra giữa kỳ lần 1
-- Chạy trong MySQL Workbench / MySQL command line
-- =====================================================================

DROP DATABASE IF EXISTS QuanLyRapPhim;
CREATE DATABASE QuanLyRapPhim CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE QuanLyRapPhim;

-- ---------------------------------------------------------------------
-- 1. Tạo bảng (khóa chính, khóa ngoại, miền giá trị)
-- ---------------------------------------------------------------------

CREATE TABLE PHIM (
    MaPhim        VARCHAR(10)  NOT NULL,
    TenPhim       VARCHAR(100) NOT NULL,
    TheLoai       VARCHAR(30)  NOT NULL,
    ThoiLuong     INT          NOT NULL,          -- đơn vị: phút
    NgayKhoiChieu DATE         NOT NULL,
    CONSTRAINT PK_PHIM PRIMARY KEY (MaPhim),
    CONSTRAINT CK_PHIM_ThoiLuong CHECK (ThoiLuong > 0)
);

CREATE TABLE PHONGCHIEU (
    MaPhong   VARCHAR(10) NOT NULL,
    TenPhong  VARCHAR(50) NOT NULL,
    LoaiPhong VARCHAR(10) NOT NULL,
    SoGhe     INT         NOT NULL,
    CONSTRAINT PK_PHONGCHIEU PRIMARY KEY (MaPhong),
    CONSTRAINT CK_PHONG_LoaiPhong CHECK (LoaiPhong IN ('2D', '3D', 'IMAX')),
    CONSTRAINT CK_PHONG_SoGhe CHECK (SoGhe > 0)
);

CREATE TABLE SUATCHIEU (
    MaSuat     VARCHAR(10)  NOT NULL,
    MaPhim     VARCHAR(10)  NOT NULL,
    MaPhong    VARCHAR(10)  NOT NULL,
    NgayChieu  DATE         NOT NULL,
    GioBatDau  TIME         NOT NULL,
    GiaVe      DECIMAL(10,0) NOT NULL,            -- đơn vị: VNĐ
    CONSTRAINT PK_SUATCHIEU PRIMARY KEY (MaSuat),
    CONSTRAINT FK_SUAT_PHIM FOREIGN KEY (MaPhim)  REFERENCES PHIM (MaPhim),
    CONSTRAINT FK_SUAT_PHONG FOREIGN KEY (MaPhong) REFERENCES PHONGCHIEU (MaPhong),
    CONSTRAINT CK_SUAT_GiaVe CHECK (GiaVe >= 0)
);

CREATE TABLE KHACHHANG (
    MaKH  VARCHAR(10)  NOT NULL,
    HoTen VARCHAR(60)  NOT NULL,
    SDT   CHAR(10)     NOT NULL,
    Email VARCHAR(60),
    CONSTRAINT PK_KHACHHANG PRIMARY KEY (MaKH),
    CONSTRAINT UQ_KH_SDT UNIQUE (SDT),
    CONSTRAINT CK_KH_SDT CHECK (SDT REGEXP '^[0-9]{10}$')
);

CREATE TABLE VE (
    MaVe    VARCHAR(10) NOT NULL,
    MaSuat  VARCHAR(10) NOT NULL,
    MaKH    VARCHAR(10) NOT NULL,
    SoGhe   VARCHAR(5)  NOT NULL,                 -- ví dụ: A5, B3
    NgayDat DATE        NOT NULL,
    CONSTRAINT PK_VE PRIMARY KEY (MaVe),
    CONSTRAINT FK_VE_SUAT FOREIGN KEY (MaSuat) REFERENCES SUATCHIEU (MaSuat),
    CONSTRAINT FK_VE_KH   FOREIGN KEY (MaKH)   REFERENCES KHACHHANG (MaKH),
    -- một ghế chỉ được bán một lần cho mỗi suất chiếu
    CONSTRAINT UQ_VE_Suat_Ghe UNIQUE (MaSuat, SoGhe)
);

-- ---------------------------------------------------------------------
-- 2. Dữ liệu mẫu (nhập theo thứ tự bảng cha trước, bảng con sau)
-- ---------------------------------------------------------------------

INSERT INTO PHIM (MaPhim, TenPhim, TheLoai, ThoiLuong, NgayKhoiChieu) VALUES
('F01', 'Mai',               'Tâm lý',     131, '2024-02-10'),
('F02', 'Inside Out 2',      'Hoạt hình',   96, '2024-06-14'),
('F03', 'Avengers: Endgame', 'Hành động',  181, '2019-04-26');

INSERT INTO PHONGCHIEU (MaPhong, TenPhong, LoaiPhong, SoGhe) VALUES
('R01', 'Phòng 1',     '2D',   120),
('R02', 'Phòng 2',     '3D',   100),
('R03', 'Phòng IMAX',  'IMAX', 150);

INSERT INTO SUATCHIEU (MaSuat, MaPhim, MaPhong, NgayChieu, GioBatDau, GiaVe) VALUES
('S01', 'F01', 'R01', '2025-03-20', '18:00:00',  90000),
('S02', 'F02', 'R02', '2025-03-20', '20:30:00', 110000),
('S03', 'F03', 'R03', '2025-03-21', '19:00:00', 150000);

INSERT INTO KHACHHANG (MaKH, HoTen, SDT, Email) VALUES
('KH01', 'Nguyễn Văn An',  '0901234567', 'an.nguyen@example.com'),
('KH02', 'Trần Thị Bình',  '0912345678', 'binh.tran@example.com'),
('KH03', 'Lê Hoàng Cường', '0987654321', 'cuong.le@example.com');

INSERT INTO VE (MaVe, MaSuat, MaKH, SoGhe, NgayDat) VALUES
('V01', 'S01', 'KH01', 'A5', '2025-03-18'),
('V02', 'S01', 'KH02', 'A6', '2025-03-18'),
('V03', 'S02', 'KH01', 'B3', '2025-03-19');

-- ---------------------------------------------------------------------
-- 3. Xem dữ liệu (chụp màn hình các kết quả này để dán vào slide 4)
-- ---------------------------------------------------------------------

SELECT * FROM PHIM;
SELECT * FROM PHONGCHIEU;
SELECT * FROM SUATCHIEU;
SELECT * FROM KHACHHANG;
SELECT * FROM VE;

-- Truy vấn minh họa quan hệ nhiều - nhiều: khách hàng ↔ suất chiếu (qua bảng VE)
SELECT kh.HoTen, p.TenPhim, sc.NgayChieu, sc.GioBatDau, v.SoGhe
FROM VE v
JOIN KHACHHANG kh ON kh.MaKH   = v.MaKH
JOIN SUATCHIEU sc ON sc.MaSuat = v.MaSuat
JOIN PHIM p       ON p.MaPhim  = sc.MaPhim
ORDER BY kh.HoTen;
