-- =====================================================================
-- KỊCH BẢN 3 — TRÙNG HỌC PHẦN (Phantom khi chèn) — 2 phiên
-- HQT.01 và HQT.02: khác giờ nhưng cùng môn HQT
-- =====================================================================
USE dkhp;

-- ---------------- A. KHÔNG XỬ LÝ ----------------
CALL sp_dat_lai_kich_ban(3);
-- Phiên 1:
CALL sp_trung_hp_loi('SV17', 'HQT.01', 10);
-- Phiên 2 (trong vòng 10 giây):
CALL sp_trung_hp_loi('SV17', 'HQT.02', 10);

SELECT * FROM v_kiem_tra_toan_ven WHERE loai = 'TRUNG_HOC_PHAN' AND doi_tuong = 'SV17';

-- ---------------- B. CÓ XỬ LÝ — Cách 1: SERIALIZABLE ----------------
CALL sp_dat_lai_kich_ban(3);
-- Phiên 1:
CALL sp_trung_hp_an_toan('SV17', 'HQT.01', 10);
-- Phiên 2: khi cả hai cùng INSERT, một bên nhận ket_qua = 'LOI', ma_loi = 1213 (Deadlock)
--          → chạy lại lệnh đó lần nữa: bị từ chối "Đã đăng kí môn HQT ở lớp ..."
CALL sp_trung_hp_an_toan('SV17', 'HQT.02', 10);

SELECT * FROM v_kiem_tra_toan_ven WHERE loai = 'TRUNG_HOC_PHAN' AND doi_tuong = 'SV17';   -- rỗng

-- ---------------- C. CÓ XỬ LÝ — Cách 2: ràng buộc UNIQUE (lớp bảo vệ cuối) ----------------
-- Để DBMS tự chặn: dù thủ tục _loi vẫn chạy song song, dòng thứ 2 bị từ chối với lỗi 1062.
CALL sp_dat_lai_kich_ban(3);
ALTER TABLE dang_ky ADD CONSTRAINT uq_dk_sv_mh UNIQUE (ma_sv, ma_mh);
-- Phiên 1:
CALL sp_trung_hp_loi('SV17', 'HQT.01', 10);
-- Phiên 2: nhận ket_qua = 'LOI', ma_loi = 1062 (Duplicate entry 'SV17-HQT')
CALL sp_trung_hp_loi('SV17', 'HQT.02', 10);

-- Gỡ ràng buộc để các lần demo "KHÔNG xử lý" sau vẫn thấy lỗi
ALTER TABLE dang_ky DROP INDEX uq_dk_sv_mh;
