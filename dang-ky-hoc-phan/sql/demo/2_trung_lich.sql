-- =====================================================================
-- KỊCH BẢN 2 — TRÙNG LỊCH ĐỒNG THỜI (Phantom / Write skew) — 2 phiên
-- CSDL.01: Thứ 2 tiết 1-3   |   CTDL.01: Thứ 2 tiết 2-4   → trùng giờ
-- =====================================================================
USE dkhp;

-- ---------------- A. KHÔNG XỬ LÝ ----------------
CALL sp_dat_lai_kich_ban(2);
-- Phiên 1:
CALL sp_trung_lich_loi('SV16', 'CSDL.01', 10);
-- Phiên 2 (trong vòng 10 giây):
CALL sp_trung_lich_loi('SV16', 'CTDL.01', 10);

-- Kết quả: cả 2 thành công → SV16 có 2 lớp trùng giờ
SELECT * FROM v_kiem_tra_toan_ven WHERE loai = 'TRUNG_LICH' AND doi_tuong = 'SV16';

-- ---------------- B. CÓ XỬ LÝ (khoá dòng sinh_vien FOR UPDATE) ----------------
CALL sp_dat_lai_kich_ban(2);
-- Phiên 1:
CALL sp_trung_lich_an_toan('SV16', 'CSDL.01', 10);
-- Phiên 2: chờ phiên 1 COMMIT, rồi bị từ chối "Trùng lịch với lớp CSDL.01"
CALL sp_trung_lich_an_toan('SV16', 'CTDL.01', 10);

SELECT * FROM v_kiem_tra_toan_ven WHERE loai = 'TRUNG_LICH' AND doi_tuong = 'SV16';   -- rỗng
