import { Bell, LogIn, Search, UserCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext.jsx';

export default function Topbar({ isCourseArea }) {
  const { isAuthenticated } = useAuth();

  return (
    <header className="topbar">
      <label className="search-box">
        <Search size={19} />
        <input placeholder={isCourseArea ? 'Tìm kiếm trong khóa học...' : 'Tìm kiếm tài liệu, khóa học...'} />
      </label>
      <div className="topbar-actions">
        <button className="icon-button" aria-label="Thông báo">
          <Bell size={21} />
          <span className="notify-dot" />
        </button>
        <Link to={isAuthenticated ? '/profile' : '/login'} className="profile-link">
          {isAuthenticated ? <UserCircle size={24} /> : <LogIn size={23} />}
          <span>{isAuthenticated ? 'Hồ sơ' : 'Đăng nhập'}</span>
        </Link>
      </div>
    </header>
  );
}
