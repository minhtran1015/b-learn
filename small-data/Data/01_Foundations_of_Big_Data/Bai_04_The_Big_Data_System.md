# Bài 4. Hệ thống Big Data

Một hệ thống Big Data không chỉ là nơi lưu dữ liệu. Nó là một chuỗi giá trị hoàn chỉnh biến dữ liệu thành hành động có ý nghĩa cho doanh nghiệp.

## 1. Chuỗi giá trị Big Data
Luồng cơ bản thường đi theo dạng:
- Nguồn dữ liệu.
- Thu thập dữ liệu.
- Lưu trữ dữ liệu.
- Xử lý dữ liệu.
- Phân tích dữ liệu.
- Ra quyết định hoặc tự động hành động.

## 2. Batch và Streaming

### Batch
- Xử lý khối lượng lớn dữ liệu lịch sử theo lô.
- Phù hợp với phân tích ngoại tuyến, kho dữ liệu và bài toán tổng hợp lớn.

### Streaming
- Xử lý dữ liệu liên tục khi nó vừa xuất hiện.
- Phù hợp với cảnh báo thời gian thực, giám sát và phát hiện gian lận.

## 3. Lambda và Kappa

### Lambda Architecture
- Kết hợp batch layer và speed layer.
- Ưu điểm: chính xác cao, chịu lỗi tốt.
- Nhược điểm: phức tạp, phải duy trì hai đường ống xử lý.

### Kappa Architecture
- Chỉ dùng stream processing.
- Dữ liệu lịch sử được xử lý bằng cách replay luồng.
- Ưu điểm: đơn giản hơn, chỉ cần một codebase.

## 4. Những thách thức kỹ thuật
- Khả năng mở rộng ngang.
- Tính chịu lỗi.
- Độ trễ.
- Chất lượng dữ liệu.
- Quản trị và bảo mật.

## 5. Kết luận
Giá trị của Big Data nằm ở toàn bộ pipeline. Nếu chỉ có lưu trữ mà không có xử lý và phân tích phù hợp thì dữ liệu vẫn chỉ là dữ liệu.