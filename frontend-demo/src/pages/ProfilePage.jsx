import { LogOut, Save, ShieldCheck } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext.jsx';
import PageHeader from '../components/PageHeader.jsx';

const emptyProfile = {
  fullName: '',
  role: '',
  phone: '',
  birthYear: '',
  gender: '',
  location: '',
  educationLevel: '',
  learningGoal: '',
  school: '',
  major: '',
  occupation: '',
  studyTimePreference: '',
};

export default function ProfilePage() {
  const { currentUser, isAuthenticated, logout, updateProfile } = useAuth();
  const [form, setForm] = useState(emptyProfile);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!currentUser) return;
    setForm({
      ...emptyProfile,
      ...currentUser.profile,
      ...currentUser.demographics,
    });
  }, [currentUser]);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  const handleSubmit = (event) => {
    event.preventDefault();
    updateProfile(form);
    setSaved(true);
    window.setTimeout(() => setSaved(false), 2200);
  };

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Tài khoản"
        title="Hồ sơ học viên"
        description="Cập nhật thông tin cá nhân, thông tin đăng nhập và nhân khẩu học phục vụ cá nhân hóa học tập."
      />

      <section className="profile-layout">
        <aside className="profile-summary card">
          <div className="profile-avatar">{form.fullName.split(' ').map((part) => part[0]).slice(-2).join('').toUpperCase() || 'U'}</div>
          <h2>{form.fullName}</h2>
          <p>{currentUser.email}</p>
          <span><ShieldCheck size={17} /> Lưu tạm trong trình duyệt</span>
          <div className="profile-actions">
            <Link className="button outline full" to="/settings">Cài đặt</Link>
            <button className="button ghost full" type="button" onClick={logout}><LogOut size={18} />Đăng xuất</button>
          </div>
        </aside>

        <form className="card profile-form" onSubmit={handleSubmit}>
          <div className="form-section-title">
            <h2>Thông tin cơ bản</h2>
            {saved && <span>Đã lưu thay đổi</span>}
          </div>
          <div className="form-row">
            <label>
              Họ và tên
              <input required value={form.fullName} onChange={(event) => setForm({ ...form, fullName: event.target.value })} />
            </label>
            <label>
              Vai trò
              <input value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value })} />
            </label>
          </div>
          <div className="form-row">
            <label>
              Email đăng nhập
              <input value={currentUser.email} disabled />
            </label>
            <label>
              Số điện thoại
              <input value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} />
            </label>
          </div>

          <div className="form-section-title">
            <h2>Nhân khẩu học</h2>
          </div>
          <div className="form-row">
            <label>
              Năm sinh
              <input value={form.birthYear} onChange={(event) => setForm({ ...form, birthYear: event.target.value })} />
            </label>
            <label>
              Giới tính
              <select value={form.gender} onChange={(event) => setForm({ ...form, gender: event.target.value })}>
                <option value="">Chọn</option>
                <option>Nam</option>
                <option>Nữ</option>
                <option>Khác</option>
                <option>Không muốn nêu</option>
              </select>
            </label>
          </div>
          <div className="form-row">
            <label>
              Khu vực
              <input value={form.location} onChange={(event) => setForm({ ...form, location: event.target.value })} />
            </label>
            <label>
              Trình độ học vấn
              <input value={form.educationLevel} onChange={(event) => setForm({ ...form, educationLevel: event.target.value })} />
            </label>
          </div>
          <div className="form-row">
            <label>
              Trường
              <input value={form.school} onChange={(event) => setForm({ ...form, school: event.target.value })} />
            </label>
            <label>
              Ngành học
              <input value={form.major} onChange={(event) => setForm({ ...form, major: event.target.value })} />
            </label>
          </div>
          <div className="form-row">
            <label>
              Nghề nghiệp
              <input value={form.occupation} onChange={(event) => setForm({ ...form, occupation: event.target.value })} />
            </label>
            <label>
              Thời gian học ưa thích
              <input value={form.studyTimePreference} onChange={(event) => setForm({ ...form, studyTimePreference: event.target.value })} />
            </label>
          </div>
          <label>
            Mục tiêu học tập
            <textarea rows="4" value={form.learningGoal} onChange={(event) => setForm({ ...form, learningGoal: event.target.value })} />
          </label>
          <button className="button primary" type="submit"><Save size={18} />Lưu hồ sơ</button>
        </form>
      </section>
    </div>
  );
}
