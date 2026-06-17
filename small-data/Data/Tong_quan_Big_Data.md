# TỔNG QUAN VỀ KỸ THUẬT VÀ CÔNG NGHỆ DỮ LIỆU LỚN (BIG DATA)

## 1. Từ Dữ liệu đến Trí tuệ: Mô hình DIKW
Một trong những mục tiêu tối thượng của các hệ thống Big Data là biến những luồng dữ liệu thô khổng lồ thành các quyết định mang tính chiến lược. Quá trình này tuân theo mô hình **DIKW (Data - Information - Knowledge - Wisdom)**, tương đương với pipeline: *Thu thập Dữ liệu → Xử lý → Phân tích → Ra quyết định*.

### **D - Data (Dữ liệu thô)**
* **Định nghĩa:** Là các tín hiệu, sự kiện thô chưa qua xử lý, không có ngữ cảnh hoặc sự diễn giải.
* **Đặc điểm:** Có thể có cấu trúc hoặc phi cấu trúc, chưa mang ý nghĩa tự thân, khối lượng rất lớn (nhật ký hệ thống, luồng cảm biến, hình ảnh, văn bản...).
* **Ví dụ:** Cảm biến giao thông ghi nhận: `Thời gian: 08:00:02 | Số xe: 120 | Vận tốc trung bình: 18 km/h | Vị trí: Ngã tư A`. Ở bước này, ta chỉ có các con số, không có kết luận nào.
* **Thành phần hệ thống tương ứng:** Hệ thống lưu trữ phân tán (Distributed Storage).

### **I - Information (Thông tin)**
* **Định nghĩa:** Dữ liệu đã được xử lý, cấu trúc hóa, tổng hợp và đặt vào ngữ cảnh. Nó trả lời cho các câu hỏi: *Ai? Cái gì? Khi nào? Ở đâu?*
* **Ví dụ:** Từ log thô tổng hợp lại thành: `"Phát hiện tắc nghẽn giao thông tại Ngã tư A trong giờ cao điểm buổi sáng (7:45 - 8:30 AM), vận tốc giảm 40%"`. Ta đã biết có tắc nghẽn, nhưng chưa biết tại sao.
* **Thành phần hệ thống tương ứng:** Các hệ thống Trích xuất, Biến đổi, Tải (ETL / Aggregation).

### **K - Knowledge (Kiến thức)**
* **Định nghĩa:** Thông tin được kết hợp với kinh nghiệm, mô hình học máy (ML), phân tích thống kê và kiến thức chuyên ngành để tìm ra quy luật. Trả lời câu hỏi: *Như thế nào? Tại sao?*
* **Ví dụ:** Phân tích cho thấy: `"Tắc nghẽn xảy ra vào mỗi ngày trong tuần do lưu lượng xe từ trường học gần đó và nhịp đèn giao thông chưa tối ưu."` Chúng ta đã hiểu được mối quan hệ nhân - quả.
* **Thành phần hệ thống tương ứng:** Các Engine Học máy và Phân tích (ML / Analytics Engines).

### **W - Wisdom (Trí tuệ)**
* **Định nghĩa:** Kiến thức được áp dụng cùng với sự đánh giá, tư duy chiến lược, cân nhắc đạo đức và tính bền vững. Trả lời câu hỏi: *Chúng ta nên làm gì?*
* **Ví dụ:** Ra quyết định: `"Triển khai hệ thống điều khiển đèn tín hiệu thích ứng động và áp dụng giờ học lệch ca để giảm ùn tắc dài hạn."`
* **Thành phần hệ thống tương ứng:** Hệ thống Hỗ trợ Ra quyết định (Decision Support Systems).

---

## 2. Vị trí và Vai trò của Kỹ thuật Big Data

Nhiều người thường nhầm lẫn Big Data với Khoa học Dữ liệu (Data Science) hay Trí tuệ Nhân tạo (AI). Cần phân định rõ:
* **Data Science:** Tập trung vào việc khai phá insight và mô hình hóa.
* **AI (Trí tuệ nhân tạo):** Tập trung vào khả năng học hỏi và suy luận của máy móc.
* **Big Data:** **Là bài toán Kỹ thuật (Engineering).** Nó tập trung vào việc xây dựng cơ sở hạ tầng, hệ thống phân tán và khả năng mở rộng (Scalability) để xử lý dữ liệu khổng lồ.

**Tại sao phải học hệ thống Big Data?**
* **Giới hạn hệ thống truyền thống:** Dữ liệu đang tăng trưởng theo cấp số nhân (khối lượng lớn, tốc độ cao, đa dạng). Các hệ quản trị cơ sở dữ liệu truyền thống không thể đáp ứng.
* **Nền tảng cho AI:** Không có hạ tầng Big Data thì không thể có AI ở quy mô lớn (Scalable AI). AI phụ thuộc hoàn toàn vào nguồn dữ liệu này.
* **Lợi thế cạnh tranh:** Giúp doanh nghiệp chuyển từ Dữ liệu → Insight → Hành động, từ đó tối ưu hóa vận hành, dự đoán xu hướng và đưa ra quyết định theo thời gian thực.

---

## 3. Khi nào Dữ liệu trở thành "Dữ liệu lớn"? Vấn đề của Hệ thống

Dữ liệu được coi là "Big" khi nó vượt quá khả năng xử lý của một hệ thống máy chủ đơn lẻ (Single-node systems). 

### Giới hạn của máy chủ đơn lẻ
Khi hệ thống phải xử lý lượng dữ liệu khổng lồ, nó sẽ đối mặt với các điểm lỗi (Failure Points) sau:
* Hết bộ nhớ RAM (Out of Memory).
* Nghẽn cổ chai truy xuất ổ cứng (Disk I/O Bottleneck).
* Quá tải CPU (CPU Saturation).
* Tắc nghẽn mạng (Network Congestion).
* Rủi ro sập toàn bộ hệ thống nếu máy chủ hỏng (Single Node Failure).

### Giải pháp: Scale-Up vs. Scale-Out
Để giải quyết giới hạn này, có hai phương pháp tiếp cận:
1.  **Mở rộng theo chiều dọc (Scale-Up / Vertical Scaling):** Nâng cấp máy chủ hiện tại bằng cách mua RAM, CPU, Ổ cứng mạnh hơn. 
    * *Nhược điểm:* Rất đắt đỏ, chạm "trần" phần cứng rất nhanh và vẫn tồn tại rủi ro Single Point of Failure.
2.  **Mở rộng theo chiều ngang (Scale-Out / Horizontal Scaling):** Thêm nhiều máy tính (node) rẻ tiền hơn vào mạng lưới để tạo thành một cụm (Cluster) cùng chia sẻ khối lượng công việc. 
    * *Ưu điểm:* Khả năng mở rộng linh hoạt (Elastic), có tính chịu lỗi cao (Fault tolerance). **Đây chính là cốt lõi của công nghệ Big Data (như Hadoop, Spark).**

---

## 4. Định nghĩa và Đặc trưng của Big Data (Các chữ V)

"Dữ liệu lớn" không chỉ là sự to lớn về kích thước, mà còn là **sự phức tạp**. Nó được định nghĩa chuẩn xác nhất qua các đặc trưng "V":

### 3 Chữ V Cốt lõi:
1.  **Volume (Dung lượng):** Lượng dữ liệu khổng lồ. Ngày nay, dữ liệu không đo bằng Terabyte mà bằng Petabyte (PB), Exabyte (EB) hay Zettabyte (ZB - 1 tỷ Terabyte). Ví dụ: Máy bay Airbus A350 tạo ra ~2.5 TB/ngày; xe tự lái tạo ra 4-6 TB/ngày; dự kiến dữ liệu IoT đạt 73.1 ZB vào năm 2025.
2.  **Velocity (Tốc độ):** Tốc độ dữ liệu được tạo ra và yêu cầu tốc độ xử lý tương ứng. Việc ra quyết định chậm trễ đồng nghĩa với việc đánh mất cơ hội. (Ví dụ: Phát hiện gian lận thẻ tín dụng theo thời gian thực, giám sát y tế, hoặc các chiến dịch khuyến mãi e-Promotions dựa trên vị trí hiện tại của khách hàng).
3.  **Variety (Đa dạng):** Dữ liệu đến từ nhiều nguồn và nhiều định dạng khác nhau: Dữ liệu quan hệ, văn bản, bán cấu trúc (XML), dữ liệu đồ thị (mạng xã hội), dữ liệu dạng luồng (streaming), hình ảnh, video... Để có insight tốt, hệ thống phải liên kết được tất cả các dạng dữ liệu này.

---

## 5. Giá trị Doanh nghiệp và Ứng dụng Thực tiễn

Big Data không phải là một thuật ngữ sáo rỗng (buzzword) mà là động lực đổi mới trong hầu hết các ngành công nghiệp (Chính phủ, Tài chính, Sản xuất, Giáo dục, Y tế, Giao thông, IoT...):
* **Cải thiện trải nghiệm khách hàng:** Cá nhân hóa nội dung, hệ thống gợi ý.
* **Tối ưu hóa vận hành & giảm chi phí:** Quản lý chuỗi cung ứng, dự báo hàng tồn kho.
* **Phát hiện gian lận & bảo mật:** Phân tích giao dịch tài chính trong tích tắc để chặn giao dịch đáng ngờ.
* **Bảo trì dự đoán (Predictive Maintenance):** Dự đoán khi nào máy móc hoặc bộ phận xe hỏng.

---

## 6. Lời khuyên khi đối mặt với Big Data (Theo Jim Gray)

1.  **Ưu tiên Scale-Out thay vì Scale-Up.**
2.  **Đưa hệ thống phân tích đến nơi chứa dữ liệu (Move the analysis to the data).**
3.  **Tập trung vào "20 truy vấn cốt lõi".**
4.  **"Go from working to working" (Từ hoạt động đến hoạt động).**

# HỆ THỐNG DỮ LIỆU LỚN VÀ ỨNG DỤNG (Phần 2)

## 1. 20 Nhóm Truy Vấn Phổ Biến Trong Big Data
Jim Gray đã khuyên nên tập trung vào "20 truy vấn cốt lõi". Dưới đây là các phân nhóm truy vấn phổ biến nhất khi làm việc với hệ thống dữ liệu lớn:

### 1.1. Truy xuất & Tìm kiếm (Data Retrieval & Search)
* Tìm kiếm bản ghi cụ thể theo ID (ví dụ: tìm người dùng, sản phẩm, hoặc kết quả thí nghiệm).
* Lấy danh sách các bản ghi gần đây nhất (ví dụ: 100 giao dịch mới nhất).
* Tìm kiếm toàn văn bản (Full-text search) trên các trường dữ liệu lớn (ví dụ: tìm từ khóa trong hàng triệu bài báo khoa học).
* Tìm kiếm các bản ghi khớp một phần (ví dụ: gợi ý tự động - autocomplete khi gõ từ khóa).

### 1.2. Tổng hợp & Thống kê (Aggregation & Statistics)
* Tính tổng số lượng (ví dụ: có bao nhiêu khách hàng mua sắm trong tháng này?).
* Tính toán các giá trị: Tổng (Sum), Trung bình (Average), Nhỏ nhất (Min), Lớn nhất (Max) (ví dụ: nhiệt độ trung bình của cảm biến, doanh số cao nhất).
* Nhóm dữ liệu và tổng hợp (Group by & aggregate) (ví dụ: tổng doanh thu theo từng khu vực).

### 1.3. Phân tích theo Thời gian (Time-Based Analysis)
* Tìm các bản ghi trong một khoảng thời gian cụ thể (ví dụ: giao dịch từ 1/1 đến 1/2).
* So sánh xu hướng theo thời gian (ví dụ: tăng trưởng doanh thu năm nay so với năm ngoái).
* Tính trung bình động (Moving averages) (ví dụ: trung bình lượng truy cập website trong 7 ngày xoay vòng).

