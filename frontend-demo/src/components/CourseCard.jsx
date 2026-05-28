import { Link } from 'react-router-dom';

export default function CourseCard({ course }) {
  return (
    <article className="course-card">
      <div className={`course-cover ${course.color}`}>
        <span>{course.accent}</span>
        <strong>CẤP ĐỘ: {course.level}</strong>
      </div>
      <div className="course-body">
        <h3>{course.title}</h3>
        <p>GV: {course.teacher}</p>
        <div className="progress-row">
          <span>Tiến độ</span>
          <strong>{course.progress}%</strong>
        </div>
        <div className="progress-track">
          <span style={{ width: `${course.progress}%` }} />
        </div>
        <Link to={`/courses/${course.id}`} className="button outline full">
          Vào học
        </Link>
      </div>
    </article>
  );
}
