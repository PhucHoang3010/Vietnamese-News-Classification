// Web server: trang đăng kí học phần + API giả lập xung đột
const path = require('path');
const express = require('express');
const { layPool, goiThuTuc, napDuLieuMau, giaiThichLoi } = require('./db');
const { chayKichBan, thongTinKichBan } = require('./kich-ban');

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, '..', 'public'), { index: 'mo-phong.html' })); // trang chính = trang demo
app.use('/docs', express.static(path.join(__dirname, '..', 'docs')));

const boc = (fn) => (req, res) =>
  fn(req, res).catch((e) => res.status(e.status || 500).json({ loi: giaiThichLoi(e) }));

// ---------- Dữ liệu cho trang đăng kí ----------
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

// coXuLy: true = có xử lý đồng thời (khoá), false = không xử lý; tre: số giây xử lý chậm (0..10)
app.post('/api/dang-ky', boc(async (req, res) => {
  const { ma_sv, ma_lhp, coXuLy = true, tre = 0 } = req.body || {};
  const giay = Math.min(10, Math.max(0, Number(tre) || 0));
  const conn = await layPool().getConnection();
  try {
    res.json(await goiThuTuc(conn, 'sp_dang_ky_mo_phong', [ma_sv, ma_lhp, coXuLy !== false, giay]));
  } finally { conn.release(); }
}));

app.post('/api/huy-dang-ky', boc(async (req, res) => {
  const { ma_sv, ma_lhp } = req.body || {};
  const conn = await layPool().getConnection();
  try { res.json(await goiThuTuc(conn, 'sp_huy_dang_ky', [ma_sv, ma_lhp])); } finally { conn.release(); }
}));

app.get('/api/kiem-tra', boc(async (req, res) => {
  const [rows] = await layPool().query('SELECT * FROM v_kiem_tra_toan_ven ORDER BY loai, doi_tuong');
  res.json(rows);
}));

app.post('/api/du-lieu-mau', boc(async (req, res) => {
  await napDuLieuMau();
  res.json({ ok: true });
}));

// ---------- Xem dữ liệu thô các bảng (tab "Thiết kế CSDL") ----------
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

// ---------- Giả lập xung đột ----------
app.get('/api/kich-ban', (req, res) => res.json(thongTinKichBan()));

app.post('/api/kich-ban/:id/chay', boc(async (req, res) => {
  res.json(await chayKichBan(Number(req.params.id), (req.body || {}).cheDo));
}));

app.post('/api/kich-ban/:id/dat-lai', boc(async (req, res) => {
  await layPool().query('CALL sp_dat_lai_kich_ban(?)', [Number(req.params.id)]);
  res.json({ ok: true });
}));

// ---------- Trang mô phỏng 2 sinh viên trên một màn hình ----------
app.use('/api/mo-phong', require('./mo-phong').router);

/** Mở web ở cổng `port`; trả về server (lỗi EADDRINUSE nếu cổng đang bị dùng). */
function batDau(port) {
  return new Promise((resolve, reject) => {
    const sv = app.listen(port, () => resolve(sv));
    sv.on('error', reject);
  });
}

if (require.main === module) {
  const PORT = Number(process.env.PORT || 3000);
  batDau(PORT)
    .then(async () => {
      console.log(`Trang demo:              http://localhost:${PORT}`);
      console.log(`Trang đăng kí đầy đủ:    http://localhost:${PORT}/day-du.html`);
      try { await layPool().query('SELECT 1 FROM sinh_vien LIMIT 1'); } catch (e) { console.error('⚠ ' + giaiThichLoi(e)); }
    })
    .catch((e) => {
      console.error(e.code === 'EADDRINUSE'
        ? `✖ Cổng ${PORT} đang bị chương trình khác dùng (thường là web cũ còn chạy). Tắt cửa sổ đó, hoặc bấm đúp chay-web.bat: nó tự chọn cổng khác.`
        : '✖ ' + e.message);
      process.exit(1);
    });
}

module.exports = { app, batDau };
