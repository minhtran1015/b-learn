# Bài 3. Thực thi và tối ưu hóa MapReduce

Tối ưu MapReduce tập trung vào việc chọn đúng số lượng mapper/reducer, giảm dữ liệu phải shuffle và xử lý độ lệch dữ liệu.

## 1. Chia nhỏ dữ liệu
- Dữ liệu đầu vào được chia thành các input split.
- Mỗi split thường tương ứng với một map task.
- Kích thước split tốt thường gần bằng block HDFS.
- Cần ưu tiên data locality để map task chạy gần nơi dữ liệu nằm.

## 2. Chọn số lượng task
- Số lượng map thường phụ thuộc vào tổng số block đầu vào.
- Số lượng reduce phụ thuộc vào số node, số container và mức độ cân bằng tải mong muốn.

## 3. Đặc điểm của MapReduce
- Phù hợp với dữ liệu siêu lớn và WORM.
- Yêu cầu hoàn thành toàn bộ map trước khi reduce.
- Chạy trên HDFS với các bước phụ trợ như combiner và partitioner.

## 4. Phạm vi ứng dụng
- Sort.
- WordCount.
- PageRank.
- Indexing.
- Các bài toán data mining và phân tích quy mô lớn.

## 5. Kết luận
Tối ưu MapReduce chủ yếu là giảm di chuyển dữ liệu, cân bằng tải và tránh nghẽn ở các khâu shuffle, partition hoặc data skew.