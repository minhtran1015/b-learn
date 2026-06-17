# Bài 1. Từ MapReduce đến Spark

Spark ra đời để khắc phục các hạn chế lớn nhất của MapReduce, đặc biệt là việc đọc ghi đĩa quá nhiều và xử lý lặp chậm.

## 1. Hạn chế của MapReduce
- Luồng dữ liệu một chiều nghiêm ngặt.
- Mỗi bước tính toán thường phải ghi tạm xuống đĩa.
- Không phù hợp với các bài toán lặp nhiều lần như machine learning hoặc truy vấn tương tác.

## 2. Mục tiêu của Spark
- Giữ dữ liệu trong bộ nhớ RAM càng lâu càng tốt.
- Tăng tốc độ xử lý cho các workload lặp và interactive.
- Vẫn giữ khả năng chịu lỗi, data locality và khả năng mở rộng.

## 3. RDD
- Spark giới thiệu Resilient Distributed Datasets để xử lý dữ liệu phân tán trên bộ nhớ an toàn và hiệu quả.

## 4. Kết luận
Spark là bước tiến tự nhiên khi MapReduce không còn đủ nhanh và linh hoạt cho các bài toán phân tích hiện đại.