-- =====================================================================
--  ĐỒ ÁN HỆ QUẢN TRỊ CƠ SỞ DỮ LIỆU — ĐĂNG KÍ HỌC PHẦN (MySQL 8, InnoDB)
--  File 1/3: Tạo CSDL, bảng, ràng buộc và view kiểm tra toàn vẹn
--  Chạy theo thứ tự: 01_schema.sql → 02_procedures.sql → 03_seed.sql
-- =====================================================================

DROP DATABASE IF EXISTS dkhp;
CREATE DATABASE dkhp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE dkhp;

-- ---------------------------------------------------------------------
-- SINH_VIEN
-- ---------------------------------------------------------------------
CREATE TABLE sinh_vien (
  ma_sv          VARCHAR(10)  NOT NULL COMMENT 'Mã sinh viên',
  ho_ten         VARCHAR(100) NOT NULL COMMENT 'Họ và tên',
  lop            VARCHAR(20)  NOT NULL COMMENT 'Lớp sinh hoạt',
  tin_chi_toi_da TINYINT      NOT NULL DEFAULT 24 COMMENT 'Số tín chỉ tối đa được đăng kí',
  no_hoc_phi     BOOLEAN      NOT NULL DEFAULT FALSE COMMENT 'Còn nợ học phí thì không được đăng kí',
  PRIMARY KEY (ma_sv)
) ENGINE = InnoDB COMMENT = 'Sinh viên';

-- ---------------------------------------------------------------------
-- MON_HOC (học phần)
-- ---------------------------------------------------------------------
CREATE TABLE mon_hoc (
  ma_mh      VARCHAR(10)  NOT NULL COMMENT 'Mã môn học',
  ten_mh     VARCHAR(100) NOT NULL COMMENT 'Tên môn học',
  so_tin_chi TINYINT      NOT NULL COMMENT 'Số tín chỉ',
  PRIMARY KEY (ma_mh),
  CONSTRAINT ck_mh_tin_chi CHECK (so_tin_chi BETWEEN 1 AND 10)
) ENGINE = InnoDB COMMENT = 'Môn học (học phần)';

-- ---------------------------------------------------------------------
-- LOP_HOC_PHAN (lớp mở cho 1 môn, có lịch học và sĩ số)
--   thu: 2..7 = Thứ 2..Thứ 7, 8 = Chủ nhật;  tiet: 1..12
-- ---------------------------------------------------------------------
CREATE TABLE lop_hoc_phan (
  ma_lhp         VARCHAR(15)  NOT NULL COMMENT 'Mã lớp học phần',
  ma_mh          VARCHAR(10)  NOT NULL COMMENT 'Môn của lớp',
  giang_vien     VARCHAR(100) NOT NULL COMMENT 'Giảng viên',
  thu            TINYINT      NOT NULL COMMENT 'Thứ học: 2..7, 8 = Chủ nhật',
  tiet_bd        TINYINT      NOT NULL COMMENT 'Tiết bắt đầu (1..12)',
  tiet_kt        TINYINT      NOT NULL COMMENT 'Tiết kết thúc (1..12)',
  phong          VARCHAR(20)  NOT NULL COMMENT 'Phòng học',
  si_so_toi_da   INT          NOT NULL COMMENT 'Sĩ số tối đa',
  si_so_hien_tai INT          NOT NULL DEFAULT 0 COMMENT 'Số sinh viên đã đăng kí',
  PRIMARY KEY (ma_lhp),
  UNIQUE KEY uq_lhp_mh (ma_lhp, ma_mh),        -- để dang_ky tham chiếu cặp (ma_lhp, ma_mh)
  CONSTRAINT fk_lhp_mh FOREIGN KEY (ma_mh) REFERENCES mon_hoc (ma_mh),
  CONSTRAINT ck_lhp_thu   CHECK (thu BETWEEN 2 AND 8),
  CONSTRAINT ck_lhp_tiet  CHECK (tiet_bd BETWEEN 1 AND 12 AND tiet_kt BETWEEN tiet_bd AND 12),
  CONSTRAINT ck_lhp_si_so CHECK (si_so_toi_da > 0 AND si_so_hien_tai >= 0)
) ENGINE = InnoDB COMMENT = 'Lớp học phần: lớp mở cho một môn, có lịch học và sĩ số';