### 1.4. Kết nối & Quan hệ (Join & Relationships)
* Kết hợp (Join) hai hoặc nhiều tập dữ liệu (ví dụ: liên kết thông tin khách hàng với lịch sử mua hàng của họ).
* Tìm các mục thường xuất hiện cùng nhau (ví dụ: các sản phẩm khách hàng hay mua kèm với nhau).
* Phát hiện dữ liệu thiếu hoặc không khớp (ví dụ: sinh viên đã đăng ký môn nhưng không có tên trong điểm danh).

### 1.5. Xếp hạng & Không gian địa lý (Ranking & Geospatial)
* **Xếp hạng & Sắp xếp:** Tìm top N kết quả (ví dụ: 10 cuốn sách bán chạy nhất); Phát hiện bất thường/ngoại lai (ví dụ: chi tiêu thẻ tín dụng cao bất thường).
* **Xử lý Không gian địa lý:** Tìm bản ghi trong một bán kính nhất định (ví dụ: các bệnh viện trong bán kính 10km); Tìm điểm lân cận gần nhất (ví dụ: trạm thời tiết gần nhất với vị trí hiện tại).

### 1.6. Học máy & Phát hiện bất thường (ML & Anomaly Detection)
* Tìm các bản ghi tương đồng (ví dụ: nhóm khách hàng có hành vi mua sắm giống nhau).
* Phát hiện và gộp các bản ghi trùng lặp.
* Nhận diện các đợt tăng/giảm đột ngột (ví dụ: lượng truy cập website tăng vọt bất thường).
* Phát hiện các giá trị bị thiếu (ví dụ: báo cáo ngày dự kiến bị trống).

---

## 2. Hệ Thống Dữ Liệu Lớn (The Big Data System)

### 2.1. Chuỗi giá trị Big Data (Value Chain)
Chuỗi giá trị tập trung vào việc chuyển hóa từ dữ liệu thành giá trị cốt lõi cho doanh nghiệp. Quá trình này bao gồm:
* Nguồn dữ liệu (Data Sources) → Thu thập (Ingestion) → Lưu trữ (Storage) → Xử lý (Processing) → Phân tích (Analytics) → Ra quyết định/Hành động (Decision/Action).

### 2.2. Xử lý Hàng loạt (Batch) vs. Xử lý Luồng (Streaming)
Hệ thống Big Data có hai kiểu kiến trúc chính để xử lý luồng công việc:

**Kiến trúc Lambda (Lambda Architecture):**
* **Ý tưởng:** Kết hợp cả xử lý hàng loạt (Batch) và xử lý thời gian thực (Stream).
* **Cấu trúc:** Gồm 2 đường ống (pipeline): Batch layer (xử lý dữ liệu lịch sử) và Speed layer (xử lý dữ liệu thời gian thực), kết quả được tổng hợp tại Serving layer.
* **Ưu điểm:** Độ chính xác cao, dễ mở rộng, chịu lỗi tốt.
* **Nhược điểm:** Phức tạp, phải duy trì hai bộ mã nguồn (codebases) song song.

**Kiến trúc Kappa (Kappa Architecture):**
* **Ý tưởng:** Chỉ sử dụng duy nhất nền tảng xử lý luồng (Stream processing).
* **Cấu trúc:** Chỉ có 1 đường ống. Dữ liệu lịch sử được xử lý bằng cách "phát lại" (replay) luồng dữ liệu.
* **Ưu điểm:** Đơn giản, chỉ cần duy trì một bộ mã nguồn.
* **Nhược điểm:** Phụ thuộc hoàn toàn vào hiệu suất của engine xử lý luồng.

### 2.3. Vòng đời & Thách thức kỹ thuật
* **Tính lặp lại:** Xử lý Big Data là một quá trình lặp lại (Iterative), không phải tuyến tính (Linear). Nó bao gồm các vòng lặp phản hồi để tinh chỉnh mô hình, thu thập dữ liệu liên tục và đào tạo lại mô hình liên tục.
* **Định lý CAP:** Trong hệ thống phân tán, bạn chỉ có thể đảm bảo tối đa 2 trong 3 yếu tố: Tính nhất quán (Consistency), Tính sẵn sàng (Availability), và Khả năng chịu lỗi phân vùng (Partition Tolerance). Việc thiết kế hệ thống là sự đánh đổi (trade-offs) giữa các yếu tố này.
* **Thách thức Kỹ thuật:** Khả năng mở rộng ngang, tính chịu lỗi, chất lượng dữ liệu, quản trị & bảo mật, và độ trễ.

---

## 3. Các Tầng Kiến Trúc Khuyên Dùng (Target Stack)

Kỹ thuật Big Data xây dựng các hệ thống để giải quyết sự hạn chế của máy tính đơn lẻ (ví dụ bài toán đếm từ - Word Count: thay vì chạy tuần tự trên 1 CPU giới hạn RAM, ta chạy song song trên nhiều node với khả năng chịu lỗi).

1.  **Tầng Quản lý tài nguyên (Resource Management Layer):** Quản lý lập lịch, cấp phát tài nguyên, xử lý lỗi (Ví dụ: YARN, Kubernetes).
2.  **Tầng Lưu trữ (Storage Layer):** Lưu trữ phân tán, đảm bảo tính cục bộ của dữ liệu (Data Locality) và sao chép dự phòng (Ví dụ: HDFS, Object Storage).
3.  **Tầng Xử lý (Processing Layer):** Xử lý Batch, Stream và lặp lại (Ví dụ: MapReduce, Spark, Flink).

**💡 Khi nào KHÔNG nên dùng Big Data?**
Đừng sử dụng hệ thống Big Data nếu: Dữ liệu của bạn nhỏ, không có nhu cầu mở rộng, khối lượng công việc đơn giản. Việc cố áp dụng sẽ dẫn đến rủi ro "thiết kế quá mức cần thiết" (Over-engineering), gây lãng phí tài nguyên và phức tạp hóa vấn đề.

---

## 4. Nghề Nghiệp Và Kỹ Năng Trong Ngành Big Data

Ngành Big Data yêu cầu sự phối hợp của nhiều vai trò chuyên biệt:

*   **Data Scientists (Nhà khoa học dữ liệu):** Thu thập, phân tích, diễn giải khối lượng lớn dữ liệu để tìm ra mô hình, xu hướng và mối quan hệ.
*   **Big Data Engineers & Architects (Kỹ sư/Kiến trúc sư Big Data):** Thiết kế, xây dựng và quản lý hạ tầng phần mềm cốt lõi (pipelines) để các Data Scientist có nền tảng phân tích.
*   **Big Data Developers (Lập trình viên Big Data):** Áp dụng công nghệ như Hadoop, Spark với ngôn ngữ Java, Python, Scala để xử lý dữ liệu.
*   **Big Data Analysts & Specialists:** Phân tích dữ liệu thực tế, khám phá xu hướng ẩn, giúp lãnh đạo đưa ra các quyết định kinh doanh chiến lược.

### Các nhóm kỹ năng cốt lõi:
1.  **Lưu trữ và Xử lý (Store & Process):** Hiểu biết về CSDL quy mô lớn, Kỹ nghệ phần mềm, Kỹ sư hệ thống/mạng.
2.  **Phân tích và Mô hình hóa (Analyse & Model):** Học máy (Machine Learning), Truy xuất thông tin (Information Retrieval), Suy luận và biểu diễn tri thức.
3.  **Thấu hiểu và Thiết kế (Understand & Design):** Lý thuyết ra quyết định, Phân tích trực quan (Visual analytics), Nhận thức học.
# HỆ THỐNG DỮ LIỆU LỚN VÀ ỨNG DỤNG (Phần 3)

## 1. Mô hình hóa dữ liệu trong Hệ thống Big Data (Data Modeling)

### 1.1. Tầm quan trọng của dữ liệu
"Big Data", "Data Science", "Data Lakes", "Visual Analytics" - tất cả những xu hướng này đều hướng tới cùng một mục tiêu: Khám phá, xây dựng mô hình và hỗ trợ ra quyết định. Tuy nhiên, để "Deep Learning", "Phân tích thống kê" hay "Phân tích kinh doanh" hoạt động hiệu quả, **Dữ liệu cần phải được mô hình hóa, làm sạch và liên kết!**

### 1.2. Thách thức với "Medium Data" (Dữ liệu mức trung bình)
Trong thực tế, ngoài các công ty Web lớn hay hệ thống giám sát đặc thù, phần lớn dữ liệu chúng ta đối mặt chưa sẵn sàng để phân tích ngay:
*   **Dữ liệu phân tán:** Nằm ở nhiều hệ thống khác nhau, cần kết hợp với các bộ dữ liệu công cộng (public datasets) hoặc thông qua API (ví dụ: Twitter API).
*   **Chất lượng dữ liệu kém:** Dữ liệu có thể chứa giá trị bị thiếu (missing values), giá trị sai lệch (spurious values).
*   **Thiếu đặc trưng (Features):** Các thuộc tính (features) cần thiết để chạy các mô hình dự đoán (Machine Learning) chưa có sẵn mà phải thông qua trích xuất.

### 1.3. Quá trình chuyển đổi dữ liệu
*   **Mục tiêu:** Dữ liệu thô (Raw data: Hình ảnh, Gen, Văn bản) + Trích xuất đặc trưng & Làm sạch (Wrangling) → Dữ liệu có cấu trúc (Structured data: Các trường, thực thể, đối tượng, đặc trưng học máy).
*   Mối quan hệ cấu trúc (Structural relationships) giữa các dữ liệu đôi khi chính là những đặc trưng (features) quan trọng nhất.
*   **Các kỹ thuật mô hình hóa:**
    *   **Linked Data:** Tìm mẫu thông qua tính kết nối (Cụm - Clusters, Đường đi - Paths).
    *   **Knowledge Graphs:** Đồ thị tri thức (Gồm các Lớp, Lớp con, Thực thể và Thuộc tính).
    *   **Dynamic Data:** Theo dõi sự thay đổi theo thời gian để dự báo tương lai.
    *   **Tabular Data:** Dữ liệu dạng bảng (Quan hệ) và thực hiện kết nối (Joins/Lookups) với các dịch vụ bên ngoài.

---

## 2. Các mô hình cơ sở dữ liệu hiện đại (SOTA Data Models)

Hệ sinh thái cơ sở dữ liệu hiện nay rất đa dạng, mỗi loại tối ưu cho một bài toán cụ thể:

