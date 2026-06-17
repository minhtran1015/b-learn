# Bài 4. Luồng thực thi một Job MapReduce

Khi một job được gửi lên hệ thống, dữ liệu và điều phối công việc sẽ đi qua nhiều bước nội bộ trước khi tạo ra kết quả cuối cùng.

## 1. Luồng submit job
- Client tạo job và cấu hình.
- Job được gửi lên JobTracker.
- Input split được tính ở phía client.
- Metadata và file jar được đẩy vào hệ thống.
- TaskTracker liên tục nhận task để chạy.

## 2. Luồng dữ liệu nội bộ
- Input file được cắt thành input split.
- InputFormat quyết định cách đọc file.
- RecordReader đọc thành cặp key/value.
- Mapper xử lý từng bản ghi.
- Dữ liệu trung gian có thể đi qua partitioner.
- Reducer tổng hợp dữ liệu.
- OutputFormat và RecordWriter ghi kết quả ra file.

## 3. Kết luận
Hiểu anatomy của job giúp dễ debug lỗi và hiểu vì sao một job MapReduce có thể chậm, lệch tải hoặc phát sinh bottleneck ở từng giai đoạn khác nhau.