import { ArrowLeft, ArrowRight, Timer } from 'lucide-react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthContext.jsx';
import { ensureGatewaySession } from '../api/gateway.js';

const questionsList = Array.from({ length: 20 }, (_, idx) => {
  const qNum = idx + 1;
  if (qNum === 1) {
    return {
      id: 1,
      question: "Trong phân tích độ phức tạp thuật toán, ký hiệu Big O thể hiện điều gì?",
      answers: [
        'Thời gian chạy trung bình của thuật toán trong điều kiện lý tưởng.',
        'Giới hạn trên của thời gian chạy hoặc không gian bộ nhớ mà thuật toán cần trong trường hợp xấu nhất.',
        'Giới hạn dưới tối thiểu mà thuật toán chắc chắn phải thực hiện.',
        'Số lượng dòng code thực tế sau khi biên dịch sang mã máy.',
      ],
      correctAnswerIdx: 1
    };
  }
  if (qNum === 2) {
    return {
      id: 2,
      question: "Ưu điểm chính của kiến trúc Microservices so với Monolithic là gì?",
      answers: [
        'Dễ dàng deploy và quản lý trong môi trường local.',
        'Khả năng mở rộng độc lập (Independent Scaling) và phân tách trách nhiệm rõ ràng.',
        'Hiệu năng gọi hàm nhanh hơn do không có độ trễ mạng.',
        'Cơ sở dữ liệu tập trung giúp truy vấn join dữ liệu dễ dàng.',
      ],
      correctAnswerIdx: 1
    };
  }
  if (qNum === 3) {
    return {
      id: 3,
      question: "Thuật toán đồng thuận (Consensus Algorithm) như Raft hay Paxos giải quyết bài toán gì?",
      answers: [
        'Mã hóa dữ liệu truyền tải trên đường truyền internet.',
        'Nén dữ liệu để truyền tải nhanh hơn.',
        'Đảm bảo tính nhất quán dữ liệu giữa các node trong hệ thống phân tán khi có sự cố mạng.',
        'Phân chia tải lượng request đều cho các web servers.',
      ],
      correctAnswerIdx: 2
    };
  }
  const topics = [
    {
      q: `Câu hỏi số ${qNum}: Trong mô hình truyền thông điệp bất đồng bộ (Asynchronous Messaging), thành phần Message Broker đóng vai trò gì?`,
      a: [
        'Xử lý trực tiếp database query cho client.',
        'Lưu giữ và phân phối tin nhắn giữa Producer và Consumer, giảm sự phụ thuộc trực tiếp giữa các service.',
        'Mã hóa thông tin giao dịch giữa các máy chủ.',
        'Là công cụ theo dõi log thời gian thực.'
      ],
      ans: 1
    },
    {
      q: `Câu hỏi số ${qNum}: Khái niệm "Eventual Consistency" (Nhất quán sau cùng) được hiểu như thế nào?`,
      a: [
        'Dữ liệu luôn nhất quán ở tất cả các node tại mọi thời điểm.',
        'Dữ liệu sẽ đạt trạng thái nhất quán trên toàn hệ thống sau một khoảng thời gian nhất định không có bản ghi mới.',
        'Dữ liệu không bao giờ đồng bộ để tăng tối đa tốc độ đọc ghi.',
        'Là cơ chế khóa database khi ghi ghi đè dữ liệu.'
      ],
      ans: 1
    },
    {
      q: `Câu hỏi số ${qNum}: Trong Spark, sự khác biệt chính giữa "Transformation" và "Action" là gì?`,
      a: [
        'Transformation trả về kết quả lập tức, Action lười biếng (lazy evaluation).',
        'Transformation tạo RDD mới và lười biếng, trong khi Action kích hoạt việc tính toán thực tế và trả về kết quả.',
        'Action chỉ chạy trên driver, Transformation chạy trên các worker.',
        'Không có sự khác biệt về bản chất.'
      ],
      ans: 1
    },
    {
      q: `Câu hỏi số ${qNum}: Cơ chế "Circuit Breaker" trong Microservices giúp ích gì cho hệ thống?`,
      a: [
        'Ngắt kết nối mạng của toàn bộ hệ thống để bảo mật.',
        'Ngăn chặn lỗi lan truyền (cascading failure) bằng cách dừng gọi service lỗi và trả về fallback nhanh chóng.',
        'Tăng tốc độ truy cập database của các service.',
        'Tự động khởi động lại container bị chết.'
      ],
      ans: 1
    }
  ];
  const selectedTopic = topics[idx % topics.length];
  return {
    id: qNum,
    question: selectedTopic.q,
    answers: selectedTopic.a,
    correctAnswerIdx: selectedTopic.ans
  };
});

