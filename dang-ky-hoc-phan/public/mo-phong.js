// Cổng đăng kí học phần (bản demo): hai "máy" A và B dùng cùng một web, đăng kí trên MySQL thật.
(function () {
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const giay = (ms) => (ms / 1000).toFixed(1).replace('.', ',');
  const tenThu = (t) => (Number(t) === 8 ? 'Chủ nhật' : `Thứ ${t}`);
  const lich = (o) => `${tenThu(o.thu)}, tiết ${o.tiet_bd}-${o.tiet_kt}`;
  const TRE = 3; // giây xử lý chậm giữa lúc kiểm tra và lúc ghi

  const KE = {
    'tranh-slot': { ten: 'Tranh slot', lech: 300,
      sai: 'Lớp KTCT.02 chỉ có 1 chỗ mà có 2 sinh viên đăng kí được.',
      dung: 'Chỉ 1 sinh viên vào được lớp KTCT.02, người còn lại bị báo hết chỗ.' },
    'trung-lich': { ten: 'Trùng lịch đồng thời', lech: 300,
      sai: 'SV09 đăng kí được 2 lớp học cùng giờ (Thứ 2, tiết 2-3).',
      dung: 'SV09 chỉ có 1 lớp vào Thứ 2, lớp trùng giờ bị từ chối.' },
    'dirty-read': { ten: 'SV đăng kí', lech: 500,
      sai: 'SV19 bị báo lớp đầy, nhưng lớp KTCT.02 vẫn còn chỗ trống.',
      dung: 'SV18 huỷ giữ chỗ, SV19 vào được lớp KTCT.02.' },
    'trung-hoc-phan': { ten: 'Trùng học phần', lech: 300,
      sai: 'SV10 đăng kí được 2 lớp của cùng môn Cơ sở dữ liệu.',
      dung: 'SV10 chỉ có 1 lớp môn Cơ sở dữ liệu, lớp thứ hai bị từ chối.' },
  };
  const THU_TU = ['tranh-slot', 'trung-lich', 'dirty-read', 'trung-hoc-phan'];

  const st = { ds: {}, id: null, coXuLy: false, gd: { A: null, B: null }, chay: { A: null, B: null }, tt: null, phien: 0, soYeuCau: 0, dangDatLai: false, dem: 0, hoi: 0 };
  const th = () => st.ds[st.id];
  const cungSv = () => th().A.ma_sv === th().B.ma_sv;
  const dangChay = () => st.chay.A != null || st.chay.B != null;

  async function api(url, body) {
    const res = await fetch(url, body === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.loi || `Lỗi máy chủ (HTTP ${res.status})`);
    return data;
  }

  function thoiGianCho(sk) {
    let tong = 0;
    sk.forEach((e, i) => { if (e.loai === 'LOCK' && sk[i + 1]) { const d = sk[i + 1].t - e.t; if (d >= 300) tong += d; } });
    return tong;
  }

  // ---------- Thanh demo ----------
  function veThanh() {
    $('tinh-huong').innerHTML = THU_TU.map((id) => `<button type="button" role="tab" data-th="${id}" aria-selected="${id === st.id}">${esc(KE[id].ten)}</button>`).join('');
    $('xl-tat').classList.toggle('on', !st.coXuLy);
    $('xl-bat').classList.toggle('on', st.coXuLy);
    const khoa = dangChay() || st.dangDatLai;
    document.querySelectorAll('#tinh-huong button, .cong-tac button, #nut-cung-luc, #nut-dat-lai').forEach((b) => (b.disabled = khoa));
  }

  // ---------- Một cửa sổ (máy A hoặc B) ----------
  function veMay(vai) {
    const g = th()[vai], tt = st.tt, kq = st.gd[vai], dang = st.chay[vai] != null;
    const nhan = cungSv() ? `Tab ${vai === 'A' ? 1 : 2} của ${g.ma_sv}` : `Máy của bạn ${vai}`;
    let trang = '<p class="trong">Đang tải…</p>';
    if (tt) {
      const sv = tt.sinhVien.find((x) => x.ma_sv === g.ma_sv) || { ho_ten: g.ho_ten, lop: '', so_tc: 0, tin_chi_toi_da: 24 };
      const dkSv = tt.dangKy.filter((d) => d.ma_sv === g.ma_sv);
      const hang = tt.lop.map((l) => {
        const mucTieu = l.ma_lhp === g.ma_lhp, daDk = dkSv.some((d) => d.ma_lhp === l.ma_lhp);
        const day = l.thuc_te >= l.si_so_toi_da, qua = l.thuc_te > l.si_so_toi_da;
        let nut;
        if (mucTieu) {
          if (dang) nut = `<button class="nut-dk dang" disabled><span class="xoay"></span><span id="dem-${vai}">Đang xử lý… 0,0 s</span></button>`;
          else if (daDk) nut = '<button class="nut-dk da" disabled>✓ Đã đăng kí</button>';
          else nut = `<button class="nut-dk" data-dk="${vai}" ${dangChay() || st.dangDatLai ? 'disabled' : ''}>Đăng kí</button>`;
        } else {
          nut = daDk ? '<span class="nho">✓ Đã đăng kí</span>' : `<span class="nho">${cungSv() ? 'đăng kí ở tab kia' : ''}</span>`;
        }
        return `<tr class="${mucTieu ? 'muc-tieu' : ''}">
          <td class="ma">${esc(l.ma_lhp)}</td>
          <td>${esc(l.ten_mh)}<div class="phu">${esc(l.giang_vien)}</div></td>
          <td>${l.so_tin_chi}</td>
          <td>${lich(l)}<div class="phu">Phòng ${esc(l.phong)}</div></td>
          <td class="si-so"><span class="so ${qua ? 'qua' : ''}">${l.thuc_te}/${l.si_so_toi_da}</span>
            <div class="thanh ${day ? 'day' : ''}"><span style="width:${Math.min(100, (l.thuc_te / l.si_so_toi_da) * 100)}%"></span></div>
            ${l.thuc_te !== l.si_so_hien_tai ? `<span class="canh">sĩ số lưu: ${l.si_so_hien_tai}</span>` : ''}</td>
          <td>${nut}</td></tr>`;
      }).join('');
      const ds = dkSv.map((d) => {
        const trungGio = dkSv.some((x) => x !== d && x.thu === d.thu && x.tiet_bd <= d.tiet_kt && d.tiet_bd <= x.tiet_kt);
        const trungMon = dkSv.some((x) => x !== d && x.ma_mh === d.ma_mh);
        const loi = trungGio ? 'Trùng giờ' : trungMon ? 'Trùng môn' : '';
        return `<li class="${loi ? 'loi' : ''}"><span><b>${esc(d.ma_lhp)}</b> · ${esc(d.ten_mh)}</span><span class="nho">${lich(d)}${loi ? ` · <span class="the-loi">${loi}</span>` : ''}</span></li>`;
      }).join('');
      trang = `<div class="sv"><span class="sv-anh">${vai}</span><div><p class="sv-ten">${esc(sv.ho_ten)}</p>
          <p class="sv-phu">MSSV ${esc(g.ma_sv)} · Lớp ${esc(sv.lop)}</p>${sv.no_hoc_phi ? '<span class="nhan-no">Còn nợ học phí</span>' : ''}</div>
          <p class="sv-tc">Đã đăng kí<br><b>${sv.so_tc}/${sv.tin_chi_toi_da}</b> tín chỉ</p></div>
        <h3>Lớp học phần đang mở</h3>
        <div class="bang-cuon"><table class="lop"><thead><tr><th>Mã lớp</th><th>Môn học</th><th>TC</th><th>Lịch học</th><th>Sĩ số</th><th></th></tr></thead><tbody>${hang}</tbody></table></div>
        <h3>Lớp đã đăng kí</h3>
        ${ds ? `<ul class="da-dk">${ds}</ul>` : '<p class="trong">Chưa đăng kí lớp nào</p>'}`;
    }
    let thongBao = '';
    if (kq && !dang) {
      const ok = kq.ket_qua === 'THANH_CONG', cho = thoiGianCho(kq.suKien);
      const chu = ok ? '✓ Đăng kí thành công' : (st.id === 'dirty-read' && vai === 'A' ? '↩ ' : '✕ ') + kq.thong_bao;
      thongBao = `<div class="thong-bao ${ok ? 'ok' : 'ko'}" role="status"><span>${esc(chu)}</span>${cho ? `<span class="cho">Đã phải chờ ${giay(cho)} giây</span>` : ''}</div>`;
    }
    $(`may-${vai}`).innerHTML = `<p class="may-nhan"><span class="cham"></span>${esc(nhan)}</p>
      <div class="cua-so"><div class="trinh-duyet"><span class="ba-cham"><span></span><span></span><span></span></span>
        <span class="dia-chi">dkhp.edu.vn/dang-ki-hoc-phan</span></div>
        <div class="trang">${thongBao}${trang}</div></div>`;
  }

  // ---------- Kiểm tra dữ liệu + nhật kí ----------
  function veKiemTra() {
    const el = $('kiem-tra'), co = st.gd.A || st.gd.B;
    const cd = `Xử lý xung đột: ${st.coXuLy ? 'Bật' : 'Tắt'}`;
    if (dangChay()) { el.className = 'kiem-tra'; el.innerHTML = `<span class="bieu-tuong">⏳</span><div><p class="chu-de">Kiểm tra dữ liệu trong MySQL · ${cd}</p><p class="cau">Đang xử lý…</p></div>`; return; }
    if (!co || !st.tt) { el.className = 'kiem-tra'; el.innerHTML = `<span class="bieu-tuong">ℹ️</span><div><p class="chu-de">Kiểm tra dữ liệu trong MySQL · ${cd}</p><p class="cau">Chưa có ai bấm Đăng kí.</p></div>`; return; }
    const dung = st.tt.dung, haiBen = st.gd.A && st.gd.B;
    const cau = haiBen ? (dung ? KE[st.id].dung : KE[st.id].sai) : (dung ? 'Dữ liệu đúng.' : st.tt.loi.join(' · '));
    el.className = `kiem-tra ${dung ? 'dung' : 'sai'}`;
    el.innerHTML = `<span class="bieu-tuong">${dung ? '✅' : '❌'}</span><div><p class="chu-de">Kiểm tra dữ liệu trong MySQL · ${cd}</p><p class="cau">${esc(cau)}</p></div>`;
  }

  function dich(e, vai, sk) {
    const msg = e.msg.replace(/ — nhả khoá$/, '');
    const batDau = sk.find((x) => x.vai === vai && x.loai === 'BEGIN');
    switch (e.loai) {
      case 'BEGIN': return `Bấm Đăng kí ${th()[vai].ma_lhp}`;
      case 'LOCK': return msg.startsWith('UPDATE') ? 'Muốn ghi, phải chờ A xong' : 'Xin khoá dữ liệu';
      case 'READ': {
        const m = msg.match(/(\d+)\/(\d+)/);
        let s = (msg.startsWith('Được cấp khoá') ? 'Được khoá. ' : '') + (m ? `Đọc sĩ số ${m[1]}/${m[2]}` : 'Đọc dữ liệu');
        if (batDau && batDau.msg.includes('READ UNCOMMITTED')) s += ' (gồm cả chỗ A giữ tạm)';
        return s;
      }
      case 'INFO': return msg.includes('học phí') ? 'Kiểm tra học phí…' : 'Kiểm tra xong, đang xử lý…';
      case 'WRITE': return msg.includes('Giữ chỗ') ? 'Giữ chỗ tạm (chưa lưu)' : 'Ghi đăng kí';
      case 'COMMIT': return 'Lưu (COMMIT)';
      case 'ROLLBACK': return `Huỷ (ROLLBACK): ${msg}`;
      default: return msg;
    }
  }

  function veNhatKi() {
    const co = ['A', 'B'].filter((v) => st.gd[v]);
    $('nhat-ki').hidden = !co.length;
    const sk = co.flatMap((v) => st.gd[v].suKien.map((e) => ({ ...e, vai: v }))).sort((x, y) => x.t - y.t);
    if (!sk.length) { $('dien-bien').innerHTML = ''; return; }
    const t0 = sk[0].t;
    $('dien-bien').innerHTML = sk.map((e, i) => {
      const truoc = sk.slice(0, i).reverse().find((x) => x.vai === e.vai);
      const cho = truoc && truoc.loai === 'LOCK' && e.t - truoc.t >= 300 ? `<span class="chip-cho">đã chờ ${giay(e.t - truoc.t)} s</span>` : '';
      return `<li class="${e.vai}"><div class="bong"><span class="ai">${e.vai}</span> ${esc(dich(e, e.vai, sk))}${cho}</div><span class="gio">${giay(e.t - t0)} s</span></li>`;
    }).join('');
  }

  function veHet() { veThanh(); veMay('A'); veMay('B'); veKiemTra(); veNhatKi(); }

  async function taiTrangThai() {
    const phien = st.phien, so = ++st.soYeuCau;
    try {
      const tt = await api(`/api/mo-phong/trang-thai?tinhHuong=${encodeURIComponent(st.id)}`);
      if (phien === st.phien && so === st.soYeuCau) { st.tt = tt; veMay('A'); veMay('B'); veKiemTra(); }
    } catch (e) {
      $('kiem-tra').className = 'kiem-tra sai';
      $('kiem-tra').innerHTML = `<span class="bieu-tuong">⚠️</span><div><p class="chu-de">Lỗi kết nối</p><p class="cau">${esc(e.message)}</p></div>`;
    }
  }

  // ---------- Hành động ----------
  async function datLai() {
    st.phien++;
    st.gd = { A: null, B: null };
    st.chay = { A: null, B: null };
    st.dangDatLai = true;
    veThanh();
    try {
      await api('/api/mo-phong/dat-lai', {});
      await taiTrangThai();
    } finally {
      st.dangDatLai = false;
      veHet();
    }
  }

  async function bam(vai, phien = st.phien) {
    if (st.chay[vai] != null || st.dangDatLai) return;
    st.chay[vai] = performance.now();
    st.gd[vai] = null;
    veHet(); batDem();
    let kq;
    try {
      kq = await api('/api/mo-phong/giao-dich', { tinhHuong: st.id, vai, coXuLy: st.coXuLy, tre: TRE });
    } catch (e) { kq = { ket_qua: 'LOI', thong_bao: e.message, suKien: [] }; }
    if (phien !== st.phien) return;
    st.chay[vai] = null;
    st.gd[vai] = kq;
    await taiTrangThai();
    veHet();
  }

  async function cungLuc() {
    if (dangChay() || st.dangDatLai) return;
    await datLai();
    const phien = st.phien;
    bam('A', phien);
    setTimeout(() => { if (phien === st.phien) bam('B', phien); }, KE[st.id].lech);
  }

  function batDem() {
    if (!st.dem) {
      st.dem = setInterval(() => {
        let con = false;
        ['A', 'B'].forEach((v) => {
          if (st.chay[v] == null) return;
          con = true;
          const el = $(`dem-${v}`);
          if (el) el.textContent = `Đang xử lý… ${giay(performance.now() - st.chay[v])} s`;
        });
        if (!con) { clearInterval(st.dem); st.dem = 0; }
      }, 100);
    }
    if (!st.hoi) {
      st.hoi = setInterval(() => {
        if (!dangChay()) { clearInterval(st.hoi); st.hoi = 0; return; }
        taiTrangThai();
      }, 600);
    }
  }

  async function chonTinhHuong() {
    const id = (location.hash || '').slice(1);
    st.id = THU_TU.includes(id) ? id : THU_TU[0];
    st.tt = null;
    await datLai();
  }

  // ---------- Sự kiện ----------
  document.addEventListener('click', (e) => {
    const t = e.target.closest('[data-th]');
    if (t && !t.disabled) { location.hash = t.dataset.th; return; }
    const d = e.target.closest('[data-dk]');
    if (d && !d.disabled) bam(d.dataset.dk);
  });
  $('xl-tat').addEventListener('click', () => { if (st.coXuLy) { st.coXuLy = false; datLai(); } });
  $('xl-bat').addEventListener('click', () => { if (!st.coXuLy) { st.coXuLy = true; datLai(); } });
  $('nut-cung-luc').addEventListener('click', cungLuc);
  $('nut-dat-lai').addEventListener('click', datLai);
  window.addEventListener('hashchange', chonTinhHuong);

  api('/api/mo-phong/tinh-huong')
    .then((ds) => { ds.forEach((t) => { st.ds[t.id] = t; }); return chonTinhHuong(); })
    .catch((e) => { $('kiem-tra').className = 'kiem-tra sai'; $('kiem-tra').innerHTML = `<span class="bieu-tuong">⚠️</span><div><p class="chu-de">Không kết nối được máy chủ / MySQL</p><p class="cau">${esc(e.message)}</p></div>`; });
})();
