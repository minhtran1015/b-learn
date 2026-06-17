import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar.jsx';
import Topbar from './Topbar.jsx';
import { useEffect, useRef, useState } from 'react';

export default function AppLayout() {
  const location = useLocation();
  const courseMatch = location.pathname.match(/^\/courses\/([^/]+)/);
  const courseId = courseMatch?.[1];
  const isCourseArea = Boolean(courseId);

  const [toast, setToast] = useState(null);
  const toastTimerRef = useRef(null);

  useEffect(() => {
    const handleToast = (e) => {
      const { message, type = 'info' } = e.detail;
      setToast({ message, type });

      if (toastTimerRef.current) {
        clearTimeout(toastTimerRef.current);
      }

      toastTimerRef.current = setTimeout(() => {
        setToast(null);
        toastTimerRef.current = null;
      }, 3500);
    };

    window.addEventListener('blearn-toast', handleToast);
    return () => {
      window.removeEventListener('blearn-toast', handleToast);
      if (toastTimerRef.current) {
        clearTimeout(toastTimerRef.current);
      }
    };
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
        {toast && (
          <div className={`toast ${toast.type}`}>
            {toast.type === 'success' && '🟢'}
            {toast.type === 'error' && '🔴'}
            {toast.type === 'info' && '📡'}
            <span>{toast.message}</span>
          </div>
        )}
      </div>
    </div>
  );
}