export default function DoAssignmentPage() {
  const { courseId, assignmentId } = useParams();
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  const [studentHash, setStudentHash] = useState('');
  const [token, setToken] = useState('');
  
  // Quiz states
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answersState, setAnswersState] = useState(() => Array(questionsList.length).fill(null));
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [timeLeft, setTimeLeft] = useState(2700); // 45 minutes

  // Timer logic with safe cleanup
  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

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

  const handleSelectAnswer = (index) => {
    setAnswersState((prev) => {
      const next = [...prev];
      next[currentQuestion] = index;
      return next;
    });
  };

  const handleSubmit = async () => {
    // Check if at least one question is answered
    const answeredCount = answersState.filter((a) => a !== null).length;
    if (answeredCount === 0) {
      alert("Vui lòng chọn ít nhất một đáp án trước khi nộp bài!");
      return;
    }

    setIsSubmitting(true);
    try {
      // Calculate dynamic score based on correct answers
      let correctCount = 0;
      questionsList.forEach((q, idx) => {
        if (answersState[idx] === q.correctAnswerIdx) {
          correctCount += 1;
        }
      });
      const calculatedScore = Math.round((correctCount / questionsList.length) * 100);

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

      alert(`Nộp bài thành công! Điểm của bạn: ${calculatedScore}%. Warning: tỷ rủi ro bỏ học đã giảm xuống.`);
      navigate(`/courses/${courseId}/assignments`);
    } catch (err) {
      console.error("Lỗi nộp bài:", err);
      alert("Nộp bài thất bại. Vui lòng kiểm tra lại kết nối API Gateway.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Safe question boundary guard
  const activeQuiz = questionsList[currentQuestion] || questionsList[0];
  const progressPercent = Math.round((answersState.filter(a => a !== null).length / questionsList.length) * 100);

  return (
    <div className="exam-layout">
      <div className="exam-top card">
        <div>
          <span>Tiến độ làm bài</span>
          <div className="progress-track"><span style={{ width: `${progressPercent}%` }} /></div>
        </div>
        <strong>{answersState.filter(a => a !== null).length} / {questionsList.length} câu</strong>
        <div className="timer"><Timer />{formatTime(timeLeft)}</div>
      </div>
      <section className="question-card card">
        <span className="pill">Câu hỏi {currentQuestion + 1}</span>
        <h1>{activeQuiz.question}</h1>
        <div className="answer-list">
          {activeQuiz.answers.map((answer, index) => (
            <button 
              key={answer} 
              className={answersState[currentQuestion] === index ? 'selected' : ''}
              onClick={() => handleSelectAnswer(index)}
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
          {questionsList.map((q, index) => (
            <button 
              key={q.id} 
              className={`
                ${index === currentQuestion ? 'current' : ''}
                ${answersState[index] !== null ? 'done' : ''}
              `}
              onClick={() => setCurrentQuestion(index)}
            >
              {index + 1}
            </button>
          ))}
        </div>
      </aside>
      <div className="exam-actions card">
        <button 
          className="button outline"
          disabled={currentQuestion === 0}
          onClick={() => setCurrentQuestion(prev => prev - 1)}
        >
          <ArrowLeft /> Câu trước
        </button>
        <button 
          className="button outline danger" 
          onClick={handleSubmit} 
          disabled={isSubmitting}
        >
          {isSubmitting ? "Đang nộp..." : "Nộp bài"}
        </button>
        {currentQuestion < questionsList.length - 1 ? (
          <button 
            className="button primary"
            onClick={() => setCurrentQuestion(prev => prev + 1)}
          >
            Câu tiếp theo <ArrowRight size={18} />
          </button>
        ) : (
          <button 
            className="button primary"
            onClick={handleSubmit}
            disabled={isSubmitting}
          >
            Nộp bài <ArrowRight size={18} />
          </button>
        )}
      </div>
    </div>
  );
}
