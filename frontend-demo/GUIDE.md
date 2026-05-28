# BLearn Frontend Demo

## Chạy demo

```bash
cd frontend-demo
npm install
npm run dev
```

Sau đó mở địa chỉ Vite hiển thị trong terminal, thường là `http://localhost:5173`.

## Đã làm

- Scaffold app React + Vite trong riêng thư mục `frontend-demo/`.
- Tạo layout chung gồm sidebar, topbar, search, profile và hệ thống card/button/progress thống nhất.
- Tạo dữ liệu giả hardcode tại `src/data/mockData.js`.
- Tạo các trang demo cơ bản: tổng quan, phân tích, gợi ý, danh sách khóa học, tổng quan khóa học, tài liệu, chi tiết tài liệu, bài tập, chi tiết bài tập, màn hình làm bài, cài đặt.
- Tách điều hướng thành 2 tầng: menu hệ thống luôn hiển thị, còn `Tài liệu học tập`, `Bài tập`, `Thảo luận` chỉ hiện khi đã vào một khóa học.
- Thêm các nút/đường dẫn chuyển trang bằng React Router để kiểm tra flow demo.

## Cấu trúc chính

```text
frontend-demo/
  src/
    components/      # Layout, sidebar, topbar, card dùng chung
    data/            # Mock data hardcode
    pages/           # Các màn hình demo
    App.jsx          # Khai báo routes
    styles.css       # Design system và responsive CSS
```
