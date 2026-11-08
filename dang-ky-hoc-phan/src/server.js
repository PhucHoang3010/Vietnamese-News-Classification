// Web server của cổng đăng kí học phần.
//   /               Mô phỏng xung đột (4 tình huống, 2 sinh viên trên một màn hình)
//   /dang-ki.html   Đăng kí học phần đầy đủ cho mọi sinh viên
//   /csdl.html      Thiết kế CSDL: ERD, lược đồ quan hệ, stored procedure, dữ liệu
const path = require('path');
const express = require('express');
const { layPool, goiThuTuc, napDuLieuMau, giaiThichLoi, DB_NAME } = require('./db');

const app = express();
app.disable('x-powered-by');
app.use(express.json({ limit: '10kb' }));

// Địa chỉ cũ vẫn dùng được
app.get('/mo-phong.html', (req, res) => res.redirect(301, '/'));
app.get('/day-du.html', (req, res) => res.redirect(301, '/dang-ki.html'));
app.use(express.static(path.join(__dirname, '..', 'public')));
app.use('/docs', express.static(path.join(__dirname, '..', 'docs')));

const loiYeuCau = (msg) => Object.assign(new Error(msg), { status: 400 });
const boc = (fn) => (req, res, next) => fn(req, res).catch(next);

/** Lấy mã (sinh viên / lớp) từ body, chỉ nhận chữ, số, dấu chấm, gạch. */
function layMa(body, ten) {
  const v = body && body[ten];
  if (typeof v !== 'string' || !/^[A-Za-z0-9._-]{1,15}$/.test(v)) throw loiYeuCau(`Thiếu hoặc sai "${ten}"`);
  return v;
}

async function goi(ten, thamSo) {
  const conn = await layPool().getConnection();
  try { return await goiThuTuc(conn, ten, thamSo); } finally { conn.release(); }
}

// ---------- Trang đăng kí học phần ----------
app.get('/api/sinh-vien', boc(async (req, res) => {
  const [rows] = await layPool().query(
    `SELECT s.ma_sv, s.ho_ten, s.lop, s.tin_chi_toi_da, s.no_hoc_phi,
            COUNT(d.id) AS so_lop, IFNULL(SUM(m.so_tin_chi), 0) AS so_tc
     FROM sinh_vien s
     LEFT JOIN dang_ky d ON d.ma_sv = s.ma_sv
     LEFT JOIN mon_hoc m ON m.ma_mh = d.ma_mh
     GROUP BY s.ma_sv ORDER BY s.ma_sv`);
  res.json(rows.map((r) => ({ ...r, so_tc: Number(r.so_tc), no_hoc_phi: !!r.no_hoc_phi })));
}));

app.get('/api/lop-hoc-phan', boc(async (req, res) => {
  const [rows] = await layPool().query(
    `SELECT l.*, m.ten_mh, m.so_tin_chi,
            (SELECT COUNT(*) FROM dang_ky d WHERE d.ma_lhp = l.ma_lhp) AS so_dk_thuc_te
     FROM lop_hoc_phan l JOIN mon_hoc m ON m.ma_mh = l.ma_mh
     ORDER BY l.ma_mh, l.ma_lhp`);
  res.json(rows);
}));

app.get('/api/sinh-vien/:ma/dang-ky', boc(async (req, res) => {
  const [rows] = await layPool().query(
    `SELECT d.ma_lhp, d.ma_mh, m.ten_mh, m.so_tin_chi, l.thu, l.tiet_bd, l.tiet_kt, l.phong, l.giang_vien, d.thoi_gian
     FROM dang_ky d
     JOIN lop_hoc_phan l ON l.ma_lhp = d.ma_lhp
     JOIN mon_hoc m ON m.ma_mh = d.ma_mh
     WHERE d.ma_sv = ? ORDER BY l.thu, l.tiet_bd`, [req.params.ma]);
  res.json(rows);
}));

// coXuLy: true = có xử lý xung đột (khoá FOR UPDATE), false = không xử lý; tre: số giây xử lý chậm (0..10)
app.post('/api/dang-ky', boc(async (req, res) => {
  const maSv = layMa(req.body, 'ma_sv'), maLhp = layMa(req.body, 'ma_lhp');
  const { coXuLy = true, tre = 0 } = req.body;
  const giay = Math.min(10, Math.max(0, Number(tre) || 0));
  res.json(await goi('sp_dang_ky_mo_phong', [maSv, maLhp, coXuLy !== false, giay]));
}));

app.post('/api/huy-dang-ky', boc(async (req, res) => {
  res.json(await goi('sp_huy_dang_ky', [layMa(req.body, 'ma_sv'), layMa(req.body, 'ma_lhp')]));
}));

