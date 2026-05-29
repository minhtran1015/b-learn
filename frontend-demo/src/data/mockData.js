export const user = {
  name: 'Minh Quân',
  role: 'Sinh viên năm 3',
  rank: 'Hạng Kim Cương',
};

export const courses = [
  {
    id: 'machine-learning',
    title: 'Học máy nâng cao',
    teacher: 'TS. Nguyễn Văn A',
    level: 'Khó',
    progress: 65,
    color: 'blue',
    description: 'Tối ưu mô hình, đánh giá độ chính xác và triển khai quy trình học máy thực tế.',
    accent: 'Neural',
  },
  {
    id: 'data-python',
    title: 'Phân tích dữ liệu với Python',
    teacher: 'ThS. Lê Thị B',
    level: 'Trung bình',
    progress: 82,
    color: 'green',
    description: 'Làm sạch dữ liệu, trực quan hóa và xây dựng báo cáo phân tích bằng Python.',
    accent: 'Python',
  },
  {
    id: 'system-design',
    title: 'Thiết kế hệ thống',
    teacher: 'TS. Trần Văn C',
    level: 'Khó',
    progress: 35,
    color: 'red',
    description: 'Kiến trúc microservices, giao dịch phân tán và khả năng mở rộng hệ thống lớn.',
    accent: 'System',
  },
  // ─── KHÓA HỌC TÙY CHỈNH – Lecture_Bank.json & Question_Bank.json ──────────
  // Mỗi học liệu và bài tập đều mang id_site_mapping trỏ về ID thực của OULAD VLE
  // để khi người dùng tương tác, frontend âm thầm đẩy OULAD id_site sang Kafka.
  {
    id: 'big-data-course',
    title: 'Hệ thống Dữ liệu lớn (Big Data)',
    teacher: 'TS. Đặng Văn D',
    level: 'Khó',
    progress: 15,
    color: 'purple',
    description: 'Xử lý dữ liệu phân tán với Hadoop, Spark và các hệ sinh thái dữ liệu lớn.',
    accent: 'BigData',
    // Metadata ánh xạ: khóa học ánh xạ sang mô-đun OULAD thực tế
    _source: 'Lecture_Bank',
    _oulad_course_mapping: 'AAA',
  },
];

// ─── Học liệu gốc (machine-learning course) ──────────────────────────────────
export const materials = [
  {
    id: '546803',
    id_site: '546803',
    // id_site_mapping: chính là id_site, giữ nhất quán với interface
    id_site_mapping: '546803',
    title: 'Giới thiệu về Neural Networks (Học phần #546803)',
    type: 'Video bài giảng',
    duration: '45:20',
    views: '1.2k',
    status: 'Đang học',
    chapter: 'Chương 1: Nền tảng Học máy',
  },
  {
    id: '546652',
    id_site: '546652',
    id_site_mapping: '546652',
    title: 'Tài liệu tóm tắt: Các thuật toán cốt lõi (Học phần #546652)',
    type: 'PDF',
    duration: '15 trang',
    views: '856',
    status: 'Đã hoàn thành',
    chapter: 'Chương 1: Nền tảng Học máy',
  },
  {
    id: '546732',
    id_site: '546732',
    id_site_mapping: '546732',
    title: 'Tối ưu hóa Mô hình Học máy Cơ bản (Học phần #546732)',
    type: 'Video',
    duration: '12 phút',
    views: '932',
    status: 'Mở khóa',
    chapter: 'Chương 3: Phân tích Dữ liệu Nâng cao',
  },
];

