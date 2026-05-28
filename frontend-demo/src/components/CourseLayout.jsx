import { BarChart3, BookOpen, ClipboardList, Compass, MessageSquare } from 'lucide-react';
import { Navigate, NavLink, Outlet, useParams } from 'react-router-dom';
import { courses } from '../data/mockData.js';

const courseItems = [
  { suffix: '', label: 'Tổng quan', icon: Compass },
  { suffix: '/analytics', label: 'Phân tích học tập', icon: BarChart3 },
  { suffix: '/materials', label: 'Tài liệu', icon: BookOpen },
  { suffix: '/assignments', label: 'Bài tập', icon: ClipboardList },
  { suffix: '/discussions', label: 'Thảo luận', icon: MessageSquare },
];

export default function CourseLayout() {
  const { courseId } = useParams();
  const course = courses.find((item) => item.id === courseId);

  if (!course) {
    return <Navigate to="/courses" replace />;
  }

  return (
    <div className="course-workspace">
      <aside className="course-sidebar" aria-label="Điều hướng trong khóa học">
        <div className={`course-sidebar-head ${course.color}`}>
          <small>Không gian khóa học</small>
          <strong>{course.title}</strong>
          <span>{course.teacher}</span>
          <div className="progress-track">
            <span style={{ width: `${course.progress}%` }} />
          </div>
          <em>{course.progress}% hoàn thành</em>
        </div>

        <nav className="course-nav-list">
          {courseItems.map((item) => (
            <NavLink
              key={item.suffix}
              to={`/courses/${course.id}${item.suffix}`}
              end={item.suffix === ''}
              className="course-nav-item"
            >
              <item.icon size={19} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>

      <section className="course-content">
        <Outlet />
      </section>
    </div>
  );
}
