# Bài 3. Trình tối ưu hóa

Spark có một trình tối ưu hóa mạnh mẽ cho DataFrame và SQL, giúp tự động cải thiện truy vấn trước khi thực thi.

## 1. Vai trò của Catalyst
- Xây dựng logical plan và physical plan.
- Tự động loại bỏ cột thừa.
- Đẩy bộ lọc xuống sớm để giảm dữ liệu phải đọc.
- Chọn chiến lược phân vùng phù hợp hơn cho groupBy hoặc sort.

## 2. Vì sao quan trọng
- Vì người dùng chỉ mô tả kết quả mong muốn nên Spark có nhiều không gian để tối ưu.
- Trình tối ưu giúp giảm chi phí shuffle và giảm dữ liệu phải xử lý.

## 3. Kết luận
Optimizer là lý do quan trọng khiến DataFrame và SQL trong Spark thường hiệu quả hơn code xử lý thủ công ở mức thấp.