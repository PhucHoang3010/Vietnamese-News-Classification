/* Bình luận dưới bài báo (phía máy chủ: comments.py).
   Mọi chữ do người dùng nhập (tên, nội dung) đều được thoát ký tự HTML bằng h() trước khi chèn vào trang. */
(() => {
  const root = document.getElementById('binh-luan');
  if (!root) return;
  const aid = Number(root.dataset.aid);
  const $ = s => root.querySelector(s);
  const h = s => String(s).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));

  /* mã bạn đọc: ngẫu nhiên, lưu trong trình duyệt, gửi kèm mỗi yêu cầu; máy chủ chỉ giữ bản băm */
  const mem = {};
  const ls = {
    get(k) { try { return localStorage.getItem(k) } catch (e) { return mem[k] || null } },
    set(k, v) { try { localStorage.setItem(k, v) } catch (e) { mem[k] = v } },
  };
  let rid = ls.get('vn_uid');
  if (!/^[A-Za-z0-9_-]{16,80}$/.test(rid || '')) {
    const b = new Uint8Array(16);
    if (window.crypto && crypto.getRandomValues) crypto.getRandomValues(b); else b.forEach((_, i) => { b[i] = Math.random() * 256 });
    rid = Array.from(b, x => x.toString(16).padStart(2, '0')).join('');
    ls.set('vn_uid', rid);
  }
  const api = async (url, opt = {}) => {
    const r = await fetch(url, {...opt, headers: {'X-Reader-Id': rid, ...(opt.body ? {'Content-Type': 'application/json'} : {})}});
    let d = {};
    try { d = await r.json() } catch (e) { /* trả về không phải JSON */ }
    if (!r.ok) throw new Error(d.error || 'Có lỗi, hãy thử lại.');
    return d;
  };
  const say = m => { if (typeof toast === 'function') toast(m) };

  let sort = 'moi', items = [], total = 0, more = false, skew = 0, busy = false;
  const open = new Set();                     // các bình luận gốc đang hiện đủ trả lời
  const list = $('#cm-list'), form = $('#cm-form'), ta = $('#cm-body'), nm = $('#cm-name'), cnt = $('#cm-cnt'), err = $('#cm-err'), moreBtn = $('#cm-more');

  const ago = ts => {
    const d = Math.floor(Date.now() / 1000 + skew - ts);
    if (d < 60) return 'vừa xong';
    if (d < 3600) return Math.floor(d / 60) + ' phút trước';
    if (d < 86400) return Math.floor(d / 3600) + ' giờ trước';
    if (d < 7 * 86400) return Math.floor(d / 86400) + ' ngày trước';
    return new Date(ts * 1000).toLocaleDateString('vi-VN');
  };
  const PAL = ['#0a74c0', '#0a7f84', '#17803f', '#6a42c2', '#a85800', '#d1344a', '#2b50d6', '#b8267f'];
  const avatar = n => {
    let x = 0;
    for (const ch of n) x = (x * 31 + ch.codePointAt(0)) >>> 0;
    return `<span class="cm-av" style="background:${PAL[x % PAL.length]}" aria-hidden="true">${h((Array.from(n)[0] || '?').toUpperCase())}</span>`;
  };
  const likeLabel = c => '👍 Thích' + (c.likes ? ' · ' + c.likes : '');

  const one = (c, rep) => `<article class="cm${rep ? ' rep' : ''}" id="c${c.id}" data-id="${c.id}">${avatar(c.name)}<div class="cm-main">
      <div class="cm-top"><b>${h(c.name)}</b>${c.mine ? '<span class="cm-me">Bạn</span>' : ''}<time title="${h(new Date(c.ts * 1000).toLocaleString('vi-VN'))}">${ago(c.ts)}</time></div>
      <p>${h(c.body).replace(/\n/g, '<br>')}</p>
      <div class="cm-act"><button type="button" class="like${c.liked ? ' on' : ''}" data-a="like" aria-pressed="${c.liked}">${likeLabel(c)}</button><button type="button" data-a="reply">💬 Trả lời</button>${c.mine ? '<button type="button" data-a="del">🗑 Xóa</button>' : ''}</div>
      <div class="cm-reply"></div>${rep ? '' : reps(c)}</div></article>`;
  const reps = c => {
    const r = c.replies || [], cut = !open.has(c.id) && r.length > 3;
    return r.length ? `<div class="cm-reps">${(cut ? r.slice(0, 2) : r).map(x => one(x, true)).join('')}${cut ? `<button type="button" class="btn ghost sm" data-a="expand" style="margin-top:8px">Xem thêm ${r.length - 2} trả lời</button>` : ''}</div>` : '';
  };

  function render() {
    $('#cm-n').textContent = total ? `(${total})` : '';
    list.innerHTML = items.length ? items.map(c => one(c, false)).join('') : '<p class="cm-empty">Chưa có bình luận nào. Hãy là người đầu tiên chia sẻ ý kiến về bài viết này.</p>';
    moreBtn.hidden = !more;
    const link = document.getElementById('cm-link');
    if (link) link.textContent = `💬 ${total} bình luận`;
    const m = /^#c(\d+)$/.exec(location.hash), el = m && document.getElementById('c' + m[1]);
    if (el && !render.done) { render.done = true; el.scrollIntoView({block: 'center'}); el.classList.add('hit'); }
  }

  async function load(reset) {
    const q = new URLSearchParams({aid, sort, offset: reset ? 0 : items.length});
    try {
      const d = await api('/api/comments?' + q);
      skew = d.now - Date.now() / 1000;
      items = reset ? d.items : items.concat(d.items);
      total = d.total; more = d.more;
      render();
    } catch (e) {
      list.innerHTML = `<p class="cm-empty">${h(e.message)}</p>`;
      form.querySelectorAll('textarea,input,button').forEach(x => { x.disabled = true });
    }
  }

  const find = id => {
    for (const c of items) {
      if (c.id === id) return {c, top: c};
      const r = (c.replies || []).find(x => x.id === id);
      if (r) return {c: r, top: c};
    }
    return null;
  };

  /* gửi bình luận gốc */
  ta.addEventListener('input', () => { cnt.textContent = ta.value.length + '/1000' });
  ta.addEventListener('keydown', e => { if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') form.requestSubmit ? form.requestSubmit() : form.dispatchEvent(new Event('submit', {cancelable: true})) });
  nm.value = ls.get('vn_name') || '';
  form.addEventListener('submit', async e => {
    e.preventDefault();
    if (busy) return;
    busy = true; err.hidden = true;
    const btn = form.querySelector('button.btn'); btn.disabled = true;
    try {
      const d = await api('/api/comments', {method: 'POST', body: JSON.stringify({aid, body: ta.value, name: nm.value})});
      ls.set('vn_name', nm.value.trim());
      ta.value = ''; cnt.textContent = '0/1000'; total = d.total;
      if (sort === 'moi') { items.unshift(d.comment); render(); } else { await load(true); }
      say('Đã đăng bình luận');
    } catch (ex) { err.textContent = ex.message; err.hidden = false; }
    btn.disabled = false; busy = false;
  });

  /* trả lời */
  function replyBox(art, c) {
    const box = art.querySelector(':scope > .cm-main > .cm-reply');
    if (box.firstChild) { box.innerHTML = ''; return; }                                        // bấm lần nữa để đóng
    box.innerHTML = `<form class="cm-rep-form"><textarea rows="2" maxlength="1000" placeholder="Trả lời ${h(c.name)}…" required></textarea>
      <div class="cm-row"><input maxlength="30" placeholder="Tên hiển thị (không bắt buộc)" value="${h(ls.get('vn_name') || '')}"><button class="btn sm">Gửi trả lời</button><button type="button" class="btn ghost sm" data-a="cancel">Hủy</button></div><div class="err" hidden></div></form>`;
    const f = box.firstChild, t = f.querySelector('textarea'), er = f.querySelector('.err');
    if (art.classList.contains('rep')) t.value = '@' + c.name + ' ';
    t.focus(); t.setSelectionRange(t.value.length, t.value.length);
    f.addEventListener('submit', async e => {
      e.preventDefault();
      const btn = f.querySelector('button.btn'); btn.disabled = true; er.hidden = true;
      try {
        const name = f.querySelector('input').value;
        const d = await api('/api/comments', {method: 'POST', body: JSON.stringify({aid, body: t.value, name, parent: c.id})});
        ls.set('vn_name', name.trim());
        const top = find(c.id).top;
        (top.replies = top.replies || []).push(d.comment); open.add(top.id); total = d.total;
        render(); say('Đã đăng trả lời');
      } catch (ex) { er.textContent = ex.message; er.hidden = false; btn.disabled = false; }
    });
  }

  list.addEventListener('click', async e => {
    const b = e.target.closest('button[data-a]');
    if (!b) return;
    const art = b.closest('.cm'), id = Number(art.dataset.id), hit = find(id), a = b.dataset.a;
    if (a === 'cancel') { art.querySelector(':scope > .cm-main > .cm-reply').innerHTML = ''; return; }
    if (a === 'expand') { open.add(id); render(); return; }
    if (!hit) return;
    try {
      if (a === 'reply') replyBox(art, hit.c);
      if (a === 'like') {
        const d = await api(`/api/comments/${id}/like`, {method: 'POST'});
        hit.c.likes = d.likes; hit.c.liked = d.liked;
        b.className = 'like' + (d.liked ? ' on' : ''); b.textContent = likeLabel(hit.c); b.setAttribute('aria-pressed', d.liked);
      }
      if (a === 'del') {
        const n = hit.c === hit.top ? (hit.c.replies || []).length : 0;
        if (!confirm('Xóa bình luận này?' + (n ? ` ${n} trả lời bên dưới cũng sẽ bị xóa.` : ''))) return;
        const d = await api(`/api/comments/${id}/delete`, {method: 'POST'});
        total = d.total;
        if (hit.c === hit.top) items = items.filter(x => x.id !== id); else hit.top.replies = hit.top.replies.filter(x => x.id !== id);
        render(); say('Đã xóa bình luận');
      }
    } catch (ex) { say(ex.message); }
  });

  root.querySelectorAll('.cm-sort button').forEach(b => b.addEventListener('click', () => {
    sort = b.dataset.s;
    root.querySelectorAll('.cm-sort button').forEach(x => x.classList.toggle('on', x === b));
    open.clear(); load(true);
  }));
  moreBtn.addEventListener('click', () => load(false));
  load(true);
})();
