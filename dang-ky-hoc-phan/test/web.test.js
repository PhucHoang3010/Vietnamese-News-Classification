// Kiểm thử qua HTTP đúng như trang web gọi: 4 tình huống xung đột × 2 chế độ, và các API còn lại.
// Cần MySQL đang chạy và đã `npm run db:init`. Test sẽ nạp lại dữ liệu mẫu.
const test = require('node:test');
const assert = require('node:assert/strict');
const { batDau } = require('../src/server');
const { dongPool, napDuLieuMau } = require('../src/db');

const TRE = 1; // giây xử lý chậm trong thủ tục
let server, goc;

test.before(async () => {
  server = await batDau(0);
  goc = `http://127.0.0.1:${server.address().port}`;
});
test.after(async () => {
  await napDuLieuMau();
  await new Promise((r) => server.close(r));
  await dongPool();
});

async function goi(duongDan, body) {
  const res = await fetch(goc + duongDan, body === undefined ? {} : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  });
  return { status: res.status, data: await res.json() };
}
const ngu = (ms) => new Promise((r) => setTimeout(r, ms));

/** Thời gian B phải chờ khoá: từ sự kiện LOCK tới bước kế tiếp (giống trang web tính). */
const thoiGianCho = (sk) => sk.reduce((t, e, i) => (e.loai === 'LOCK' && sk[i + 1] ? t + Math.max(0, sk[i + 1].t - e.t) : t), 0);

/** Đặt lại, cho A bấm rồi B bấm sau `lech` ms, trả về kết quả hai bên và kết luận như trang web. */
async function chay(tinhHuong, coXuLy, lech = 300) {
  assert.equal((await goi('/api/mo-phong/dat-lai', {})).status, 200);
  const [a, b] = await Promise.all([
    goi('/api/mo-phong/giao-dich', { tinhHuong, vai: 'A', coXuLy, tre: TRE }),
    ngu(lech).then(() => goi('/api/mo-phong/giao-dich', { tinhHuong, vai: 'B', coXuLy, tre: TRE })),
  ]);
  const tt = (await goi(`/api/mo-phong/trang-thai?tinhHuong=${tinhHuong}`)).data;
  let dung = tt.dung;
  if (tinhHuong === 'dirty-read' && b.data.ket_qua !== 'THANH_CONG') {
    const l = tt.lop[0];
    if (l.thuc_te < l.si_so_toi_da) dung = false; // SV19 bị từ chối oan
  }
  return { A: a.data, B: b.data, tt, dung };
}

test('Tranh slot · Tắt: lớp 1 chỗ có 2 sinh viên, sĩ số lưu sai', async () => {
  const kq = await chay('tranh-slot', false);
  assert.equal(kq.A.ket_qua, 'THANH_CONG');
  assert.equal(kq.B.ket_qua, 'THANH_CONG');
  assert.equal(kq.dung, false);
  assert.deepEqual(kq.tt.viPham.map((v) => v.loai).sort(), ['SAI_SI_SO', 'VUOT_SI_SO']);
});
test('Tranh slot · Bật: B chờ khoá rồi bị báo hết chỗ', async () => {
  const kq = await chay('tranh-slot', true);
  assert.equal(kq.A.ket_qua, 'THANH_CONG');
  assert.match(kq.B.thong_bao, /đủ sĩ số/);
  assert.ok(thoiGianCho(kq.B.suKien) >= 400, 'B phải chờ khoá của A');
  assert.equal(kq.dung, true, kq.tt.loi.join('; '));
});

test('Trùng lịch · Tắt: SV09 có 2 lớp cùng giờ', async () => {
  const kq = await chay('trung-lich', false);
  assert.equal(kq.B.ket_qua, 'THANH_CONG');
  assert.equal(kq.dung, false);
  assert.ok(kq.tt.viPham.some((v) => v.loai === 'TRUNG_LICH'));
});
test('Trùng lịch · Bật: tab 2 chờ rồi bị từ chối vì trùng lịch', async () => {
  const kq = await chay('trung-lich', true);
  assert.equal(kq.A.ket_qua, 'THANH_CONG');
  assert.match(kq.B.thong_bao, /Trùng lịch với lớp CSDL\.01/);
  assert.ok(thoiGianCho(kq.B.suKien) >= 400);
  assert.equal(kq.dung, true, kq.tt.loi.join('; '));
});

test('SV đăng kí · Tắt: SV19 bị từ chối oan dù lớp còn chỗ', async () => {
  const kq = await chay('dirty-read', false, 400);
  assert.match(kq.A.thong_bao, /nợ học phí/);
  assert.match(kq.B.thong_bao, /đủ sĩ số/);
  assert.equal(kq.tt.lop[0].thuc_te, 0);
  assert.equal(kq.dung, false);
});
test('SV đăng kí · Bật: SV19 chờ SV18 huỷ rồi đăng kí được', async () => {
  const kq = await chay('dirty-read', true, 400);
  assert.equal(kq.A.ket_qua, 'TU_CHOI');
  assert.equal(kq.B.ket_qua, 'THANH_CONG');
  assert.ok(thoiGianCho(kq.B.suKien) >= 300);
  assert.equal(kq.tt.lop[0].thuc_te, 1);
  assert.equal(kq.dung, true, kq.tt.loi.join('; '));
});