// ─── HỌC LIỆU KHÓA HỌC TÙY CHỈNH – Big Data (Lecture_Bank.json) ─────────────
// Trường id_site_mapping trỏ về các mã ID thực của OULAD VLE resource.
// Khi người dùng click/hoàn thành, frontend sẽ extract id_site_mapping này
// và gửi nó sang /track-click thay vì id hiển thị nội bộ.
export const customCourseMaterials = [
  // ── Chương 1: Foundations of Big Data ─────────────────────────────────────
  {
    id: 'bd-c1-l1',
    id_site_mapping: '546803', // → OULAD VLE resource ID thực
    title: 'Bài 1: Concepts – From Data to Intelligence',
    type: 'Video bài giảng',
    duration: '38 phút',
    views: '1.4k',
    status: 'Đang học',
    chapter: 'Chương 1: Foundations of Big Data',
    lecId: 'C1-L1',
    chapterId: 'C1',
    _bank_source: 'Lecture_Bank',
  },
  {
    id: 'bd-c1-l2',
    id_site_mapping: '546652', // → OULAD VLE resource ID thực
    title: 'Bài 2: When Does Data Become Big?',
    type: 'PDF',
    duration: '12 trang',
    views: '987',
    status: 'Mở khóa',
    chapter: 'Chương 1: Foundations of Big Data',
    lecId: 'C1-L2',
    chapterId: 'C1',
    _bank_source: 'Lecture_Bank',
  },
  {
    id: 'bd-c1-l3',
    id_site_mapping: '546732', // → OULAD VLE resource ID thực
    title: 'Bài 3: Big Data Characteristics – The 3Vs, 5Vs, 6Vs',
    type: 'Video bài giảng',
    duration: '42 phút',
    views: '1.1k',
    status: 'Mở khóa',
    chapter: 'Chương 1: Foundations of Big Data',
    lecId: 'C1-L3',
    chapterId: 'C1',
    _bank_source: 'Lecture_Bank',
  },
  {
    id: 'bd-c1-l4',
    id_site_mapping: '546803', // → OULAD VLE resource ID thực (tái sử dụng – hợp lệ OULAD)
    title: 'Bài 4: The Big Data System – Architecture & Components',
    type: 'PDF',
    duration: '18 trang',
    views: '762',
    status: 'Mở khóa',
    chapter: 'Chương 1: Foundations of Big Data',
    lecId: 'C1-L4',
    chapterId: 'C1',
    _bank_source: 'Lecture_Bank',
  },
  {
    id: 'bd-c1-l5',
    id_site_mapping: '546652', // → OULAD VLE resource ID thực
    title: 'Bài 5: Big Data Jobs – Roles & Career Paths',
    type: 'Video bài giảng',
    duration: '25 phút',
    views: '634',
    status: 'Mở khóa',
    chapter: 'Chương 1: Foundations of Big Data',
    lecId: 'C1-L5',
    chapterId: 'C1',
    _bank_source: 'Lecture_Bank',
  },
  // ── Chương 2: Big Data Ecosystems ─────────────────────────────────────────
  {
    id: 'bd-c2-l1',
    id_site_mapping: '546732', // → OULAD VLE resource ID thực
    title: 'Bài 1: Data Modeling in Big Data Systems',
    type: 'Video bài giảng',
    duration: '35 phút',
    views: '891',
    status: 'Mở khóa',
    chapter: 'Chương 2: Big Data Ecosystems',
    lecId: 'C2-L1',
    chapterId: 'C2',
    _bank_source: 'Lecture_Bank',
  },
  {
    id: 'bd-c2-l2',
    id_site_mapping: '546803', // → OULAD VLE resource ID thực
    title: 'Bài 2: Modern Big Data Stack – Kafka, Spark, Iceberg',
    type: 'PDF',
    duration: '20 trang',
    views: '1.3k',
    status: 'Mở khóa',
    chapter: 'Chương 2: Big Data Ecosystems',
    lecId: 'C2-L2',
    chapterId: 'C2',
    _bank_source: 'Lecture_Bank',
  },
  {
    id: 'bd-c2-l3',
    id_site_mapping: '546652', // → OULAD VLE resource ID thực
    title: 'Bài 3: Modern Data Platform – Lakehouse Architecture',
    type: 'Video bài giảng',
    duration: '40 phút',
    views: '978',
    status: 'Mở khóa',
    chapter: 'Chương 2: Big Data Ecosystems',
    lecId: 'C2-L3',
    chapterId: 'C2',
    _bank_source: 'Lecture_Bank',
  },
  {
    id: 'bd-c2-l4',
    id_site_mapping: '546732', // → OULAD VLE resource ID thực
    title: 'Bài 4: Big Data Analysis – Descriptive to Prescriptive',
    type: 'PDF',
    duration: '16 trang',
    views: '745',
    status: 'Mở khóa',
    chapter: 'Chương 2: Big Data Ecosystems',
    lecId: 'C2-L4',
    chapterId: 'C2',
    _bank_source: 'Lecture_Bank',
  },
  {
    id: 'bd-c2-l5',
    id_site_mapping: '546803', // → OULAD VLE resource ID thực
    title: 'Bài 5: Big Data Applications & Landscape',
    type: 'Video bài giảng',
    duration: '30 phút',
    views: '612',
    status: 'Mở khóa',
    chapter: 'Chương 2: Big Data Ecosystems',
    lecId: 'C2-L5',
    chapterId: 'C2',
    _bank_source: 'Lecture_Bank',
  },
  // ── Chương 3: Big Data Storage ─────────────────────────────────────────────
  {
    id: 'bd-c3-l1',
    id_site_mapping: '546652', // → OULAD VLE resource ID thực
    title: 'Bài 1: Introduction Big Data Storage – Block, File, Object',
    type: 'Video bài giảng',
    duration: '45 phút',
    views: '1.0k',
    status: 'Mở khóa',
    chapter: 'Chương 3: Big Data Storage',
    lecId: 'C3-L1',
    chapterId: 'C3',
    _bank_source: 'Lecture_Bank',
  },
  {
    id: 'bd-c3-l2',
    id_site_mapping: '546732', // → OULAD VLE resource ID thực
    title: 'Bài 2: Decisive Principles – CAP, ACID, BASE',
    type: 'PDF',
    duration: '14 trang',
    views: '822',
    status: 'Mở khóa',
    chapter: 'Chương 3: Big Data Storage',
    lecId: 'C3-L2',
    chapterId: 'C3',
    _bank_source: 'Lecture_Bank',
  },
  {
    id: 'bd-c3-l3',
    id_site_mapping: '546803', // → OULAD VLE resource ID thực
    title: 'Bài 3: Big Data Storage Solutions – HDFS, S3, Ceph',
    type: 'Video bài giảng',
    duration: '38 phút',
    views: '789',
    status: 'Mở khóa',
    chapter: 'Chương 3: Big Data Storage',
    lecId: 'C3-L3',
    chapterId: 'C3',
    _bank_source: 'Lecture_Bank',
  },
  // ── Chương 4: Big Data Paradigms ──────────────────────────────────────────
  {
    id: 'bd-c4-l1',
    id_site_mapping: '546652', // → OULAD VLE resource ID thực
    title: 'Bài 1: Big Data Processing Paradigms – Batch vs Stream',
    type: 'Video bài giảng',
    duration: '36 phút',
    views: '1.2k',
    status: 'Mở khóa',
    chapter: 'Chương 4: Big Data Paradigms',
    lecId: 'C4-L1',
    chapterId: 'C4',
    _bank_source: 'Lecture_Bank',
  },
  {
    id: 'bd-c4-l2',
    id_site_mapping: '546732', // → OULAD VLE resource ID thực
    title: 'Bài 2: MapReduce Fundamentals',
    type: 'PDF',
    duration: '22 trang',
    views: '956',
    status: 'Mở khóa',
    chapter: 'Chương 4: Big Data Paradigms',
    lecId: 'C4-L2',
    chapterId: 'C4',
    _bank_source: 'Lecture_Bank',
  },
  // ── Chương 5: Spark ────────────────────────────────────────────────────────
  {
    id: 'bd-c5-l1',
    id_site_mapping: '546803', // → OULAD VLE resource ID thực
    title: 'Bài 1: From MapReduce to Spark – Motivation & Overview',
    type: 'Video bài giảng',
    duration: '48 phút',
    views: '1.6k',
    status: 'Mở khóa',
    chapter: 'Chương 5: Spark',
    lecId: 'C5-L1',
    chapterId: 'C5',
    _bank_source: 'Lecture_Bank',
  },
  {
    id: 'bd-c5-l2',
    id_site_mapping: '546652', // → OULAD VLE resource ID thực
    title: 'Bài 2: Spark Programming Model – RDD, DataFrame, Dataset',
    type: 'PDF',
    duration: '25 trang',
    views: '1.1k',
    status: 'Mở khóa',
    chapter: 'Chương 5: Spark',
    lecId: 'C5-L2',
    chapterId: 'C5',
    _bank_source: 'Lecture_Bank',
  },
];

