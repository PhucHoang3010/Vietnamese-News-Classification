# Cổng đăng kí học phần: mô phỏng xung đột dữ liệu đồng thời

Đồ án môn **Hệ quản trị cơ sở dữ liệu**. CSDL chạy trên **MySQL 8 (InnoDB)**, web viết bằng Node.js + Express, giao diện HTML/CSS/JS thuần.

Yêu cầu của đề tài:
1. Làm dữ liệu cho trang đăng kí học phần.
2. Giả lập xung đột dữ liệu khi nhiều người đăng kí cùng lúc, và trình bày cách giải quyết.
3. Chỉ làm một trang web đơn giản, có chức năng đăng kí học phần.

Toàn bộ nghiệp vụ đăng kí nằm trong **stored procedure** của MySQL. Web chỉ gọi `CALL` và hiển thị kết quả, nên mọi xung đột và cách sửa đều xảy ra thật trong MySQL.

| Phần | Nội dung | Thành viên |
|---|---|---|
| Tranh slot | Hai SV tranh chỗ cuối cùng của một lớp (lost update) | Minh Hiếu |
| Trùng lịch đồng thời | Một SV đăng kí cùng lúc hai lớp trùng giờ (write skew) | Phúc Hoàng |
| SV đăng kí | Thiết kế CSDL, dữ liệu mẫu, trang đăng kí và các quy tắc; xung đột đọc dữ liệu chưa COMMIT (dirty read) | (điền tên) |
| Trùng học phần | Một SV đăng kí cùng lúc hai lớp của một môn (phantom) | Đoàn Thịnh |

---

## 1. Chạy chương trình

Cần **MySQL 8.0 trở lên** và **Node.js 18 trở lên**.

**Windows, cách nhanh nhất:** giải nén, vào thư mục `dang-ky-hoc-phan`, **bấm đúp `chay-web.bat`**. File này làm 4 bước:
1. cài thư viện (`npm install`) nếu chưa có;
2. hỏi mật khẩu MySQL, sai thì hỏi lại, đúng thì lưu vào `.env` để lần sau khỏi nhập;
3. tạo CSDL `dkhp` gồm bảng, view, stored procedure và dữ liệu mẫu;
4. mở web ở cổng trống đầu tiên từ 3000 và mở trình duyệt.

Trên macOS / Linux dùng lệnh:

```bash
npm run chay
```

**Làm từng bước:**

```bash
npm install
```

Sao chép `.env.example` thành `.env`, điền `DB_USER` và `DB_PASSWORD` của MySQL trên máy.

```bash
npm run db:init
```

```bash
npm start
```

Mở http://localhost:3000.

- `npm run db:init` **xoá CSDL `dkhp` cũ nếu có** rồi tạo lại. Cách khác: mở 3 file trong `sql/` bằng MySQL Workbench, chạy lần lượt `01_schema.sql` → `02_procedures.sql` → `03_seed.sql`.
- Chưa cài MySQL thì có thể chạy bằng Docker: `docker compose up -d` (MySQL 8.4, user `root`, mật khẩu `root`).

**Lỗi thường gặp**

| Thông báo | Cách xử lý |
|---|---|
| `Could not read package.json` | Đang đứng sai thư mục. Vào đúng thư mục `dang-ky-hoc-phan` (thư mục có file `package.json`). |
| `Access denied for user 'root'` | Sai mật khẩu MySQL. Bấm đúp `chay-web.bat` để nhập lại, hoặc sửa `DB_PASSWORD` trong `.env`. |
| `MySQL chưa chạy` / `ECONNREFUSED` | Bật dịch vụ MySQL: Windows + R → `services.msc` → `MySQL80` → Start. |
| `Cổng 3000 đang bị chương trình khác dùng` | Web cũ còn chạy. Tắt cửa sổ đó, hoặc dùng `chay-web.bat` (tự chọn cổng khác). |
| Chạy trong VS Code bằng nút ▷ (Code Runner) bị treo ở bước nhập mật khẩu | Khung Output của Code Runner không nhập được. Bấm đúp `chay-web.bat`, hoặc mở Terminal → New Terminal rồi chạy `.\chay-web.bat`. |

