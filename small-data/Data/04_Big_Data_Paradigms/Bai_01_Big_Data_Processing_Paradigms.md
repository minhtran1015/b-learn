# Bài 1. Các mô hình xử lý Big Data

Mô hình xử lý dữ liệu lớn là các phương pháp kiến trúc và tính toán được dùng để xử lý, lưu trữ và phân tích dữ liệu quy mô lớn một cách hiệu quả.

## 1. Batch Processing
- Xử lý khối lượng lớn dữ liệu tĩnh trong các công việc được lên lịch sẵn.
- Ưu điểm: thông lượng cao, mở rộng tốt, hệ sinh thái trưởng thành.
- Ví dụ: data warehousing, data mining, phân tích dự đoán.
- Framework tiêu biểu: Hadoop MapReduce, Spark, Hive.

## 2. Stream Processing
- Xử lý dữ liệu theo thời gian thực hoặc gần thời gian thực.
- Ưu điểm: độ trễ thấp, ra quyết định nhanh, phù hợp IoT và cảnh báo.
- Framework tiêu biểu: Flink, Storm, Kafka Streams.

## 3. Micro-batch Processing
- Chia dữ liệu thành các lô nhỏ rất ngắn.
- Cân bằng giữa độ trễ và thông lượng.
- Ví dụ: Spark Structured Streaming.

## 4. Lambda, Kappa và Unified Processing
- Lambda kết hợp batch và stream.
- Kappa chỉ dùng stream và replay dữ liệu lịch sử.
- Unified processing hướng tới một hệ thống duy nhất cho cả batch lẫn stream.

## 5. Cloud và Serverless
- Chạy trên hạ tầng cloud-native do nhà cung cấp quản lý.
- Không phải tự vận hành server.
- Trả tiền theo mức sử dụng và phù hợp workload biến động.

## 6. Kết luận
Lựa chọn mô hình xử lý phụ thuộc vào yêu cầu về độ trễ, quy mô dữ liệu, tính lặp lại và mức độ phức tạp của hệ thống.