// ─── BÀI TẬP KHÓA HỌC TÙY CHỈNH – Big Data (Question_Bank.json) ─────────────
// Trường id_site_mapping trỏ về OULAD id_assessment thực.
// Khi nộp bài, DoAssignmentPage sẽ extract id_site_mapping làm assignment_id gửi sang API.
export const customCourseAssignments = [
  {
    id: 'bd-quiz-c1',
    id_site_mapping: '546803', // → OULAD assessment ID thực (ánh xạ sang C1 assessment)
    title: 'Quiz Chương 1: Foundations of Big Data',
    summary: 'Kiểm tra kiến thức nền tảng: 3Vs, kiến trúc hệ thống, các vai trò Big Data.',
    duration: '20m',
    difficulty: 'Dễ',
    status: 'active',
    chapter: 'Chương 1: Foundations of Big Data',
    chapterId: 'C1',
    questionCount: 20,
    _bank_source: 'Question_Bank',
  },
  {
    id: 'bd-quiz-c2',
    id_site_mapping: '546652', // → OULAD assessment ID thực (ánh xạ sang C2 assessment)
    title: 'Quiz Chương 2: Big Data Ecosystems & Modern Stack',
    summary: 'Kiểm tra hiểu biết về Kafka, Spark, Lakehouse, Lambda/Kappa Architecture.',
    duration: '25m',
    difficulty: 'Trung bình',
    status: 'todo',
    chapter: 'Chương 2: Big Data Ecosystems',
    chapterId: 'C2',
    questionCount: 20,
    _bank_source: 'Question_Bank',
  },
  {
    id: 'bd-quiz-c3',
    id_site_mapping: '546732', // → OULAD assessment ID thực (ánh xạ sang C3 assessment)
    title: 'Quiz Chương 3: Big Data Storage – Block, Object, HDFS',
    summary: 'Kiểm tra kiến thức về CAP theorem, các loại storage, sharding và replication.',
    duration: '30m',
    difficulty: 'Trung bình',
    status: 'todo',
    chapter: 'Chương 3: Big Data Storage',
    chapterId: 'C3',
    questionCount: 20,
    _bank_source: 'Question_Bank',
  },
  {
    id: 'bd-quiz-c4',
    id_site_mapping: '546803', // → OULAD assessment ID thực (tái sử dụng hợp lệ)
    title: 'Quiz Chương 4: MapReduce & Processing Paradigms',
    summary: 'Kiểm tra hiểu biết về MapReduce, Lambda Architecture, Batch và Stream Processing.',
    duration: '35m',
    difficulty: 'Khó',
    status: 'todo',
    chapter: 'Chương 4: Big Data Paradigms',
    chapterId: 'C4',
    questionCount: 20,
    _bank_source: 'Question_Bank',
  },
  {
    id: 'bd-quiz-c5',
    id_site_mapping: '546652', // → OULAD assessment ID thực
    title: 'Quiz Chương 5: Apache Spark Deep Dive',
    summary: 'Kiểm tra kiến thức về RDD, Transformation/Action, Spark Architecture và UDFs.',
    duration: '40m',
    difficulty: 'Khó',
    status: 'todo',
    chapter: 'Chương 5: Spark',
    chapterId: 'C5',
    questionCount: 20,
    _bank_source: 'Question_Bank',
  },
];

