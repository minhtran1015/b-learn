import { ArrowLeft, ArrowRight, Timer } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';

const answers = [
  'Thời gian chạy trung bình của thuật toán trong điều kiện lý tưởng.',
  'Giới hạn trên của thời gian chạy hoặc không gian bộ nhớ mà thuật toán cần trong trường hợp xấu nhất.',
  'Giới hạn dưới tối thiểu mà thuật toán chắc chắn phải thực hiện.',
  'Số lượng dòng code thực tế sau khi biên dịch sang mã máy.',
];

export default function DoAssignmentPage() {
  const { courseId, assignmentId } = useParams();

  return (
    <div className="exam-layout">
      <div className="exam-top card">
        <div>
          <span>Tiến độ làm bài</span>
          <div className="progress-track"><span style={{ width: '30%' }} /></div>
        </div>
        <strong>12 / 40 câu</strong>
        <div className="timer"><Timer />44:57</div>
      </div>
      <section className="question-card card">
        <span className="pill">Câu hỏi 13</span>
        <h1>Trong phân tích độ phức tạp thuật toán, ký hiệu Big O thể hiện điều gì?</h1>
        <div className="answer-list">
          {answers.map((answer, index) => (
            <button key={answer} className={index === 1 ? 'selected' : ''}>
              <span>{String.fromCharCode(65 + index)}</span>
              {answer}
            </button>
          ))}
        </div>
      </section>
      <aside className="question-map card">
        <h2>Danh sách câu hỏi</h2>
        <div className="question-grid">
          {Array.from({ length: 20 }, (_, index) => <button key={index} className={index < 12 ? 'done' : index === 12 ? 'current' : ''}>{index + 1}</button>)}
        </div>
      </aside>
      <div className="exam-actions card">
        <Link to={`/courses/${courseId}/assignments/${assignmentId}`}><ArrowLeft /> Câu trước</Link>
        <button className="button outline danger">Nộp bài</button>
        <button className="button primary">Câu tiếp theo <ArrowRight size={18} /></button>
      </div>
    </div>
  );
}
