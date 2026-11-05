-- =====================================================================
--  File 2/3: Stored procedure
--
--  A. sp_dang_ky_mo_phong / sp_dang_ky / sp_huy_dang_ky — dùng cho trang web
--     (đủ mọi kiểm tra; có công tắc CÓ / KHÔNG xử lý đồng thời để mô phỏng trực tiếp trên web)
--  B. Các cặp thủ tục giả lập xung đột (tham số p_tre = số giây "xử lý chậm"
--     chèn giữa bước ĐỌC và bước GHI để mở rộng cửa sổ tranh chấp):
--       KB1 Tranh slot          sp_tranh_slot_loi      / sp_tranh_slot_an_toan
--       KB2 Trùng lịch đồng thời sp_trung_lich_loi      / sp_trung_lich_an_toan
--       KB3 Trùng học phần      sp_trung_hp_loi        / sp_trung_hp_an_toan
--       KB4 Đăng kí bị huỷ giữa chừng (dirty read)
--                               sp_giu_cho_roi_huy (T1) + sp_dirty_read_loi / sp_dirty_read_an_toan (T2)
--  C. sp_dat_lai_kich_ban(kb)   — đưa dữ liệu của kịch bản về trạng thái ban đầu
--
--  Mọi thủ tục trả về 1 dòng: ket_qua (THANH_CONG | TU_CHOI | LOI), thong_bao,
--  ma_loi (mã lỗi MySQL nếu có) và nhat_ky (các bước kèm thời điểm, để vẽ lịch T1/T2).
--  Những dòng đánh dấu [SỬA] là điểm khác nhau giữa bản _loi và bản _an_toan.
-- =====================================================================
USE dkhp;

DELIMITER $$

-- ---------------------------------------------------------------------
-- Tiện ích ghi nhật ký: mỗi dòng "thời_điểm|LOẠI|nội dung"
-- LOẠI: BEGIN, READ, WRITE, LOCK, INFO, COMMIT, ROLLBACK
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_log $$
CREATE PROCEDURE sp_log(INOUT p_log TEXT, IN p_loai VARCHAR(10), IN p_msg VARCHAR(500))
BEGIN
  SET p_log = CONCAT(IFNULL(p_log, ''),
                     DATE_FORMAT(SYSDATE(3), '%Y-%m-%d %H:%i:%s.%f'), '|', p_loai, '|', p_msg, '\n');
END $$


-- =====================================================================
-- A. THỦ TỤC CHÍNH CHO TRANG WEB
-- =====================================================================

-- ---------------------------------------------------------------------
-- sp_dang_ky_mo_phong: thủ tục đăng kí mà nút "Đăng kí" trên trang web gọi.
--   p_co_xu_ly = TRUE  (CÓ xử lý đồng thời):
--     B1. Khoá dòng SINH_VIEN (FOR UPDATE) → mọi thao tác của cùng 1 SV chạy tuần tự
--         ⇒ chống trùng lịch, trùng học phần, vượt tín chỉ.
--         Phải là câu lệnh ĐẦU TIÊN của giao dịch (xem giải thích KB2).
--     B2. Khoá dòng LOP_HOC_PHAN (FOR UPDATE) → các SV tranh 1 lớp chạy tuần tự
--         ⇒ chống tranh slot / lost update.
--     Thứ tự khoá luôn là SV → LHP để không gây deadlock giữa các lần gọi.
--   p_co_xu_ly = FALSE (KHÔNG xử lý): cùng các bước kiểm tra nhưng đọc thường,
--     không khoá, ghi sĩ số bằng giá trị đã đọc → mở 2 cửa sổ bấm cùng lúc sẽ thấy lỗi.
--   p_tre: số giây "xử lý chậm" giữa bước kiểm tra và bước ghi (0 = không chậm).
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_dang_ky_mo_phong $$
CREATE PROCEDURE sp_dang_ky_mo_phong(IN p_ma_sv VARCHAR(10), IN p_ma_lhp VARCHAR(15),
                                     IN p_co_xu_ly BOOLEAN, IN p_tre DECIMAL(5,2))
