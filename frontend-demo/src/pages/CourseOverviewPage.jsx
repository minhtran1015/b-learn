import { BookOpen, CheckCircle2, ClipboardList, MessageSquare } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import PageHeader from '../components/PageHeader.jsx';
import { courses, materials, assignments } from '../data/mockData.js';

export default function CourseOverviewPage() {
  const { courseId } = useParams();
  const course = courses.find((item) => item.id === courseId) ?? courses[0];

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Không gian khóa học"
        title={course.title}
        description={course.description}
        action={<Link className="button primary" to={`/courses/${course.id}/materials`}>Vào tài liệu</Link>}
      />

      <section className="stats-grid">
        <div className="stat-card"><CheckCircle2 /><span>Tiến độ</span><strong>{course.progress}%</strong></div>
        <div className="stat-card"><BookOpen /><span>Tài liệu</span><strong>{materials.length}</strong></div>
        <div className="stat-card"><ClipboardList /><span>Bài tập</span><strong>{assignments.length}</strong></div>
      </section>

      <section className="two-column">
        <div className="card">
          <h2>Lộ trình tuần này</h2>
          <div className="timeline">
            {materials.map((item) => (
              <Link key={item.id} to={`/courses/${course.id}/materials/${item.id}`} className="timeline-item">
                <span />
                <div>
                  <strong>{item.title}</strong>
                  <small>{item.type} • {item.duration}</small>
                </div>
              </Link>
            ))}
          </div>
        </div>
        <div className="blue-panel">
          <MessageSquare />
          <h2>Cần hỗ trợ học thuật?</h2>
          <p>Đặt câu hỏi trực tiếp cho giảng viên hoặc mở chủ đề thảo luận trong khóa.</p>
          <Link to={`/courses/${course.id}/discussions`}>Tạo thảo luận mới</Link>
        </div>
      </section>
    </div>
  );
}
