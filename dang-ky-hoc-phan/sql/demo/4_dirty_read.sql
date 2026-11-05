-- =====================================================================
-- KỊCH BẢN 4 — ĐĂNG KÍ BỊ HUỶ GIỮA CHỪNG (Dirty read) — 2 phiên
-- KTCT.02 còn 1 chỗ. SV18 nợ học phí: giữ chỗ trước, kiểm tra học phí sau → ROLLBACK.
-- =====================================================================
USE dkhp;

-- ---------------- A. KHÔNG XỬ LÝ (T2 ở READ UNCOMMITTED) ----------------
CALL sp_dat_lai_kich_ban(4);
-- Phiên 1 (T1):
CALL sp_giu_cho_roi_huy('SV18', 'KTCT.02', 10);
-- Phiên 2 (T2), trong lúc phiên 1 đang chạy: đọc 1/1 (chưa COMMIT) → "Lớp đã đủ sĩ số"
CALL sp_dirty_read_loi('SV19', 'KTCT.02');

-- Sau khi phiên 1 ROLLBACK: lớp vẫn trống, SV19 đã bị từ chối oan
SELECT ma_lhp, si_so_hien_tai, si_so_toi_da FROM lop_hoc_phan WHERE ma_lhp = 'KTCT.02';

-- ---------------- B. CÓ XỬ LÝ (T2 ở READ COMMITTED) ----------------
CALL sp_dat_lai_kich_ban(4);
-- Phiên 1 (T1):
CALL sp_giu_cho_roi_huy('SV18', 'KTCT.02', 10);
-- Phiên 2 (T2): đọc 0/1 (bản đã COMMIT), chờ khoá ở bước UPDATE; T1 ROLLBACK xong thì thành công
CALL sp_dirty_read_an_toan('SV19', 'KTCT.02');

SELECT ma_lhp, si_so_hien_tai, si_so_toi_da FROM lop_hoc_phan WHERE ma_lhp = 'KTCT.02';
SELECT * FROM dang_ky WHERE ma_lhp = 'KTCT.02';
