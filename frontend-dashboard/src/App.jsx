import React, { useState, useEffect, useRef } from 'react';
import {
  BookOpen,
  GraduationCap,
  Users,
  AlertTriangle,
  CheckCircle,
  Clock,
  Search,
  Settings,
  RefreshCw,
  Send,
  Terminal,
  Database,
  Activity,
  ArrowRight,
  ExternalLink,
  Info
} from 'lucide-react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  AreaChart,
  Area,
  Legend
} from 'recharts';
import './App.css';

// --- MOCK DATA FALLBACKS ---
const MOCK_STUDENTS = [
  "000bdcdddb354ddafe53c4c4a31644af87963a3d05d5506844a7ff4bbb3d4c5e",
  "00185e2df67d8cd5d5df7265147817f8a7e08d5506844a7ff4bbb3d4c5ef3da1",
  "0029b4dd354ddafe53c4c4a31644af87963a3d05d5506844a7ff4bbb3d4c5e31c",
  "0039fcd45a4ddafe53c4c4a31644af87963a3d05d5506844a7ff4bbb3d4c5e88e",
  "0048af984bc8bcf5d5df7265147817f8a7e08d5506844a7ff4bbb3d4c5ef3da7",
  "0053a8df984bc8bcf5d5df7265147817f8a7e08d5506844a7ff4bbb3d4c5e92ef"
];

const MOCK_COHORT_STATS = [
  { metric_name: "gender", category: "Nam (M)", count: 13500 },
  { metric_name: "gender", category: "Nữ (F)", count: 11666 },
  
  { metric_name: "highest_education", category: "Dưới A Level", count: 8023 },
  { metric_name: "highest_education", category: "A Level hoặc Tương đương", count: 12532 },
  { metric_name: "highest_education", category: "Đại học / Cao đẳng", count: 3951 },
  { metric_name: "highest_education", category: "Sau Đại học", count: 660 },

  { metric_name: "region", category: "London Region", count: 4520 },
  { metric_name: "region", category: "West Midlands", count: 3840 },
  { metric_name: "region", category: "East Anglian", count: 3510 },
  { metric_name: "region", category: "South Region", count: 3120 },
  { metric_name: "region", category: "North Western Region", count: 2840 },
  { metric_name: "region", category: "South West Region", count: 2530 },
  { metric_name: "region", category: "Yorkshire Region", count: 2410 },
  { metric_name: "region", category: "East Midlands Region", count: 2396 },

  { metric_name: "engagement_weekly", category: "1", value: 12.4 },
  { metric_name: "engagement_weekly", category: "2", value: 15.6 },
  { metric_name: "engagement_weekly", category: "3", value: 18.2 },
  { metric_name: "engagement_weekly", category: "4", value: 14.8 },
  { metric_name: "engagement_weekly", category: "5", value: 22.3 },
  { metric_name: "engagement_weekly", category: "6", value: 26.5 },
  { metric_name: "engagement_weekly", category: "7", value: 24.1 },
  { metric_name: "engagement_weekly", category: "8", value: 21.0 },
  { metric_name: "engagement_weekly", category: "9", value: 25.4 },
  { metric_name: "engagement_weekly", category: "10", value: 28.9 }
];

