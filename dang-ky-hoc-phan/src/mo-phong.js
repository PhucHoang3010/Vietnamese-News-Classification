// API cho trang "Mô phỏng 2 sinh viên" (public/mo-phong.html):
// hai sinh viên A và B trên cùng một màn hình, mỗi lần bấm Đăng kí là một giao dịch thật trên MySQL.
const express = require('express');
const { layPool, goiThuTuc, napDuLieuMau } = require('./db');

const TINH_HUONG = {
  'tranh-slot': {
    ten: 'Tranh slot', loai: 'Lost update', lop: ['KTCT.02'],
    moTa: 'Lớp KTCT.02 chỉ còn 1 chỗ. Hai sinh viên khác nhau cùng bấm Đăng kí lớp này.',
    A: { ma_sv: 'SV09', ma_lhp: 'KTCT.02' }, B: { ma_sv: 'SV10', ma_lhp: 'KTCT.02' },
    giaiThich: {
      nguyenNhan: 'Không khoá nên A và B cùng đọc sĩ số 0/1, cùng thấy còn chỗ, rồi cùng ghi si_so_hien_tai = 0 + 1. Lớp 1 chỗ có 2 sinh viên, còn cột sĩ số chỉ là 1: lần ghi sau đè lên lần ghi trước (lost update).',
      cachSua: 'SELECT ... FROM lop_hoc_phan ... FOR UPDATE đặt khoá X lên dòng lớp đến khi COMMIT. B phải chờ A xong, đọc lại thấy 1/1 nên bị từ chối "Lớp đã đủ sĩ số".',
      sqlLoi: 'SELECT si_so_hien_tai, si_so_toi_da INTO v_si_so, v_toi_da\nFROM lop_hoc_phan WHERE ma_lhp = p_ma_lhp;      -- đọc thường\n...\nUPDATE lop_hoc_phan SET si_so_hien_tai = v_si_so + 1 ...;',
      sqlSua: 'SELECT si_so_hien_tai, si_so_toi_da INTO v_si_so, v_toi_da\nFROM lop_hoc_phan WHERE ma_lhp = p_ma_lhp\nFOR UPDATE;                                     -- khoá X đến khi COMMIT',
    },
  },
  'trung-lich': {
    ten: 'Trùng lịch đồng thời', loai: 'Write skew / phantom', lop: ['CSDL.01', 'CTDL.01'],
    moTa: 'Cùng một sinh viên mở 2 tab, đăng kí cùng lúc CSDL.01 (Thứ 2, tiết 1-3) và CTDL.01 (Thứ 2, tiết 2-4).',
    A: { ma_sv: 'SV09', ma_lhp: 'CSDL.01' }, B: { ma_sv: 'SV09', ma_lhp: 'CTDL.01' },
    giaiThich: {
      nguyenNhan: 'A và B chèn hai dòng khác nhau nên không đụng khoá của nhau. Mỗi bên kiểm tra lịch trên dữ liệu đã COMMIT, chưa thấy lớp bên kia vừa chèn, nên cả hai đều lọt (write skew). Khoá dòng lớp không giúp được vì hai bên đăng kí hai lớp khác nhau.',
      cachSua: 'Khoá dòng cha chung là sinh viên: SELECT ... FROM sinh_vien WHERE ma_sv = ? FOR UPDATE, đặt ở câu đầu tiên của giao dịch. B phải chờ A COMMIT rồi mới kiểm tra lịch, nên thấy CSDL.01 và từ chối.',
      sqlLoi: 'START TRANSACTION;\nSELECT COUNT(*) INTO v_dem FROM dang_ky d JOIN lop_hoc_phan l ...\nWHERE d.ma_sv = p_ma_sv AND l.thu = v_thu\n  AND l.tiet_bd <= v_kt AND v_bd <= l.tiet_kt;   -- không khoá',
      sqlSua: 'START TRANSACTION;\nSELECT ... FROM sinh_vien WHERE ma_sv = p_ma_sv\nFOR UPDATE;                                     -- khoá dòng cha, câu đầu tiên\nSELECT COUNT(*) INTO v_dem FROM dang_ky ...;    -- giờ thấy lớp của A',
    },
  },
  'trung-hoc-phan': {
    ten: 'Trùng học phần', loai: 'Phantom khi chèn', lop: ['CSDL.01', 'CSDL.02'],
    moTa: 'Cùng một sinh viên đăng kí cùng lúc CSDL.01 và CSDL.02: hai lớp khác giờ nhưng cùng môn Cơ sở dữ liệu.',
    A: { ma_sv: 'SV10', ma_lhp: 'CSDL.01' }, B: { ma_sv: 'SV10', ma_lhp: 'CSDL.02' },
    giaiThich: {
      nguyenNhan: 'Cả A và B kiểm tra "đã đăng kí môn CSDL chưa" trước khi bên kia chèn, đều được 0, rồi cùng chèn. UNIQUE(ma_sv, ma_lhp) không chặn được vì hai lớp có mã khác nhau.',
      cachSua: 'Khoá dòng sinh viên ở đầu giao dịch để hai lần đăng kí của cùng một sinh viên chạy lần lượt. Có thể thêm UNIQUE(ma_sv, ma_mh) làm lớp bảo vệ cuối, hoặc dùng mức SERIALIZABLE (xem kịch bản 3 ở tab Giả lập xung đột).',
      sqlLoi: 'SELECT COUNT(*) INTO v_dem FROM dang_ky\nWHERE ma_sv = p_ma_sv AND ma_mh = v_ma_mh;     -- không khoá',
      sqlSua: 'SELECT ... FROM sinh_vien WHERE ma_sv = p_ma_sv FOR UPDATE;\nSELECT COUNT(*) INTO v_dem FROM dang_ky\nWHERE ma_sv = p_ma_sv AND ma_mh = v_ma_mh;\n-- thêm: ALTER TABLE dang_ky ADD UNIQUE (ma_sv, ma_mh);',
    },
  },
  'dirty-read': {
    ten: 'Đọc dữ liệu chưa COMMIT', loai: 'Dirty read', lop: ['KTCT.02'],
    moTa: 'KTCT.02 còn 1 chỗ. A (SV18, đang nợ học phí) giữ chỗ trước rồi mới kiểm tra học phí, thấy nợ nên ROLLBACK. B (SV19) bấm Đăng kí trong lúc A chưa xong.',
    A: { ma_sv: 'SV18', ma_lhp: 'KTCT.02', vaiTro: 'Giữ chỗ trước, kiểm tra học phí sau rồi ROLLBACK' },
    B: { ma_sv: 'SV19', ma_lhp: 'KTCT.02' },
    giaiThich: {
      nguyenNhan: 'Không xử lý thì B chạy ở READ UNCOMMITTED, đọc được sĩ số 1/1 mà A mới ghi tạm, nên từ chối SV19. Sau đó A ROLLBACK, lớp về 0/1: SV19 bị từ chối oan vì con số B đọc chưa bao giờ được COMMIT.',
      cachSua: 'Dùng mức cô lập READ COMMITTED trở lên (mặc định của MySQL là REPEATABLE READ). B chỉ đọc dữ liệu đã COMMIT (0/1), đến UPDATE thì chờ khoá của A; A ROLLBACK xong, B kiểm tra lại và đăng kí thành công.',
      sqlLoi: 'SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;\nSTART TRANSACTION;\nSELECT si_so_hien_tai ...;                      -- thấy 1/1 chưa COMMIT',
      sqlSua: 'SET TRANSACTION ISOLATION LEVEL READ COMMITTED;\nSTART TRANSACTION;\nSELECT si_so_hien_tai ...;                      -- thấy 0/1 đã COMMIT\nUPDATE lop_hoc_phan SET si_so_hien_tai = si_so_hien_tai + 1\nWHERE ma_lhp = p_ma_lhp AND si_so_hien_tai < si_so_toi_da;',
    },
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

const boc = (fn) => (req, res) => fn(req, res).catch((e) => res.status(e.status || 500).json({ loi: e.message }));
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
    return { id, ten: th.ten, loai: th.loai, moTa: th.moTa, giaiThich: th.giaiThich, A: vai.A, B: vai.B };
  }));
  res.json(ds);
}));

