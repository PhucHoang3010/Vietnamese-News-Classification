// Trang chủ "Mô phỏng xung đột": hai cửa sổ A và B dùng cùng cổng đăng kí, mỗi lần bấm Đăng kí
// là một giao dịch thật trên MySQL (một kết nối riêng). Dữ liệu hiển thị là dữ liệu đã COMMIT.
(function () {
  const { esc, lich, giay, api, hopLoi } = window.DK;
  const $ = (id) => document.getElementById(id);
  const TRE = 3; // giây xử lý chậm giữa lúc kiểm tra và lúc ghi, để hai lần bấm chắc chắn chen nhau

  // Thứ tự tab đúng theo phân công của nhóm; lech = B bấm sau A bao nhiêu mili giây
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
  const biKhoa = () => dangChay() || st.dangDatLai;

  /** Tổng thời gian một giao dịch phải chờ khoá (từ sự kiện LOCK tới bước kế tiếp). */
  function thoiGianCho(sk) {
    let tong = 0;
    sk.forEach((e, i) => { if (e.loai === 'LOCK' && sk[i + 1]) { const d = sk[i + 1].t - e.t; if (d >= 300) tong += d; } });
    return tong;
  }

  /** Kết luận về dữ liệu: vi phạm toàn vẹn trong MySQL, cộng trường hợp SV19 bị từ chối oan. */
  function danhGia() {
    const loi = [...st.tt.loi];
    if (st.id === 'dirty-read' && st.gd.B && st.gd.B.ket_qua !== 'THANH_CONG') {
      const l = st.tt.lop[0];
      if (l && l.thuc_te < l.si_so_toi_da) loi.push(`${th().B.ma_sv} bị từ chối dù lớp ${l.ma_lhp} vẫn còn chỗ (${l.thuc_te}/${l.si_so_toi_da}).`);
    }
    return { dung: loi.length === 0, loi };
  }

  // ---------- Thanh điều khiển ----------
  function veThanh() {
    $('tinh-huong').innerHTML = THU_TU.map((id, i) => `<button type="button" role="tab" data-th="${id}" aria-selected="${id === st.id}"><span class="so">${i + 1}</span>${esc(KE[id].ten)}</button>`).join('');
    $('xl-tat').setAttribute('aria-pressed', String(!st.coXuLy));
    $('xl-bat').setAttribute('aria-pressed', String(st.coXuLy));
    document.querySelectorAll('#tinh-huong button, .cong-tac button, #nut-cung-luc, #nut-dat-lai').forEach((b) => { b.disabled = biKhoa(); });
  }

  // ---------- Một cửa sổ (máy A hoặc B) ----------
  function veMay(vai) {
    const g = th()[vai], tt = st.tt, kq = st.gd[vai], dang = st.chay[vai] != null;
    const nhan = cungSv() ? `Tab ${vai === 'A' ? 1 : 2} của ${g.ma_sv}` : `Máy của bạn ${vai}`;
    let noiDung = '<p class="trong">Đang tải…</p>';
    if (tt) {
      const sv = tt.sinhVien.find((x) => x.ma_sv === g.ma_sv) || { ho_ten: g.ho_ten, lop: '', so_tc: 0, tin_chi_toi_da: 24 };
      const dkSv = tt.dangKy.filter((d) => d.ma_sv === g.ma_sv);
      const hang = tt.lop.map((l) => {
        const mucTieu = l.ma_lhp === g.ma_lhp, daDk = dkSv.some((d) => d.ma_lhp === l.ma_lhp);
        const day = l.thuc_te >= l.si_so_toi_da, qua = l.thuc_te > l.si_so_toi_da;
        let nut;
        if (mucTieu) {
          if (dang) nut = `<button type="button" class="nut-dk dang" disabled><span class="xoay"></span><span id="dem-${vai}">Đang xử lý… 0,0 s</span></button>`;
          else if (daDk) nut = '<button type="button" class="nut-dk da" disabled>✓ Đã đăng kí</button>';
          else nut = `<button type="button" class="nut-dk" data-dk="${vai}" ${biKhoa() ? 'disabled' : ''}>Đăng kí</button>`;
        } else {
          nut = daDk ? '<span class="nho-chu">✓ Đã đăng kí</span>' : `<span class="nho-chu">${cungSv() ? 'đăng kí ở tab kia' : ''}</span>`;
        }
        return `<tr class="${mucTieu ? 'noi-bat' : ''}">
          <td class="ma">${esc(l.ma_lhp)} <span class="tc-the phu">· ${l.so_tin_chi} TC</span></td>
          <td>${esc(l.ten_mh)}<div class="phu">${esc(l.giang_vien)}</div></td>
          <td class="o-tc">${l.so_tin_chi}</td>
          <td>${lich(l)}<div class="phu">Phòng ${esc(l.phong)}</div></td>
          <td class="si-so"><span class="so ${qua ? 'qua' : ''}">${l.thuc_te}/${l.si_so_toi_da}</span>
            <div class="thanh ${day ? 'day' : ''}"><span style="width:${Math.min(100, (l.thuc_te / l.si_so_toi_da) * 100)}%"></span></div>
            ${l.thuc_te !== l.si_so_hien_tai ? `<span class="canh">sĩ số lưu: ${l.si_so_hien_tai}</span>` : ''}</td>
          <td class="o-nut">${nut}</td></tr>`;
      }).join('');
      const ds = dkSv.map((d) => {
        const trungGio = dkSv.some((x) => x !== d && x.thu === d.thu && x.tiet_bd <= d.tiet_kt && d.tiet_bd <= x.tiet_kt);
        const trungMon = dkSv.some((x) => x !== d && x.ma_mh === d.ma_mh);
        const loi = trungGio ? 'Trùng giờ' : trungMon ? 'Trùng môn' : '';
        return `<li class="${loi ? 'loi' : ''}"><span><b>${esc(d.ma_lhp)}</b> · ${esc(d.ten_mh)}</span><span class="nho-chu">${lich(d)}${loi ? ` · <span class="the-loi">${loi}</span>` : ''}</span></li>`;
      }).join('');
      noiDung = `<div class="sv"><span class="sv-anh">${vai}</span><div><p class="sv-ten">${esc(sv.ho_ten)}</p>
          <p class="sv-phu">MSSV ${esc(g.ma_sv)} · Lớp ${esc(sv.lop)}</p>${sv.no_hoc_phi ? '<span class="nhan vang">Còn nợ học phí</span>' : ''}</div>
          <p class="sv-tc">Đã đăng kí<br><b>${sv.so_tc}/${sv.tin_chi_toi_da}</b> tín chỉ</p></div>
        <h3>Lớp học phần đang mở</h3>
        <div class="co-khung"><table class="lop"><thead><tr><th>Mã lớp</th><th>Môn học</th><th>TC</th><th>Lịch học</th><th>Sĩ số</th><th><span class="an">Thao tác</span></th></tr></thead><tbody>${hang}</tbody></table></div>
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
        <div class="noi-dung-may">${thongBao}${noiDung}</div></div>`;
  }

  // ---------- Kiểm tra dữ liệu ----------
  function veKiemTra() {
    const el = $('kiem-tra'), cd = `Kiểm tra dữ liệu trong MySQL · Xử lý xung đột: ${st.coXuLy ? 'Bật' : 'Tắt'}`;
    const hop = (lop, bieuTuong, cau) => { el.className = `ket-luan ${lop}`; el.innerHTML = `<span class="bieu-tuong">${bieuTuong}</span><div><p class="chu-de">${cd}</p><p class="cau">${esc(cau)}</p></div>`; };
    if (dangChay()) return hop('', '⏳', 'Đang xử lý…');
    if (!(st.gd.A || st.gd.B) || !st.tt) return hop('', 'ℹ️', 'Chưa có ai bấm Đăng kí.');
    const { dung, loi } = danhGia(), haiBen = st.gd.A && st.gd.B;
    const cau = haiBen ? (dung ? KE[st.id].dung : KE[st.id].sai) : (dung ? 'Dữ liệu đúng.' : loi.join(' · '));
    hop(dung ? 'dung' : 'sai', dung ? '✅' : '❌', cau);
  }

  // ---------- Nhật kí giao dịch ----------
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

  function baoLoi(tieuDe, e) {
    const el = $('kiem-tra');
    el.className = '';
    el.innerHTML = hopLoi(tieuDe, e);
  }

  async function taiTrangThai() {
    const phien = st.phien, so = ++st.soYeuCau;
    try {
      const tt = await api(`/api/mo-phong/trang-thai?tinhHuong=${encodeURIComponent(st.id)}`);
      if (phien === st.phien && so === st.soYeuCau) { st.tt = tt; veMay('A'); veMay('B'); veKiemTra(); }
    } catch (e) {
      if (phien === st.phien) baoLoi('Lỗi kết nối', e);
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
    } catch (e) {
      st.dangDatLai = false;
      veHet();
      baoLoi('Không đặt lại được dữ liệu', e);
      return false;
    }
    st.dangDatLai = false;
    veHet();
    return true;
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
    if (biKhoa()) return;
    if (!(await datLai())) return;
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
    if (!st.hoi) { // trong lúc chạy, cứ 0,6 giây đọc lại dữ liệu đã COMMIT
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

  function doiCheDo(bat) {
    if (st.coXuLy === bat || biKhoa()) return;
    st.coXuLy = bat;
    datLai();
  }

  // ---------- Sự kiện ----------
  document.addEventListener('click', (e) => {
    const t = e.target.closest('[data-th]');
    if (t && !t.disabled) { location.hash = t.dataset.th; return; }
    const d = e.target.closest('[data-dk]');
    if (d && !d.disabled) bam(d.dataset.dk);
  });
  $('tinh-huong').addEventListener('keydown', (e) => { // mũi tên trái/phải để đổi tình huống
    if (!['ArrowLeft', 'ArrowRight'].includes(e.key) || biKhoa()) return;
    const i = (THU_TU.indexOf(st.id) + (e.key === 'ArrowRight' ? 1 : THU_TU.length - 1)) % THU_TU.length;
    location.hash = THU_TU[i];
  });
  $('xl-tat').addEventListener('click', () => doiCheDo(false));
  $('xl-bat').addEventListener('click', () => doiCheDo(true));
  $('nut-cung-luc').addEventListener('click', cungLuc);
  $('nut-dat-lai').addEventListener('click', () => { if (!biKhoa()) datLai(); });
  window.addEventListener('hashchange', () => { if (!biKhoa()) chonTinhHuong(); });

  api('/api/mo-phong/tinh-huong')
    .then((ds) => { ds.forEach((t) => { st.ds[t.id] = t; }); return chonTinhHuong(); })
    .catch((e) => baoLoi('Không kết nối được máy chủ / MySQL', e));
})();
