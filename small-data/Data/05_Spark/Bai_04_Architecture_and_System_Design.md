# Bài 4. Kiến trúc và thiết kế hệ thống

Kiến trúc Spark theo mô hình Driver - Worker, trong đó driver điều phối còn executors thực thi tính toán phân tán.

## 1. Các thành phần chính
- Spark Driver: chạy hàm main và tạo SparkContext.
- Cluster Manager: cấp phát tài nguyên như YARN, Mesos hoặc Standalone.
- Executors: chạy task trên worker nodes.

## 2. Cách dữ liệu được xử lý
- Code người dùng được serialize và gửi tới executors.
- Executors xử lý partitions tại chỗ để tận dụng data locality.
- Kết quả cuối cùng chỉ được trả về driver khi cần.

## 3. Kết luận
Thiết kế hệ thống Spark tốt là cân bằng giữa song song hóa, bộ nhớ, tài nguyên cluster và cách di chuyển dữ liệu.