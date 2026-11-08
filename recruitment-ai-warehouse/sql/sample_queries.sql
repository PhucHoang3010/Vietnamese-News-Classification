-- =====================================================================
-- Truy vấn mẫu trên kho dữ liệu tuyển dụng TalentLens (PostgreSQL)
-- =====================================================================

-- Q1. Phễu tuyển dụng: số hồ sơ đã đi tới từng vòng và tỷ lệ so với số nộp
SELECT s.stage_order, s.name AS vong,
       COUNT(DISTINCT e.application_id) AS so_ho_so,
       ROUND(100.0 * COUNT(DISTINCT e.application_id) /
             (SELECT COUNT(*) FROM fact_application), 1) AS pct_so_voi_nop
FROM fact_stage_event e
JOIN dim_stage s ON s.id = e.stage_id
GROUP BY s.stage_order, s.name
ORDER BY s.stage_order;

-- Q2. Tỷ lệ chuyển đổi giữa hai vòng liên tiếp (window function LEAD)
WITH reached AS (
    SELECT s.stage_order, s.name, COUNT(DISTINCT e.application_id) AS n
    FROM fact_stage_event e JOIN dim_stage s ON s.id = e.stage_id
    GROUP BY s.stage_order, s.name
)
SELECT name AS tu_vong,
       LEAD(name) OVER (ORDER BY stage_order) AS den_vong,
       n, LEAD(n) OVER (ORDER BY stage_order) AS n_tiep,
       ROUND(100.0 * LEAD(n) OVER (ORDER BY stage_order) / n, 1) AS ty_le_chuyen_doi
FROM reached
ORDER BY stage_order;

-- Q3. Thời gian chuyển vòng (trung vị, P90) và % vượt SLA – phát hiện điểm nghẽn
SELECT s.name AS vong, s.sla_days,
       COUNT(*) AS so_ho_so_di_tiep,
       ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY e.duration_hours) / 24)::numeric, 1) AS trung_vi_ngay,
       ROUND((PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY e.duration_hours) / 24)::numeric, 1) AS p90_ngay,
       ROUND(100.0 * AVG(CASE WHEN e.duration_hours / 24 > s.sla_days THEN 1 ELSE 0 END), 1) AS pct_vuot_sla
FROM fact_stage_event e
JOIN dim_stage s ON s.id = e.stage_id
WHERE e.outcome = 'passed' AND e.duration_hours IS NOT NULL AND NOT s.is_terminal
GROUP BY s.stage_order, s.name, s.sla_days
ORDER BY trung_vi_ngay DESC;

-- Q4. Hiệu quả nguồn tuyển dụng: số hồ sơ, tỷ lệ tuyển, thời gian tuyển trung bình
SELECT so.name AS nguon,
       COUNT(*) AS so_ho_so,
       SUM(CASE WHEN a.status = 'hired' THEN 1 ELSE 0 END) AS nhan_viec,
       ROUND(100.0 * AVG(CASE WHEN a.status = 'hired' THEN 1 ELSE 0 END), 1) AS ty_le_tuyen,
       ROUND(AVG(EXTRACT(EPOCH FROM (a.closed_at - a.applied_at)) / 86400)
             FILTER (WHERE a.status = 'hired')::numeric, 1) AS tg_tuyen_tb_ngay
FROM fact_application a
JOIN dim_source so ON so.id = a.source_id
GROUP BY so.name
ORDER BY so_ho_so DESC;

-- Q5. Hồ sơ mới theo tuần (dùng bảng chiều thời gian dim_date)
SELECT d.week_start, COUNT(*) AS ho_so_moi
FROM fact_application a
JOIN dim_date d ON d.date_key = a.applied_date_key
GROUP BY d.week_start
ORDER BY d.week_start;

-- Q6. Lý do loại / rút hồ sơ phổ biến theo vòng (đã phân loại bằng NLP)
SELECT s.name AS vong, a.rejection_category AS nhom_ly_do, COUNT(*) AS so_ho_so
FROM fact_application a
JOIN dim_stage s ON s.id = a.current_stage_id
WHERE a.status IN ('rejected', 'withdrawn')
GROUP BY s.stage_order, s.name, a.rejection_category
ORDER BY s.stage_order, so_ho_so DESC;

-- Q7. Kiểm tra khử trùng: không có email trùng trong dim_candidate
SELECT email, COUNT(*) FROM dim_candidate
WHERE email IS NOT NULL
GROUP BY email HAVING COUNT(*) > 1;

-- Q8. Ứng viên được gộp từ nhiều nguồn (lineage) và số hồ sơ theo hệ nguồn
SELECT c.candidate_code, c.full_name, jsonb_array_length(c.merged_identities) AS so_ban_ghi_gop,
       a.source_systems
FROM dim_candidate c
JOIN fact_application a ON a.candidate_id = c.id
WHERE jsonb_array_length(c.merged_identities) >= 2
ORDER BY so_ban_ghi_gop DESC
LIMIT 10;

-- Q9. Hồ sơ đang xử lý quá SLA ở vòng hiện tại
SELECT a.application_code, p.title AS vi_tri, s.name AS vong,
       ROUND((EXTRACT(EPOCH FROM (NOW() - e.entered_at)) / 86400)::numeric, 1) AS so_ngay, s.sla_days
FROM fact_application a
JOIN fact_stage_event e ON e.application_id = a.id AND e.stage_id = a.current_stage_id
JOIN dim_stage s ON s.id = a.current_stage_id
JOIN dim_position p ON p.id = a.position_id
WHERE a.status = 'active' AND NOW() - e.entered_at > s.sla_days * INTERVAL '1 day'
ORDER BY so_ngay DESC;

-- Q10. Pipeline theo phòng ban và vị trí (đang xử lý / đã tuyển / chỉ tiêu)
SELECT dp.name AS phong_ban, p.title AS vi_tri, p.headcount AS chi_tieu,
       COUNT(*) AS ho_so,
       SUM(CASE WHEN a.status = 'active' THEN 1 ELSE 0 END) AS dang_xu_ly,
       SUM(CASE WHEN a.status = 'hired' THEN 1 ELSE 0 END) AS da_tuyen
FROM fact_application a
JOIN dim_position p ON p.id = a.position_id
JOIN dim_department dp ON dp.id = p.department_id
GROUP BY dp.name, p.title, p.headcount
ORDER BY dp.name, ho_so DESC;
