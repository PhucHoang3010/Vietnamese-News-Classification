// API cho trang chủ "Mô phỏng xung đột" (public/index.html):
// hai sinh viên A và B trên cùng một màn hình, mỗi lần bấm Đăng kí là một giao dịch thật trên MySQL.
//   Tranh slot, Trùng lịch, Trùng học phần: cùng gọi sp_dang_ky_mo_phong(sv, lớp, co_xu_ly, tre)
//   SV đăng kí: A gọi sp_giu_cho_roi_huy, B gọi sp_dirty_read_loi / sp_dirty_read_an_toan
const express = require('express');
const { layPool, goiThuTuc, napDuLieuMau } = require('./db');

const TINH_HUONG = {
  'tranh-slot': {
    ten: 'Tranh slot', loai: 'Lost update', lop: ['KTCT.02'],
    moTa: 'Lớp KTCT.02 chỉ còn 1 chỗ. Hai sinh viên khác nhau cùng bấm Đăng kí lớp này.',
    A: { ma_sv: 'SV09', ma_lhp: 'KTCT.02' }, B: { ma_sv: 'SV10', ma_lhp: 'KTCT.02' },
  },
  'trung-lich': {
    ten: 'Trùng lịch đồng thời', loai: 'Write skew / phantom', lop: ['CSDL.01', 'CTDL.01'],
    moTa: 'Cùng một sinh viên mở 2 tab, đăng kí cùng lúc CSDL.01 (Thứ 2, tiết 1-3) và CTDL.01 (Thứ 2, tiết 2-4).',
    A: { ma_sv: 'SV09', ma_lhp: 'CSDL.01' }, B: { ma_sv: 'SV09', ma_lhp: 'CTDL.01' },
  },
  'trung-hoc-phan': {
    ten: 'Trùng học phần', loai: 'Phantom khi chèn', lop: ['CSDL.01', 'CSDL.02'],
    moTa: 'Cùng một sinh viên đăng kí cùng lúc CSDL.01 và CSDL.02: hai lớp khác giờ nhưng cùng môn Cơ sở dữ liệu.',
    A: { ma_sv: 'SV10', ma_lhp: 'CSDL.01' }, B: { ma_sv: 'SV10', ma_lhp: 'CSDL.02' },
  },
  'dirty-read': {
    ten: 'SV đăng kí', loai: 'Dirty read', lop: ['KTCT.02'],
    moTa: 'KTCT.02 còn 1 chỗ. A (SV18, đang nợ học phí) giữ chỗ trước rồi mới kiểm tra học phí, thấy nợ nên ROLLBACK. B (SV19) bấm Đăng kí trong lúc A chưa xong.',
    A: { ma_sv: 'SV18', ma_lhp: 'KTCT.02', vaiTro: 'Giữ chỗ trước, kiểm tra học phí sau rồi ROLLBACK' },
    B: { ma_sv: 'SV19', ma_lhp: 'KTCT.02' },
  },
};

function thuTucCho(id, vai, coXuLy, tre) {
  const g = TINH_HUONG[id][vai];
  if (id === 'dirty-read') {
    if (vai === 'A') return ['sp_giu_cho_roi_huy', [g.ma_sv, g.ma_lhp, tre]];
    return [coXuLy ? 'sp_dirty_read_an_toan' : 'sp_dirty_read_loi', [g.ma_sv, g.ma_lhp]];
  }
  return ['sp_dang_ky_mo_phong', [g.ma_sv, g.ma_lhp, coXuLy, tre]];
}

const thoiDiem = (s) => Date.parse(s.replace(' ', 'T').slice(0, 23) + 'Z');
const phanTich = (nhatKy) => (nhatKy || '').split('\n').filter(Boolean).map((d) => {
  const [tg, loai, ...msg] = d.split('|');
  return { t: thoiDiem(tg), loai, msg: msg.join('|') };
});

const boc = (fn) => (req, res, next) => fn(req, res).catch(next); // lỗi do server.js trả về dạng JSON
const layTinhHuong = (id) => {
  const th = TINH_HUONG[id];
  if (!th) throw Object.assign(new Error('Tình huống không tồn tại'), { status: 404 });
  return th;
};

const router = express.Router();

router.get('/tinh-huong', boc(async (req, res) => {
  const pool = layPool();
  const ds = await Promise.all(Object.entries(TINH_HUONG).map(async ([id, th]) => {
    const vai = {};
    for (const v of ['A', 'B']) {
      const [[r]] = await pool.query(
        `SELECT s.ho_ten, l.ma_lhp, m.ten_mh, l.thu, l.tiet_bd, l.tiet_kt
         FROM sinh_vien s, lop_hoc_phan l JOIN mon_hoc m ON m.ma_mh = l.ma_mh
         WHERE s.ma_sv = ? AND l.ma_lhp = ?`, [th[v].ma_sv, th[v].ma_lhp]);
      vai[v] = { ...th[v], ...r };
    }
    return { id, ten: th.ten, loai: th.loai, moTa: th.moTa, A: vai.A, B: vai.B };
  }));
  res.json(ds);
}));

