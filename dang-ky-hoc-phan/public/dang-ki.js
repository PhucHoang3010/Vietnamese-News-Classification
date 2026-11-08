// Trang "Đăng kí học phần": chọn sinh viên, đăng kí / huỷ lớp, thời khoá biểu, kiểm tra toàn vẹn.
// Nút Đăng kí gọi sp_dang_ky_mo_phong(ma_sv, ma_lhp, co_xu_ly, tre) trên MySQL.
(function () {
  const { esc, tenThu, lich, trungGio, giay, api, toast, hopLoi } = window.DK;
  const $ = (id) => document.getElementById(id);

  // Sinh viên đang chọn lưu riêng từng cửa sổ (sessionStorage) để 2 cửa sổ đóng vai 2 người;
  // chế độ xử lý xung đột lưu chung (localStorage) để mọi cửa sổ cùng một chế độ.
  const kho = (loai) => ({
    get: (k) => { try { return window[loai].getItem(k); } catch { return null; } },
    set: (k, v) => { try { window[loai].setItem(k, v); } catch { /* trình duyệt chặn lưu trữ: bỏ qua */ } },
  });
  const cuaSo = kho('sessionStorage'), chung = kho('localStorage');
  const st = {
    sv: [], lop: [], daDk: [], kt: [], maSv: cuaSo.get('ma_sv') || 'SV01',
    dangXuLy: new Map(), coXuLy: chung.get('co_xu_ly') !== '0', tre: Number(chung.get('tre') || 0),
    khoaSv: '', khoaMon: '', banVe: '',
  };

  async function taiLai() {
    const [sv, lop, kt] = await Promise.all([api('/api/sinh-vien'), api('/api/lop-hoc-phan'), api('/api/kiem-tra')]);
    if (!sv.some((s) => s.ma_sv === st.maSv)) st.maSv = sv[0] && sv[0].ma_sv;
    const daDk = st.maSv ? await api(`/api/sinh-vien/${encodeURIComponent(st.maSv)}/dang-ky`) : [];
    const banVe = JSON.stringify([sv, lop, kt, daDk, st.maSv]);
    if (banVe === st.banVe) return; // dữ liệu không đổi thì không vẽ lại
    Object.assign(st, { sv, lop, kt, daDk, banVe });
    veHet();
  }
  const taiLaiAnToan = () => taiLai().catch((e) => { $('kiem-tra').innerHTML = hopLoi('Không tải được dữ liệu', e); });

  function veHet() { veChonSv(); veTheSv(); veLocMon(); veBangLop(); veDaDk(); veTkb(); veKiemTra(); }

  // ---------- Sinh viên ----------
  function veChonSv() {
    const khoa = st.sv.map((s) => s.ma_sv).join() + '|' + st.maSv;
    if (khoa === st.khoaSv) return; // không vẽ lại danh sách khi đang mở
    st.khoaSv = khoa;
    $('chon-sv').innerHTML = st.sv.map((s) => `<option value="${esc(s.ma_sv)}" ${s.ma_sv === st.maSv ? 'selected' : ''}>${esc(s.ma_sv)} · ${esc(s.ho_ten)}${s.no_hoc_phi ? ' (nợ học phí)' : ''}</option>`).join('');
  }

  function veTheSv() {
    const s = st.sv.find((x) => x.ma_sv === st.maSv);
    if (!s) { $('the-sv').innerHTML = ''; return; }
    const pt = Math.min(100, (s.so_tc / s.tin_chi_toi_da) * 100);
    $('the-sv').innerHTML = `<span class="phu">Lớp <b>${esc(s.lop)}</b> · ${s.so_lop} lớp đã đăng kí</span>
      <div class="tc-tong"><span class="so">${s.so_tc}/${s.tin_chi_toi_da}</span> tín chỉ<div class="thanh ${s.so_tc >= s.tin_chi_toi_da ? 'day' : ''}"><span style="width:${pt}%"></span></div></div>
      ${s.no_hoc_phi ? '<span class="nhan vang">Còn nợ học phí</span>' : ''}`;
  }

  // ---------- Lớp học phần ----------
  function veLocMon() {
    const mon = [...new Map(st.lop.map((l) => [l.ma_mh, l.ten_mh])).entries()];
    const khoa = mon.map(([m]) => m).join();
    if (khoa === st.khoaMon) return;
    st.khoaMon = khoa;
    const chon = $('loc-mon').value;
    $('loc-mon').innerHTML = '<option value="">Tất cả môn</option>' + mon.map(([m, t]) => `<option value="${esc(m)}" ${m === chon ? 'selected' : ''}>${esc(t)}</option>`).join('');
  }

  function nutLop(l, coDk) {
    const bd = st.dangXuLy.get(l.ma_lhp);
    if (bd != null) return `<button type="button" class="nut-dk dang" disabled><span class="xoay"></span><span data-dem="${esc(l.ma_lhp)}">Đang xử lý… ${giay(performance.now() - bd)} s</span></button>`;
    if (coDk) return `<button type="button" class="nut-dk huy" data-huy="${esc(l.ma_lhp)}">Huỷ</button>`;
    return `<button type="button" class="nut-dk" data-dk="${esc(l.ma_lhp)}">Đăng kí</button>`;
  }

  function veBangLop() {
    const q = $('tim-lop').value.trim().toLowerCase(), mon = $('loc-mon').value;
    const daDk = new Set(st.daDk.map((d) => d.ma_lhp));
    const ds = st.lop.filter((l) => (!mon || l.ma_mh === mon) && (!q || `${l.ma_lhp} ${l.ten_mh} ${l.giang_vien}`.toLowerCase().includes(q)));
    $('so-lop').textContent = `· ${ds.length} lớp`;
    $('bang-lop').tBodies[0].innerHTML = ds.map((l) => {
      const coDk = daDk.has(l.ma_lhp);
      const day = l.so_dk_thuc_te >= l.si_so_toi_da, qua = l.so_dk_thuc_te > l.si_so_toi_da;
      return `<tr class="${coDk ? 'cua-toi' : ''}">
        <td class="ma">${esc(l.ma_lhp)} <span class="tc-the phu">· ${l.so_tin_chi} TC</span></td>
        <td>${esc(l.ten_mh)}<div class="phu">${esc(l.giang_vien)}</div></td>
        <td class="o-tc">${l.so_tin_chi}</td>
        <td>${lich(l)}<div class="phu">Phòng ${esc(l.phong)}</div></td>
        <td class="si-so"><span class="so ${qua ? 'qua' : ''}">${l.so_dk_thuc_te}/${l.si_so_toi_da}</span>
          <div class="thanh ${day ? 'day' : ''}"><span style="width:${Math.min(100, (l.so_dk_thuc_te / l.si_so_toi_da) * 100)}%"></span></div>
          ${l.so_dk_thuc_te !== l.si_so_hien_tai ? `<span class="canh">sĩ số lưu: ${l.si_so_hien_tai}</span>` : ''}</td>
        <td class="o-nut">${nutLop(l, coDk)}</td></tr>`;
    }).join('') || '<tr><td colspan="6" class="trong">Không có lớp phù hợp</td></tr>';
  }

  // ---------- Đã đăng kí + thời khoá biểu ----------
  function veDaDk() {
    const s = st.sv.find((x) => x.ma_sv === st.maSv);
    $('tong-tc').innerHTML = s ? `Tổng <b>${s.so_tc}</b> / ${s.tin_chi_toi_da} tín chỉ` : '';
    $('ds-da-dk').innerHTML = st.daDk.length
      ? `<ul class="da-dk">${st.daDk.map((d) => {
        const trung = st.daDk.some((x) => x !== d && trungGio(x, d)) ? 'Trùng giờ' : st.daDk.some((x) => x !== d && x.ma_mh === d.ma_mh) ? 'Trùng môn' : '';
        return `<li class="${trung ? 'loi' : ''}"><span><b>${esc(d.ma_lhp)}</b> · ${esc(d.ten_mh)}<br><span class="nho-chu">${lich(d)} · Phòng ${esc(d.phong)} · ${d.so_tin_chi} TC${trung ? ` · <span class="the-loi">${trung}</span>` : ''}</span></span>
          <button type="button" class="nut do nho" data-huy="${esc(d.ma_lhp)}" ${st.dangXuLy.has(d.ma_lhp) ? 'disabled' : ''}>Huỷ</button></li>`;
      }).join('')}</ul>`
      : '<p class="trong">Chưa đăng kí lớp nào.</p>';
  }

  function veTkb() {
    const o = ['<div class="h"></div>'];
    for (let t = 2; t <= 8; t++) o.push(`<div class="h">${t === 8 ? 'CN' : `T${t}`}</div>`);
    for (let tiet = 1; tiet <= 12; tiet++) {
      o.push(`<div class="tiet" style="grid-row:${tiet + 1};grid-column:1">${tiet}</div>`);
      for (let t = 2; t <= 8; t++) o.push(`<div class="o" style="grid-row:${tiet + 1};grid-column:${t}"></div>`);
    }
    st.daDk.forEach((d) => { // các lớp trùng giờ được xếp thành làn cạnh nhau, tô đỏ
      const nhom = st.daDk.filter((x) => x === d || trungGio(x, d)).sort((a, b) => a.ma_lhp.localeCompare(b.ma_lhp));
      const w = 100 / nhom.length, lan = nhom.indexOf(d);
      o.push(`<div class="mon ${nhom.length > 1 ? 'trung' : ''}" title="${esc(`${d.ma_lhp} · ${d.ten_mh} · ${lich(d)} · Phòng ${d.phong}`)}"
        style="grid-row:${d.tiet_bd + 1} / ${d.tiet_kt + 2};grid-column:${d.thu};width:calc(${w}% - 2px);margin-left:calc(${w * lan}% + 1px)">
        <b>${esc(d.ma_lhp)}</b><br>${esc(d.phong)}</div>`);
    });
    $('tkb').innerHTML = o.join('');
  }

  // ---------- Kiểm tra toàn vẹn ----------
  const TEN_VI_PHAM = { VUOT_SI_SO: 'Vượt sĩ số', SAI_SI_SO: 'Sai sĩ số', TRUNG_LICH: 'Trùng lịch', TRUNG_HOC_PHAN: 'Trùng học phần', VUOT_TIN_CHI: 'Vượt tín chỉ' };
  function veKiemTra() {
    $('kiem-tra').innerHTML = st.kt.length
      ? `<div class="cuon-ngang"><table class="bang"><thead><tr><th>Loại vi phạm</th><th>Đối tượng</th><th>Chi tiết</th></tr></thead><tbody>${
        st.kt.map((v) => `<tr><td><span class="nhan ko">${esc(TEN_VI_PHAM[v.loai] || v.loai)}</span></td><td class="ma">${esc(v.doi_tuong)}</td><td>${esc(v.chi_tiet)}</td></tr>`).join('')}</tbody></table></div>`
      : '<div class="ket-luan dung"><span class="bieu-tuong">✅</span><div><p class="cau">Không có vi phạm nào.</p><p class="nho-chu">Không vượt sĩ số, sĩ số khớp số đăng kí, không trùng lịch, không trùng học phần, không vượt tín chỉ.</p></div></div>';
  }

  // ---------- Thử xung đột bằng 2 cửa sổ ----------
  function veCheDo() {
    document.querySelectorAll('[data-xl]').forEach((b) => b.setAttribute('aria-pressed', String((b.dataset.xl === '1') === st.coXuLy)));
    $('chon-tre').value = String(st.tre);
    $('thu-xung-dot').classList.toggle('tat', !st.coXuLy);
    $('goi-y-xd').textContent = st.coXuLy
      ? 'Mở thêm một cửa sổ trang này, chọn sinh viên khác và bấm Đăng kí cùng lúc: hai lần đăng kí được xử lý lần lượt.'
      : 'Đang tắt xử lý xung đột. Chọn thời gian xử lý 3–5 giây, rồi bấm Đăng kí ở hai cửa sổ gần như cùng lúc.';
  }
  document.querySelectorAll('[data-xl]').forEach((b) => b.addEventListener('click', () => {
    st.coXuLy = b.dataset.xl === '1'; chung.set('co_xu_ly', st.coXuLy ? '1' : '0'); veCheDo();
  }));
  $('chon-tre').addEventListener('change', (e) => { st.tre = Number(e.target.value); chung.set('tre', String(st.tre)); veCheDo(); });
  window.addEventListener('storage', (e) => { // đồng bộ chế độ giữa các cửa sổ
    if (e.key === 'co_xu_ly') st.coXuLy = e.newValue !== '0';
    if (e.key === 'tre') st.tre = Number(e.newValue || 0);
    veCheDo();
  });

  // ---------- Thao tác ----------
  let dem = 0;
  function batDem() {
    if (dem) return;
    dem = setInterval(() => {
      if (!st.dangXuLy.size) { clearInterval(dem); dem = 0; return; }
      document.querySelectorAll('[data-dem]').forEach((el) => {
        const bd = st.dangXuLy.get(el.dataset.dem);
        if (bd != null) el.textContent = `Đang xử lý… ${giay(performance.now() - bd)} s`;
      });
    }, 100);
  }

  async function thaoTac(loai, maLhp) {
    const maSv = st.maSv;
    if (st.dangXuLy.has(maLhp)) return;
    st.dangXuLy.set(maLhp, performance.now());
    veBangLop(); veDaDk(); batDem();
    try {
      const kq = loai === 'dk'
        ? await api('/api/dang-ky', { ma_sv: maSv, ma_lhp: maLhp, coXuLy: st.coXuLy, tre: st.tre })
        : await api('/api/huy-dang-ky', { ma_sv: maSv, ma_lhp: maLhp });
      toast(`${maSv} · ${maLhp}: ${kq.thong_bao}`, kq.ket_qua === 'THANH_CONG' ? 'ok' : 'ko');
    } catch (e) { toast(e.message, 'ko'); }
    st.dangXuLy.delete(maLhp);
    st.banVe = '';
    await taiLaiAnToan();
  }

  document.addEventListener('click', (e) => {
    const dk = e.target.closest('[data-dk]'), huy = e.target.closest('[data-huy]');
    if (dk && !dk.disabled) thaoTac('dk', dk.dataset.dk);
    else if (huy && !huy.disabled) thaoTac('huy', huy.dataset.huy);
  });
  $('chon-sv').addEventListener('change', (e) => { st.maSv = e.target.value; cuaSo.set('ma_sv', st.maSv); taiLaiAnToan(); });
  $('tim-lop').addEventListener('input', veBangLop);
  $('loc-mon').addEventListener('change', veBangLop);
  $('nut-kiem-tra').addEventListener('click', async () => {
    try { st.kt = await api('/api/kiem-tra'); veKiemTra(); toast('Đã kiểm tra lại dữ liệu', 'ok'); } catch (e) { toast(e.message, 'ko'); }
  });
  $('nut-du-lieu-mau').addEventListener('click', async () => {
    if (!confirm('Xoá toàn bộ đăng kí hiện tại và nạp lại dữ liệu mẫu?')) return;
    try { await api('/api/du-lieu-mau', {}); toast('Đã nạp lại dữ liệu mẫu', 'ok'); st.banVe = ''; await taiLaiAnToan(); } catch (e) { toast(e.message, 'ko'); }
  });

  veCheDo();
  taiLaiAnToan();
  // Tự làm mới mỗi 2 giây để thấy thay đổi do cửa sổ khác gây ra
  setInterval(() => { if (!document.hidden) taiLai().catch(() => {}); }, 2000);
})();