BEGIN
  DECLARE v_log TEXT DEFAULT '';
  DECLARE v_kq VARCHAR(20) DEFAULT 'THANH_CONG';
  DECLARE v_tb VARCHAR(500) DEFAULT 'Đăng kí thành công';
  DECLARE v_loi INT DEFAULT NULL;
  DECLARE v_khong_thay BOOLEAN DEFAULT FALSE;
  DECLARE v_tc_max, v_no_hp, v_tc_mon, v_tc_da_dk, v_dem INT;
  DECLARE v_thu, v_bd, v_kt, v_si_so, v_toi_da INT;
  DECLARE v_ma_mh VARCHAR(10);
  DECLARE v_lhp_trung VARCHAR(15);
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_khong_thay = TRUE;
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    GET DIAGNOSTICS CONDITION 1 v_loi = MYSQL_ERRNO, v_tb = MESSAGE_TEXT;
    ROLLBACK;
    CALL sp_log(v_log, 'ROLLBACK', CONCAT('Lỗi ', v_loi, ': ', v_tb));
    SELECT 'LOI' AS ket_qua, v_tb AS thong_bao, v_loi AS ma_loi, v_log AS nhat_ky;
  END;

  CALL sp_log(v_log, 'BEGIN', CONCAT(p_ma_sv, ' đăng kí ', p_ma_lhp, IF(p_co_xu_ly, '', ' [KHÔNG xử lý]')));
  START TRANSACTION;

  xu_ly: BEGIN
    -- B1. Đọc (và khoá) dòng sinh viên
    IF p_co_xu_ly THEN
      SELECT tin_chi_toi_da, no_hoc_phi INTO v_tc_max, v_no_hp
      FROM sinh_vien WHERE ma_sv = p_ma_sv FOR UPDATE;
    ELSE
      SELECT tin_chi_toi_da, no_hoc_phi INTO v_tc_max, v_no_hp
      FROM sinh_vien WHERE ma_sv = p_ma_sv;
    END IF;
    IF v_khong_thay THEN SET v_kq = 'TU_CHOI', v_tb = 'Không tìm thấy sinh viên'; LEAVE xu_ly; END IF;
    IF v_no_hp THEN SET v_kq = 'TU_CHOI', v_tb = 'Sinh viên còn nợ học phí, không được đăng kí'; LEAVE xu_ly; END IF;

    -- B2. Đọc (và khoá) dòng lớp học phần
    IF p_co_xu_ly THEN
      SELECT ma_mh, thu, tiet_bd, tiet_kt, si_so_hien_tai, si_so_toi_da
        INTO v_ma_mh, v_thu, v_bd, v_kt, v_si_so, v_toi_da
      FROM lop_hoc_phan WHERE ma_lhp = p_ma_lhp FOR UPDATE;
    ELSE
      SELECT ma_mh, thu, tiet_bd, tiet_kt, si_so_hien_tai, si_so_toi_da
        INTO v_ma_mh, v_thu, v_bd, v_kt, v_si_so, v_toi_da
      FROM lop_hoc_phan WHERE ma_lhp = p_ma_lhp;
    END IF;
    IF v_khong_thay THEN SET v_kq = 'TU_CHOI', v_tb = 'Không tìm thấy lớp học phần'; LEAVE xu_ly; END IF;
    CALL sp_log(v_log, 'READ', CONCAT('Đọc ', p_ma_lhp, ': sĩ số ', v_si_so, '/', v_toi_da));

    -- B3. Kiểm tra nghiệp vụ
    SELECT COUNT(*) INTO v_dem FROM dang_ky WHERE ma_sv = p_ma_sv AND ma_lhp = p_ma_lhp;
    IF v_dem > 0 THEN SET v_kq = 'TU_CHOI', v_tb = 'Bạn đã đăng kí lớp này rồi'; LEAVE xu_ly; END IF;

    SELECT COUNT(*), MIN(ma_lhp) INTO v_dem, v_lhp_trung
    FROM dang_ky WHERE ma_sv = p_ma_sv AND ma_mh = v_ma_mh;
    IF v_dem > 0 THEN
      SET v_kq = 'TU_CHOI', v_tb = CONCAT('Trùng học phần: đã đăng kí môn ', v_ma_mh, ' ở lớp ', v_lhp_trung);
      LEAVE xu_ly;
    END IF;

    SELECT COUNT(*), MIN(d.ma_lhp) INTO v_dem, v_lhp_trung
    FROM dang_ky d JOIN lop_hoc_phan l ON l.ma_lhp = d.ma_lhp
    WHERE d.ma_sv = p_ma_sv AND l.thu = v_thu AND l.tiet_bd <= v_kt AND v_bd <= l.tiet_kt;
    IF v_dem > 0 THEN
      SET v_kq = 'TU_CHOI', v_tb = CONCAT('Trùng lịch với lớp ', v_lhp_trung);
      LEAVE xu_ly;
    END IF;

    SELECT so_tin_chi INTO v_tc_mon FROM mon_hoc WHERE ma_mh = v_ma_mh;
    SELECT IFNULL(SUM(m.so_tin_chi), 0) INTO v_tc_da_dk
    FROM dang_ky d JOIN mon_hoc m ON m.ma_mh = d.ma_mh WHERE d.ma_sv = p_ma_sv;
    IF v_tc_da_dk + v_tc_mon > v_tc_max THEN
      SET v_kq = 'TU_CHOI',
          v_tb = CONCAT('Vượt số tín chỉ tối đa (', v_tc_da_dk, ' + ', v_tc_mon, ' > ', v_tc_max, ')');
      LEAVE xu_ly;
    END IF;

    IF v_si_so >= v_toi_da THEN SET v_kq = 'TU_CHOI', v_tb = 'Lớp đã đủ sĩ số'; LEAVE xu_ly; END IF;

    -- Xử lý chậm (để kịp bấm ở cửa sổ thứ hai)
    IF p_tre > 0 THEN
      CALL sp_log(v_log, 'INFO', CONCAT('Hợp lệ → xử lý ', p_tre, 's...'));
      DO SLEEP(p_tre);
    END IF;

    -- B4. Ghi (cập nhật dòng cha trước, chèn dòng con sau)
    IF p_co_xu_ly THEN
      UPDATE lop_hoc_phan SET si_so_hien_tai = si_so_hien_tai + 1 WHERE ma_lhp = p_ma_lhp;
    ELSE
      UPDATE lop_hoc_phan SET si_so_hien_tai = v_si_so + 1 WHERE ma_lhp = p_ma_lhp;  -- ghi đè giá trị đã đọc
    END IF;
    INSERT INTO dang_ky (ma_sv, ma_lhp, ma_mh) VALUES (p_ma_sv, p_ma_lhp, v_ma_mh);
    CALL sp_log(v_log, 'WRITE', CONCAT('Ghi dang_ky; si_so_hien_tai := ', v_si_so + 1));
  END xu_ly;

  IF v_kq = 'THANH_CONG' THEN COMMIT; CALL sp_log(v_log, 'COMMIT', v_tb);
  ELSE ROLLBACK; CALL sp_log(v_log, 'ROLLBACK', v_tb);
  END IF;
  SELECT v_kq AS ket_qua, v_tb AS thong_bao, v_loi AS ma_loi, v_log AS nhat_ky;
END $$


-- ---------------------------------------------------------------------
-- sp_dang_ky: bản đăng kí chuẩn = có xử lý đồng thời, không chậm
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_dang_ky $$
CREATE PROCEDURE sp_dang_ky(IN p_ma_sv VARCHAR(10), IN p_ma_lhp VARCHAR(15))
BEGIN
  CALL sp_dang_ky_mo_phong(p_ma_sv, p_ma_lhp, TRUE, 0);
END $$


-- ---------------------------------------------------------------------
-- sp_huy_dang_ky: huỷ 1 lớp đã đăng kí (cùng thứ tự khoá SV → LHP)
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_huy_dang_ky $$
CREATE PROCEDURE sp_huy_dang_ky(IN p_ma_sv VARCHAR(10), IN p_ma_lhp VARCHAR(15))
BEGIN
  DECLARE v_log TEXT DEFAULT '';
  DECLARE v_kq VARCHAR(20) DEFAULT 'THANH_CONG';
  DECLARE v_tb VARCHAR(500) DEFAULT 'Đã huỷ đăng kí';
  DECLARE v_loi INT DEFAULT NULL;
  DECLARE v_khong_thay BOOLEAN DEFAULT FALSE;
  DECLARE v_tmp VARCHAR(15);
  DECLARE v_n INT;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_khong_thay = TRUE;
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    GET DIAGNOSTICS CONDITION 1 v_loi = MYSQL_ERRNO, v_tb = MESSAGE_TEXT;
    ROLLBACK;
    SELECT 'LOI' AS ket_qua, v_tb AS thong_bao, v_loi AS ma_loi, v_log AS nhat_ky;
  END;

  CALL sp_log(v_log, 'BEGIN', CONCAT(p_ma_sv, ' huỷ ', p_ma_lhp));
  START TRANSACTION;
  xu_ly: BEGIN
    SELECT ma_sv INTO v_tmp FROM sinh_vien WHERE ma_sv = p_ma_sv FOR UPDATE;
    IF v_khong_thay THEN SET v_kq = 'TU_CHOI', v_tb = 'Không tìm thấy sinh viên'; LEAVE xu_ly; END IF;
    SELECT ma_lhp INTO v_tmp FROM lop_hoc_phan WHERE ma_lhp = p_ma_lhp FOR UPDATE;
    IF v_khong_thay THEN SET v_kq = 'TU_CHOI', v_tb = 'Không tìm thấy lớp học phần'; LEAVE xu_ly; END IF;

    DELETE FROM dang_ky WHERE ma_sv = p_ma_sv AND ma_lhp = p_ma_lhp;
    SET v_n = ROW_COUNT();
    IF v_n = 0 THEN SET v_kq = 'TU_CHOI', v_tb = 'Bạn chưa đăng kí lớp này'; LEAVE xu_ly; END IF;
    UPDATE lop_hoc_phan SET si_so_hien_tai = GREATEST(si_so_hien_tai - v_n, 0) WHERE ma_lhp = p_ma_lhp;
  END xu_ly;

  IF v_kq = 'THANH_CONG' THEN COMMIT; CALL sp_log(v_log, 'COMMIT', v_tb);
  ELSE ROLLBACK; CALL sp_log(v_log, 'ROLLBACK', v_tb);
  END IF;
  SELECT v_kq AS ket_qua, v_tb AS thong_bao, v_loi AS ma_loi, v_log AS nhat_ky;
