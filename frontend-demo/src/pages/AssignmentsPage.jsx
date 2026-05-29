import { CheckCircle2, Circle, Clock } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import PageHeader from '../components/PageHeader.jsx';
import { assignments as localAssignments } from '../data/mockData.js';
import { useState, useEffect } from 'react';

export default function AssignmentsPage() {
  const { courseId } = useParams();
  const [assignments, setAssignments] = useState(localAssignments);

  useEffect(() => {
    const submitted = JSON.parse(localStorage.getItem('blearn.submitted_assignments') || '[]');
    if (submitted.length > 0) {
      const updated = localAssignments.map(item => {
        if (submitted.includes(item.id)) {
          return { ...item, status: 'done' };
        }
        return item;
      });
      setAssignments(updated);
    }
  }, []);
  
  const doneCount = assignments.filter(a => a.status === 'done').length;
  const progressPercent = Math.round((doneCount / assignments.length) * 100);

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Khóa học / Bài tập"
        title="Bài tập thực hành"
        description="Hoàn thành các bài tập để củng cố kiến thức và mở khóa gợi ý học tập tiếp theo."
      />
      <div className="completion-banner">
        <span>Tiến độ hoàn thành</span>
        <div className="progress-track"><span style={{ width: `${progressPercent}%` }} /></div>
        <strong>{doneCount}/{assignments.length} bài tập</strong>
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
