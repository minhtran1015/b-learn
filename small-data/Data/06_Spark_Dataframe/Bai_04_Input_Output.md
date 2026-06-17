# Bài 4. Input/Output

Spark hỗ trợ nhiều định dạng nhập và xuất dữ liệu, nhưng định dạng cột như Parquet thường là lựa chọn tối ưu cho phân tích.

## 1. Vai trò của định dạng lưu trữ
- CSV và JSON tiện trao đổi nhưng không tối ưu cho phân tích lớn.
- Parquet và ORC là các định dạng cột giúp đọc nhanh và nén tốt.

## 2. Phân vùng dữ liệu
- Khi ghi dữ liệu có thể dùng partitionBy.
- Dữ liệu được tổ chức thành các thư mục vật lý theo giá trị cột.
- Truy vấn có thể bỏ qua phần lớn dữ liệu không liên quan.

## 3. Kết luận
Chọn định dạng và cách phân vùng ảnh hưởng trực tiếp đến tốc độ quét, kích thước lưu trữ và hiệu năng truy vấn.