-- ---------------------------------------------------------------------
-- DANG_KY (sinh viên đăng kí lớp học phần)
--   ma_mh được lưu kèm để kiểm tra "trùng học phần" nhanh (có index);
--   khoá ngoại kép (ma_lhp, ma_mh) bảo đảm ma_mh luôn khớp với lớp.
-- ---------------------------------------------------------------------
CREATE TABLE dang_ky (
  id        INT          NOT NULL AUTO_INCREMENT COMMENT 'Mã lượt đăng kí (tự tăng)',
  ma_sv     VARCHAR(10)  NOT NULL COMMENT 'Sinh viên đăng kí',
  ma_lhp    VARCHAR(15)  NOT NULL COMMENT 'Lớp được đăng kí',
  ma_mh     VARCHAR(10)  NOT NULL COMMENT 'Môn của lớp (lưu kèm để kiểm tra trùng học phần)',
  thoi_gian DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT 'Thời điểm đăng kí',
  PRIMARY KEY (id),
  UNIQUE KEY uq_dk_sv_lhp (ma_sv, ma_lhp),     -- không đăng kí 1 lớp 2 lần
  KEY idx_dk_sv_mh (ma_sv, ma_mh),             -- phục vụ kiểm tra trùng học phần
  CONSTRAINT fk_dk_sv  FOREIGN KEY (ma_sv) REFERENCES sinh_vien (ma_sv),
  CONSTRAINT fk_dk_lhp FOREIGN KEY (ma_lhp, ma_mh) REFERENCES lop_hoc_phan (ma_lhp, ma_mh)
) ENGINE = InnoDB COMMENT = 'Đăng kí: sinh viên đăng kí lớp học phần';

-- ---------------------------------------------------------------------
-- VIEW kiểm tra toàn vẹn: mỗi dòng là 1 vi phạm do xung đột đồng thời gây ra.
-- Dữ liệu đúng ⇔ view rỗng.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_kiem_tra_toan_ven AS
-- (1) Lớp có số SV đăng kí vượt sĩ số tối đa  (Tranh slot)
SELECT 'VUOT_SI_SO' AS loai, l.ma_lhp AS doi_tuong,
       CONCAT('Có ', COUNT(d.id), ' SV đăng kí nhưng sĩ số tối đa chỉ ', l.si_so_toi_da) AS chi_tiet
FROM lop_hoc_phan l JOIN dang_ky d ON d.ma_lhp = l.ma_lhp
GROUP BY l.ma_lhp, l.si_so_toi_da
HAVING COUNT(d.id) > l.si_so_toi_da
UNION ALL
-- (2) Cột si_so_hien_tai không khớp số đăng kí thực tế  (Lost update)
SELECT 'SAI_SI_SO', l.ma_lhp,
       CONCAT('si_so_hien_tai = ', l.si_so_hien_tai, ' nhưng thực tế có ', COUNT(d.id), ' SV')
FROM lop_hoc_phan l LEFT JOIN dang_ky d ON d.ma_lhp = l.ma_lhp
GROUP BY l.ma_lhp, l.si_so_hien_tai
HAVING COUNT(d.id) <> l.si_so_hien_tai
UNION ALL
-- (3) Một SV có 2 lớp trùng lịch  (Trùng lịch)
SELECT 'TRUNG_LICH', d1.ma_sv,
       CONCAT(d1.ma_lhp, ' và ', d2.ma_lhp, ' cùng ', IF(l1.thu = 8, 'Chủ nhật', CONCAT('Thứ ', l1.thu)),
              ', tiết ', l1.tiet_bd, '-', l1.tiet_kt, ' / ', l2.tiet_bd, '-', l2.tiet_kt)
FROM dang_ky d1
JOIN dang_ky d2      ON d2.ma_sv = d1.ma_sv AND d1.ma_lhp < d2.ma_lhp
JOIN lop_hoc_phan l1 ON l1.ma_lhp = d1.ma_lhp
JOIN lop_hoc_phan l2 ON l2.ma_lhp = d2.ma_lhp
WHERE l1.thu = l2.thu AND l1.tiet_bd <= l2.tiet_kt AND l2.tiet_bd <= l1.tiet_kt
UNION ALL
-- (4) Một SV đăng kí nhiều lớp của cùng 1 môn  (Trùng học phần)
SELECT 'TRUNG_HOC_PHAN', ma_sv,
       CONCAT('Đăng kí ', COUNT(*), ' lớp của môn ', ma_mh, ': ',
              GROUP_CONCAT(ma_lhp ORDER BY ma_lhp SEPARATOR ', '))
FROM dang_ky
GROUP BY ma_sv, ma_mh
HAVING COUNT(*) > 1
UNION ALL
-- (5) Vượt số tín chỉ tối đa
SELECT 'VUOT_TIN_CHI', s.ma_sv,
       CONCAT('Đăng kí ', SUM(m.so_tin_chi), ' TC, tối đa ', s.tin_chi_toi_da, ' TC')
FROM sinh_vien s
JOIN dang_ky d ON d.ma_sv = s.ma_sv
JOIN mon_hoc m ON m.ma_mh = d.ma_mh
GROUP BY s.ma_sv, s.tin_chi_toi_da
HAVING SUM(m.so_tin_chi) > s.tin_chi_toi_da;
