-- =====================================================================
-- Đề tài: Quản lý đặt vé rạp chiếu phim
-- Doanh nghiệp (giả định): Công ty Giải trí Ánh Sao - dữ liệu mô phỏng
-- Học phần: Hệ quản trị cơ sở dữ liệu - Kiểm tra giữa kỳ lần 1
--
-- Chạy trong MySQL Workbench hoặc MySQL command line.
-- Lưu ý: ràng buộc CHECK chỉ có tác dụng trên MySQL 8.0.16 trở lên
-- (hoặc MariaDB 10.2 trở lên). MySQL 5.7 bỏ qua CHECK.
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
    SucChua   INT         NOT NULL,                   -- số ghế tối đa của phòng
    CONSTRAINT PK_PHONGCHIEU PRIMARY KEY (MaPhong),
    CONSTRAINT CK_PHONG_LoaiPhong CHECK (LoaiPhong IN ('2D', '3D', 'IMAX')),
    CONSTRAINT CK_PHONG_SucChua CHECK (SucChua > 0)
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

-- VE là thực thể yếu: không có mã riêng, phụ thuộc thực thể chủ SUATCHIEU.
-- Khóa chính = khóa của thực thể chủ (MaSuat) + khóa bộ phận (SoGhe).
CREATE TABLE VE (
    MaSuat  VARCHAR(10) NOT NULL,
    SoGhe   VARCHAR(5)  NOT NULL,                 -- khóa bộ phận, ví dụ: A5, B3
    MaKH    VARCHAR(10) NOT NULL,
    NgayDat DATE        NOT NULL,
    -- một ghế chỉ được bán một lần cho mỗi suất chiếu
    CONSTRAINT PK_VE PRIMARY KEY (MaSuat, SoGhe),
    -- xóa suất chiếu (thực thể chủ) thì các vé của suất đó bị xóa theo
    CONSTRAINT FK_VE_SUAT FOREIGN KEY (MaSuat) REFERENCES SUATCHIEU (MaSuat) ON DELETE CASCADE,
    CONSTRAINT FK_VE_KH   FOREIGN KEY (MaKH)   REFERENCES KHACHHANG (MaKH)
);

-- ---------------------------------------------------------------------
-- 2. Dữ liệu mẫu (nhập theo thứ tự bảng cha trước, bảng con sau)
-- ---------------------------------------------------------------------

INSERT INTO PHIM (MaPhim, TenPhim, TheLoai, ThoiLuong, NgayKhoiChieu) VALUES
('F01', 'Mai',                     'Tâm lý',     131, '2024-02-10'),
('F02', 'Inside Out 2',            'Hoạt hình',   96, '2024-06-14'),
('F03', 'Avengers: Endgame',       'Hành động',  181, '2019-04-26'),
('F04', 'Lật Mặt 7: Một Điều Ước', 'Gia đình',   138, '2024-04-26'),
('F05', 'Kung Fu Panda 4',         'Hoạt hình',   94, '2024-03-08');

INSERT INTO PHONGCHIEU (MaPhong, TenPhong, LoaiPhong, SucChua) VALUES
('R01', 'Phòng 1',     '2D',   120),
('R02', 'Phòng 2',     '3D',   100),
('R03', 'Phòng IMAX',  'IMAX', 150);

INSERT INTO SUATCHIEU (MaSuat, MaPhim, MaPhong, NgayChieu, GioBatDau, GiaVe) VALUES
('S01', 'F01', 'R01', '2025-03-20', '18:00:00',  90000),
('S02', 'F02', 'R02', '2025-03-20', '20:30:00', 110000),
('S03', 'F03', 'R03', '2025-03-21', '19:00:00', 150000),
('S04', 'F04', 'R01', '2025-03-21', '20:00:00',  90000),
('S05', 'F05', 'R02', '2025-03-22', '09:30:00',  80000),
('S06', 'F01', 'R01', '2025-03-22', '19:30:00', 100000);

INSERT INTO KHACHHANG (MaKH, HoTen, SDT, Email) VALUES
('KH01', 'Nguyễn Văn An',  '0901234567', 'an.nguyen@example.com'),
('KH02', 'Trần Thị Bình',  '0912345678', 'binh.tran@example.com'),
('KH03', 'Lê Hoàng Cường', '0987654321', 'cuong.le@example.com'),
('KH04', 'Phạm Thu Dung',  '0933456789', 'dung.pham@example.com'),
('KH05', 'Võ Minh Khôi',   '0944567890', 'khoi.vo@example.com');

INSERT INTO VE (MaSuat, SoGhe, MaKH, NgayDat) VALUES
('S01', 'A5', 'KH01', '2025-03-18'),
('S01', 'A6', 'KH02', '2025-03-18'),
('S02', 'B3', 'KH01', '2025-03-19'),
('S03', 'C7', 'KH03', '2025-03-19'),
('S03', 'C8', 'KH03', '2025-03-19'),
('S04', 'D2', 'KH04', '2025-03-20'),
('S05', 'E4', 'KH05', '2025-03-21'),
('S06', 'A6', 'KH02', '2025-03-21');

-- ---------------------------------------------------------------------
-- 3. Xem dữ liệu (chụp màn hình các kết quả này nếu cần dán vào slide 6)
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

-- ---------------------------------------------------------------------
-- 4. Thử vi phạm ràng buộc (slide 7): bỏ dấu -- trước từng lệnh để chạy,
--    mỗi lệnh phải bị MySQL từ chối và báo lỗi
-- ---------------------------------------------------------------------

-- INSERT INTO PHIM VALUES ('F06', 'Phim thử', 'Khác', 0, '2025-01-01');                    -- miền giá trị: ThoiLuong > 0
-- INSERT INTO PHONGCHIEU VALUES ('R04', 'Phòng 4', '4DX', 80);                              -- miền giá trị: LoaiPhong
-- INSERT INTO PHIM VALUES ('F01', 'Trùng mã', 'Khác', 90, '2025-01-01');                    -- khóa chính: trùng MaPhim
-- INSERT INTO SUATCHIEU VALUES ('S09', 'F99', 'R01', '2025-03-23', '18:00:00', 90000);      -- khóa ngoại: không có phim F99
-- INSERT INTO KHACHHANG VALUES ('KH09', 'Thử', '12345', 'thu@example.com');                 -- miền giá trị: SDT phải đủ 10 chữ số
-- INSERT INTO VE VALUES ('S01', 'A5', 'KH03', '2025-03-18');                                -- khóa chính: ghế A5 của suất S01 đã bán
