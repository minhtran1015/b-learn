import { ArrowRight, CalendarDays, ClipboardList, MessageSquare, PlayCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import CourseCard from '../components/CourseCard.jsx';
import PageHeader from '../components/PageHeader.jsx';
import { courses, recentActivities } from '../data/mockData.js';

export default function CoursesPage() {
  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Không gian học tập"
        title="Khóa học của bạn"
        description="Chọn khóa học để xem tổng quan, tài liệu, bài tập, thảo luận và phân tích học tập riêng của khóa đó."
        action={<Link className="button primary" to="/courses/machine-learning/materials/m3"><PlayCircle size={19} />Tiếp tục học</Link>}
      />
      <section className="dashboard-grid">
        <div className="wide-panel">
          <div className="section-title">
            <h2>Danh sách khóa học</h2>
            <Link to="/courses/machine-learning">Mở khóa gần nhất <ArrowRight size={16} /></Link>
          </div>
          <div className="course-grid">
            {courses.map((course) => <CourseCard key={course.id} course={course} />)}
          </div>
        </div>

        <aside className="side-stack">
          <div className="card">
            <h3>Lối tắt nhanh</h3>
            <div className="shortcut-grid">
              <Link to="/courses/machine-learning/materials"><ClipboardList /> Tài liệu</Link>
              <Link to="/courses/machine-learning/assignments"><CalendarDays /> Bài tập</Link>
              <Link to="/courses/machine-learning/discussions"><MessageSquare /> Thảo luận</Link>
              <Link to="/courses/machine-learning/analytics"><PlayCircle /> Phân tích</Link>
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
