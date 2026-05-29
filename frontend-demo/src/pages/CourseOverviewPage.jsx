import { BookOpen, CheckCircle2, ClipboardList, MessageSquare, Sparkles } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import PageHeader from '../components/PageHeader.jsx';
import { courses, materials, assignments } from '../data/mockData.js';
import { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthContext.jsx';
import { ensureGatewaySession, fetchRecommendations, trackStudentClick } from '../api/gateway.js';

export default function CourseOverviewPage() {
  const { courseId } = useParams();
  const course = courses.find((item) => item.id === courseId) ?? courses[0];
  const { currentUser } = useAuth();
  const [recommendations, setRecommendations] = useState([]);
  const [studentHash, setStudentHash] = useState('');
  const [isRecsLoading, setIsRecsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    async function loadRecommendations() {
      try {
        setIsRecsLoading(true);
        const { studentHash: sHash } = await ensureGatewaySession(currentUser);
        if (isMounted) {
          setStudentHash(sHash);
        }
        const payload = await fetchRecommendations(sHash);
        const recList = Array.isArray(payload?.recommendations) ? payload.recommendations : [];
        // Lấy 3 tài liệu có score cao nhất (Top-3)
        const top3 = [...recList].sort((a, b) => (b.score || 0) - (a.score || 0)).slice(0, 3);
        if (isMounted) {
          setRecommendations(top3);
        }
      } catch (err) {
        console.error("Failed to load recommendations in dashboard:", err);
      } finally {
        if (isMounted) {
          setIsRecsLoading(false);
        }
      }
    }

    if (currentUser) {
      loadRecommendations();
    }
    return () => {
      isMounted = false;
    };
  }, [currentUser]);

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
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className="card recommendation-panel">
            <div className="panel-header" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
              <Sparkles style={{ color: '#3b82f6' }} size={24} />
              <h2 style={{ margin: 0 }}>Gợi ý học tập dành riêng cho bạn hôm nay</h2>
            </div>
            {isRecsLoading ? (
              <p style={{ opacity: 0.8, fontSize: '14px' }}>Đang tính toán Live Inference từ mô hình AI...</p>
            ) : recommendations.length > 0 ? (
              <div className="rec-list" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {recommendations.map((item) => (
                  <Link
                    key={item.id}
                    to={`/courses/${course.id}/materials/${item.id}`}
                    className="timeline-item-rec"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '12px',
                      borderRadius: '8px',
                      background: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid rgba(255, 255, 255, 0.08)',
                      textDecoration: 'none',
                      color: 'inherit',
                      transition: 'all 0.2s ease',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.transform = 'translateY(-2px)';
                      e.currentTarget.style.borderColor = '#3b82f6';
                      e.currentTarget.style.background = 'rgba(255, 255, 255, 0.06)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.transform = 'none';
                      e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)';
                      e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)';
                    }}
                    onClick={async () => {
                      const rawId = item.id_site_mapping || item.id_site || item.id;
                      const cleanedSiteId = String(rawId).replace(/\D/g, '');
                      await trackStudentClick(studentHash, cleanedSiteId);
                    }}
                  >
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', maxWidth: '80%' }}>
                      <strong style={{ fontSize: '14px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{item.title}</strong>
                      <small style={{ opacity: 0.7, fontSize: '12px' }}>{item.type} • {item.duration}</small>
                    </div>
                    <span
                      style={{
                        fontSize: '12px',
                        fontWeight: 'bold',
                        color: '#10b981',
                        background: 'rgba(16, 185, 129, 0.1)',
                        padding: '4px 8px',
                        borderRadius: '12px',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      Match: {Math.round((item.score || 0) * 100)}%
                    </span>
                  </Link>
                ))}
              </div>
            ) : (
              <p style={{ opacity: 0.6, fontSize: '14px' }}>Không có gợi ý nào phù hợp.</p>
            )}
          </div>

          <div className="blue-panel" style={{ margin: 0 }}>
            <MessageSquare />
            <h2>Cần hỗ trợ học thuật?</h2>
            <p>Đặt câu hỏi trực tiếp cho giảng viên hoặc mở chủ đề thảo luận trong khóa.</p>
            <Link to={`/courses/${course.id}/discussions`}>Tạo thảo luận mới</Link>
          </div>
        </div>
      </section>
    </div>
  );
}