---

## 2. Website

Web có 3 trang, dùng chung đầu trang và cùng một giao diện. Trang nào cũng dùng được trên điện thoại.

| Trang | Địa chỉ | Nội dung |
|---|---|---|
| Mô phỏng xung đột | `/` | 4 tình huống xung đột, hai sinh viên trên cùng một màn hình |
| Đăng kí học phần | `/dang-ki.html` | Chức năng đăng kí đầy đủ cho mọi sinh viên |
| Thiết kế CSDL | `/csdl.html` | ERD, lược đồ quan hệ, stored procedure, dữ liệu các bảng |

### 2.1. Mô phỏng xung đột (trang chủ)

Màn hình có hai cửa sổ giống cổng đăng kí thật: **Máy của bạn A** và **Máy của bạn B**. Nếu hai lần bấm là của cùng một sinh viên thì hai cửa sổ ghi **Tab 1 / Tab 2**. Mỗi lần bấm Đăng kí là một giao dịch thật, chạy trên một kết nối MySQL riêng.

Cách demo:
1. Chọn tình huống: **1 Tranh slot**, **2 Trùng lịch đồng thời**, **3 SV đăng kí**, **4 Trùng học phần**.
2. Chọn **Xử lý xung đột: Tắt** rồi bấm **▶ Hai bạn cùng bấm Đăng kí**. Dữ liệu tự đặt lại, A bấm trước, B bấm sau 0,3 giây (tình huống 3 là 0,5 giây). Thủ tục có 3 giây xử lý chậm giữa lúc kiểm tra và lúc ghi, nên hai giao dịch chắc chắn chen nhau.
3. Xem kết quả ở từng cửa sổ và dòng **Kiểm tra dữ liệu trong MySQL** bên dưới (❌ là dữ liệu bị sai).
4. Chuyển sang **Bật** và bấm lại: B phải chờ khoá ("Đã phải chờ … giây"), dữ liệu đúng (✅).
5. Mục **Nhật kí giao dịch** liệt kê từng bước của A và B theo thời điểm do MySQL ghi.

| Tình huống | A | B | Tắt | Bật |
|---|---|---|---|---|
| Tranh slot | SV09 → KTCT.02 (1 chỗ) | SV10 → KTCT.02 | Cả hai đăng kí được, lớp 2/1, cột sĩ số lưu = 1 | B chờ ~2,7 giây, nhận "Lớp đã đủ sĩ số" |
| Trùng lịch đồng thời | SV09 → CSDL.01 (Thứ 2, tiết 1-3) | SV09 → CTDL.01 (Thứ 2, tiết 2-4) | SV09 có 2 lớp trùng giờ | Tab 2 chờ ~2,7 giây, nhận "Trùng lịch với lớp CSDL.01" |
| SV đăng kí | SV18 (nợ học phí) → KTCT.02 | SV19 → KTCT.02 | SV19 bị báo "Lớp đã đủ sĩ số" dù lớp vẫn 0/1 | SV19 chờ ~2,5 giây rồi đăng kí thành công |
| Trùng học phần | SV10 → CSDL.01 | SV10 → CSDL.02 (cùng môn) | SV10 có 2 lớp của một môn | Tab 2 chờ ~2,7 giây, nhận "Trùng học phần" |

Có thể bấm từng nút Đăng kí trong mỗi cửa sổ bằng tay thay cho nút bấm cùng lúc. Nút **↺ Đặt lại** nạp lại dữ liệu mẫu.

### 2.2. Đăng kí học phần