const MOCK_STUDENT_PROFILE = {
  "000bdcdddb354ddafe53c4c4a31644af87963a3d05d5506844a7ff4bbb3d4c5e": {
    risk: {
      student_id_hash: "000bdcdddb354ddafe53c4c4a31644af87963a3d05d5506844a7ff4bbb3d4c5e",
      dropout_probability: 0.145,
      dropout_risk_level: "Low Risk",
      total_clicks: 342,
      final_result: "Pass"
    },
    bkt_mastery: [
      { skill_name: "lexical_resource", mastery_probability: 0.42, correct_count: 8, total_attempts: 15 },
      { skill_name: "grammatical_range", mastery_probability: 0.68, correct_count: 12, total_attempts: 16 },
      { skill_name: "cohesion_coherence", mastery_probability: 0.81, correct_count: 14, total_attempts: 15 },
      { skill_name: "task_achievement", mastery_probability: 0.55, correct_count: 9, total_attempts: 14 }
    ],
    recommendations: [
      { id_site: "542847", activity_type: "resource", activity_name: "Bài giảng từ vựng Academic English", recommendation_score: 0.942 },
      { id_site: "542851", activity_type: "oucontent", activity_name: "Bài tập Ngữ pháp Nâng cao", recommendation_score: 0.875 },
      { id_site: "542910", activity_type: "url", activity_name: "Tài liệu đọc tham khảo thêm", recommendation_score: 0.793 },
      { id_site: "542805", activity_type: "forumng", activity_name: "Diễn đàn trao đổi học thuật", recommendation_score: 0.688 },
      { id_site: "542999", activity_type: "quiz", activity_name: "Trắc nghiệm tự đánh giá tuần 4", recommendation_score: 0.512 }
    ]
  },
  "00185e2df67d8cd5d5df7265147817f8a7e08d5506844a7ff4bbb3d4c5ef3da1": {
    risk: {
      student_id_hash: "00185e2df67d8cd5d5df7265147817f8a7e08d5506844a7ff4bbb3d4c5ef3da1",
      dropout_probability: 0.742,
      dropout_risk_level: "High Risk",
      total_clicks: 89,
      final_result: "Fail"
    },
    bkt_mastery: [
      { skill_name: "lexical_resource", mastery_probability: 0.21, correct_count: 2, total_attempts: 10 },
      { skill_name: "grammatical_range", mastery_probability: 0.35, correct_count: 4, total_attempts: 12 },
      { skill_name: "cohesion_coherence", mastery_probability: 0.45, correct_count: 5, total_attempts: 11 },
      { skill_name: "task_achievement", mastery_probability: 0.18, correct_count: 1, total_attempts: 8 }
    ],
    recommendations: [
      { id_site: "542847", activity_type: "resource", activity_name: "Bài giảng từ vựng Academic English", recommendation_score: 0.985 },
      { id_site: "542805", activity_type: "forumng", activity_name: "Diễn đàn trao đổi học thuật", recommendation_score: 0.812 },
      { id_site: "542901", activity_type: "oucontent", activity_name: "Tài liệu ôn tập ngữ pháp căn bản", recommendation_score: 0.764 },
      { id_site: "542910", activity_type: "url", activity_name: "Tài liệu đọc tham khảo thêm", recommendation_score: 0.612 },
      { id_site: "542999", activity_type: "quiz", activity_name: "Trắc nghiệm tự đánh giá tuần 4", recommendation_score: 0.452 }
    ]
  }
};

const DEFAULT_PROFILE = {
  risk: { student_id_hash: "Unknown", dropout_probability: 0.50, dropout_risk_level: "Medium Risk", total_clicks: 150, final_result: "Pass" },
  bkt_mastery: [
    { skill_name: "lexical_resource", mastery_probability: 0.50, correct_count: 5, total_attempts: 10 },
    { skill_name: "grammatical_range", mastery_probability: 0.50, correct_count: 5, total_attempts: 10 }
  ],
  recommendations: [
    { id_site: "542847", activity_type: "resource", activity_name: "Tài liệu gợi ý tổng quan", recommendation_score: 0.80 }
  ]
};

// Colors for charts
const COLORS_GENDER = ['#6366f1', '#ec4899'];
const COLORS_THEME = ['#6366f1', '#8b5cf6', '#ec4899', '#3b82f6', '#10b981', '#f59e0b', '#ef4444'];