export const assignments = [
  {
    id: 'a1',
    title: 'Thiết kế API Gateway cơ bản',
    summary: 'Xây dựng kiến trúc định tuyến request cho 3 services độc lập.',
    duration: '30m',
    difficulty: 'Dễ',
    status: 'done',
    chapter: 'Chương 1: Cơ bản về Microservices',
  },
  {
    id: 'a2',
    title: 'Phân tách Monolith sang Microservices',
    summary: 'Phân tích domain và thiết kế ranh giới ngữ cảnh cho ứng dụng E-commerce.',
    duration: '45m',
    difficulty: 'Trung bình',
    status: 'active',
    chapter: 'Chương 1: Cơ bản về Microservices',
  },
  {
    id: 'a3',
    title: 'Quản lý giao dịch trong Distributed Systems',
    summary: 'Áp dụng 2PC và thuật toán đồng thuận để đảm bảo tính nhất quán dữ liệu.',
    duration: '60m',
    difficulty: 'Khó',
    status: 'todo',
    chapter: 'Chương 2: Quản lý giao dịch phân tán',
  },
];

export const recentActivities = [
  'Hoàn thành bài tập Lab 4',
  'Đọc tài liệu SQL Optimization',
  'Lịch kiểm tra sắp tới',
];

export const calendarEvents = [
  {
    date: '2026-05-30',
    time: '23:59',
    title: 'Nộp bài Lab 4',
    course: 'Học máy nâng cao',
    type: 'Deadline',
    status: 'urgent',
  },
  {
    date: '2026-06-02',
    time: '08:30',
    title: 'Kiểm tra giữa kỳ',
    course: 'Thiết kế hệ thống',
    type: 'Kiểm tra',
    status: 'exam',
    location: 'Phòng B203',
  },
  {
    date: '2026-06-05',
    time: '19:30',
    title: 'Thảo luận case study',
    course: 'Phân tích dữ liệu với Python',
    type: 'Buổi học',
    status: 'class',
    location: 'Google Meet',
  },
  {
    date: '2026-06-10',
    time: '20:00',
    title: 'Nộp notebook trực quan hóa',
    course: 'Phân tích dữ liệu với Python',
    type: 'Deadline',
    status: 'deadline',
  },
  {
    date: '2026-06-14',
    time: '09:00',
    title: 'Review kiến trúc microservices',
    course: 'Thiết kế hệ thống',
    type: 'Workshop',
    status: 'class',
  },
  {
    date: '2026-06-07',
    time: '23:59',
    title: 'Quiz Chương 1 – Big Data Foundations',
    course: 'Hệ thống Dữ liệu lớn (Big Data)',
    type: 'Deadline',
    status: 'urgent',
  },
];

