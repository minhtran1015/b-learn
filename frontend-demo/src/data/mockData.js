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
    id: 'm1',
    title: 'Giới thiệu về Neural Networks',
    type: 'Video bài giảng',
    duration: '45:20',
    views: '1.2k',
    status: 'Đang học',
    chapter: 'Chương 1: Nền tảng Học máy',
  },
  {
    id: 'm2',
    title: 'Tài liệu tóm tắt: Các thuật toán cốt lõi',
    type: 'PDF',
    duration: '15 trang',
    views: '856',
    status: 'Đã hoàn thành',
    chapter: 'Chương 1: Nền tảng Học máy',
  },
  {
    id: 'm3',
    title: 'Tối ưu hóa Mô hình Học máy Cơ bản',
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

export const recommendations = [
  'Ôn lại Big O trước bài kiểm tra cấu trúc dữ liệu.',
  'Hoàn thành video 3.2 để mở khóa bài thực hành ROC/AUC.',
  'Tham gia thảo luận về API Gateway để nhận phản hồi sớm.',
];