END $$


-- =====================================================================
-- B1. KỊCH BẢN 1 — TRANH SLOT (Lost update)
--   Nhiều SV cùng đăng kí 1 lớp sắp đầy. Mỗi giao dịch: ĐỌC sĩ số → còn chỗ →
--   (xử lý chậm) → GHI sĩ số = giá_trị_đã_đọc + 1.
-- =====================================================================
DROP PROCEDURE IF EXISTS sp_tranh_slot_loi $$
CREATE PROCEDURE sp_tranh_slot_loi(IN p_ma_sv VARCHAR(10), IN p_ma_lhp VARCHAR(15), IN p_tre DECIMAL(5,2))
BEGIN
  DECLARE v_log TEXT DEFAULT '';
  DECLARE v_kq VARCHAR(20) DEFAULT 'THANH_CONG';
  DECLARE v_tb VARCHAR(500) DEFAULT 'Đăng kí thành công';
  DECLARE v_loi INT DEFAULT NULL;
  DECLARE v_ma_mh VARCHAR(10);
  DECLARE v_si_so, v_toi_da INT;
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    GET DIAGNOSTICS CONDITION 1 v_loi = MYSQL_ERRNO, v_tb = MESSAGE_TEXT;
    ROLLBACK;
    CALL sp_log(v_log, 'ROLLBACK', CONCAT('Lỗi ', v_loi, ': ', v_tb));
    SELECT 'LOI' AS ket_qua, v_tb AS thong_bao, v_loi AS ma_loi, v_log AS nhat_ky;
  END;

  CALL sp_log(v_log, 'BEGIN', CONCAT(p_ma_sv, ' đăng kí ', p_ma_lhp));
  START TRANSACTION;
  xu_ly: BEGIN
    -- (1) ĐỌC sĩ số: đọc thường, KHÔNG khoá → các giao dịch khác vẫn đọc được cùng giá trị
    SELECT ma_mh, si_so_hien_tai, si_so_toi_da INTO v_ma_mh, v_si_so, v_toi_da
    FROM lop_hoc_phan WHERE ma_lhp = p_ma_lhp;
    CALL sp_log(v_log, 'READ', CONCAT('Đọc sĩ số ', p_ma_lhp, ' = ', v_si_so, '/', v_toi_da));
    IF v_si_so >= v_toi_da THEN SET v_kq = 'TU_CHOI', v_tb = 'Lớp đã đủ sĩ số'; LEAVE xu_ly; END IF;

    -- (2) Xử lý chậm
    CALL sp_log(v_log, 'INFO', CONCAT('Còn chỗ → xử lý ', p_tre, 's...'));
    DO SLEEP(p_tre);

    -- (3) GHI bằng giá trị đã đọc ở (1)
    UPDATE lop_hoc_phan SET si_so_hien_tai = v_si_so + 1 WHERE ma_lhp = p_ma_lhp;
    INSERT INTO dang_ky (ma_sv, ma_lhp, ma_mh) VALUES (p_ma_sv, p_ma_lhp, v_ma_mh);
    CALL sp_log(v_log, 'WRITE', CONCAT('Ghi dang_ky; si_so_hien_tai := ', v_si_so + 1));
  END xu_ly;

  IF v_kq = 'THANH_CONG' THEN COMMIT; CALL sp_log(v_log, 'COMMIT', v_tb);
  ELSE ROLLBACK; CALL sp_log(v_log, 'ROLLBACK', v_tb);
  END IF;
  SELECT v_kq AS ket_qua, v_tb AS thong_bao, v_loi AS ma_loi, v_log AS nhat_ky;
END $$

