import { ArrowLeft, ArrowRight, Timer } from 'lucide-react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthContext.jsx';
import { ensureGatewaySession } from '../api/gateway.js';

const answers = [
  'Thời gian chạy trung bình của thuật toán trong điều kiện lý tưởng.',
  'Giới hạn trên của thời gian chạy hoặc không gian bộ nhớ mà thuật toán cần trong trường hợp xấu nhất.',
  'Giới hạn dưới tối thiểu mà thuật toán chắc chắn phải thực hiện.',
  'Số lượng dòng code thực tế sau khi biên dịch sang mã máy.',
];

export default function DoAssignmentPage() {
  const { courseId, assignmentId } = useParams();
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  const [studentHash, setStudentHash] = useState('');
  const [token, setToken] = useState('');
  const [selectedIdx, setSelectedIdx] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    async function initSession() {
      try {
        const session = await ensureGatewaySession(currentUser);
        setStudentHash(session.studentHash);
        setToken(session.token);
      } catch (err) {
        console.error('Session init error:', err);
      }
    }
    initSession();
  }, [currentUser]);

  const handleSubmit = async () => {
    if (selectedIdx === null) {
      alert("Vui lòng chọn một đáp án trước khi nộp bài!");
      return;
    }
    setIsSubmitting(true);
    try {
      const calculatedScore = selectedIdx === 1 ? 100 : 50;

      const rawBaseUrl = import.meta.env.VITE_GATEWAY_URL || 'http://localhost:8000';
      const API_BASE_URL = rawBaseUrl.replace(/\/$/, '');

      const response = await fetch(`${API_BASE_URL}/submit-assessment`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          student_id_hash: studentHash,
          assignment_id: assignmentId,
          score: calculatedScore
        })
      });

      if (!response.ok) {
        throw new Error(`Submission failed with status ${response.status}`);
      }

      // Save submitted assignment state locally
      const submitted = JSON.parse(localStorage.getItem('blearn.submitted_assignments') || '[]');
      if (!submitted.includes(assignmentId)) {
        submitted.push(assignmentId);
        localStorage.setItem('blearn.submitted_assignments', JSON.stringify(submitted));
      }

      alert(`Nộp bài thành công! Điểm của bạn: ${calculatedScore}%. Rủi ro bỏ học đã giảm xuống.`);
      navigate(`/courses/${courseId}/assignments`);
    } catch (err) {
      console.error("Lỗi nộp bài:", err);
      alert("Nộp bài thất bại. Vui lòng kiểm tra lại kết nối API Gateway.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="exam-layout">
      <div className="exam-top card">
        <div>
          <span>Tiến độ làm bài</span>
          <div className="progress-track"><span style={{ width: '65%' }} /></div>
        </div>
        <strong>13 / 20 câu</strong>
        <div className="timer"><Timer />44:57</div>
      </div>
      <section className="question-card card">
        <span className="pill">Câu hỏi 13</span>
        <h1>Trong phân tích độ phức tạp thuật toán, ký hiệu Big O thể hiện điều gì?</h1>
        <div className="answer-list">
          {answers.map((answer, index) => (
            <button 
              key={answer} 
              className={selectedIdx === index ? 'selected' : ''}
              onClick={() => setSelectedIdx(index)}
            >
              <span>{String.fromCharCode(65 + index)}</span>
              {answer}
            </button>
          ))}
        </div>
      </section>
      <aside className="question-map card">
        <h2>Danh sách câu hỏi</h2>
        <div className="question-grid">
          {Array.from({ length: 20 }, (_, index) => (
            <button 
              key={index} 
              className={
                index < 12 
                  ? 'done' 
                  : index === 12 
                    ? 'current' 
                    : selectedIdx !== null && index === 12 
                      ? 'done' 
                      : ''
              }
            >
              {index + 1}
            </button>
          ))}
        </div>
      </aside>
      <div className="exam-actions card">
        <Link to={`/courses/${courseId}/assignments/${assignmentId}`}><ArrowLeft /> Câu trước</Link>
        <button 
          className="button outline danger" 
          onClick={handleSubmit} 
          disabled={isSubmitting}
        >
          {isSubmitting ? "Đang nộp..." : "Nộp bài"}
        </button>
        <button className="button primary">Câu tiếp theo <ArrowRight size={18} /></button>
      </div>
    </div>
  );
}
