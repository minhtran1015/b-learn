import { MessageSquare, Plus, Search } from 'lucide-react';
import PageHeader from '../components/PageHeader.jsx';
import { discussionThreads } from '../data/mockData.js';

export default function DiscussionsPage() {
  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Không gian khóa học"
        title="Thảo luận khóa học"
        description="Theo dõi câu hỏi đang mở, chủ đề nổi bật và phản hồi mới từ giảng viên hoặc bạn học."
        action={<button className="button primary"><Plus size={18} />Tạo chủ đề</button>}
      />

      <section className="discussion-layout">
        <div className="discussion-board">
          <label className="mail-search">
            <Search size={18} />
            <input placeholder="Tìm chủ đề thảo luận..." />
          </label>
          <div className="mail-tabs">
            <button className="active">Đang nổi bật</button>
            <button>Chưa trả lời</button>
            <button>Của tôi</button>
          </div>
          {discussionThreads.map((thread) => (
            <article key={thread.title} className="thread-card">
              <div className="thread-icon"><MessageSquare size={20} /></div>
              <div>
                <span>{thread.tag}</span>
                <h3>{thread.title}</h3>
                <p>{thread.author} • {thread.lastActive}</p>
              </div>
              <strong>{thread.replies} trả lời</strong>
            </article>
          ))}
        </div>
        <aside className="support-panel">
          <h2>Quy tắc nhanh</h2>
          <div className="support-card">
            <MessageSquare size={22} />
            <div>
              <strong>Viết rõ ngữ cảnh</strong>
              <span>Đính kèm bài, chương hoặc lỗi gặp phải</span>
              <small>Giúp giảng viên phản hồi chính xác hơn</small>
            </div>
          </div>
        </aside>
      </section>
    </div>
  );
}