DROP PROCEDURE IF EXISTS sp_tranh_slot_an_toan $$
CREATE PROCEDURE sp_tranh_slot_an_toan(IN p_ma_sv VARCHAR(10), IN p_ma_lhp VARCHAR(15), IN p_tre DECIMAL(5,2))
BEGIN
  DECLARE v_log TEXT DEFAULT '';
  DECLARE v_kq VARCHAR(20) DEFAULT 'THANH_CONG';
  DECLARE v_tb VARCHAR(500) DEFAULT 'Đăng kí thành công';
  DECLARE v_loi INT DEFAULT NULL;
  DECLARE v_ma_mh VARCHAR(10);
  DECLARE v_si_so, v_toi_da INT;
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    GET DIAGNOSTICS CONDITION 1 v_loi = MYSQL_ERRNO, v_tb = MESSAGE_TEXT;
    ROLLBACK;
    CALL sp_log(v_log, 'ROLLBACK', CONCAT('Lỗi ', v_loi, ': ', v_tb));
    SELECT 'LOI' AS ket_qua, v_tb AS thong_bao, v_loi AS ma_loi, v_log AS nhat_ky;
  END;

  CALL sp_log(v_log, 'BEGIN', CONCAT(p_ma_sv, ' đăng kí ', p_ma_lhp));
  START TRANSACTION;
  xu_ly: BEGIN
    -- (1) [SỬA] ĐỌC CÓ KHOÁ: SELECT ... FOR UPDATE giữ khoá X trên dòng lớp đến khi COMMIT.
    --     Giao dịch khác muốn đọc-có-khoá dòng này phải CHỜ → đọc được sĩ số mới nhất.
    CALL sp_log(v_log, 'LOCK', CONCAT('SELECT ... FOR UPDATE: xin khoá X dòng ', p_ma_lhp));
    SELECT ma_mh, si_so_hien_tai, si_so_toi_da INTO v_ma_mh, v_si_so, v_toi_da
    FROM lop_hoc_phan WHERE ma_lhp = p_ma_lhp
    FOR UPDATE;
    CALL sp_log(v_log, 'READ', CONCAT('Được cấp khoá. Đọc sĩ số ', p_ma_lhp, ' = ', v_si_so, '/', v_toi_da));
    IF v_si_so >= v_toi_da THEN SET v_kq = 'TU_CHOI', v_tb = 'Lớp đã đủ sĩ số'; LEAVE xu_ly; END IF;

    -- (2) Xử lý chậm
    CALL sp_log(v_log, 'INFO', CONCAT('Còn chỗ → xử lý ', p_tre, 's...'));
    DO SLEEP(p_tre);

    -- (3) GHI (giá trị đã đọc giờ là mới nhất vì đang giữ khoá)
    UPDATE lop_hoc_phan SET si_so_hien_tai = v_si_so + 1 WHERE ma_lhp = p_ma_lhp;
    INSERT INTO dang_ky (ma_sv, ma_lhp, ma_mh) VALUES (p_ma_sv, p_ma_lhp, v_ma_mh);
    CALL sp_log(v_log, 'WRITE', CONCAT('Ghi dang_ky; si_so_hien_tai := ', v_si_so + 1));
  END xu_ly;

  IF v_kq = 'THANH_CONG' THEN COMMIT; CALL sp_log(v_log, 'COMMIT', CONCAT(v_tb, ' — nhả khoá'));
  ELSE ROLLBACK; CALL sp_log(v_log, 'ROLLBACK', CONCAT(v_tb, ' — nhả khoá'));
  END IF;
  SELECT v_kq AS ket_qua, v_tb AS thong_bao, v_loi AS ma_loi, v_log AS nhat_ky;
END $$


-- =====================================================================
-- B2. KỊCH BẢN 2 — TRÙNG LỊCH ĐỒNG THỜI (Phantom / Write skew)
--   1 SV mở 2 tab, cùng lúc đăng kí 2 lớp KHÁC NHAU nhưng trùng giờ học.
--   Mỗi giao dịch kiểm tra "chưa có lớp nào trùng lịch" rồi mới chèn.
-- =====================================================================
DROP PROCEDURE IF EXISTS sp_trung_lich_loi $$
CREATE PROCEDURE sp_trung_lich_loi(IN p_ma_sv VARCHAR(10), IN p_ma_lhp VARCHAR(15), IN p_tre DECIMAL(5,2))
BEGIN
  DECLARE v_log TEXT DEFAULT '';
  DECLARE v_kq VARCHAR(20) DEFAULT 'THANH_CONG';
  DECLARE v_tb VARCHAR(500) DEFAULT 'Đăng kí thành công';
  DECLARE v_loi INT DEFAULT NULL;
  DECLARE v_ma_mh VARCHAR(10);
  DECLARE v_lhp_trung VARCHAR(15);
  DECLARE v_thu, v_bd, v_kt, v_dem INT;
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    GET DIAGNOSTICS CONDITION 1 v_loi = MYSQL_ERRNO, v_tb = MESSAGE_TEXT;
    ROLLBACK;
    CALL sp_log(v_log, 'ROLLBACK', CONCAT('Lỗi ', v_loi, ': ', v_tb));
    SELECT 'LOI' AS ket_qua, v_tb AS thong_bao, v_loi AS ma_loi, v_log AS nhat_ky;
  END;

  CALL sp_log(v_log, 'BEGIN', CONCAT(p_ma_sv, ' đăng kí ', p_ma_lhp));
  START TRANSACTION;
  xu_ly: BEGIN
    SELECT ma_mh, thu, tiet_bd, tiet_kt INTO v_ma_mh, v_thu, v_bd, v_kt
    FROM lop_hoc_phan WHERE ma_lhp = p_ma_lhp;

    -- (1) ĐỌC: kiểm tra trùng lịch (đọc snapshot, không khoá)
    SELECT COUNT(*), MIN(d.ma_lhp) INTO v_dem, v_lhp_trung
    FROM dang_ky d JOIN lop_hoc_phan l ON l.ma_lhp = d.ma_lhp
    WHERE d.ma_sv = p_ma_sv AND l.thu = v_thu AND l.tiet_bd <= v_kt AND v_bd <= l.tiet_kt;
    CALL sp_log(v_log, 'READ', CONCAT('Kiểm tra lịch Thứ ', v_thu, ' tiết ', v_bd, '-', v_kt, ': ',
                                      IF(v_dem = 0, 'không trùng', CONCAT('trùng ', v_lhp_trung))));
    IF v_dem > 0 THEN SET v_kq = 'TU_CHOI', v_tb = CONCAT('Trùng lịch với lớp ', v_lhp_trung); LEAVE xu_ly; END IF;

    -- (2) Xử lý chậm
    CALL sp_log(v_log, 'INFO', CONCAT('Hợp lệ → xử lý ', p_tre, 's...'));
    DO SLEEP(p_tre);

    -- (3) GHI
    UPDATE lop_hoc_phan SET si_so_hien_tai = si_so_hien_tai + 1 WHERE ma_lhp = p_ma_lhp;
    INSERT INTO dang_ky (ma_sv, ma_lhp, ma_mh) VALUES (p_ma_sv, p_ma_lhp, v_ma_mh);
    CALL sp_log(v_log, 'WRITE', CONCAT('Chèn dang_ky (', p_ma_sv, ', ', p_ma_lhp, ')'));
  END xu_ly;

  IF v_kq = 'THANH_CONG' THEN COMMIT; CALL sp_log(v_log, 'COMMIT', v_tb);
  ELSE ROLLBACK; CALL sp_log(v_log, 'ROLLBACK', v_tb);
  END IF;
  SELECT v_kq AS ket_qua, v_tb AS thong_bao, v_loi AS ma_loi, v_log AS nhat_ky;
END $$