app.get('/api/kiem-tra', boc(async (req, res) => {
  const [rows] = await layPool().query('SELECT * FROM v_kiem_tra_toan_ven ORDER BY loai, doi_tuong');
  res.json(rows);
}));

app.post('/api/du-lieu-mau', boc(async (req, res) => {
  await napDuLieuMau();
  res.json({ ok: true });
}));

// ---------- Trang thiết kế CSDL ----------
const BANG = ['sinh_vien', 'mon_hoc', 'lop_hoc_phan', 'dang_ky', 'v_kiem_tra_toan_ven'];

app.get('/api/bang', boc(async (req, res) => {
  const pool = layPool();
  res.json(await Promise.all(BANG.map(async (ten) => {
    const [[r]] = await pool.query(`SELECT COUNT(*) AS n FROM ${ten}`);
    return { ten, so_dong: r.n };
  })));
}));

app.get('/api/bang/:ten', boc(async (req, res) => {
  const ten = req.params.ten;
  if (!BANG.includes(ten)) return res.status(404).json({ loi: 'Bảng không tồn tại' });
  const [rows, fields] = await layPool().query(`SELECT * FROM ${ten} ORDER BY 1, 2 LIMIT 500`);
  res.json({ cot: fields.map((f) => f.name), dong: rows });
}));

