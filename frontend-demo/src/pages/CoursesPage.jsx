import { ArrowRight, CalendarDays, ClipboardList, MessageSquare, PlayCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import CourseCard from '../components/CourseCard.jsx';
import PageHeader from '../components/PageHeader.jsx';
import { courses, recentActivities } from '../data/mockData.js';
import { getCourseProgressPercent } from '../utils/progress.js';

export default function CoursesPage() {
  const activeCourseId = localStorage.getItem('blearn.activeCourseId') || 'big-data-course';
  const courseCards = courses.map((course) => ({
    ...course,
    displayProgress: getCourseProgressPercent(course.id) ?? course.progress,
  }));

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Không gian học tập"
        title="Khóa học của bạn"
        description="Chọn khóa học để xem tổng quan, tài liệu, bài tập, thảo luận và phân tích học tập riêng của khóa đó."
        action={<Link className="button primary" to={`/courses/${activeCourseId}/materials`}><PlayCircle size={19} />Tiếp tục học</Link>}
      />
      <section className="dashboard-grid">
        <div className="wide-panel">
          <div className="section-title">
            <h2>Danh sách khóa học</h2>
            <Link to={`/courses/${activeCourseId}`}>Mở khóa gần nhất <ArrowRight size={16} /></Link>
          </div>
          <div className="course-grid">
            {courseCards.map((course) => <CourseCard key={course.id} course={course} />)}
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