1.  **RDBMS (CSDL Quan hệ truyền thống):** (Ví dụ: MySQL, PostgreSQL). Cấu trúc bảng (hàng & cột), dùng SQL, tuân thủ nghiêm ngặt chuẩn ACID. Tốt nhất cho dữ liệu có cấu trúc và ứng dụng giao dịch (Transactions).
2.  **NoSQL:** (Ví dụ: MongoDB, Cassandra, Redis, Neo4j). Thiết kế để mở rộng ngang và linh hoạt (Key-Value, Document, Column-Family, Graph). Phù hợp cho dữ liệu bán cấu trúc và phi cấu trúc.
3.  **NewSQL:** (Ví dụ: Google Spanner, CockroachDB). Kết hợp tính nhất quán (ACID) của RDBMS và khả năng mở rộng của NoSQL. Dùng cho hệ thống giao dịch quy mô cực lớn.
4.  **Graph DB (CSDL Đồ thị):** (Ví dụ: Neo4j, TigerGraph). Tối ưu để xử lý các mối quan hệ (Nodes & Edges). Rất mạnh trong phân tích mạng lưới, phát hiện gian lận, hệ thống gợi ý.
5.  **Vector DB:** (Ví dụ: Pinecone, FAISS). Lưu trữ dữ liệu vector nhiều chiều. Là "trái tim" của các hệ thống AI hiện đại, tìm kiếm sự tương đồng (Similarity search) và học máy.
6.  **Realtime DB:** (Ví dụ: Firebase, Apache Ignite). Hỗ trợ xử lý dữ liệu với độ trễ cực thấp và thông lượng cao. Dùng trong giao dịch tài chính, game, IoT.
7.  **GPU DB:** (Ví dụ: Kinetica, OmniSci). Sử dụng GPU để xử lý song song khối lượng dữ liệu khổng lồ, tăng tốc khối lượng công việc AI và phân tích thời gian thực.
8.  **AI-Driven DB:** (Ví dụ: Google BigQuery ML). Tích hợp sẵn AI/ML để tự động hóa tối ưu hóa chỉ mục, truy vấn, dự đoán và phát hiện bất thường.
9.  **Multi-Modal DB:** (Ví dụ: ArangoDB, MarkLogic). Hỗ trợ nhiều mô hình dữ liệu (Document, Graph, Key-Value...) trong cùng một hệ thống, giúp phá bỏ các "ốc đảo dữ liệu" (Data silos).

---

## 3. Kiến Trúc Căn Bản của Hệ Thống Big Data (Modern Big Data Stack)

Sáu yếu tố cốt lõi bắt buộc đối với một nền tảng Big Data:
1.  **Khám phá & Điều hướng:** Có khả năng tìm kiếm đa nguồn, quản lý Metadata.
2.  **Hiệu suất cực cao:** Đưa phân tích đến gần dữ liệu (MPP, Spark).
3.  **Quản lý dữ liệu phi cấu trúc:** (Hadoop ecosystem, NLP, lưu trữ ảnh/video).
4.  **Phân tích dữ liệu đang chuyển động (Data in Motion):** Xử lý luồng thời gian thực (Kafka, Flink) cho IoT.
5.  **Thư viện phân tích phong phú:** In-database Machine Learning, trực quan hóa.
6.  **Tích hợp và Quản trị:** Đảm bảo luồng dữ liệu thông suốt, quản lý chất lượng (MDM) và bảo mật.

### Các thành phần của ngăn xếp (Stack Components)
1.  **Nguồn dữ liệu (Data Sources):** Có cấu trúc (RDBMS), Bán cấu trúc (JSON, Logs), Phi cấu trúc (Text, Images).
2.  **Thu thập dữ liệu (Data Ingestion):** 
    *   Thu thập Batch (Sqoop, Flume) hoặc Stream (Kafka, NiFi).
    *   Bao gồm: Lấy dữ liệu, điều phối, định dạng, thu thập metadata và xác thực ban đầu.
3.  **Lưu trữ dữ liệu (Data Storage):** 
    *   Từ RDBMS, NoSQL đến Data Lakes (HDFS, Amazon S3).
    *   Bao gồm: Phân vùng (Partitioning), Sao chép dự phòng (Replication), phân quyền và bảo mật.
4.  **Xử lý dữ liệu (Data Processing):** 
    *   Sử dụng Spark, MapReduce (Batch) hoặc Storm, Flink (Real-time).
    *   **Data Wrangling:** Làm sạch + Cấu trúc hóa + Chuyển đổi + Hợp nhất.
    *   **Data Curation:** Làm sạch + Chuyển đổi + Tích hợp + Thêm chú thích/Metadata + Quản lý chất lượng.
5.  **Phân tích dữ liệu (Data Analytics):** Qua 4 cấp độ:
    *   *Mô tả (Descriptive):* Chuyện gì đã xảy ra?
    *   *Chẩn đoán (Diagnostic):* Tại sao lại xảy ra?
    *   *Dự đoán (Predictive):* Chuyện gì sẽ xảy ra? (Machine Learning).
    *   *Đề xuất (Prescriptive):* Chúng ta nên làm gì?
6.  **Ra quyết định / Hành động (Decision / Action):** Hỗ trợ ra quyết định, tự động hóa, tích hợp vào hệ thống vận hành thông qua báo cáo (Tableau, Power BI) và Dashboard (Grafana).

---

## 4. Nền Tảng Dữ Liệu Hiện Đại (Modern Data Platform - Lakehouse + AI Stack)
*(Phần này bài giảng giới thiệu về các giải pháp thương mại/đám mây toàn diện)*
Các nền tảng hiện đại đang hướng tới mô hình kiến trúc kết hợp (Lakehouse) và tích hợp sâu công cụ AI, tiêu biểu như:
*   Cloudera Data Platform
*   Databricks Intelligent Platform
*   IBM Cloud Pak for Data
*   Microsoft Fabric

# HỆ THỐNG DỮ LIỆU LỚN VÀ ỨNG DỤNG (Phần 4)

## 1. Phân tích Dữ liệu Lớn (Big Data Analytics)

### 1.1. Định nghĩa và Sai lầm thường gặp
*   **Định nghĩa:** Phân tích Dữ liệu Lớn là quá trình kiểm tra các tập dữ liệu lớn và đa dạng nhằm khám phá ra các mẫu ẩn (hidden patterns), mối tương quan, xu hướng thị trường và sở thích của khách hàng.
*   **Sai lầm phổ biến (Misconception):** Nhiều người cho rằng "Nhiều dữ liệu hơn = Nhiều trí tuệ hơn" (More data = more wisdom). Thực tế, nếu không có kiến trúc hệ thống phù hợp, mô hình phân tích chuẩn và sự am hiểu lĩnh vực (domain understanding), dữ liệu khổng lồ sẽ chỉ trở thành:
    *   Tiếng ồn (Noise).
    *   Gánh nặng chi phí lưu trữ.
    *   Rủi ro cho doanh nghiệp.

### 1.2. Mục tiêu: Từ Dữ liệu đến Tri thức và Hành động
Mục tiêu tối thượng là chuyển hóa dữ liệu thô thành nhận thức một phần và sau đó là các quyết định hành động:
*   **Phát hiện quy luật:** Dữ liệu thô → Các mẫu → Hiểu biết một phần (Ví dụ: "Hiển thị doanh số theo khu vực và danh mục sản phẩm").
*   **Kiểm định giả thuyết:** Quan sát → Đặt giả thuyết → Thử nghiệm trên mẫu → Đánh giá ý nghĩa thống kê (Ví dụ: "Hành vi F dẫn đến rủi ro O cao hơn").
*   **Quy trình CORBA:** Collect (Thu thập) → Extrapolate (Ngoại suy) → Recognize (Nhận diện) → Build (Xây dựng) → Apply (Áp dụng).

### 1.3. Phân tích Big Data bao gồm những công đoạn nào?
1.  **Thu thập & Truy cập:** Tìm kiếm và lấy dữ liệu.
2.  **Nhào nặn dữ liệu (Wrangling):** Định dạng lại dữ liệu thô.
3.  **Tích hợp & Biểu diễn:** Thể hiện các mối quan hệ giữa các dữ liệu.
4.  **Làm sạch & Lọc:** Xử lý dữ liệu kém chất lượng.
5.  **Giả thuyết, Truy vấn, Phân tích & Mô hình hóa:** Chuyển dữ liệu thành thông tin.
6.  **Thấu hiểu, Lặp lại & Khám phá:** Xây dựng tri thức.
*   *Lưu ý về Đạo đức:* Phải bảo vệ dữ liệu, tuân thủ nguyên tắc thống kê và không trình bày kết quả gây hiểu lầm.

### 1.4. Khoa học Dữ liệu (Data Science): Huyền thoại vs. Thực tế
*   **Kỳ vọng ảo (Myth):** Chỉ cần nạp dữ liệu vào các thuật toán học máy (Machine Learning) phức tạp là hệ thống sẽ tự động "đẻ" ra insight. (Dữ liệu + Thuật toán = Tri thức).
*   **Thực tế (Reality):** Cần sự can thiệp của con người để áp đặt mô hình, chọn lọc đặc trưng. Deep Learning có thể tự chọn lọc đặc trưng, nhưng không nên vứt bỏ những kiến thức chuyên gia đã biết! (Dữ liệu + Sáng suốt của con người + Thuật toán + Quá trình lặp = Tri thức).

Trong thực tế, **80-90% công việc của một dự án Data Science** không phải là chạy mô hình ML, mà là:
*   Làm việc với chuyên gia để hiểu miền ứng dụng, giả định, câu hỏi.
*   Lập danh mục và phân tích nguồn dữ liệu.
*   Nhào nặn (Wrangling), trích xuất và tích hợp dữ liệu.
*   Làm sạch dữ liệu đã nhào nặn.

---

## 2. Các Ứng Dụng Tiềm Năng & Bức Tranh Toàn Cảnh (Applications & Landscape)

### 2.1. Các lĩnh vực ứng dụng tiềm năng
*   **Y tế & Chăm sóc sức khỏe:** Phân tích dự đoán bệnh tật (ung thư, tim mạch); Phân tích ảnh y khoa bằng AI; Xử lý dữ liệu hệ gen (Y học cá nhân hóa); Quản lý dịch tễ học và tài nguyên bệnh viện.
*   **Giáo dục & Nghiên cứu:** Học tập cá nhân hóa (Adaptive learning); Dự đoán kết quả học tập để hỗ trợ sinh viên có nguy cơ; Đưa ra quyết định chính sách giáo dục dựa trên dữ liệu.
*   **Kinh tế & Kinh doanh:** Phân tích thị trường & hành vi người tiêu dùng; Quản lý rủi ro tài chính & chống gian lận; Tối ưu hóa chuỗi cung ứng; Marketing cá nhân hóa; Dự đoán thị trường chứng khoán.
*   **Xã hội & Dịch vụ công:** Thành phố thông minh (tối ưu giao thông, quản lý rác thải); Dự đoán và phòng chống tội phạm; Quản lý thảm họa.
*   **An ninh Quốc gia & Quốc phòng:** An ninh mạng & tình báo mối đe dọa; Chiến lược và hoạt động quân sự (Hậu cần); Kiểm soát biên giới.
*   **Môi trường & Tính Bền vững:** Giám sát biến đổi khí hậu; Cảnh báo sớm thiên tai; Nông nghiệp chính xác (Precision Farming); Bảo tồn đa dạng sinh học.

### 2.2. Khi nào doanh nghiệp CẦN giải pháp Big Data?
Doanh nghiệp nên cân nhắc nâng cấp lên Big Data khi:
1.  **Dung lượng dữ liệu tăng quá nhanh:** Hạ tầng hiện tại không chứa nổi (Ví dụ: hàng triệu giao dịch bán lẻ mỗi ngày).
2.  **Cần xử lý thời gian thực:** Ra quyết định ngay lập tức (Ví dụ: phát hiện gian lận thẻ ngân hàng).
3.  **Dữ liệu phi cấu trúc/Đa định dạng:** Không thể nhét vừa các cột/hàng truyền thống (Ví dụ: phân tích cảm xúc trên mạng xã hội).
4.  **Vấn đề hiệu suất:** CSDL quan hệ truyền thống phản hồi truy vấn quá chậm.
5.  **Cần tích hợp Analytics và AI nâng cao:** Cần chạy Machine Learning, Deep Learning.
6.  **Cần khả năng mở rộng linh hoạt:** Khối lượng công việc lên xuống thất thường, cần nền tảng Cloud.
7.  **Muốn ra quyết định dựa trên dữ liệu:** Để tạo lợi thế cạnh tranh.

