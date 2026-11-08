// Trang mô phỏng: 4 trường hợp xung đột, A và B bấm Đăng kí cùng lúc trên MySQL thật.
(function () {
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const giay = (ms) => (ms / 1000).toFixed(1).replace('.', ',');
  const tenThu = (t) => (Number(t) === 8 ? 'Chủ nhật' : `Thứ ${t}`);
  const TRE = 3; // giây "xử lý chậm" giữa lúc kiểm tra và lúc ghi

  // Lời kể dễ hiểu cho từng trường hợp
  const KE = {
    'tranh-slot': {
      tieuDe: 'Tranh slot', loai: 'Hai bạn tranh 1 chỗ cuối', hinh: 'ghe', lech: 300,
      chuyen: 'Lớp KTCT.02 chỉ còn 1 chỗ. A và B cùng bấm Đăng kí.',
      sai: 'Lớp chỉ có 1 chỗ mà cả A và B đều vào được.',
      dung: 'A vào được. B phải chờ A xong, thấy lớp đã hết chỗ nên bị từ chối.',
      viSao: 'Khi chưa xử lý, A và B cùng nhìn thấy “còn 1 chỗ” trước khi ai kịp ghi, nên cả hai cùng đăng kí. Cột sĩ số còn bị ghi đè, lưu sai thành 1 (lost update).',
      cachSua: 'Khoá dòng lớp học phần bằng SELECT … FOR UPDATE: ai bấm trước được làm trước, người sau phải đợi rồi xem lại số chỗ.',
      khong: 'Chưa xử lý: hệ thống không khoá, hai bạn cùng đọc rồi cùng ghi.',
      co: 'Đã xử lý: hệ thống khoá dòng lớp, người đến sau phải xếp hàng chờ.',
    },
    'trung-lich': {
      tieuDe: 'Trùng lịch đồng thời', loai: '1 bạn đăng kí 2 lớp trùng giờ', hinh: 'tkb', lech: 300,
      chuyen: 'SV09 mở 2 tab, cùng lúc đăng kí CSDL.01 và CTDL.01: hai lớp trùng giờ Thứ 2.',
      sai: 'SV09 có 2 lớp học cùng giờ vào Thứ 2.',
      dung: 'Tab A đăng kí được CSDL.01. Tab B phải chờ, thấy trùng giờ nên bị từ chối.',
      viSao: 'Mỗi tab chỉ kiểm tra các lớp đã lưu. Lúc kiểm tra, lớp của tab kia chưa lưu nên không thấy trùng. Hai lớp khác nhau nên khoá dòng lớp cũng không giúp được.',
      cachSua: 'Khoá dòng sinh viên ngay đầu giao dịch: hai lần đăng kí của cùng một bạn phải làm lần lượt, lần sau sẽ thấy lớp lần trước vừa lưu.',
      khong: 'Chưa xử lý: hai tab kiểm tra lịch cùng lúc, không khoá gì.',
      co: 'Đã xử lý: hệ thống khoá dòng sinh viên, tab sau phải chờ tab trước xong.',
    },
    'trung-hoc-phan': {
      tieuDe: 'Trùng học phần', loai: '1 bạn đăng kí 2 lớp cùng môn', hinh: 'mon', lech: 300,
      chuyen: 'SV10 mở 2 tab, cùng lúc đăng kí CSDL.01 và CSDL.02: hai lớp cùng môn.',
      sai: 'SV10 học 2 lớp của cùng một môn.',
      dung: 'Tab A đăng kí được CSDL.01. Tab B phải chờ, thấy đã có môn này nên bị từ chối.',
      viSao: 'Hai lần đăng kí cùng kiểm tra “đã học môn này chưa” khi bên kia chưa lưu, nên cả hai đều thấy “chưa” và cùng ghi.',
      cachSua: 'Khoá dòng sinh viên để hai lần đăng kí làm lần lượt. Có thể thêm ràng buộc UNIQUE (mã SV, mã môn) để MySQL chặn tận gốc.',
      khong: 'Chưa xử lý: hai tab kiểm tra môn cùng lúc, không khoá gì.',
      co: 'Đã xử lý: hệ thống khoá dòng sinh viên, tab sau phải chờ tab trước xong.',
    },
    'dirty-read': {
      tieuDe: 'SV đăng kí', loai: 'Đăng kí bị huỷ giữa chừng', hinh: 'ghe', lech: 500,
      chuyen: 'Lớp KTCT.02 còn 1 chỗ. A giữ chỗ rồi huỷ vì nợ học phí; B đăng kí đúng lúc A đang giữ chỗ.',
      sai: 'B bị báo lớp đầy, nhưng A huỷ xong thì lớp vẫn còn chỗ: B bị từ chối oan.',
      dung: 'B chờ A huỷ xong, thấy lớp còn chỗ nên đăng kí được.',
      viSao: 'Khi chưa xử lý, B đọc cả chỗ mà A mới giữ tạm, chưa lưu (mức READ UNCOMMITTED). A huỷ thì con số B đã đọc thành sai.',
      cachSua: 'Chỉ cho đọc dữ liệu đã lưu (mức READ COMMITTED): B thấy lớp còn chỗ, chờ A xong rồi đăng kí.',
      khong: 'Chưa xử lý: B đọc cả dữ liệu A chưa lưu (READ UNCOMMITTED).',
      co: 'Đã xử lý: B chỉ đọc dữ liệu đã lưu (READ COMMITTED).',
    },
  };
  const THU_TU = ['tranh-slot', 'trung-lich', 'dirty-read', 'trung-hoc-phan'];

  const st = { ds: {}, id: null, cheDo: null, gd: { A: null, B: null }, chay: { A: null, B: null }, tt: null, phien: 0, dem: 0, hoi: 0 };
  const ke = () => KE[st.id];
  const th = () => st.ds[st.id];
  const cungSv = () => th().A.ma_sv === th().B.ma_sv;

  async function api(url, body) {
    const res = await fetch(url, body === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.loi || `Lỗi máy chủ (HTTP ${res.status})`);
    return data;
  }

  // thời gian phải chờ khoá của một giao dịch (ms), 0 nếu không chờ
  function thoiGianCho(sk) {
    let tong = 0;
    sk.forEach((e, i) => { if (e.loai === 'LOCK' && sk[i + 1]) { const d = sk[i + 1].t - e.t; if (d >= 300) tong += d; } });
    return tong;
  }

  // ---------- Vẽ ----------
  function veTab() {
    $('tab').innerHTML = THU_TU.map((id, i) => `<a href="#${id}" ${id === st.id ? 'aria-current="page"' : ''}>
      <span class="so">TRƯỜNG HỢP ${i + 1}</span><span class="t">${esc(KE[id].tieuDe)}</span><span class="l">${esc(KE[id].loai)}</span></a>`).join('');
  }

  function veBan(vai) {
    const g = th()[vai], kq = st.gd[vai], dang = st.chay[vai] != null;
    const ten = cungSv() ? `${esc(g.ho_ten)} · tab ${vai}` : `Bạn ${vai} · ${esc(g.ho_ten)}`;
    let tt;
    if (dang) tt = `<div class="trang-thai dang"><span class="xoay"></span><span id="dem-${vai}">Đang đăng kí… 0,0 s</span></div>`;
    else if (!kq) tt = '<div class="trang-thai">Chưa bấm</div>';
    else {
      const cho = thoiGianCho(kq.suKien);
      const ok = kq.ket_qua === 'THANH_CONG';
      const huy = st.id === 'dirty-read' && vai === 'A';
      tt = `<div class="trang-thai ${ok ? 'ok' : 'ko'}">${ok ? '✅ Đăng kí được' : huy ? '↩ Huỷ giữ chỗ' : '❌ Bị từ chối'}
        ${ok ? '' : `<span class="them">${esc(kq.thong_bao)}</span>`}
        ${cho ? `<span class="chip-cho">phải chờ ${giay(cho)} s</span>` : ''}</div>`;
    }
    $(`ban-${vai}`).innerHTML = `<div class="ban-dau"><span class="avatar">${vai}</span><div>
        <p class="ten">${ten}</p><p class="phu">${esc(g.ma_sv)}</p></div></div>
      <p class="muon">Muốn đăng kí <b>${esc(g.ma_lhp)}</b> · ${esc(g.ten_mh)} · ${tenThu(g.thu)}, tiết ${g.tiet_bd}-${g.tiet_kt}</p>
      ${g.vaiTro ? `<p class="ghi-chu">${esc(g.vaiTro)}</p>` : ''}${tt}`;
  }

  function veGiua() {
    const tt = st.tt, el = $('giua');
    if (!tt) { el.innerHTML = '<p class="trong">Đang tải dữ liệu…</p>'; return; }
    const loai = ke().hinh;
    let html = '';
    if (loai === 'ghe') {
      const l = tt.lop[0];
      const ngoi = (l.ds || '').split(', ').filter(Boolean);
      const o = [];
      for (let i = 0; i < Math.max(l.si_so_toi_da, ngoi.length); i++) {
        if (i < ngoi.length) o.push(`<div class="ghe ${i < l.si_so_toi_da ? 'co' : 'qua'}"><span><b>${esc(ngoi[i])}</b>${i < l.si_so_toi_da ? 'đã vào lớp' : 'quá chỗ!'}</span></div>`);
        else if (st.id === 'dirty-read' && st.chay.A != null) o.push(`<div class="ghe tam"><span><b>${esc(th().A.ma_sv)}</b>giữ tạm, chưa lưu</span></div>`);
        else o.push('<div class="ghe"><span>Còn trống</span></div>');
      }
      html = `<p class="tieu-de">Lớp học</p><p class="lop-ten">${esc(l.ma_lhp)} · chỉ có ${l.si_so_toi_da} chỗ</p>
        <div class="ghe-hang">${o.join('')}</div>
        <p class="so-lieu">Đang có <b>${l.thuc_te}/${l.si_so_toi_da}</b> người · cột sĩ số lưu: <b>${l.si_so_hien_tai}</b></p>
        ${l.thuc_te > l.si_so_toi_da ? '<p class="canh-bao">⚠ Vượt sĩ số</p>' : ''}
        ${l.thuc_te !== l.si_so_hien_tai ? '<p class="canh-bao">⚠ Cột sĩ số lưu sai (bị ghi đè)</p>' : ''}`;
    } else if (loai === 'tkb') {
      const sv = th().A.ma_sv;
      const lop = tt.dangKy.filter((d) => d.ma_sv === sv && Number(d.thu) === 2);
      const trung = lop.length > 1;
      const hang = lop.map((d, i) => `<span style="grid-row:${i + 2};grid-column:1;font-weight:700">${esc(d.ma_lhp)}</span>
        <span class="vach x${(i % 2) + 1} ${trung ? 'trung' : ''}" style="grid-row:${i + 2};grid-column:${d.tiet_bd + 1} / ${Math.min(d.tiet_kt, 5) + 2}">${esc(d.ma_lhp)}</span>`).join('');
      html = `<p class="tieu-de">Thời khoá biểu Thứ 2 của ${esc(sv)}</p>
        <div class="tkb"><span></span>${[1, 2, 3, 4, 5].map((t) => `<span class="h">tiết ${t}</span>`).join('')}${hang}</div>
        ${lop.length ? '' : '<p class="trong">Chưa có lớp nào vào Thứ 2</p>'}
        ${trung ? '<p class="canh-bao">⚠ Trùng giờ: hai lớp cùng học tiết 2-3</p>' : ''}`;
    } else {
      const sv = th().A.ma_sv;
      const mh = tt.lop[0] ? tt.dangKy.filter((d) => d.ma_sv === sv && d.ma_mh === 'CSDL') : [];
      html = `<p class="tieu-de">Môn Cơ sở dữ liệu của ${esc(sv)}</p>
        ${mh.length ? `<div class="mon ${mh.length > 1 ? 'qua' : ''}">${mh.map((d) => `<span>${esc(d.ma_lhp)}</span>`).join('')}</div>` : '<p class="trong">Chưa đăng kí lớp nào của môn này</p>'}
        ${mh.length > 1 ? '<p class="canh-bao">⚠ Học 2 lớp của cùng một môn</p>' : ''}`;
    }
    el.innerHTML = html + '<p class="phu">Dữ liệu đã lưu (COMMIT) trong MySQL</p>';
  }

  function dich(e, vai, sk) {
    const loai = ke().hinh, msg = e.msg.replace(/ — nhả khoá$/, '');
    const batDau = sk.find((x) => x.vai === vai && x.loai === 'BEGIN');
    switch (e.loai) {
      case 'BEGIN': return `Bấm Đăng kí ${th()[vai].ma_lhp}`;
      case 'LOCK': return msg.startsWith('UPDATE') ? 'Muốn ghi, phải chờ A xong' : 'Xin khoá: ai đến trước làm trước';
      case 'READ': {
        if (loai === 'tkb') return (msg.startsWith('Được cấp khoá') ? 'Đến lượt. ' : '') + 'Kiểm tra lịch đã đăng kí';
        if (loai === 'mon') return (msg.startsWith('Được cấp khoá') ? 'Đến lượt. ' : '') + 'Kiểm tra các môn đã đăng kí';
        const m = msg.match(/(\d+)\/(\d+)/);
        let s = (msg.startsWith('Được cấp khoá') ? 'Đến lượt. ' : '') + (m ? `Xem lớp: đã có ${m[1]}/${m[2]} người` : 'Xem lớp');
        if (batDau && batDau.msg.includes('READ UNCOMMITTED')) s += ' (thấy cả chỗ A giữ tạm)';
        if (msg.includes('bản đã COMMIT')) s += ' (chỉ thấy dữ liệu đã lưu)';
        return s;
      }
      case 'INFO':
        if (msg.includes('học phí')) return 'Đang kiểm tra học phí…';
        return loai === 'tkb' ? 'Không thấy trùng giờ, đang xử lý…' : loai === 'mon' ? 'Chưa có môn này, đang xử lý…' : 'Còn chỗ, đang xử lý…';
      case 'WRITE': return msg.includes('Giữ chỗ') ? 'Giữ chỗ tạm, chưa lưu' : 'Ghi đăng kí';
      case 'COMMIT': return '✅ Lưu xong (COMMIT)';
      case 'ROLLBACK': return msg.includes('nợ học phí') ? '↩ Nợ học phí: huỷ, trả lại chỗ (ROLLBACK)' : `❌ Bị từ chối: ${msg}`;
      default: return msg;
    }
  }

  function veDienBien() {
    const co = ['A', 'B'].filter((v) => st.gd[v]);
    const sk = co.flatMap((v) => st.gd[v].suKien.map((e) => ({ ...e, vai: v }))).sort((x, y) => x.t - y.t);
    if (!sk.length) { $('dien-bien').innerHTML = ''; return; }
    const t0 = sk[0].t;
    const items = [];
    sk.forEach((e, i) => {
      if (e.loai === 'INFO' && !e.msg.includes('học phí') && !e.msg.startsWith('Hợp lệ') && !e.msg.startsWith('Còn chỗ')) return;
      const truoc = sk.slice(0, i).reverse().find((x) => x.vai === e.vai);
      const cho = truoc && truoc.loai === 'LOCK' && e.t - truoc.t >= 300 ? ` <span class="chip-cho">đã chờ ${giay(e.t - truoc.t)} s</span>` : '';
      const lop = e.loai === 'COMMIT' ? 'ok' : e.loai === 'ROLLBACK' ? 'ko' : '';
      items.push(`<li class="${e.vai}"><div class="bong ${lop}"><span class="ai">${e.vai}</span> ${esc(dich(e, e.vai, sk))}${cho}</div><span class="gio">${giay(e.t - t0)} s</span></li>`);
    });
    $('dien-bien').innerHTML = items.join('');
  }

  function veKetLuan() {
    const xong = st.gd.A && st.gd.B && st.chay.A == null && st.chay.B == null;
    $('ket-luan').hidden = !xong;
    $('sau-khi-chay').hidden = !xong;
    if (!xong || !st.tt) return;
    const k = ke(), dung = st.tt.dung, cd = st.cheDo === 'co' ? 'khi ĐÃ xử lý' : 'khi CHƯA xử lý';
    let cau = dung ? k.dung : k.sai;
    if (st.cheDo === 'khong' && dung) cau = 'Lần này hai bên không kịp chen vào nhau. Bấm chạy lại để thấy xung đột.';
    if (st.cheDo === 'co' && !dung) cau = st.tt.loi.join(' · ');
    $('ket-luan').className = `ket-luan ${dung ? 'dung' : 'sai'}`;
    $('ket-luan').innerHTML = `<p class="nhan">${dung ? '✅ Dữ liệu đúng' : '❌ Dữ liệu bị sai'} · ${cd}</p><p class="cau">${esc(cau)}</p>`;
  }

  function veNut() {
    const dang = st.chay.A != null || st.chay.B != null || st.dangDatLai;
    $('chay-khong').disabled = dang;
    $('chay-co').disabled = dang;
    $('chay-khong').classList.toggle('vua-chay', st.cheDo === 'khong');
    $('chay-co').classList.toggle('vua-chay', st.cheDo === 'co');
  }

  function veHet() { veBan('A'); veBan('B'); veGiua(); veDienBien(); veKetLuan(); veNut(); }

  async function taiTrangThai() {
    const phien = st.phien, so = (st.soYeuCau = (st.soYeuCau || 0) + 1);
    try {
      const tt = await api(`/api/mo-phong/trang-thai?tinhHuong=${encodeURIComponent(st.id)}`);
      // chỉ nhận câu trả lời của lần hỏi mới nhất (câu trả lời cũ về muộn sẽ bị bỏ qua)
      if (phien === st.phien && so === st.soYeuCau) { st.tt = tt; veGiua(); veKetLuan(); }
    } catch (e) { $('giua').innerHTML = `<p class="canh-bao">${esc(e.message)}</p>`; }
  }

  // ---------- Chạy ----------
  async function datLai() {
    st.phien++;
    st.gd = { A: null, B: null };
    st.chay = { A: null, B: null };
    st.tt = null;
    st.dangDatLai = true;
    veNut();
    try {
      await api('/api/mo-phong/dat-lai', {});
      await taiTrangThai();
    } finally {
      st.dangDatLai = false;
      veHet();
    }
  }

  async function bam(vai, phien) {
    st.chay[vai] = performance.now();
    veHet(); batDem();
    let kq;
    try {
      kq = await api('/api/mo-phong/giao-dich', { tinhHuong: st.id, vai, coXuLy: st.cheDo === 'co', tre: TRE });
    } catch (e) { kq = { ket_qua: 'LOI', thong_bao: e.message, suKien: [] }; }
    if (phien !== st.phien) return;
    st.chay[vai] = null;
    st.gd[vai] = kq;
    await taiTrangThai();
    veHet();
  }

  async function chay(cheDo) {
    if (st.dangDatLai || st.chay.A != null || st.chay.B != null) return;
    st.cheDo = cheDo;
    await datLai();
    const phien = st.phien;
    bam('A', phien);
    setTimeout(() => { if (phien === st.phien) bam('B', phien); }, ke().lech);
  }

  function batDem() {
    if (!st.dem) {
      st.dem = setInterval(() => {
        let con = false;
        ['A', 'B'].forEach((v) => {
          if (st.chay[v] == null) return;
          con = true;
          const el = $(`dem-${v}`);
          if (el) el.textContent = `Đang đăng kí… ${giay(performance.now() - st.chay[v])} s`;
        });
        if (!con) { clearInterval(st.dem); st.dem = 0; }
      }, 100);
    }
    if (!st.hoi) {
      st.hoi = setInterval(() => {
        if (st.chay.A == null && st.chay.B == null) { clearInterval(st.hoi); st.hoi = 0; return; }
        taiTrangThai();
      }, 500);
    }
  }

  async function chonTruongHop() {
    const id = (location.hash || '').slice(1);
    st.id = THU_TU.includes(id) ? id : THU_TU[0];
    st.cheDo = null;
    $('cau-chuyen').textContent = ke().chuyen;
    veTab();
    await datLai();
  }

  $('chay-khong').addEventListener('click', () => chay('khong'));
  $('chay-co').addEventListener('click', () => chay('co'));
  window.addEventListener('hashchange', chonTruongHop);

  api('/api/mo-phong/tinh-huong')
    .then((ds) => { ds.forEach((t) => { st.ds[t.id] = t; }); return chonTruongHop(); })
    .catch((e) => { $('cau-chuyen').textContent = `Không kết nối được máy chủ / MySQL: ${e.message}`; });
})();
