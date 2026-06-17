# Bài 2. Mô hình lập trình

RDD là cấu trúc dữ liệu cốt lõi của Spark. Nó thể hiện tập dữ liệu phân tán, có khả năng chịu lỗi và bất biến.

## 1. Đặc tính của RDD
- Resilient: có thể khôi phục dữ liệu nhờ lineage.
- Distributed: dữ liệu chia thành partitions trên nhiều worker.
- Dataset: là tập hợp object bất biến.

## 2. Transformations và Actions
- Transformations tạo RDD mới nhưng chưa chạy ngay.
- Actions kích hoạt tính toán thực sự và trả kết quả về driver hoặc ghi ra ngoài.

## 3. Lineage và caching
- Lineage ghi lại lịch sử tạo RDD.
- Caching/Persistence giúp tái sử dụng dữ liệu nhiều lần mà không tính lại từ đầu.

## 4. Kết luận
Mô hình lập trình của Spark rất mạnh vì kết hợp được tính khai báo, khả năng chịu lỗi và hiệu năng cao trên dữ liệu phân tán.