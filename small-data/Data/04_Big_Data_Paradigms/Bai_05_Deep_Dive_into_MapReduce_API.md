# Bài 5. Đi sâu vào MapReduce API

MapReduce API cung cấp các lớp và kiểu dữ liệu cần thiết để xây dựng job phân tán.

## 1. Các lớp cốt lõi
- Mapper<Kin, Vin, Kout, Vout>.
- Reducer<Kin, Vin, Kout, Vout>.
- Partitioner<K, V>.
- Job để cấu hình đường dẫn, lớp xử lý và số reducer.

## 2. Vòng đời method
- setup chạy đầu job.
- map chạy cho mỗi cặp key/value.
- reduce chạy cho mỗi key cùng danh sách values.
- cleanup chạy cuối job.

## 3. Kiểu dữ liệu Hadoop
- Writable cho tuần tự hóa và giải tuần tự hóa.
- WritableComparable cho các key cần sắp xếp.
- IntWritable, LongWritable, Text và các lớp tương tự.

## 4. Xử lý dữ liệu phức tạp
- Có thể mã hóa tạm dưới dạng chuỗi Text.
- Cách chuẩn là tự định nghĩa Writable/Comparable.

## 5. Những lưu ý quan trọng
- Tránh tạo object liên tục trong reducer.
- Không dùng static để truyền dữ liệu giữa các node.
- Có thể đưa dữ liệu phụ vào job qua configuration hoặc distributed cache.

## 6. Kết luận
API của MapReduce khá thấp cấp, nhưng chính điều đó cho phép kiểm soát tốt partitioning, grouping và aggregation trong môi trường phân tán.