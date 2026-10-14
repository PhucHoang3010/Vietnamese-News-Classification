"""Chuẩn hóa dữ liệu ứng viên và tạo kho dữ liệu (Nhóm 8 - Đề tài AI 9 - Task 2).

Các bước:
  1. Đọc file hồ sơ tổng hợp (mỗi người nhập một kiểu)
  2. Chuẩn hóa từng thông tin theo quy tắc chung
  3. Tạo 6 bảng từ file kho_du_lieu.sql
  4. Lưu dữ liệu vào các bảng
  5. In báo cáo, rồi thử lưu dữ liệu sai để xem cơ sở dữ liệu có chặn không

Bản chạy thử dùng SQLite (có sẵn trong Python, không cần cài).
File kho_du_lieu.sql viết theo SQL chuẩn nên chạy được cả trên PostgreSQL.

Cách chạy:
  pip install pandas
  python tao_kho_du_lieu.py
"""
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

THU_MUC = Path(__file__).parent

# ---------------------------------------------------------------- DANH MỤC
# Mỗi giá trị chuẩn đi kèm các cách ghi khác hay gặp (viết thường hết).
VI_TRI = {
    "Data Analyst": ["da", "phân tích dữ liệu"],
    "Lập trình viên Python": ["python developer", "dev python", "lập trình python"],
    "Lập trình viên Web": ["web developer", "frontend", "lập trình web"],
    "Nhân viên HR": ["hr", "nhân sự", "nhân viên nhân sự"],
}
PHONG_BAN = {
    "Data Analyst": "Phòng Dữ liệu",
    "Lập trình viên Python": "Phòng Kỹ thuật",
    "Lập trình viên Web": "Phòng Kỹ thuật",
    "Nhân viên HR": "Phòng Nhân sự",
}
NGUON = {
    "TopCV": ["topcv.vn", "top cv"],
    "VietnamWorks": ["vietnamworks.com", "vnw"],
    "Google Form": ["gg form", "form"],
    "Giới thiệu": ["nhân viên giới thiệu", "referral"],
}
# Thứ tự trong VONG chính là thứ tự các vòng: 1 = Nộp hồ sơ ... 5 = Nhận việc
VONG = {
    "Nộp hồ sơ": ["new", "mới nộp", "nộp hs"],
    "Sàng lọc": ["screening", "lọc cv"],
    "Phỏng vấn": ["interview", "pv", "vòng pv"],
    "Đề nghị": ["offer", "gửi offer"],
    "Nhận việc": ["hired", "đi làm"],
}
TRANG_THAI = {
    "Đang xử lý": ["đang chờ", "pending", ""],   # để trống = chưa có kết quả
    "Đạt": ["pass", "đậu"],
    "Không đạt": ["trượt", "rớt", "fail"],
    "Rút hồ sơ": ["từ chối", "withdrawn"],
}


# ------------------------------------------------------- QUY TẮC CHUẨN HÓA
def tra_danh_muc(gia_tri, danh_muc):
    """Đổi một cách ghi bất kỳ về giá trị chuẩn. Không nhận ra thì trả về None."""
    gia_tri = gia_tri.strip().lower()
    for chuan, cach_ghi_khac in danh_muc.items():
        if gia_tri == chuan.lower() or gia_tri in cach_ghi_khac:
            return chuan
    return None


def chuan_hoa_ten(ten):
    """'  trần  văn AN ' -> 'Trần Văn An'"""
    return " ".join(ten.split()).title()


def chuan_hoa_sdt(sdt):
    """'+84 906 609 544' hoặc '0906.609.544' -> '0906609544'"""
    chi_so = "".join(c for c in sdt if c.isdigit())
    if chi_so.startswith("84"):
        chi_so = "0" + chi_so[2:]
    return chi_so


def chuan_hoa_ngay(chuoi):
    """'15/06/2026' hoặc '2026-06-15' -> '2026-06-15' (năm-tháng-ngày)"""
    if "/" in chuoi:
        return datetime.strptime(chuoi, "%d/%m/%Y").date().isoformat()
    return datetime.strptime(chuoi, "%Y-%m-%d").date().isoformat()