### 2.3. Những thách thức hiện tại
*   Chất lượng dữ liệu và công đoạn làm sạch.
*   Chi phí lưu trữ và tính toán (Compute cost).
*   Vấn đề bảo mật và quyền riêng tư.
*   Sự thiếu hụt kỹ năng/nhân sự về Kỹ sư dữ liệu và Phân tích.
*   Khó khăn trong việc phá vỡ các "ốc đảo dữ liệu" (Data silos) giữa các phòng ban.

### 2.4. Tương lai của Big Data
*   Phân tích tự trị (Autonomous analytics) được thúc đẩy bởi AI.
*   Sự phát triển của Edge Computing (Điện toán biên).
*   Sự bùng nổ của hệ thống IoT và thiết bị cảm biến.
*   Khả năng ra quyết định theo thời gian thực ở quy mô toàn cầu.
*   Tầm quan trọng ngày càng tăng của Quản trị dữ liệu có trách nhiệm (Data governance).

---

## 3. Tổng kết Chương Mở Đầu
*   Dữ liệu lớn (Big Data) xuất hiện khi Dung lượng (Volume), Tốc độ (Velocity) và Độ đa dạng (Variety) vượt quá khả năng của các hệ thống truyền thống.
*   Nền tảng Big Data hiện đại dựa vào kiến trúc phân tán (Distributed architectures) để lưu trữ và xử lý có thể mở rộng.
*   Hệ sinh thái bao gồm các đường ống dữ liệu (pipelines), kiến trúc, vòng đời và các vai trò công việc chuyên biệt.
*   Công nghệ lõi (như Hadoop, Spark, nền tảng streaming, Lakehouse) cho phép phân tích quy mô cực lớn.
*   Big Data là động lực cho AI, phân tích thời gian thực và các dịch vụ thông minh.

# HỆ THỐNG DỮ LIỆU LỚN VÀ ỨNG DỤNG (Phần 5: Lưu trữ Dữ liệu Lớn)

## 1. Giới thiệu chung (Introduction)
*   **Định nghĩa:** Lưu trữ dữ liệu lớn đề cập đến cơ sở hạ tầng và công nghệ được thiết kế để lưu trữ, quản lý hiệu quả khối lượng lớn dữ liệu có cấu trúc, bán cấu trúc và phi cấu trúc.
*   **Tầm quan trọng:** Là nền tảng thiết yếu để xử lý các tập dữ liệu khổng lồ sinh ra từ IoT, AI, phân tích kinh doanh và điện toán đám mây.
*   **Đặc điểm chính:** Khả năng mở rộng (Scalability), Tính sẵn sàng cao và Bền bỉ (High availability and durability), Kiến trúc phân tán (Distributed architecture), Hiệu quả chi phí (Cost efficiency).
*   **Sự khác biệt cốt lõi:** Dữ liệu có tính bền bỉ và đắt đỏ (Data is persistent and expensive), trong khi tính toán lại co giãn (Compute is elastic). Lưu trữ quyết định hiệu suất và chi phí của toàn bộ hệ thống.

## 2. Sự tiến hóa của các giải pháp lưu trữ
1.  **RDBMS (Hệ quản trị CSDL Quan hệ):** Dữ liệu có cấu trúc, tuân thủ ACID, mở rộng dọc. Khó đáp ứng quy mô Big Data.
2.  **Hệ thống tệp phân tán (Distributed File Systems - GFS, HDFS):** Chia file thành các block, sao chép dự phòng để chịu lỗi. Tối ưu cho xử lý Batch. Nhược điểm là quản lý phức tạp và không phải thiết kế gốc trên Cloud.
3.  **Lưu trữ đối tượng trên Đám mây (Cloud Object Storage):** Lưu dữ liệu dưới dạng Object (File + Metadata). Mở rộng vô hạn, siêu bền, trả tiền theo mức sử dụng, truy cập qua API (Ví dụ: Amazon S3, Google Cloud Storage).
4.  **Data Lake (Hồ dữ liệu):** Lưu trữ dữ liệu thô (mọi định dạng). Áp dụng Schema-on-read. Là nền tảng cho phân tích Big Data.
5.  **Lakehouse:** Kết hợp ưu điểm của Data Lake và Data Warehouse. Hỗ trợ giao dịch ACID, kiểm soát schema, và "du hành thời gian" (time travel - versioning). (Ví dụ: Delta Lake, Apache Iceberg).
6.  **Lưu trữ gốc AI (AI-native Storage):** Thiết kế cho ML, hỗ trợ vector search và dữ liệu nhiều chiều (Ví dụ: Vector DB như Pinecone).

## 3. Các Nguyên Tắc Quyết Định (Decisive Principles)

Tại sao lại cần lưu trữ phân tán? Vấn đề cốt lõi của siêu máy tính truyền thống (SAN) là chi phí mạng để chuyển hàng Terabyte dữ liệu đến CPU xử lý (Seek vs. Scans). 
*   **Giải pháp của Big Data:** *"Đừng di chuyển dữ liệu đến các máy tính, hãy mang các máy tính đến chỗ chứa dữ liệu!"* (Move workers to the data). Bằng cách kết hợp khả năng lưu trữ và tính toán trên cùng một Node (co-locate storage and compute), ta giảm thiểu tối đa độ trễ mạng. 

### 3.1. Phân mảnh (Partitioning vs. Sharding)
*   **Partitioning:** Chia nhỏ dữ liệu về mặt logic để tăng hiệu suất (thường nằm trên cùng một máy ảo/database). Có hai cách là chia theo chiều dọc (cột) hoặc chiều ngang (hàng).
*   **Sharding (Distributed Partitioning):** Là hình thức chia ngang nhưng phân bổ dữ liệu ra **nhiều máy chủ vật lý khác nhau** (Nodes) để tăng khả năng mở rộng (Scalability). Thường sử dụng hàm Băm (Hash function) để phân bổ dữ liệu một cách đồng đều và có thể dự đoán được.

### 3.2. Sao chép dự phòng (Replication)
*   Tạo ra nhiều bản sao (copies) của dữ liệu trên các máy chủ khác nhau.
*   **Mục đích:** Tăng cường khả năng chịu lỗi (Fault tolerance), tránh điểm nghẽn cổ chai (bottlenecks) và lỗi một điểm (Single point of failures), tăng tính sẵn sàng (Availability).

### 3.3. Định lý CAP và Tính nhất quán (Consistency)
Khi dữ liệu bị phân tán và sao chép ở nhiều nơi, việc đảm bảo tất cả các bản sao đều giống hệt nhau (Consistency) trở thành một thách thức lớn.
*   **Định lý CAP:** Trong một hệ thống phân tán, bạn chỉ có thể đảm bảo **tối đa 2 trong 3** yếu tố sau tại cùng một thời điểm:
    1.  **C - Consistency (Tính nhất quán):** Mọi node đều trả về cùng một dữ liệu mới nhất.
    2.  **A - Availability (Tính sẵn sàng):** Hệ thống luôn phản hồi truy vấn (ngay cả khi một số node chết).
    3.  **P - Partition Tolerance (Khả năng chịu lỗi phân vùng):** Hệ thống vẫn hoạt động khi mạng kết nối giữa các node bị đứt gãy.

### 3.4. Từ ACID đến BASE
*   **SQL (ACID):** Chú trọng tính Nhất quán mạnh (Strong consistency), thường đánh đổi tính sẵn sàng hoặc khả năng phân vùng (CA hoặc CP).
*   **NoSQL (BASE):** Để đạt tốc độ và khả năng mở rộng ngang, NoSQL nới lỏng các quy tắc ACID và áp dụng **BASE**:
    *   **B**asically **A**vailable: Đảm bảo tính sẵn sàng.
    *   **S**oft-State: Trạng thái hệ thống có thể thay đổi theo thời gian.
    *   **E**ventual Consistency (Nhất quán cuối cùng): Thay vì đồng bộ ngay lập tức, các bản sao dữ liệu sẽ dần dần (eventually) đồng nhất với nhau sau một khoảng thời gian.
*   **Tunable Consistency (Nhất quán có thể điều chỉnh):** Nhiều hệ thống NoSQL cho phép điều chỉnh luật Đọc/Ghi (W + R > N hoặc W + R <= N) để cân bằng giữa Tốc độ và Tính nhất quán.

### 3.5. Định lý PACELC (Mở rộng của CAP)
PACELC giải quyết câu hỏi: "Khi *không có* lỗi mạng phân vùng (Else), hệ thống sẽ chọn gì?".
*   **P**artition -> Choose **A**vailability or **C**onsistency.
*   **E**lse -> Choose **L**atency (Độ trễ thấp) or **C**onsistency (Nhất quán).

# HỆ THỐNG DỮ LIỆU LỚN VÀ ỨNG DỤNG (Phần 6 Mở rộng: Vận hành Kỹ thuật và Thực hành)

## 1. Cơ chế hoạt động nội bộ của HDFS (HDFS Inside)

Thay vì để dữ liệu đi qua NameNode (gây nghẽn cổ chai), HDFS thiết kế để Client tương tác trực tiếp với các DataNode sau khi lấy được "bản đồ" (Metadata).

### 1.1. Quá trình Đọc dữ liệu (Read)
1. **Yêu cầu:** Client kết nối với NameNode (NN) để yêu cầu đọc một file.
2. **Phản hồi vị trí:** NN trả về cho Client danh sách các Block của file đó và vị trí các DataNode đang lưu trữ chúng. *Đặc biệt: Danh sách DataNode được sắp xếp theo mức độ gần gũi về mặt mạng lưới (Proximity) so với Client.*
3. **Đọc trực tiếp:** Client kết nối trực tiếp đến các DataNode để tải block về (không đi qua NN).
4. **Xử lý lỗi:** Nếu một DataNode bị chết giữa chừng, Client sẽ tự động kết nối với DataNode khác đang chứa bản sao (replica) của block đó.

### 1.2. Quá trình Ghi dữ liệu (Write)
1. **Yêu cầu:** Client yêu cầu NN tạo một file mới.
2. **Chỉ định vị trí:** NN kiểm tra quyền, tạo bản ghi metadata và chỉ định cho Client biết nên ghi các block vào những DataNode nào.
3. **Ghi theo luồng (Pipeline):** Client ghi dữ liệu trực tiếp vào DataNode đầu tiên. DataNode này sẽ tự động chuyển tiếp dữ liệu sang DataNode thứ 2 (bản sao 1), và Node 2 chuyển sang Node 3 (bản sao 2). 
4. **Đảm bảo độ tin cậy:** Nếu có Node sập trong lúc ghi, NN sẽ phát hiện sự thiếu hụt bản sao và tự động ra lệnh nhân bản bù đắp sau đó.

---

## 2. Giao diện và Lệnh thao tác với HDFS (HDFS Interface & CLI)

HDFS cung cấp Web UI (để giám sát trực quan) và Command Line Interface (để thao tác trực tiếp). Cú pháp lệnh CLI của Hadoop rất giống với lệnh hệ thống Linux.

### Các lệnh Client cơ bản (Dành cho người dùng/Lập trình viên):
*   **Tạo thư mục mới trong HDFS:** 
    `hadoop fs -mkdir /user/dis/books`
*   **Liệt kê nội dung thư mục:** 
    `hadoop fs -ls /user/dis/`
*   **Copy file từ máy Local (máy tính của bạn) lên HDFS:** 
    `hadoop fs -copyFromLocal /home/docs/bigdata.txt /user/dis/`
*   **Copy file từ HDFS về máy Local:** 
    `hadoop fs -copyToLocal /user/dis/tinydata.txt /home/docs/`
*   **Kiểm tra tình trạng các block của hệ thống (FS Check):** 
    `hdfs fsck / -files -blocks`
*   **Copy song song khối lượng lớn (Distributed Copy):**
    `hadoop distcp folder1 folder2`

