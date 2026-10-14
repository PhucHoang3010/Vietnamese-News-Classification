-- Kho dữ liệu tuyển dụng - Nhóm 8 - Đề tài AI 9 - Task 2
-- Viết theo SQL chuẩn: chạy được trên cả PostgreSQL và SQLite.
-- PK = khóa chính (mã riêng của mỗi dòng), FK = khóa ngoại (mã nối sang bảng khác).

-- ===== 5 BẢNG THÔNG TIN (xung quanh) =====

CREATE TABLE ung_vien (
    ma_ung_vien   INTEGER PRIMARY KEY,
    ho_ten        VARCHAR(100) NOT NULL,
    email         VARCHAR(100) NOT NULL UNIQUE,   -- một email chỉ thuộc một ứng viên
    so_dien_thoai CHAR(10)                        -- đúng 10 số, bắt đầu bằng 0
);

CREATE TABLE vi_tri (
    ma_vi_tri  INTEGER PRIMARY KEY,
    ten_vi_tri VARCHAR(100) NOT NULL UNIQUE,
    phong_ban  VARCHAR(100)
);

CREATE TABLE nguon (
    ma_nguon  INTEGER PRIMARY KEY,
    ten_nguon VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE vong_tuyen (
    ma_vong  INTEGER PRIMARY KEY,
    ten_vong VARCHAR(50) NOT NULL UNIQUE,
    thu_tu   INTEGER NOT NULL                     -- 1 = Nộp hồ sơ ... 5 = Nhận việc
);

CREATE TABLE trang_thai (
    ma_trang_thai  INTEGER PRIMARY KEY,
    ten_trang_thai VARCHAR(50) NOT NULL UNIQUE
);

-- ===== BẢNG CHÍNH: mỗi dòng là một lần nộp hồ sơ =====

CREATE TABLE ho_so_ung_tuyen (
    ma_ho_so      INTEGER PRIMARY KEY,
    ma_ung_vien   INTEGER NOT NULL REFERENCES ung_vien,
    ma_vi_tri     INTEGER NOT NULL REFERENCES vi_tri,
    ma_nguon      INTEGER NOT NULL REFERENCES nguon,
    ma_vong       INTEGER NOT NULL REFERENCES vong_tuyen,
    ma_trang_thai INTEGER NOT NULL REFERENCES trang_thai,
    ngay_nop      DATE NOT NULL,
    ngay_cap_nhat DATE,
    diem_ai       NUMERIC(5,2)                    -- phần AI của nhóm sẽ điền
                  CHECK (diem_ai BETWEEN 0 AND 100),
    UNIQUE (ma_ung_vien, ma_vi_tri)               -- mỗi người nộp 1 vị trí 1 lần
);
