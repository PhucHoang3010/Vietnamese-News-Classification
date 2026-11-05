// npm run demo [số kịch bản] — chạy giả lập ngay trên terminal (không cần mở web)
//   npm run demo        → chạy cả 4 kịch bản, mỗi kịch bản 2 chế độ
//   npm run demo -- 2   → chỉ kịch bản 2
const { chayKichBan, KICH_BAN } = require('./kich-ban');
const { dongPool } = require('./db');

const TEN_CHE_DO = { loi: 'KHÔNG xử lý', an_toan: 'CÓ xử lý' };

function inKetQua(kq) {
  console.log(`\n=== KB${kq.id} · ${kq.ten} · ${TEN_CHE_DO[kq.cheDo]} ===`);
  for (const e of kq.suKien) {
    const lan = e.lanThu > 1 ? ` (lần ${e.lanThu})` : '';
    console.log(`  +${(e.t / 1000).toFixed(3)}s  ${e.tx}${lan}  ${e.loai.padEnd(8)} ${e.msg}`);
  }
  for (const g of kq.giaoDich) {
    const thuLai = g.cacLan.length > 1 ? ` [${g.cacLan.length} lần, có deadlock]` : '';
    console.log(`  → ${g.ten} ${g.ma_sv} ${g.ma_lhp}: ${g.ket_qua} — ${g.thong_bao}${thuLai}`);
  }
  for (const [k, v] of kq.trangThai.dong) console.log(`    ${k}: ${v}`);
  console.log(kq.trangThai.dung ? '  ✅ DỮ LIỆU ĐÚNG' : `  ❌ XUNG ĐỘT: ${kq.trangThai.loi.join(' | ')}`);
}

(async () => {
  const chon = process.argv[2] ? [Number(process.argv[2])] : Object.keys(KICH_BAN).map(Number);
  try {
    for (const id of chon) for (const cheDo of ['loi', 'an_toan']) inKetQua(await chayKichBan(id, cheDo));
  } catch (e) {
    console.error('Lỗi:', e.message);
    process.exitCode = 1;
  } finally {
    await dongPool();
  }
})();