- Chọn sinh viên, xem lớp, mã sinh viên, tổng tín chỉ đã đăng kí và nhãn **Còn nợ học phí**.
- Danh sách lớp học phần đang mở: tìm theo mã lớp, tên môn, giảng viên, hoặc lọc theo môn; sĩ số có thanh màu. Nút **Đăng kí** gọi `sp_dang_ky_mo_phong`, nút **Huỷ** gọi `sp_huy_dang_ky`.
- **Lớp đã đăng kí** kèm tổng tín chỉ, và **thời khoá biểu** theo tiết (lớp trùng giờ tô đỏ, xếp cạnh nhau).
- **Kiểm tra toàn vẹn dữ liệu** đọc view `v_kiem_tra_toan_ven`.

Thủ tục đăng kí kiểm tra **6 quy tắc**, sai một quy tắc thì ROLLBACK và trả lý do bằng tiếng Việt. Dữ liệu mẫu có sẵn ví dụ cho từng quy tắc:

| Quy tắc | Điều kiện | Thử |
|---|---|---|
| Lớp đã đầy | `si_so_hien_tai >= si_so_toi_da` | Bất kì SV nào đăng kí `PLDC.01` (đang 3/3) |
| Đăng kí lại một lớp | đã có `(ma_sv, ma_lhp)`; thêm `UNIQUE (ma_sv, ma_lhp)` | `SV01` đăng kí lại `CSDL.01` |
| Trùng học phần | đã có lớp cùng `ma_mh` | `SV01` đăng kí `CSDL.02` |
| Trùng lịch | cùng `thu`, `tiet_bd1 <= tiet_kt2` và `tiet_bd2 <= tiet_kt1` | `SV01` đăng kí `CTDL.01` |
| Vượt tín chỉ | tín chỉ đã có + môn mới > `tin_chi_toi_da` | `SV07` (tối đa 8 TC) đăng kí 3 môn 4 TC |
| Nợ học phí | `no_hoc_phi = TRUE` | `SV08` đăng kí bất kì lớp nào |

**Thử xung đột bằng hai cửa sổ trình duyệt thật:** chọn **Xử lý xung đột: Tắt** và **Thời gian xử lý 3–5 giây** (chế độ tự áp dụng cho mọi cửa sổ). Mở thêm một cửa sổ cùng địa chỉ, chọn sinh viên khác, rồi bấm Đăng kí ở hai cửa sổ gần như cùng lúc, theo các cặp ở bảng mục 2.1. Trang tự làm mới mỗi 2 giây nên thấy ngay thay đổi do cửa sổ kia gây ra.

### 2.3. Thiết kế CSDL

- ERD kiểu Chen và sơ đồ quan hệ Crow's Foot, có nút tải ảnh PNG.
- **Lược đồ quan hệ đọc thẳng từ `information_schema`:** từng cột kèm kiểu dữ liệu, `NOT NULL`, giá trị mặc định, khoá chính, khoá ngoại, ý nghĩa (lấy từ `COMMENT` của cột), và danh sách ràng buộc `PRIMARY KEY`, `UNIQUE`, `FOREIGN KEY`, `CHECK`, chỉ mục.
- **Danh sách 14 stored procedure** kèm tham số và mô tả (lấy từ `COMMENT` của thủ tục).
- Dữ liệu từng bảng và view `v_kiem_tra_toan_ven` (`SELECT *` từ MySQL).

---

## 3. Thiết kế cơ sở dữ liệu

### 3.1. ERD (mô hình thực thể – kết hợp, ký hiệu Chen)

![ERD kiểu Chen](docs/erd-chen.png)

Hình chữ nhật là thực thể, hình elip là thuộc tính, hình thoi là mối kết hợp. Thuộc tính **gạch chân là khoá chính**; thuộc tính ghi **(FK)**, chữ nghiêng, viền nét đứt **là khoá ngoại**. `1`, `N` là bản số. Bản vector: [`docs/erd-chen.svg`](docs/erd-chen.svg).

- Một sinh viên có nhiều lượt đăng kí; mỗi lượt đăng kí thuộc đúng một sinh viên.
- Một lớp học phần có nhiều lượt đăng kí; mỗi lượt đăng kí thuộc đúng một lớp.
- Một môn học mở nhiều lớp học phần; mỗi lớp thuộc đúng một môn.