*(Ngoài ra còn có các lệnh quản trị `Admin Commands` như quản lý quota, safe mode, và `Daemon Commands` để khởi động/dừng các node).*

---

## 3. Phân biệt các mô hình lưu trữ: File vs. Block vs. Object

Để hiểu tại sao Cloud Object Storage (như Amazon S3) lại thống trị, ta cần phân biệt 3 loại hình lưu trữ cốt lõi:

| Tiêu chí | File Storage (Hệ thống tệp) | Block Storage (Lưu trữ khối) | Object Storage (Lưu trữ đối tượng) |
| :--- | :--- | :--- | :--- |
| **Tổ chức dữ liệu** | Cây thư mục phân cấp (Hierarchical) | Địa chỉ khối (Block addressing) | Không gian phẳng (Flat namespace) |
| **Khả năng mở rộng** | Bị giới hạn bởi cấu trúc cây | Bị giới hạn bởi dung lượng ổ đĩa | **Mở rộng vô hạn (Highly scalable)** |
| **Hiệu năng** | Tốt cho dữ liệu có cấu trúc/nội bộ | I/O tốc độ cực cao (Độ trễ siêu thấp) | Tối ưu cho dữ liệu lớn, phi cấu trúc |
| **Ứng dụng tiêu biểu** | Thư mục chia sẻ (Google Drive, NFS) | Database (RDBMS), Ổ cứng máy ảo (SAN) | Cloud Backup, Data Lake, Media Streaming |

**Ưu điểm của Object Storage:** Rẻ, bền bỉ (áp dụng Erasure Coding thay vì chỉ nhân bản), dễ dàng gọi qua API.
**Nhược điểm:** Độ trễ cao, không phù hợp để chạy Database Transactional (các giao dịch cập nhật nhỏ lẻ, liên tục).

---

## 4. Kiến trúc Dữ liệu Hiện đại & Xu hướng Tương lai

### 4.1. Sự tiến hóa: Data Lake -> Data Lakehouse
*   **Data Lake:** Nơi đổ mọi loại dữ liệu thô vào. Rất linh hoạt, chi phí cực rẻ (do dùng Object Storage). *Khuyết điểm:* Dễ biến thành "Đầm lầy dữ liệu" (Swamp) do không có giao dịch ACID, khó xóa/sửa đổi.
*   **Data Lakehouse:** Thêm một lớp "Định dạng bảng" (Table Formats như Apache Iceberg, Delta Lake) lên trên Data Lake. Nó mang lại khả năng kiểm soát schema, hỗ trợ ACID (đảm bảo tính toàn vẹn) và tính năng Time Travel (truy vấn dữ liệu ở một thời điểm trong quá khứ).

### 4.2. Xu hướng Tương lai (Future Trends)
1.  **Hybrid Cloud Storage:** Kết hợp linh hoạt giữa lưu trữ tại chỗ (On-premise - bảo mật cao) và Đám mây (Cloud - co giãn tốt).
2.  **AI-driven Storage Optimization:** Dùng AI để tự động tối ưu hóa tốc độ truy xuất và dọn dẹp dữ liệu.
3.  **Edge & IoT Storage:** Đưa bộ nhớ đến gần các thiết bị biên (Edge) thay vì gửi tất cả về trung tâm để giảm độ trễ (latency).
4.  **Cải tiến Erasure Coding:** Thay thế dần Replication (nhân bản tốn kém) bằng các thuật toán mã hóa khôi phục dữ liệu thông minh, tiết kiệm dung lượng phần cứng.
5.  **Quantum Storage:** Nghiên cứu lưu trữ tốc độ siêu cao bằng công nghệ lượng tử.

---
**💡 Tổng kết chương (Takeaway):**
Khi thiết kế hệ thống Big Data, **đừng bắt đầu từ Công cụ (Tools), hãy bắt đầu từ Khối lượng công việc (Workload).** Cách ứng dụng truy cập dữ liệu (Access patterns: tuần tự hay ngẫu nhiên, đọc nhiều hay ghi nhiều) sẽ quyết định bạn nên chọn HDFS, Object Storage hay cấu trúc Lakehouse.

# MÔ HÌNH XỬ LÝ DỮ LIỆU LỚN: MAPREDUCE (Toàn tập chi tiết)

## 1. Các Mô Hình Xử Lý Dữ Liệu Lớn (Big Data Processing Paradigms)
Mô hình xử lý dữ liệu lớn đề cập đến các phương pháp kiến trúc và tính toán khác nhau được sử dụng để xử lý, lưu trữ và phân tích dữ liệu quy mô lớn một cách hiệu quả.

### 1.1. Xử lý Hàng loạt (Batch Processing Paradigm)
*   **Định nghĩa:** Xử lý khối lượng lớn dữ liệu tĩnh trong các công việc được lên lịch trước (xử lý ngoại tuyến - offline).
*   **Ưu điểm:** Thông lượng cao (High throughput), có khả năng mở rộng cho các tập dữ liệu lớn, hệ sinh thái trưởng thành, tiết kiệm chi phí, phù hợp cho các tính toán phức tạp và hỗ trợ xử lý dữ liệu quy mô lớn.
*   **Trường hợp sử dụng (Use cases):** Kho dữ liệu (Data warehousing), khai phá dữ liệu (Data mining), và phân tích dự đoán.
*   **Framework tiêu biểu:** Hadoop MapReduce, Apache Spark, Hive.

### 1.2. Xử lý Luồng (Stream Processing Paradigm)
*   **Định nghĩa:** Xử lý dữ liệu theo thời gian thực (hoặc gần thời gian thực) ngay khi nó chảy từ các nguồn đa dạng.
*   **Ưu điểm:** Độ trễ thấp, mang lại insight theo thời gian thực, tính toán liên tục, cho phép ra quyết định ngay lập tức, hỗ trợ ứng dụng IoT, và nâng cao trải nghiệm khách hàng.
*   **Trường hợp sử dụng:** Phân tích thời gian thực, phát hiện gian lận, giám sát & cảnh báo, xử lý dữ liệu cảm biến IoT.
*   **Framework tiêu biểu:** Apache Flink (Xử lý luồng gốc), Apache Storm (Xử lý sự kiện thời gian thực), Kafka Streams.

### 1.3. Xử lý Vi lô (Micro-batch Processing)
*   **Định nghĩa:** Xử lý dữ liệu thành các lô nhỏ trong khoảng thời gian rất ngắn (gần thời gian thực).
*   **Ưu điểm:** Đơn giản hơn xử lý luồng thực sự (true streaming), có khả năng chịu lỗi, cân bằng tốt giữa độ trễ và thông lượng.
*   **Trường hợp sử dụng:** Dashboard hiển thị gần thời gian thực, xử lý log, ETL tăng dần (incremental ETL).
*   **Framework tiêu biểu:** Spark Structured Streaming.

### 1.4. Kiến trúc Lambda
*   **Định nghĩa:** Kiến trúc lai (hybrid) kết hợp cả đường ống Batch và Streaming để phân tích cả dữ liệu lịch sử và dữ liệu thời gian thực.
*   **Ưu điểm:** Độ chính xác cao (nhờ Batch layer), độ trễ thấp (nhờ Speed layer), có khả năng chịu lỗi.
*   **Trường hợp sử dụng:** Hệ thống phân tích quy mô lớn, phân tích thời gian thực kết hợp lịch sử, các nền tảng dữ liệu phức tạp.
*   **Framework tiêu biểu:** Hadoop + Spark + Kafka, Storm / Flink.

### 1.5. Kiến trúc Kappa
*   **Định nghĩa:** Kiến trúc chỉ dùng luồng (Stream-only), nơi mọi quá trình xử lý đều được thực hiện qua luồng (cả dữ liệu thời gian thực và lịch sử). Dữ liệu Batch chính là việc "phát lại" (replay) các luồng.
*   **Ưu điểm:** Kiến trúc đơn giản hơn, đường ống hợp nhất, dễ bảo trì hơn.
*   **Trường hợp sử dụng:** Hệ thống hướng sự kiện (Event-driven systems), nền tảng phân tích thời gian thực, kiến trúc dựa trên log.
*   **Framework tiêu biểu:** Apache Kafka, Apache Flink, Kafka Streams.

### 1.6. Xử lý Hợp nhất (Unified Processing - SOTA)
*   **Định nghĩa:** Mô hình xử lý đơn lẻ xử lý cả Batch và Streaming trong cùng một hệ thống (Hợp nhất lô + luồng). Lấy luồng làm mô hình mặc định.
*   **Ưu điểm:** Đơn giản hóa việc phát triển, API nhất quán, giảm độ phức tạp của hệ thống.
*   **Trường hợp sử dụng:** Nền tảng dữ liệu hiện đại, phân tích Lakehouse, truy vấn thời gian thực kết hợp lịch sử.
*   **Framework tiêu biểu:** Apache Spark (structured streaming), Apache Flink, Beam / Dataflow.

### 1.7. Điện toán Đám mây & Serverless (Cloud & Serverless Paradigm)
*   **Định nghĩa:** Mô hình dựa trên đám mây nguyên bản (cloud-native) nơi việc xử lý dữ liệu được thực thi trên hạ tầng do nhà cung cấp quản lý với tài nguyên tính toán serverless theo yêu cầu.
*   **Đặc điểm chính:** Không cần quản lý hạ tầng (serverless); Khả năng mở rộng co giãn; Trả tiền theo mức sử dụng (Pay-as-you-go); Thực thi hướng sự kiện.
*   **Ưu điểm:** Giảm chi phí vận hành; Khả năng mở rộng và tính sẵn sàng cao; Triển khai và phát triển nhanh hơn; Tiết kiệm chi phí cho các khối lượng công việc biến động.
*   **Trường hợp sử dụng:** Đường ống dữ liệu hướng sự kiện; Xử lý dữ liệu thời gian thực; ETL/ELT trên đám mây; Suy luận ML (ML inference) & microservices.
*   **Dịch vụ tiêu biểu:** AWS Lambda, Google Cloud Functions, Azure Functions; AWS Glue, Google Dataflow, Azure Data Factory; BigQuery, Snowflake, Databricks Serverless.

---

## 2. Nền Tảng MapReduce (MapReduce Fundamentals)

MapReduce là mô hình lập trình mà Google đã sử dụng thành công để xử lý các tập dữ liệu cực lớn (khoảng 20.000 petabyte mỗi ngày).
*   Người dùng chỉ định việc tính toán thông qua hai hàm **map** và **reduce**.
*   Hệ thống runtime (môi trường thực thi) bên dưới tự động song song hóa việc tính toán trên các cụm máy tính lớn.
*   Hệ thống cũng tự xử lý các lỗi máy móc, giao tiếp mạng hiệu quả và các vấn đề hiệu suất.

### 2.1. MapReduce là gì? (Nguồn gốc)
*   Thuật ngữ được mượn từ Ngôn ngữ chức năng (ví dụ: Lisp).
*   **Ví dụ tính tổng bình phương:**
    *   `(map square '(1 2 3 4))` -> Output: `(1 4 9 16)` [Xử lý từng bản ghi tuần tự và độc lập].
    *   `(reduce + '(1 4 9 16))` -> `(+ 16 (+ 9 (+ 4 1)))` -> Output: `30` [Xử lý tập hợp tất cả các bản ghi theo lô].
*   **Bài toán thực tế (WordCount):** Đếm tần suất các từ trong một tập dữ liệu khổng lồ (như bộ dữ liệu Wikipedia hoặc toàn bộ tác phẩm của Shakespeare).

