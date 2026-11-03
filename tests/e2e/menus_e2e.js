// Kiểm thử giao diện bằng trình duyệt thật (Playwright). KHÔNG chạy cùng `python -m unittest` vì cần Node.js + Playwright và một website đang chạy.
// Cách chạy (trên máy bạn):
//   1) npm install playwright && npx playwright install chromium
//   2) Dùng kho bình luận tạm để không đụng vào bình luận thật:  VNNEWS_COMMENTS_DB=/tmp/test-comments.db python app.py
//   3) node tests/e2e/menus_e2e.js <thư mục lưu ảnh chụp>      (kịch bản này xóa bình luận ở bài 240151, nên chỉ chạy với kho tạm)
const { chromium } = require('playwright');
const out = process.argv[2] || '.';
let fails = 0;
const ok = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };
(async () => {
  const browser = await chromium.launch();
  const errs = [];
  // máy tính
  let ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  let p = await ctx.newPage();
  p.on('pageerror', e => errs.push(e.message));
  await p.goto('http://127.0.0.1:5000/', { waitUntil: 'load' });
  await p.click('#ddbtn');
  ok(await p.isVisible('#ddpanel'), 'máy tính: "Chủ đề" mở danh sách 11 chuyên mục');
  ok((await p.locator('#ddpanel a').count()) === 11, 'danh sách có 11 chuyên mục');
  await p.screenshot({ path: `${out}/menu_dd.png`, clip: { x: 0, y: 0, width: 1440, height: 520 } });
  await p.keyboard.press('Escape');
  ok(!(await p.isVisible('#ddpanel')), 'nhấn Esc đóng danh sách');
  await p.click('#burger');
  ok(await p.isVisible('#menu'), 'máy tính: nút ☰ mở menu lớn');
  await p.screenshot({ path: `${out}/menu_burger.png`, clip: { x: 0, y: 0, width: 1440, height: 560 } });
  await p.mouse.click(700, 800);
  ok(!(await p.isVisible('#menu')), 'bấm ra ngoài đóng menu');
  await p.click('#ddbtn'); await p.click('#burger');
  ok(!(await p.isVisible('#ddpanel')) && (await p.isVisible('#menu')), 'mở menu này thì menu kia tự đóng');
  await p.click('#theme2');
  ok((await p.evaluate(() => document.documentElement.dataset.theme)) === 'dark', 'nút đổi sáng/tối trong menu hoạt động');
  await p.click('#menu a[href="/chu-de/xe"]');
  await p.waitForURL('**/chu-de/xe');
  ok((await p.evaluate(() => document.documentElement.dataset.theme)) === 'dark', 'chế độ tối được nhớ sau khi chuyển trang');
  await ctx.close();
  // điện thoại
  ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  p = await ctx.newPage();
  p.on('pageerror', e => errs.push(e.message));
  await p.goto('http://127.0.0.1:5000/', { waitUntil: 'load' });
  await p.waitForTimeout(1500);
  await p.screenshot({ path: `${out}/m_home.png` });
  await p.tap('#ddbtn');
  ok(await p.isVisible('#menu') && !(await p.isVisible('#ddpanel')), 'điện thoại: "Chủ đề" mở menu ☰ (không mở danh sách thả xuống)');
  await p.screenshot({ path: `${out}/m_menu.png` });
  ok(!(await p.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1)), 'điện thoại: trang chủ không tràn ngang');
  await ctx.close();
  ok(errs.length === 0, 'không có lỗi JavaScript' + (errs.length ? ': ' + errs.join(' | ') : ''));
  await browser.close();
  console.log(fails ? `\n${fails} KIỂM TRA THẤT BẠI` : '\nTất cả đạt');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error('LỖI KỊCH BẢN:', e); process.exit(2); });
