// ===== Tiện ích =====
const $ = (s, el = document) => el.querySelector(s);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const tenThu = (t) => (Number(t) === 8 ? 'CN' : `Thứ ${t}`);
const lich = (l) => `${tenThu(l.thu)}, tiết ${l.tiet_bd}-${l.tiet_kt}`;
const trungGio = (a, b) => a.thu === b.thu && a.tiet_bd <= b.tiet_kt && b.tiet_bd <= a.tiet_kt;

async function api(url, body) {
  const res = await fetch(url, body === undefined ? {} : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.loi || `HTTP ${res.status}`);
  return data;
}

let toastTimer;
function toast(msg, kieu = '') {
  const el = $('#toast');
  el.textContent = msg;
  el.className = `toast ${kieu}`;
  el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (el.hidden = true), 3500);
}

// ===== Tabs =====
document.querySelectorAll('.tab').forEach((b) => b.addEventListener('click', () => {
  document.querySelectorAll('.tab').forEach((x) => x.classList.toggle('active', x === b));
  document.querySelectorAll('.tab-panel').forEach((p) => (p.hidden = p.id !== `tab-${b.dataset.tab}`));
  if (b.dataset.tab === 'dang-ky') taiLai();
  if (b.dataset.tab === 'csdl') taiDsBang();
}));

// ===== TAB 1: ĐĂNG KÍ =====
// SV đang chọn lưu theo từng cửa sổ (sessionStorage) để 2 cửa sổ đóng vai 2 SV khác nhau;
// chế độ mô phỏng lưu chung (localStorage) để mọi cửa sổ cùng một chế độ.
const kho = (loai) => ({
  get: (k) => { try { return window[loai].getItem(k); } catch { return null; } },
  set: (k, v) => { try { window[loai].setItem(k, v); } catch { /* bỏ qua */ } },
});
const cuaSo = kho('sessionStorage'), chung = kho('localStorage');
const st = {
  sv: [], lop: [], daDk: [], maSv: cuaSo.get('ma_sv') || 'SV01', dangXuLy: new Set(),
  coXuLy: chung.get('co_xu_ly') !== '0', tre: Number(chung.get('tre') || 0),
};
let khoaDsSv = '';

async function taiLai() {
  const [sv, lop, kt] = await Promise.all([api('/api/sinh-vien'), api('/api/lop-hoc-phan'), api('/api/kiem-tra')]);
  st.sv = sv; st.lop = lop;
  if (!sv.some((s) => s.ma_sv === st.maSv)) st.maSv = sv[0]?.ma_sv;
  st.daDk = st.maSv ? await api(`/api/sinh-vien/${encodeURIComponent(st.maSv)}/dang-ky`) : [];
  veChonSv(); veThongTinSv(); veBangLop(); veDaDk(); veTkb(); veKiemTra(kt);
}

function veChonSv() {
  const sel = $('#chon-sv');
  const khoa = st.sv.map((s) => s.ma_sv).join() + '|' + st.maSv;
  if (khoa === khoaDsSv) return; // không vẽ lại khi không đổi (tránh đóng dropdown đang mở)
  khoaDsSv = khoa;
  sel.innerHTML = st.sv.map((s) => `<option value="${esc(s.ma_sv)}" ${s.ma_sv === st.maSv ? 'selected' : ''}>${esc(s.ma_sv)} — ${esc(s.ho_ten)}</option>`).join('');
}

function veThongTinSv() {
  const s = st.sv.find((x) => x.ma_sv === st.maSv);
  if (!s) return ($('#sv-info').innerHTML = '');
  $('#sv-info').innerHTML = `Lớp <b>${esc(s.lop)}</b> · Đã đăng kí <b>${s.so_lop}</b> lớp · <b>${s.so_tc}/${s.tin_chi_toi_da}</b> tín chỉ`
    + (s.no_hoc_phi ? ' · <span class="tag bad">Nợ học phí</span>' : '');
}

