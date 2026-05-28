import { ArrowRight, CheckCircle2, Clock, HelpCircle, Target } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import PageHeader from '../components/PageHeader.jsx';
import { assignments } from '../data/mockData.js';

export default function AssignmentDetailPage() {
  const { courseId, assignmentId } = useParams();
  const assignment = assignments.find((item) => item.id === assignmentId) ?? assignments[2];

  return (
    <div className="assignment-detail-grid">
      <section className="page-stack">
        <PageHeader
          eyebrow="Khóa học / Chi tiết bài tập"
          title={assignment.title}
          description="Áp dụng kiến thức đã học vào một tình huống mô phỏng, tập trung vào cách suy luận và cấu trúc giải pháp."
        />
        <div className="card accent-card">
          <h2>Mô tả bài tập</h2>
          <p>Trong bài tập thực hành này, bạn sẽ được cung cấp một kiến trúc microservices đơn giản gồm Order Service, Payment Service và Inventory Service. Nhiệm vụ là thiết kế luồng phối hợp giao dịch ổn định khi có lỗi mạng.</p>
          <p>Hãy đề xuất cơ chế rollback, timeout và cách quan sát hệ thống để đảm bảo dữ liệu nhất quán.</p>
        </div>
        <div className="card">
          <h2><Target size={24} /> Mục tiêu học tập</h2>
          <ul className="check-list boxed">
            <li>Hiểu và áp dụng nguyên lý ACID trong bối cảnh phân tán.</li>
            <li>Triển khai ý tưởng Two-Phase Commit bằng sơ đồ luồng.</li>
            <li>Xác định tình huống lỗi mạng và cách xử lý node failure.</li>
          </ul>
        </div>
      </section>
      <aside className="assignment-aside">
        <div className="metric-mini"><Clock /><span>Thời gian</span><strong>60 phút</strong></div>
        <div className="metric-mini"><HelpCircle /><span>Số lượng</span><strong>25 câu hỏi</strong></div>
        <div className="passing-score">Passing Score <strong>80%</strong></div>
        <Link className="button primary full" to={`/courses/${courseId}/assignments/${assignment.id}/do`}>Bắt đầu làm bài <ArrowRight size={20} /></Link>
      </aside>
    </div>
  );
}
