import { Headphones, LifeBuoy, Mail, MessageCircle, Phone, Search } from 'lucide-react';
import PageHeader from '../components/PageHeader.jsx';
import { helpTopics } from '../data/mockData.js';

const supportChannels = [
  { icon: Mail, label: 'Email', value: 'support@blearn.test', note: 'Phản hồi trong 1 ngày làm việc' },
  { icon: Phone, label: 'Hotline', value: '1900 0101', note: '08:00 - 17:30, Thứ 2 - Thứ 6' },
  { icon: MessageCircle, label: 'Chat nội bộ', value: 'Mở yêu cầu hỗ trợ', note: 'Theo dõi trạng thái ngay trên hệ thống' },
];

export default function HelpPage() {
  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Hỗ trợ"
        title="Trợ giúp"
        description="Tìm nhanh hướng dẫn sử dụng, quy trình xử lý lỗi và kênh liên hệ phù hợp."
        action={<button className="button primary"><LifeBuoy size={18} />Tạo yêu cầu</button>}
      />

      <section className="help-hero">
        <Headphones size={42} />
        <div>
          <h2>Bạn cần hỗ trợ phần nào?</h2>
          <p>Nhập từ khóa về đăng nhập, khóa học, bài tập, lịch hoặc phân tích học tập.</p>
        </div>
        <label className="help-search">
          <Search size={19} />
          <input placeholder="Tìm hướng dẫn..." />
        </label>
      </section>

      <section className="help-layout">
        <div className="faq-panel">
          <div className="section-title">
            <h2>Câu hỏi thường gặp</h2>
          </div>
          <div className="faq-list">
            {helpTopics.map((topic) => (
              <article key={topic.title} className="faq-item">
                <span>{topic.category}</span>
                <h3>{topic.title}</h3>
                <p>{topic.description}</p>
              </article>
            ))}
          </div>
        </div>

        <aside className="support-panel">
          <h2>Kênh liên hệ</h2>
          {supportChannels.map((channel) => (
            <div key={channel.label} className="support-card">
              <channel.icon size={22} />
              <div>
                <strong>{channel.label}</strong>
                <span>{channel.value}</span>
                <small>{channel.note}</small>
              </div>
            </div>
          ))}
        </aside>
      </section>
    </div>
  );
}
