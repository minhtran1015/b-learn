# Bài 1. Khái niệm DataFrame

DataFrame trong Spark là một bảng phân tán có schema và tên cột rõ ràng.

## 1. DataFrame là gì
- Là cách nhìn dạng bảng trên dữ liệu phân tán.
- Dữ liệu được tổ chức theo cột có kiểu rõ ràng.
- Gần với cách suy nghĩ của SQL và các hệ dữ liệu quan hệ.

## 2. So sánh với RDD
- RDD thiên về hàng và mức thấp hơn.
- DataFrame có schema nên Spark dễ tối ưu hơn.
- DataFrame phù hợp cho phân tích có cấu trúc và các truy vấn kiểu SQL.

## 3. DataFrame và Dataset
- DataFrame linh hoạt và hỗ trợ nhiều ngôn ngữ.
- Dataset kiểm tra kiểu ở thời điểm biên dịch, chỉ hỗ trợ Scala và Java.

## 4. Kết luận
DataFrame là abstraction quan trọng nhất trong Spark hiện đại vì nó kết hợp được tính dễ dùng và khả năng tối ưu.