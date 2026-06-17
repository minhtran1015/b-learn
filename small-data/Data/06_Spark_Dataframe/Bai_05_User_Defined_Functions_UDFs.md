# Bài 5. Hàm tự định nghĩa (UDFs)

Khi các hàm có sẵn của Spark không đủ cho logic nghiệp vụ, ta có thể dùng UDF. Tuy nhiên, phải cân nhắc kỹ vì UDF có thể làm giảm khả năng tối ưu.

## 1. Các mức độ thực thi
- Native Spark functions là nhanh nhất.
- Pandas UDF nhanh hơn UDF Python thường nhờ xử lý theo vector.
- Python UDF thường là chậm nhất vì phải chuyển đổi qua lại giữa JVM và Python.

## 2. Khi nào nên dùng
- Khi bài toán có logic đặc thù mà hàm có sẵn không hỗ trợ.
- Khi không còn lựa chọn nào tốt hơn từ hệ hàm mặc định.

## 3. Kết luận
UDF hữu ích nhưng không nên là lựa chọn mặc định. Nếu có thể, hãy ưu tiên các hàm native của Spark và biểu thức khai báo để tối ưu tốt hơn.