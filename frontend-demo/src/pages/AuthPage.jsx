import { ArrowRight, BookOpenCheck, LockKeyhole, Mail, UserPlus } from 'lucide-react';
import { useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext.jsx';
import { demoCredentials } from '../data/tempUsers.js';

const initialRegister = {
  fullName: '',
  email: '',
  password: '',
  role: 'Học viên',
  birthYear: '',
  gender: '',
  location: '',
  educationLevel: '',
  school: '',
  major: '',
  occupation: '',
  studyTimePreference: '',
  learningGoal: '',
};

export default function AuthPage({ mode }) {
  const isRegister = mode === 'register';
  const navigate = useNavigate();
  const { isAuthenticated, login, register } = useAuth();
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loginForm, setLoginForm] = useState({ email: demoCredentials.email, password: demoCredentials.password });
  const [registerForm, setRegisterForm] = useState(initialRegister);

  if (isAuthenticated) {
    return <Navigate to="/profile" replace />;
  }

  const handleLogin = async (event) => {
    event.preventDefault();
    setError('');
    setIsSubmitting(true);
    try {
      await login(loginForm);
      navigate('/profile');
    } catch (loginError) {
      setError(loginError.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRegister = async (event) => {
    event.preventDefault();
    setError('');
    setIsSubmitting(true);
    try {
      await register(registerForm);
      navigate('/profile');
    } catch (registerError) {
      setError(registerError.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="auth-shell">
      <section className="auth-panel">
        <Link to="/" className="brand auth-brand">
          <span className="brand-mark">B</span>
          <span>
            <strong>BLearn</strong>
            <small>Học tập chính xác</small>
          </span>
        </Link>
        <div>
          <p className="eyebrow">Tài khoản học tập</p>
          <h1>{isRegister ? 'Tạo tài khoản mới' : 'Đăng nhập'}</h1>
          <p className="auth-copy">
            {isRegister
              ? 'Thiết lập hồ sơ học tập để hệ thống cá nhân hóa lộ trình và phân tích năng lực.'
              : 'Tiếp tục học tập, theo dõi tiến độ và quản lý hồ sơ cá nhân của bạn.'}
          </p>
        </div>
        <div className="auth-benefits">
          <span><BookOpenCheck size={18} /> Lưu tiến độ học tập</span>
          <span><LockKeyhole size={18} /> Mật khẩu được hash tạm thời</span>
          <span><UserPlus size={18} /> Sẵn sàng thay bằng database</span>
        </div>
      </section>

      <section className="auth-card">
        {isRegister ? (
          <form className="form-grid" onSubmit={handleRegister}>
            <div className="form-heading">
              <h2>Đăng ký</h2>
              <Link to="/login">Đã có tài khoản?</Link>
            </div>
            {error && <p className="form-error">{error}</p>}
            <label>
              Họ và tên
              <input required value={registerForm.fullName} onChange={(event) => setRegisterForm({ ...registerForm, fullName: event.target.value })} />
            </label>
            <label>
              Email
              <input required type="email" value={registerForm.email} onChange={(event) => setRegisterForm({ ...registerForm, email: event.target.value })} />
            </label>
            <label>
              Mật khẩu
              <input required minLength="6" type="password" value={registerForm.password} onChange={(event) => setRegisterForm({ ...registerForm, password: event.target.value })} />
            </label>
            <label>
              Vai trò
              <input value={registerForm.role} onChange={(event) => setRegisterForm({ ...registerForm, role: event.target.value })} />
            </label>
            <div className="form-row">
              <label>
                Năm sinh
                <input value={registerForm.birthYear} onChange={(event) => setRegisterForm({ ...registerForm, birthYear: event.target.value })} />
              </label>
              <label>
                Giới tính
                <select value={registerForm.gender} onChange={(event) => setRegisterForm({ ...registerForm, gender: event.target.value })}>
                  <option value="">Chọn</option>
                  <option>Nam</option>
                  <option>Nữ</option>
                  <option>Khác</option>
                  <option>Không muốn nêu</option>
                </select>
              </label>
            </div>
            <label>
              Khu vực
              <input value={registerForm.location} onChange={(event) => setRegisterForm({ ...registerForm, location: event.target.value })} />
            </label>
            <label>
              Trình độ học vấn
              <input value={registerForm.educationLevel} onChange={(event) => setRegisterForm({ ...registerForm, educationLevel: event.target.value })} />
            </label>
            <div className="form-row">
              <label>
                Trường
                <input value={registerForm.school} onChange={(event) => setRegisterForm({ ...registerForm, school: event.target.value })} />
              </label>
              <label>
                Ngành học
                <input value={registerForm.major} onChange={(event) => setRegisterForm({ ...registerForm, major: event.target.value })} />
              </label>
            </div>
            <div className="form-row">
              <label>
                Nghề nghiệp
                <input value={registerForm.occupation} onChange={(event) => setRegisterForm({ ...registerForm, occupation: event.target.value })} />
              </label>
              <label>
                Thời gian học
                <input value={registerForm.studyTimePreference} onChange={(event) => setRegisterForm({ ...registerForm, studyTimePreference: event.target.value })} />
              </label>
            </div>
            <label>
              Mục tiêu học tập
              <textarea rows="3" value={registerForm.learningGoal} onChange={(event) => setRegisterForm({ ...registerForm, learningGoal: event.target.value })} />
            </label>
            <button className="button primary full" disabled={isSubmitting}>
              Tạo tài khoản <ArrowRight size={18} />
            </button>
          </form>
        ) : (
          <form className="form-grid compact" onSubmit={handleLogin}>
            <div className="form-heading">
              <h2>Đăng nhập</h2>
              <Link to="/register">Tạo tài khoản</Link>
            </div>
            {error && <p className="form-error">{error}</p>}
            <label>
              Email
              <span className="input-icon"><Mail size={18} /></span>
              <input required type="email" value={loginForm.email} onChange={(event) => setLoginForm({ ...loginForm, email: event.target.value })} />
            </label>
            <label>
              Mật khẩu
              <span className="input-icon"><LockKeyhole size={18} /></span>
              <input required type="password" value={loginForm.password} onChange={(event) => setLoginForm({ ...loginForm, password: event.target.value })} />
            </label>
            <button className="button primary full" disabled={isSubmitting}>
              Đăng nhập <ArrowRight size={18} />
            </button>
            <p className="form-note">Tài khoản demo: {demoCredentials.email} / {demoCredentials.password}</p>
          </form>
        )}
      </section>
    </main>
  );
}