### 2.2. Sự tiến hóa của bài toán đếm từ và Vấn đề Quy mô
Nếu giải quyết bài toán đếm từ từ đầu, ta sẽ gặp các vấn đề:
1.  **Một máy (Single thread):** Tốc độ chậm.
2.  **Đa luồng (Multi-thread):** Cần dùng "khóa" (Lock) trên dữ liệu dùng chung -> giảm hiệu suất.
3.  **Tách bộ đếm (Separate counters):** Giải quyết được việc không cần Lock.
4.  **Dữ liệu quy mô Peta (Peta-scale):** Dữ liệu khổng lồ buộc phải phân tán trên nhiều máy.
    *   Giả sử có 1000 ổ cứng, 1TB mỗi ổ.
    *   Với tỷ lệ lỗi (MTBF - Thời gian trung bình giữa các lỗi) là 1/1000, tại bất kỳ thời điểm nào cũng sẽ có ít nhất 1 ổ cứng bị chết. Do đó, **Lỗi là chuyện bình thường (failure is norm)** chứ không phải là ngoại lệ.
    *   Hệ thống tệp phải có khả năng chịu lỗi thông qua nhân bản (replication) và checksum. Băng thông truyền dữ liệu là cực kỳ quan trọng.

### 2.3. Giải pháp cốt lõi
*   Tận dụng tính chất dữ liệu **WORM (Write Once Read Many - Ghi một lần đọc nhiều lần)**: Dữ liệu này phù hợp cho việc xử lý song song, không phụ thuộc nhau (out of order processing).
*   **Chiến lược Chia để trị (Divide and Conquer):** *Đừng chuyển dữ liệu đến các máy tính, hãy mang các tiến trình tính toán đến tận nơi chứa dữ liệu! (Provision computing at data location)*.
*   Hệ thống runtime của MapReduce sẽ thêm vào các tính năng: Phân tán + Chịu lỗi + Nhân bản + Giám sát + Cân bằng tải cho ứng dụng của bạn.

### 2.4. Phép toán Map và Reduce
*   **MAP:** Dữ liệu đầu vào -> cặp `<key, value>`. (Ví dụ cắt từng từ và gán giá trị 1).
*   **REDUCE:** cặp `<key, value>` -> `<kết quả>`. (Nhóm các cặp có chung key lại để tính tổng).
*   **Lưu ý kỹ thuật:** Reducer xử lý các key theo thứ tự ĐÃ ĐƯỢC SẮP XẾP (sorted order).

### 2.5. Mô hình Lập trình MapReduce (Các bước thực hiện)
1. Xác định xem bài toán có thể song song hóa và giải bằng MapReduce không (Dữ liệu WORM? Lớn?).
2. Thiết kế và triển khai giải pháp thành các lớp Mapper và lớp Reducer.
3. Biên dịch (Compile) mã nguồn với lõi Hadoop.
4. Đóng gói code thành file thực thi `jar`.
5. Cấu hình ứng dụng (job): Số lượng mapper, reducer, luồng dữ liệu vào/ra.
6. Tải dữ liệu lên (hoặc dùng dữ liệu đã có trên hệ thống).
7. Khởi chạy job và giám sát.
8. Nghiên cứu kết quả.

---

## 3. Thực thi & Tối ưu hóa MapReduce (Execution & Optimization)

Mục tiêu tối ưu hóa gồm: Chọn đúng số lượng Mappers/Reducers, Dùng hàm Combiner, và Xử lý lệch phân phối dữ liệu (Data Skew).

### 3.1. Quá trình chia nhỏ dữ liệu
*   Hệ thống chia dữ liệu đầu vào thành các phần có kích thước cố định gọi là **input splits** (hay splits).
*   Tạo một **Map task cho mỗi split**.
*   Kích thước split tốt nhất thường bằng với kích thước block của HDFS (mặc định là **128 MB**).
*   **Tối ưu hóa Data Locality (Tính cục bộ dữ liệu):** Luôn cố gắng chạy map task trên node mà dữ liệu đang nằm trên đó trong HDFS.

### 3.2. Cấu hình số lượng (How Many?)
*   **Bao nhiêu Map?**
    *   Thường được quyết định bởi tổng dung lượng file đầu vào (tổng số blocks).
    *   Mức độ song song lý tưởng là khoảng **10-100 maps mỗi node**. (Setup task mất thời gian, nên mỗi map nên chạy ít nhất 1 phút).
    *   *Ví dụ:* 10TB dữ liệu, block size 128MB => Bạn sẽ có **82.000 maps**. (Trừ khi bạn ghi đè cấu hình bằng `MRJobConfig.NUM_MAPS` như một gợi ý cho hệ thống).
*   **Bao nhiêu Reduce?**
    *   Công thức: **0.95 hoặc 1.75 * (<số nodes> * <số containers tối đa trên mỗi node>)**.
    *   Với hệ số `0.95`: Tất cả reduces có thể khởi chạy ngay lập tức khi map vừa xong.
    *   Với hệ số `1.75`: Các node nhanh sẽ xong đợt 1 và tiếp tục chạy đợt 2, giúp **cân bằng tải tốt hơn rất nhiều**.
    *   Hệ số không dùng số nguyên tròn trĩnh là để dự trữ một vài slot cho các task đầu cơ (speculative-tasks) hoặc task bị lỗi.

### 3.3. Đặc điểm và Phạm vi của MapReduce
*   **Đặc điểm:** Dữ liệu siêu lớn (Peta, Exa bytes); WORM; Code đơn giản; Cần hoàn tất tất cả quá trình Map trước khi Reduce bắt đầu; Cấu hình linh hoạt phần cứng thông thường; Chạy trên HDFS. (Có các bước phụ trợ là combine và partition).
*   **Phạm vi (Scope):** Xử lý song song phân tán (Embarrassingly parallel). Kích thước dữ liệu lớn, ở cấp độ khối Mega (Mega Block level).
*   **Lớp bài toán (Classes of problems):** Thử thách Jim Gray (Ví dụ "SORT"); Google dùng cho Wordcount, Adwords, PageRank, Đánh chỉ mục dữ liệu (Indexing); Các thuật toán đơn giản (Grep, Text-indexing); Phân loại Bayesian (Data Mining); Facebook (phân tích nhân khẩu học); Phân tích tài chính; Thiên văn học (Gaussian analysis để tìm vật thể ngoài Trái đất); Đóng vai trò quan trọng trong Web3.0.

---

## 4. Giải phẫu một Công việc (Anatomy of a Job)

Khi một Job được gửi (Submit) lên hệ thống, chuyện gì xảy ra?
1. Client (driver program) tạo job, cấu hình, nộp cho **JobTracker**.
2. **Đằng sau hậu trường (Behind the scenes):**
   * Các Input splits được tính toán ở phía Client.
   * Dữ liệu của Job (jar, file XML cấu hình) được gửi tới JobTracker.
   * JobTracker đặt dữ liệu vào thư mục chia sẻ, đẩy các tác vụ vào hàng đợi (enqueues).
   * TaskTrackers liên tục ping (poll) để nhận tasks về chạy.

### Luồng Dữ liệu nội bộ (Data flow)
1. `Input File` -> Được cắt thành `InputSplit`.
2. `InputFormat` xác định cách đọc file.
3. `RecordReader` đọc dữ liệu thành cặp key/value.
4. Chạy qua **`Mapper`**.
5. Đầu ra là `Intermediates` (dữ liệu trung gian). (Có thể qua Partitioner).
6. Truyền tới **`Reducer`**.
7. Chạy qua `RecordWriter` -> Ghi ra `OutputFile` nhờ `OutputFormat`.

---

## 5. Đi sâu vào MapReduce API (Deep Dive API)

### 5.1. Các lớp (Classes) cốt lõi
*(Có 3 phiên bản API trong lịch sử Hadoop)*

*   **Lớp `Mapper<Kin, Vin, Kout, Vout>`**
    *   `void setup(Mapper.Context context)`: Gọi 1 lần khi bắt đầu task.
    *   `void map(Kin key, Vin value, Mapper.Context context)`: Gọi 1 lần cho MỖI cặp key/value trong split.
    *   `void cleanup(Mapper.Context context)`: Gọi 1 lần khi kết thúc task.
*   **Lớp `Reducer<Kin, Vin, Kout, Vout>` (Hoặc Combiner)**
    *   `setup()`: Chạy 1 lần đầu.
    *   `void reduce(Kin key, Iterable<Vin> values, Reducer.Context context)`: Gọi 1 lần cho MỖI KEY (cùng với danh sách các giá trị của nó).
    *   `cleanup()`: Chạy 1 lần cuối.
*   **Lớp `Partitioner<K, V>`**
    *   `int getPartition(K key, V value, int numPartitions)`: Trả về số hiệu của phân vùng.
*   **Lớp `Job`**
    *   Đại diện cho job đã đóng gói. Cần chỉ định: Đường dẫn in/out, Định dạng in/out, Các lớp mapper/reducer/combiner/partitioner, Các lớp key/value (trung gian và cuối cùng), **Số lượng reducers** (Lưu ý: Không chỉ định số lượng mappers ở đây vì hệ thống tự tính dựa trên split!). KHÔNG nên phụ thuộc vào cấu hình mặc định.

### 5.2. Các kiểu dữ liệu (Data Types) trong Hadoop
*   **`Writable`**: Định nghĩa giao thức tuần tự/giải tuần tự hóa (de/serialization). Mọi kiểu dữ liệu trong Hadoop đều phải là Writable.
*   **`WritableComparable`**: Định nghĩa trật tự sắp xếp (sort order). TẤT CẢ CÁC KHÓA (Keys) đều phải dùng kiểu này (nhưng Values thì không bắt buộc).
*   **Các lớp cụ thể:** `IntWritable`, `LongWritable`, `Text`, v.v... Lưu ý đây là các đối tượng "chứa" (container objects).
*   **`SequenceFile`**: Chuỗi các cặp key/value được mã hóa nhị phân.

### 5.3. Xử lý Kiểu dữ liệu Phức tạp (Complex Data Types)
*   **Cách dễ:** Mã hóa nó dưới dạng chuỗi `Text`, ví dụ: `(a, b)` thành `"a:b"`. Dùng biểu thức chính quy để phân tích. (Chạy được nhưng khá tệ - janky).
*   **Cách khó (chuẩn):** Định nghĩa một phiên bản tùy chỉnh triển khai giao diện `Writable(Comparable)`.
    *   Phải triển khai các hàm: `readFields`, `write`, `compareTo`.
    *   Hiệu quả tính toán cao, nhưng tốn thời gian lập trình ban đầu.
    *   Nên triển khai thêm hook `WritableComparator` để tối ưu hiệu suất.

### 5.4. Đưa dữ liệu phụ vào Mappers/Reducers
*   Dùng **Configuration parameters** (truyền qua object cấu hình của Job).
*   Dùng **"Side data" / DistributedCache** (Mappers/Reducers có thể đọc tệp tĩnh từ HDFS thông qua hàm `setup`).

### 5.5. Ba cạm bẫy cực lớn (Three Gotchas)
1.  **Tránh việc liên tục tạo đối tượng (Avoid object creation):** Hệ thống framework sẽ **tái sử dụng (reuses) đối tượng value** trong reducer. Nếu bạn tạo mới liên tục bằng `new Object()`, bộ nhớ sẽ bị tràn.
2.  *(Phần mở rộng ý 1 từ slide: Execution framework reuses value object in reducer).*
3.  **KHÔNG sử dụng biến Static để truyền tham số:** Truyền tham số thông qua các biến tĩnh (class statics) hoàn toàn không có tác dụng trong môi trường phân tán!

