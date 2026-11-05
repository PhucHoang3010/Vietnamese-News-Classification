// Định nghĩa 4 kịch bản xung đột + bộ chạy giả lập nhiều giao dịch đồng thời.
// Mỗi giao dịch Tn chạy trên 1 kết nối MySQL riêng (= 1 phiên riêng), bắt đầu lệch nhau vài trăm ms.
const { layPool, goiThuTuc } = require('./db');

const SO_LAN_THU_LAI_DEADLOCK = 3;
const ngu = (ms) => new Promise((r) => setTimeout(r, ms));

const KICH_BAN = {
  1: {
    id: 1,
    ten: 'Tranh slot',
    loai: 'Lost update (mất dữ liệu cập nhật)',
    moTa: '5 sinh viên (SV11–SV15) cùng lúc đăng kí lớp HQT.03, lớp chỉ còn 2 chỗ.',
    giaoDich: (cheDo, tre) =>
      ['SV11', 'SV12', 'SV13', 'SV14', 'SV15'].map((sv, i) => ({
        ten: `T${i + 1}`, ma_sv: sv, ma_lhp: 'HQT.03', batDauSau: i * 100,
        thuTuc: cheDo === 'loi' ? 'sp_tranh_slot_loi' : 'sp_tranh_slot_an_toan', thamSo: [sv, 'HQT.03', tre],
      })),
    async kiemTra(conn) {
      const [[l]] = await conn.query(
        `SELECT si_so_toi_da, si_so_hien_tai,
                (SELECT COUNT(*) FROM dang_ky WHERE ma_lhp = 'HQT.03') AS thuc_te,
                (SELECT GROUP_CONCAT(ma_sv ORDER BY ma_sv SEPARATOR ', ') FROM dang_ky WHERE ma_lhp = 'HQT.03') AS ds
         FROM lop_hoc_phan WHERE ma_lhp = 'HQT.03'`);
      const loi = [];
      if (l.thuc_te > l.si_so_toi_da) loi.push(`Vượt sĩ số: ${l.thuc_te} SV đăng kí > tối đa ${l.si_so_toi_da}`);
      if (l.thuc_te !== l.si_so_hien_tai) loi.push(`Lost update: cột si_so_hien_tai = ${l.si_so_hien_tai} nhưng thực tế có ${l.thuc_te} SV`);
      return {
        dung: loi.length === 0, loi,
        dong: [
          ['Sĩ số tối đa', l.si_so_toi_da],
          ['Cột si_so_hien_tai', l.si_so_hien_tai],
          ['Số dòng dang_ky thực tế (COUNT)', l.thuc_te],
          ['SV đã vào lớp', l.ds || '—'],
        ],
      };
    },
    giaiThich: {
      nguyenNhan:
        'Mỗi giao dịch ĐỌC sĩ số bằng SELECT thường (không khoá) nên cả 5 cùng thấy 0/2 → cùng kết luận "còn chỗ". ' +
        'Sau đó mỗi giao dịch GHI si_so_hien_tai = (giá trị đã đọc) + 1 = 1, ghi đè lên nhau → mất cập nhật (lost update): ' +
        '5 SV vào lớp 2 chỗ mà cột sĩ số chỉ là 1.',
      cachGiai:
        'Đọc có khoá: SELECT ... FOR UPDATE đặt khoá ghi (X) lên dòng lớp đến khi COMMIT. Giao dịch sau phải CHỜ, ' +
        'đến lượt thì đọc được sĩ số mới nhất → chỉ 2 SV đầu thành công, 3 SV sau bị từ chối "Lớp đã đủ sĩ số". ' +
        'Cách khác: UPDATE có điều kiện "SET si_so_hien_tai = si_so_hien_tai + 1 WHERE si_so_hien_tai < si_so_toi_da" rồi kiểm tra ROW_COUNT().',
      sqlLoi: `SELECT si_so_hien_tai, si_so_toi_da INTO v_si_so, v_toi_da
FROM lop_hoc_phan WHERE ma_lhp = p_ma_lhp;          -- không khoá
...
UPDATE lop_hoc_phan SET si_so_hien_tai = v_si_so + 1 WHERE ma_lhp = p_ma_lhp;`,
      sqlSua: `SELECT si_so_hien_tai, si_so_toi_da INTO v_si_so, v_toi_da
FROM lop_hoc_phan WHERE ma_lhp = p_ma_lhp
FOR UPDATE;                                          -- [SỬA] khoá X đến khi COMMIT`,
    },
  },

  2: {
    id: 2,
    ten: 'Trùng lịch đồng thời',
    loai: 'Phantom / Write skew',
    moTa: 'SV16 mở 2 tab, cùng lúc đăng kí CSDL.01 (Thứ 2, tiết 1-3) và CTDL.01 (Thứ 2, tiết 2-4) — hai lớp trùng giờ.',
    giaoDich: (cheDo, tre) =>
      [['T1', 'CSDL.01', 0], ['T2', 'CTDL.01', 300]].map(([ten, lhp, sau]) => ({
        ten, ma_sv: 'SV16', ma_lhp: lhp, batDauSau: sau,
        thuTuc: cheDo === 'loi' ? 'sp_trung_lich_loi' : 'sp_trung_lich_an_toan', thamSo: ['SV16', lhp, tre],
      })),
    async kiemTra(conn) {
      const [ds] = await conn.query(
        `SELECT d.ma_lhp, l.thu, l.tiet_bd, l.tiet_kt FROM dang_ky d JOIN lop_hoc_phan l ON l.ma_lhp = d.ma_lhp
         WHERE d.ma_sv = 'SV16' ORDER BY d.ma_lhp`);
      const [vp] = await conn.query(
        `SELECT chi_tiet FROM v_kiem_tra_toan_ven WHERE loai = 'TRUNG_LICH' AND doi_tuong = 'SV16'`);
      return {
        dung: vp.length === 0,
        loi: vp.map((v) => `Trùng lịch: ${v.chi_tiet}`),
        dong: [['Lớp SV16 đã đăng kí', ds.map((d) => `${d.ma_lhp} (Thứ ${d.thu}, tiết ${d.tiet_bd}-${d.tiet_kt})`).join('; ') || '—']],
      };
    },
    giaiThich: {
      nguyenNhan:
        'Mỗi giao dịch kiểm tra "SV16 chưa có lớp nào trùng giờ" trên dữ liệu đã COMMIT. Lúc T2 kiểm tra, dòng T1 vừa chèn chưa COMMIT nên T2 không thấy. ' +
        'Hai giao dịch chèn hai dòng KHÁC NHAU nên không đụng khoá của nhau; mỗi bên đều đúng khi xét riêng, ghép lại thì sai (write skew). ' +
        'Dòng mới của giao dịch kia là "bóng ma" (phantom) đối với điều kiện đã kiểm tra. Khoá dòng lớp học phần cũng không giúp gì vì hai bên đăng kí hai lớp khác nhau.',
      cachGiai:
        'Khoá một dòng mà mọi lần đăng kí của cùng SV đều phải đi qua: dòng sinh_vien (SELECT ... FROM sinh_vien WHERE ma_sv = ? FOR UPDATE). ' +
        'T2 phải chờ T1 COMMIT rồi mới kiểm tra, nên thấy CSDL.01 và từ chối. Lệnh khoá phải là câu ĐẦU TIÊN của giao dịch vì ở REPEATABLE READ ' +
        'snapshot được chụp ở lần SELECT thường đầu tiên; nếu đọc trước rồi mới khoá, T2 vẫn kiểm tra trên snapshot cũ.',
      sqlLoi: `START TRANSACTION;
SELECT COUNT(*) INTO v_dem FROM dang_ky d JOIN lop_hoc_phan l ON l.ma_lhp = d.ma_lhp
WHERE d.ma_sv = p_ma_sv AND l.thu = v_thu AND l.tiet_bd <= v_kt AND v_bd <= l.tiet_kt;
-- v_dem = 0 → INSERT`,
      sqlSua: `START TRANSACTION;
SELECT ma_sv INTO v_tmp FROM sinh_vien
WHERE ma_sv = p_ma_sv FOR UPDATE;                    -- [SỬA] khoá dòng cha, câu đầu tiên
SELECT COUNT(*) INTO v_dem FROM dang_ky ...          -- giờ thấy dữ liệu T1 đã COMMIT`,
    },
  },

  3: {
    id: 3,
    ten: 'Trùng học phần',
    loai: 'Phantom khi chèn',
    moTa: 'SV17 cùng lúc đăng kí HQT.01 và HQT.02: hai lớp khác giờ nhưng cùng môn Hệ quản trị CSDL.',
    giaoDich: (cheDo, tre) =>
      [['T1', 'HQT.01', 0], ['T2', 'HQT.02', 300]].map(([ten, lhp, sau]) => ({
        ten, ma_sv: 'SV17', ma_lhp: lhp, batDauSau: sau,
        thuTuc: cheDo === 'loi' ? 'sp_trung_hp_loi' : 'sp_trung_hp_an_toan', thamSo: ['SV17', lhp, tre],
      })),
    async kiemTra(conn) {
      const [ds] = await conn.query(`SELECT ma_lhp, ma_mh FROM dang_ky WHERE ma_sv = 'SV17' ORDER BY ma_lhp`);
      const [vp] = await conn.query(
        `SELECT chi_tiet FROM v_kiem_tra_toan_ven WHERE loai = 'TRUNG_HOC_PHAN' AND doi_tuong = 'SV17'`);
      return {
        dung: vp.length === 0,
        loi: vp.map((v) => `Trùng học phần: ${v.chi_tiet}`),
        dong: [['Lớp SV17 đã đăng kí', ds.map((d) => `${d.ma_lhp} (môn ${d.ma_mh})`).join('; ') || '—']],
      };
    },
    giaiThich: {
      nguyenNhan:
        'Cả hai giao dịch chạy "SELECT COUNT(*) FROM dang_ky WHERE ma_sv = ? AND ma_mh = ?", đều được 0 vì dòng của bên kia chưa COMMIT, ' +
        'rồi cả hai cùng INSERT. Ràng buộc UNIQUE(ma_sv, ma_lhp) không chặn được vì hai lớp có mã khác nhau.',
      cachGiai:
        'Nâng mức cô lập lên SERIALIZABLE. Khi đó InnoDB biến SELECT thành SELECT ... FOR SHARE và khoá cả khoảng trống (gap/next-key lock) trên index (ma_sv, ma_mh). ' +
        'Hai giao dịch cùng giữ khoá S trên khoảng đó; khi cả hai INSERT vào khoảng ấy thì chờ nhau → InnoDB phát hiện DEADLOCK (lỗi 1213) và huỷ một giao dịch. ' +
        'Ứng dụng bắt lỗi 1213 và thử lại; lần thử lại thấy SV đã có lớp HQT nên từ chối. ' +
        'Nên thêm UNIQUE(ma_sv, ma_mh) làm lớp bảo vệ cuối để chính DBMS chặn dòng trùng (lỗi 1062), xem sql/demo/3_trung_hoc_phan.sql.',
      sqlLoi: `START TRANSACTION;                                   -- REPEATABLE READ (mặc định)
SELECT COUNT(*) INTO v_dem FROM dang_ky
WHERE ma_sv = p_ma_sv AND ma_mh = v_ma_mh;           -- đọc snapshot, không khoá`,
      sqlSua: `SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;       -- [SỬA]
START TRANSACTION;
SELECT COUNT(*) INTO v_dem FROM dang_ky
WHERE ma_sv = p_ma_sv AND ma_mh = v_ma_mh;           -- khoá S + gap lock
-- ứng dụng: nếu lỗi 1213 (deadlock) → thử lại giao dịch`,
    },
  },

  4: {
    id: 4,
    ten: 'Đăng kí bị huỷ giữa chừng',
    loai: 'Dirty read (đọc dữ liệu chưa COMMIT)',
    moTa:
      'Lớp KTCT.02 còn 1 chỗ. T1: SV18 giữ chỗ trước rồi mới kiểm tra học phí, phát hiện nợ học phí nên ROLLBACK. ' +
      'T2: SV19 đăng kí cùng lớp trong lúc T1 chưa kết thúc.',
    giaoDich: (cheDo, tre) => [
      { ten: 'T1', ma_sv: 'SV18', ma_lhp: 'KTCT.02', batDauSau: 0, thuTuc: 'sp_giu_cho_roi_huy', thamSo: ['SV18', 'KTCT.02', tre] },
      {
        ten: 'T2', ma_sv: 'SV19', ma_lhp: 'KTCT.02', batDauSau: 500,
        thuTuc: cheDo === 'loi' ? 'sp_dirty_read_loi' : 'sp_dirty_read_an_toan', thamSo: ['SV19', 'KTCT.02'],
      },
    ],
    async kiemTra(conn) {
      const [[l]] = await conn.query(
        `SELECT si_so_toi_da, si_so_hien_tai,
                (SELECT GROUP_CONCAT(ma_sv) FROM dang_ky WHERE ma_lhp = 'KTCT.02') AS ds
         FROM lop_hoc_phan WHERE ma_lhp = 'KTCT.02'`);
      const sv19Vao = (l.ds || '').split(',').includes('SV19');
      const loi = [];
      if (!sv19Vao && l.si_so_hien_tai < l.si_so_toi_da) {
        loi.push(`SV19 bị từ chối "lớp đã đủ sĩ số" nhưng lớp vẫn trống ${l.si_so_hien_tai}/${l.si_so_toi_da}: T2 đã đọc dữ liệu chưa COMMIT của T1, mà T1 sau đó ROLLBACK.`);
      }
      return {
        dung: loi.length === 0, loi,
        dong: [
          ['Sĩ số KTCT.02 sau cùng', `${l.si_so_hien_tai}/${l.si_so_toi_da}`],
          ['SV trong lớp', l.ds || '—'],
        ],
      };
    },
    giaiThich: {
      nguyenNhan:
        'T2 chạy ở mức READ UNCOMMITTED nên đọc được sĩ số 1/1 mà T1 mới ghi tạm và chưa COMMIT, rồi từ chối SV19 vì tưởng lớp đã đầy. ' +
        'Sau đó T1 ROLLBACK, lớp trở lại 0/1: SV19 bị từ chối oan vì giá trị T2 đọc chưa bao giờ thực sự tồn tại.',
      cachGiai:
        'Dùng mức cô lập từ READ COMMITTED trở lên (mặc định của MySQL là REPEATABLE READ) để chỉ đọc dữ liệu đã COMMIT. ' +
        'T2 đọc được 0/1, đến bước UPDATE thì chờ khoá X của T1. T1 ROLLBACK xong, T2 kiểm tra lại điều kiện "si_so_hien_tai < si_so_toi_da" và đăng kí thành công.',
      sqlLoi: `SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
START TRANSACTION;
SELECT si_so_hien_tai ... FROM lop_hoc_phan ...;     -- đọc cả dữ liệu chưa COMMIT`,
      sqlSua: `SET TRANSACTION ISOLATION LEVEL READ COMMITTED;     -- [SỬA]
START TRANSACTION;
SELECT si_so_hien_tai ... ;                          -- chỉ thấy bản đã COMMIT
UPDATE lop_hoc_phan SET si_so_hien_tai = si_so_hien_tai + 1
WHERE ma_lhp = p_ma_lhp AND si_so_hien_tai < si_so_toi_da;   -- chờ khoá, kiểm tra lại`,
    },
  },
};

