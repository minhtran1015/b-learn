# Kịch Bản Trình Diễn Live Demo Hệ Thống Học Tập B-Learn

Tài liệu này hướng dẫn cách chuẩn bị môi trường, chạy các phím tắt và thực hiện kịch bản trình diễn tương tác khép kín (Closed-Loop Learning Analytics) phục vụ báo cáo Hội đồng.

---

## 🖥️ Cấu Hình Trình Diễn 3 Màn Hình Song Song (Recommended Layout)

Để tạo hiệu ứng thị giác và tính thuyết phục tốt nhất, hãy chia màn hình làm việc (hoặc sử dụng nhiều màn hình) theo cấu hình sau:

1. **Màn hình bên Trái (Giao diện người học):**
   - Trình duyệt Web mở địa chỉ: `http://localhost:5173` khi chạy local dev.
   - Nếu trình diễn qua cluster, dùng `http://localhost:8080` sau khi port-forward / load balancer đã sẵn sàng.
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

Nếu bạn chạy local để demo nhanh, hãy mở 2 terminal riêng:
```bash
source .venv/bin/activate
python backend-api/serving_gateway.py

npm --prefix frontend-demo run dev
```

### Bước 2: Thiết lập kết nối
Chạy lệnh tự động mở port-forward ngầm về máy Mac cho cả API Gateway và Frontend:
```bash
make demo-connect
```
Kiểm tra truy cập:
- Frontend local dev: `http://localhost:5173`
- Frontend qua tunnel: `http://localhost:8080`
- API Gateway Swagger Docs: `http://localhost:8000/docs`
- API Gateway health: `http://localhost:8000/health`

### Bước 3: Xem trạng thái rủi ro ban đầu (Baseline)
1. Đăng nhập vào trang Frontend.
2. Điều hướng tới trang **Phân tích học tập** (Analytics Page).
3. Ghi lại tỷ lệ Đỗ/Trượt hiện tại.
4. Ở dưới heatmap, kiểm tra nhãn nguồn dữ liệu:
   - `live_event_log` = đang lấy dữ liệu live từ backend.
   - `seeded_cache` = đang dùng dữ liệu fallback khởi tạo.

### Bước 4: Thực hiện kịch bản rẽ nhánh theo điểm số

#### Kịch bản A: Học viên nộp bài thi Đạt (Score $\ge$ 50%)
1. Vào trang làm bài tập (Quiz), chọn các câu trả lời đúng để đạt điểm số trên trung bình (Ví dụ: đúng 15/20 câu $\rightarrow$ 75%).
2. Nhấp nút **Nộp bài**.
3. **Quan sát:**
   - **Gateway logs:** xuất hiện `POST /submit-assessment` và `GET /recommendations/{student_hash}`.
   - **Màn hình bên trái (UI Analytics):** khi quay lại trang Phân tích học tập, các khối `Thời gian học tuần này`, `Chi tiết phiên học gần đây`, và radar BKT sẽ thay đổi theo payload backend.
   - **Nhãn nguồn dữ liệu:** đổi sang `live_event_log` nếu event log đã có tương tác mới.
   - Hệ thống phản hồi thông báo: *"Nộp bài thành công!"* và hiển thị rủi ro/độ thành thạo mới.

#### Kịch bản B: Học viên nộp bài thi Yếu (Score < 50%)
1. Thực hiện làm bài tiếp theo, cố tình chọn sai để đạt điểm thấp (Ví dụ: chỉ trả lời đúng 2/20 câu $\rightarrow$ 10%).
2. Nhấp nút **Nộp bài**.
3. **Quan sát:**
   - **Gateway logs:** vẫn có request `POST /submit-assessment`.
   - **Màn hình bên trái (UI Analytics):** `dropout_probability`, `passRate` và `Chi tiết phiên học gần đây` cập nhật theo event mới.
   - **Nguồn dữ liệu** vẫn phải hiện `live_event_log` nếu bạn vừa tạo tương tác.
   - Hệ thống phát cảnh báo phù hợp với điểm số mới.

---

## 🔄 Cách Reset Trạng Thái Để Trình Diễn Lại (Demo Loop Reset)

Để thực hiện lại demo từ đầu cho các nhóm chấm thi khác nhau mà không phải khởi động lại cluster, hãy dùng reset nhanh:
```bash
make demo-reset
```
*Lệnh này gọi API Gateway để giải phóng toàn bộ in-memory shifts và nạp lại baseline predictions từ đĩa/cache. Giao diện sẽ quay về trạng thái ban đầu, nhưng nếu chưa xoá localStorage thì vẫn nên refresh trang hoặc đăng nhập lại.*

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

---

## ✅ Checklist Nhanh Trước Khi Vào Phòng Demo

1. `python backend-api/serving_gateway.py` đang chạy và `http://127.0.0.1:8000/health` trả `200`.
2. `npm --prefix frontend-demo run dev` đang chạy và mở `http://localhost:5173`.
3. Đã đăng nhập tài khoản demo `quan@blearn.test / 123456`.
4. Ở Analytics page, dòng nguồn dữ liệu hiển thị `live_event_log` sau khi click/nộp bài.
5. Nếu dùng AKS, `make demo-connect` đã mở tunnel và không còn token cũ trong localStorage.