export const inboxMessages = [
  {
    id: 'msg-1',
    sender: 'TS. Nguyễn Văn A',
    role: 'Giảng viên',
    subject: 'Nhắc hạn nộp báo cáo mô hình',
    preview: 'Các nhóm cần cập nhật notebook và gửi link trước hạn nộp cuối tuần.',
    body: 'Các nhóm vui lòng cập nhật notebook huấn luyện, biểu đồ đánh giá và link repository trước 23:59 ngày 30/05. Nếu có thay đổi thành viên nhóm, phản hồi lại email này trước thứ Sáu.',
    course: 'Học máy nâng cao',
    sentAt: 'Hôm nay, 09:15',
    unread: true,
    priority: 'Cao',
  },
  {
    id: 'msg-2',
    sender: 'Phòng đào tạo',
    role: 'Ban quản lý',
    subject: 'Lịch kiểm tra học kỳ',
    preview: 'Lịch kiểm tra chính thức đã được cập nhật, vui lòng kiểm tra lại phòng thi.',
    body: 'Lịch kiểm tra học kỳ đã được chốt trên hệ thống. Sinh viên cần kiểm tra phòng thi, thời gian bắt đầu và có mặt trước giờ thi 15 phút.',
    course: 'Toàn hệ thống',
    sentAt: 'Hôm qua, 16:40',
    unread: true,
    priority: 'Quan trọng',
  },
  {
    id: 'msg-3',
    sender: 'ThS. Lê Thị B',
    role: 'Giảng viên',
    subject: 'Tài liệu bổ sung tuần 6',
    preview: 'Cô đã gửi thêm bộ dữ liệu mẫu để thực hành trực quan hóa.',
    body: 'Bộ dữ liệu mẫu và notebook gợi ý đã được thêm vào mục tài liệu tuần 6. Các em nên hoàn thành phần làm sạch dữ liệu trước buổi học tiếp theo.',
    course: 'Phân tích dữ liệu với Python',
    sentAt: 'Thứ Ba, 20:10',
    unread: false,
    priority: 'Bình thường',
  },
  {
    id: 'msg-4',
    sender: 'TS. Đặng Văn D',
    role: 'Giảng viên',
    subject: 'Khai giảng khóa Big Data – Lịch học và tài liệu',
    preview: 'Khóa Hệ thống Dữ liệu lớn bắt đầu tuần này. Vui lòng xem trước Chương 1.',
    body: 'Xin chào các em, khóa học Hệ thống Dữ liệu lớn chính thức bắt đầu. Các em hãy vào mục Tài liệu để đọc bài Chương 1 trước buổi học trực tiếp đầu tiên vào thứ Ba. Quiz Chương 1 sẽ mở vào cuối tuần này.',
    course: 'Hệ thống Dữ liệu lớn (Big Data)',
    sentAt: 'Hôm nay, 07:30',
    unread: true,
    priority: 'Cao',
  },
];

