# Bài 2. Nền tảng MapReduce

MapReduce là mô hình lập trình mà Google đã sử dụng thành công để xử lý các tập dữ liệu cực lớn.

## 1. Ý tưởng cốt lõi
- Người dùng chỉ cần định nghĩa hai hàm: map và reduce.
- Runtime bên dưới tự động song song hóa trên nhiều máy.
- Hệ thống cũng tự xử lý lỗi máy, giao tiếp mạng và cân bằng tải.

## 2. Nguồn gốc của MapReduce
- Tên gọi mượn từ lập trình hàm.
- map xử lý từng bản ghi độc lập.
- reduce nhóm và tổng hợp các giá trị có chung key.

## 3. Ví dụ WordCount
- Bài toán đếm tần suất từ trong bộ dữ liệu rất lớn.
- Đây là ví dụ kinh điển vì mô hình hóa rõ ràng dưới dạng key-value.

## 4. Giải pháp cốt lõi
- Dữ liệu WORM rất phù hợp với xử lý song song.
- Thay vì mang dữ liệu tới máy tính, ta mang tiến trình tính toán tới gần dữ liệu.
- Hệ thống runtime bổ sung phân tán, chịu lỗi, nhân bản và giám sát.

## 5. Kết luận
MapReduce phù hợp cho bài toán batch lớn, đơn giản hóa cách lập trình phân tán nhưng vẫn giữ được khả năng mở rộng và chịu lỗi.