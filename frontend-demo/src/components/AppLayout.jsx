import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar.jsx';
import Topbar from './Topbar.jsx';

export default function AppLayout() {
  const location = useLocation();
  const courseMatch = location.pathname.match(/^\/courses\/([^/]+)/);
  const courseId = courseMatch?.[1];
  const isCourseArea = Boolean(courseId);

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-shell">
        <Topbar isCourseArea={isCourseArea} />
        <main className="page-frame">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
