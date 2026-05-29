import { Clock3, Info, Trophy } from 'lucide-react';
import { useParams } from 'react-router-dom';
import PageHeader from '../components/PageHeader.jsx';
import { courses } from '../data/mockData.js';
import { useEffect, useState } from 'react';
import { useAuth } from '../auth/AuthContext.jsx';
import { ensureGatewaySession, fetchRecommendations } from '../api/gateway.js';

const skillScores = [
  { label: 'Chương 1', value: 86 },
  { label: 'Chương 2', value: 72 },
  { label: 'Chương 3', value: 91 },
  { label: 'Chương 4', value: 64 },
  { label: 'Chương 5', value: 78 },
  { label: 'Chương 6', value: 69 },
];

const activityLevels = Array.from({ length: 26 * 7 }, (_, index) => {
  const week = Math.floor(index / 7);
  const day = index % 7;
  return ((week * 2 + day * 3 + (week % 4 === 0 ? 2 : 0)) % 5) + 1;
});

const recentSessions = [
  { title: 'Tư duy hệ thống Level 4', score: 88, time: 22 },
  { title: 'Tiếng Anh thương mại', score: 45, time: 15 },
  { title: 'Phân tích dữ liệu cơ bản', score: 92, time: 45 },
  { title: 'Thiết kế kiến trúc dữ liệu', score: 76, time: 30 },
];

function RadarChart({ scores }) {
  const center = 150;
  const maxRadius = 104;
  const angleStep = (Math.PI * 2) / scores.length;
  const pointFor = (index, radius) => {
    const angle = angleStep * index - Math.PI / 2;
    return {
      x: center + Math.cos(angle) * radius,
      y: center + Math.sin(angle) * radius,
    };
  };
  const polygon = scores
    .map((score, index) => {
      const point = pointFor(index, maxRadius * (score.value / 100));
      return `${point.x},${point.y}`;
    })
    .join(' ');

  return (
    <div className="radar-chart">
      <svg viewBox="0 0 300 300" role="img" aria-label="Biểu đồ mạng nhện mức độ thành thạo theo 6 chương">
        {[0.25, 0.5, 0.75, 1].map((ratio) => (
          <polygon
            key={ratio}
            points={scores.map((_, index) => {
              const point = pointFor(index, maxRadius * ratio);
              return `${point.x},${point.y}`;
            }).join(' ')}
            className="radar-ring"
          />
        ))}
        {scores.map((_, index) => {
          const edge = pointFor(index, maxRadius);
          return <line key={index} x1={center} y1={center} x2={edge.x} y2={edge.y} className="radar-axis" />;
        })}
        <polygon points={polygon} className="radar-area" />
        {scores.map((score, index) => {
          const point = pointFor(index, maxRadius * (score.value / 100));
          return <circle key={score.label} cx={point.x} cy={point.y} r="4.5" className="radar-point" />;
        })}
      </svg>
      <div className="radar-legend">
        {scores.map((score) => (
          <span key={score.label}>
            <strong>{score.value}%</strong>
            {score.label}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function AnalyticsPage() {
  const { courseId } = useParams();
  const course = courses.find((item) => item.id === courseId) ?? courses[0];
  const { currentUser, token: contextToken, currentStudentHash: contextHash } = useAuth();
  const [loading, setLoading] = useState(true);
  const [performanceData, setPerformanceData] = useState(null);

  useEffect(() => {
    async function loadStats() {
      try {
        setLoading(true);
        const { token, studentHash } = await ensureGatewaySession(currentUser);
        const currentStudentHash = studentHash || contextHash;
        const finalToken = token || contextToken;

        if (!currentStudentHash) return;

        const rawBaseUrl = import.meta.env.VITE_GATEWAY_URL || 'http://localhost:8000';
        const API_BASE_URL = rawBaseUrl.replace(/\/$/, '');

        const response = await fetch(`${API_BASE_URL}/recommendations/${currentStudentHash}`, {
          method: 'GET',
          headers: {
            Authorization: `Bearer ${finalToken}`,
          },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch recommendations: ${response.status}`);
        }

        const apiResponse = await response.json();
        setPerformanceData(apiResponse);
      } catch (err) {
        console.error("Failed to load prediction stats:", err);
      } finally {
        setLoading(false);
      }
    }
    if (currentUser) {
      loadStats();
    }
  }, [currentUser, contextToken, contextHash]);

  const apiResponse = performanceData || {};
  const keyMap = {
    C1: 'Chương 1',
    C2: 'Chương 2',
    C3: 'Chương 3',
    C4: 'Chương 4',
    C5: 'Chương 5',
    C6: 'Chương 6',
  };
  const dynamicSkillScores = Object.entries(apiResponse.bkt_mastery || {}).map(([key, val]) => ({
    label: keyMap[key] || key,
    value: Math.round(val * 100) // Chuyển xác suất thập phân sang phần trăm %
  }));

  const scores = dynamicSkillScores.length > 0 ? dynamicSkillScores : [
    { label: 'Chương 1', value: 86 },
    { label: 'Chương 2', value: 72 },
    { label: 'Chương 3', value: 91 },
    { label: 'Chương 4', value: 64 },
    { label: 'Chương 5', value: 78 },
    { label: 'Chương 6', value: 69 },
  ];

  const dropoutProb = apiResponse.dropout_probability !== undefined ? apiResponse.dropout_probability : 0.15;
  const passRate = (1 - dropoutProb) * 100;

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow={course.title}
        title="Phân tích học tập"
        description="Báo cáo năng lực, hành vi học tập và dự báo hoàn thành trong khóa học này."
      />
      <section className="analytics-grid">
        <div className="card radar-card">
          <h2>Mức độ thành thạo <Info size={18} /></h2>
          <RadarChart scores={scores} />
        </div>
        <div className="card heatmap-card">
          <div className="card-heading">
            <div>
              <h2>Tần suất hoạt động</h2>
              <p>Tổng thời gian tuần này: 12.5 giờ</p>
            </div>
            <span>6 tháng gần nhất</span>
          </div>
          <div className="heatmap">
            {activityLevels.map((level, index) => <span key={index} className={`level-${level}`} />)}
          </div>
          <div className="heatmap-footer">
            <small>Ít</small>
            {[1, 2, 3, 4, 5].map((level) => <span key={level} className={`level-${level}`} />)}
            <small>Nhiều</small>
          </div>
        </div>
        <div className="stat-wide"><Clock3 /><span>Thời gian học trung bình</span><strong>45 phút</strong><small>+12% so với tuần trước</small></div>
        <div className="stat-wide"><Trophy /><span>Số bài kiểm tra đã xong</span><strong>128 bài</strong><small>Top 5% học viên</small></div>
        <div className="card prediction-card">
          <h2>Dự đoán khả năng trượt/đỗ</h2>
          <div className="pass-box">Đỗ {passRate.toFixed(0)}%</div>
          <p>Dựa trên hiệu suất học tập 30 ngày qua, hệ thống dự báo bạn có khả năng cao hoàn thành khóa học xuất sắc.</p>
        </div>
        <div className="card session-table">
          <h2>Chi tiết phiên học gần đây</h2>
          {recentSessions.map((item) => (
            <div key={item.title} className="table-row">
              <span>{item.title}</span>
              <strong>{item.score}%</strong>
              <small>{item.time} phút</small>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
