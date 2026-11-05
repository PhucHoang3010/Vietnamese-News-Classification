// Kết nối MySQL + tiện ích chạy file .sql (hỗ trợ lệnh DELIMITER như MySQL Workbench / mysql CLI)
const fs = require('fs');
const path = require('path');
const mysql = require('mysql2/promise');
require('dotenv').config({ path: path.join(__dirname, '..', '.env') });

const DB_NAME = 'dkhp';
const SQL_DIR = path.join(__dirname, '..', 'sql');

const cauHinh = {
  host: process.env.DB_HOST || '127.0.0.1',
  port: Number(process.env.DB_PORT || 3306),
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASSWORD || '',
  charset: 'utf8mb4_unicode_ci',
  dateStrings: true,
};

let pool;
function layPool() {
  if (!pool) {
    // Mỗi giao dịch giả lập cần 1 kết nối riêng (= 1 phiên làm việc riêng trên MySQL)
    pool = mysql.createPool({ ...cauHinh, database: DB_NAME, connectionLimit: 20, waitForConnections: true });
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
  const conn = await mysql.createConnection(cauHinh);
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

module.exports = { layPool, dongPool, khoiTaoCsdl, napDuLieuMau, goiThuTuc, tachCauLenh, DB_NAME };
