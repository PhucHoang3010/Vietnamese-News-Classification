// npm run db:init — tạo CSDL dkhp, các bảng, stored procedure và dữ liệu mẫu
const { khoiTaoCsdl } = require('./db');

khoiTaoCsdl()
  .then(() => console.log('✔ Đã tạo CSDL "dkhp": bảng, view, stored procedure và dữ liệu mẫu.'))
  .catch((e) => {
    console.error('✖ Khởi tạo thất bại:', e.message);
    console.error('  Kiểm tra MySQL đã chạy và thông tin DB_USER/DB_PASSWORD trong file .env');
    process.exit(1);
  });