DROP PROCEDURE IF EXISTS sp_trung_lich_an_toan $$
CREATE PROCEDURE sp_trung_lich_an_toan(IN p_ma_sv VARCHAR(10), IN p_ma_lhp VARCHAR(15), IN p_tre DECIMAL(5,2))
BEGIN
  DECLARE v_log TEXT DEFAULT '';
  DECLARE v_kq VARCHAR(20) DEFAULT 'THANH_CONG';
  DECLARE v_tb VARCHAR(500) DEFAULT 'Đăng kí thành công';
  DECLARE v_loi INT DEFAULT NULL;
  DECLARE v_ma_mh VARCHAR(10);
  DECLARE v_lhp_trung VARCHAR(15);
  DECLARE v_tmp VARCHAR(10);
  DECLARE v_thu, v_bd, v_kt, v_dem INT;
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    GET DIAGNOSTICS CONDITION 1 v_loi = MYSQL_ERRNO, v_tb = MESSAGE_TEXT;
    ROLLBACK;
    CALL sp_log(v_log, 'ROLLBACK', CONCAT('Lỗi ', v_loi, ': ', v_tb));
    SELECT 'LOI' AS ket_qua, v_tb AS thong_bao, v_loi AS ma_loi, v_log AS nhat_ky;
  END;

  CALL sp_log(v_log, 'BEGIN', CONCAT(p_ma_sv, ' đăng kí ', p_ma_lhp));
  START TRANSACTION;
  xu_ly: BEGIN
    -- [SỬA] Khoá dòng SINH_VIEN ngay câu lệnh ĐẦU TIÊN.
    --   Hai giao dịch chèn 2 dòng KHÁC NHAU nên không có dòng chung để khoá;
    --   ta khoá "dòng cha" chung là sinh viên → giao dịch sau phải chờ giao dịch trước COMMIT.
    --   Đặt trước mọi SELECT thường vì ở REPEATABLE READ snapshot được chụp ở lần đọc thường đầu tiên.
    CALL sp_log(v_log, 'LOCK', CONCAT('SELECT ... FROM sinh_vien FOR UPDATE: xin khoá X dòng ', p_ma_sv));
    SELECT ma_sv INTO v_tmp FROM sinh_vien WHERE ma_sv = p_ma_sv FOR UPDATE;
    CALL sp_log(v_log, 'INFO', CONCAT('Được cấp khoá dòng ', p_ma_sv));

    SELECT ma_mh, thu, tiet_bd, tiet_kt INTO v_ma_mh, v_thu, v_bd, v_kt
    FROM lop_hoc_phan WHERE ma_lhp = p_ma_lhp;

    -- (1) ĐỌC: kiểm tra trùng lịch (giờ đã thấy dữ liệu giao dịch trước vừa COMMIT)
    SELECT COUNT(*), MIN(d.ma_lhp) INTO v_dem, v_lhp_trung
    FROM dang_ky d JOIN lop_hoc_phan l ON l.ma_lhp = d.ma_lhp
    WHERE d.ma_sv = p_ma_sv AND l.thu = v_thu AND l.tiet_bd <= v_kt AND v_bd <= l.tiet_kt;
    CALL sp_log(v_log, 'READ', CONCAT('Kiểm tra lịch Thứ ', v_thu, ' tiết ', v_bd, '-', v_kt, ': ',
                                      IF(v_dem = 0, 'không trùng', CONCAT('trùng ', v_lhp_trung))));
    IF v_dem > 0 THEN SET v_kq = 'TU_CHOI', v_tb = CONCAT('Trùng lịch với lớp ', v_lhp_trung); LEAVE xu_ly; END IF;

    -- (2) Xử lý chậm
    CALL sp_log(v_log, 'INFO', CONCAT('Hợp lệ → xử lý ', p_tre, 's...'));
    DO SLEEP(p_tre);

    -- (3) GHI
    UPDATE lop_hoc_phan SET si_so_hien_tai = si_so_hien_tai + 1 WHERE ma_lhp = p_ma_lhp;
    INSERT INTO dang_ky (ma_sv, ma_lhp, ma_mh) VALUES (p_ma_sv, p_ma_lhp, v_ma_mh);
    CALL sp_log(v_log, 'WRITE', CONCAT('Chèn dang_ky (', p_ma_sv, ', ', p_ma_lhp, ')'));
  END xu_ly;

  IF v_kq = 'THANH_CONG' THEN COMMIT; CALL sp_log(v_log, 'COMMIT', CONCAT(v_tb, ' — nhả khoá'));
  ELSE ROLLBACK; CALL sp_log(v_log, 'ROLLBACK', CONCAT(v_tb, ' — nhả khoá'));
  END IF;
  SELECT v_kq AS ket_qua, v_tb AS thong_bao, v_loi AS ma_loi, v_log AS nhat_ky;
END $$


-- =====================================================================
-- B3. KỊCH BẢN 3 — TRÙNG HỌC PHẦN (Phantom khi chèn)
--   1 SV cùng lúc đăng kí 2 lớp KHÁC NHAU của CÙNG 1 MÔN (không trùng giờ).
--   Mỗi giao dịch kiểm tra "chưa đăng kí môn này" rồi chèn → cả hai đều lọt.
-- =====================================================================
DROP PROCEDURE IF EXISTS sp_trung_hp_loi $$
CREATE PROCEDURE sp_trung_hp_loi(IN p_ma_sv VARCHAR(10), IN p_ma_lhp VARCHAR(15), IN p_tre DECIMAL(5,2))
BEGIN
  DECLARE v_log TEXT DEFAULT '';
  DECLARE v_kq VARCHAR(20) DEFAULT 'THANH_CONG';
  DECLARE v_tb VARCHAR(500) DEFAULT 'Đăng kí thành công';
  DECLARE v_loi INT DEFAULT NULL;
  DECLARE v_ma_mh VARCHAR(10);
  DECLARE v_lhp_trung VARCHAR(15);
  DECLARE v_dem INT;
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    GET DIAGNOSTICS CONDITION 1 v_loi = MYSQL_ERRNO, v_tb = MESSAGE_TEXT;
    ROLLBACK;
    CALL sp_log(v_log, 'ROLLBACK', CONCAT('Lỗi ', v_loi, ': ', v_tb));
    SELECT 'LOI' AS ket_qua, v_tb AS thong_bao, v_loi AS ma_loi, v_log AS nhat_ky;
  END;

  CALL sp_log(v_log, 'BEGIN', CONCAT(p_ma_sv, ' đăng kí ', p_ma_lhp));
  START TRANSACTION;
  xu_ly: BEGIN
    SELECT ma_mh INTO v_ma_mh FROM lop_hoc_phan WHERE ma_lhp = p_ma_lhp;

    -- (1) ĐỌC: đã đăng kí môn này chưa? (đọc snapshot, không khoá)
    SELECT COUNT(*), MIN(ma_lhp) INTO v_dem, v_lhp_trung
    FROM dang_ky WHERE ma_sv = p_ma_sv AND ma_mh = v_ma_mh;
    CALL sp_log(v_log, 'READ', CONCAT('Kiểm tra môn ', v_ma_mh, ': ',
                                      IF(v_dem = 0, 'chưa đăng kí', CONCAT('đã có lớp ', v_lhp_trung))));
    IF v_dem > 0 THEN
      SET v_kq = 'TU_CHOI', v_tb = CONCAT('Đã đăng kí môn ', v_ma_mh, ' ở lớp ', v_lhp_trung);
      LEAVE xu_ly;
    END IF;

    -- (2) Xử lý chậm
    CALL sp_log(v_log, 'INFO', CONCAT('Hợp lệ → xử lý ', p_tre, 's...'));
    DO SLEEP(p_tre);

    -- (3) GHI
    UPDATE lop_hoc_phan SET si_so_hien_tai = si_so_hien_tai + 1 WHERE ma_lhp = p_ma_lhp;
    INSERT INTO dang_ky (ma_sv, ma_lhp, ma_mh) VALUES (p_ma_sv, p_ma_lhp, v_ma_mh);
    CALL sp_log(v_log, 'WRITE', CONCAT('Chèn dang_ky (', p_ma_sv, ', ', p_ma_lhp, ', ', v_ma_mh, ')'));
  END xu_ly;

  IF v_kq = 'THANH_CONG' THEN COMMIT; CALL sp_log(v_log, 'COMMIT', v_tb);
  ELSE ROLLBACK; CALL sp_log(v_log, 'ROLLBACK', v_tb);
  END IF;
  SELECT v_kq AS ket_qua, v_tb AS thong_bao, v_loi AS ma_loi, v_log AS nhat_ky;