export const helpTopics = [
  {
    title: 'Vào khóa học và học tiếp',
    description: 'Mở Khóa học, chọn khóa đang học, sau đó dùng sidebar trong khóa để đi tới tài liệu, bài tập hoặc phân tích.',
    category: 'Học tập',
  },
  {
    title: 'Theo dõi tiến độ và phân tích',
    description: 'Mỗi khóa có trang Phân tích học tập riêng để xem mức độ thành thạo, tần suất học và dự báo hoàn thành.',
    category: 'Báo cáo',
  },
  {
    title: 'Liên hệ hỗ trợ',
    description: 'Gửi email tới support@blearn.test hoặc liên hệ phòng quản lý đào tạo trong giờ hành chính.',
    category: 'Hỗ trợ',
  },
];

export const discussionThreads = [
  {
    title: 'Có nên chuẩn hóa dữ liệu trước khi train mọi mô hình?',
    author: 'Minh Quân',
    replies: 8,
    lastActive: '12 phút trước',
    tag: 'Học máy',
  },
  {
    title: 'Cách chọn boundary cho service thanh toán',
    author: 'Hoàng Nam',
    replies: 5,
    lastActive: '1 giờ trước',
    tag: 'Thiết kế hệ thống',
  },
  {
    title: 'Notebook tuần 6 bị lỗi khi merge dataframe',
    author: 'Lan Anh',
    replies: 3,
    lastActive: 'Hôm qua',
    tag: 'Python',
  },
  {
    title: 'Tại sao Lambda Architecture lại cần cả Batch lẫn Speed Layer?',
    author: 'Minh Quân',
    replies: 6,
    lastActive: '30 phút trước',
    tag: 'Big Data',
  },
];
