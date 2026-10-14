"""ETL mẫu cho kho dữ liệu tuyển dụng (Nhóm 8 - Đề tài AI 9 - Task 1).

ETL gồm 3 bước:
  E - Extract  : lấy dữ liệu từ 3 nguồn trong thư mục du_lieu_mau/
  T - Transform: làm sạch, đưa về cùng một mẫu, xóa hồ sơ trùng
  L - Load     : lưu dữ liệu sạch vào cơ sở dữ liệu

Bản chạy thử lưu vào SQLite (có sẵn trong Python, không cần cài).
Khi triển khai thật, nhóm đổi sang PostgreSQL.

Cách chạy:
  pip install pandas
  python etl_demo.py
"""
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

THU_MUC = Path(__file__).parent

# Mỗi nguồn đặt tên cột khác nhau -> đổi về cùng một tên
DOI_TEN_COT = {
    "Họ tên": "ho_ten", "Tên ứng viên": "ho_ten", "full_name": "ho_ten",
    "Email": "email", "Email liên hệ": "email",
    "SĐT": "sdt", "Số điện thoại": "sdt", "phone": "sdt",
    "Vị trí": "vi_tri", "Vị trí ứng tuyển": "vi_tri", "job_title": "vi_tri",
    "Ngày nộp": "ngay_nop", "Dấu thời gian": "ngay_nop", "applied_at": "ngay_nop",
    "Trạng thái": "vong", "status": "vong",
}

# Mỗi nguồn ghi trạng thái một kiểu -> đổi về các vòng chuẩn
DOI_TEN_VONG = {
    "nộp hồ sơ": "Nộp hồ sơ", "new": "Nộp hồ sơ",
    "sàng lọc": "Sàng lọc", "screening": "Sàng lọc",
    "phỏng vấn": "Phỏng vấn", "interview": "Phỏng vấn",
    "đề nghị": "Đề nghị", "offer": "Đề nghị",
    "nhận việc": "Nhận việc", "hired": "Nhận việc",
    "loại": "Bị loại", "rejected": "Bị loại",
}
CAC_VONG = ["Nộp hồ sơ", "Sàng lọc", "Phỏng vấn", "Đề nghị", "Nhận việc"]


# ---------------------------------------------------------------- E: EXTRACT
def extract():
    """Đọc 3 nguồn rồi ghép thành một bảng."""
    hr = pd.read_csv(THU_MUC / "du_lieu_mau" / "file_hr.csv", dtype=str)
    web = pd.read_json(THU_MUC / "du_lieu_mau" / "web_tuyen_dung.json", dtype=str,
                       convert_dates=False)
    form = pd.read_csv(THU_MUC / "du_lieu_mau" / "google_form.csv", dtype=str)

    hr["nguon"] = "File HR"
    web["nguon"] = "Web tuyển dụng"
    form["nguon"] = "Google Form"

    print(f"Đọc được: File HR {len(hr)} dòng, Web {len(web)} dòng, "
          f"Google Form {len(form)} dòng")
    # Đổi tên cột của từng nguồn trước, rồi mới ghép lại
    cac_nguon = [nguon.rename(columns=DOI_TEN_COT) for nguon in (hr, web, form)]
    return pd.concat(cac_nguon, ignore_index=True)


# -------------------------------------------------------------- T: TRANSFORM
def chuan_hoa_sdt(sdt):
    """'+84906609544' hoặc '0906.609.544' -> '0906609544'"""
    chi_so = "".join(c for c in str(sdt) if c.isdigit())
    if chi_so.startswith("84"):
        chi_so = "0" + chi_so[2:]
    return chi_so


def chuan_hoa_ngay(chuoi):
    """'15/06/2026' hoặc '2026-06-15 ...' -> ngày 2026-06-15"""
    if "/" in chuoi:
        return datetime.strptime(chuoi, "%d/%m/%Y").date()
    return datetime.strptime(chuoi[:10], "%Y-%m-%d").date()


def transform(df):
    """Làm sạch dữ liệu, trả về bảng sạch và số liệu thống kê."""
    thong_ke = {"Số dòng đọc vào": len(df)}

    # 1. Bỏ dòng trống (không có tên hoặc email)
    df = df.dropna(subset=["ho_ten", "email"]).copy()
    thong_ke["Dòng trống bị bỏ"] = thong_ke["Số dòng đọc vào"] - len(df)

    # 2. Đưa mọi cột về cùng một mẫu
    df["ho_ten"] = df["ho_ten"].str.strip().str.title()
    df["email"] = df["email"].str.strip().str.lower()
    df["sdt"] = df["sdt"].apply(chuan_hoa_sdt)
    df["ngay_nop"] = df["ngay_nop"].apply(chuan_hoa_ngay)
    # Google Form không có trạng thái -> coi như vừa nộp hồ sơ
    df["vong"] = df["vong"].fillna("nộp hồ sơ").str.strip().str.lower().map(DOI_TEN_VONG)

    # 3. Bỏ email sai (thiếu @)
    email_dung = df["email"].str.contains("@")
    thong_ke["Email sai bị bỏ"] = int((~email_dung).sum())
    df = df[email_dung]

    # 4. Xóa hồ sơ trùng: cùng email + cùng vị trí -> giữ bản mới nhất
    so_dong_truoc = len(df)
    df = df.sort_values("ngay_nop").drop_duplicates(["email", "vi_tri"], keep="last")
    thong_ke["Hồ sơ trùng bị xóa"] = so_dong_truoc - len(df)

    thong_ke["Hồ sơ sạch lưu vào kho"] = len(df)
    return df, thong_ke


# ------------------------------------------------------------------- L: LOAD
def load(df):
    """Lưu bảng sạch vào cơ sở dữ liệu (chạy lại thì ghi đè, không bị nhân đôi)."""
    with sqlite3.connect(THU_MUC / "kho_tuyen_dung.db") as ket_noi:
        df.to_sql("ho_so_ung_tuyen", ket_noi, if_exists="replace", index=False)


# ------------------------------------------------------------------ BÁO CÁO
def in_bao_cao(df, thong_ke):
    print("\n=== KẾT QUẢ ETL ===")
    for ten, so in thong_ke.items():
        print(f"{ten:<24}: {so}")

    print("\n=== SỐ ỨNG VIÊN ĐÃ ĐI TỚI MỖI VÒNG ===")
    # Người đang ở vòng Phỏng vấn thì đã qua Nộp hồ sơ và Sàng lọc.
    # Người bị loại: chỉ tính là đã nộp hồ sơ.
    so_thu_tu = df["vong"].map({vong: i for i, vong in enumerate(CAC_VONG)}).fillna(0)
    for i, vong in enumerate(CAC_VONG):
        so_nguoi = int((so_thu_tu >= i).sum())
        print(f"{vong:<10}: {so_nguoi:>4}  ({so_nguoi / len(df):.0%})")


if __name__ == "__main__":
    du_lieu = extract()
    du_lieu_sach, thong_ke = transform(du_lieu)
    load(du_lieu_sach)
    in_bao_cao(du_lieu_sach, thong_ke)