function veBangLop() {
  const q = $('#tim-lop').value.trim().toLowerCase();
  const daDk = new Set(st.daDk.map((d) => d.ma_lhp));
  const rows = st.lop
    .filter((l) => !q || `${l.ma_lhp} ${l.ten_mh} ${l.giang_vien}`.toLowerCase().includes(q))
    .map((l) => {
      const full = l.si_so_hien_tai >= l.si_so_toi_da;
      const pct = Math.min(100, (l.so_dk_thuc_te / l.si_so_toi_da) * 100);
      const lech = l.so_dk_thuc_te !== l.si_so_hien_tai;
      const coDk = daDk.has(l.ma_lhp);
      const nut = st.dangXuLy.has(l.ma_lhp)
        ? '<button class="btn small cho" disabled>Đang xử lý…</button>'
        : coDk
        ? `<button class="btn small outline-bad" data-huy="${esc(l.ma_lhp)}">Huỷ</button>`
        : `<button class="btn small" data-dk="${esc(l.ma_lhp)}" ${full ? 'disabled' : ''}>${full ? 'Đã đầy' : 'Đăng kí'}</button>`;
      return `<tr class="${coDk ? 'da-dk' : ''}">
        <td class="ma">${esc(l.ma_lhp)}</td>
        <td>${esc(l.ten_mh)}</td>
        <td>${l.so_tin_chi}</td>
        <td>${lich(l)}<div class="gv">${esc(l.phong)}</div></td>
        <td class="gv">${esc(l.giang_vien)}</td>
        <td class="siso ${full || l.so_dk_thuc_te > l.si_so_toi_da ? 'full' : ''}">${l.so_dk_thuc_te}/${l.si_so_toi_da}
          <div class="bar"><span style="width:${pct}%"></span></div>
          ${lech ? `<span class="warn">⚠ cột si_so_hien_tai = ${l.si_so_hien_tai}</span>` : ''}</td>
        <td>${nut}</td></tr>`;
    });
  $('#bang-lop tbody').innerHTML = rows.join('') || '<tr><td colspan="7" class="empty">Không có lớp phù hợp</td></tr>';
}

function veDaDk() {
  $('#ds-da-dk').innerHTML = st.daDk.length
    ? st.daDk.map((d) => `<div class="dk-item"><div><div class="t">${esc(d.ma_lhp)} · ${esc(d.ten_mh)}</div>
        <div class="s">${lich(d)} · ${esc(d.phong)} · ${d.so_tin_chi} TC</div></div>
        <button class="btn small outline-bad" data-huy="${esc(d.ma_lhp)}">Huỷ</button></div>`).join('')
    : '<div class="empty">Chưa đăng kí lớp nào.</div>';
}

function veTkb() {
  const o = [`<div class="h"></div>`];
  for (let t = 2; t <= 7; t++) o.push(`<div class="h">${tenThu(t)}</div>`);
  for (let tiet = 1; tiet <= 12; tiet++) {
    o.push(`<div class="tiet" style="grid-row:${tiet + 1};grid-column:1">${tiet}</div>`);
    for (let t = 2; t <= 7; t++) o.push(`<div class="o" style="grid-row:${tiet + 1};grid-column:${t}"></div>`);
  }
  // xếp làn cho các lớp trùng giờ để thấy rõ xung đột
  const ds = st.daDk.filter((d) => d.thu <= 7);
  ds.forEach((d) => {
    const trung = ds.filter((x) => x !== d && trungGio(x, d));
    const nhom = [d, ...trung].sort((a, b) => a.ma_lhp.localeCompare(b.ma_lhp));
    const lan = nhom.indexOf(d), soLan = nhom.length;
    const w = 100 / soLan;
    o.push(`<div class="lop ${trung.length ? 'trung' : ''}" title="${esc(d.ten_mh)}"
      style="grid-row:${d.tiet_bd + 1} / ${d.tiet_kt + 2};grid-column:${d.thu};width:calc(${w}% - 2px);margin-left:calc(${w * lan}% + 1px)">
      <b>${esc(d.ma_lhp)}</b><br>${esc(d.phong)}</div>`);
  });
  $('#tkb').innerHTML = o.join('');
}

