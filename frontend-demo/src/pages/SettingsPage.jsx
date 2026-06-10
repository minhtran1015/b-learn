import { Bell, LockKeyhole, Moon, Save, ShieldCheck, RotateCcw } from 'lucide-react';
import PageHeader from '../components/PageHeader.jsx';

const settings = [
  { icon: Bell, title: 'Nhắc lịch học và deadline', description: 'Gửi thông báo trước hạn nộp 24 giờ và 2 giờ.' },
  { icon: ShieldCheck, title: 'Thông báo từ giảng viên', description: 'Ưu tiên hiển thị email quan trọng trong hộp thư.' },
  { icon: Moon, title: 'Chế độ tập trung buổi tối', description: 'Giảm thông báo không khẩn cấp sau 22:00.' },
  { icon: LockKeyhole, title: 'Bảo mật phiên đăng nhập', description: 'Yêu cầu đăng nhập lại khi thay đổi hồ sơ cá nhân.' },
];

export default function SettingsPage() {
  const handleResetDemo = async () => {
    if (window.confirm("Bạn có chắc chắn muốn reset toàn bộ trạng thái demo trên cả client và Serving Gateway?")) {
      try {
        const rawBaseUrl = import.meta.env.VITE_GATEWAY_URL || 'http://localhost:8000';
        const API_BASE_URL = rawBaseUrl.replace(/\/$/, '');
        const token = localStorage.getItem('blearn.gatewayToken');
        if (token) {
          await fetch(`${API_BASE_URL}/reset-assessment-shifts`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
        }
      } catch (err) {
        console.error("Gateway reset failed:", err);
      }
      localStorage.removeItem('blearn.activeCourseId');
      localStorage.removeItem('blearn.gatewayToken');
      localStorage.removeItem('blearn.studentHash');
      localStorage.removeItem('blearn.recommendationMaterials');
      sessionStorage.clear();
      
      window.dispatchEvent(new CustomEvent('blearn-toast', {
        detail: { message: 'Đã reset toàn bộ trạng thái demo thành công!', type: 'success' }
      }));
      
      setTimeout(() => {
        window.location.href = '/login';
      }, 1000);
    }
  };

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Tài khoản"
        title="Cài đặt"
        description="Điều chỉnh thông báo, quyền riêng tư và trải nghiệm học tập cá nhân."
        action={<button className="button primary"><Save size={18} />Lưu thay đổi</button>}
      />

      <section className="settings-grid">
        {settings.map((item, index) => (
          <article key={item.title} className="setting-card">
            <item.icon size={24} />
            <div>
              <h3>{item.title}</h3>
              <p>{item.description}</p>
            </div>
            <label className="switch">
              <input type="checkbox" defaultChecked={index < 2} />
              <span />
            </label>
          </article>
        ))}

        <article className="setting-card" style={{ border: '1px dashed var(--danger)', background: 'rgba(239, 68, 68, 0.03)' }}>
          <RotateCcw size={24} style={{ color: 'var(--danger)' }} />
          <div>
            <h3 style={{ color: 'var(--danger)' }}>Quản trị Trình diễn (Demo Admin)</h3>
            <p>Xóa sạch toàn bộ lịch sử tương tác, đưa vector đặc trưng và nguy cơ bỏ học về trạng thái ban đầu.</p>
          </div>
          <button className="button outline danger" onClick={handleResetDemo}>
            <RotateCcw size={16} /> Reset Demo
          </button>
        </article>
      </section>
    </div>
  );
}
