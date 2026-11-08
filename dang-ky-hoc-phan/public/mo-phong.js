// Trang "Mô phỏng 2 sinh viên": 4 tình huống xung đột, A và B trên cùng một màn hình.
(function () {
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const tenThu = (t) => (Number(t) === 8 ? 'Chủ nhật' : `Thứ ${t}`);
  const lich = (o) => `${tenThu(o.thu)}, tiết ${o.tiet_bd}-${o.tiet_kt}`;
  const NHAN = { BEGIN: 'BEGIN', READ: 'ĐỌC', WRITE: 'GHI', LOCK: 'KHOÁ', INFO: '', COMMIT: 'COMMIT', ROLLBACK: 'ROLLBACK' };
  const TEN_KQ = { THANH_CONG: 'Thành công', TU_CHOI: 'Từ chối', LOI: 'Lỗi' };

  const st = {
    ds: [], th: null, coXuLy: false,
    gd: { A: null, B: null },          // kết quả giao dịch đã xong
    chay: { A: null, B: null },        // thời điểm bắt đầu (performance.now) khi đang chạy
    hen: [], demGio: 0, hoiTT: 0, phien: 0,
  };

  async function api(url, body) {
    const res = await fetch(url, body === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.loi || `HTTP ${res.status}`);
    return data;
  }

  // ---------- Vẽ ----------
  function veChon() {
    $('chon').innerHTML = st.ds.map((t) => `<a href="#${t.id}" data-id="${t.id}" ${st.th && st.th.id === t.id ? 'aria-current="page"' : ''}>
      <span class="t">${esc(t.ten)}</span><span class="l">${esc(t.loai)}</span></a>`).join('');
  }

  function veCheDo() {
    $('cd-co').classList.toggle('on', st.coXuLy);
    $('cd-khong').classList.toggle('on', !st.coXuLy);
    const th = st.th;
    if (!th) return;
    const ghiChu = th.id === 'dirty-read'
      ? (st.coXuLy ? 'B chạy ở <b>READ COMMITTED</b>: chỉ đọc dữ liệu đã COMMIT.' : 'B chạy ở <b>READ UNCOMMITTED</b>: đọc được dữ liệu A chưa COMMIT.')
      : (st.coXuLy ? 'Nút Đăng kí khoá dòng sinh viên và dòng lớp bằng <b>SELECT … FOR UPDATE</b>.' : 'Nút Đăng kí đọc thường, <b>không khoá</b>, ghi sĩ số bằng giá trị đã đọc.');
    $('goi-y').innerHTML = `${ghiChu} Có thể bấm từng nút Đăng kí bằng tay trong khoảng xử lý chậm, hoặc bấm “Cho A và B bấm cùng lúc”.`;
  }

  function veSv(vai) {
    const th = st.th, g = th[vai], el = $(`sv-${vai}`);
    const kq = st.gd[vai], dangChay = st.chay[vai] != null;
    let tt;
    if (dangChay) tt = `<div class="tt-gd dang-chay"><span class="xoay"></span><span id="dem-${vai}">Đang xử lý… 0.0 s</span></div>`;
    else if (kq) tt = `<div class="tt-gd ${esc(kq.ket_qua)}"><span class="tag ${esc(kq.ket_qua)}">${TEN_KQ[kq.ket_qua] || esc(kq.ket_qua)}</span><span>${esc(kq.thong_bao)}</span><span class="muted">· xong sau ${(kq.thoiGian / 1000).toFixed(2)} s</span></div>`;
    else tt = '<div class="tt-gd">Chưa bấm</div>';
    let buoc = '';
    if (kq && kq.suKien.length) {
      const t0 = kq.suKien[0].t, cho = thoiGianCho(kq.suKien.map((e) => ({ ...e, tx: vai })));
      buoc = '<ol class="buoc-gd">' + kq.suKien.map((e, i) => `<li><span class="tg">+${((e.t - t0) / 1000).toFixed(3)}</span>${veSuKien(e, cho.get(i))}</li>`).join('') + '</ol>';
    }
    const nhanNut = th.id === 'dirty-read' && vai === 'A' ? `Đăng kí ${g.ma_lhp} (giữ chỗ)` : `Đăng kí ${g.ma_lhp}`;
    el.innerHTML = `<div class="sv-dau"><span class="huy-hieu">${vai}</span><div>
        <p class="ten">${esc(g.ma_sv)} · ${esc(g.ho_ten)}</p>
        <p class="lop">${esc(g.ma_lhp)} · ${esc(g.ten_mh)} · ${lich(g)}</p></div></div>
      ${g.vaiTro ? `<p class="vai-tro">${esc(g.vaiTro)}</p>` : ''}
      <button type="button" class="nut-dk" data-bam="${vai}" ${dangChay ? 'disabled' : ''}>${esc(nhanNut)}</button>
      ${tt}${buoc}`;
  }

  function veSuKien(e, cho) {
    const nhan = NHAN[e.loai] ?? e.loai;
    return `<span class="ev ${esc(e.loai)}">${nhan ? `<span class="k">${esc(nhan)}</span>` : ''}${esc(e.msg)}${cho ? `<span class="cho">⏳ đã chờ ${(cho / 1000).toFixed(2)} s</span>` : ''}</span>`;
  }

  // thời gian chờ khoá: từ sự kiện KHOÁ tới sự kiện kế tiếp của cùng giao dịch
  function thoiGianCho(sk) {
    const m = new Map();
    sk.forEach((e, i) => {
      if (e.loai !== 'LOCK') return;
      const j = sk.findIndex((x, k) => k > i && x.tx === e.tx);
      if (j > 0 && sk[j].t - e.t >= 80) m.set(j, sk[j].t - e.t);
    });
    return m;
  }

  function veLich() {
    const co = ['A', 'B'].filter((v) => st.gd[v]);
    if (!co.length) { $('lich').innerHTML = '<p class="trong">Bấm Đăng kí ở A, ở B, hoặc bấm “Cho A và B bấm cùng lúc”.</p>'; return; }
    const sk = co.flatMap((v) => st.gd[v].suKien.map((e) => ({ ...e, tx: v }))).sort((x, y) => x.t - y.t);
    const t0 = sk[0].t, cho = thoiGianCho(sk), th = st.th;
    const head = `<tr><th class="tg">Thời điểm</th>${['A', 'B'].map((v) => `<th class="cot-${v}">${v} · ${esc(th[v].ma_sv)} → ${esc(th[v].ma_lhp)}${st.chay[v] != null ? ' (đang chạy…)' : ''}</th>`).join('')}</tr>`;
    const rows = sk.map((e, i) => `<tr><td class="tg">+${((e.t - t0) / 1000).toFixed(3)}s</td>${['A', 'B'].map((v) => `<td>${v === e.tx ? veSuKien(e, cho.get(i)) : ''}</td>`).join('')}</tr>`).join('');
    $('lich').innerHTML = `<table class="lich"><thead>${head}</thead><tbody>${rows}</tbody></table>`;
  }

  async function veTrangThai(coKetLuan) {
    const th = st.th, phien = st.phien;
    let tt;
    try { tt = await api(`/api/mo-phong/trang-thai?tinhHuong=${encodeURIComponent(th.id)}`); } catch (e) { return; }
    if (phien !== st.phien) return; // đã đổi tình huống
    const oLop = tt.lop.map((l) => {
      const lech = l.thuc_te !== l.si_so_hien_tai, qua = l.thuc_te > l.si_so_toi_da;
      const pct = Math.min(100, (l.thuc_te / l.si_so_toi_da) * 100);
      return `<div class="o-tt"><p class="t">${esc(l.ma_lhp)} · ${esc(l.ten_mh)}</p>
        <p class="phu">${lich(l)} · tối đa ${l.si_so_toi_da} SV</p>
        <div class="thanh ${qua ? 'qua' : ''}"><span style="width:${pct}%"></span></div>
        <p>Đang có <b>${l.thuc_te}</b> SV${l.ds ? `: ${esc(l.ds)}` : ''} · cột si_so_hien_tai = <b>${l.si_so_hien_tai}</b></p>
        ${qua ? `<p class="canh-bao">Vượt sĩ số: ${l.thuc_te} &gt; ${l.si_so_toi_da}</p>` : ''}
        ${lech ? '<p class="canh-bao">Cột sĩ số lệch với số đăng kí thực tế</p>' : ''}</div>`;
    }).join('');
    const dsSv = [...new Set([th.A.ma_sv, th.B.ma_sv])];
    const oSv = dsSv.map((sv) => {
      const ds = tt.dangKy.filter((d) => d.ma_sv === sv);
      return `<div class="o-tt"><p class="t">Lớp ${esc(sv)} đã đăng kí</p>${ds.length
        ? `<ul class="ds-dk">${ds.map((d) => `<li>${esc(d.ma_lhp)} (môn ${esc(d.ma_mh)}, ${lich(d)})</li>`).join('')}</ul>` : '<p class="phu">Chưa có lớp nào</p>'}</div>`;
    }).join('');
    $('trang-thai').innerHTML = oLop + oSv;

    const daCo = st.gd.A || st.gd.B, dangChay = st.chay.A != null || st.chay.B != null;
    if (!daCo || dangChay || !coKetLuan) {
      $('ket-luan').innerHTML = `<div class="ket-luan cho-ket-qua"><p>${dangChay ? 'Đang chạy… kết luận hiện khi các giao dịch xong.' : 'Chưa chạy. Dữ liệu đang ở trạng thái ban đầu.'}</p></div>`;
      return;
    }
    $('ket-luan').innerHTML = tt.dung
      ? '<div class="ket-luan dung"><h3>✅ Dữ liệu đúng</h3><p>Không có vi phạm nào trong view v_kiem_tra_toan_ven.</p></div>'
      : `<div class="ket-luan sai"><h3>❌ Xảy ra xung đột, dữ liệu bị sai</h3><ul>${tt.loi.map((l) => `<li>${esc(l)}</li>`).join('')}</ul></div>`;
  }

  function veGiaiThich() {
    const g = st.th.giaiThich;
    $('mo-ta').textContent = st.th.moTa;
    $('gt-nn').textContent = g.nguyenNhan;
    $('gt-cs').textContent = g.cachSua;
    $('gt-sql-loi').textContent = g.sqlLoi;
    $('gt-sql-sua').textContent = g.sqlSua;
  }

  function veNut() {
    const dangChay = st.chay.A != null || st.chay.B != null;
    $('btn-cung-luc').disabled = dangChay;
    $('btn-dat-lai').disabled = dangChay;
    document.querySelectorAll('.seg button, #tre, #lech').forEach((b) => (b.disabled = dangChay));
  }

  function veHet(coKetLuan = true) { veSv('A'); veSv('B'); veLich(); veNut(); veTrangThai(coKetLuan); }

  // ---------- Hành động ----------
  function dungHen() { st.hen.forEach(clearTimeout); st.hen = []; }

  async function datLai() {
    dungHen();
    st.phien++;
    st.gd = { A: null, B: null };
    st.chay = { A: null, B: null };
    await api('/api/mo-phong/dat-lai', {});
    veHet(false);
  }

  async function bam(vai) {
    if (st.chay[vai] != null) return;
    const phien = st.phien, th = st.th;
    st.chay[vai] = performance.now();
    st.gd[vai] = null;
    veSv(vai); veLich(); veNut(); batDemGio(); veTrangThai(false);
    let kq;
    try {
      kq = await api('/api/mo-phong/giao-dich', { tinhHuong: th.id, vai, coXuLy: st.coXuLy, tre: Number($('tre').value) });
    } catch (e) {
      kq = { ket_qua: 'LOI', thong_bao: e.message, suKien: [] };
    }
    if (phien !== st.phien) return;
    kq.thoiGian = performance.now() - st.chay[vai];
    st.chay[vai] = null;
    st.gd[vai] = kq;
    veHet(true);
  }

  async function bamCungLuc() {
    await datLai();
    bam('A');
    st.hen.push(setTimeout(() => bam('B'), Number($('lech').value)));
  }

  // bộ đếm thời gian cho giao dịch đang chạy + làm mới dữ liệu CSDL
  function batDemGio() {
    if (st.demGio) return;
    st.demGio = setInterval(() => {
      let con = false;
      for (const v of ['A', 'B']) {
        if (st.chay[v] == null) continue;
        con = true;
        const el = $(`dem-${v}`);
        if (el) el.textContent = `Đang xử lý… ${((performance.now() - st.chay[v]) / 1000).toFixed(1)} s`;
      }
      if (!con) { clearInterval(st.demGio); st.demGio = 0; }
    }, 100);
    if (!st.hoiTT) {
      st.hoiTT = setInterval(() => {
        if (st.chay.A == null && st.chay.B == null) { clearInterval(st.hoiTT); st.hoiTT = 0; return; }
        veTrangThai(false);
      }, 600);
    }
  }

  async function chonTinhHuong() {
    const id = (location.hash || '').slice(1);
    st.th = st.ds.find((t) => t.id === id) || st.ds[0];
    veChon(); veGiaiThich(); veCheDo();
    $('lech').value = st.th.id === 'dirty-read' ? '500' : '200';
    await datLai();
  }

  // ---------- Sự kiện ----------
  document.addEventListener('click', (e) => {
    const b = e.target.closest('[data-bam]');
    if (b) bam(b.dataset.bam);
  });
  document.querySelectorAll('.seg button').forEach((b) => b.addEventListener('click', async () => {
    st.coXuLy = b.dataset.co === '1';
    veCheDo();
    await datLai();
  }));
  $('btn-cung-luc').addEventListener('click', bamCungLuc);
  $('btn-dat-lai').addEventListener('click', datLai);
  window.addEventListener('hashchange', chonTinhHuong);

  api('/api/mo-phong/tinh-huong').then((ds) => { st.ds = ds; chonTinhHuong(); })
    .catch((e) => { $('mo-ta').textContent = `Không kết nối được máy chủ / MySQL: ${e.message}`; });
})();
