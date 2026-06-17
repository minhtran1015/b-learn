# Bài 2. Biểu thức cột

Biểu thức cột là nền tảng của mọi biến đổi trên DataFrame.

## 1. Tư duy biểu thức cột
- Các thao tác như select, where, groupBy hay withColumn đều được mô tả qua biểu thức cột.
- Người viết code đang mô tả điều muốn làm, không phải chỉ cách thực thi chi tiết.

## 2. Cú pháp và hàm hỗ trợ
- Dùng data['age'] < 30 thay vì truy cập mơ hồ.
- Dùng các hàm trong pyspark.sql.functions để viết logic rõ ràng.
- Có thể tạo bảng tạm và viết Spark SQL khi logic phức tạp.

## 3. Kết luận
Viết theo biểu thức cột giúp Spark hiểu được ý định của truy vấn và tối ưu kế hoạch thực thi tốt hơn.