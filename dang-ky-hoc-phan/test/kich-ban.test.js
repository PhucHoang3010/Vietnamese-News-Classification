// npm test — cần MySQL đang chạy và đã `npm run db:init`. Test sẽ nạp lại dữ liệu mẫu.
const test = require('node:test');
const assert = require('node:assert/strict');
const { layPool, dongPool, goiThuTuc, napDuLieuMau } = require('../src/db');
const { chayKichBan } = require('../src/kich-ban');

const TRE = 0.6;

async function goi(ten, thamSo) {
  const conn = await layPool().getConnection();
  try { return await goiThuTuc(conn, ten, thamSo); } finally { conn.release(); }
}

test.before(napDuLieuMau);
test.after(async () => { await napDuLieuMau(); await dongPool(); });

for (const id of [1, 2, 3, 4]) {
  test(`KB${id}: KHÔNG xử lý → phát sinh xung đột`, async () => {
    const kq = await chayKichBan(id, 'loi', TRE);
    assert.equal(kq.trangThai.dung, false, kq.trangThai.loi.join('; '));
  });
  test(`KB${id}: CÓ xử lý → dữ liệu đúng`, async () => {
    const kq = await chayKichBan(id, 'an_toan', TRE);
    assert.equal(kq.trangThai.dung, true, kq.trangThai.loi.join('; '));
  });
}

test('KB1 có xử lý: đúng 2/5 SV vào lớp 2 chỗ', async () => {
  const kq = await chayKichBan(1, 'an_toan', TRE);
  assert.equal(kq.giaoDich.filter((g) => g.ket_qua === 'THANH_CONG').length, 2);
});

test('KB3 cách 2: UNIQUE(ma_sv, ma_mh) chặn dòng trùng bằng lỗi 1062', async () => {
  const pool = layPool();
  await pool.query('CALL sp_dat_lai_kich_ban(3)');
  await pool.query('ALTER TABLE dang_ky ADD CONSTRAINT uq_dk_sv_mh UNIQUE (ma_sv, ma_mh)');
  try {
    const [a, b] = await Promise.all([
      goi('sp_trung_hp_loi', ['SV17', 'HQT.01', TRE]),
      new Promise((r) => setTimeout(r, 200)).then(() => goi('sp_trung_hp_loi', ['SV17', 'HQT.02', TRE])),
    ]);
    assert.equal(a.ket_qua, 'THANH_CONG');
    assert.equal(b.ma_loi, 1062);
  } finally {
    await pool.query('ALTER TABLE dang_ky DROP INDEX uq_dk_sv_mh');
  }
});

test('sp_dang_ky: kiểm tra các quy tắc nghiệp vụ', async () => {
  await napDuLieuMau();
  const kq = async (sv, lhp) => (await goi('sp_dang_ky', [sv, lhp])).thong_bao;
  assert.match(await kq('SV01', 'CSDL.01'), /đã đăng kí lớp này/);
  assert.match(await kq('SV01', 'CSDL.02'), /Trùng học phần/);
  assert.match(await kq('SV01', 'CTDL.01'), /Trùng lịch với lớp CSDL.01/);
  assert.match(await kq('SV06', 'PLDC.01'), /đủ sĩ số/);
  assert.match(await kq('SV08', 'MMT.01'), /nợ học phí/);
  assert.equal(await kq('SV07', 'MMT.01'), 'Đăng kí thành công');
  assert.equal(await kq('SV07', 'HDH.01'), 'Đăng kí thành công');          // 4 + 4 = 8 TC (tối đa 8)
  assert.match(await kq('SV07', 'CTDL.02'), /Vượt số tín chỉ tối đa \(8 \+ 4 > 8\)/);
  assert.equal((await goi('sp_huy_dang_ky', ['SV07', 'MMT.01'])).ket_qua, 'THANH_CONG');
  assert.match((await goi('sp_huy_dang_ky', ['SV07', 'MMT.01'])).thong_bao, /chưa đăng kí/);
});

test('sp_dang_ky an toàn khi bấm đồng thời (tranh slot, trùng lịch, trùng học phần)', async () => {
  await napDuLieuMau();
  const pool = layPool();
  const dongThoi = (ds) => Promise.all(ds.map(([sv, lhp]) => goi('sp_dang_ky', [sv, lhp])));

  // 6 SV tranh lớp HQT.03 (2 chỗ)
  const r1 = await dongThoi(['SV01', 'SV02', 'SV03', 'SV09', 'SV10', 'SV11'].map((sv) => [sv, 'HQT.03']));
  assert.equal(r1.filter((r) => r.ket_qua === 'THANH_CONG').length, 2); // SV01 còn bị chặn vì đã học môn HQT
  // SV09 đăng kí 2 lớp trùng giờ cùng lúc, SV10 đăng kí 2 lớp cùng môn cùng lúc
  await dongThoi([['SV09', 'CSDL.01'], ['SV09', 'CTDL.01'], ['SV10', 'XSTK.01'], ['SV10', 'XSTK.02']]);

  const [vp] = await pool.query('SELECT * FROM v_kiem_tra_toan_ven');
  assert.deepEqual(vp, []);
});

test('Trang đăng kí: sp_dang_ky_mo_phong KHÔNG xử lý gây lỗi, CÓ xử lý thì không', async () => {
  const pool = layPool();
  const haiCuaSo = (coXuLy) => Promise.all([
    goi('sp_dang_ky_mo_phong', ['SV09', 'KTCT.02', coXuLy, TRE]),
    new Promise((r) => setTimeout(r, 150)).then(() => goi('sp_dang_ky_mo_phong', ['SV10', 'KTCT.02', coXuLy, TRE])),
  ]);
  await napDuLieuMau();
  await haiCuaSo(false);
  const [vp1] = await pool.query("SELECT loai FROM v_kiem_tra_toan_ven WHERE doi_tuong = 'KTCT.02' ORDER BY loai");
  assert.deepEqual(vp1.map((v) => v.loai), ['SAI_SI_SO', 'VUOT_SI_SO']);

  await napDuLieuMau();
  const [a, b] = await haiCuaSo(true);
  assert.equal(a.ket_qua, 'THANH_CONG');
  assert.equal(b.thong_bao, 'Lớp đã đủ sĩ số');
  const [vp2] = await pool.query('SELECT * FROM v_kiem_tra_toan_ven');
  assert.deepEqual(vp2, []);
});