function App() {
  // --- APP STATE ---
  const [activeTab, setActiveTab] = useState('cohort');
  const [apiBaseUrl, setApiBaseUrl] = useState('http://20.195.55.162'); // Default to deployed AKS API
  const [isLiveMode, setIsLiveMode] = useState(false); // Controlled by health check
  const [showConfig, setShowConfig] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  
  // Data State
  const [studentsList, setStudentsList] = useState([]);
  const [selectedStudent, setSelectedStudent] = useState('');
  const [studentSearch, setStudentSearch] = useState('');
  const [cohortStats, setCohortStats] = useState([]);
  const [studentProfile, setStudentProfile] = useState(null);
  
  // Simulation Console Logs
  const [consoleLogs, setConsoleLogs] = useState([]);
  const consoleBottomRef = useRef(null);

  // --- LOG WRITER FOR SIMULATOR ---
  const writeLog = (message, type = 'system') => {
    const timestamp = new Date().toLocaleTimeString();
    setConsoleLogs(prev => [...prev, { timestamp, message, type }]);
  };

  // --- HEALTH CHECK / CONNECT TO API ---
  const checkApiConnection = async (targetUrl = apiBaseUrl, silent = false) => {
    if (!silent) setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetch(`${targetUrl}/health`, { signal: AbortSignal.timeout(3000) });
      if (res.ok) {
        setIsLiveMode(true);
        if (!silent) writeLog(`🔌 Kết nối thành công đến API Serving: ${targetUrl}`, 'response');
        return true;
      }
    } catch (e) {
      // Fallback
    }
    setIsLiveMode(false);
    if (!silent) {
      writeLog(`⚠️ Không thể kết nối tới API Serving: ${targetUrl}. Đã tự động chuyển sang chế độ Mô Phỏng Cục Bộ (Offline Simulator)`, 'error');
    }
    setIsLoading(false);
    return false;
  };

  // --- FETCH DATA ---
  const loadData = async (targetUrl = apiBaseUrl) => {
    setIsLoading(true);
    setErrorMsg(null);
    
    // 1. Check health first
    const isOnline = await checkApiConnection(targetUrl, true);
    
    if (isOnline) {
      try {
        // Fetch Cohort Stats
        const cohortRes = await fetch(`${targetUrl}/api/v1/cohort/stats`);
        const cohortData = await cohortRes.json();
        setCohortStats(cohortData);
        
        // Fetch Students List
        const studentsRes = await fetch(`${targetUrl}/api/v1/students`);
        const studentsData = await studentsRes.json();
        const students = studentsData.students || [];
        setStudentsList(students);
        
        if (students.length > 0) {
          const firstStudent = students[0];
          setSelectedStudent(firstStudent);
          await loadStudentProfile(firstStudent, targetUrl);
        }
        
        writeLog("📊 Đã nạp thành công dữ liệu từ Gold Layer qua REST API.", "response");
      } catch (err) {
        setIsLiveMode(false);
        setErrorMsg(`Lỗi khi gọi API: ${err.message}. Đang chạy chế độ giả lập.`);
        loadMockData();
      }
    } else {
      loadMockData();
    }
    setIsLoading(false);
  };

  const loadMockData = () => {
    setCohortStats(MOCK_COHORT_STATS);
    setStudentsList(MOCK_STUDENTS);
    setSelectedStudent(MOCK_STUDENTS[0]);
    
    // Set first profile
    const profile = MOCK_STUDENT_PROFILE[MOCK_STUDENTS[0]] || DEFAULT_PROFILE;
    setStudentProfile(profile);
    writeLog("💡 Đang chạy chế độ Giả lập Offline. Dữ liệu tĩnh cục bộ đã được kích hoạt.", "system");
  };

  const loadStudentProfile = async (studentId, targetUrl = apiBaseUrl) => {
    if (!studentId) return;
    
    if (isLiveMode) {
      try {
        // Fetch Profile (Risk and pyBKT)
        const profileRes = await fetch(`${targetUrl}/api/v1/student/${studentId}`);
        const profileData = await profileRes.json();
        
        // Fetch Recommendations
        const recsRes = await fetch(`${targetUrl}/api/v1/student/${studentId}/recommendations`);
        const recsData = await recsRes.json();
        
        setStudentProfile({
          risk: profileData.risk,
          bkt_mastery: profileData.bkt_mastery,
          recommendations: recsData.recommendations
        });
        
        writeLog(`📥 Đã nạp Hồ sơ học viên & Gợi ý LightGCN cho student: ${studentId.substring(0, 8)}...`, "system");
      } catch (err) {
        writeLog(`❌ Lỗi khi tải hồ sơ học viên từ API: ${err.message}. Sử dụng dữ liệu giả lập.`, "error");
        // Fallback
        const fallbackProfile = MOCK_STUDENT_PROFILE[studentId] || MOCK_STUDENT_PROFILE[MOCK_STUDENTS[0]] || DEFAULT_PROFILE;
        setStudentProfile(fallbackProfile);
      }
    } else {
      const profile = MOCK_STUDENT_PROFILE[studentId] || MOCK_STUDENT_PROFILE[MOCK_STUDENTS[0]] || DEFAULT_PROFILE;
      setStudentProfile(profile);
    }
  };

  // --- INITIAL LOAD ---
  useEffect(() => {
    loadData();
    writeLog("🚀 Khởi tạo B-LEARN Frontend Dashboard. Sẵn sàng tích hợp.");
  }, []);

  // Auto-scroll logs to bottom
  useEffect(() => {
    if (consoleBottomRef.current) {
      consoleBottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [consoleLogs]);

  // --- INTERACTION SIMULATION (TAB 3) ---
  const handleSimulateStudy = async (item) => {
    if (!selectedStudent || !studentProfile) return;
    
    writeLog(`\n[TƯƠNG TÁC] 👤 Học sinh #${studentsList.indexOf(selectedStudent) + 1} click vào tài liệu: "${item.activity_name || `LMS Site ID ${item.id_site}`}"`, "request");
    
    if (isLiveMode) {
      const startTime = performance.now();
      writeLog(`📤 Gửi POST /api/v1/student/${selectedStudent}/interaction với body: { id_site: "${item.id_site}", activity_type: "${item.activity_type}" }`, "request");
      
      try {
        const res = await fetch(`${apiBaseUrl}/api/v1/student/${selectedStudent}/interaction`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            id_site: String(item.id_site),
            activity_type: item.activity_type
          })
        });
        
        if (res.ok) {
          const data = await res.json();
          const latency = (performance.now() - startTime).toFixed(0);
          
          writeLog(`⚡ [FastAPI Backend] Tải nhúng người dùng -> dịch chuyển vector u = u + 0.3 * i_item -> dot product với tất cả items. Hoàn tất trong ${latency}ms`, "response");
          
          // Map mock names to returned IDs for neat rendering
          const updatedRecs = data.recommendations.map(rec => {
            // Try to find matching metadata in mock resources
            const matchedMock = Object.values(MOCK_STUDENT_PROFILE)
              .flatMap(p => p.recommendations)
              .find(m => String(m.id_site) === String(rec.id_site));
            return {
              ...rec,
              activity_name: matchedMock ? matchedMock.activity_name : `Tài liệu môn học (Site ${rec.id_site})`
            };
          });
          
          setStudentProfile(prev => ({
            ...prev,
            recommendations: updatedRecs
          }));
          
          writeLog(`📥 Nhận phản hồi thành công (HTTP 200). Đã cập nhật 5 gợi ý học tập mới thích ứng.`, "response");
        } else {
          throw new Error(`Server returned ${res.status}`);
        }
      } catch (err) {
        writeLog(`❌ Gọi POST API lỗi: ${err.message}. Giả lập thuật toán dịch chuyển vector cục bộ...`, "error");
        simulateOfflineShift(item);
      }
    } else {
      simulateOfflineShift(item);
    }
  };

  const simulateOfflineShift = (item) => {
    // Simulate offline embedding shift logic (NumPy mock)
    writeLog("🔮 [Giả lập cục bộ] Tính toán ma trận nhúng: Dịch chuyển vector học viên tiến gần 30% tới Item Vector.", "system");
    
    // Scramble the mock recommendations to show visible change
    const currentRecs = [...studentProfile.recommendations];
    const clickedItemIndex = currentRecs.findIndex(r => r.id_site === item.id_site);
    
    // Shift elements: move the clicked one out or change scores
    const shiftedRecs = currentRecs.map(rec => {
      let scoreChange = (Math.random() - 0.3) * 0.1; // Random perturbation
      if (rec.id_site === item.id_site) scoreChange = -0.15; // De-prioritize already studied
      return {
        ...rec,
        recommendation_score: Math.min(0.99, Math.max(0.1, rec.recommendation_score + scoreChange))
      };
    }).sort((a, b) => b.recommendation_score - a.recommendation_score);
    
    // Replace the lowest one with a new resource to show adaptation
    if (shiftedRecs.length > 0) {
      const mockPool = [
        { id_site: "542711", activity_type: "quiz", activity_name: "Trắc nghiệm ngữ pháp nhanh", recommendation_score: 0.88 },
        { id_site: "542990", activity_type: "oucontent", activity_name: "Đọc hiểu: Essay Structure Guide", recommendation_score: 0.85 },
        { id_site: "542112", activity_type: "url", activity_name: "Từ điển học thuật Oxford trực tuyến", recommendation_score: 0.82 }
      ];
      
      const unrecommended = mockPool.filter(p => !shiftedRecs.some(r => r.id_site === p.id_site));
      if (unrecommended.length > 0) {
        shiftedRecs[shiftedRecs.length - 1] = {
          ...unrecommended[0],
          recommendation_score: shiftedRecs[0].recommendation_score - 0.05
        };
      }
    }
    
    setStudentProfile(prev => ({
      ...prev,
      recommendations: shiftedRecs.sort((a, b) => b.recommendation_score - a.recommendation_score)
    }));
    
    writeLog("🎉 Đề xuất thích ứng đã được cập nhật thành công (Offline Mode).", "response");
  };

  // --- DATA PARSING FOR CHARTS ---
  const genderData = cohortStats
    .filter(item => item.metric_name === 'gender')
    .map(item => ({ name: item.category, value: item.count }));
    
  const eduData = cohortStats
    .filter(item => item.metric_name === 'highest_education')
    .map(item => ({ name: item.category, sinhvien: item.count }));

  const regionData = cohortStats
    .filter(item => item.metric_name === 'region')
    .sort((a, b) => b.count - a.count)
    .slice(0, 6)
    .map(item => ({ name: item.category, value: item.count }));

  const trendData = cohortStats
    .filter(item => item.metric_name === 'engagement_weekly')
    .map(item => ({ name: `Tuần ${item.category}`, clicks: parseFloat(item.value || 0).toFixed(1) }));

  // --- STUDENT EXPLORER SEARCH ---
  const filteredStudents = studentsList.filter(s => 
    s.toLowerCase().includes(studentSearch.toLowerCase())
  );

  return (
    <div className="dashboard-container">
      {/* ─── HEADER BAR ─── */}
      <header className="header-bar glass-panel animate-fade">
        <div className="brand-section">
          <GraduationCap className="logo-icon" />
          <div>
            <h1 className="brand-title text-gradient">B-LEARN Portal</h1>
            <p className="brand-subtitle">Hệ thống phân tích dữ liệu lớn EdTech</p>
          </div>
        </div>
        
        <div className="tabs-navigation">
          <button 
            className={`tab-button ${activeTab === 'cohort' ? 'active' : ''}`}
            onClick={() => setActiveTab('cohort')}
          >
            <Users size={16} />
            Thống Kê Cohort
          </button>
          <button 
            className={`tab-button ${activeTab === 'student' ? 'active' : ''}`}
            onClick={() => setActiveTab('student')}
          >
            <Activity size={16} />
            Học Viên Chi Tiết
          </button>
          <button 
            className={`tab-button ${activeTab === 'simulator' ? 'active' : ''}`}
            onClick={() => setActiveTab('simulator')}
          >
            <Terminal size={16} />
            Giả Lập LMS
          </button>
        </div>

        <div className="config-section">
          <div 
            className={`config-badge ${isLiveMode ? 'live' : 'simulated'}`}
            onClick={() => setShowConfig(!showConfig)}
          >
            <Database size={14} />
            <span>{isLiveMode ? 'Live API (AKS)' : 'Mock Mode (Local)'}</span>
            <Settings size={14} style={{ marginLeft: 4 }} />
          </div>
        </div>
      </header>

      {/* ─── SETTINGS DRAWER ─── */}
      {showConfig && (
        <section className="config-drawer glass-panel glow-purple animate-fade">
          <div className="config-input-group">
            <label htmlFor="api-url-input" className="kpi-label" style={{ minWidth: 100 }}>FastAPI Endpoint:</label>
            <input 
              id="api-url-input"
              type="text" 
              className="config-input" 
              value={apiBaseUrl} 
              onChange={(e) => setApiBaseUrl(e.target.value)} 
              placeholder="http://20.x.x.x"
            />
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button 
              className="config-button" 
              onClick={() => {
                checkApiConnection(apiBaseUrl);
                loadData(apiBaseUrl);
              }}
              disabled={isLoading}
            >
              {isLoading ? 'Đang kết nối...' : 'Kết nối & Tải lại'}
            </button>
            <button 
              className="config-button" 
              style={{ background: 'rgba(0,0,0,0.05)', color: 'var(--text-main)', border: '1px solid var(--panel-border)' }}
              onClick={() => {
                setIsLiveMode(false);
                loadMockData();
              }}
            >
              Chạy giả lập
            </button>
          </div>
        </section>
      )}

      {/* ─── ERROR STATE ─── */}
      {errorMsg && (
        <div className="error-card animate-fade">
          <p className="error-title">Cảnh báo hệ thống</p>
          <p className="error-desc">{errorMsg}</p>
        </div>
      )}

      {/* ─── LOADING COVER ─── */}
      {isLoading && studentsList.length === 0 ? (
        <div className="loading-wrapper glass-panel animate-fade">
          <div className="spinner"></div>
          <p style={{ fontSize: 14, color: 'var(--text-muted)' }}>Đang kết nối hạ tầng Big Data...</p>
        </div>
      ) : (
        <main className="animate-fade">
          {/* ════════ TAB 1: COHORT ANALYTICS ════════ */}
          {activeTab === 'cohort' && (
            <div>
              {/* KPI Section */}
              <div className="kpi-grid">
                <div className="kpi-card glass-panel glow-purple">
                  <div className="kpi-icon-wrapper purple">
                    <Users size={24} />
                  </div>
                  <div className="kpi-info">
                    <span className="kpi-label">Tổng học viên quản lý</span>
                    <span className="kpi-value">{isLiveMode ? '25,166' : '1,200'}</span>
                    <span className="kpi-desc">Dữ liệu từ tầng Gold (OULAD)</span>
                  </div>
                </div>

                <div className="kpi-card glass-panel glow-green">
                  <div className="kpi-icon-wrapper green">
                    <CheckCircle size={24} />
                  </div>
                  <div className="kpi-info">
                    <span className="kpi-label">Tỷ lệ rủi ro bình quân</span>
                    <span className="kpi-value">18.5%</span>
                    <span className="kpi-desc">Dự đoán bởi mô hình LightGBM</span>
                  </div>
                </div>

                <div className="kpi-card glass-panel glow-green" style={{ borderLeft: '4px solid var(--danger)' }}>
                  <div className="kpi-icon-wrapper red">
                    <AlertTriangle size={24} />
                  </div>
                  <div className="kpi-info">
                    <span className="kpi-label">Kỹ năng yếu nhất</span>
                    <span className="kpi-value" style={{ fontSize: 18, fontWeight: 700, marginTop: 10 }}>lexical_resource</span>
                    <span className="kpi-desc">Độ thành thục trung bình: 38.2%</span>
                  </div>
                </div>
              </div>

              {/* Charts Sections */}
              <div className="charts-grid">
                {/* Weekly Click Timelines */}
                <div className="chart-card glass-panel">
                  <h3 className="chart-title">
                    <Activity size={18} color="var(--primary)" />
                    Xu hướng Tương tác Clicks Hàng Tuần (Engagement Baseline)
                  </h3>
                  <div className="chart-container-inner">
                    <ResponsiveContainer width="100%" height={260}>
                      <AreaChart data={trendData}>
                        <defs>
                          <linearGradient id="colorClicks" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.4}/>
                            <stop offset="95%" stopColor="var(--primary)" stopOpacity={0.01}/>
                          </linearGradient>
                        </defs>
                        <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={11} />
                        <YAxis stroke="var(--text-muted)" fontSize={11} />
                        <Tooltip />
                        <Area type="monotone" dataKey="clicks" stroke="var(--primary)" strokeWidth={2} fillOpacity={1} fill="url(#colorClicks)" name="Số lượt Clicks TB" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Highest Education */}
                <div className="chart-card glass-panel">
                  <h3 className="chart-title">
                    <GraduationCap size={18} color="#8b5cf6" />
                    Trình độ học vấn cao nhất (Education Levels)
                  </h3>
                  <div className="chart-container-inner">
                    <ResponsiveContainer width="100%" height={260}>
                      <BarChart data={eduData}>
                        <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={9} interval={0} />
                        <YAxis stroke="var(--text-muted)" fontSize={11} />
                        <Tooltip />
                        <Bar dataKey="sinhvien" fill="#8b5cf6" radius={[4, 4, 0, 0]} name="Số lượng SV">
                          {eduData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS_THEME[index % COLORS_THEME.length]} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Gender Ring */}
                <div className="chart-card glass-panel">
                  <h3 className="chart-title">
                    <Users size={18} color="#ec4899" />
                    Phân bố Giới tính (Gender Balance)
                  </h3>
                  <div className="chart-container-inner">
                    <ResponsiveContainer width="100%" height={240}>
                      <PieChart>
                        <Pie
                          data={genderData}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={80}
                          paddingAngle={5}
                          dataKey="value"
                        >
                          {genderData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS_GENDER[index % COLORS_GENDER.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                        <Legend verticalAlign="bottom" height={36} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Top Regions */}
                <div className="chart-card glass-panel">
                  <h3 className="chart-title">
                    <Info size={18} color="#06b6d4" />
                    Phân bố Địa lý Học viên (Top 6 Regions)
                  </h3>
                  <div className="chart-container-inner">
                    <ResponsiveContainer width="100%" height={260}>
                      <BarChart data={regionData} layout="vertical" margin={{ left: 20 }}>
                        <XAxis type="number" stroke="var(--text-muted)" fontSize={11} />
                        <YAxis dataKey="name" type="category" stroke="var(--text-muted)" fontSize={10} width={80} />
                        <Tooltip />
                        <Bar dataKey="value" fill="#06b6d4" radius={[0, 4, 4, 0]} name="Số học viên" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ════════ TAB 2: STUDENT DEEP-DIVE ════════ */}
          {activeTab === 'student' && (
            <div className="student-explorer">
              {/* Sidebar student select */}
              <aside className="student-sidebar glass-panel">
                <span className="sidebar-title">Danh sách học viên</span>
                <div className="student-selector-group">
                  <div style={{ position: 'relative' }}>
                    <input 
                      type="text" 
                      className="config-input" 
                      style={{ width: '100%', paddingLeft: 30 }}
                      placeholder="Tìm mã hash học viên..."
                      value={studentSearch}
                      onChange={(e) => setStudentSearch(e.target.value)}
                    />
                    <Search size={14} style={{ position: 'absolute', left: 10, top: 12, color: 'var(--text-muted)' }} />
                  </div>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                    Tìm thấy: {filteredStudents.length} / {studentsList.length}
                  </span>
                </div>

                <div className="student-list-scroller">
                  {filteredStudents.map((id, index) => {
                    const friendlyName = `👤 Học viên #${studentsList.indexOf(id) + 1}`;
                    return (
                      <div 
                        key={id} 
                        className={`student-list-item ${selectedStudent === id ? 'selected' : ''}`}
                        onClick={() => {
                          setSelectedStudent(id);
                          loadStudentProfile(id);
                        }}
                      >
                        <span>{friendlyName}</span>
                        <span style={{ fontSize: 10, opacity: 0.6 }}>{id.substring(0, 6)}...</span>
                      </div>
                    );
                  })}
                </div>
              </aside>

              {/* Main Profile Details */}
              {studentProfile ? (
                <div className="profile-content">
                  <div className="glass-panel profile-summary-header">
                    <div>
                      <h2 style={{ fontSize: 20, fontWeight: 700 }}>
                        📊 Phân tích hồ sơ: Học viên #{studentsList.indexOf(selectedStudent) + 1}
                      </h2>
                      <span className="profile-id-badge">Secure ID: {selectedStudent}</span>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <span className="kpi-label">Tổng lượt clicks tương tác</span>
                      <p style={{ fontSize: 20, fontWeight: 700, color: 'var(--primary)' }}>
                        {studentProfile.risk.total_clicks}
                      </p>
                    </div>
                  </div>

                  <div className="profile-main-grid">
                    {/* Dropout risk analysis */}
                    <section className="risk-card glass-panel">
                      <h3 className="chart-title">Dropout Risk Prediction (LightGBM)</h3>
                      
                      <div className="risk-gauge-wrapper">
                        {/* Custom SVG ring risk indicator */}
                        <svg width="160" height="160" viewBox="0 0 100 100">
                          <circle cx="50" cy="50" r="40" stroke="var(--panel-border)" strokeWidth="8" fill="transparent" />
                          <circle 
                            cx="50" 
                            cy="50" 
                            r="40" 
                            stroke={
                              studentProfile.risk.dropout_risk_level.toLowerCase().includes('high') ? 'var(--danger)' : 
                              studentProfile.risk.dropout_risk_level.toLowerCase().includes('medium') ? 'var(--warning)' : 'var(--success)'
                            } 
                            strokeWidth="8" 
                            fill="transparent" 
                            strokeDasharray="251.2"
                            strokeDashoffset={251.2 - (251.2 * (studentProfile.risk.dropout_probability || 0))}
                            strokeLinecap="round"
                            transform="rotate(-90 50 50)"
                          />
                        </svg>
                        
                        <div className="risk-value-text">
                          <span>{((studentProfile.risk.dropout_probability || 0) * 100).toFixed(1)}%</span>
                          <span className="risk-value-label">Nguy cơ</span>
                        </div>
                      </div>

                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, alignItems: 'center' }}>
                        <span className={`risk-level-badge ${
                          studentProfile.risk.dropout_risk_level.toLowerCase().includes('high') ? 'high' : 
                          studentProfile.risk.dropout_risk_level.toLowerCase().includes('medium') ? 'medium' : 'low'
                        }`}>
                          {studentProfile.risk.dropout_risk_level}
                        </span>
                        <p style={{ fontSize: 13, color: 'var(--text-muted)', textAlign: 'center', marginTop: 4 }}>
                          Dựa trên hành vi clickstream của học viên so với toàn bộ cohort lịch sử.
                        </p>
                      </div>
                    </section>

                    {/* BKT Mastery skills */}
                    <section className="mastery-card glass-panel">
                      <h3 className="chart-title">Độ Thành Thục Kiến Thức (pyBKT Skills Tracker)</h3>
                      <div className="skills-list">
                        {studentProfile.bkt_mastery.map(skill => {
                          const pct = (skill.mastery_probability * 100).toFixed(0);
                          const isStuck = skill.mastery_probability < 0.5;
                          return (
                            <div className="skill-row" key={skill.skill_name}>
                              <div className="skill-header">
                                <span className="skill-name">{skill.skill_name}</span>
                                <span className="skill-pct" style={{ color: isStuck ? 'var(--danger)' : 'var(--success)' }}>
                                  {pct}% {isStuck ? '⚠️' : '✓'}
                                </span>
                              </div>
                              <div className="skill-bar-bg">
                                <div 
                                  className="skill-bar-fill"
                                  style={{ 
                                    width: `${pct}%`,
                                    background: isStuck ? 'var(--danger)' : 'var(--success)'
                                  }}
                                ></div>
                              </div>
                              <span className="skill-attempts">
                                Đã thử: {skill.correct_count}/{skill.total_attempts} câu đúng (BKT State Tracking)
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </section>
                  </div>

                  {/* LightGCN Recommendations */}
                  <section className="recs-card glass-panel">
                    <h3 className="chart-title">Gợi ý học tập cá nhân hóa (LightGCN User-Item Embeddings)</h3>
                    <div className="recs-grid">
                      {studentProfile.recommendations.map((rec, idx) => (
                        <div className="rec-item animate-fade" style={{ animationDelay: `${idx * 0.05}s` }} key={rec.id_site}>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            <div className="rec-activity-icon">
                              <BookOpen size={16} />
                            </div>
                            <span className="rec-id">Site ID: {rec.id_site}</span>
                            <span className="rec-name">{rec.activity_name || `LMS Activity Type: ${rec.activity_type}`}</span>
                          </div>
                          
                          <div className="rec-score-wrapper">
                            <span style={{ color: 'var(--text-muted)', textTransform: 'uppercase', fontSize: 9 }}>Độ tương đồng</span>
                            <span className="rec-score-val">{(rec.recommendation_score || 0).toFixed(3)}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </section>
                </div>
              ) : (
                <div className="glass-panel" style={{ padding: 48, textAlign: 'center', color: 'var(--text-muted)' }}>
                  Vui lòng chọn học viên ở cột bên trái để phân tích sâu.
                </div>
              )}
            </div>
          )}

          {/* ════════ TAB 3: LMS SIMULATOR ════════ */}
          {activeTab === 'simulator' && (
            <div className="sim-grid">
              {/* LMS Screen */}
              <section className="sim-actions-panel glass-panel glow-purple">
                <h3 className="chart-title">Cổng thông tin LMS (LMS Simulation Console)</h3>
                
                {selectedStudent ? (
                  <div>
                    <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: 13, fontWeight: 500 }}>
                        Đang học với tư cách: <strong>Học viên #{studentsList.indexOf(selectedStudent) + 1}</strong>
                      </span>
                      <span className="profile-id-badge" style={{ fontSize: 10 }}>{selectedStudent.substring(0, 10)}...</span>
                    </div>

                    <p className="sim-actions-intro">
                      Đồng đội viết React của bạn có thể sử dụng các API Endpoint được mở để xây dựng các nút bấm "Học tiếp" thế này. Khi học sinh click, nó sẽ cập nhật hệ thống ngay lập tức:
                    </p>

                    <div className="sim-recs-list">
                      {studentProfile && studentProfile.recommendations ? (
                        studentProfile.recommendations.map(rec => (
                          <div className="sim-rec-row" key={rec.id_site}>
                            <div className="sim-rec-info">
                              <div className="rec-activity-icon" style={{ padding: 6 }}>
                                <BookOpen size={14} />
                              </div>
                              <div>
                                <p style={{ fontSize: 13, fontWeight: 600 }}>{rec.activity_name || `LMS Resource ${rec.id_site}`}</p>
                                <span style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                                  Loại: {rec.activity_type} | ID: {rec.id_site}
                                </span>
                              </div>
                            </div>

                            <button 
                              className="study-btn"
                              onClick={() => handleSimulateStudy(rec)}
                            >
                              <span>Học ngay</span>
                              <ArrowRight size={12} />
                            </button>
                          </div>
                        ))
                      ) : (
                        <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>Chưa có gợi ý tài liệu học tập.</p>
                      )}
                    </div>
                  </div>
                ) : (
                  <p style={{ fontSize: 14, color: 'var(--text-muted)', textAlign: 'center', padding: 24 }}>
                    Vui lòng cấu hình học viên trong tab "Học Viên Chi Tiết" trước.
                  </p>
                )}
              </section>

              {/* Console logs */}
              <section className="console-panel glass-panel">
                <div className="console-header">
                  <span className="sidebar-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Terminal size={14} />
                    Hoạt động API Serving (Real-time Console logs)
                  </span>
                  <button className="console-clear-btn" onClick={() => setConsoleLogs([])}>Xóa logs</button>
                </div>

                <div className="console-screen">
                  {consoleLogs.length === 0 ? (
                    <p style={{ color: '#64748b', fontStyle: 'italic' }}>Chưa có log sự kiện API. Hãy click "Học ngay" ở màn hình giả lập LMS bên trái để kích hoạt luồng gọi API thực tế.</p>
                  ) : (
                    consoleLogs.map((log, index) => (
                      <div className={`log-line ${log.type}`} key={index}>
                        <span style={{ color: '#64748b', marginRight: 8 }}>[{log.timestamp}]</span>
                        <span>{log.message}</span>
                      </div>
                    ))
                  )}
                  <div ref={consoleBottomRef}></div>
                </div>
              </section>
            </div>
          )}
        </main>
      )}

      {/* ─── FOOTER ─── */}
      <footer className="footer">
        <p>B-LEARN Big Data Serving Gateway • REST API v1.0.0 (FastAPI)</p>
        <p style={{ marginTop: 4, fontSize: 11, opacity: 0.7 }}>
          Bản quyền © 2026 Minh Tran & B-Learn Dev Team. Xem tài liệu Swagger tại{' '}
          <a href={`${apiBaseUrl}/docs`} target="_blank" rel="noreferrer" style={{ textDecoration: 'underline', display: 'inline-flex', alignItems: 'center', gap: 2 }}>
            docs Swagger <ExternalLink size={10} />
          </a>
        </p>
      </footer>
    </div>
  );
}

export default App;