def doc_va_chuan_hoa():
    tho = pd.read_csv(THU_MUC / "du_lieu_mau" / "ho_so_tong_hop.csv",
                      dtype=str, keep_default_na=False)
    thong_ke = {
        "Số dòng đọc vào": len(tho),
        "Cách ghi vị trí khác nhau": tho["Vị trí"].nunique(),
        "Cách ghi vòng khác nhau": tho["Vòng"].nunique(),
        "Cách ghi kết quả khác nhau": tho["Kết quả"].nunique(),
    }

    df = pd.DataFrame({
        "ho_ten": tho["Họ tên"].apply(chuan_hoa_ten),
        "email": tho["Email"].str.strip().str.lower(),
        "so_dien_thoai": tho["SĐT"].apply(chuan_hoa_sdt),
        "vi_tri": tho["Vị trí"].apply(tra_danh_muc, danh_muc=VI_TRI),
        "nguon": tho["Nguồn"].apply(tra_danh_muc, danh_muc=NGUON),
        "vong": tho["Vòng"].apply(tra_danh_muc, danh_muc=VONG),
        "trang_thai": tho["Kết quả"].apply(tra_danh_muc, danh_muc=TRANG_THAI),
        "ngay_nop": tho["Ngày nộp"].apply(chuan_hoa_ngay),
        "ngay_cap_nhat": tho["Ngày cập nhật"].apply(chuan_hoa_ngay),
    })

    # Dòng có email sai hoặc giá trị không có trong danh mục -> để HR kiểm tra lại
    hop_le = df["email"].str.contains("@") & df[["vi_tri", "nguon", "vong", "trang_thai"]].notna().all(axis=1)
    tho[~hop_le].to_csv(THU_MUC / "can_kiem_tra.csv", index=False, encoding="utf-8-sig")
    thong_ke["Dòng lỗi (gửi HR kiểm tra)"] = int((~hop_le).sum())
    df = df[hop_le]

    # Trùng: cùng email + cùng vị trí -> giữ bản cập nhật mới nhất
    so_dong_truoc = len(df)
    df = df.sort_values("ngay_cap_nhat").drop_duplicates(["email", "vi_tri"], keep="last")
    thong_ke["Hồ sơ trùng bị bỏ"] = so_dong_truoc - len(df)
    return df, thong_ke


# ------------------------------------------------------------ TẠO KHO DỮ LIỆU
def tao_kho(df):
    duong_dan = THU_MUC / "kho_tuyen_dung.db"
    duong_dan.unlink(missing_ok=True)           # chạy lại thì tạo kho mới từ đầu
    ket_noi = sqlite3.connect(duong_dan)
    ket_noi.execute("PRAGMA foreign_keys = ON")  # SQLite cần bật để kiểm tra khóa ngoại
    ket_noi.executescript((THU_MUC / "kho_du_lieu.sql").read_text(encoding="utf-8"))

    # 1. Bảng thông tin: mã = số thứ tự trong danh mục
    ma_vi_tri = {ten: i for i, ten in enumerate(VI_TRI, start=1)}
    ma_nguon = {ten: i for i, ten in enumerate(NGUON, start=1)}
    ma_vong = {ten: i for i, ten in enumerate(VONG, start=1)}
    ma_trang_thai = {ten: i for i, ten in enumerate(TRANG_THAI, start=1)}
    for ten, ma in ma_vi_tri.items():
        ket_noi.execute("INSERT INTO vi_tri VALUES (?, ?, ?)", (ma, ten, PHONG_BAN[ten]))
    for ten, ma in ma_nguon.items():
        ket_noi.execute("INSERT INTO nguon VALUES (?, ?)", (ma, ten))
    for ten, ma in ma_vong.items():
        ket_noi.execute("INSERT INTO vong_tuyen VALUES (?, ?, ?)", (ma, ten, ma))
    for ten, ma in ma_trang_thai.items():
        ket_noi.execute("INSERT INTO trang_thai VALUES (?, ?)", (ma, ten))

    # 2. Bảng ứng viên: mỗi email một dòng
    ma_ung_vien = {}
    for ma, dong in enumerate(df.drop_duplicates("email").itertuples(), start=1):
        ket_noi.execute("INSERT INTO ung_vien VALUES (?, ?, ?, ?)",
                        (ma, dong.ho_ten, dong.email, dong.so_dien_thoai))
        ma_ung_vien[dong.email] = ma

    # 3. Bảng chính: chỉ lưu mã, không lưu lặp tên vị trí, nguồn...
    for ma, dong in enumerate(df.itertuples(), start=1):
        ket_noi.execute(
            "INSERT INTO ho_so_ung_tuyen VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (ma, ma_ung_vien[dong.email], ma_vi_tri[dong.vi_tri], ma_nguon[dong.nguon],
             ma_vong[dong.vong], ma_trang_thai[dong.trang_thai],
             dong.ngay_nop, dong.ngay_cap_nhat, None))   # diem_ai: phần AI điền sau
    ket_noi.commit()
    return ket_noi


