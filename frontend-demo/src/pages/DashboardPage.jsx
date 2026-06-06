import { ArrowRight, CalendarDays, ClipboardList, MessageSquare, PlayCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import CourseCard from '../components/CourseCard.jsx';
import PageHeader from '../components/PageHeader.jsx';
import { courses, recentActivities } from '../data/mockData.js';

export default function DashboardPage() {
  const activeCourseId = localStorage.getItem('blearn.activeCourseId') || 'machine-learning';

  return (
    <div className="page-stack">
      <PageHeader
        title="Chào buổi sáng, Quân!"
        description="Hôm nay là một ngày tốt để chinh phục thêm một mốc kiến thức mới."
        action={<Link className="button primary" to={`/courses/${activeCourseId}/materials`}><PlayCircle size={19} />Tiếp tục học</Link>}
      />

      <section className="dashboard-grid">
        <div className="wide-panel">
          <div className="section-title">
            <h2>Khóa học của bạn</h2>
            <Link to="/courses">Xem tất cả <ArrowRight size={16} /></Link>
          </div>
          <div className="course-grid">
            {courses.map((course) => <CourseCard key={course.id} course={course} />)}
          </div>
        </div>

        <aside className="side-stack">
          <div className="card">
            <h3>Lối tắt nhanh</h3>
            <div className="shortcut-grid">
              <Link to={`/courses/${activeCourseId}/materials`}><ClipboardList /> Tài liệu</Link>
              <Link to={`/courses/${activeCourseId}/assignments`}><CalendarDays /> Bài tập</Link>
              <Link to={`/courses/${activeCourseId}/discussions`}><MessageSquare /> Thảo luận</Link>
              <Link to={`/courses/${activeCourseId}/analytics`}><PlayCircle /> Phân tích</Link>
            </div>
          </div>
          <div className="card">
            <h3>Hoạt động gần đây</h3>
            <ul className="activity-list">
              {recentActivities.map((item) => <li key={item}>{item}<small>2 giờ trước</small></li>)}
            </ul>
          </div>
        </aside>
      </section>
    </div>
  );
}
