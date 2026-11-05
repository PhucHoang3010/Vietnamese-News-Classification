-- =====================================================================
-- KỊCH BẢN 1 — TRANH SLOT (Lost update) — demo thủ công bằng 2 phiên
-- Cần 2 KẾT NỐI riêng: trong MySQL Workbench bấm vào connection ở màn hình Home
-- 2 lần (2 tab kết nối). Các tab query trong CÙNG 1 kết nối dùng chung 1 phiên nên không được.
-- Hoặc mở 2 cửa sổ: mysql -u root -p --default-character-set=utf8mb4 dkhp
-- =====================================================================
USE dkhp;

-- (0) Chuẩn bị, chạy ở phiên nào cũng được. Lớp HQT.03 chỉ còn 1 chỗ để 2 phiên là đủ thấy lỗi.
CALL sp_dat_lai_kich_ban(1);
UPDATE lop_hoc_phan SET si_so_toi_da = 1 WHERE ma_lhp = 'HQT.03';

-- ---------------- A. KHÔNG XỬ LÝ ----------------
-- Phiên 1:
CALL sp_tranh_slot_loi('SV11', 'HQT.03', 10);
-- Phiên 2 (chạy trong vòng 10 giây sau phiên 1):
CALL sp_tranh_slot_loi('SV12', 'HQT.03', 10);

-- Kết quả: cả 2 thành công, lớp 1 chỗ có 2 SV, si_so_hien_tai = 1 (lost update)
SELECT si_so_toi_da, si_so_hien_tai,
       (SELECT COUNT(*) FROM dang_ky WHERE ma_lhp = 'HQT.03') AS so_dk_thuc_te
FROM lop_hoc_phan WHERE ma_lhp = 'HQT.03';
SELECT * FROM v_kiem_tra_toan_ven WHERE doi_tuong = 'HQT.03';

-- ---------------- B. CÓ XỬ LÝ (SELECT ... FOR UPDATE) ----------------
CALL sp_dat_lai_kich_ban(1);
UPDATE lop_hoc_phan SET si_so_toi_da = 1 WHERE ma_lhp = 'HQT.03';
-- Phiên 1:
CALL sp_tranh_slot_an_toan('SV11', 'HQT.03', 10);
-- Phiên 2: bị treo (chờ khoá) đến khi phiên 1 COMMIT, sau đó nhận "Lớp đã đủ sĩ số"
CALL sp_tranh_slot_an_toan('SV12', 'HQT.03', 10);

SELECT si_so_toi_da, si_so_hien_tai,
       (SELECT COUNT(*) FROM dang_ky WHERE ma_lhp = 'HQT.03') AS so_dk_thuc_te
FROM lop_hoc_phan WHERE ma_lhp = 'HQT.03';