### 5.6. Chiến lược Gỡ lỗi (Debugging Strategies)
1.  **Hít một hơi thật sâu!** (First, take a deep breath).
2.  Bắt đầu từ quy mô nhỏ, chạy trên máy cục bộ (Local mode) trước. Sau đó mới sang Cụm giả lập (Pseudo-distributed) và Cụm thực tế (Fully-distributed).
3.  Xây dựng từng bước nhỏ (Build incrementally).
4.  **Hạn chế `System.out.println`**: Hãy học cách dùng Web App để xem log. Logging được ưu tiên hơn in ra màn hình. Và cẩn thận đừng log quá nhiều dữ liệu!
5.  **Fail on success (Gây lỗi có chủ đích):** Hãy chủ động ném ra các lỗi `RuntimeExceptions` để chụp lại trạng thái (state) hệ thống khi cần debug.
6.  **Hadoop chỉ là "chất keo dính" (Glue):** Hãy viết code logic chính bên ngoài các hàm map/reduce, kiểm thử độc lập chúng (Unit testing), rồi mới lắp ghép vào mapper/reducer.

---

## 6. Tổng kết (Takeaway)

*   **Ứng dụng MapReduce trong Công nghiệp:**
    *   Hệ thống Đánh chỉ mục Tìm kiếm của Google (Google Search Indexing).
    *   Đường ống Phân tích dữ liệu của Facebook (Facebook Analytics Pipeline).
    *   Xử lý Dữ liệu Khoa học Quy mô lớn (Large-Scale Scientific Data).
*   **Hạn chế của MapReduce:**
    *   Độ trễ cao, KHÔNG phù hợp cho việc xử lý thời gian thực.
    *   Chỉ là mô hình xử lý hàng loạt (Batch-Only).
    *   Độ phức tạp trong việc gỡ lỗi (Debugging Complexity).
*   **Điểm cốt lõi:**
    *   Hiểu các hệ chuẩn xử lý Big Data.
    *   Nắm rõ nguyên lý hoạt động và ưu điểm của MapReduce.
    *   Hiểu các phương pháp tối ưu hóa hiệu năng phổ biến (combiner, data locality, skew handling).

**BigData Techniques and Technologies**

**Spark: Unified engine for large-scale data analytics**

**1\. From MapReduce to Spark (Từ MapReduce đến Spark)**

**Motivation (Động lực ra đời của Spark)**

- **Hạn chế của MapReduce:** Lập trình MapReduce tuân theo một luồng dữ liệu một chiều nghiêm ngặt (Acyclic data flow): Đọc dữ liệu từ ổ cứng (HDFS) -> Map -> Ghi trung gian ra ổ đĩa cục bộ (Shuffle) -> Reduce -> Ghi kết quả ra ổ cứng (HDFS).
- **Vấn đề hiệu năng (Disk I/O):** Vì MapReduce liên tục phải đọc và ghi dữ liệu ra ổ cứng ở mỗi bước, nó trở nên cực kỳ chậm chạp và không hiệu quả đối với các ứng dụng cần tái sử dụng dữ liệu nhiều lần (như các thuật toán Machine Learning lặp đi lặp lại) hoặc các truy vấn tương tác (Interactive queries).

**Goal (Mục tiêu của Spark)**

- **In-Memory Computing (Xử lý trên bộ nhớ RAM):** Mục tiêu cốt lõi của Spark là giữ dữ liệu trên RAM (working sets) giữa các bước tính toán thay vì ghi ra đĩa. Điều này giúp tăng tốc độ xử lý lên gấp nhiều lần (có thể nhanh hơn MapReduce tới 100 lần trong bộ nhớ).
- **Kế thừa ưu điểm:** Dù thay đổi cách lưu trữ, Spark vẫn giữ lại những đặc tính ưu việt của MapReduce như: Khả năng chịu lỗi (Fault tolerance), xử lý dữ liệu cục bộ (Data locality), và khả năng mở rộng quy mô (Scalability).
- **Giải pháp - RDD:** Spark giới thiệu một khái niệm mới gọi là **Resilient Distributed Datasets (RDDs)** để giải quyết bài toán xử lý dữ liệu phân tán trên bộ nhớ một cách an toàn và hiệu quả.

**2\. Programming Model (Mô hình lập trình)**

**Resilient Distributed Datasets (RDD)**

RDD là cấu trúc dữ liệu cốt lõi của Spark. Nó mang 3 đặc tính quan trọng như chính tên gọi của nó:

- **Resilient (Chịu lỗi):** Nếu một phần dữ liệu bị mất do lỗi phần cứng (node sập), RDD có khả năng tự động khôi phục lại dữ liệu đó dựa trên lịch sử các phép toán đã tạo ra nó (Lineage).
- **Distributed (Phân tán):** Dữ liệu không nằm trên một máy mà được chia nhỏ thành các "Partitions" (phân vùng) và phân tán trên nhiều máy tính (worker nodes) trong cluster để xử lý song song.
- **Dataset (Tập dữ liệu):** Là tập hợp các object (có thể là bất kỳ kiểu dữ liệu nào trong Python, Java, Scala). RDD là **Bất biến (Immutable)** - bạn không thể thay đổi dữ liệu bên trong một RDD đã tạo ra, mà chỉ có thể tạo ra một RDD mới thông qua các phép biến đổi.

**Operations on RDDs (Các thao tác trên RDD)**

Spark chia các thao tác trên RDD thành 2 loại hoàn toàn khác biệt:

1.  **Transformations (Phép biến đổi):**
    - _Ví dụ:_ map(), filter(), flatMap(), groupByKey(), reduceByKey().
    - _Đặc điểm:_ Trả về một RDD mới từ một RDD hiện có.
    - **Lazy Evaluation (Đánh giá lười):** Đây là chìa khóa tối ưu của Spark. Khi bạn gọi một Transformation, Spark **không chạy tính toán ngay lập tức**. Nó chỉ ghi nhớ "kế hoạch" (graph) về cách dữ liệu sẽ được biến đổi.
2.  **Actions (Hành động):**
    - _Ví dụ:_ reduce(), collect(), count(), saveAsTextFile(), take().
    - _Đặc điểm:_ Trả kết quả về cho Driver program hoặc ghi dữ liệu ra bộ nhớ ngoài (HDFS, S3).
    - _Kích hoạt tính toán:_ Chỉ khi một Action được gọi, Spark mới thực sự biên dịch các kế hoạch (Transformations trước đó) và thực thi chúng trên cụm máy chủ.

**Lineage và Caching (Lịch sử dữ liệu và Lưu trữ tạm)**

- **Lineage (Gia phả/Lịch sử):** Spark ghi nhớ chuỗi các phép toán (Transformations) tạo ra một RDD. Nhờ chuỗi này, nếu dữ liệu bị mất, Spark chỉ cần tính toán lại từ RDD gốc.
- **Caching/Persistence:** Bạn có thể chủ động ra lệnh lưu một RDD vào bộ nhớ (RAM hoặc Disk) bằng lệnh .cache() để sử dụng lại ở các bước sau mà không cần phải tính toán lại từ đầu. Việc này cực kỳ hữu ích cho Machine Learning (ví dụ: công thức Logistic Regression tính toán lặp $O(n)$ nhiều lần trên cùng một tập dữ liệu như $\\frac{1}{1 + e^{-y(w \\cdot x)}}$).

**3\. Execution Model (Mô hình thực thi: DAG, Stages, Tasks)**

Mô hình thực thi là cốt lõi làm nên sức mạnh và tốc độ của Spark. Mọi thứ bắt đầu bằng **Nguyên lý Đánh giá lười (Lazy Evaluation)**. Khi bạn viết các lệnh biến đổi dữ liệu (Transformations), Spark chỉ ngồi "ghi chép" lại các bước. Chỉ khi bạn gọi một **Action**, toàn bộ quá trình mới thực sự diễn ra theo trình tự: **Code -> Job -> DAG -> Stages -> Tasks**.

**Phân rã luồng thực thi**

**1\. Job (Công việc tổng)**

- **Định nghĩa:** Mỗi khi một **Action** được gọi, Spark sẽ tạo ra một **Job**.
- Nếu trong code của bạn có 3 lệnh Action, Spark sẽ tạo ra 3 Jobs hoàn toàn tách biệt.

**2\. DAG (Đồ thị có hướng không tuần hoàn)**

Thay vì làm việc theo kiểu "tuần tự mù quáng" như MapReduce, Spark sẽ nhìn vào cuốn sổ "ghi chép" các lệnh bạn đã viết và vẽ ra một bản đồ chiến thuật gọi là **DAG (Directed Acyclic Graph)**.

- **Đồ thị (Graph):** Các điểm (node) là các tập dữ liệu RDD, các đường nối (edge) là các phép toán biến đổi dữ liệu.
- **Có hướng (Directed):** Dữ liệu chảy theo một chiều từ RDD đầu vào đến RDD kết quả, không chảy ngược.
- **Không tuần hoàn (Acyclic):** Dữ liệu đi thẳng tới đích, không bao giờ rơi vào vòng lặp vô tận.
- **Ý nghĩa:** Nhờ có DAG, Spark có thể tối ưu hóa luồng chạy trước khi thực sự đụng vào phần cứng.

**3\. Stages (Các giai đoạn)**

Spark chia bản đồ DAG đó thành nhiều mảnh nhỏ gọi là **Stages**. Nguyên tắc chia Stage là dựa vào việc dữ liệu có cần "băng qua mạng" (Shuffle) hay không.

- **Narrow Transformation (Phụ thuộc hẹp - Không xáo trộn):** Các lệnh như map(), filter(). Một máy con có thể tự xử lý dữ liệu ngay trên RAM của chính nó mà không cần hỏi xin dữ liệu từ máy khác. Spark sẽ gộp tất cả các lệnh này vào **CÙNG MỘT STAGE** (để chạy một mạch cho nhanh - Pipelining).
- **Wide Transformation (Phụ thuộc rộng - Cần xáo trộn/Shuffle):** Các lệnh như reduceByKey(), groupByKey(). Các máy con bắt buộc phải ném dữ liệu cho nhau qua lại trên mạng lưới. Mỗi khi gặp một lệnh cần Shuffle, Spark buộc phải "cắt" DAG ra và tạo thành một **STAGE MỚI**.
- _Quy luật:_ Stage trước phải chạy xong hoàn toàn (và ghi dữ liệu tạm ra đĩa cục bộ) thì Stage sau mới được phép bắt đầu.

**4\. Tasks (Tác vụ)**

Đây là đơn vị công việc nhỏ nhất được chạy trên CPU của các máy con (Executors).

- Mỗi Stage lại được băm nhỏ thành nhiều **Tasks**.
- **Công thức:** 1 Task = 1 Stage áp dụng lên 1 Partition (phân vùng dữ liệu).
- _Ví dụ:_ Nếu dữ liệu được chia thành 100 partitions, Spark sẽ sinh ra đúng 100 Tasks và gửi cho các máy con chạy song song đồng thời trong Stage đó.

**Ví dụ thực tế: Ứng dụng Đếm từ (Word Count)**

Hãy tưởng tượng bạn có 1 file văn bản lớn được chia thành **4 partitions** nằm trên 4 máy tính khác nhau.

Python

lines = sc.textFile("data.txt") # (1)

words = lines.flatMap(lambda line: line.split(" ")) # (2)

pairs = words.map(lambda w: (w, 1)) # (3)

counts = pairs.reduceByKey(lambda a, b: a + b) # (4)

counts.saveAsTextFile("output") # (5) Action!

**Quá trình thực thi diễn ra như sau:**

1.  **Job:** Lệnh (5) saveAsTextFile kích hoạt quá trình chạy. Spark lên lịch cho 1 Job.
2.  **Chia Stage:**
    - Lệnh (1), (2), (3) đều là _Narrow Transformation_, không cần các máy nói chuyện với nhau. Spark gộp chúng lại thành **Stage 1**.
    - Lệnh (4) reduceByKey là _Wide Transformation_. Các máy phải truyền dữ liệu cho nhau (Shuffle) để cộng gộp các từ giống nhau. Đây là vạch ranh giới, Spark tạo ra **Stage 2**.
