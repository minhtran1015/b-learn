import PageHeader from '../components/PageHeader.jsx';
import { recommendations } from '../data/mockData.js';

const copy = {
  recommendations: {
    title: 'Gợi ý học tập',
    description: 'Các đề xuất tạm thời dựa trên dữ liệu giả để demo luồng giao diện.',
  },
  discussions: {
    title: 'Thảo luận khóa học',
    description: 'Khung trang thảo luận trong khóa học, sẵn sàng nối dữ liệu thật ở bước sau.',
  },
  settings: {
    title: 'Cài đặt',
    description: 'Trang cấu hình hồ sơ, thông báo và tùy chọn học tập.',
  },
  profile: {
    title: 'Hồ sơ',
    description: 'Thông tin cá nhân, năng lực hiện tại và tiến độ học tập tổng quan.',
  },
};

export default function SimplePage({ type }) {
  const page = copy[type] ?? copy.recommendations;

  return (
    <div className="page-stack">
      <PageHeader eyebrow="Demo" title={page.title} description={page.description} />
      <div className="card">
        <h2>Nội dung mẫu</h2>
        <ul className="check-list">
          {recommendations.map((item) => <li key={item}>{item}</li>)}
        </ul>
      </div>
    </div>
  );
}
