// Kết nối MySQL + tiện ích chạy file .sql (hỗ trợ lệnh DELIMITER như MySQL Workbench / mysql CLI)
const fs = require('fs');
const path = require('path');
const mysql = require('mysql2/promise');
require('dotenv').config({ path: path.join(__dirname, '..', '.env') });

const DB_NAME = 'dkhp';
const SQL_DIR = path.join(__dirname, '..', 'sql');

// Đọc cấu hình mỗi lần dùng, để trình khởi động (khoi-dong.js) đổi mật khẩu xong là có hiệu lực ngay
const layCauHinh = () => ({
  host: process.env.DB_HOST || '127.0.0.1',
  port: Number(process.env.DB_PORT || 3306),
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASSWORD || '',
  charset: 'utf8mb4_unicode_ci',
  dateStrings: true,
});

/** Đổi lỗi kết nối MySQL thành câu tiếng Việt dễ hiểu. */
function giaiThichLoi(e) {
  const u = process.env.DB_USER || 'root';
  if (e.code === 'ER_ACCESS_DENIED_ERROR') return `Sai mật khẩu MySQL của tài khoản "${u}". Bấm đúp chay-web.bat (hoặc chạy npm run chay) để nhập lại mật khẩu.`;
  if (e.code === 'ECONNREFUSED') return 'MySQL chưa chạy. Bấm phím Windows + R, gõ services.msc, tìm MySQL80, bấm Start, rồi chạy lại.';
  if (e.code === 'ER_BAD_DB_ERROR') return 'Chưa có CSDL "dkhp". Chạy npm run db:init (hoặc bấm đúp chay-web.bat).';
  return e.message;
}

let pool;
function layPool() {
  if (!pool) {
    // Mỗi giao dịch giả lập cần 1 kết nối riêng (= 1 phiên làm việc riêng trên MySQL)
    pool = mysql.createPool({ ...layCauHinh(), database: DB_NAME, connectionLimit: 20, waitForConnections: true });
  }
  return pool;
}

async function dongPool() {
  if (pool) { await pool.end(); pool = undefined; }
}

/** Tách nội dung file .sql thành từng câu lệnh, tôn trọng `DELIMITER xx`. */
function tachCauLenh(sql) {
  const cauLenh = [];
  let delim = ';';
  let buf = [];
  const day = () => {
    const s = buf.join('\n').trim();
    buf = [];
    const conNoiDung = s.split('\n').some((d) => d.trim() && !d.trim().startsWith('--'));
    if (conNoiDung) cauLenh.push(s);
  };
  for (const dong of sql.split(/\r?\n/)) {
    const m = dong.match(/^\s*DELIMITER\s+(\S+)\s*$/i);
    if (m) { day(); delim = m[1]; continue; }
    // bỏ chú thích cuối dòng ("lệnh;  -- ghi chú") trước khi tìm dấu kết thúc câu lệnh
    const khongChuThich = dong.replace(/\s+--\s.*$/, '');
    const t = khongChuThich.trim();
    if (!t.startsWith('--') && t.endsWith(delim)) {
      buf.push(khongChuThich.slice(0, khongChuThich.lastIndexOf(delim)));
      day();
    } else {
      buf.push(dong);
    }
  }
  day();
  return cauLenh;
}

async function chayFileSql(conn, tenFile) {
  const noiDung = fs.readFileSync(path.join(SQL_DIR, tenFile), 'utf8');
  for (const cau of tachCauLenh(noiDung)) await conn.query(cau);
}

/** Tạo lại toàn bộ CSDL: bảng + thủ tục + dữ liệu mẫu. */
async function khoiTaoCsdl() {
  const conn = await mysql.createConnection(layCauHinh());
  try {
    for (const f of ['01_schema.sql', '02_procedures.sql', '03_seed.sql']) await chayFileSql(conn, f);
  } finally {
    await conn.end();
  }
}

/** Nạp lại dữ liệu mẫu (giữ nguyên bảng/thủ tục). */
async function napDuLieuMau() {
  const conn = await layPool().getConnection();
  try { await chayFileSql(conn, '03_seed.sql'); } finally { conn.release(); }
}

/** Gọi 1 stored procedure trả về dòng {ket_qua, thong_bao, ma_loi, nhat_ky}. */
async function goiThuTuc(conn, ten, thamSo) {
  const dauHoi = thamSo.map(() => '?').join(', ');
  const [ketQua] = await conn.query(`CALL ${ten}(${dauHoi})`, thamSo);
  const dong = Array.isArray(ketQua[0]) ? ketQua[0][0] : ketQua[0];
  return dong;
}

module.exports = { layPool, dongPool, khoiTaoCsdl, napDuLieuMau, goiThuTuc, tachCauLenh, layCauHinh, giaiThichLoi, DB_NAME };
