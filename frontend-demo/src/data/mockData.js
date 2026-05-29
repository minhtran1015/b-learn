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
];

export const materials = [
  {
    id: '546803',
    id_site: '546803',
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
    title: 'Tối ưu hóa Mô hình Học máy Cơ bản (Học phần #546732)',
    type: 'Video',
    duration: '12 phút',
    views: '932',
    status: 'Mở khóa',
    chapter: 'Chương 3: Phân tích Dữ liệu Nâng cao',
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
];
