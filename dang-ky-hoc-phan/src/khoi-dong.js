// Chạy web chỉ với một lệnh: npm run chay   (Windows: bấm đúp chay-web.bat)
//  1. Cài thư viện nếu chưa có
//  2. Kiểm tra kết nối MySQL; sai mật khẩu thì hỏi lại và tự lưu vào .env
//  3. Tạo lại CSDL dkhp (bảng, thủ tục, dữ liệu mẫu)
//  4. Mở web ở cổng trống đầu tiên từ 3000 và mở trình duyệt
const fs = require('fs');
const path = require('path');
const readline = require('readline');
const { execSync, exec } = require('child_process');

const GOC = path.join(__dirname, '..');
process.chdir(GOC);
const FILE_ENV = path.join(GOC, '.env');
const log = (s = '') => console.log(s);

function hoi(cauHoi, an = false) {
  return new Promise((resolve) => {
    const tty = Boolean(process.stdin.isTTY);
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout, terminal: tty });
    if (an && tty) {
      rl._writeToOutput = (s) => { rl.output.write(s.startsWith(cauHoi) || s.includes('\n') ? s : '*'.repeat(s.length)); };
    }
    rl.question(cauHoi, (tl) => { rl.close(); resolve(tl.trim()); });
  });
}

function giaTriEnv(v) {
  if (/^[A-Za-z0-9_.@!%^*()+=-]*$/.test(v)) return v;
  return v.includes("'") ? `"${v}"` : `'${v}'`;
}

function ghiEnv(ten, giaTri) {
  let s = fs.existsSync(FILE_ENV) ? fs.readFileSync(FILE_ENV, 'utf8') : '';
  const dong = `${ten}=${giaTriEnv(giaTri)}`;
  s = new RegExp(`^${ten}=.*$`, 'm').test(s) ? s.replace(new RegExp(`^${ten}=.*$`, 'm'), () => dong) : `${s.trimEnd()}\n${dong}\n`;
  fs.writeFileSync(FILE_ENV, s);
}

function moTrinhDuyet(url) {
  const lenh = process.platform === 'win32' ? `start "" "${url}"` : process.platform === 'darwin' ? `open "${url}"` : `xdg-open "${url}"`;
  exec(lenh, () => {});
}

async function main() {
  log('=== Đăng kí học phần · đồ án Hệ quản trị CSDL ===\n');

  // 1. Thư viện
  if (!fs.existsSync(path.join(GOC, 'node_modules', 'mysql2')) || !fs.existsSync(path.join(GOC, 'node_modules', 'express'))) {
    log('[1/4] Đang cài thư viện (chỉ lần đầu, cần có mạng)...');
    execSync('npm install', { stdio: 'inherit' });
  } else {
    log('[1/4] Thư viện đã có.');
  }

  // 2. Kết nối MySQL
  if (!fs.existsSync(FILE_ENV)) fs.copyFileSync(path.join(GOC, '.env.example'), FILE_ENV);
  require('dotenv').config({ path: FILE_ENV });
  const mysql = require('mysql2/promise');
  const { layCauHinh, khoiTaoCsdl, giaiThichLoi } = require('./db');

  log(`[2/4] Kết nối MySQL (tài khoản ${process.env.DB_USER || 'root'})...`);
  for (let lan = 1; ; lan++) {
    try {
      const c = await mysql.createConnection(layCauHinh());
      await c.end();
      break;
    } catch (e) {
      if (e.code === 'ER_ACCESS_DENIED_ERROR') {
        if (lan > 5) { log('\n✖ Nhập sai quá 5 lần. Mật khẩu là mật khẩu bạn đặt cho tài khoản root lúc cài MySQL.'); return thoat(1); }
        log(lan === 1 && !process.env.DB_PASSWORD ? '   Chưa có mật khẩu MySQL.' : '   ✖ Sai mật khẩu MySQL.');
        const mk = await hoi(`   Nhập mật khẩu tài khoản ${process.env.DB_USER || 'root'} của MySQL rồi bấm Enter: `, true);
        process.env.DB_PASSWORD = mk;
        continue;
      }
      if (e.code === 'ECONNREFUSED') {
        log('\n✖ ' + giaiThichLoi(e));
        await hoi('   Bật MySQL xong thì bấm Enter để thử lại: ');
        continue;
      }
      log('\n✖ Không kết nối được MySQL: ' + giaiThichLoi(e));
      return thoat(1);
    }
  }
  ghiEnv('DB_PASSWORD', process.env.DB_PASSWORD || '');
  log('   ✔ Kết nối được. Đã lưu mật khẩu vào file .env, lần sau không phải nhập nữa.');

  // 3. CSDL
  log('[3/4] Tạo CSDL dkhp: bảng, stored procedure, dữ liệu mẫu...');
  try {
    await khoiTaoCsdl();
  } catch (e) {
    log('✖ Tạo CSDL thất bại: ' + giaiThichLoi(e));
    return thoat(1);
  }
  log('   ✔ Xong.');

  // 4. Web
  const { batDau, inDiaChi } = require('./server');
  let cong = Number(process.env.PORT || 3000);
  for (let i = 0; ; i++) {
    try { await batDau(cong); break; } catch (e) {
      if (e.code !== 'EADDRINUSE' || i >= 10) { log('✖ Không mở được web: ' + e.message); return thoat(1); }
      cong++;
    }
  }
  const url = `http://localhost:${cong}/`;
  log('[4/4] Web đang chạy:');
  inDiaChi(cong);
  log('\n   Giữ cửa sổ này mở trong lúc dùng web. Muốn tắt web: bấm Ctrl+C hoặc đóng cửa sổ.');
  moTrinhDuyet(url);
}

async function thoat(ma) {
  if (process.stdin.isTTY) await hoi('\nBấm Enter để đóng...');
  process.exit(ma);
}

main().catch(async (e) => { log('✖ ' + e.message); await thoat(1); });