# ------------------------------------------------------------------ BÁO CÁO
def bao_cao(ket_noi, thong_ke):
    print("=== CHUẨN HÓA ===")
    for ten, so in thong_ke.items():
        print(f"{ten:<28}: {so}")

    print("\n=== SỐ DÒNG TRONG MỖI BẢNG ===")
    for bang in ["ung_vien", "vi_tri", "nguon", "vong_tuyen", "trang_thai", "ho_so_ung_tuyen"]:
        so = ket_noi.execute(f"SELECT COUNT(*) FROM {bang}").fetchone()[0]
        print(f"{bang:<16}: {so}")

    print("\n=== SỐ ỨNG VIÊN KHÔNG ĐẠT Ở MỖI VÒNG ===")
    khong_dat = ket_noi.execute("""
        SELECT v.ten_vong, COUNT(*)
        FROM ho_so_ung_tuyen h
        JOIN vong_tuyen v ON v.ma_vong = h.ma_vong
        JOIN trang_thai t ON t.ma_trang_thai = h.ma_trang_thai
        WHERE t.ten_trang_thai = 'Không đạt'
        GROUP BY v.thu_tu, v.ten_vong
        ORDER BY v.thu_tu
    """).fetchall()
    for ten_vong, so in khong_dat:
        print(f"{ten_vong:<10}: {so}")

    nhan_viec = pd.read_sql("""
        SELECT h.ngay_nop, h.ngay_cap_nhat
        FROM ho_so_ung_tuyen h JOIN vong_tuyen v ON v.ma_vong = h.ma_vong
        WHERE v.ten_vong = 'Nhận việc'
    """, ket_noi, parse_dates=["ngay_nop", "ngay_cap_nhat"])
    so_ngay = (nhan_viec["ngay_cap_nhat"] - nhan_viec["ngay_nop"]).dt.days.mean()
    print(f"\nThời gian tuyển trung bình: {so_ngay:.0f} ngày ({len(nhan_viec)} người nhận việc)")


def thu_du_lieu_sai(ket_noi):
    """Thử lưu 3 dữ liệu sai: cơ sở dữ liệu phải từ chối cả 3."""
    email_da_co = ket_noi.execute("SELECT email FROM ung_vien LIMIT 1").fetchone()[0]
    cac_lan_thu = [
        ("Email bị trùng", "INSERT INTO ung_vien VALUES (9999, 'Người Thử', ?, NULL)", (email_da_co,)),
        ("Điểm AI = 150", "UPDATE ho_so_ung_tuyen SET diem_ai = 150 WHERE ma_ho_so = 1", ()),
        ("Vòng số 9 (không có)", "UPDATE ho_so_ung_tuyen SET ma_vong = 9 WHERE ma_ho_so = 1", ()),
    ]
    print("\n=== THỬ LƯU DỮ LIỆU SAI ===")
    for ten, cau_lenh, tham_so in cac_lan_thu:
        try:
            ket_noi.execute(cau_lenh, tham_so)
            print(f"{ten:<22}: KHÔNG bị chặn -> cần xem lại ràng buộc")
        except sqlite3.IntegrityError as loi:
            print(f"{ten:<22}: bị chặn ({loi})")
    ket_noi.rollback()


if __name__ == "__main__":
    du_lieu, thong_ke = doc_va_chuan_hoa()
    ket_noi = tao_kho(du_lieu)
    bao_cao(ket_noi, thong_ke)
    thu_du_lieu_sai(ket_noi)
    ket_noi.close()