3.  **Tạo và chạy Tasks:**
    - **Ở Stage 1:** Vì dữ liệu có 4 partitions, Spark ném ra **4 Tasks**. Bốn CPU sẽ cùng lúc đọc file, cắt chữ, và tạo các cặp (từ, 1).
    - **Ở Stage 2:** Giả sử RDD kết quả được cấu hình chia thành **2 partitions**. Spark ném ra **2 Tasks**. 2 CPU lúc này sẽ gom toàn bộ dữ liệu từ 4 máy ở Stage 1 qua mạng (Shuffle), tính tổng, và ghi ra đĩa.

**4\. Architecture & System Design (Kiến trúc hệ thống)**

Kiến trúc mạng của Spark theo mô hình Master-Slave (hoặc Driver-Worker).

**Spark Application Components**

1.  **Spark Driver (Trình điều khiển):**
    - Nơi chạy hàm main() của bạn.
    - Chứa **SparkContext** – cánh cổng kết nối ứng dụng với toàn bộ cluster.
    - Chịu trách nhiệm dịch code thành DAG, lập lịch các tasks và gửi chúng cho các Executors.
2.  **Cluster Manager (Trình quản lý tài nguyên):**
    - Spark không tự quản lý phần cứng mà cần hệ thống bên thứ ba cấp phát tài nguyên (CPU, RAM). Các hệ thống phổ biến là **YARN** (của Hadoop), Mesos, hoặc chế độ Standalone.
3.  **Spark Executors (Máy thực thi):**
    - Nằm trên các Worker Nodes.
    - Nhận Task từ Driver, thực thi code do người dùng viết trên các phân vùng dữ liệu (partitions).
    - Lưu trữ dữ liệu (Caching/Memory) để dùng cho các tính toán tiếp theo.

**Tương tác hệ thống (Data Distribution)**

- Code Python/Scala của bạn không chạy toàn bộ trên máy chủ gốc (Driver). Khi bạn map hoặc filter, một "bản sao" của hàm đó (function) sẽ được serialize (đóng gói) và gửi qua mạng đến từng **Executor**. Các Executor này sẽ xử lý các dòng dữ liệu (partitions) ngay tại chỗ (Data Locality) và chỉ trả kết quả cuối cùng (khi chạy action collect) về lại Driver. Việc kéo quá nhiều dữ liệu về Driver (bằng .collect()) là một sai lầm phổ biến có thể làm sập (crash) bộ nhớ của Driver.

**5\. Takeaway (Kết luận)**

- **Mô hình thống nhất (Unified Model):** Bằng cách đưa khái niệm tập dữ liệu (RDD) trở thành trung tâm, Spark cung cấp một mô hình lập trình đơn giản nhưng mạnh mẽ, hỗ trợ nhiều thư viện tích hợp như Spark SQL, Spark Streaming, MLlib (Machine Learning), và GraphX.
- **Lợi thế RDD:** Cung cấp thông tin lịch sử (Lineage) để phục hồi lỗi, khả năng tùy chỉnh bộ nhớ đệm (Caching) và khả năng xử lý song song tối ưu hóa theo vị trí dữ liệu.
- **Linh hoạt hơn MapReduce:** Rất nhiều thao tác MapReduce nặng nề đều có thể tối ưu trên Spark nhờ DAG và Lazy Evaluation, giảm thiểu triệt để việc đọc/ghi dư thừa xuống ổ cứng, biến nó thành tiêu chuẩn mới cho Xử lý dữ liệu lớn (Big Data Analytics) thời hiện đại.

# TỔNG HỢP NỘI DUNG: SPARK - PHÂN TÍCH DỮ LIỆU VỚI DATAFRAME

## PHẦN 1: CÁC MỤC TIÊU BÀI HỌC CHI TIẾT (LEARNING OUTCOMES)

Bài giảng thiết kế để người học đạt được 3 nhóm năng lực cốt lõi sau:

### 1. Hiểu API DataFrame và Lợi ích của nó (Understand the DataFrame API)
*   **Giải thích sự cải tiến so với RDD:** Nắm được cách DataFrame vượt trội hơn RDD truyền thống nhờ việc áp đặt Lược đồ dữ liệu (Schema enforcement) và cung cấp các khả năng truy vấn giống SQL.
*   **Phân biệt mô hình lưu trữ:** Hiểu rõ sự khác biệt giữa lưu trữ dữ liệu hướng hàng (Row-based storage - dùng trong RDD/hiển thị) và lưu trữ dữ liệu hướng cột (Column-based storage - dùng trong Parquet/bộ nhớ cache để tăng tốc tính toán vector).

### 2. Áp dụng Spark SQL và Biểu thức Cột (Apply Spark SQL & Column Expressions)
*   **Sử dụng biến đổi dữ liệu:** Biết cách dùng các truy vấn Spark SQL và các phép biến đổi DataFrame (như `.select()`, `.where()`, `.groupby()`) để phân tích dữ liệu có cấu trúc.
*   **Tận dụng Engine tối ưu:** Hiểu cách các truy vấn được tối ưu hóa tự động thông qua Trình tối ưu hóa Catalyst (Catalyst Optimizer) và Engine thực thi Tungsten của Spark.

### 3. Tối ưu hóa Hiệu suất (Optimize Performance)
*   **Phân tích kế hoạch thực thi:** Biết cách sử dụng lệnh `.explain()` để đọc Kế hoạch thực thi vật lý (Physical Execution Plan), từ đó tìm ra điểm nghẽn của truy vấn.
*   **Áp dụng chiến lược phân vùng & Caching:** Biết cách dùng tính năng Phân vùng (Partitioning) khi lưu file và xử lý để giảm thiểu chi phí tính toán (overhead) không cần thiết.

---

## PHẦN 2: NỘI DUNG CHI TIẾT THEO BÀI GIẢNG

### 1. Khái niệm DataFrame & Dataset (Dataframe Concept)
*   **Vấn đề của RDD:** RDD lưu trữ dữ liệu theo mô hình hướng hàng (row-oriented). Lập trình viên phải tự quản lý cấu trúc dữ liệu (bằng tuple) và các thao tác thủ công rất vất vả. Spark không biết bên trong RDD chứa gì.
*   **Giải pháp DataFrame:** Lấy cảm hứng từ Pandas, DataFrame tổ chức dữ liệu thành các cột có kiểu dữ liệu rõ ràng (Schema). Việc giữ các cột cùng nhau trong bộ nhớ giúp tận dụng tối đa bộ nhớ Cache và tập lệnh Vector (SSE, AVX) của CPU.
*   **Phân biệt DataFrame vs. Dataset:**
    *   **DataFrame:** Xác định kiểu dữ liệu lúc chạy (Dynamic typing/Runtime). Hỗ trợ Python, R, Scala, Java. API đơn giản, giống SQL.
    *   **Dataset:** Kiểm tra kiểu dữ liệu lúc biên dịch (Static typing/Compile-time). Chỉ hỗ trợ Scala và Java. An toàn hơn nhưng API phức tạp hơn.

### 2. Biểu thức Cột và Cú pháp (Column Expressions & SQL)
*   Mọi thao tác trên DataFrame đều sử dụng "Biểu thức cột". Đây KHÔNG phải là code Python thực thi ngay, mà là cách bạn "mô tả" cho Spark biết bạn muốn làm gì.
*   **Cú pháp chuẩn (Khuyên dùng):** `data['age'] < 30`. (Tránh dùng `data.age` vì dễ trùng thuộc tính hệ thống, và tuyệt đối không dùng `'age' < 30` vì Python sẽ báo lỗi `TypeError`).
*   **Hàm có sẵn:** Sử dụng thư viện `pyspark.sql.functions` (ví dụ `functions.lit('John')`) để so sánh biến linh hoạt.
*   **Spark SQL:** Nếu logic phức tạp, bạn có thể tạo bảng tạm (`data.createOrReplaceTempView('data')`) và viết câu lệnh SQL thuần túy qua hàm `spark.sql()`.

### 3. Trình Tối ưu hóa (The Optimizer)
Vì DataFrame sử dụng mô hình khai báo (bạn chỉ nói kết quả bạn muốn, không bảo Spark phải làm thế nào), Spark có không gian để tự động tối ưu hóa:
*   **Lệnh `.explain()`:** In ra Kế hoạch thực thi vật lý (Physical Plan).
*   **Khả năng của Catalyst Optimizer:** Nó tự động nhận biết để:
    *   Chỉ đọc những cột cần thiết (bỏ qua cột thừa).
    *   Đẩy bộ lọc xuống sớm (PushedFilters) để không phải load dữ liệu rác vào RAM.
    *   Tự động gom nhóm cục bộ (như một Combiner) trước khi trộn dữ liệu (Shuffle) trên toàn mạng.
    *   Lựa chọn chiến lược phân vùng lại (HashPartitioning vs RangePartitioning) sao cho `Sort` hoặc `GroupBy` chạy nhanh nhất.

### 4. Input/Output, Parquet và Phân vùng (I/O & Partitioning)
*   **Định dạng Parquet:** Là định dạng lưu trữ hướng cột (Columnar format) tiêu chuẩn của Big Data. Parquet lưu sẵn Schema, hỗ trợ nén cực tốt (bỏ qua giá trị null) và cho phép Spark chỉ đọc đúng cột cần thiết cực kỳ nhanh chóng. Quy trình chuẩn thường là: Đọc CSV/JSON -> Làm sạch -> Lưu thành Parquet -> Bắt đầu phân tích.
*   **Phân vùng dữ liệu (Partitioning):**
    *   Khi ghi dữ liệu, sử dụng `.write.partitionBy('tên_cột')`.
    *   Spark sẽ tạo ra các thư mục vật lý (ví dụ: `output/subreddit=canada/`).
    *   Lợi ích: Khi truy vấn với `.where('subreddit' == 'canada')`, Spark sẽ "bỏ qua" toàn bộ các thư mục khác, giúp tốc độ truy vấn tăng đột biến.

### 5. Hàm Tự Định Nghĩa (UDFs - User Defined Functions)
Khi các hàm có sẵn của Spark không đáp ứng được logic nghiệp vụ, ta dùng UDF. Tuy nhiên, cần hiểu rõ sự khác biệt về hiệu năng (vì lõi Spark chạy trên JVM - Java Virtual Machine, còn code của bạn viết bằng Python).
*   **Ưu tiên 1 (Nhanh nhất): Dùng các hàm có sẵn của Spark DataFrame (Native Ops).** Mất ~10s. Mọi tính toán diễn ra bên trong JVM, không cần chuyển đổi dữ liệu.
*   **Ưu tiên 2 (Khá nhanh): Pandas UDF (Vectorized UDFs).** Mất ~113s. Sử dụng công nghệ Apache Arrow, Spark truyền toàn bộ một khối dữ liệu (partition) sang Python cùng một lúc dưới dạng bảng Pandas để tính toán, thay vì truyền từng dòng.
*   **Ưu tiên 3 (Chậm nhất - Tránh dùng): Python UDF thông thường.** Mất ~437s. Spark phải tuần tự hóa từng dòng dữ liệu, gửi từ JVM sang Python, xử lý, rồi lại đổi ngược về JVM. Gây nghẽn cổ chai cực kỳ trầm trọng.

**=> Kết luận chung:** Hãy suy nghĩ việc thao tác với DataFrame như viết một câu lệnh truy vấn SQL (Khai báo) thay vì viết từng bước lập trình (Mệnh lệnh). Tận dụng tối đa Spark Functions và định dạng Parquet để hệ thống tự tối ưu cho bạn.