router.post('/dat-lai', boc(async (req, res) => {
  await napDuLieuMau();
  res.json({ ok: true });
}));

// Một lần bấm Đăng kí của A hoặc B = một giao dịch trên một kết nối riêng
router.post('/giao-dich', boc(async (req, res) => {
  const { tinhHuong, vai, coXuLy = true, tre = 3 } = req.body || {};
  layTinhHuong(tinhHuong);
  if (!['A', 'B'].includes(vai)) throw Object.assign(new Error('vai phải là A hoặc B'), { status: 400 });
  const giay = Math.min(10, Math.max(0, Number(tre) || 0));
  const [ten, thamSo] = thuTucCho(tinhHuong, vai, coXuLy !== false, giay);
  const conn = await layPool().getConnection();
  try {
    const kq = await goiThuTuc(conn, ten, thamSo);
    res.json({ vai, thuTuc: ten, ket_qua: kq.ket_qua, thong_bao: kq.thong_bao, ma_loi: kq.ma_loi, suKien: phanTich(kq.nhat_ky) });
  } finally {
    conn.release();
  }
}));

// Trạng thái CSDL (dữ liệu đã COMMIT) của các lớp và sinh viên trong tình huống
router.get('/trang-thai', boc(async (req, res) => {
  const id = String(req.query.tinhHuong || '');
  const th = layTinhHuong(id);
  const pool = layPool();
  const dsSv = [...new Set([th.A.ma_sv, th.B.ma_sv])];
  const [lop] = await pool.query(
    `SELECT l.ma_lhp, m.ten_mh, l.thu, l.tiet_bd, l.tiet_kt, l.si_so_hien_tai, l.si_so_toi_da,
            (SELECT COUNT(*) FROM dang_ky d WHERE d.ma_lhp = l.ma_lhp) AS thuc_te,
            (SELECT GROUP_CONCAT(d.ma_sv ORDER BY d.ma_sv SEPARATOR ', ') FROM dang_ky d WHERE d.ma_lhp = l.ma_lhp) AS ds
     FROM lop_hoc_phan l JOIN mon_hoc m ON m.ma_mh = l.ma_mh
     WHERE l.ma_lhp IN (?) ORDER BY l.ma_lhp`, [th.lop]);
  const [dangKy] = await pool.query(
    `SELECT d.ma_sv, d.ma_lhp, d.ma_mh, l.thu, l.tiet_bd, l.tiet_kt
     FROM dang_ky d JOIN lop_hoc_phan l ON l.ma_lhp = d.ma_lhp
     WHERE d.ma_sv IN (?) ORDER BY d.ma_sv, l.thu, l.tiet_bd`, [dsSv]);
  const [viPham] = await pool.query(
    'SELECT loai, doi_tuong, chi_tiet FROM v_kiem_tra_toan_ven WHERE doi_tuong IN (?) ORDER BY loai',
    [[...th.lop, ...dsSv]]);
  const loi = viPham.map((v) => `${v.doi_tuong}: ${v.chi_tiet}`);
  if (id === 'dirty-read') {
    const l = lop[0];
    const coB = (l.ds || '').split(', ').includes(th.B.ma_sv);
    if (!coB && l.si_so_hien_tai < l.si_so_toi_da) {
      loi.push(`${th.B.ma_sv} không vào được lớp dù ${l.ma_lhp} vẫn còn chỗ (${l.si_so_hien_tai}/${l.si_so_toi_da}): bị từ chối oan vì đã đọc dữ liệu chưa COMMIT của A`);
    }
  }
  res.json({ lop, dangKy, viPham, loi, dung: loi.length === 0 });
}));

module.exports = { router, TINH_HUONG };
