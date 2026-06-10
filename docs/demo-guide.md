# Kịch Bản Trình Diễn Live Demo Hệ Thống Học Tập B-Learn

Tài liệu này hướng dẫn cách chuẩn bị môi trường, chạy các phím tắt và thực hiện kịch bản trình diễn tương tác khép kín (Closed-Loop Learning Analytics) phục vụ báo cáo Hội đồng.

---

## 🖥️ Cấu Hình Trình Diễn 3 Màn Hình Song Song (Recommended Layout)

Để tạo hiệu ứng thị giác và tính thuyết phục tốt nhất, hãy chia màn hình làm việc (hoặc sử dụng nhiều màn hình) theo cấu hình sau:

1. **Màn hình bên Trái (Giao diện người học):**
   - Trình duyệt Web mở địa chỉ: `http://localhost:8080` (hoặc IP Public của LoadBalancer nếu sẵn có).
   - Đăng nhập với tư cách sinh viên và mở mục **Phân tích học tập** (Analytics) hoặc trang **Làm bài tập** (Quiz).

2. **Màn hình ở Giữa (Lực lượng giám sát Stream - Terminal):**
   - Terminal chạy lệnh lọc dòng sự kiện thực tế nạp vào Kafka:
     ```bash
     make demo-smoke-test
     ```

3. **Màn hình bên Phải (Streamlit MLOps Dashboard & Gateway Logs):**
   - Trình duyệt Web mở địa chỉ Streamlit Dashboard (ví dụ: `http://135.171.193.190` hoặc local dev server) để theo dõi các cảnh báo đỏ và đồ thị thay đổi.

---

## 🛠️ Quy Trình Thực Hiện Demo

### Bước 1: Khởi động hệ thống
Từ thư mục dự án trên máy Mac, chạy lệnh chuẩn bị và đánh thức cụm tài nguyên:
```bash
make demo-prep
```
*Lưu ý: Chờ khoảng 1-2 phút cho các node AKS và Pod chuyển sang trạng thái Running.*

### Bước 2: Thiết lập kết nối
Chạy lệnh tự động mở port-forward ngầm về máy Mac cho cả API Gateway và Frontend:
```bash
make demo-connect
```
Kiểm tra truy cập:
- Frontend: `http://localhost:8080`
- API Gateway Swagger Docs: `http://localhost:8000/docs`

### Bước 3: Xem trạng thái rủi ro ban đầu (Baseline)
1. Đăng nhập vào trang Frontend.
2. Điều hướng tới trang **Phân tích học tập** (Analytics Page).
3. Ghi lại tỷ lệ Đỗ/Trượt hiện tại (Ví dụ: tỷ lệ Đỗ là `85%` dựa trên baseline dropout probability là `15%` trong parquet).

### Bước 4: Thực hiện kịch bản rẽ nhánh theo điểm số

#### Kịch bản A: Học viên nộp bài thi Đạt (Score $\ge$ 50%)
1. Vào trang làm bài tập (Quiz), chọn các câu trả lời đúng để đạt điểm số trên trung bình (Ví dụ: đúng 15/20 câu $\rightarrow$ 75%).
2. Nhấp nút **Nộp bài**.
3. **Quan sát:**
   - **Terminal ở giữa (Kafka Consumer):** Lập tức in ra bản tin JSON `assessment_submission` chứa `score: 75.0` và `student_id_hash`.
   - **Màn hình bên trái (UI Analytics):** Khi quay lại trang Phân tích học tập, tỉ lệ Đỗ tăng lên thêm `5%` (dropout probability giảm `0.05` từ `0.15` xuống `0.10` $\rightarrow$ Tỷ lệ đỗ hiển thị `90%`).
   - Hệ thống phản hồi thông báo: *"Nộp bài thành công! Năng lực cải thiện, rủi ro bỏ học đã giảm xuống!"*

#### Kịch bản B: Học viên nộp bài thi Yếu (Score < 50%)
1. Thực hiện làm bài tiếp theo, cố tình chọn sai để đạt điểm thấp (Ví dụ: chỉ trả lời đúng 2/20 câu $\rightarrow$ 10%).
2. Nhấp nút **Nộp bài**.
3. **Quan sát:**
   - **Terminal ở giữa (Kafka Consumer):** Bản tin JSON tiếp theo nhảy về với `score: 10.0`.
   - **Màn hình bên trái (UI Analytics):** Trang Phân tích học tập cập nhật, tỷ lệ Đỗ sụt giảm mạnh `10%` (dropout probability tăng thêm `0.10` từ `0.10` lên `0.20` $\rightarrow$ Tỷ lệ đỗ giảm còn `80%`).
   - Hệ thống phát cảnh báo màu đỏ: *"Cảnh báo: Kết quả dưới trung bình, nguy cơ bỏ học tăng cao!"*

---

## 🔄 Cách Reset Trạng Thái Để Trình Diễn Lại (Demo Loop Reset)

Để thực hiện lại demo từ đầu cho các nhóm chấm thi khác nhau mà không phải khởi động lại cluster, hãy dùng reset nhanh:
```bash
make demo-reset
```
*Lệnh này gọi API Gateway để giải phóng toàn bộ in-memory shifts và nạp lại baseline predictions từ đĩa. Tỷ lệ đỗ của học viên trên giao diện UI sẽ lập tức trả về mặc định `85%`.*

Nếu cần dọn sâu checkpoint và stream state trước một buổi demo lớn hoặc sau khi gặp lỗi khôi phục, dùng:
```bash
make demo-reset-deep
```

---

## 😴 Đóng Băng Tiết Kiệm Tài Nguyên (Sau Khi Kết Thúc Demo)
Sau khi kết thúc buổi báo cáo, hãy tắt cụm để bảo toàn credit Azure của bạn:
```bash
make streaming-suspend
make aks-stop
```
