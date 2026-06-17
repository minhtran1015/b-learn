# Bài 3. Mô hình thực thi

Sức mạnh của Spark đến từ cách nó chuyển code thành DAG, chia thành stages và phân phối thành tasks trên cluster.

## 1. Job, DAG, Stage, Task
- Action tạo ra Job.
- Spark xây dựng DAG từ các transformations.
- DAG được chia thành các stages.
- Mỗi stage được chia thành nhiều tasks.

## 2. Lazy evaluation
- Transformations chỉ được ghi nhận chứ chưa thực thi ngay.
- Spark tối ưu trước khi chạy thật sự.

## 3. Narrow và wide transformation
- Narrow transformation có thể được pipelining trong cùng một stage.
- Wide transformation cần shuffle và thường tạo stage mới.

## 4. Ví dụ Word Count
- Đọc file thành partitions.
- Cắt từ và tạo cặp (word, 1).
- ReduceByKey gom và cộng số lần xuất hiện.

## 5. Kết luận
Mô hình thực thi của Spark giúp xử lý các bài toán lặp và tương tác nhanh hơn rất nhiều so với mô hình batch cứng nhắc kiểu MapReduce.