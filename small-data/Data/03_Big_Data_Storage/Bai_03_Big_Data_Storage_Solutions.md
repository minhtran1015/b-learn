# Bài 3. Các giải pháp lưu trữ Big Data

Hệ sinh thái lưu trữ Big Data đã tiến hóa từ RDBMS truyền thống sang hệ thống tệp phân tán, cloud object storage, data lake, lakehouse và cả lưu trữ gốc AI.

## 1. Sự tiến hóa của giải pháp lưu trữ
1. RDBMS: tốt cho dữ liệu có cấu trúc nhưng khó mở rộng lớn.
2. Distributed File Systems như GFS, HDFS: chia file thành block và sao chép dự phòng.
3. Cloud Object Storage: mở rộng mạnh, bền bỉ, truy cập qua API.
4. Data Lake: lưu dữ liệu thô với schema-on-read.
5. Lakehouse: kết hợp ưu điểm của lake và warehouse, có ACID và time travel.
6. AI-native storage: phục vụ vector search và dữ liệu nhiều chiều.

## 2. Một số lựa chọn phổ biến
- HDFS.
- Amazon S3 hoặc các object storage tương tự.
- Cassandra, HBase, MongoDB và các hệ NoSQL khác.
- Các định dạng cột như Parquet cho workload phân tích.

## 3. Kết luận
Không có một giải pháp lưu trữ nào là tốt nhất cho mọi bài toán. Lựa chọn đúng phụ thuộc vào truy cập dữ liệu, độ trễ, quy mô và kiểu workload.