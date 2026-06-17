# Bài 2. Các nguyên tắc quyết định

Thiết kế lưu trữ Big Data không bắt đầu từ công cụ, mà bắt đầu từ khối lượng công việc, cách truy cập dữ liệu và yêu cầu chịu lỗi.

## 1. Nguyên tắc cốt lõi
- Ưu tiên scale-out thay vì cố nâng cấp mãi một máy.
- Đưa tính toán đến gần nơi dữ liệu nằm.
- Dùng partitioning và replication để cân bằng tốc độ và độ tin cậy.
- Thiết kế với giả định rằng lỗi là bình thường.

## 2. Partitioning và Sharding
- Partitioning chia dữ liệu về mặt logic.
- Sharding là partitioning phân tán trên nhiều máy vật lý.

## 3. Replication
- Tạo nhiều bản sao trên các node khác nhau.
- Mục đích là tăng chịu lỗi, tăng sẵn sàng và giảm bottleneck.

## 4. CAP, BASE và PACELC
- CAP cho thấy hệ phân tán phải đánh đổi giữa consistency, availability và partition tolerance.
- BASE nới lỏng ACID để đạt mở rộng ngang tốt hơn.
- PACELC mở rộng câu hỏi: khi không có phân vùng, hệ thống ưu tiên latency hay consistency.

## 5. Kết luận
Một hệ thống lưu trữ tốt phải tồn tại được khi node, disk hoặc network gặp lỗi.