`SINH_VIEN` và `LOP_HOC_PHAN` có quan hệ nhiều – nhiều, được tách thành thực thể `DANG_KY`.

### 3.2. Lược đồ quan hệ

Khoá chính gạch chân (viết trong ngoặc `[ ]`), khoá ngoại có mũi tên:

```
SINH_VIEN    ([ma_sv], ho_ten, lop, tin_chi_toi_da, no_hoc_phi)
MON_HOC      ([ma_mh], ten_mh, so_tin_chi)
LOP_HOC_PHAN ([ma_lhp], ma_mh → MON_HOC, giang_vien, thu, tiet_bd, tiet_kt, phong, si_so_toi_da, si_so_hien_tai)
DANG_KY      ([id], ma_sv → SINH_VIEN, (ma_lhp, ma_mh) → LOP_HOC_PHAN(ma_lhp, ma_mh), thoi_gian)
```

| Bảng | Khoá chính | Khoá ngoại (khoá phụ) | Ràng buộc khác |
|---|---|---|---|
| `sinh_vien` | `ma_sv` | – | `tin_chi_toi_da` mặc định 24 |
| `mon_hoc` | `ma_mh` | – | `CHECK (so_tin_chi BETWEEN 1 AND 10)` |
| `lop_hoc_phan` | `ma_lhp` | `ma_mh` → `mon_hoc(ma_mh)` | `UNIQUE (ma_lhp, ma_mh)`; `CHECK` thứ 2..8, tiết 1..12 và `tiet_bd <= tiet_kt`, sĩ số |
| `dang_ky` | `id` (tự tăng) | `ma_sv` → `sinh_vien(ma_sv)`; `(ma_lhp, ma_mh)` → `lop_hoc_phan(ma_lhp, ma_mh)` | `UNIQUE (ma_sv, ma_lhp)`; chỉ mục `(ma_sv, ma_mh)` |

`dang_ky` lưu kèm `ma_mh` để kiểm tra trùng học phần nhanh bằng chỉ mục. Khoá ngoại kép `(ma_lhp, ma_mh)` bảo đảm cột lưu kèm này luôn khớp với lớp (vì vậy `lop_hoc_phan` có `UNIQUE (ma_lhp, ma_mh)` làm đích tham chiếu).

