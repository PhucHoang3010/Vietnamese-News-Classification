// npm run db:init — tạo CSDL dkhp, các bảng, stored procedure và dữ liệu mẫu
const { khoiTaoCsdl, giaiThichLoi } = require('./db');

khoiTaoCsdl()
  .then(() => console.log('✔ Đã tạo CSDL "dkhp": bảng, view, stored procedure và dữ liệu mẫu.'))
  .catch((e) => {
    console.error('✖ Khởi tạo thất bại: ' + giaiThichLoi(e));
    process.exit(1);
  });