END $$

DROP PROCEDURE IF EXISTS sp_trung_hp_an_toan $$
CREATE PROCEDURE sp_trung_hp_an_toan(IN p_ma_sv VARCHAR(10), IN p_ma_lhp VARCHAR(15), IN p_tre DECIMAL(5,2))
BEGIN
  DECLARE v_log TEXT DEFAULT '';
  DECLARE v_kq VARCHAR(20) DEFAULT 'THANH_CONG';
  DECLARE v_tb VARCHAR(500) DEFAULT 'Đăng kí thành công';
  DECLARE v_loi INT DEFAULT NULL;
  DECLARE v_ma_mh VARCHAR(10);
  DECLARE v_lhp_trung VARCHAR(15);
  DECLARE v_dem INT;
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    GET DIAGNOSTICS CONDITION 1 v_loi = MYSQL_ERRNO, v_tb = MESSAGE_TEXT;
    ROLLBACK;
    CALL sp_log(v_log, 'ROLLBACK', CONCAT('Lỗi ', v_loi, ': ', v_tb));
    SELECT 'LOI' AS ket_qua, v_tb AS thong_bao, v_loi AS ma_loi, v_log AS nhat_ky;
  END;

  -- [SỬA] Mức cô lập SERIALIZABLE: InnoDB biến mọi SELECT thành SELECT ... FOR SHARE
  --   và khoá cả "khoảng trống" (gap/next-key lock) trên index (ma_sv, ma_mh).
  --   ⇒ Không giao dịch nào chèn được dòng rơi vào khoảng mà giao dịch kia đã đọc.
  --   Hai bên cùng giữ khoá S trên khoảng đó rồi cùng INSERT → DEADLOCK (1213):
  --   InnoDB huỷ 1 giao dịch, ứng dụng bắt lỗi 1213 và thử lại → lần sau thấy đã đăng kí.
  SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
  CALL sp_log(v_log, 'BEGIN', CONCAT(p_ma_sv, ' đăng kí ', p_ma_lhp, ' [SERIALIZABLE]'));
  START TRANSACTION;
  xu_ly: BEGIN
    SELECT ma_mh INTO v_ma_mh FROM lop_hoc_phan WHERE ma_lhp = p_ma_lhp;

    -- (1) ĐỌC: đã đăng kí môn này chưa? (ở SERIALIZABLE: giữ khoá S + gap lock)
    SELECT COUNT(*), MIN(ma_lhp) INTO v_dem, v_lhp_trung
    FROM dang_ky WHERE ma_sv = p_ma_sv AND ma_mh = v_ma_mh;
    CALL sp_log(v_log, 'READ', CONCAT('Kiểm tra môn ', v_ma_mh, ': ',
                                      IF(v_dem = 0, 'chưa đăng kí', CONCAT('đã có lớp ', v_lhp_trung)),
                                      ' (giữ khoá S trên khoảng ', p_ma_sv, '/', v_ma_mh, ')'));
    IF v_dem > 0 THEN
      SET v_kq = 'TU_CHOI', v_tb = CONCAT('Đã đăng kí môn ', v_ma_mh, ' ở lớp ', v_lhp_trung);
      LEAVE xu_ly;
    END IF;

    -- (2) Xử lý chậm
    CALL sp_log(v_log, 'INFO', CONCAT('Hợp lệ → xử lý ', p_tre, 's...'));
    DO SLEEP(p_tre);

    -- (3) GHI
    UPDATE lop_hoc_phan SET si_so_hien_tai = si_so_hien_tai + 1 WHERE ma_lhp = p_ma_lhp;
    CALL sp_log(v_log, 'LOCK', 'INSERT dang_ky: xin khoá chèn vào khoảng đã bị khoá S');
    INSERT INTO dang_ky (ma_sv, ma_lhp, ma_mh) VALUES (p_ma_sv, p_ma_lhp, v_ma_mh);
    CALL sp_log(v_log, 'WRITE', CONCAT('Chèn dang_ky (', p_ma_sv, ', ', p_ma_lhp, ', ', v_ma_mh, ')'));
  END xu_ly;

  IF v_kq = 'THANH_CONG' THEN COMMIT; CALL sp_log(v_log, 'COMMIT', v_tb);
  ELSE ROLLBACK; CALL sp_log(v_log, 'ROLLBACK', v_tb);
  END IF;
  SELECT v_kq AS ket_qua, v_tb AS thong_bao, v_loi AS ma_loi, v_log AS nhat_ky;
END $$


