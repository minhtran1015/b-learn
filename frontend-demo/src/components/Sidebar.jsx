import { CalendarDays, GraduationCap, HelpCircle, Mail, Settings, UserCircle } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext.jsx';
import { user } from '../data/mockData.js';

const globalItems = [
  { to: '/courses', label: 'Khóa học', icon: GraduationCap },
  { to: '/calendar', label: 'Lịch', icon: CalendarDays },
  { to: '/messages', label: 'Tin nhắn', icon: Mail },
  { to: '/help', label: 'Trợ giúp', icon: HelpCircle },
];

const accountItems = [
  { to: '/profile', label: 'Hồ sơ', icon: UserCircle },
  { to: '/settings', label: 'Cài đặt', icon: Settings },
];

export default function Sidebar() {
  const { currentUser } = useAuth();
  const displayUser = currentUser?.profile ?? user;
  const initials = (displayUser.fullName ?? user.name)
    .split(' ')
    .map((part) => part[0])
    .slice(-2)
    .join('')
    .toUpperCase();

  return (
    <aside className="sidebar">
      <NavLink to="/courses" className="brand">
        <span className="brand-mark">B</span>
        <span>
          <strong>BLearn</strong>
          <small>Học tập chính xác</small>
        </span>
      </NavLink>

      <div className="sidebar-main">
        <nav className="nav-section">
          <p className="nav-label">Hệ thống</p>
          {globalItems.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.to === '/'} className="nav-item">
              <item.icon size={20} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
      </div>

      <nav className="nav-section nav-account">
        <p className="nav-label">Tài khoản</p>
        {accountItems.map((item) => (
          <NavLink key={item.to} to={item.to} className="nav-item">
            <item.icon size={20} />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-user">
        <div className="avatar">{initials}</div>
        <div>
          <strong>{displayUser.fullName ?? user.name}</strong>
          <small>{displayUser.role}</small>
        </div>
      </div>
    </aside>
  );
}