/** "2026-11-05 10:00:00.123000" → mili-giây (chỉ dùng để tính hiệu thời gian). */
const thoiDiem = (s) => Date.parse(s.replace(' ', 'T').slice(0, 23) + 'Z');

function phanTichNhatKy(nhatKy, tx, lanThu) {
  return (nhatKy || '').split('\n').filter(Boolean).map((dong) => {
    const [tg, loai, ...msg] = dong.split('|');
    return { tx, lanThu, t: thoiDiem(tg), loai, msg: msg.join('|') };
  });
}

async function chayMotGiaoDich(pool, gd) {
  await ngu(gd.batDauSau);
  const conn = await pool.getConnection();
  const cacLan = [];
  const suKien = [];
  try {
    for (let lan = 1; lan <= SO_LAN_THU_LAI_DEADLOCK; lan++) {
      const kq = await goiThuTuc(conn, gd.thuTuc, gd.thamSo);
      cacLan.push({ lan, ket_qua: kq.ket_qua, thong_bao: kq.thong_bao, ma_loi: kq.ma_loi });
      suKien.push(...phanTichNhatKy(kq.nhat_ky, gd.ten, lan));
      if (!(kq.ket_qua === 'LOI' && kq.ma_loi === 1213)) break; // chỉ thử lại khi bị deadlock
    }
  } finally {
    conn.release();
  }
  const cuoi = cacLan[cacLan.length - 1];
  return { ten: gd.ten, ma_sv: gd.ma_sv, ma_lhp: gd.ma_lhp, thuTuc: gd.thuTuc, cacLan, ket_qua: cuoi.ket_qua, thong_bao: cuoi.thong_bao, suKien };
}

