import { CheckCircle2, Circle, Clock } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import PageHeader from '../components/PageHeader.jsx';
import { assignments as localAssignments, customCourseAssignments } from '../data/mockData.js';
import { useState, useEffect } from 'react';
import { PASSING_SCORE, readCompetencyProgress } from '../utils/progress.js';

const CUSTOM_COURSE_ID = 'big-data-course';

export default function AssignmentsPage() {
  const { courseId } = useParams();
  const isCustomCourse = courseId === CUSTOM_COURSE_ID;

  const baseAssignments = isCustomCourse ? customCourseAssignments : localAssignments;
  const [assignments, setAssignments] = useState(baseAssignments);

  useEffect(() => {
    const submitted = JSON.parse(localStorage.getItem('blearn.submitted_assignments') || '[]');
    const competencyProgress = readCompetencyProgress();
    const updated = baseAssignments.map(item => {
      const score = Number(competencyProgress[item.chapterId]?.score || 0);
      if (isCustomCourse && score >= PASSING_SCORE) {
        return { ...item, status: 'done' };
      }
      if (!isCustomCourse && submitted.includes(item.id)) {
        return { ...item, status: 'done' };
      }
      return item;
    });
    setAssignments(updated);
  }, [courseId, isCustomCourse, baseAssignments]);
  
  const doneCount = assignments.filter(a => a.status === 'done').length;
  const progressPercent = Math.round((doneCount / assignments.length) * 100);

  // Nhóm bài tập theo chapter
  const chapters = [...new Set(assignments.map(a => a.chapter))];

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow={isCustomCourse ? 'Big Data / Bài tập' : 'Khóa học / Bài tập'}
        title={isCustomCourse ? 'Bài tập Big Data' : 'Bài tập thực hành'}
        description={
          isCustomCourse
            ? 'Các bài kiểm tra theo từng chương. Kết quả được dùng để cập nhật tiến độ, mức thành thạo và phân tích học tập.'
            : 'Hoàn thành các bài tập để củng cố kiến thức và mở khóa gợi ý học tập tiếp theo.'
        }
      />
      <div className="completion-banner">
        <span>Tiến độ hoàn thành</span>
        <div className="progress-track"><span style={{ width: `${progressPercent}%` }} /></div>
        <strong>{doneCount}/{assignments.length} bài tập</strong>
      </div>
      {chapters.map(chapter => (
        <section key={chapter} className="assignment-group">
          <h2>{chapter}</h2>
          {assignments.filter(a => a.chapter === chapter).map((item) => (
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
      ))}
    </div>
  );
}
