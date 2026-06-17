export const bigDataLessonContentByLecId = {
  "C1-L1": {
    "lecId": "C1-L1",
    "chapterId": "C1",
    "chapterName": "Foundations of Big Data",
    "title": "Concepts: From Data to Intelligence",
    "contentPath": "Data/01_Foundations_of_Big_Data/Bai_01_Concepts_From_Data_to_Intelligence.md",
    "body": "# Bài 1. Concepts: From Data to Intelligence\r\n\r\nMột trong những mục tiêu quan trọng nhất của hệ thống Big Data là biến các luồng dữ liệu thô khổng lồ thành quyết định có giá trị. Quá trình này thường được mô tả bằng mô hình DIKW: Data - Information - Knowledge - Wisdom.\r\n\r\n## 1. Mô hình DIKW\r\n\r\n### D - Data (Dữ liệu thô)\r\n- Là các tín hiệu, sự kiện, bản ghi chưa qua xử lý.\r\n- Chưa có ngữ cảnh và chưa mang ý nghĩa tự thân.\r\n- Có thể là dữ liệu có cấu trúc, bán cấu trúc hoặc phi cấu trúc.\r\n- Ví dụ: log hệ thống, dữ liệu cảm biến, hình ảnh, văn bản.\r\n\r\n### I - Information (Thông tin)\r\n- Là dữ liệu đã được xử lý, tổng hợp và đặt vào ngữ cảnh.\r\n- Trả lời các câu hỏi như: ai, cái gì, khi nào, ở đâu.\r\n- Ví dụ: tổng hợp log thành thông tin “phát hiện tắc nghẽn giao thông tại Ngã tư A trong giờ cao điểm”.\r\n\r\n### K - Knowledge (Kiến thức)\r\n- Là thông tin được kết hợp với kinh nghiệm, mô hình thống kê hoặc học máy để tìm ra quy luật.\r\n- Trả lời câu hỏi như: vì sao, như thế nào.\r\n- Ví dụ: tắc nghẽn xảy ra lặp lại do lưu lượng xe từ trường học gần đó và nhịp đèn chưa tối ưu.\r\n\r\n### W - Wisdom (Trí tuệ)\r\n- Là kiến thức được áp dụng cùng đánh giá chiến lược và cân nhắc thực tiễn.\r\n- Trả lời câu hỏi: nên làm gì.\r\n- Ví dụ: triển khai đèn tín hiệu thích ứng động và điều chỉnh giờ học để giảm ùn tắc.\r\n\r\n## 2. Big Data là gì trong bức tranh tổng thể\r\n- Big Data không chỉ là “nhiều dữ liệu”, mà là bài toán kỹ thuật về hạ tầng, lưu trữ và khả năng mở rộng.\r\n- Data Science tập trung vào khám phá insight và mô hình hóa.\r\n- AI tập trung vào khả năng học hỏi và suy luận của máy.\r\n- Big Data là nền tảng để các hệ thống AI và phân tích hoạt động ở quy mô lớn.\r\n\r\n## 3. Vì sao phải học Big Data\r\n- Dữ liệu tăng trưởng theo ba chiều Volume, Velocity, Variety.\r\n- Hệ thống truyền thống không đủ khả năng xử lý dữ liệu khổng lồ một cách linh hoạt.\r\n- Không có hạ tầng dữ liệu tốt thì AI ở quy mô lớn cũng khó tồn tại.\r\n- Doanh nghiệp cần Big Data để chuyển từ dữ liệu sang insight và cuối cùng là hành động.\r\n\r\n## 4. Ý nghĩa thực tế\r\nMô hình DIKW giúp nhìn rõ Big Data không phải đích đến cuối cùng. Big Data chỉ có ý nghĩa khi nó tạo ra tri thức và hỗ trợ ra quyết định trong thực tế.",
    "excerpt": "# Bài 1. Concepts: From Data to Intelligence\nMột trong những mục tiêu quan trọng nhất của hệ thống Big Data là biến các luồng dữ liệu thô khổng lồ thành quyết định có giá trị. Quá trình này thường được mô tả bằng mô hình DIKW: Data - Information - Knowledge - Wisdom.\n## 1. Mô hình DIKW\n### D - Data (Dữ liệu thô)\n- Là các tín hiệu, sự kiện, bản ghi chưa qua xử lý.\n- Chưa có ngữ cảnh và chưa mang ý nghĩa tự thân."
  },
  "C1-L2": {
    "lecId": "C1-L2",
    "chapterId": "C1",
    "chapterName": "Foundations of Big Data",
    "title": "When Does Data Become Big?",
    "contentPath": "Data/01_Foundations_of_Big_Data/Bai_02_When_Does_Data_Become_Big.md",
    "body": "# Bài 2. Khi nào dữ liệu trở thành “lớn”? \r\n\r\nDữ liệu được coi là Big Data khi nó vượt quá khả năng xử lý của một máy chủ đơn lẻ. Khi đó, bài toán không còn là lưu trữ hay tính toán đơn thuần, mà là vấn đề hệ thống.\r\n\r\n## 1. Giới hạn của máy chủ đơn lẻ\r\nKhi xử lý dữ liệu khổng lồ, hệ thống thường gặp các điểm nghẽn sau:\r\n- Hết bộ nhớ RAM.\r\n- Nghẽn cổ chai truy xuất đĩa.\r\n- Quá tải CPU.\r\n- Tắc nghẽn mạng.\r\n- Rủi ro sập toàn bộ hệ thống khi một node hỏng.\r\n\r\n## 2. Hai hướng mở rộng hệ thống\r\n\r\n### Scale-Up / Vertical Scaling\r\n- Nâng cấp máy hiện tại bằng cách tăng RAM, CPU, ổ cứng.\r\n- Ưu điểm: đơn giản ở mức vận hành ban đầu.\r\n- Nhược điểm: chi phí cao, chạm trần phần cứng nhanh và vẫn có single point of failure.\r\n\r\n### Scale-Out / Horizontal Scaling\r\n- Thêm nhiều máy rẻ hơn vào một cluster để chia sẻ tải.\r\n- Ưu điểm: linh hoạt, chịu lỗi tốt, mở rộng dễ hơn.\r\n- Đây là nền tảng của Hadoop, Spark và phần lớn hệ thống Big Data hiện đại.\r\n\r\n## 3. Kết luận\r\nData trở thành “big” không chỉ vì kích thước, mà vì nó đòi hỏi cách kiến trúc khác: thay vì tăng sức mạnh một máy, ta phải phối hợp nhiều máy cùng làm việc.",
    "excerpt": "# Bài 2. Khi nào dữ liệu trở thành “lớn”?\nDữ liệu được coi là Big Data khi nó vượt quá khả năng xử lý của một máy chủ đơn lẻ. Khi đó, bài toán không còn là lưu trữ hay tính toán đơn thuần, mà là vấn đề hệ thống.\n## 1. Giới hạn của máy chủ đơn lẻ\nKhi xử lý dữ liệu khổng lồ, hệ thống thường gặp các điểm nghẽn sau:\n- Hết bộ nhớ RAM.\n- Nghẽn cổ chai truy xuất đĩa."
  },
  "C1-L3": {
    "lecId": "C1-L3",
    "chapterId": "C1",
    "chapterName": "Foundations of Big Data",
    "title": "Big Data Characteristics",
    "contentPath": "Data/01_Foundations_of_Big_Data/Bai_03_Big_Data_Characteristics.md",
    "body": "# Bài 3. Đặc trưng của Big Data\r\n\r\nBig Data không chỉ là dữ liệu lớn về kích thước, mà còn là dữ liệu phức tạp về tốc độ, nguồn gốc và hình thức biểu diễn. Đặc trưng này thường được mô tả qua “3V”.\r\n\r\n## 1. Volume - Dung lượng\r\n- Dữ liệu có quy mô cực lớn, từ petabyte đến exabyte và zettabyte.\r\n- Ví dụ: máy bay hiện đại, xe tự lái hay hệ thống IoT tạo ra lượng dữ liệu rất lớn mỗi ngày.\r\n\r\n## 2. Velocity - Tốc độ\r\n- Dữ liệu được tạo ra và cần xử lý với tốc độ cao.\r\n- Nhiều bài toán yêu cầu phản ứng gần thời gian thực như phát hiện gian lận, giám sát y tế hay khuyến mãi theo vị trí.\r\n\r\n## 3. Variety - Đa dạng\r\n- Dữ liệu có thể là bảng quan hệ, văn bản, XML, đồ thị, luồng streaming, ảnh, video.\r\n- Muốn khai thác được insight tốt, hệ thống phải xử lý được nhiều loại dữ liệu khác nhau cùng lúc.\r\n\r\n## 4. Ý nghĩa\r\nMột hệ thống chỉ thật sự “Big Data-ready” khi nó có thể xử lý đồng thời dữ liệu lớn, nhanh và đa dạng, chứ không chỉ đơn giản là chứa được nhiều file.",
    "excerpt": "# Bài 3. Đặc trưng của Big Data\nBig Data không chỉ là dữ liệu lớn về kích thước, mà còn là dữ liệu phức tạp về tốc độ, nguồn gốc và hình thức biểu diễn. Đặc trưng này thường được mô tả qua “3V”.\n## 1. Volume - Dung lượng\n- Dữ liệu có quy mô cực lớn, từ petabyte đến exabyte và zettabyte.\n- Ví dụ: máy bay hiện đại, xe tự lái hay hệ thống IoT tạo ra lượng dữ liệu rất lớn mỗi ngày.\n## 2. Velocity - Tốc độ"
  },
  "C1-L4": {
    "lecId": "C1-L4",
    "chapterId": "C1",
    "chapterName": "Foundations of Big Data",
    "title": "The Big Data System",
    "contentPath": "Data/01_Foundations_of_Big_Data/Bai_04_The_Big_Data_System.md",
    "body": "# Bài 4. Hệ thống Big Data\r\n\r\nMột hệ thống Big Data không chỉ là nơi lưu dữ liệu. Nó là một chuỗi giá trị hoàn chỉnh biến dữ liệu thành hành động có ý nghĩa cho doanh nghiệp.\r\n\r\n## 1. Chuỗi giá trị Big Data\r\nLuồng cơ bản thường đi theo dạng:\r\n- Nguồn dữ liệu.\r\n- Thu thập dữ liệu.\r\n- Lưu trữ dữ liệu.\r\n- Xử lý dữ liệu.\r\n- Phân tích dữ liệu.\r\n- Ra quyết định hoặc tự động hành động.\r\n\r\n## 2. Batch và Streaming\r\n\r\n### Batch\r\n- Xử lý khối lượng lớn dữ liệu lịch sử theo lô.\r\n- Phù hợp với phân tích ngoại tuyến, kho dữ liệu và bài toán tổng hợp lớn.\r\n\r\n### Streaming\r\n- Xử lý dữ liệu liên tục khi nó vừa xuất hiện.\r\n- Phù hợp với cảnh báo thời gian thực, giám sát và phát hiện gian lận.\r\n\r\n## 3. Lambda và Kappa\r\n\r\n### Lambda Architecture\r\n- Kết hợp batch layer và speed layer.\r\n- Ưu điểm: chính xác cao, chịu lỗi tốt.\r\n- Nhược điểm: phức tạp, phải duy trì hai đường ống xử lý.\r\n\r\n### Kappa Architecture\r\n- Chỉ dùng stream processing.\r\n- Dữ liệu lịch sử được xử lý bằng cách replay luồng.\r\n- Ưu điểm: đơn giản hơn, chỉ cần một codebase.\r\n\r\n## 4. Những thách thức kỹ thuật\r\n- Khả năng mở rộng ngang.\r\n- Tính chịu lỗi.\r\n- Độ trễ.\r\n- Chất lượng dữ liệu.\r\n- Quản trị và bảo mật.\r\n\r\n## 5. Kết luận\r\nGiá trị của Big Data nằm ở toàn bộ pipeline. Nếu chỉ có lưu trữ mà không có xử lý và phân tích phù hợp thì dữ liệu vẫn chỉ là dữ liệu.",
    "excerpt": "# Bài 4. Hệ thống Big Data\nMột hệ thống Big Data không chỉ là nơi lưu dữ liệu. Nó là một chuỗi giá trị hoàn chỉnh biến dữ liệu thành hành động có ý nghĩa cho doanh nghiệp.\n## 1. Chuỗi giá trị Big Data\nLuồng cơ bản thường đi theo dạng:\n- Nguồn dữ liệu.\n- Thu thập dữ liệu."
  },
  "C1-L5": {
    "lecId": "C1-L5",
    "chapterId": "C1",
    "chapterName": "Foundations of Big Data",
    "title": "Big Data Jobs",
    "contentPath": "Data/01_Foundations_of_Big_Data/Bai_05_Big_Data_Jobs.md",
    "body": "# Bài 5. Nghề nghiệp trong Big Data\r\n\r\nNgành Big Data đòi hỏi nhiều vai trò chuyên biệt phối hợp với nhau. Mỗi vai trò tập trung vào một phần khác nhau của vòng đời dữ liệu.\r\n\r\n## 1. Các vai trò chính\r\n\r\n### Data Scientist\r\n- Thu thập, phân tích và diễn giải dữ liệu lớn.\r\n- Tìm mô hình, xu hướng và mối quan hệ ẩn trong dữ liệu.\r\n\r\n### Big Data Engineer / Architect\r\n- Thiết kế và xây dựng hạ tầng, pipeline và kiến trúc dữ liệu.\r\n- Đảm bảo hệ thống đủ khả năng mở rộng và vận hành ổn định.\r\n\r\n### Big Data Developer\r\n- Phát triển ứng dụng xử lý dữ liệu bằng Hadoop, Spark, Python, Scala hoặc Java.\r\n\r\n### Big Data Analyst / Specialist\r\n- Khai thác dữ liệu thực tế để hỗ trợ quyết định kinh doanh.\r\n\r\n## 2. Các nhóm kỹ năng cốt lõi\r\n- Store & Process: lưu trữ dữ liệu lớn, hệ phân tán, kỹ nghệ phần mềm, hệ thống và mạng.\r\n- Analyse & Model: machine learning, information retrieval, suy luận và biểu diễn tri thức.\r\n- Understand & Design: lý thuyết ra quyết định, visual analytics, tư duy thiết kế hệ thống.\r\n\r\n## 3. Kết luận\r\nBig Data là một lĩnh vực liên ngành. Người làm trong mảng này không chỉ cần biết công nghệ mà còn phải hiểu bài toán dữ liệu, mục tiêu kinh doanh và cách hệ thống được vận hành ở quy mô lớn.",
    "excerpt": "# Bài 5. Nghề nghiệp trong Big Data\nNgành Big Data đòi hỏi nhiều vai trò chuyên biệt phối hợp với nhau. Mỗi vai trò tập trung vào một phần khác nhau của vòng đời dữ liệu.\n## 1. Các vai trò chính\n### Data Scientist\n- Thu thập, phân tích và diễn giải dữ liệu lớn.\n- Tìm mô hình, xu hướng và mối quan hệ ẩn trong dữ liệu."
  },
  "C2-L1": {
    "lecId": "C2-L1",
    "chapterId": "C2",
    "chapterName": "Big Data Ecosystems",
    "title": "Data Modeling in Big Data Systems",
    "contentPath": "Data/02_Big_Data_Ecosystems/Bai_01_Data_Modeling_in_Big_Data_Systems.md",
    "body": "# Bài 1. Mô hình hóa dữ liệu trong hệ thống Big Data\r\n\r\nTrong Big Data, dữ liệu thô hiếm khi sẵn sàng để phân tích ngay. Muốn khai thác giá trị, dữ liệu phải được mô hình hóa, làm sạch và liên kết.\r\n\r\n## 1. Tại sao cần mô hình hóa dữ liệu\r\n- Dữ liệu thường phân tán ở nhiều hệ thống khác nhau.\r\n- Dữ liệu có thể kém chất lượng, thiếu giá trị hoặc có giá trị sai lệch.\r\n- Nhiều mô hình học máy cần đặc trưng mà dữ liệu gốc chưa có sẵn.\r\n\r\n## 2. Quá trình chuyển đổi dữ liệu\r\n- Raw data như hình ảnh, gen, văn bản.\r\n- Trích xuất đặc trưng và làm sạch dữ liệu.\r\n- Biến dữ liệu thành structured data có thể dùng cho phân tích và học máy.\r\n- Các quan hệ cấu trúc đôi khi chính là đặc trưng quan trọng nhất.\r\n\r\n## 3. Một số hướng mô hình hóa phổ biến\r\n- Linked Data: tìm mẫu thông qua các kết nối, cụm và đường đi.\r\n- Knowledge Graphs: biểu diễn lớp, lớp con, thực thể và thuộc tính.\r\n- Dynamic Data: theo dõi sự thay đổi theo thời gian để dự báo.\r\n- Tabular Data: dữ liệu bảng kết hợp với lookup hoặc join từ hệ thống ngoài.\r\n\r\n## 4. Kết luận\r\nMô hình hóa dữ liệu là bước nền tảng để biến dữ liệu rời rạc thành dữ liệu có thể phân tích, truy vấn và học máy.",
    "excerpt": "# Bài 1. Mô hình hóa dữ liệu trong hệ thống Big Data\nTrong Big Data, dữ liệu thô hiếm khi sẵn sàng để phân tích ngay. Muốn khai thác giá trị, dữ liệu phải được mô hình hóa, làm sạch và liên kết.\n## 1. Tại sao cần mô hình hóa dữ liệu\n- Dữ liệu thường phân tán ở nhiều hệ thống khác nhau.\n- Dữ liệu có thể kém chất lượng, thiếu giá trị hoặc có giá trị sai lệch.\n- Nhiều mô hình học máy cần đặc trưng mà dữ liệu gốc chưa có sẵn."
  },
  "C2-L2": {
    "lecId": "C2-L2",
    "chapterId": "C2",
    "chapterName": "Big Data Ecosystems",
    "title": "Modern Big Data Stack",
    "contentPath": "Data/02_Big_Data_Ecosystems/Bai_02_Modern_Big_Data_Stack.md",
    "body": "# Bài 2. Modern Big Data Stack\r\n\r\nNgăn xếp Big Data hiện đại là tập hợp các lớp công nghệ giúp dữ liệu đi từ nguồn vào đến giá trị đầu ra một cách trơn tru.\r\n\r\n## 1. Các lớp chính\r\n- Nguồn dữ liệu.\r\n- Thu thập dữ liệu.\r\n- Lưu trữ dữ liệu.\r\n- Xử lý dữ liệu.\r\n- Phân tích dữ liệu.\r\n- Ra quyết định và hành động.\r\n\r\n## 2. Sáu khả năng cốt lõi của stack hiện đại\r\n1. Khám phá và điều hướng dữ liệu đa nguồn.\r\n2. Hiệu suất cực cao, đưa phân tích đến gần dữ liệu.\r\n3. Xử lý dữ liệu phi cấu trúc như ảnh, video, text.\r\n4. Xử lý dữ liệu đang chuyển động, đặc biệt là streaming.\r\n5. Thư viện phân tích và machine learning phong phú.\r\n6. Tích hợp, quản trị, chất lượng và bảo mật.\r\n\r\n## 3. Các thành phần điển hình\r\n- Data sources: RDBMS, JSON, logs, text, images.\r\n- Data ingestion: batch hoặc stream, ví dụ Kafka, NiFi, Sqoop, Flume.\r\n- Data storage: HDFS, object storage, data lakes.\r\n- Data processing: Spark, MapReduce, Flink, Storm.\r\n- Data analytics: mô tả, chẩn đoán, dự đoán, đề xuất.\r\n- Decision/action: dashboard, automation, báo cáo.\r\n\r\n## 4. Kết luận\r\nStack hiện đại giúp doanh nghiệp không chỉ lưu dữ liệu, mà còn tổ chức luồng dữ liệu thành một hệ sinh thái phục vụ phân tích và hành động.",
    "excerpt": "# Bài 2. Modern Big Data Stack\nNgăn xếp Big Data hiện đại là tập hợp các lớp công nghệ giúp dữ liệu đi từ nguồn vào đến giá trị đầu ra một cách trơn tru.\n## 1. Các lớp chính\n- Nguồn dữ liệu.\n- Thu thập dữ liệu.\n- Lưu trữ dữ liệu."
  },
  "C2-L3": {
    "lecId": "C2-L3",
    "chapterId": "C2",
    "chapterName": "Big Data Ecosystems",
    "title": "Modern Data Platform",
    "contentPath": "Data/02_Big_Data_Ecosystems/Bai_03_Modern_Data_Platform.md",
    "body": "# Bài 3. Nền tảng dữ liệu hiện đại\r\n\r\nCác nền tảng dữ liệu hiện đại hướng tới mô hình Lakehouse và tích hợp sâu với công cụ AI/ML để phục vụ cả phân tích lẫn vận hành.\r\n\r\n## 1. Hướng phát triển chính\r\n- Kết hợp tính linh hoạt của data lake với độ tin cậy kiểu warehouse.\r\n- Hỗ trợ cả BI và machine learning trên cùng một nền tảng.\r\n- Tập trung vào quản trị dữ liệu, lineage và kiểm soát truy cập.\r\n- Làm cho quy trình dữ liệu và AI dễ vận hành hơn ở quy mô lớn.\r\n\r\n## 2. Ví dụ nền tảng\r\n- Cloudera Data Platform.\r\n- Databricks Intelligent Platform.\r\n- IBM Cloud Pak for Data.\r\n- Microsoft Fabric.\r\n\r\n## 3. Kết luận\r\nNền tảng dữ liệu hiện đại không chỉ là công cụ lưu trữ hay tính toán, mà là sản phẩm hạ tầng giúp đội ngũ phân tích, kỹ sư và AI làm việc trên cùng một hệ dữ liệu thống nhất.",
    "excerpt": "# Bài 3. Nền tảng dữ liệu hiện đại\nCác nền tảng dữ liệu hiện đại hướng tới mô hình Lakehouse và tích hợp sâu với công cụ AI/ML để phục vụ cả phân tích lẫn vận hành.\n## 1. Hướng phát triển chính\n- Kết hợp tính linh hoạt của data lake với độ tin cậy kiểu warehouse.\n- Hỗ trợ cả BI và machine learning trên cùng một nền tảng.\n- Tập trung vào quản trị dữ liệu, lineage và kiểm soát truy cập."
  },
  "C2-L4": {
    "lecId": "C2-L4",
    "chapterId": "C2",
    "chapterName": "Big Data Ecosystems",
    "title": "Big Data Analysis",
    "contentPath": "Data/02_Big_Data_Ecosystems/Bai_04_Big_Data_Analysis.md",
    "body": "# Bài 4. Phân tích Big Data\r\n\r\nPhân tích Big Data là quá trình kiểm tra các tập dữ liệu lớn và đa dạng để tìm mẫu ẩn, mối tương quan, xu hướng thị trường và sở thích của khách hàng.\r\n\r\n## 1. Hiểu đúng về phân tích dữ liệu lớn\r\n- Không phải cứ nhiều dữ liệu là sẽ có nhiều trí tuệ.\r\n- Nếu thiếu kiến trúc hệ thống, mô hình phân tích và hiểu biết miền ứng dụng, dữ liệu lớn chỉ trở thành tiếng ồn và chi phí.\r\n\r\n## 2. Mục tiêu của phân tích\r\n- Phát hiện quy luật từ dữ liệu thô.\r\n- Kiểm định giả thuyết bằng quan sát và thử nghiệm.\r\n- Chuyển dữ liệu thành thông tin, rồi thành tri thức và hành động.\r\n\r\n## 3. Quy trình phân tích\r\n1. Thu thập và truy cập dữ liệu.\r\n2. Nhào nặn dữ liệu.\r\n3. Tích hợp và biểu diễn quan hệ.\r\n4. Làm sạch và lọc.\r\n5. Giả thuyết, truy vấn, phân tích và mô hình hóa.\r\n6. Thấu hiểu, lặp lại và khám phá.\r\n\r\n## 4. Lưu ý về đạo đức\r\n- Bảo vệ dữ liệu.\r\n- Tuân thủ nguyên tắc thống kê.\r\n- Không trình bày kết quả gây hiểu lầm.\r\n\r\n## 5. Kết luận\r\nPhân tích là cầu nối giữa hạ tầng dữ liệu và quyết định. Dữ liệu chỉ tạo giá trị khi được làm sạch, mô hình hóa và diễn giải đúng cách.",
    "excerpt": "# Bài 4. Phân tích Big Data\nPhân tích Big Data là quá trình kiểm tra các tập dữ liệu lớn và đa dạng để tìm mẫu ẩn, mối tương quan, xu hướng thị trường và sở thích của khách hàng.\n## 1. Hiểu đúng về phân tích dữ liệu lớn\n- Không phải cứ nhiều dữ liệu là sẽ có nhiều trí tuệ.\n- Nếu thiếu kiến trúc hệ thống, mô hình phân tích và hiểu biết miền ứng dụng, dữ liệu lớn chỉ trở thành tiếng ồn và chi phí.\n## 2. Mục tiêu của phân tích"
  },
  "C2-L5": {
    "lecId": "C2-L5",
    "chapterId": "C2",
    "chapterName": "Big Data Ecosystems",
    "title": "Big Data Applications & Landscape",
    "contentPath": "Data/02_Big_Data_Ecosystems/Bai_05_Big_Data_Applications_and_Landscape.md",
    "body": "# Bài 5. Ứng dụng và bức tranh toàn cảnh của Big Data\r\n\r\nBig Data xuất hiện trong hầu hết các ngành vì các mẫu dữ liệu lớn thường lặp lại ở nhiều miền ứng dụng khác nhau.\r\n\r\n## 1. Các lĩnh vực ứng dụng tiêu biểu\r\n- Y tế và chăm sóc sức khỏe.\r\n- Giáo dục và nghiên cứu.\r\n- Kinh tế và kinh doanh.\r\n- Xã hội và dịch vụ công.\r\n- An ninh quốc gia và quốc phòng.\r\n- Môi trường và tính bền vững.\r\n\r\n## 2. Khi nào doanh nghiệp cần Big Data\r\n- Dữ liệu tăng nhanh, hệ thống hiện tại không còn đáp ứng.\r\n- Cần xử lý thời gian thực.\r\n- Dữ liệu phi cấu trúc hoặc đa định dạng.\r\n- CSDL truyền thống phản hồi quá chậm.\r\n- Cần tích hợp phân tích và AI nâng cao.\r\n- Cần mở rộng linh hoạt theo nhu cầu.\r\n- Muốn ra quyết định dựa trên dữ liệu.\r\n\r\n## 3. Thách thức và xu hướng\r\n- Chất lượng dữ liệu và làm sạch.\r\n- Chi phí lưu trữ và tính toán.\r\n- Bảo mật và quyền riêng tư.\r\n- Thiếu nhân lực dữ liệu.\r\n- Phá vỡ các silo dữ liệu.\r\n- Xu hướng tương lai: autonomous analytics, edge computing, IoT, realtime decision-making và data governance.\r\n\r\n## 4. Kết luận\r\nBức tranh Big Data rất rộng, nhưng mục tiêu cuối cùng luôn là biến dữ liệu quy mô lớn thành giá trị thực cho tổ chức và xã hội.",
    "excerpt": "# Bài 5. Ứng dụng và bức tranh toàn cảnh của Big Data\nBig Data xuất hiện trong hầu hết các ngành vì các mẫu dữ liệu lớn thường lặp lại ở nhiều miền ứng dụng khác nhau.\n## 1. Các lĩnh vực ứng dụng tiêu biểu\n- Y tế và chăm sóc sức khỏe.\n- Giáo dục và nghiên cứu.\n- Kinh tế và kinh doanh."
  },
  "C3-L1": {
    "lecId": "C3-L1",
    "chapterId": "C3",
    "chapterName": "Big Data Storage",
    "title": "Introduction Big Data Storage",
    "contentPath": "Data/03_Big_Data_Storage/Bai_01_Introduction_Big_Data_Storage.md",
    "body": "# Bài 1. Giới thiệu về lưu trữ Big Data\r\n\r\nLưu trữ Big Data là cơ sở hạ tầng được thiết kế để quản lý hiệu quả khối lượng lớn dữ liệu có cấu trúc, bán cấu trúc và phi cấu trúc.\r\n\r\n## 1. Tại sao lưu trữ là nền tảng\r\n- Lưu trữ là nơi giữ dữ liệu bền bỉ để phục vụ xử lý và phân tích về sau.\r\n- Đây là nền tảng cho IoT, AI, phân tích kinh doanh và điện toán đám mây.\r\n\r\n## 2. Đặc điểm chính\r\n- Khả năng mở rộng.\r\n- Tính sẵn sàng cao và bền bỉ.\r\n- Kiến trúc phân tán.\r\n- Hiệu quả chi phí.\r\n\r\n## 3. Điểm khác biệt quan trọng\r\n- Dữ liệu là thứ bền bỉ và đắt đỏ.\r\n- Tính toán là thứ co giãn.\r\n- Vì vậy, cách lưu trữ ảnh hưởng trực tiếp đến hiệu suất và chi phí toàn bộ hệ thống.\r\n\r\n## 4. Kết luận\r\nLưu trữ không chỉ là “chỗ để file”, mà là thành phần định hình khả năng mở rộng và hiệu năng của Big Data system.",
    "excerpt": "# Bài 1. Giới thiệu về lưu trữ Big Data\nLưu trữ Big Data là cơ sở hạ tầng được thiết kế để quản lý hiệu quả khối lượng lớn dữ liệu có cấu trúc, bán cấu trúc và phi cấu trúc.\n## 1. Tại sao lưu trữ là nền tảng\n- Lưu trữ là nơi giữ dữ liệu bền bỉ để phục vụ xử lý và phân tích về sau.\n- Đây là nền tảng cho IoT, AI, phân tích kinh doanh và điện toán đám mây.\n## 2. Đặc điểm chính"
  },
  "C3-L2": {
    "lecId": "C3-L2",
    "chapterId": "C3",
    "chapterName": "Big Data Storage",
    "title": "Decisive Principles",
    "contentPath": "Data/03_Big_Data_Storage/Bai_02_Decisive_Principles.md",
    "body": "# Bài 2. Các nguyên tắc quyết định\r\n\r\nThiết kế lưu trữ Big Data không bắt đầu từ công cụ, mà bắt đầu từ khối lượng công việc, cách truy cập dữ liệu và yêu cầu chịu lỗi.\r\n\r\n## 1. Nguyên tắc cốt lõi\r\n- Ưu tiên scale-out thay vì cố nâng cấp mãi một máy.\r\n- Đưa tính toán đến gần nơi dữ liệu nằm.\r\n- Dùng partitioning và replication để cân bằng tốc độ và độ tin cậy.\r\n- Thiết kế với giả định rằng lỗi là bình thường.\r\n\r\n## 2. Partitioning và Sharding\r\n- Partitioning chia dữ liệu về mặt logic.\r\n- Sharding là partitioning phân tán trên nhiều máy vật lý.\r\n\r\n## 3. Replication\r\n- Tạo nhiều bản sao trên các node khác nhau.\r\n- Mục đích là tăng chịu lỗi, tăng sẵn sàng và giảm bottleneck.\r\n\r\n## 4. CAP, BASE và PACELC\r\n- CAP cho thấy hệ phân tán phải đánh đổi giữa consistency, availability và partition tolerance.\r\n- BASE nới lỏng ACID để đạt mở rộng ngang tốt hơn.\r\n- PACELC mở rộng câu hỏi: khi không có phân vùng, hệ thống ưu tiên latency hay consistency.\r\n\r\n## 5. Kết luận\r\nMột hệ thống lưu trữ tốt phải tồn tại được khi node, disk hoặc network gặp lỗi.",
    "excerpt": "# Bài 2. Các nguyên tắc quyết định\nThiết kế lưu trữ Big Data không bắt đầu từ công cụ, mà bắt đầu từ khối lượng công việc, cách truy cập dữ liệu và yêu cầu chịu lỗi.\n## 1. Nguyên tắc cốt lõi\n- Ưu tiên scale-out thay vì cố nâng cấp mãi một máy.\n- Đưa tính toán đến gần nơi dữ liệu nằm.\n- Dùng partitioning và replication để cân bằng tốc độ và độ tin cậy."
  },
  "C3-L3": {
    "lecId": "C3-L3",
    "chapterId": "C3",
    "chapterName": "Big Data Storage",
    "title": "Big Data Storage Solutions",
    "contentPath": "Data/03_Big_Data_Storage/Bai_03_Big_Data_Storage_Solutions.md",
    "body": "# Bài 3. Các giải pháp lưu trữ Big Data\r\n\r\nHệ sinh thái lưu trữ Big Data đã tiến hóa từ RDBMS truyền thống sang hệ thống tệp phân tán, cloud object storage, data lake, lakehouse và cả lưu trữ gốc AI.\r\n\r\n## 1. Sự tiến hóa của giải pháp lưu trữ\r\n1. RDBMS: tốt cho dữ liệu có cấu trúc nhưng khó mở rộng lớn.\r\n2. Distributed File Systems như GFS, HDFS: chia file thành block và sao chép dự phòng.\r\n3. Cloud Object Storage: mở rộng mạnh, bền bỉ, truy cập qua API.\r\n4. Data Lake: lưu dữ liệu thô với schema-on-read.\r\n5. Lakehouse: kết hợp ưu điểm của lake và warehouse, có ACID và time travel.\r\n6. AI-native storage: phục vụ vector search và dữ liệu nhiều chiều.\r\n\r\n## 2. Một số lựa chọn phổ biến\r\n- HDFS.\r\n- Amazon S3 hoặc các object storage tương tự.\r\n- Cassandra, HBase, MongoDB và các hệ NoSQL khác.\r\n- Các định dạng cột như Parquet cho workload phân tích.\r\n\r\n## 3. Kết luận\r\nKhông có một giải pháp lưu trữ nào là tốt nhất cho mọi bài toán. Lựa chọn đúng phụ thuộc vào truy cập dữ liệu, độ trễ, quy mô và kiểu workload.",
    "excerpt": "# Bài 3. Các giải pháp lưu trữ Big Data\nHệ sinh thái lưu trữ Big Data đã tiến hóa từ RDBMS truyền thống sang hệ thống tệp phân tán, cloud object storage, data lake, lakehouse và cả lưu trữ gốc AI.\n## 1. Sự tiến hóa của giải pháp lưu trữ\n1. RDBMS: tốt cho dữ liệu có cấu trúc nhưng khó mở rộng lớn.\n2. Distributed File Systems như GFS, HDFS: chia file thành block và sao chép dự phòng.\n3. Cloud Object Storage: mở rộng mạnh, bền bỉ, truy cập qua API."
  },
  "C4-L1": {
    "lecId": "C4-L1",
    "chapterId": "C4",
    "chapterName": "Big Data Paradigms",
    "title": "Big Data Processing Paradigms",
    "contentPath": "Data/04_Big_Data_Paradigms/Bai_01_Big_Data_Processing_Paradigms.md",
    "body": "# Bài 1. Các mô hình xử lý Big Data\r\n\r\nMô hình xử lý dữ liệu lớn là các phương pháp kiến trúc và tính toán được dùng để xử lý, lưu trữ và phân tích dữ liệu quy mô lớn một cách hiệu quả.\r\n\r\n## 1. Batch Processing\r\n- Xử lý khối lượng lớn dữ liệu tĩnh trong các công việc được lên lịch sẵn.\r\n- Ưu điểm: thông lượng cao, mở rộng tốt, hệ sinh thái trưởng thành.\r\n- Ví dụ: data warehousing, data mining, phân tích dự đoán.\r\n- Framework tiêu biểu: Hadoop MapReduce, Spark, Hive.\r\n\r\n## 2. Stream Processing\r\n- Xử lý dữ liệu theo thời gian thực hoặc gần thời gian thực.\r\n- Ưu điểm: độ trễ thấp, ra quyết định nhanh, phù hợp IoT và cảnh báo.\r\n- Framework tiêu biểu: Flink, Storm, Kafka Streams.\r\n\r\n## 3. Micro-batch Processing\r\n- Chia dữ liệu thành các lô nhỏ rất ngắn.\r\n- Cân bằng giữa độ trễ và thông lượng.\r\n- Ví dụ: Spark Structured Streaming.\r\n\r\n## 4. Lambda, Kappa và Unified Processing\r\n- Lambda kết hợp batch và stream.\r\n- Kappa chỉ dùng stream và replay dữ liệu lịch sử.\r\n- Unified processing hướng tới một hệ thống duy nhất cho cả batch lẫn stream.\r\n\r\n## 5. Cloud và Serverless\r\n- Chạy trên hạ tầng cloud-native do nhà cung cấp quản lý.\r\n- Không phải tự vận hành server.\r\n- Trả tiền theo mức sử dụng và phù hợp workload biến động.\r\n\r\n## 6. Kết luận\r\nLựa chọn mô hình xử lý phụ thuộc vào yêu cầu về độ trễ, quy mô dữ liệu, tính lặp lại và mức độ phức tạp của hệ thống.",
    "excerpt": "# Bài 1. Các mô hình xử lý Big Data\nMô hình xử lý dữ liệu lớn là các phương pháp kiến trúc và tính toán được dùng để xử lý, lưu trữ và phân tích dữ liệu quy mô lớn một cách hiệu quả.\n## 1. Batch Processing\n- Xử lý khối lượng lớn dữ liệu tĩnh trong các công việc được lên lịch sẵn.\n- Ưu điểm: thông lượng cao, mở rộng tốt, hệ sinh thái trưởng thành.\n- Ví dụ: data warehousing, data mining, phân tích dự đoán."
  },
  "C4-L2": {
    "lecId": "C4-L2",
    "chapterId": "C4",
    "chapterName": "Big Data Paradigms",
    "title": "MapReduce Fundamentals",
    "contentPath": "Data/04_Big_Data_Paradigms/Bai_02_MapReduce_Fundamentals.md",
    "body": "# Bài 2. Nền tảng MapReduce\r\n\r\nMapReduce là mô hình lập trình mà Google đã sử dụng thành công để xử lý các tập dữ liệu cực lớn.\r\n\r\n## 1. Ý tưởng cốt lõi\r\n- Người dùng chỉ cần định nghĩa hai hàm: map và reduce.\r\n- Runtime bên dưới tự động song song hóa trên nhiều máy.\r\n- Hệ thống cũng tự xử lý lỗi máy, giao tiếp mạng và cân bằng tải.\r\n\r\n## 2. Nguồn gốc của MapReduce\r\n- Tên gọi mượn từ lập trình hàm.\r\n- map xử lý từng bản ghi độc lập.\r\n- reduce nhóm và tổng hợp các giá trị có chung key.\r\n\r\n## 3. Ví dụ WordCount\r\n- Bài toán đếm tần suất từ trong bộ dữ liệu rất lớn.\r\n- Đây là ví dụ kinh điển vì mô hình hóa rõ ràng dưới dạng key-value.\r\n\r\n## 4. Giải pháp cốt lõi\r\n- Dữ liệu WORM rất phù hợp với xử lý song song.\r\n- Thay vì mang dữ liệu tới máy tính, ta mang tiến trình tính toán tới gần dữ liệu.\r\n- Hệ thống runtime bổ sung phân tán, chịu lỗi, nhân bản và giám sát.\r\n\r\n## 5. Kết luận\r\nMapReduce phù hợp cho bài toán batch lớn, đơn giản hóa cách lập trình phân tán nhưng vẫn giữ được khả năng mở rộng và chịu lỗi.",
    "excerpt": "# Bài 2. Nền tảng MapReduce\nMapReduce là mô hình lập trình mà Google đã sử dụng thành công để xử lý các tập dữ liệu cực lớn.\n## 1. Ý tưởng cốt lõi\n- Người dùng chỉ cần định nghĩa hai hàm: map và reduce.\n- Runtime bên dưới tự động song song hóa trên nhiều máy.\n- Hệ thống cũng tự xử lý lỗi máy, giao tiếp mạng và cân bằng tải."
  },
  "C4-L3": {
    "lecId": "C4-L3",
    "chapterId": "C4",
    "chapterName": "Big Data Paradigms",
    "title": "MapReduce Execution & Optimization",
    "contentPath": "Data/04_Big_Data_Paradigms/Bai_03_MapReduce_Execution_and_Optimization.md",
    "body": "# Bài 3. Thực thi và tối ưu hóa MapReduce\r\n\r\nTối ưu MapReduce tập trung vào việc chọn đúng số lượng mapper/reducer, giảm dữ liệu phải shuffle và xử lý độ lệch dữ liệu.\r\n\r\n## 1. Chia nhỏ dữ liệu\r\n- Dữ liệu đầu vào được chia thành các input split.\r\n- Mỗi split thường tương ứng với một map task.\r\n- Kích thước split tốt thường gần bằng block HDFS.\r\n- Cần ưu tiên data locality để map task chạy gần nơi dữ liệu nằm.\r\n\r\n## 2. Chọn số lượng task\r\n- Số lượng map thường phụ thuộc vào tổng số block đầu vào.\r\n- Số lượng reduce phụ thuộc vào số node, số container và mức độ cân bằng tải mong muốn.\r\n\r\n## 3. Đặc điểm của MapReduce\r\n- Phù hợp với dữ liệu siêu lớn và WORM.\r\n- Yêu cầu hoàn thành toàn bộ map trước khi reduce.\r\n- Chạy trên HDFS với các bước phụ trợ như combiner và partitioner.\r\n\r\n## 4. Phạm vi ứng dụng\r\n- Sort.\r\n- WordCount.\r\n- PageRank.\r\n- Indexing.\r\n- Các bài toán data mining và phân tích quy mô lớn.\r\n\r\n## 5. Kết luận\r\nTối ưu MapReduce chủ yếu là giảm di chuyển dữ liệu, cân bằng tải và tránh nghẽn ở các khâu shuffle, partition hoặc data skew.",
    "excerpt": "# Bài 3. Thực thi và tối ưu hóa MapReduce\nTối ưu MapReduce tập trung vào việc chọn đúng số lượng mapper/reducer, giảm dữ liệu phải shuffle và xử lý độ lệch dữ liệu.\n## 1. Chia nhỏ dữ liệu\n- Dữ liệu đầu vào được chia thành các input split.\n- Mỗi split thường tương ứng với một map task.\n- Kích thước split tốt thường gần bằng block HDFS."
  },
  "C4-L4": {
    "lecId": "C4-L4",
    "chapterId": "C4",
    "chapterName": "Big Data Paradigms",
    "title": "Anatomy of a Job",
    "contentPath": "Data/04_Big_Data_Paradigms/Bai_04_Anatomy_of_a_Job.md",
    "body": "# Bài 4. Luồng thực thi một Job MapReduce\r\n\r\nKhi một job được gửi lên hệ thống, dữ liệu và điều phối công việc sẽ đi qua nhiều bước nội bộ trước khi tạo ra kết quả cuối cùng.\r\n\r\n## 1. Luồng submit job\r\n- Client tạo job và cấu hình.\r\n- Job được gửi lên JobTracker.\r\n- Input split được tính ở phía client.\r\n- Metadata và file jar được đẩy vào hệ thống.\r\n- TaskTracker liên tục nhận task để chạy.\r\n\r\n## 2. Luồng dữ liệu nội bộ\r\n- Input file được cắt thành input split.\r\n- InputFormat quyết định cách đọc file.\r\n- RecordReader đọc thành cặp key/value.\r\n- Mapper xử lý từng bản ghi.\r\n- Dữ liệu trung gian có thể đi qua partitioner.\r\n- Reducer tổng hợp dữ liệu.\r\n- OutputFormat và RecordWriter ghi kết quả ra file.\r\n\r\n## 3. Kết luận\r\nHiểu anatomy của job giúp dễ debug lỗi và hiểu vì sao một job MapReduce có thể chậm, lệch tải hoặc phát sinh bottleneck ở từng giai đoạn khác nhau.",
    "excerpt": "# Bài 4. Luồng thực thi một Job MapReduce\nKhi một job được gửi lên hệ thống, dữ liệu và điều phối công việc sẽ đi qua nhiều bước nội bộ trước khi tạo ra kết quả cuối cùng.\n## 1. Luồng submit job\n- Client tạo job và cấu hình.\n- Job được gửi lên JobTracker.\n- Input split được tính ở phía client."
  },
  "C4-L5": {
    "lecId": "C4-L5",
    "chapterId": "C4",
    "chapterName": "Big Data Paradigms",
    "title": "Deep Dive into MapReduce API",
    "contentPath": "Data/04_Big_Data_Paradigms/Bai_05_Deep_Dive_into_MapReduce_API.md",
    "body": "# Bài 5. Đi sâu vào MapReduce API\r\n\r\nMapReduce API cung cấp các lớp và kiểu dữ liệu cần thiết để xây dựng job phân tán.\r\n\r\n## 1. Các lớp cốt lõi\r\n- Mapper<Kin, Vin, Kout, Vout>.\r\n- Reducer<Kin, Vin, Kout, Vout>.\r\n- Partitioner<K, V>.\r\n- Job để cấu hình đường dẫn, lớp xử lý và số reducer.\r\n\r\n## 2. Vòng đời method\r\n- setup chạy đầu job.\r\n- map chạy cho mỗi cặp key/value.\r\n- reduce chạy cho mỗi key cùng danh sách values.\r\n- cleanup chạy cuối job.\r\n\r\n## 3. Kiểu dữ liệu Hadoop\r\n- Writable cho tuần tự hóa và giải tuần tự hóa.\r\n- WritableComparable cho các key cần sắp xếp.\r\n- IntWritable, LongWritable, Text và các lớp tương tự.\r\n\r\n## 4. Xử lý dữ liệu phức tạp\r\n- Có thể mã hóa tạm dưới dạng chuỗi Text.\r\n- Cách chuẩn là tự định nghĩa Writable/Comparable.\r\n\r\n## 5. Những lưu ý quan trọng\r\n- Tránh tạo object liên tục trong reducer.\r\n- Không dùng static để truyền dữ liệu giữa các node.\r\n- Có thể đưa dữ liệu phụ vào job qua configuration hoặc distributed cache.\r\n\r\n## 6. Kết luận\r\nAPI của MapReduce khá thấp cấp, nhưng chính điều đó cho phép kiểm soát tốt partitioning, grouping và aggregation trong môi trường phân tán.",
    "excerpt": "# Bài 5. Đi sâu vào MapReduce API\nMapReduce API cung cấp các lớp và kiểu dữ liệu cần thiết để xây dựng job phân tán.\n## 1. Các lớp cốt lõi\n- Mapper<Kin, Vin, Kout, Vout>.\n- Reducer<Kin, Vin, Kout, Vout>.\n- Partitioner<K, V>."
  },
  "C5-L1": {
    "lecId": "C5-L1",
    "chapterId": "C5",
    "chapterName": "Spark",
    "title": "From MapReduce to Spark",
    "contentPath": "Data/05_Spark/Bai_01_From_MapReduce_to_Spark.md",
    "body": "# Bài 1. Từ MapReduce đến Spark\r\n\r\nSpark ra đời để khắc phục các hạn chế lớn nhất của MapReduce, đặc biệt là việc đọc ghi đĩa quá nhiều và xử lý lặp chậm.\r\n\r\n## 1. Hạn chế của MapReduce\r\n- Luồng dữ liệu một chiều nghiêm ngặt.\r\n- Mỗi bước tính toán thường phải ghi tạm xuống đĩa.\r\n- Không phù hợp với các bài toán lặp nhiều lần như machine learning hoặc truy vấn tương tác.\r\n\r\n## 2. Mục tiêu của Spark\r\n- Giữ dữ liệu trong bộ nhớ RAM càng lâu càng tốt.\r\n- Tăng tốc độ xử lý cho các workload lặp và interactive.\r\n- Vẫn giữ khả năng chịu lỗi, data locality và khả năng mở rộng.\r\n\r\n## 3. RDD\r\n- Spark giới thiệu Resilient Distributed Datasets để xử lý dữ liệu phân tán trên bộ nhớ an toàn và hiệu quả.\r\n\r\n## 4. Kết luận\r\nSpark là bước tiến tự nhiên khi MapReduce không còn đủ nhanh và linh hoạt cho các bài toán phân tích hiện đại.",
    "excerpt": "# Bài 1. Từ MapReduce đến Spark\nSpark ra đời để khắc phục các hạn chế lớn nhất của MapReduce, đặc biệt là việc đọc ghi đĩa quá nhiều và xử lý lặp chậm.\n## 1. Hạn chế của MapReduce\n- Luồng dữ liệu một chiều nghiêm ngặt.\n- Mỗi bước tính toán thường phải ghi tạm xuống đĩa.\n- Không phù hợp với các bài toán lặp nhiều lần như machine learning hoặc truy vấn tương tác."
  },
  "C5-L2": {
    "lecId": "C5-L2",
    "chapterId": "C5",
    "chapterName": "Spark",
    "title": "Programming Model",
    "contentPath": "Data/05_Spark/Bai_02_Programming_Model.md",
    "body": "# Bài 2. Mô hình lập trình\r\n\r\nRDD là cấu trúc dữ liệu cốt lõi của Spark. Nó thể hiện tập dữ liệu phân tán, có khả năng chịu lỗi và bất biến.\r\n\r\n## 1. Đặc tính của RDD\r\n- Resilient: có thể khôi phục dữ liệu nhờ lineage.\r\n- Distributed: dữ liệu chia thành partitions trên nhiều worker.\r\n- Dataset: là tập hợp object bất biến.\r\n\r\n## 2. Transformations và Actions\r\n- Transformations tạo RDD mới nhưng chưa chạy ngay.\r\n- Actions kích hoạt tính toán thực sự và trả kết quả về driver hoặc ghi ra ngoài.\r\n\r\n## 3. Lineage và caching\r\n- Lineage ghi lại lịch sử tạo RDD.\r\n- Caching/Persistence giúp tái sử dụng dữ liệu nhiều lần mà không tính lại từ đầu.\r\n\r\n## 4. Kết luận\r\nMô hình lập trình của Spark rất mạnh vì kết hợp được tính khai báo, khả năng chịu lỗi và hiệu năng cao trên dữ liệu phân tán.",
    "excerpt": "# Bài 2. Mô hình lập trình\nRDD là cấu trúc dữ liệu cốt lõi của Spark. Nó thể hiện tập dữ liệu phân tán, có khả năng chịu lỗi và bất biến.\n## 1. Đặc tính của RDD\n- Resilient: có thể khôi phục dữ liệu nhờ lineage.\n- Distributed: dữ liệu chia thành partitions trên nhiều worker.\n- Dataset: là tập hợp object bất biến."
  },
  "C5-L3": {
    "lecId": "C5-L3",
    "chapterId": "C5",
    "chapterName": "Spark",
    "title": "Execution Model",
    "contentPath": "Data/05_Spark/Bai_03_Execution_Model.md",
    "body": "# Bài 3. Mô hình thực thi\r\n\r\nSức mạnh của Spark đến từ cách nó chuyển code thành DAG, chia thành stages và phân phối thành tasks trên cluster.\r\n\r\n## 1. Job, DAG, Stage, Task\r\n- Action tạo ra Job.\r\n- Spark xây dựng DAG từ các transformations.\r\n- DAG được chia thành các stages.\r\n- Mỗi stage được chia thành nhiều tasks.\r\n\r\n## 2. Lazy evaluation\r\n- Transformations chỉ được ghi nhận chứ chưa thực thi ngay.\r\n- Spark tối ưu trước khi chạy thật sự.\r\n\r\n## 3. Narrow và wide transformation\r\n- Narrow transformation có thể được pipelining trong cùng một stage.\r\n- Wide transformation cần shuffle và thường tạo stage mới.\r\n\r\n## 4. Ví dụ Word Count\r\n- Đọc file thành partitions.\r\n- Cắt từ và tạo cặp (word, 1).\r\n- ReduceByKey gom và cộng số lần xuất hiện.\r\n\r\n## 5. Kết luận\r\nMô hình thực thi của Spark giúp xử lý các bài toán lặp và tương tác nhanh hơn rất nhiều so với mô hình batch cứng nhắc kiểu MapReduce.",
    "excerpt": "# Bài 3. Mô hình thực thi\nSức mạnh của Spark đến từ cách nó chuyển code thành DAG, chia thành stages và phân phối thành tasks trên cluster.\n## 1. Job, DAG, Stage, Task\n- Action tạo ra Job.\n- Spark xây dựng DAG từ các transformations.\n- DAG được chia thành các stages."
  },
  "C5-L4": {
    "lecId": "C5-L4",
    "chapterId": "C5",
    "chapterName": "Spark",
    "title": "Architecture & System Design",
    "contentPath": "Data/05_Spark/Bai_04_Architecture_and_System_Design.md",
    "body": "# Bài 4. Kiến trúc và thiết kế hệ thống\r\n\r\nKiến trúc Spark theo mô hình Driver - Worker, trong đó driver điều phối còn executors thực thi tính toán phân tán.\r\n\r\n## 1. Các thành phần chính\r\n- Spark Driver: chạy hàm main và tạo SparkContext.\r\n- Cluster Manager: cấp phát tài nguyên như YARN, Mesos hoặc Standalone.\r\n- Executors: chạy task trên worker nodes.\r\n\r\n## 2. Cách dữ liệu được xử lý\r\n- Code người dùng được serialize và gửi tới executors.\r\n- Executors xử lý partitions tại chỗ để tận dụng data locality.\r\n- Kết quả cuối cùng chỉ được trả về driver khi cần.\r\n\r\n## 3. Kết luận\r\nThiết kế hệ thống Spark tốt là cân bằng giữa song song hóa, bộ nhớ, tài nguyên cluster và cách di chuyển dữ liệu.",
    "excerpt": "# Bài 4. Kiến trúc và thiết kế hệ thống\nKiến trúc Spark theo mô hình Driver - Worker, trong đó driver điều phối còn executors thực thi tính toán phân tán.\n## 1. Các thành phần chính\n- Spark Driver: chạy hàm main và tạo SparkContext.\n- Cluster Manager: cấp phát tài nguyên như YARN, Mesos hoặc Standalone.\n- Executors: chạy task trên worker nodes."
  },
  "C6-L1": {
    "lecId": "C6-L1",
    "chapterId": "C6",
    "chapterName": "Spark Dataframe",
    "title": "Dataframe Concept",
    "contentPath": "Data/06_Spark_Dataframe/Bai_01_Dataframe_Concept.md",
    "body": "# Bài 1. Khái niệm DataFrame\r\n\r\nDataFrame trong Spark là một bảng phân tán có schema và tên cột rõ ràng.\r\n\r\n## 1. DataFrame là gì\r\n- Là cách nhìn dạng bảng trên dữ liệu phân tán.\r\n- Dữ liệu được tổ chức theo cột có kiểu rõ ràng.\r\n- Gần với cách suy nghĩ của SQL và các hệ dữ liệu quan hệ.\r\n\r\n## 2. So sánh với RDD\r\n- RDD thiên về hàng và mức thấp hơn.\r\n- DataFrame có schema nên Spark dễ tối ưu hơn.\r\n- DataFrame phù hợp cho phân tích có cấu trúc và các truy vấn kiểu SQL.\r\n\r\n## 3. DataFrame và Dataset\r\n- DataFrame linh hoạt và hỗ trợ nhiều ngôn ngữ.\r\n- Dataset kiểm tra kiểu ở thời điểm biên dịch, chỉ hỗ trợ Scala và Java.\r\n\r\n## 4. Kết luận\r\nDataFrame là abstraction quan trọng nhất trong Spark hiện đại vì nó kết hợp được tính dễ dùng và khả năng tối ưu.",
    "excerpt": "# Bài 1. Khái niệm DataFrame\nDataFrame trong Spark là một bảng phân tán có schema và tên cột rõ ràng.\n## 1. DataFrame là gì\n- Là cách nhìn dạng bảng trên dữ liệu phân tán.\n- Dữ liệu được tổ chức theo cột có kiểu rõ ràng.\n- Gần với cách suy nghĩ của SQL và các hệ dữ liệu quan hệ."
  },
  "C6-L2": {
    "lecId": "C6-L2",
    "chapterId": "C6",
    "chapterName": "Spark Dataframe",
    "title": "Column Expression",
    "contentPath": "Data/06_Spark_Dataframe/Bai_02_Column_Expression.md",
    "body": "# Bài 2. Biểu thức cột\r\n\r\nBiểu thức cột là nền tảng của mọi biến đổi trên DataFrame.\r\n\r\n## 1. Tư duy biểu thức cột\r\n- Các thao tác như select, where, groupBy hay withColumn đều được mô tả qua biểu thức cột.\r\n- Người viết code đang mô tả điều muốn làm, không phải chỉ cách thực thi chi tiết.\r\n\r\n## 2. Cú pháp và hàm hỗ trợ\r\n- Dùng data['age'] < 30 thay vì truy cập mơ hồ.\r\n- Dùng các hàm trong pyspark.sql.functions để viết logic rõ ràng.\r\n- Có thể tạo bảng tạm và viết Spark SQL khi logic phức tạp.\r\n\r\n## 3. Kết luận\r\nViết theo biểu thức cột giúp Spark hiểu được ý định của truy vấn và tối ưu kế hoạch thực thi tốt hơn.",
    "excerpt": "# Bài 2. Biểu thức cột\nBiểu thức cột là nền tảng của mọi biến đổi trên DataFrame.\n## 1. Tư duy biểu thức cột\n- Các thao tác như select, where, groupBy hay withColumn đều được mô tả qua biểu thức cột.\n- Người viết code đang mô tả điều muốn làm, không phải chỉ cách thực thi chi tiết.\n## 2. Cú pháp và hàm hỗ trợ"
  },
  "C6-L3": {
    "lecId": "C6-L3",
    "chapterId": "C6",
    "chapterName": "Spark Dataframe",
    "title": "The Optimizer",
    "contentPath": "Data/06_Spark_Dataframe/Bai_03_The_Optimizer.md",
    "body": "# Bài 3. Trình tối ưu hóa\r\n\r\nSpark có một trình tối ưu hóa mạnh mẽ cho DataFrame và SQL, giúp tự động cải thiện truy vấn trước khi thực thi.\r\n\r\n## 1. Vai trò của Catalyst\r\n- Xây dựng logical plan và physical plan.\r\n- Tự động loại bỏ cột thừa.\r\n- Đẩy bộ lọc xuống sớm để giảm dữ liệu phải đọc.\r\n- Chọn chiến lược phân vùng phù hợp hơn cho groupBy hoặc sort.\r\n\r\n## 2. Vì sao quan trọng\r\n- Vì người dùng chỉ mô tả kết quả mong muốn nên Spark có nhiều không gian để tối ưu.\r\n- Trình tối ưu giúp giảm chi phí shuffle và giảm dữ liệu phải xử lý.\r\n\r\n## 3. Kết luận\r\nOptimizer là lý do quan trọng khiến DataFrame và SQL trong Spark thường hiệu quả hơn code xử lý thủ công ở mức thấp.",
    "excerpt": "# Bài 3. Trình tối ưu hóa\nSpark có một trình tối ưu hóa mạnh mẽ cho DataFrame và SQL, giúp tự động cải thiện truy vấn trước khi thực thi.\n## 1. Vai trò của Catalyst\n- Xây dựng logical plan và physical plan.\n- Tự động loại bỏ cột thừa.\n- Đẩy bộ lọc xuống sớm để giảm dữ liệu phải đọc."
  },
  "C6-L4": {
    "lecId": "C6-L4",
    "chapterId": "C6",
    "chapterName": "Spark Dataframe",
    "title": "Input/Output",
    "contentPath": "Data/06_Spark_Dataframe/Bai_04_Input_Output.md",
    "body": "# Bài 4. Input/Output\r\n\r\nSpark hỗ trợ nhiều định dạng nhập và xuất dữ liệu, nhưng định dạng cột như Parquet thường là lựa chọn tối ưu cho phân tích.\r\n\r\n## 1. Vai trò của định dạng lưu trữ\r\n- CSV và JSON tiện trao đổi nhưng không tối ưu cho phân tích lớn.\r\n- Parquet và ORC là các định dạng cột giúp đọc nhanh và nén tốt.\r\n\r\n## 2. Phân vùng dữ liệu\r\n- Khi ghi dữ liệu có thể dùng partitionBy.\r\n- Dữ liệu được tổ chức thành các thư mục vật lý theo giá trị cột.\r\n- Truy vấn có thể bỏ qua phần lớn dữ liệu không liên quan.\r\n\r\n## 3. Kết luận\r\nChọn định dạng và cách phân vùng ảnh hưởng trực tiếp đến tốc độ quét, kích thước lưu trữ và hiệu năng truy vấn.",
    "excerpt": "# Bài 4. Input/Output\nSpark hỗ trợ nhiều định dạng nhập và xuất dữ liệu, nhưng định dạng cột như Parquet thường là lựa chọn tối ưu cho phân tích.\n## 1. Vai trò của định dạng lưu trữ\n- CSV và JSON tiện trao đổi nhưng không tối ưu cho phân tích lớn.\n- Parquet và ORC là các định dạng cột giúp đọc nhanh và nén tốt.\n## 2. Phân vùng dữ liệu"
  },
  "C6-L5": {
    "lecId": "C6-L5",
    "chapterId": "C6",
    "chapterName": "Spark Dataframe",
    "title": "User Defined Functions (UDFs)",
    "contentPath": "Data/06_Spark_Dataframe/Bai_05_User_Defined_Functions_UDFs.md",
    "body": "# Bài 5. Hàm tự định nghĩa (UDFs)\r\n\r\nKhi các hàm có sẵn của Spark không đủ cho logic nghiệp vụ, ta có thể dùng UDF. Tuy nhiên, phải cân nhắc kỹ vì UDF có thể làm giảm khả năng tối ưu.\r\n\r\n## 1. Các mức độ thực thi\r\n- Native Spark functions là nhanh nhất.\r\n- Pandas UDF nhanh hơn UDF Python thường nhờ xử lý theo vector.\r\n- Python UDF thường là chậm nhất vì phải chuyển đổi qua lại giữa JVM và Python.\r\n\r\n## 2. Khi nào nên dùng\r\n- Khi bài toán có logic đặc thù mà hàm có sẵn không hỗ trợ.\r\n- Khi không còn lựa chọn nào tốt hơn từ hệ hàm mặc định.\r\n\r\n## 3. Kết luận\r\nUDF hữu ích nhưng không nên là lựa chọn mặc định. Nếu có thể, hãy ưu tiên các hàm native của Spark và biểu thức khai báo để tối ưu tốt hơn.",
    "excerpt": "# Bài 5. Hàm tự định nghĩa (UDFs)\nKhi các hàm có sẵn của Spark không đủ cho logic nghiệp vụ, ta có thể dùng UDF. Tuy nhiên, phải cân nhắc kỹ vì UDF có thể làm giảm khả năng tối ưu.\n## 1. Các mức độ thực thi\n- Native Spark functions là nhanh nhất.\n- Pandas UDF nhanh hơn UDF Python thường nhờ xử lý theo vector.\n- Python UDF thường là chậm nhất vì phải chuyển đổi qua lại giữa JVM và Python."
  }
};
