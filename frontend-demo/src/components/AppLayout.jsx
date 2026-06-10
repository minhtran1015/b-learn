import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar.jsx';
import Topbar from './Topbar.jsx';
import { useEffect, useState } from 'react';

export default function AppLayout() {
  const location = useLocation();
  const courseMatch = location.pathname.match(/^\/courses\/([^/]+)/);
  const courseId = courseMatch?.[1];
  const isCourseArea = Boolean(courseId);

  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    const handleToast = (e) => {
      const { message, type = 'info' } = e.detail;
      const id = Date.now();
      setToasts((prev) => [...prev, { id, message, type }]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 3500);
    };
    window.addEventListener('blearn-toast', handleToast);
    return () => window.removeEventListener('blearn-toast', handleToast);
  }, []);

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-shell">
        <Topbar isCourseArea={isCourseArea} />
        <main className="page-frame">
          <Outlet />
        </main>
      </div>

      <div className="toast-container" aria-live="polite">
        {toasts.map((toast) => (
          <div key={toast.id} className={`toast ${toast.type}`}>
            {toast.type === 'success' && '🟢'}
            {toast.type === 'error' && '🔴'}
            {toast.type === 'info' && '📡'}
            <span>{toast.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
