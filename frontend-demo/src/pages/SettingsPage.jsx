import { Bell, LockKeyhole, Moon, Save, ShieldCheck } from 'lucide-react';
import PageHeader from '../components/PageHeader.jsx';

const settings = [
  { icon: Bell, title: 'Nhắc lịch học và deadline', description: 'Gửi thông báo trước hạn nộp 24 giờ và 2 giờ.' },
  { icon: ShieldCheck, title: 'Thông báo từ giảng viên', description: 'Ưu tiên hiển thị email quan trọng trong hộp thư.' },
  { icon: Moon, title: 'Chế độ tập trung buổi tối', description: 'Giảm thông báo không khẩn cấp sau 22:00.' },
  { icon: LockKeyhole, title: 'Bảo mật phiên đăng nhập', description: 'Yêu cầu đăng nhập lại khi thay đổi hồ sơ cá nhân.' },
];

export default function SettingsPage() {
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
      </section>
    </div>
  );
}
