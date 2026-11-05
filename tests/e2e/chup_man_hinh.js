// Chụp ảnh màn hình website để đưa vào báo cáo (outputs/man_hinh/*.png). KHÔNG chạy cùng `python -m unittest`: cần Node.js + Playwright và website đang chạy.
// Cách chạy:
//   1) npm install playwright && npx playwright install chromium
//   2) Dùng kho bình luận tạm (kịch bản này đăng vài bình luận mẫu):  VNNEWS_COMMENTS_DB=/tmp/demo-comments.db python app.py
//   3) node tests/e2e/chup_man_hinh.js outputs/man_hinh
// Các bình luận trong ảnh là ví dụ minh họa do kịch bản nhập, không phải ý kiến thật.
const { chromium } = require('playwright');
const out = process.argv[2] || 'outputs/man_hinh';
const BASE = 'http://127.0.0.1:5000';
const AID = 240151;
const W = 1200;
const wait = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  require('fs').mkdirSync(out, { recursive: true });
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: W, height: 900 }, deviceScaleFactor: 1.5 });
  await ctx.addInitScript(() => { try { localStorage.setItem('theme', 'light'); } catch (e) {} });
  const page = await ctx.newPage();
  const errs = [];
  page.on('pageerror', e => errs.push(e.message));
  const shot = async (name, opt = {}) => { await page.screenshot({ path: `${out}/${name}.png`, ...opt }); console.log('đã chụp', name); };
  const go = async (path, ready) => { await page.goto(BASE + path, { waitUntil: 'load', timeout: 120000 }); if (ready) await page.waitForSelector(ready, { timeout: 60000 }); await wait(1500); };

  // 1) trang chủ (ô phân loại 3 bước)
  await go('/', '#hres .cl-top');
  await shot('man-hinh-trang-chu', { clip: { x: 0, y: 0, width: W, height: 900 } });

  // 2) trang bài báo: kết quả AI, mở phần "xem chi tiết"
  await go('/bai/' + AID, '#cs .cs-line');
  await page.click('.cls-more summary');
  await wait(600);
  const box = await page.locator('.cls').boundingBox();
  await shot('man-hinh-trang-bai', { clip: { x: 0, y: 0, width: W, height: Math.min(box.y + box.height + 24, 2000) }, fullPage: true });

  // 3) bình luận: đăng vài bình luận mẫu bằng API (mỗi "bạn đọc" một mã riêng) rồi chụp khu bình luận
  const post = (rid, body) => page.evaluate(async ([rid, body]) => {
    const r = await fetch('/api/comments', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Reader-Id': rid }, body: JSON.stringify(body) });
    return r.json();
  }, [rid, body]);
  const R = n => (n + '_demo_reader_id_0123456789').slice(0, 32);
  const c1 = await post(R('lananh'), { aid: AID, name: 'Lan Anh', body: 'Bài viết rất hữu ích, mong cơ quan chức năng sớm làm rõ trách nhiệm của đơn vị thi công.' });
  await post(R('minhquan'), { aid: AID, name: 'Minh Quân', body: 'Mình đồng ý, cần công khai kết quả điều tra.', parent: c1.comment.id });
  await post(R('hoangnam'), { aid: AID, name: 'Hoàng Nam', body: 'Cầu mới khánh thành mà đã sụt thì cần kiểm tra lại toàn bộ chất lượng công trình.' });
  await page.evaluate(async ([rid, id]) => { await fetch(`/api/comments/${id}/like`, { method: 'POST', headers: { 'X-Reader-Id': rid } }); }, [R('hoangnam'), c1.comment.id]);
  await page.evaluate(async ([rid, id]) => { await fetch(`/api/comments/${id}/like`, { method: 'POST', headers: { 'X-Reader-Id': rid } }); }, [R('minhquan'), c1.comment.id]);
  await go('/bai/' + AID, '#cm-list .cm');
  await page.locator('#binh-luan').scrollIntoViewIfNeeded();
  await wait(500);
  await page.locator('#binh-luan').screenshot({ path: `${out}/man-hinh-binh-luan.png` });
  console.log('đã chụp man-hinh-binh-luan');

  // 4) AI Lab (giải thích từng từ)
  await go('/giai-thich?id=' + AID, '.lab-text');
  await shot('man-hinh-ai-lab', { clip: { x: 0, y: 0, width: W, height: 1000 } });

  // 5) Hỏi AI: một câu hỏi có câu trả lời trích từ bài kèm nguồn
  await go('/hoi-ai', '#aq');
  await page.fill('#aq', 'Giá vàng trong nước biến động thế nào?');
  await page.click('#ago');
  await page.waitForSelector('.qa-best, .qa-row, .qa-none', { timeout: 60000 });
  await wait(1200);
  await shot('man-hinh-hoi-ai', { clip: { x: 0, y: 0, width: W, height: 1000 } });

  // 6) Tìm kiếm nâng cao
  await go('/tim-kiem?q=' + encodeURIComponent('giá vàng AND (tăng OR giảm) NOT bitcoin'), '.parsed');
  await shot('man-hinh-tim-kiem', { clip: { x: 0, y: 0, width: W, height: 950 } });

  console.log(errs.length ? 'LỖI JS: ' + errs.join(' | ') : 'không có lỗi JavaScript');
  await browser.close();
})().catch(e => { console.error('LỖI KỊCH BẢN:', e); process.exit(2); });