const TEN_VI_PHAM = {
  VUOT_SI_SO: 'Vượt sĩ số', SAI_SI_SO: 'Sai sĩ số (lost update)', TRUNG_LICH: 'Trùng lịch',
  TRUNG_HOC_PHAN: 'Trùng học phần', VUOT_TIN_CHI: 'Vượt tín chỉ',
};
function veKiemTra(ds) {
  $('#kiem-tra').innerHTML = ds.length
    ? `<table class="tbl"><thead><tr><th>Loại vi phạm</th><th>Đối tượng</th><th>Chi tiết</th></tr></thead><tbody>${
      ds.map((v) => `<tr class="vp-row"><td><span class="tag bad">${esc(TEN_VI_PHAM[v.loai] || v.loai)}</span></td>
        <td class="ma">${esc(v.doi_tuong)}</td><td>${esc(v.chi_tiet)}</td></tr>`).join('')}</tbody></table>`
    : '<div class="vp-ok">✅ Không có vi phạm: không vượt sĩ số, sĩ số khớp số đăng kí, không trùng lịch, không trùng học phần, không vượt tín chỉ.</div>';
}

$('#chon-sv').addEventListener('change', (e) => { st.maSv = e.target.value; cuaSo.set('ma_sv', st.maSv); taiLai(); });

// ----- Công tắc mô phỏng xung đột trên trang -----
function veCheDo() {
  document.querySelectorAll('[data-che-do-trang]').forEach((b) => b.classList.toggle('on', (b.dataset.cheDoTrang === '1') === st.coXuLy));
  $('#tre-trang').value = String(st.tre);
  const card = $('#mo-phong');
  card.classList.toggle('co-xu-ly', st.coXuLy);
  card.classList.toggle('khong-xu-ly', !st.coXuLy);
  $('#mp-trang-thai').innerHTML = st.coXuLy
    ? `Nút <b>Đăng kí</b> gọi <code>sp_dang_ky_mo_phong(…, TRUE, ${st.tre})</code>: khoá dòng sinh viên và lớp bằng <code>SELECT ... FOR UPDATE</code>, nên hai người bấm cùng lúc sẽ được xử lý lần lượt.`
    : `<b style="color:var(--bad)">Đang tắt xử lý xung đột.</b> Nút <b>Đăng kí</b> gọi <code>sp_dang_ky_mo_phong(…, FALSE, ${st.tre})</code>: đọc thường, không khoá, ghi sĩ số bằng giá trị đã đọc.`;
}
document.querySelectorAll('[data-che-do-trang]').forEach((b) => b.addEventListener('click', () => {
  st.coXuLy = b.dataset.cheDoTrang === '1'; chung.set('co_xu_ly', st.coXuLy ? '1' : '0'); veCheDo();
}));
$('#tre-trang').addEventListener('change', (e) => { st.tre = Number(e.target.value); chung.set('tre', String(st.tre)); veCheDo(); });
window.addEventListener('storage', (e) => { // đồng bộ chế độ giữa các cửa sổ
  if (e.key === 'co_xu_ly') st.coXuLy = e.newValue !== '0';
  if (e.key === 'tre') st.tre = Number(e.newValue || 0);
  veCheDo();
});
veCheDo();

// Tự làm mới mỗi 2 giây để thấy thay đổi do cửa sổ khác gây ra
setInterval(() => { if (!$('#tab-dang-ky').hidden && !document.hidden) taiLai().catch(() => {}); }, 2000);
$('#tim-lop').addEventListener('input', veBangLop);
$('#btn-kiem-tra').addEventListener('click', async () => veKiemTra(await api('/api/kiem-tra')));
$('#btn-du-lieu-mau').addEventListener('click', async () => {
  if (!confirm('Xoá toàn bộ đăng kí hiện tại và nạp lại dữ liệu mẫu?')) return;
  await api('/api/du-lieu-mau', {});
  toast('Đã nạp lại dữ liệu mẫu', 'ok');
  taiLai();
});
document.addEventListener('click', async (e) => {
  const dk = e.target.closest('[data-dk]'), huy = e.target.closest('[data-huy]');
  if (!dk && !huy) return;
  const btn = dk || huy;
  const maLhp = btn.dataset.dk || btn.dataset.huy;
  const maSv = st.maSv;
  st.dangXuLy.add(maLhp);
  veBangLop();
  try {
    const kq = dk
      ? await api('/api/dang-ky', { ma_sv: maSv, ma_lhp: maLhp, coXuLy: st.coXuLy, tre: st.tre })
      : await api('/api/huy-dang-ky', { ma_sv: maSv, ma_lhp: maLhp });
    toast(`${maSv} → ${maLhp}: ${kq.thong_bao}`, kq.ket_qua === 'THANH_CONG' ? 'ok' : 'bad');
  } catch (err) { toast(err.message, 'bad'); }
  st.dangXuLy.delete(maLhp);
  taiLai();
});

