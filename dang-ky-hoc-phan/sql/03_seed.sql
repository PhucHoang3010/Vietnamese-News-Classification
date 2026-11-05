-- =====================================================================
--  File 3/3: Dữ liệu mẫu (chạy lại được nhiều lần — xoá sạch rồi nạp lại)
-- =====================================================================
USE dkhp;
SET SQL_SAFE_UPDATES = 0;   -- MySQL Workbench bật chế độ này mặc định

DELETE FROM dang_ky;
DELETE FROM lop_hoc_phan;
DELETE FROM mon_hoc;
DELETE FROM sinh_vien;
ALTER TABLE dang_ky AUTO_INCREMENT = 1;

-- ---------------------------------------------------------------------
-- Sinh viên: SV01..SV10 dùng trên trang đăng kí, SV11..SV19 dành cho kịch bản
-- ---------------------------------------------------------------------
INSERT INTO sinh_vien (ma_sv, ho_ten, lop, tin_chi_toi_da, no_hoc_phi) VALUES
('SV01', 'Nguyễn Văn An',     'K23-CNTT1', 24, FALSE),
('SV02', 'Trần Thị Bích',     'K23-CNTT1', 24, FALSE),
('SV03', 'Lê Minh Châu',      'K23-CNTT2', 24, FALSE),
('SV04', 'Phạm Quốc Dũng',    'K23-CNTT2', 24, FALSE),
('SV05', 'Hoàng Thu Giang',   'K23-HTTT',  24, FALSE),
('SV06', 'Vũ Đức Huy',        'K23-HTTT',  24, FALSE),
('SV07', 'Đặng Ngọc Khánh',   'K23-KTPM',   8, FALSE),   -- cảnh báo học vụ: tối đa 8 TC
('SV08', 'Bùi Thanh Long',    'K23-KTPM',  24, TRUE),    -- còn nợ học phí
('SV09', 'Đỗ Mai Phương',     'K23-CNTT1', 24, FALSE),
('SV10', 'Ngô Gia Quân',      'K23-CNTT2', 24, FALSE),
('SV11', 'Lý Hải Sơn',        'K23-CNTT1', 24, FALSE),   -- KB1
('SV12', 'Mai Anh Thư',       'K23-CNTT1', 24, FALSE),   -- KB1
('SV13', 'Trịnh Bảo Uyên',    'K23-CNTT2', 24, FALSE),   -- KB1
('SV14', 'Phan Văn Việt',     'K23-HTTT',  24, FALSE),   -- KB1
('SV15', 'Cao Thị Xuân',      'K23-KTPM',  24, FALSE),   -- KB1
('SV16', 'Đinh Công Thành',   'K23-CNTT1', 24, FALSE),   -- KB2
('SV17', 'Hồ Ngọc Trâm',      'K23-CNTT2', 24, FALSE),   -- KB3
('SV18', 'Tạ Quang Vinh',     'K23-HTTT',  24, TRUE),    -- KB4: nợ học phí
('SV19', 'Lâm Khánh Yến',     'K23-KTPM',  24, FALSE);   -- KB4

-- ---------------------------------------------------------------------
-- Môn học
-- ---------------------------------------------------------------------
INSERT INTO mon_hoc (ma_mh, ten_mh, so_tin_chi) VALUES
('CSDL', 'Cơ sở dữ liệu',                  4),
('HQT',  'Hệ quản trị cơ sở dữ liệu',      4),
('CTDL', 'Cấu trúc dữ liệu và giải thuật', 4),
('MMT',  'Mạng máy tính',                  4),
('HDH',  'Hệ điều hành',                   4),
('OOP',  'Lập trình hướng đối tượng',      4),
('CNPM', 'Nhập môn công nghệ phần mềm',    3),
('XSTK', 'Xác suất thống kê',              3),
('PLDC', 'Pháp luật đại cương',            2),
('KTCT', 'Kinh tế chính trị Mác - Lênin',  2);

-- ---------------------------------------------------------------------
-- Lớp học phần (thu: 2..7, 8 = CN)
-- ---------------------------------------------------------------------
INSERT INTO lop_hoc_phan (ma_lhp, ma_mh, giang_vien, thu, tiet_bd, tiet_kt, phong, si_so_toi_da) VALUES
('CSDL.01', 'CSDL', 'ThS. Nguyễn Thị Mai',  2, 1, 3, 'A101',  60),
('CSDL.02', 'CSDL', 'TS. Trần Văn Bình',    4, 7, 9, 'A102',  60),
('HQT.01',  'HQT',  'TS. Lê Hoàng Nam',     3, 1, 3, 'B201',  50),
('HQT.02',  'HQT',  'ThS. Phạm Thu Hà',     5, 7, 9, 'B202',  50),
('HQT.03',  'HQT',  'TS. Lê Hoàng Nam',     7, 1, 3, 'B203',   2),
('CTDL.01', 'CTDL', 'ThS. Võ Minh Tuấn',    2, 2, 4, 'C301',  60),
('CTDL.02', 'CTDL', 'TS. Huỳnh Thị Lan',    6, 1, 3, 'C302',  60),
('MMT.01',  'MMT',  'TS. Đoàn Văn Phúc',    3, 7, 9, 'C303',  55),
('HDH.01',  'HDH',  'ThS. Nguyễn Hữu Tài',  4, 1, 3, 'A201',  55),
('OOP.01',  'OOP',  'ThS. Lê Thị Ngọc',     5, 1, 3, 'A202',  60),
('CNPM.01', 'CNPM', 'TS. Phan Minh Đức',    6, 7, 9, 'B101',  45),
('XSTK.01', 'XSTK', 'TS. Trương Văn Hải',   3, 4, 6, 'D101',  80),
('XSTK.02', 'XSTK', 'ThS. Mai Thị Hồng',    5, 4, 6, 'D102',  80),
('PLDC.01', 'PLDC', 'ThS. Vũ Thị Thảo',     7, 7, 8, 'D201',   3),
('KTCT.01', 'KTCT', 'TS. Ngô Văn Kiên',     6, 4, 5, 'D202', 100),
('KTCT.02', 'KTCT', 'TS. Ngô Văn Kiên',     7, 9, 10, 'D203',  1);

-- ---------------------------------------------------------------------
-- Đăng kí có sẵn (không vi phạm ràng buộc nào). PLDC.01 đã đầy (3/3).
-- ---------------------------------------------------------------------
INSERT INTO dang_ky (ma_sv, ma_lhp, ma_mh) VALUES
('SV01', 'CSDL.01', 'CSDL'), ('SV01', 'HQT.01', 'HQT'),  ('SV01', 'XSTK.01', 'XSTK'),
('SV02', 'CSDL.02', 'CSDL'), ('SV02', 'MMT.01', 'MMT'),  ('SV02', 'KTCT.01', 'KTCT'),
('SV03', 'CTDL.02', 'CTDL'), ('SV03', 'OOP.01', 'OOP'),  ('SV03', 'PLDC.01', 'PLDC'),
('SV04', 'HQT.02',  'HQT'),  ('SV04', 'HDH.01', 'HDH'),  ('SV04', 'PLDC.01', 'PLDC'),
('SV05', 'CSDL.01', 'CSDL'), ('SV05', 'CNPM.01', 'CNPM'), ('SV05', 'PLDC.01', 'PLDC'),
('SV06', 'XSTK.02', 'XSTK');

UPDATE lop_hoc_phan l
SET l.si_so_hien_tai = (SELECT COUNT(*) FROM dang_ky d WHERE d.ma_lhp = l.ma_lhp);