// Đặt lại dữ liệu lần lượt từng yêu cầu một (bấm nhanh nhiều lần không bị chồng nhau)
let hangDoi = Promise.resolve();
const tuanTu = (fn) => { const p = hangDoi.then(fn, fn); hangDoi = p.catch(() => {}); return p; };

router.post('/dat-lai', boc(async (req, res) => {
  await tuanTu(() => napDuLieuMau());
  res.json({ ok: true });
}));

// Một lần bấm Đăng kí của A hoặc B = một giao dịch trên một kết nối riêng
router.post('/giao-dich', boc(async (req, res) => {
  const { tinhHuong, vai, coXuLy = true, tre = 3 } = req.body || {};
  layTinhHuong(tinhHuong);
  if (!['A', 'B'].includes(vai)) throw Object.assign(new Error('vai phải là A hoặc B'), { status: 400 });
  const giay = Math.min(10, Math.max(0, Number(tre) || 0)); // giới hạn 0..10 giây
  const [ten, thamSo] = thuTucCho(tinhHuong, vai, coXuLy !== false, giay);
  const conn = await layPool().getConnection();
  try {
    const kq = await goiThuTuc(conn, ten, thamSo);
    res.json({ vai, thuTuc: ten, ket_qua: kq.ket_qua, thong_bao: kq.thong_bao, ma_loi: kq.ma_loi, suKien: phanTich(kq.nhat_ky) });
  } finally {
    conn.release();
  }
}));

// Trạng thái CSDL (dữ liệu đã COMMIT) của các lớp và sinh viên trong tình huống.
// dung = view v_kiem_tra_toan_ven không báo vi phạm nào liên quan; riêng tình huống SV đăng kí,
// trang web còn xét thêm SV19 có bị từ chối oan không (lớp vẫn còn chỗ mà SV19 bị báo đầy).
router.get('/trang-thai', boc(async (req, res) => {
  const id = String(req.query.tinhHuong || '');
  const th = layTinhHuong(id);
  const pool = layPool();
  const dsSv = [...new Set([th.A.ma_sv, th.B.ma_sv])];
  const [lop] = await pool.query(
    `SELECT l.ma_lhp, m.ten_mh, m.so_tin_chi, l.giang_vien, l.phong, l.thu, l.tiet_bd, l.tiet_kt, l.si_so_hien_tai, l.si_so_toi_da,
            (SELECT COUNT(*) FROM dang_ky d WHERE d.ma_lhp = l.ma_lhp) AS thuc_te,
            (SELECT GROUP_CONCAT(d.ma_sv ORDER BY d.ma_sv SEPARATOR ', ') FROM dang_ky d WHERE d.ma_lhp = l.ma_lhp) AS ds
     FROM lop_hoc_phan l JOIN mon_hoc m ON m.ma_mh = l.ma_mh
     WHERE l.ma_lhp IN (?) ORDER BY l.ma_lhp`, [th.lop]);
  const [dangKy] = await pool.query(
    `SELECT d.ma_sv, d.ma_lhp, d.ma_mh, m.ten_mh, m.so_tin_chi, l.phong, l.thu, l.tiet_bd, l.tiet_kt
     FROM dang_ky d JOIN lop_hoc_phan l ON l.ma_lhp = d.ma_lhp JOIN mon_hoc m ON m.ma_mh = d.ma_mh
     WHERE d.ma_sv IN (?) ORDER BY d.ma_sv, l.thu, l.tiet_bd`, [dsSv]);
  const [sinhVien] = await pool.query(
    `SELECT s.ma_sv, s.ho_ten, s.lop, s.tin_chi_toi_da, s.no_hoc_phi, IFNULL(SUM(m.so_tin_chi), 0) AS so_tc
     FROM sinh_vien s LEFT JOIN dang_ky d ON d.ma_sv = s.ma_sv LEFT JOIN mon_hoc m ON m.ma_mh = d.ma_mh
     WHERE s.ma_sv IN (?) GROUP BY s.ma_sv`, [dsSv]);
  const [viPham] = await pool.query(
    'SELECT loai, doi_tuong, chi_tiet FROM v_kiem_tra_toan_ven WHERE doi_tuong IN (?) ORDER BY loai',
    [[...th.lop, ...dsSv]]);
  const loi = viPham.map((v) => `${v.doi_tuong}: ${v.chi_tiet}`);
  res.json({ lop, dangKy, sinhVien: sinhVien.map((x) => ({ ...x, so_tc: Number(x.so_tc), no_hoc_phi: !!x.no_hoc_phi })), viPham, loi, dung: loi.length === 0 });
}));

module.exports = { router, TINH_HUONG };