// ===== TAB 2: GIẢ LẬP XUNG ĐỘT =====
const TEN_LOAI = { BEGIN: 'BEGIN', READ: 'ĐỌC', WRITE: 'GHI', LOCK: 'KHOÁ', INFO: '', COMMIT: 'COMMIT', ROLLBACK: 'ROLLBACK' };
const TEN_KQ = { THANH_CONG: ['ok', 'Thành công'], TU_CHOI: ['bad', 'Từ chối'], LOI: ['warn', 'Lỗi'] };

async function veDsKichBan() {
  const ds = await api('/api/kich-ban');
  $('#ds-kich-ban').innerHTML = ds.map((kb) => `
    <div class="card" id="kb-${kb.id}">
      <div class="kb-head">
        <div>
          <h2>${kb.id}. ${esc(kb.ten)} <span class="tag info">${esc(kb.loai)}</span></h2>
          <p class="kb-mo-ta">${esc(kb.moTa)}</p>
        </div>
        <div class="kb-actions">
          <button class="btn danger" data-chay="${kb.id}" data-che-do="loi">▶ Chạy KHÔNG xử lý</button>
          <button class="btn ok" data-chay="${kb.id}" data-che-do="an_toan">▶ Chạy CÓ xử lý</button>
        </div>
      </div>
      <div class="kb-kq"></div>
      <details class="giai-thich">
        <summary>Nguyên nhân và cách giải quyết</summary>
        <div class="gt-grid">
          <div><h4>Nguyên nhân</h4><p>${esc(kb.giaiThich.nguyenNhan)}</p><pre class="sql bad">${esc(kb.giaiThich.sqlLoi)}</pre></div>
          <div><h4>Cách giải quyết</h4><p>${esc(kb.giaiThich.cachGiai)}</p><pre class="sql ok">${esc(kb.giaiThich.sqlSua)}</pre></div>
        </div>
      </details>
    </div>`).join('');
}

function veLichThaoTac(kq) {
  const cot = kq.giaoDich.map((g) => g.ten);
  // thời gian chờ khoá: từ sự kiện KHOÁ tới sự kiện kế tiếp của cùng giao dịch
  const choSau = new Map();
  kq.suKien.forEach((e, i) => {
    if (e.loai !== 'LOCK') return;
    const ke = kq.suKien.slice(i + 1).find((x) => x.tx === e.tx);
    if (ke && ke.t - e.t >= 80) choSau.set(ke, ke.t - e.t);
  });
  const head = `<tr><th class="tg">Thời điểm</th>${kq.giaoDich.map((g) => `<th>${esc(g.ten)} · ${esc(g.ma_sv)} → ${esc(g.ma_lhp)}</th>`).join('')}</tr>`;
  const body = kq.suKien.map((e) => {
    const cho = choSau.get(e);
    const nhan = TEN_LOAI[e.loai] ?? e.loai;
    const lan = e.lanThu > 1 ? `<span class="tag warn">lần ${e.lanThu}</span> ` : '';
    const o = `<span class="ev ${esc(e.loai)}">${lan}${nhan ? `<span class="k">${esc(nhan)}</span>` : ''}${esc(e.msg)}${cho ? `<span class="cho">⏳ đã chờ ${(cho / 1000).toFixed(2)}s</span>` : ''}</span>`;
    return `<tr><td class="tg">+${(e.t / 1000).toFixed(3)}s</td>${cot.map((c) => `<td>${c === e.tx ? o : ''}</td>`).join('')}</tr>`;
  }).join('');
  return `<div class="table-scroll"><table class="lich"><thead>${head}</thead><tbody>${body}</tbody></table></div>`;
}