// Lược đồ quan hệ đọc thẳng từ information_schema: cột, kiểu, khoá chính, khoá ngoại, UNIQUE, CHECK
app.get('/api/luoc-do', boc(async (req, res) => {
  const pool = layPool();
  const [bang] = await pool.query(
    `SELECT TABLE_NAME AS ten, TABLE_COMMENT AS ghi_chu FROM information_schema.TABLES
     WHERE TABLE_SCHEMA = ? AND TABLE_TYPE = 'BASE TABLE'`, [DB_NAME]);
  const [cot] = await pool.query(
    `SELECT TABLE_NAME AS bang, COLUMN_NAME AS ten, COLUMN_TYPE AS kieu, IS_NULLABLE = 'YES' AS co_the_null,
            COLUMN_DEFAULT AS mac_dinh, EXTRA AS them, COLUMN_COMMENT AS ghi_chu
     FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = ? ORDER BY TABLE_NAME, ORDINAL_POSITION`, [DB_NAME]);
  const [khoa] = await pool.query(
    `SELECT k.TABLE_NAME AS bang, k.CONSTRAINT_NAME AS ten, c.CONSTRAINT_TYPE AS loai, k.COLUMN_NAME AS cot,
            k.REFERENCED_TABLE_NAME AS bang_tc, k.REFERENCED_COLUMN_NAME AS cot_tc
     FROM information_schema.KEY_COLUMN_USAGE k
     JOIN information_schema.TABLE_CONSTRAINTS c
       ON c.CONSTRAINT_SCHEMA = k.CONSTRAINT_SCHEMA AND c.TABLE_NAME = k.TABLE_NAME AND c.CONSTRAINT_NAME = k.CONSTRAINT_NAME
     WHERE k.TABLE_SCHEMA = ? ORDER BY k.TABLE_NAME, k.CONSTRAINT_NAME, k.ORDINAL_POSITION`, [DB_NAME]);
  const [kiemTra] = await pool.query(
    `SELECT t.TABLE_NAME AS bang, c.CONSTRAINT_NAME AS ten, c.CHECK_CLAUSE AS dieu_kien
     FROM information_schema.CHECK_CONSTRAINTS c
     JOIN information_schema.TABLE_CONSTRAINTS t
       ON t.CONSTRAINT_SCHEMA = c.CONSTRAINT_SCHEMA AND t.CONSTRAINT_NAME = c.CONSTRAINT_NAME
     WHERE c.CONSTRAINT_SCHEMA = ? ORDER BY c.CONSTRAINT_NAME`, [DB_NAME]);
  const [chiMuc] = await pool.query(
    `SELECT TABLE_NAME AS bang, INDEX_NAME AS ten, COLUMN_NAME AS cot FROM information_schema.STATISTICS
     WHERE TABLE_SCHEMA = ? AND NON_UNIQUE = 1 ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX`, [DB_NAME]);

  const nhom = (ds) => Object.values(ds.reduce((m, k) => {
    const id = `${k.bang}|${k.ten}`;
    (m[id] ||= { bang: k.bang, ten: k.ten, loai: k.loai, cot: [], bang_tc: k.bang_tc, cot_tc: [] }).cot.push(k.cot);
    if (k.cot_tc) m[id].cot_tc.push(k.cot_tc);
    return m;
  }, {}));
  const rangBuoc = nhom(khoa);
  const THU_TU = ['sinh_vien', 'mon_hoc', 'lop_hoc_phan', 'dang_ky'];
  res.json(bang.sort((a, b) => THU_TU.indexOf(a.ten) - THU_TU.indexOf(b.ten)).map((b) => {
    const rb = rangBuoc.filter((r) => r.bang === b.ten);
    const pk = rb.find((r) => r.loai === 'PRIMARY KEY');
    return {
      ...b,
      cot: cot.filter((c) => c.bang === b.ten).map((c) => ({
        ten: c.ten, kieu: c.kieu, co_the_null: !!c.co_the_null, mac_dinh: c.mac_dinh, them: c.them, ghi_chu: c.ghi_chu,
        khoa_chinh: !!pk && pk.cot.includes(c.ten),
        khoa_ngoai: rb.filter((r) => r.loai === 'FOREIGN KEY' && r.cot.includes(c.ten))
          .map((r) => `${r.bang_tc}(${r.cot_tc[r.cot.indexOf(c.ten)]})`),
      })),
      rang_buoc: [
        ...rb.map(({ ten, loai, cot: ds, bang_tc, cot_tc }) => ({ ten, loai, cot: ds, bang_tc, cot_tc })),
        ...kiemTra.filter((k) => k.bang === b.ten).map((k) => ({ ten: k.ten, loai: 'CHECK', dieu_kien: k.dieu_kien.replace(/`/g, '') })),
        // chỉ mục do khoá ngoại tự tạo (trùng tên khoá ngoại) thì không liệt kê lại
        ...nhom(chiMuc.filter((i) => i.bang === b.ten && !rb.some((r) => r.ten === i.ten))).map((i) => ({ ten: i.ten, loai: 'INDEX', cot: i.cot })),
      ],
    };
  }));
}));

app.get('/api/thu-tuc', boc(async (req, res) => {
  const pool = layPool();
  const [tt] = await pool.query(
    `SELECT ROUTINE_NAME AS ten, ROUTINE_COMMENT AS ghi_chu FROM information_schema.ROUTINES
     WHERE ROUTINE_SCHEMA = ? AND ROUTINE_TYPE = 'PROCEDURE' ORDER BY ROUTINE_NAME`, [DB_NAME]);
  const [ts] = await pool.query(
    `SELECT SPECIFIC_NAME AS thu_tuc, PARAMETER_MODE AS kieu_truyen, PARAMETER_NAME AS ten, DTD_IDENTIFIER AS kieu
     FROM information_schema.PARAMETERS WHERE SPECIFIC_SCHEMA = ? AND ROUTINE_TYPE = 'PROCEDURE'
     ORDER BY SPECIFIC_NAME, ORDINAL_POSITION`, [DB_NAME]);
  res.json(tt.map((t) => ({ ...t, tham_so: ts.filter((p) => p.thu_tuc === t.ten).map(({ kieu_truyen, ten, kieu }) => ({ kieu_truyen, ten, kieu })) })));
}));

// ---------- Mô phỏng xung đột (trang chủ) ----------
app.use('/api/mo-phong', require('./mo-phong').router);

// ---------- Lỗi ----------
app.use('/api', (req, res) => res.status(404).json({ loi: 'Không có API này' }));
app.use((err, req, res, next) => { // eslint-disable-line no-unused-vars
  const status = err.status || (err.type === 'entity.parse.failed' ? 400 : 500);
  if (status >= 500) console.error(err);
  res.status(status).json({ loi: status === 400 && err.type === 'entity.parse.failed' ? 'Dữ liệu gửi lên không hợp lệ' : giaiThichLoi(err) });
});

/** Mở web ở cổng `port`; trả về server (lỗi EADDRINUSE nếu cổng đang bị dùng). */
function batDau(port) {
  return new Promise((resolve, reject) => {
    const sv = app.listen(port, () => resolve(sv));
    sv.on('error', reject);
  });
}

/** In các địa chỉ của web ra màn hình. */
function inDiaChi(port) {
  const goc = `http://localhost:${port}`;
  console.log(`  Mô phỏng xung đột:  ${goc}/`);
  console.log(`  Đăng kí học phần:   ${goc}/dang-ki.html`);
  console.log(`  Thiết kế CSDL:      ${goc}/csdl.html`);
}

if (require.main === module) {
  const PORT = Number(process.env.PORT || 3000);
  batDau(PORT)
    .then(async () => {
      console.log('Web đã chạy:');
      inDiaChi(PORT);
      try { await layPool().query('SELECT 1 FROM sinh_vien LIMIT 1'); } catch (e) { console.error('⚠ ' + giaiThichLoi(e)); }
    })
    .catch((e) => {
      console.error(e.code === 'EADDRINUSE'
        ? `✖ Cổng ${PORT} đang bị chương trình khác dùng (thường là web cũ còn chạy). Tắt cửa sổ đó, hoặc bấm đúp chay-web.bat: nó tự chọn cổng khác.`
        : '✖ ' + e.message);
      process.exit(1);
    });
}

module.exports = { app, batDau, inDiaChi };