-- =====================================================================
-- B4. KỊCH BẢN 4 — ĐĂNG KÍ BỊ HUỶ GIỮA CHỪNG (Dirty read)
--   T1: SV A giữ chỗ cuối cùng (UPDATE + INSERT, chưa COMMIT) rồi mới kiểm tra
--       học phí → nợ học phí → ROLLBACK.
--   T2: SV B đăng kí cùng lớp trong lúc T1 chưa kết thúc.
-- =====================================================================
DROP PROCEDURE IF EXISTS sp_giu_cho_roi_huy $$
CREATE PROCEDURE sp_giu_cho_roi_huy(IN p_ma_sv VARCHAR(10), IN p_ma_lhp VARCHAR(15), IN p_tre DECIMAL(5,2))
BEGIN
  DECLARE v_log TEXT DEFAULT '';
  DECLARE v_kq VARCHAR(20) DEFAULT 'THANH_CONG';
  DECLARE v_tb VARCHAR(500) DEFAULT 'Đăng kí thành công';
  DECLARE v_loi INT DEFAULT NULL;
  DECLARE v_ma_mh VARCHAR(10);
  DECLARE v_si_so, v_toi_da, v_no INT;
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    GET DIAGNOSTICS CONDITION 1 v_loi = MYSQL_ERRNO, v_tb = MESSAGE_TEXT;
    ROLLBACK;
    CALL sp_log(v_log, 'ROLLBACK', CONCAT('Lỗi ', v_loi, ': ', v_tb));
    SELECT 'LOI' AS ket_qua, v_tb AS thong_bao, v_loi AS ma_loi, v_log AS nhat_ky;
  END;

  CALL sp_log(v_log, 'BEGIN', CONCAT(p_ma_sv, ' đăng kí ', p_ma_lhp));
  START TRANSACTION;
  xu_ly: BEGIN
    SELECT ma_mh, si_so_hien_tai, si_so_toi_da INTO v_ma_mh, v_si_so, v_toi_da
    FROM lop_hoc_phan WHERE ma_lhp = p_ma_lhp FOR UPDATE;
    IF v_si_so >= v_toi_da THEN SET v_kq = 'TU_CHOI', v_tb = 'Lớp đã đủ sĩ số'; LEAVE xu_ly; END IF;

    -- Giữ chỗ trước
    UPDATE lop_hoc_phan SET si_so_hien_tai = si_so_hien_tai + 1 WHERE ma_lhp = p_ma_lhp;
    INSERT INTO dang_ky (ma_sv, ma_lhp, ma_mh) VALUES (p_ma_sv, p_ma_lhp, v_ma_mh);
    CALL sp_log(v_log, 'WRITE', CONCAT('Giữ chỗ: sĩ số ', v_si_so, ' → ', v_si_so + 1, '/', v_toi_da, ' (CHƯA COMMIT)'));

    -- Kiểm tra học phí (giả lập gọi hệ thống khác, mất p_tre giây)
    CALL sp_log(v_log, 'INFO', CONCAT('Kiểm tra học phí ', p_tre, 's...'));
    DO SLEEP(p_tre);
    SELECT no_hoc_phi INTO v_no FROM sinh_vien WHERE ma_sv = p_ma_sv;
    IF v_no THEN SET v_kq = 'TU_CHOI', v_tb = 'Còn nợ học phí → huỷ giao dịch, trả lại chỗ'; LEAVE xu_ly; END IF;
  END xu_ly;

  IF v_kq = 'THANH_CONG' THEN COMMIT; CALL sp_log(v_log, 'COMMIT', v_tb);
  ELSE ROLLBACK; CALL sp_log(v_log, 'ROLLBACK', v_tb);
  END IF;
  SELECT v_kq AS ket_qua, v_tb AS thong_bao, v_loi AS ma_loi, v_log AS nhat_ky;
END $$

DROP PROCEDURE IF EXISTS sp_dirty_read_loi $$
CREATE PROCEDURE sp_dirty_read_loi(IN p_ma_sv VARCHAR(10), IN p_ma_lhp VARCHAR(15))
BEGIN
  DECLARE v_log TEXT DEFAULT '';
  DECLARE v_kq VARCHAR(20) DEFAULT 'THANH_CONG';
  DECLARE v_tb VARCHAR(500) DEFAULT 'Đăng kí thành công';
  DECLARE v_loi INT DEFAULT NULL;
  DECLARE v_ma_mh VARCHAR(10);
  DECLARE v_si_so, v_toi_da, v_n INT;
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    GET DIAGNOSTICS CONDITION 1 v_loi = MYSQL_ERRNO, v_tb = MESSAGE_TEXT;
    ROLLBACK;
    CALL sp_log(v_log, 'ROLLBACK', CONCAT('Lỗi ', v_loi, ': ', v_tb));
    SELECT 'LOI' AS ket_qua, v_tb AS thong_bao, v_loi AS ma_loi, v_log AS nhat_ky;
  END;

  -- Mức cô lập thấp nhất: được phép đọc dữ liệu CHƯA COMMIT của giao dịch khác
  SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
  CALL sp_log(v_log, 'BEGIN', CONCAT(p_ma_sv, ' đăng kí ', p_ma_lhp, ' [READ UNCOMMITTED]'));
  START TRANSACTION;
  xu_ly: BEGIN
    SELECT ma_mh, si_so_hien_tai, si_so_toi_da INTO v_ma_mh, v_si_so, v_toi_da
    FROM lop_hoc_phan WHERE ma_lhp = p_ma_lhp;
    CALL sp_log(v_log, 'READ', CONCAT('Đọc sĩ số ', p_ma_lhp, ' = ', v_si_so, '/', v_toi_da));
    IF v_si_so >= v_toi_da THEN SET v_kq = 'TU_CHOI', v_tb = 'Lớp đã đủ sĩ số'; LEAVE xu_ly; END IF;

    UPDATE lop_hoc_phan SET si_so_hien_tai = si_so_hien_tai + 1
    WHERE ma_lhp = p_ma_lhp AND si_so_hien_tai < si_so_toi_da;
    SET v_n = ROW_COUNT();
    IF v_n = 0 THEN SET v_kq = 'TU_CHOI', v_tb = 'Lớp vừa hết chỗ'; LEAVE xu_ly; END IF;
    INSERT INTO dang_ky (ma_sv, ma_lhp, ma_mh) VALUES (p_ma_sv, p_ma_lhp, v_ma_mh);
    CALL sp_log(v_log, 'WRITE', CONCAT('Ghi dang_ky (', p_ma_sv, ', ', p_ma_lhp, ')'));
  END xu_ly;

  IF v_kq = 'THANH_CONG' THEN COMMIT; CALL sp_log(v_log, 'COMMIT', v_tb);
  ELSE ROLLBACK; CALL sp_log(v_log, 'ROLLBACK', v_tb);
  END IF;
  SELECT v_kq AS ket_qua, v_tb AS thong_bao, v_loi AS ma_loi, v_log AS nhat_ky;
END $$

