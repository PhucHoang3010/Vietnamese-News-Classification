// Trang "Thiết kế CSDL": lược đồ quan hệ và stored procedure đọc từ information_schema, xem dữ liệu bảng.
(function () {
  const { esc, api, hopLoi } = window.DK;
  const $ = (id) => document.getElementById(id);

  // ---------- Lược đồ quan hệ ----------
  const THU_TU_RB = { 'PRIMARY KEY': 0, UNIQUE: 1, 'FOREIGN KEY': 2, CHECK: 3, INDEX: 4 };
  const TEN_RB = { 'PRIMARY KEY': 'Khoá chính', UNIQUE: 'UNIQUE', 'FOREIGN KEY': 'Khoá ngoại', CHECK: 'CHECK', INDEX: 'Chỉ mục' };
  const LOP_RB = { 'PRIMARY KEY': 'pk', UNIQUE: 'uq', 'FOREIGN KEY': 'fk', CHECK: 'xam', INDEX: 'xam' };

  function kieuCot(c) {
    const ds = [esc(c.kieu.toUpperCase())];
    if (!c.co_the_null) ds.push('NOT NULL');
    if (/auto_increment/i.test(c.them)) ds.push('AUTO_INCREMENT');
    if (c.mac_dinh != null) ds.push(`DEFAULT ${esc(c.mac_dinh)}`);
    return ds.join(' ');
  }

  function moTaRangBuoc(r) {
    if (r.loai === 'CHECK') return `<code>${esc(r.dieu_kien)}</code>`;
    const cot = `(${r.cot.map(esc).join(', ')})`;
    if (r.loai === 'FOREIGN KEY') return `<code>${cot}</code> → <code>${esc(r.bang_tc)}(${r.cot_tc.map(esc).join(', ')})</code>`;
    return `<code>${cot}</code>`;
  }

  async function taiLuocDo() {
    try {
      const ds = await api('/api/luoc-do');
      $('luoc-do').innerHTML = ds.map((b) => {
        const cot = b.cot.map((c) => {
          const khoa = [c.khoa_chinh ? '<span class="nhan pk">PK</span>' : '', ...c.khoa_ngoai.map((f) => `<span class="nhan fk" title="Khoá ngoại tới ${esc(f)}">FK → ${esc(f)}</span>`)].filter(Boolean).join(' ');
          return `<tr><td><span class="ten-cot ${c.khoa_chinh ? 'pk' : ''}">${esc(c.ten)}</span></td><td class="mono">${kieuCot(c)}</td><td>${khoa}</td><td class="phu">${esc(c.ghi_chu)}</td></tr>`;
        }).join('');
        const rb = [...b.rang_buoc].sort((x, y) => THU_TU_RB[x.loai] - THU_TU_RB[y.loai] || x.ten.localeCompare(y.ten))
          .map((r) => `<li><span class="nhan ${LOP_RB[r.loai]}">${TEN_RB[r.loai]}</span> <span class="mono nho-chu">${esc(r.ten)}</span> ${moTaRangBuoc(r)}</li>`).join('');
        return `<article class="bang-ld">
          <div class="bang-ld-dau"><b>${esc(b.ten.toUpperCase())}</b><span>${esc(b.ghi_chu)}</span></div>
          <div class="cuon-ngang"><table class="bang"><thead><tr><th>Cột</th><th>Kiểu dữ liệu</th><th>Khoá</th><th>Ý nghĩa</th></tr></thead><tbody>${cot}</tbody></table></div>
          <ul class="rang-buoc">${rb}</ul></article>`;
      }).join('');
    } catch (e) { $('luoc-do').innerHTML = hopLoi('Không đọc được lược đồ', e); }
  }

  // ---------- Stored procedure ----------
  const NHOM_TT = [
    { ten: 'Dùng cho trang Đăng kí học phần', co: (t) => ['sp_dang_ky', 'sp_dang_ky_mo_phong', 'sp_huy_dang_ky'].includes(t) },
    { ten: 'Dùng riêng cho tình huống SV đăng kí', co: (t) => ['sp_giu_cho_roi_huy', 'sp_dirty_read_loi', 'sp_dirty_read_an_toan'].includes(t) },
    { ten: 'Kịch bản SQL chạy bằng MySQL Workbench (thư mục sql/demo) và kiểm thử', co: (t) => /^sp_(tranh_slot|trung_lich|trung_hp)_|^sp_dat_lai_kich_ban$/.test(t) },
    { ten: 'Tiện ích', co: () => true },
  ];

  async function taiThuTuc() {
    try {
      const ds = await api('/api/thu-tuc');
      $('so-tt').textContent = `· ${ds.length} thủ tục`;
      const conLai = [...ds];
      const nhom = NHOM_TT.map((n) => ({ ten: n.ten, ds: conLai.splice(0).filter((t) => (n.co(t.ten) ? true : (conLai.push(t), false))) }));
      $('ds-thu-tuc').innerHTML = nhom.filter((n) => n.ds.length).map((n) => `<div class="nhom-tt"><h3>${esc(n.ten)}</h3>${n.ds.map((t) => `
        <div class="tt"><span class="ten">${esc(t.ten)}</span>
          <span class="ts">(${t.tham_so.map((p) => `${esc(p.kieu_truyen)} ${esc(p.ten)} ${esc(p.kieu.toUpperCase())}`).join(', ')})</span>
          <span class="mo-ta">${esc(t.ghi_chu)}</span></div>`).join('')}</div>`).join('');
    } catch (e) { $('ds-thu-tuc').innerHTML = hopLoi('Không đọc được danh sách thủ tục', e); }
  }

  // ---------- Dữ liệu bảng ----------
  let dangXem = 'dang_ky';
  async function taiDsBang() {
    try {
      const ds = await api('/api/bang');
      $('ds-bang').innerHTML = ds.map((b) => `<button type="button" role="tab" data-bang="${esc(b.ten)}" aria-selected="${b.ten === dangXem}">${esc(b.ten)}<span class="so">${b.so_dong}</span></button>`).join('');
      await xemBang(dangXem);
    } catch (e) { $('du-lieu-bang').innerHTML = hopLoi('Không tải được dữ liệu', e); }
  }

  async function xemBang(ten) {
    dangXem = ten;
    document.querySelectorAll('[data-bang]').forEach((x) => x.setAttribute('aria-selected', String(x.dataset.bang === ten)));
    try {
      const { cot, dong } = await api(`/api/bang/${encodeURIComponent(ten)}`);
      $('du-lieu-bang').innerHTML = dong.length
        ? `<table class="bang"><thead><tr>${cot.map((c) => `<th>${esc(c)}</th>`).join('')}</tr></thead>
           <tbody>${dong.map((r) => `<tr>${cot.map((c) => `<td>${esc(r[c])}</td>`).join('')}</tr>`).join('')}</tbody></table>`
        : `<p class="trong" style="padding:12px">${ten === 'v_kiem_tra_toan_ven' ? 'View rỗng: dữ liệu không có vi phạm nào.' : 'Bảng rỗng.'}</p>`;
    } catch (e) { $('du-lieu-bang').innerHTML = hopLoi('Không tải được bảng', e); }
  }

  document.addEventListener('click', (e) => {
    const b = e.target.closest('[data-bang]');
    if (b) xemBang(b.dataset.bang);
  });
  $('nut-tai-bang').addEventListener('click', taiDsBang);

  taiLuocDo();
  taiThuTuc();
  taiDsBang();
})();
