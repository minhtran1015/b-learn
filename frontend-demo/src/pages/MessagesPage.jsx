import { Archive, MailOpen, Reply, Search, Send } from 'lucide-react';
import PageHeader from '../components/PageHeader.jsx';
import { inboxMessages } from '../data/mockData.js';

export default function MessagesPage() {
  const activeMessage = inboxMessages[0];

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Hộp thư"
        title="Tin nhắn"
        description="Tập trung thông báo từ giảng viên và ban quản lý, ưu tiên những việc cần xử lý trước."
        action={<button className="button primary"><Send size={18} />Soạn tin</button>}
      />

      <section className="mail-layout">
        <aside className="mail-list-panel">
          <label className="mail-search">
            <Search size={18} />
            <input placeholder="Tìm người gửi, khóa học, tiêu đề..." />
          </label>
          <div className="mail-tabs">
            <button className="active">Tất cả</button>
            <button>Chưa đọc</button>
            <button>Quan trọng</button>
          </div>

          <div className="mail-list">
            {inboxMessages.map((message) => (
              <article key={message.id} className={`mail-item ${message.id === activeMessage.id ? 'active' : ''} ${message.unread ? 'unread' : ''}`}>
                <div className="mail-avatar">{message.sender.slice(0, 2).toUpperCase()}</div>
                <div>
                  <div className="mail-row">
                    <strong>{message.sender}</strong>
                    <time>{message.sentAt}</time>
                  </div>
                  <h3>{message.subject}</h3>
                  <p>{message.preview}</p>
                  <span>{message.course}</span>
                </div>
              </article>
            ))}
          </div>
        </aside>

        <article className="mail-reader">
          <div className="mail-reader-head">
            <div>
              <span>{activeMessage.priority}</span>
              <h2>{activeMessage.subject}</h2>
              <p>{activeMessage.sender} • {activeMessage.role} • {activeMessage.sentAt}</p>
            </div>
            <div className="mail-actions">
              <button aria-label="Đánh dấu đã đọc"><MailOpen size={18} /></button>
              <button aria-label="Lưu trữ"><Archive size={18} /></button>
            </div>
          </div>
          <div className="mail-body">
            <p>{activeMessage.body}</p>
            <div className="mail-context">
              <strong>Liên quan</strong>
              <span>{activeMessage.course}</span>
            </div>
          </div>
          <button className="button outline"><Reply size={18} />Trả lời</button>
        </article>
      </section>
    </div>
  );
}