Sơ đồ quan hệ kèm kiểu dữ liệu (Crow's Foot):

![Lược đồ quan hệ](docs/erd.png)

Muốn có EER diagram do MySQL Workbench tự vẽ: chạy `db:init` xong, vào *Database → Reverse Engineer…*, chọn schema `dkhp`.

### 3.3. View kiểm tra toàn vẹn

`v_kiem_tra_toan_ven` liệt kê mọi chỗ dữ liệu đang sai. **Dữ liệu đúng khi view rỗng.**

| `loai` | Ý nghĩa | Do xung đột |
|---|---|---|
| `VUOT_SI_SO` | Số SV đăng kí vượt sĩ số tối đa | Tranh slot |
| `SAI_SI_SO` | Cột `si_so_hien_tai` khác số đăng kí thực tế | Tranh slot (lost update) |
| `TRUNG_LICH` | Một SV có 2 lớp trùng giờ | Trùng lịch đồng thời |
| `TRUNG_HOC_PHAN` | Một SV có nhiều lớp của cùng một môn | Trùng học phần |
| `VUOT_TIN_CHI` | Tổng tín chỉ vượt mức tối đa | Đăng kí đồng thời nhiều lớp |

### 3.4. Dữ liệu mẫu (`sql/03_seed.sql`)

19 sinh viên, 10 môn, 16 lớp học phần, 16 lượt đăng kí ban đầu. Nạp lại được nhiều lần.

| Dữ liệu đặc biệt | Dùng cho |
|---|---|
| `PLDC.01` đã đầy (3/3) | Quy tắc lớp đã đầy |
| `SV07` tối đa 8 tín chỉ | Quy tắc vượt tín chỉ |
| `SV08`, `SV18` còn nợ học phí | Quy tắc nợ học phí; tình huống SV đăng kí |
| `KTCT.02` chỉ có 1 chỗ | Tranh slot; SV đăng kí |
| `CSDL.01` (Thứ 2, tiết 1-3) và `CTDL.01` (Thứ 2, tiết 2-4) | Trùng lịch |
| `CSDL.01` và `CSDL.02` cùng môn Cơ sở dữ liệu | Trùng học phần |
| `SV11`…`SV19`, lớp `HQT.03` (2 chỗ), `HQT.01`/`HQT.02` | Kịch bản SQL trong `sql/demo` |

---

## 4. Bốn xung đột và cách giải quyết

Thời điểm trong các bảng dưới lấy theo trang chủ (thủ tục chậm 3 giây, B bấm sau A 0,3 giây).

### 4.1. Tranh slot (lost update) · Minh Hiếu

Lớp `KTCT.02` còn 1 chỗ, SV09 và SV10 cùng bấm Đăng kí.

| Thời điểm | A · SV09 | B · SV10 |
|---|---|---|
| 0,0 s | Đọc sĩ số 0/1 → còn chỗ | |
| 0,3 s | | Đọc sĩ số 0/1 → còn chỗ |
| 3,0 s | Ghi `si_so_hien_tai = 0 + 1`, chèn đăng kí, COMMIT | |
| 3,3 s | | Ghi `si_so_hien_tai = 0 + 1`, chèn đăng kí, COMMIT |

**Kết quả sai:** lớp 1 chỗ có 2 sinh viên, cột sĩ số chỉ là 1 (lần ghi sau đè lần ghi trước).
**Nguyên nhân:** `SELECT` thường không khoá, hai giao dịch đọc cùng một giá trị cũ rồi ghi đè lên nhau.
**Cách giải quyết:** đọc dòng lớp bằng `SELECT ... FOR UPDATE`. Khoá giữ tới khi COMMIT, nên B phải chờ A xong rồi mới đọc, thấy 1/1 và bị từ chối. Cách khác: `UPDATE ... SET si_so_hien_tai = si_so_hien_tai + 1 WHERE si_so_hien_tai < si_so_toi_da` rồi kiểm tra `ROW_COUNT()`.

### 4.2. Trùng lịch đồng thời (write skew) · Phúc Hoàng

SV09 mở 2 tab: tab 1 đăng kí `CSDL.01` (Thứ 2, tiết 1-3), tab 2 đăng kí `CTDL.01` (Thứ 2, tiết 2-4).

| Thời điểm | Tab 1 · CSDL.01 | Tab 2 · CTDL.01 |
|---|---|---|
| 0,0 s | Kiểm tra lịch Thứ 2: chưa có lớp nào → hợp lệ | |
| 0,3 s | | Kiểm tra lịch: chưa thấy CSDL.01 (tab 1 chưa COMMIT) → hợp lệ |
| 3,0 s | Lưu CSDL.01, COMMIT | |
| 3,3 s | | Lưu CTDL.01, COMMIT |

**Kết quả sai:** SV09 có 2 lớp trùng tiết 2-3.
**Nguyên nhân:** hai giao dịch ghi hai dòng khác nhau vào hai lớp khác nhau, không có dòng chung nào bị khoá nên không ai chờ ai. Mỗi bên đúng khi xét riêng, gộp lại thì sai (write skew). Khoá dòng lớp không giúp được vì hai tab khoá hai lớp khác nhau; `UNIQUE`, `CHECK` cũng không chặn được vì chúng chỉ xét từng dòng.
**Cách giải quyết:** khoá dòng cha chung `SELECT ... FROM sinh_vien WHERE ma_sv = ? FOR UPDATE` ngay **câu đầu tiên** của giao dịch. Hai tab của cùng một SV phải chạy lần lượt: tab 2 chờ tab 1 COMMIT, rồi thấy CSDL.01 và từ chối. Sinh viên khác không bị ảnh hưởng.
⚠ Phải khoá trước khi đọc: ở `REPEATABLE READ` (mặc định), InnoDB chụp snapshot ở lần `SELECT` thường đầu tiên; đọc trước rồi mới khoá thì tab 2 vẫn kiểm tra trên snapshot cũ.

### 4.3. SV đăng kí: đăng kí bị huỷ giữa chừng (dirty read)

Lớp `KTCT.02` còn 1 chỗ. SV18 (đang nợ học phí) bấm Đăng kí: hệ thống **giữ chỗ trước** rồi mới kiểm tra học phí, mất 3 giây. SV19 bấm Đăng kí cùng lớp trong lúc đó. Khi chưa xử lý, giao dịch của SV19 chạy ở `READ UNCOMMITTED`.

| Thời điểm | A · SV18 (`sp_giu_cho_roi_huy`) | B · SV19 |
|---|---|---|
| 0,0 s | Giữ chỗ: sĩ số 0 → 1/1, chèn đăng kí, **chưa COMMIT** | |
| 0,5 s | | Đọc 1/1 (đọc cả dữ liệu chưa COMMIT) → "Lớp đã đủ sĩ số" |
| 3,0 s | Nợ học phí → ROLLBACK, lớp về 0/1 | |

**Kết quả sai:** SV19 bị từ chối oan, lớp vẫn còn trống.
**Nguyên nhân:** B đọc dữ liệu chưa COMMIT, và dữ liệu đó sau cùng bị huỷ.
**Cách giải quyết:** dùng mức cô lập từ `READ COMMITTED` trở lên (`sp_dirty_read_an_toan`). B chỉ thấy bản đã COMMIT (0/1); câu `UPDATE ... WHERE si_so_hien_tai < si_so_toi_da` phải chờ khoá dòng lớp mà A đang giữ. A ROLLBACK xong, MySQL kiểm tra lại điều kiện, B đăng kí thành công. Nếu A COMMIT thật thì `ROW_COUNT() = 0` và B bị từ chối đúng.

| Mức cô lập | Đọc dữ liệu chưa COMMIT | Đọc lại ra số khác | Thấy thêm dòng mới |
|---|---|---|---|
| READ UNCOMMITTED | Có thể | Có thể | Có thể |
| READ COMMITTED | Không | Có thể | Có thể |
| REPEATABLE READ (mặc định MySQL) | Không | Không | Có thể (InnoDB chặn phần lớn bằng next-key lock) |
| SERIALIZABLE | Không | Không | Không |

### 4.4. Trùng học phần (phantom) · Đoàn Thịnh

SV10 đăng kí cùng lúc `CSDL.01` (Thứ 2) và `CSDL.02` (Thứ 4): khác giờ nhưng cùng môn Cơ sở dữ liệu.

**Kết quả sai:** cả hai giao dịch đếm "đã có lớp môn CSDL chưa" trước khi bên kia chèn, đều được 0, rồi cùng chèn. `UNIQUE (ma_sv, ma_lhp)` không chặn được vì hai lớp có mã khác nhau.
**Cách giải quyết trên web:** khoá dòng sinh viên ở đầu giao dịch (giống 4.2), lần đăng kí thứ hai chờ rồi thấy CSDL.01, báo "Trùng học phần".
**Hai cách khác** (có trong kịch bản SQL `sql/demo/3_trung_hoc_phan.sql` và trong test):
- Mức `SERIALIZABLE`: InnoDB biến `SELECT` thành `SELECT ... FOR SHARE` và khoá cả khoảng trống (next-key lock) trên chỉ mục `(ma_sv, ma_mh)`. Hai bên cùng giữ khoá S rồi cùng muốn chèn → deadlock 1213, InnoDB huỷ một bên; bên đó thử lại thì thấy lớp đã có và từ chối.
- Ràng buộc `UNIQUE (ma_sv, ma_mh)`: lớp bảo vệ cuối, MySQL tự chặn dòng trùng bằng lỗi 1062 kể cả khi code ứng dụng sai.

### 4.5. Tóm tắt

| Xung đột | Loại | Cách giải quyết |
|---|---|---|
| Tranh slot | Lost update | Khoá dòng lớp `SELECT ... FOR UPDATE` |
| Trùng lịch đồng thời | Write skew | Khoá dòng sinh viên ở câu đầu tiên của giao dịch |
| SV đăng kí | Dirty read | Mức cô lập ≥ `READ COMMITTED` + `UPDATE` có điều kiện |
| Trùng học phần | Phantom | Khoá dòng sinh viên; hoặc `SERIALIZABLE`; hoặc `UNIQUE (ma_sv, ma_mh)` |

Thủ tục đăng kí chính `sp_dang_ky_mo_phong(ma_sv, ma_lhp, co_xu_ly, tre)` gộp các cách trên:

| Bước | Có xử lý (`co_xu_ly = TRUE`) | Không xử lý |
|---|---|---|
| B1 | `SELECT ... FROM sinh_vien ... FOR UPDATE` | `SELECT` thường |
| B2 | `SELECT ... FROM lop_hoc_phan ... FOR UPDATE` | `SELECT` thường |
| B3 | Kiểm tra 6 quy tắc, sai thì ROLLBACK | như bên trái |
| B4 | `UPDATE si_so_hien_tai = si_so_hien_tai + 1`, `INSERT dang_ky`, COMMIT | ghi sĩ số bằng giá trị đã đọc |

Cả 4 bước nằm trong một giao dịch nên có **tính nguyên tử**. Thứ tự khoá luôn là **sinh viên trước, lớp sau**, nên các lần đăng kí đồng thời không thể chờ vòng tròn, không gây deadlock. `sp_dang_ky` là bản chuẩn: có xử lý, không chậm.

---

## 5. Kịch bản SQL và chạy trên terminal

Ngoài trang web, mỗi xung đột còn có cặp thủ tục `sp_..._loi` / `sp_..._an_toan` dùng dữ liệu riêng (SV11…SV19), để demo bằng tay hoặc chạy tự động:

| Kịch bản | Không xử lý | Có xử lý | Dữ liệu |
|---|---|---|---|
| 1. Tranh slot | `sp_tranh_slot_loi` | `sp_tranh_slot_an_toan` | 5 SV (SV11…SV15) tranh lớp `HQT.03` 2 chỗ |
| 2. Trùng lịch | `sp_trung_lich_loi` | `sp_trung_lich_an_toan` | SV16: `CSDL.01` + `CTDL.01` |
| 3. Trùng học phần | `sp_trung_hp_loi` | `sp_trung_hp_an_toan` (SERIALIZABLE) | SV17: `HQT.01` + `HQT.02` |
| 4. SV đăng kí | `sp_giu_cho_roi_huy` + `sp_dirty_read_loi` | `sp_giu_cho_roi_huy` + `sp_dirty_read_an_toan` | SV18, SV19, lớp `KTCT.02` |

- **MySQL Workbench, 2 phiên:** mở file trong `sql/demo/`, chạy phần "Phiên 1" ở một tab kết nối và "Phiên 2" ở tab kết nối thứ hai trong vòng 10 giây. Trong Workbench, các tab query của cùng một kết nối dùng chung một phiên; muốn có 2 phiên phải bấm vào connection ở màn hình Home 2 lần.
- **Terminal:** `npm run demo` chạy cả 4 kịch bản, mỗi kịch bản 2 chế độ, và in lịch thao tác. Chỉ chạy kịch bản 2: `npm run demo -- 2`.
- `sp_dat_lai_kich_ban(kb)` đưa dữ liệu của một kịch bản về ban đầu.

## 6. Kiểm thử tự động

```bash
npm test
```

24 test (cần MySQL đang chạy; **test sẽ nạp lại dữ liệu mẫu**):
- `test/web.test.js` gọi qua HTTP đúng như trang web: cả 4 tình huống với **Tắt** phải làm sai dữ liệu, với **Bật** phải đúng và bên B phải chờ khoá; chỉ bấm một bên thì luôn đúng; API báo lỗi 400/404 khi dữ liệu gửi lên sai; lược đồ đủ khoá chính, khoá ngoại; mọi bảng, cột, thủ tục đều có chú thích.
- `test/kich-ban.test.js` chạy 4 cặp thủ tục kịch bản, kiểm tra 6 quy tắc đăng kí, `UNIQUE (ma_sv, ma_mh)` chặn bằng lỗi 1062, và `sp_dang_ky` an toàn khi bấm đồng thời.

## 7. API

| Phương thức | Đường dẫn | Việc |
|---|---|---|
| GET | `/api/sinh-vien` | Danh sách SV kèm số lớp, số tín chỉ đã đăng kí |
| GET | `/api/lop-hoc-phan` | Danh sách lớp kèm số đăng kí thực tế |
| GET | `/api/sinh-vien/:ma/dang-ky` | Các lớp SV đã đăng kí |
| POST | `/api/dang-ky` | `{ ma_sv, ma_lhp, coXuLy, tre }` → `sp_dang_ky_mo_phong` |
| POST | `/api/huy-dang-ky` | `{ ma_sv, ma_lhp }` → `sp_huy_dang_ky` |
| GET | `/api/kiem-tra` | Nội dung view `v_kiem_tra_toan_ven` |
| POST | `/api/du-lieu-mau` | Nạp lại dữ liệu mẫu |
| GET | `/api/luoc-do`, `/api/thu-tuc` | Lược đồ và thủ tục đọc từ `information_schema` |
| GET | `/api/bang`, `/api/bang/:ten` | Số dòng và dữ liệu từng bảng |
| GET | `/api/mo-phong/tinh-huong` | 4 tình huống của trang chủ |
| POST | `/api/mo-phong/dat-lai` | Nạp lại dữ liệu mẫu (lần lượt từng yêu cầu) |
| POST | `/api/mo-phong/giao-dich` | `{ tinhHuong, vai: 'A' \| 'B', coXuLy, tre }` → một giao dịch, trả kèm nhật kí từng bước |
| GET | `/api/mo-phong/trang-thai?tinhHuong=` | Dữ liệu đã COMMIT của tình huống và vi phạm toàn vẹn |

## 8. Cấu trúc thư mục

```
chay-web.bat             bấm đúp để chạy trên Windows
sql/01_schema.sql        tạo CSDL dkhp: 4 bảng (có COMMENT), ràng buộc, view v_kiem_tra_toan_ven
sql/02_procedures.sql    14 stored procedure (có COMMENT)
sql/03_seed.sql          dữ liệu mẫu
sql/demo/*.sql           kịch bản 2 phiên cho MySQL Workbench
src/server.js            web server (Express) và API
src/mo-phong.js          API của trang Mô phỏng xung đột
src/kich-ban.js          bộ chạy giao dịch đồng thời cho kịch bản SQL (npm run demo, test)
src/db.js                kết nối MySQL, chạy file .sql (hiểu lệnh DELIMITER), câu báo lỗi tiếng Việt
src/khoi-dong.js         trình khởi động: cài thư viện, hỏi mật khẩu, tạo CSDL, mở web
public/index.html        trang Mô phỏng xung đột      (mo-phong.js)
public/dang-ki.html      trang Đăng kí học phần       (dang-ki.js)
public/csdl.html         trang Thiết kế CSDL          (csdl.js)
public/giao-dien.css     giao diện chung; chung.js: tiện ích dùng chung
docs/erd-chen.svg, .png  ERD kiểu Chen
docs/erd.svg, .png       sơ đồ quan hệ Crow's Foot
test/                    kiểm thử tự động (node:test)
```

Đã kiểm thử trên MySQL 8.0 và Node.js 22. MariaDB (XAMPP) có thể chạy được nhưng chưa kiểm thử, và cách khoá của MariaDB có thể khác một chút.