let dangChay = false;

/**
 * Chạy 1 kịch bản.
 * @param {number} id 1..4
 * @param {'loi'|'an_toan'} cheDo  'loi' = không xử lý, 'an_toan' = có xử lý
 */
async function chayKichBan(id, cheDo, tre = Number(process.env.DEMO_DELAY || 2)) {
  const kb = KICH_BAN[id];
  if (!kb) throw Object.assign(new Error('Kịch bản không tồn tại'), { status: 404 });
  if (!['loi', 'an_toan'].includes(cheDo)) throw Object.assign(new Error('cheDo phải là "loi" hoặc "an_toan"'), { status: 400 });
  if (dangChay) throw Object.assign(new Error('Đang chạy một kịch bản khác, đợi vài giây'), { status: 409 });
  dangChay = true;
  const pool = layPool();
  try {
    await pool.query('CALL sp_dat_lai_kich_ban(?)', [id]);
    const dsGiaoDich = kb.giaoDich(cheDo, tre);
    const ketQua = await Promise.all(dsGiaoDich.map((gd) => chayMotGiaoDich(pool, gd)));

    const tatCa = ketQua.flatMap((k) => k.suKien).sort((a, b) => a.t - b.t);
    const t0 = tatCa.length ? tatCa[0].t : 0;
    const suKien = tatCa.map((e) => ({ ...e, t: e.t - t0 }));
    ketQua.forEach((k) => delete k.suKien);

    const conn = await pool.getConnection();
    let trangThai;
    try { trangThai = await kb.kiemTra(conn); } finally { conn.release(); }

    return { id, ten: kb.ten, cheDo, tre, giaoDich: ketQua, suKien, trangThai };
  } finally {
    dangChay = false;
  }
}

function thongTinKichBan() {
  return Object.values(KICH_BAN).map(({ id, ten, loai, moTa, giaiThich }) => ({ id, ten, loai, moTa, giaiThich }));
}

module.exports = { KICH_BAN, chayKichBan, thongTinKichBan };