DROP PROCEDURE IF EXISTS sp_dirty_read_an_toan $$
CREATE PROCEDURE sp_dirty_read_an_toan(IN p_ma_sv VARCHAR(10), IN p_ma_lhp VARCHAR(15))
BEGIN
  DECLARE v_log TEXT DEFAULT '';
  DECLARE v_kq VARCHAR(20) DEFAULT 'THANH_CONG';
  DECLARE v_tb VARCHAR(500) DEFAULT 'Đăng kí thành công';
  DECLARE v_loi INT DEFAULT NULL;
  DECLARE v_ma_mh VARCHAR(10);
  DECLARE v_si_so, v_toi_da, v_n INT;
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    GET DIAGNOSTICS CONDITION 1 v_loi = MYSQL_ERRNO, v_tb = MESSAGE_TEXT;
    ROLLBACK;
    CALL sp_log(v_log, 'ROLLBACK', CONCAT('Lỗi ', v_loi, ': ', v_tb));
    SELECT 'LOI' AS ket_qua, v_tb AS thong_bao, v_loi AS ma_loi, v_log AS nhat_ky;
  END;

  -- [SỬA] READ COMMITTED (hoặc mặc định REPEATABLE READ): chỉ đọc dữ liệu ĐÃ COMMIT.
  SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
  CALL sp_log(v_log, 'BEGIN', CONCAT(p_ma_sv, ' đăng kí ', p_ma_lhp, ' [READ COMMITTED]'));
  START TRANSACTION;
  xu_ly: BEGIN
    SELECT ma_mh, si_so_hien_tai, si_so_toi_da INTO v_ma_mh, v_si_so, v_toi_da
    FROM lop_hoc_phan WHERE ma_lhp = p_ma_lhp;
    CALL sp_log(v_log, 'READ', CONCAT('Đọc sĩ số ', p_ma_lhp, ' = ', v_si_so, '/', v_toi_da, ' (bản đã COMMIT)'));
    IF v_si_so >= v_toi_da THEN SET v_kq = 'TU_CHOI', v_tb = 'Lớp đã đủ sĩ số'; LEAVE xu_ly; END IF;

    -- UPDATE có điều kiện: chờ khoá X của T1; khi T1 kết thúc mới kiểm tra lại điều kiện
    CALL sp_log(v_log, 'LOCK', 'UPDATE ... WHERE si_so_hien_tai < si_so_toi_da: xin khoá X');
    UPDATE lop_hoc_phan SET si_so_hien_tai = si_so_hien_tai + 1
    WHERE ma_lhp = p_ma_lhp AND si_so_hien_tai < si_so_toi_da;
    SET v_n = ROW_COUNT();
    IF v_n = 0 THEN SET v_kq = 'TU_CHOI', v_tb = 'Lớp đã đủ sĩ số (người trước đã COMMIT)'; LEAVE xu_ly; END IF;
    INSERT INTO dang_ky (ma_sv, ma_lhp, ma_mh) VALUES (p_ma_sv, p_ma_lhp, v_ma_mh);
    CALL sp_log(v_log, 'WRITE', CONCAT('Ghi dang_ky (', p_ma_sv, ', ', p_ma_lhp, ')'));
  END xu_ly;

  IF v_kq = 'THANH_CONG' THEN COMMIT; CALL sp_log(v_log, 'COMMIT', v_tb);
  ELSE ROLLBACK; CALL sp_log(v_log, 'ROLLBACK', v_tb);
  END IF;
  SELECT v_kq AS ket_qua, v_tb AS thong_bao, v_loi AS ma_loi, v_log AS nhat_ky;
END $$


-- =====================================================================
-- C. ĐẶT LẠI DỮ LIỆU CỦA TỪNG KỊCH BẢN
--   KB1: lớp HQT.03 (tối đa 2 chỗ), SV11..SV15
--   KB2: SV16 — CSDL.01 (T2 tiết 1-3) và CTDL.01 (T2 tiết 2-4)
--   KB3: SV17 — HQT.01 và HQT.02 (cùng môn HQT)
--   KB4: lớp KTCT.02 (tối đa 1 chỗ), SV18 (nợ học phí), SV19
-- =====================================================================
DROP PROCEDURE IF EXISTS sp_dat_lai_kich_ban $$
CREATE PROCEDURE sp_dat_lai_kich_ban(IN p_kb TINYINT)
BEGIN
  DECLARE v_ds_sv  VARCHAR(200) DEFAULT '';
  DECLARE v_ds_lhp VARCHAR(200) DEFAULT '';

  CASE p_kb
    WHEN 1 THEN SET v_ds_sv = 'SV11,SV12,SV13,SV14,SV15', v_ds_lhp = 'HQT.03';
    WHEN 2 THEN SET v_ds_sv = 'SV16';
    WHEN 3 THEN SET v_ds_sv = 'SV17';
    WHEN 4 THEN SET v_ds_sv = 'SV18,SV19', v_ds_lhp = 'KTCT.02';
    ELSE SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Kịch bản không hợp lệ (1..4)';
  END CASE;

  SET @safe_cu = @@SESSION.SQL_SAFE_UPDATES;
  SET SESSION SQL_SAFE_UPDATES = 0;
  DROP TEMPORARY TABLE IF EXISTS tmp_lop;
  CREATE TEMPORARY TABLE tmp_lop (ma_lhp VARCHAR(15) PRIMARY KEY);

  START TRANSACTION;
  INSERT IGNORE INTO tmp_lop
    SELECT DISTINCT ma_lhp FROM dang_ky
    WHERE FIND_IN_SET(ma_sv, v_ds_sv) > 0 OR FIND_IN_SET(ma_lhp, v_ds_lhp) > 0;
  INSERT IGNORE INTO tmp_lop SELECT ma_lhp FROM lop_hoc_phan WHERE FIND_IN_SET(ma_lhp, v_ds_lhp) > 0;

  DELETE FROM dang_ky WHERE FIND_IN_SET(ma_sv, v_ds_sv) > 0 OR FIND_IN_SET(ma_lhp, v_ds_lhp) > 0;

  UPDATE lop_hoc_phan l JOIN tmp_lop t ON t.ma_lhp = l.ma_lhp
  SET l.si_so_hien_tai = (SELECT COUNT(*) FROM dang_ky d WHERE d.ma_lhp = l.ma_lhp);

  IF p_kb = 1 THEN UPDATE lop_hoc_phan SET si_so_toi_da = 2 WHERE ma_lhp = 'HQT.03'; END IF;
  IF p_kb = 4 THEN
    UPDATE lop_hoc_phan SET si_so_toi_da = 1 WHERE ma_lhp = 'KTCT.02';
    UPDATE sinh_vien SET no_hoc_phi = (ma_sv = 'SV18') WHERE ma_sv IN ('SV18', 'SV19');
  END IF;
  COMMIT;

  DROP TEMPORARY TABLE tmp_lop;
  SET SESSION SQL_SAFE_UPDATES = @safe_cu;
END $$

DELIMITER ;
