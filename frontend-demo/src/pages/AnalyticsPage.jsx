import { Clock3, Info, Trophy } from 'lucide-react';
import { useParams } from 'react-router-dom';
import PageHeader from '../components/PageHeader.jsx';
import { courses } from '../data/mockData.js';
import { useEffect, useState } from 'react';
import { useAuth } from '../auth/AuthContext.jsx';
import { ensureGatewaySession, gatewayUrl } from '../api/gateway.js';
import { mergeCompetencyProgress, readCompetencyProgress } from '../utils/progress.js';
import { customCourseAssignments, customCourseMaterials } from '../data/mockData.js';
import { resolveDemoLectureTitle } from '../data/ouladLectureTitleMap.js';

const CHAPTER_IDS = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6'];

function chapterLabel(chapterId) {
  return chapterId.replace('C', 'Chương ');
}

function mapCompetencyProgress(progress, mastery = {}) {
  const progressByChapter = progress && typeof progress === 'object' ? progress : {};
  const masteryByChapter = mastery && typeof mastery === 'object' ? mastery : {};

  return CHAPTER_IDS.map((chapterId) => {
    const item = progressByChapter[chapterId] || {};
    const hasSubmission = Number(item.submissions || 0) > 0;
    const masteryValue = Number(masteryByChapter[chapterId] ?? item.mastery ?? item.score ?? 0);
    const value = hasSubmission ? Math.max(0, Math.min(100, Math.round(masteryValue <= 1 ? masteryValue * 100 : masteryValue))) : 0;
    const scoreValue = hasSubmission ? Math.max(0, Math.min(100, Math.round(Number(item.score || 0)))) : 0;
    const submissions = Number(item.submissions || 0);
    return {
      label: chapterLabel(chapterId),
      value,
      scoreValue,
      submissions,
      correctCount: Number(item.correct_count || 0),
      questionCount: Number(item.question_count || 0),
    };
  });
}

function extractNumericId(text = '') {
  return String(text).match(/\d+/)?.[0] || '';
}

function findAssignmentTitleByOuladId(ouladId) {
  const assignment = customCourseAssignments.find((item) => String(item.id_site_mapping) === String(ouladId));
  return assignment?.title || (ouladId ? `Quiz học phần #${ouladId}` : 'Bài kiểm tra');
}

function findMaterialTitleByOuladId(ouladId) {
  const material = customCourseMaterials.find((item) => String(item.id_site_mapping) === String(ouladId));
  return material?.title || resolveDemoLectureTitle({ id_site: ouladId, id_site_mapping: ouladId }) || 'Học liệu';
}

function normalizeRecentSession(item) {
  const rawTitle = String(item?.title || '');
  const rawKind = item?.kind;
  const isAssessment = rawKind === 'assessment' || rawTitle.startsWith('Nộp bài');
  const isMaterial = rawKind === 'material' || rawTitle.startsWith('Hoạt động #') || rawTitle.startsWith('Xem tài liệu #') || rawTitle.startsWith('Xem tài liệu:');
  const ouladId = extractNumericId(rawTitle);

  if (isAssessment) {
    const hasReadableTitle = rawTitle.startsWith('Nộp bài:');
    return {
      ...item,
      kind: 'assessment',
      title: hasReadableTitle ? rawTitle : `Nộp bài: ${findAssignmentTitleByOuladId(ouladId)}`,
      score: Math.max(0, Math.min(100, Math.round(Number(item?.score || 0)))),
      time: Math.max(1, Math.round(Number(item?.time || 1))),
    };
  }

  if (isMaterial) {
    const hasReadableTitle = rawTitle.startsWith('Xem tài liệu:');
    return {
      ...item,
      kind: 'material',
      title: hasReadableTitle ? rawTitle : `Xem tài liệu: ${findMaterialTitleByOuladId(ouladId)}`,
      score: null,
      time: Math.max(1, Math.round(Number(item?.time || 1))),
    };
  }

  return {
    ...item,
    time: Math.max(1, Math.round(Number(item?.time || 1))),
  };
}