test('Trùng học phần · Tắt: SV10 có 2 lớp cùng môn', async () => {
  const kq = await chay('trung-hoc-phan', false);
  assert.equal(kq.B.ket_qua, 'THANH_CONG');
  assert.equal(kq.dung, false);
  assert.ok(kq.tt.viPham.some((v) => v.loai === 'TRUNG_HOC_PHAN'));
});
test('Trùng học phần · Bật: lớp thứ hai bị từ chối', async () => {
  const kq = await chay('trung-hoc-phan', true);
  assert.equal(kq.A.ket_qua, 'THANH_CONG');
  assert.match(kq.B.thong_bao, /Trùng học phần/);
  assert.equal(kq.dung, true, kq.tt.loi.join('; '));
});

test('Mỗi tình huống chỉ bấm một bên thì dữ liệu luôn đúng', async () => {
  for (const id of ['tranh-slot', 'trung-lich', 'dirty-read', 'trung-hoc-phan']) {
    for (const vai of ['A', 'B']) {
      await goi('/api/mo-phong/dat-lai', {});
      await goi('/api/mo-phong/giao-dich', { tinhHuong: id, vai, coXuLy: false, tre: 0 });
      const tt = (await goi(`/api/mo-phong/trang-thai?tinhHuong=${id}`)).data;
      assert.equal(tt.dung, true, `${id}/${vai}: ${tt.loi.join('; ')}`);
    }
  }
});

test('API đăng kí: kiểm tra dữ liệu gửi lên và báo lỗi rõ ràng', async () => {
  await napDuLieuMau();
  assert.equal((await goi('/api/dang-ky', { ma_sv: 1 })).status, 400);
  assert.equal((await goi('/api/dang-ky', { ma_sv: 'SV01; DROP', ma_lhp: 'CSDL.01' })).status, 400);
  assert.equal((await goi('/api/mo-phong/giao-dich', { tinhHuong: 'khong-co', vai: 'A' })).status, 404);
  assert.equal((await goi('/api/mo-phong/giao-dich', { tinhHuong: 'tranh-slot', vai: 'C' })).status, 400);
  assert.equal((await goi('/api/khong-co')).status, 404);
  const ok = await goi('/api/dang-ky', { ma_sv: 'SV07', ma_lhp: 'MMT.01' });
  assert.equal(ok.data.ket_qua, 'THANH_CONG');
  assert.match((await goi('/api/dang-ky', { ma_sv: 'SV07', ma_lhp: 'MMT.01' })).data.thong_bao, /đã đăng kí lớp này/);
  assert.equal((await goi('/api/huy-dang-ky', { ma_sv: 'SV07', ma_lhp: 'MMT.01' })).data.ket_qua, 'THANH_CONG');
  assert.deepEqual((await goi('/api/kiem-tra')).data, []);
});

test('Trang Thiết kế CSDL: lược đồ đủ khoá chính, khoá ngoại; thủ tục có mô tả', async () => {
  const ld = (await goi('/api/luoc-do')).data;
  assert.deepEqual(ld.map((b) => b.ten), ['sinh_vien', 'mon_hoc', 'lop_hoc_phan', 'dang_ky']);
  const pk = Object.fromEntries(ld.map((b) => [b.ten, b.cot.filter((c) => c.khoa_chinh).map((c) => c.ten)]));
  assert.deepEqual(pk, { sinh_vien: ['ma_sv'], mon_hoc: ['ma_mh'], lop_hoc_phan: ['ma_lhp'], dang_ky: ['id'] });
  const dk = ld.find((b) => b.ten === 'dang_ky');
  assert.deepEqual(dk.cot.filter((c) => c.khoa_ngoai.length).map((c) => `${c.ten}→${c.khoa_ngoai}`),
    ['ma_sv→sinh_vien(ma_sv)', 'ma_lhp→lop_hoc_phan(ma_lhp)', 'ma_mh→lop_hoc_phan(ma_mh)']);
  assert.ok(ld.every((b) => b.ghi_chu && b.cot.every((c) => c.ghi_chu)), 'bảng và cột nào cũng có chú thích');
  const tt = (await goi('/api/thu-tuc')).data;
  assert.equal(tt.length, 14);
  assert.ok(tt.every((t) => t.ghi_chu), 'thủ tục nào cũng có COMMENT');
  for (const trang of ['/', '/dang-ki.html', '/csdl.html', '/giao-dien.css', '/docs/erd-chen.svg']) {
    assert.equal((await fetch(goc + trang)).status, 200, trang);
  }
});
