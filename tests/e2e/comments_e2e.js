// Kiểm thử giao diện bằng trình duyệt thật (Playwright). KHÔNG chạy cùng `python -m unittest` vì cần Node.js + Playwright và một website đang chạy.
// Cách chạy (trên máy bạn):
//   1) npm install playwright && npx playwright install chromium
//   2) Dùng kho bình luận tạm để không đụng vào bình luận thật:  VNNEWS_COMMENTS_DB=/tmp/test-comments.db python app.py
//   3) node tests/e2e/comments_e2e.js <thư mục lưu ảnh chụp>      (kịch bản này xóa bình luận ở bài 240151, nên chỉ chạy với kho tạm)
const { chromium } = require('playwright');
const out = process.argv[2] || '.';
const URL = 'http://127.0.0.1:5000/bai/240151';
let fails = 0;
const ok = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };
const wait = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const browser = await chromium.launch();
  const errs = [];
  const mk = async (opts = {}) => {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, ...opts });
    const page = await ctx.newPage();
    page.on('pageerror', e => errs.push('pageerror: ' + e.message));
    page.on('console', m => { if (m.type() === 'error' && !/fonts\.g|ERR_|Failed to load resource/.test(m.text())) errs.push('console: ' + m.text()); });
    return { ctx, page };
  };
  const A = await mk();
  const a = A.page;
  await a.goto(URL, { waitUntil: 'load' });
  await a.waitForSelector('#cm-list');
  await a.waitForFunction(() => !/Đang tải/.test(document.querySelector('#cm-list').textContent));
  ok(/Chưa có bình luận nào/.test(await a.textContent('#cm-list')), 'trạng thái rỗng hiện đúng');

  // 1) đăng bình luận gốc
  await a.fill('#cm-name', 'Lan Anh');
  await a.fill('#cm-body', 'Bài viết rất hữu ích,\ncảm ơn tòa soạn.');
  await a.click('#cm-form button.btn');
  await a.waitForSelector('#cm-list .cm');
  ok((await a.textContent('#cm-list .cm .cm-top b')) === 'Lan Anh', 'bình luận gốc hiện ra với tên đã nhập');
  ok((await a.textContent('#cm-n')).includes('(1)'), 'bộ đếm (1)');
  ok((await a.innerHTML('#cm-list .cm p')).includes('<br>'), 'xuống dòng được giữ');
  ok((await a.textContent('#cm-list .cm-me')) === 'Bạn', 'có nhãn "Bạn" cho bình luận của chính mình');
  ok((await a.textContent('#cm-link')).includes('1 bình luận'), 'liên kết đầu bài cập nhật số bình luận');
  ok((await a.inputValue('#cm-body')) === '', 'ô nhập được xóa sau khi gửi');

  // 2) gửi liền tay lần nữa -> bị giới hạn tốc độ
  await a.fill('#cm-body', 'Gửi quá nhanh thử xem');
  await a.click('#cm-form button.btn');
  await a.waitForSelector('#cm-err:not([hidden])');
  ok(/hơi nhanh/.test(await a.textContent('#cm-err')), 'gửi dồn dập bị chặn kèm lời nhắn tiếng Việt');
  await a.fill('#cm-body', '');

  // 3) XSS: mã HTML phải hiện thành chữ, không được thực thi
  await wait(5200);
  await a.fill('#cm-name', '<b>Hacker</b>');
  await a.fill('#cm-body', '<img src=x onerror="window.__xss=1"> <script>window.__xss=2</script> **không in đậm**');
  await a.click('#cm-form button.btn');
  await a.waitForFunction(() => document.querySelectorAll('#cm-list > .cm').length === 2);
  ok(await a.evaluate(() => window.__xss === undefined), 'XSS: mã trong bình luận không chạy');
  ok(await a.evaluate(() => document.querySelectorAll('#cm-list img, #cm-list script').length === 0), 'XSS: không có thẻ img/script trong danh sách');
  ok((await a.textContent('#cm-list > .cm:first-child p')).includes('<img src=x onerror='), 'XSS: nội dung hiện nguyên văn dạng chữ');
  ok((await a.textContent('#cm-list > .cm:first-child .cm-top b')) === '<b>Hacker</b>', 'XSS: tên hiện nguyên văn dạng chữ');

  // 4) trả lời
  await wait(5200);
  await a.click('#cm-list > .cm:nth-child(2) button[data-a=reply]');
  await a.waitForSelector('.cm-rep-form textarea');
  await a.fill('.cm-rep-form textarea', 'Mình đồng ý với bạn.');
  await a.fill('.cm-rep-form input', 'Minh');
  await a.click('.cm-rep-form button.btn');
  await a.waitForSelector('#cm-list .cm-reps .cm.rep');
  ok((await a.textContent('#cm-n')).includes('(3)'), 'trả lời tính vào tổng (3)');
  ok((await a.textContent('#cm-list .cm.rep .cm-top b')) === 'Minh', 'trả lời nằm dưới bình luận gốc');
  ok((await a.getAttribute('#cm-list > .cm:nth-child(2)', 'id')) !== null && (await a.locator('#cm-list > .cm:nth-child(2) .cm-reps .cm.rep').count()) === 1, 'trả lời thuộc đúng bình luận gốc');

  // 5) thích
  const likeBtn = a.locator('#cm-list > .cm:nth-child(2) > .cm-main > .cm-act .like');
  await likeBtn.click();
  await a.waitForFunction(() => /Thích · 1/.test(document.querySelector('#cm-list > .cm:nth-child(2) .like').textContent));
  ok((await likeBtn.getAttribute('class')).includes('on'), 'nút Thích sáng lên sau khi bấm');

  // 6) tải lại: dữ liệu còn, vẫn nhận ra mình
  await a.reload({ waitUntil: 'load' });
  await a.waitForSelector('#cm-list .cm');
  ok((await a.locator('#cm-list > .cm').count()) === 2, 'tải lại trang: bình luận vẫn còn');
  ok((await a.locator('#cm-list .cm-me').count()) === 3, 'tải lại trang: vẫn nhận ra 3 bình luận của mình');
  ok((await a.locator('#cm-name').inputValue()) === 'Minh', 'tên lần trước được nhớ');

  // 7) người khác (trình duyệt khác) thấy gì
  const B = await mk();
  const b = B.page;
  await b.goto(URL, { waitUntil: 'load' });
  await b.waitForSelector('#cm-list .cm');
  ok((await b.locator('#cm-list .cm-me').count()) === 0, 'người khác không thấy nhãn "Bạn"');
  ok((await b.locator('#cm-list button[data-a=del]').count()) === 0, 'người khác không có nút Xóa');
  ok((await b.locator('#cm-list .like.on').count()) === 0 && /Thích · 1/.test(await b.textContent('#cm-list > .cm:nth-child(2) > .cm-main > .cm-act .like')), 'người khác thấy 1 lượt thích nhưng chưa tự thích');
  // họ thích một bình luận khác, rồi sắp xếp theo lượt thích
  await b.locator('#cm-list > .cm:nth-child(2) > .cm-main > .cm-act .like').click();
  await b.waitForFunction(() => /Thích · 2/.test(document.querySelector('#cm-list > .cm:nth-child(2) .like').textContent));
  await b.click('.cm-sort button[data-s=thich]');
  await b.waitForFunction(() => /Thích · 2/.test(document.querySelector('#cm-list > .cm:first-child .like').textContent));
  ok(true, 'sắp xếp theo lượt thích đưa bình luận nhiều thích lên đầu');
  // họ thử xóa bình luận của người khác bằng API trực tiếp
  const id = await b.evaluate(() => document.querySelector('#cm-list > .cm').dataset.id);
  const r = await b.evaluate(async id => { const x = await fetch(`/api/comments/${id}/delete`, { method: 'POST', headers: { 'X-Reader-Id': 'z'.repeat(32) } }); return [x.status, (await x.json()).error]; }, id);
  ok(r[0] === 403, 'API: xóa bình luận của người khác bị từ chối (403)');

  // 8) thẻ bài và khối "Ý kiến bạn đọc"
  await b.goto('http://127.0.0.1:5000/chu-de/phap-luat?loc=all', { waitUntil: 'load' });
  ok((await b.locator('.box h3', { hasText: 'Ý kiến bạn đọc' }).count()) === 1, 'thanh bên có khối "Ý kiến bạn đọc"');
  const minis = await b.locator('.cmt-mini').allTextContents();
  ok(minis.length === 3 && minis.some(t => t.includes('Mình đồng ý với bạn.')), 'khối ý kiến liệt kê 3 bình luận mới nhất');
  const html = await b.evaluate(() => [...document.querySelectorAll('.cmt-mini')].map(e => e.innerHTML).join('\n'));
  ok(html.includes('&lt;img src=x') && !/<img/i.test(html) && !/<script/i.test(html), 'khối ý kiến phía máy chủ cũng thoát HTML');
  await B.ctx.close();

  // 9) xóa bình luận của mình (có trả lời bên dưới)
  a.on('dialog', d => d.accept());
  await a.click('#cm-list > .cm:nth-child(2) > .cm-main > .cm-act button[data-a=del]');
  await a.waitForFunction(() => document.querySelectorAll('#cm-list > .cm').length === 1);
  ok((await a.textContent('#cm-n')).includes('(1)'), 'xóa bình luận gốc xóa luôn trả lời: còn (1)');
  await a.click('#cm-list > .cm > .cm-main > .cm-act button[data-a=del]');
  await a.waitForFunction(() => /Chưa có bình luận nào/.test(document.querySelector('#cm-list').textContent));
  ok(!(await a.textContent('#cm-n')).includes('('), 'xóa hết: bộ đếm trống');

  // 10) ảnh chụp giao diện
  await wait(5200);
  await a.fill('#cm-name', 'Hoàng Nam');
  await a.fill('#cm-body', 'Tôi nghĩ cần xem xét trách nhiệm của đơn vị thi công. Mong cơ quan chức năng sớm có kết luận.');
  await a.click('#cm-form button.btn');
  await a.waitForSelector('#cm-list .cm');
  await a.locator('#cm-list .like').first().click();
  await wait(5200);
  await a.click('#cm-list button[data-a=reply]');
  await a.fill('.cm-rep-form textarea', 'Đồng ý, cần minh bạch thông tin.');
  await a.click('.cm-rep-form button.btn');
  await a.waitForSelector('#cm-list .cm.rep');
  await a.locator('#binh-luan').scrollIntoViewIfNeeded();
  await a.locator('#binh-luan').screenshot({ path: `${out}/comments_light.png` });
  await a.evaluate(() => { document.documentElement.dataset.theme = 'dark'; });
  await a.locator('#binh-luan').screenshot({ path: `${out}/comments_dark.png` });
  await A.ctx.close();

  const M = await mk({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  await M.page.goto(URL, { waitUntil: 'load' });
  await M.page.waitForSelector('#cm-list .cm');
  await M.page.locator('#binh-luan').screenshot({ path: `${out}/comments_mobile.png` });
  const overflow = await M.page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
  ok(!overflow, 'điện thoại: trang không bị tràn ngang');
  await M.ctx.close();

  ok(errs.length === 0, 'không có lỗi JavaScript' + (errs.length ? ': ' + errs.join(' | ') : ''));
  await browser.close();
  console.log(fails ? `\n${fails} KIỂM TRA THẤT BẠI` : '\nTất cả đạt');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error('LỖI KỊCH BẢN:', e); process.exit(2); });