export default function AnalyticsPage() {
  const { courseId } = useParams();
  const course = courses.find((item) => item.id === courseId) ?? courses[0];
  const { currentUser, token: contextToken, currentStudentHash: contextHash } = useAuth();
  
  const [dropoutProbability, setDropoutProbability] = useState(null);
  const [radarScores, setRadarScores] = useState([]);
  const [bktMastery, setBktMastery] = useState({});
  const [activityLevels, setActivityLevels] = useState([]);
  const [recentSessions, setRecentSessions] = useState([]);
  const [activitySummary, setActivitySummary] = useState({
    weekly_minutes: 0,
    click_count: 0,
    submission_count: 0,
  });
  const [dataSource, setDataSource] = useState({
    mode: 'unknown',
    event_log_count: 0,
    features_cached: false,
    bkt_cached: false,
    risk_cached: false,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState('');

  useEffect(() => {
    // 🔴 KHÓA CHẶT TẠI ĐÂY: Ép trạng thái loading đồng bộ lập tức khi đổi định danh
    setIsLoading(true);
    setDropoutProbability(null); // Reset trị cũ để không bị lọt dữ liệu vòng chạy trước
    setLoadError('');
    setRadarScores([]);

    async function loadStats() {
      let token = null;
      let studentHash = null;
      try {
        const session = await ensureGatewaySession(currentUser);
        token = session.token;
        studentHash = session.studentHash;
      } catch (err) {
        console.error("Failed to ensure gateway session:", err);
      }

      const currentStudentHash = studentHash || contextHash;
      const finalToken = token || contextToken;

      // CHẶN TUYỆT ĐỐI TẠI ĐÂY: Nếu chưa có thông tin Auth, GIỮ NGUYÊN isLoading = true và thoát hàm an toàn
      if (!currentStudentHash || !finalToken) {
        return;
      }

      try {
        const response = await fetch(gatewayUrl(`/recommendations/${currentStudentHash}`), {
          method: 'GET',
          headers: {
            Authorization: `Bearer ${finalToken}`,
          },
        });

        if (!response.ok) {
          const detail = await response.text();
          throw new Error(`Failed to fetch recommendations (${response.status}): ${detail || 'Unknown error'}`);
        }

        const payload = await response.json();
        if (payload.dropout_probability !== undefined) {
          setDropoutProbability(payload.dropout_probability);
        }
        const mergedProgress = mergeCompetencyProgress(payload.competency_progress || {});
        const liveBktMastery = payload.bkt_mastery || {};
        setBktMastery(liveBktMastery);
        setRadarScores(mapCompetencyProgress(mergedProgress, liveBktMastery));
        if (Array.isArray(payload.activity_levels)) {
          setActivityLevels(payload.activity_levels);
        }
        if (Array.isArray(payload.recent_sessions)) {
          setRecentSessions(payload.recent_sessions.map(normalizeRecentSession));
        }
        if (payload.activity_summary) {
          setActivitySummary({
            weekly_minutes: Number(payload.activity_summary.weekly_minutes || 0),
            click_count: Number(payload.activity_summary.click_count || 0),
            submission_count: Number(payload.activity_summary.submission_count || 0),
          });
        }
        if (payload.data_source) {
          setDataSource({
            mode: payload.data_source.mode || 'unknown',
            event_log_count: Number(payload.data_source.event_log_count || 0),
            features_cached: Boolean(payload.data_source.features_cached),
            bkt_cached: Boolean(payload.data_source.bkt_cached),
            risk_cached: Boolean(payload.data_source.risk_cached),
          });
        }
      } catch (err) {
        console.error("Failed to load prediction stats:", err);
        setRadarScores(mapCompetencyProgress(readCompetencyProgress(), bktMastery));
        setLoadError(err?.message || 'Không tải được dữ liệu phân tích.');
      } finally {
        setIsLoading(false);
      }
    }
    if (currentUser) {
      loadStats();
    } else {
      setLoadError('Vui lòng đăng nhập để xem dữ liệu phân tích học tập.');
      setIsLoading(false);
    }
  }, [currentUser, contextToken, contextHash]);

  const passRate = dropoutProbability !== null ? (1 - dropoutProbability) * 100 : null;

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow={course.title}
        title="Phân tích học tập"
        description="Báo cáo năng lực, hành vi học tập và dự báo hoàn thành trong khóa học này."
      />
      <section className="analytics-grid">
        <div className="card radar-card">
          <h2>Mức độ thành thạo & Tiến trình năng lực <Info size={18} /></h2>
          {isLoading ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '250px', fontSize: '14px', opacity: 0.8 }}>
              Đang cập nhật phân tích học tập...
            </div>
          ) : (
            radarScores.length > 0 ? (
              <div className="radar-container progress-only">
                <div className="progress-bars-list">
                  {radarScores.map((score) => (
                    <div key={score.label} className="progress-bar-item">
                      <div className="progress-row">
                        <span>
                          {score.label}
                          {score.submissions > 0 && score.questionCount > 0
                            ? <small>Mức thành thạo {score.value}% • Điểm bài làm {score.scoreValue}% • {score.correctCount}/{score.questionCount} câu đúng</small>
                            : <small>Chưa có bài nộp</small>}
                        </span>
                        <strong className={score.value > 50 ? 'is-strong' : 'is-low'}>
                          {score.submissions > 0 ? `${score.value}%` : '--'}
                        </strong>
                      </div>
                      <div className="progress-track">
                        <span
                          className={score.submissions > 0 && score.value > 50 ? 'is-strong' : 'is-low'}
                          style={{ width: `${score.value}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '250px', fontSize: '14px', opacity: 0.8, textAlign: 'center' }}>
                {loadError ? `Không tải được dữ liệu phân tích. ${loadError}` : 'Chưa có dữ liệu phân tích.'}
              </div>
            )
          )}
        </div>
        <div className="card heatmap-card">
          <div className="card-heading">
            <div>
              <h2>Tần suất hoạt động</h2>
              <p>Tổng thời gian tuần này: {(activitySummary.weekly_minutes / 60).toFixed(1)} giờ</p>
            </div>
            <span>{dataSource.mode === 'live_event_log' ? 'Dữ liệu mới nhất' : 'Dữ liệu mẫu'}</span>
          </div>
          <div className="heatmap">
            {activityLevels.length > 0
              ? activityLevels.map((level, index) => <span key={index} className={`level-${level}`} />)
              : <span className="level-1" style={{ gridColumn: '1 / -1', width: '100%', height: '56px', display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: 0.6 }}>Chưa có tín hiệu hoạt động</span>
            }
          </div>
          <div style={{ marginTop: '8px', fontSize: '12px', color: '#64748b' }}>
            Nguồn dữ liệu: <strong>{dataSource.mode === 'live_event_log' ? 'hoạt động gần đây' : 'dữ liệu mẫu'}</strong> • Lượt ghi nhận: <strong>{dataSource.event_log_count}</strong>
          </div>
          <div className="heatmap-footer">
            <small>Ít</small>
            {[1, 2, 3, 4, 5].map((level) => <span key={level} className={`level-${level}`} />)}
            <small>Nhiều</small>
          </div>
        </div>
        <div className="stat-wide"><Clock3 /><span>Thời gian học tuần này</span><strong>{activitySummary.weekly_minutes} phút</strong><small>{activitySummary.click_count} lượt học được ghi nhận</small></div>
        <div className="stat-wide"><Trophy /><span>Số bài nộp gần đây</span><strong>{activitySummary.submission_count} bài</strong><small>Dựa trên hoạt động gần đây</small></div>
        <div className="card prediction-card">
          <h2>Dự đoán nguy cơ bỏ học & Kết quả</h2>
          {isLoading || dropoutProbability === null ? (
            <p style={{ opacity: 0.8, fontSize: '14px' }}>
              {loadError || 'Đang cập nhật dự báo học tập...'}
            </p>
          ) : (
            <>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', margin: '12px 0' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{
                    padding: '4px 10px',
                    borderRadius: '12px',
                    fontSize: '13px',
                    fontWeight: 'bold',
                    color: '#fff',
                    backgroundColor: dropoutProbability > 0.5 ? '#ff4757' : '#2ed573'
                  }}>
                    {dropoutProbability > 0.5 ? '🔴 Nguy cơ bỏ học cao' : '🟢 An toàn / Rủi ro thấp'}
                  </span>
                  <span style={{ fontSize: '14px', color: '#666' }}>Xác suất:</span>
                  <strong style={{ fontSize: '18px' }}>{(dropoutProbability * 100).toFixed(1)}%</strong>
                </div>
              </div>
              <p style={{ fontSize: '14px', lineHeight: '1.4' }}>
                {dropoutProbability > 0.5
                  ? 'Cảnh báo: Tần suất hoạt động và kết quả học tập của bạn đang có dấu hiệu đi xuống. Hãy tập trung làm thêm bài tập và xem lại các bài giảng khuyên dùng.'
                  : 'Hệ thống dự báo bạn đang ở vùng an toàn và có khả năng cao hoàn thành xuất sắc khóa học này.'}
              </p>
            </>
          )}
        </div>
        <div className="card session-table">
          <h2>Chi tiết phiên học gần đây</h2>
          {recentSessions.length > 0 ? recentSessions.map((item, index) => (
            <div key={`${item.title}-${index}`} className="table-row">
              <span>{item.title}</span>
              <strong>{item.kind === 'material' || item.score === null || item.score === undefined ? 'Xem tài liệu' : `${item.score}%`}</strong>
              <small>{item.time} phút</small>
            </div>
          )) : (
            <div className="table-row">
              <span>Chưa có phiên học nào</span>
              <strong>--</strong>
              <small>0 phút</small>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
