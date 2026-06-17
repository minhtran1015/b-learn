# Bài 2. Khi nào dữ liệu trở thành “lớn”? 

Dữ liệu được coi là Big Data khi nó vượt quá khả năng xử lý của một máy chủ đơn lẻ. Khi đó, bài toán không còn là lưu trữ hay tính toán đơn thuần, mà là vấn đề hệ thống.

## 1. Giới hạn của máy chủ đơn lẻ
Khi xử lý dữ liệu khổng lồ, hệ thống thường gặp các điểm nghẽn sau:
- Hết bộ nhớ RAM.
- Nghẽn cổ chai truy xuất đĩa.
- Quá tải CPU.
- Tắc nghẽn mạng.
- Rủi ro sập toàn bộ hệ thống khi một node hỏng.

## 2. Hai hướng mở rộng hệ thống

### Scale-Up / Vertical Scaling
- Nâng cấp máy hiện tại bằng cách tăng RAM, CPU, ổ cứng.
- Ưu điểm: đơn giản ở mức vận hành ban đầu.
- Nhược điểm: chi phí cao, chạm trần phần cứng nhanh và vẫn có single point of failure.

### Scale-Out / Horizontal Scaling
- Thêm nhiều máy rẻ hơn vào một cluster để chia sẻ tải.
- Ưu điểm: linh hoạt, chịu lỗi tốt, mở rộng dễ hơn.
- Đây là nền tảng của Hadoop, Spark và phần lớn hệ thống Big Data hiện đại.

## 3. Kết luận
Data trở thành “big” không chỉ vì kích thước, mà vì nó đòi hỏi cách kiến trúc khác: thay vì tăng sức mạnh một máy, ta phải phối hợp nhiều máy cùng làm việc.