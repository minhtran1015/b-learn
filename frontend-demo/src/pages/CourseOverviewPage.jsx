import { BookOpen, CheckCircle2, ClipboardList, MessageSquare, Sparkles } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import PageHeader from '../components/PageHeader.jsx';
import { courses, materials, assignments, customCourseMaterials, customCourseAssignments } from '../data/mockData.js';
import { resolveDemoLectureTitle } from '../data/ouladLectureTitleMap.js';
import { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthContext.jsx';
import { ensureGatewaySession, fetchRecommendations, trackStudentClick } from '../api/gateway.js';
import { getCourseProgressPercent } from '../utils/progress.js';

const CUSTOM_COURSE_ID = 'big-data-course';

function formatMatchScore(item) {
  const raw = item?.match_percent ?? item?.score ?? 0;
  const percent = Number(raw) <= 1 ? Math.round(Number(raw || 0) * 100) : Math.round(Number(raw || 0));
  return Math.max(0, Math.min(100, percent));
}

export default function CourseOverviewPage() {
  const { courseId } = useParams();
  const course = courses.find((item) => item.id === courseId) ?? courses[0];
  const isCustomCourse = courseId === CUSTOM_COURSE_ID;
  const courseMaterials = isCustomCourse ? customCourseMaterials : materials;
  const courseAssignments = isCustomCourse ? customCourseAssignments : assignments;
  const { currentUser } = useAuth();
  const [recommendations, setRecommendations] = useState([]);
  const [studentHash, setStudentHash] = useState('');
  const [isRecsLoading, setIsRecsLoading] = useState(true);
  const [courseProgress, setCourseProgress] = useState(() => getCourseProgressPercent(courseId) ?? course.progress);

  async function refreshRecommendations(sHash, shouldUpdateLoading = true) {
    try {
      if (shouldUpdateLoading) {
        setIsRecsLoading(true);
      }
      const payload = await fetchRecommendations(sHash);
      const recList = Array.isArray(payload?.recommendations) ? payload.recommendations : [];
      const top3 = [...recList].sort((a, b) => {
        const right = Number(b.rank_score ?? b.score ?? 0);
        const left = Number(a.rank_score ?? a.score ?? 0);
        return right - left;
      }).slice(0, 3);
      setRecommendations(top3);
      return top3;
    } finally {
      if (shouldUpdateLoading) {
        setIsRecsLoading(false);
      }
    }
  }

  useEffect(() => {
    let isMounted = true;
    async function loadRecommendations() {
      try {
        const { studentHash: sHash } = await ensureGatewaySession(currentUser);
        if (isMounted) {
          setStudentHash(sHash);
        }
        await refreshRecommendations(sHash, true);
      } catch (err) {
        console.error("Failed to load recommendations in dashboard:", err);
      }
    }

    if (currentUser) {
      loadRecommendations();
    }
    return () => {
      isMounted = false;
    };
  }, [currentUser]);

  useEffect(() => {
    const updateProgress = () => setCourseProgress(getCourseProgressPercent(courseId) ?? course.progress);
    updateProgress();
    window.addEventListener('blearn-progress-updated', updateProgress);
    window.addEventListener('storage', updateProgress);
    return () => {
      window.removeEventListener('blearn-progress-updated', updateProgress);
      window.removeEventListener('storage', updateProgress);
    };
  }, [courseId, course.progress]);

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Không gian khóa học"
        title={course.title}
        description={course.description}
        action={<Link className="button primary" to={`/courses/${course.id}/materials`}>Vào tài liệu</Link>}
      />

      <section className="stats-grid">
        <div className="stat-card"><CheckCircle2 /><span>Tiến độ</span><strong>{courseProgress}%</strong></div>
        <div className="stat-card"><BookOpen /><span>Tài liệu</span><strong>{courseMaterials.length}</strong></div>
        <div className="stat-card"><ClipboardList /><span>Bài tập</span><strong>{courseAssignments.length}</strong></div>
      </section>

      <section className="two-column">
        <div className="card">
          <h2>Lộ trình tuần này</h2>
          <div className="timeline">
            {courseMaterials.slice(0, 3).map((item) => (
              <Link key={item.id} to={`/courses/${course.id}/materials/${item.id}`} className="timeline-item">
                <span />
                <div>
                  <strong>{resolveDemoLectureTitle(item)}</strong>
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
              <p style={{ opacity: 0.8, fontSize: '14px' }}>Đang cập nhật gợi ý học tập...</p>
            ) : recommendations.length > 0 ? (
              <div className="rec-list" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {recommendations.map((item) => {
                  const displayTitle = resolveDemoLectureTitle(item);
                  return (
                    <Link
                      key={item.id}
                      to={`/courses/${course.id}/materials/${item.id}`}
                      className="timeline-item-rec"
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        gap: '12px',
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
                        await trackStudentClick(studentHash, cleanedSiteId, { ...item, title: displayTitle });
                        await refreshRecommendations(studentHash, false);
                      }}
                    >
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: '1 1 auto', minWidth: 0 }}>
                        <strong style={{ fontSize: '14px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{displayTitle}</strong>
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
                          flex: '0 0 auto',
                        }}
                      >
                        Match: {formatMatchScore(item)}%
                      </span>
                    </Link>
                  );
                })}
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