function veKetQua(kq) {
  const tt = kq.trangThai;
  const ketLuan = tt.dung
    ? `<div class="ket-luan ok"><h3>✅ Dữ liệu đúng</h3>`
    : `<div class="ket-luan bad"><h3>❌ Xảy ra xung đột</h3><ul>${tt.loi.map((l) => `<li>${esc(l)}</li>`).join('')}</ul>`;
  const kv = `<table class="kv">${tt.dong.map(([k, v]) => `<tr><td>${esc(k)}</td><td><b>${esc(v)}</b></td></tr>`).join('')}</table></div>`;
  const gd = `<div><div class="kq-tieu-de">Kết quả từng giao dịch</div><ul class="gd-list">${kq.giaoDich.map((g) => {
    const [cls, ten] = TEN_KQ[g.ket_qua] || ['info', g.ket_qua];
    const thuLai = g.cacLan.length > 1 ? ` <span class="tag warn">deadlock → thử lại ${g.cacLan.length - 1} lần</span>` : '';
    return `<li><b>${esc(g.ten)}</b> ${esc(g.ma_sv)}: <span class="tag ${cls}">${ten}</span> ${esc(g.thong_bao)}${thuLai}</li>`;
  }).join('')}</ul></div>`;
  const tenCheDo = kq.cheDo === 'loi' ? 'KHÔNG xử lý' : 'CÓ xử lý';
  return `<div class="kq-tieu-de">Lịch thao tác: ${tenCheDo} (xử lý chậm ${kq.tre}s giữa đọc và ghi)</div>
    ${veLichThaoTac(kq)}
    <div class="kq-grid">${ketLuan}${kv}${gd}</div>`;
}

document.addEventListener('click', async (e) => {
  const b = e.target.closest('[data-chay]');
  if (!b) return;
  const card = $(`#kb-${b.dataset.chay}`);
  const vung = $('.kb-kq', card);
  document.querySelectorAll('[data-chay]').forEach((x) => (x.disabled = true));
  vung.innerHTML = '<div class="dang-chay">Đang chạy các giao dịch đồng thời…</div>';
  try {
    vung.innerHTML = veKetQua(await api(`/api/kich-ban/${b.dataset.chay}/chay`, { cheDo: b.dataset.cheDo }));
  } catch (err) {
    vung.innerHTML = `<div class="ket-luan bad"><h3>Lỗi</h3>${esc(err.message)}</div>`;
  } finally {
    document.querySelectorAll('[data-chay]').forEach((x) => (x.disabled = false));
  }
});

// ===== TAB 3: THIẾT KẾ CSDL =====
let bangDangXem = 'dang_ky';

async function taiDsBang() {
  const ds = await api('/api/bang');
  $('#ds-bang').innerHTML = ds.map((b) => `<button class="btn ghost small ${b.ten === bangDangXem ? 'active' : ''}" data-bang="${esc(b.ten)}">
    ${esc(b.ten)}<span class="n">(${b.so_dong})</span></button>`).join('');
  await xemBang(bangDangXem);
}

async function xemBang(ten) {
  bangDangXem = ten;
  document.querySelectorAll('[data-bang]').forEach((x) => x.classList.toggle('active', x.dataset.bang === ten));
  const { cot, dong } = await api(`/api/bang/${encodeURIComponent(ten)}`);
  $('#du-lieu-bang').innerHTML = dong.length
    ? `<table class="tbl raw"><thead><tr>${cot.map((c) => `<th>${esc(c)}</th>`).join('')}</tr></thead>
       <tbody>${dong.map((r) => `<tr>${cot.map((c) => `<td>${esc(r[c])}</td>`).join('')}</tr>`).join('')}</tbody></table>`
    : '<div class="empty">Bảng rỗng.</div>';
}

document.addEventListener('click', (e) => {
  const b = e.target.closest('[data-bang]');
  if (b) xemBang(b.dataset.bang);
});
$('#btn-tai-bang').addEventListener('click', taiDsBang);

// ===== Khởi động =====
taiLai().catch((e) => toast(`Không kết nối được máy chủ/CSDL: ${e.message}`, 'bad'));
veDsKichBan();
