// Tiện ích dùng chung cho các trang (gắn vào window.DK)
(function () {
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const tenThu = (t) => (Number(t) === 8 ? 'Chủ nhật' : `Thứ ${t}`);
  const lich = (o) => `${tenThu(o.thu)}, tiết ${o.tiet_bd}-${o.tiet_kt}`;
  const trungGio = (a, b) => a.thu === b.thu && a.tiet_bd <= b.tiet_kt && b.tiet_bd <= a.tiet_kt;
  const giay = (ms) => (ms / 1000).toFixed(1).replace('.', ',');

  /** Gọi API: không có body = GET, có body = POST JSON. Lỗi trả về câu tiếng Việt. */
  async function api(url, body) {
    let res;
    try {
      res = await fetch(url, body === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    } catch {
      throw new Error('Không kết nối được máy chủ. Kiểm tra cửa sổ chạy web còn mở không.');
    }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.loi || `Lỗi máy chủ (HTTP ${res.status})`);
    return data;
  }

  let hen;
  /** Thông báo nổi ở cuối màn hình. kieu: '' | 'ok' | 'ko' */
  function toast(msg, kieu = '') {
    let el = document.getElementById('toast');
    if (!el) {
      el = document.createElement('div');
      el.id = 'toast';
      el.setAttribute('role', 'status');
      document.body.appendChild(el);
    }
    el.textContent = msg;
    el.className = `toast ${kieu}`;
    el.hidden = false;
    clearTimeout(hen);
    hen = setTimeout(() => { el.hidden = true; }, 4000);
  }

  /** Khung báo lỗi kết nối thay cho nội dung một vùng. */
  const hopLoi = (tieuDe, e) => `<div class="ket-luan sai"><span class="bieu-tuong">⚠️</span><div><p class="chu-de">${esc(tieuDe)}</p><p class="cau">${esc(e.message || e)}</p></div></div>`;

  window.DK = { esc, tenThu, lich, trungGio, giay, api, toast, hopLoi };
})();
