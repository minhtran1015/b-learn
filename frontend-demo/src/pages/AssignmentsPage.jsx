import { CheckCircle2, Circle, Clock } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import PageHeader from '../components/PageHeader.jsx';
import { assignments } from '../data/mockData.js';

export default function AssignmentsPage() {
  const { courseId } = useParams();

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Khóa học / Bài tập"
        title="Bài tập thực hành"
        description="Hoàn thành các bài tập để củng cố kiến thức và mở khóa gợi ý học tập tiếp theo."
      />
      <div className="completion-banner">
        <span>Tiến độ hoàn thành</span>
        <div className="progress-track"><span style={{ width: '35%' }} /></div>
        <strong>5/14 bài tập</strong>
      </div>
      <section className="assignment-group">
        <h2>Chương 1: Cơ bản về Microservices</h2>
        {assignments.map((item) => (
          <Link key={item.id} to={`/courses/${courseId}/assignments/${item.id}`} className={`assignment-row ${item.status}`}>
            {item.status === 'done' ? <CheckCircle2 /> : <Circle />}
            <div>
              <h3>{item.title}</h3>
              <p>{item.summary}</p>
            </div>
            <span><Clock size={16} />{item.duration}</span>
            <small>{item.difficulty}</small>
          </Link>
        ))}
      </section>
    </div>
  );
}
