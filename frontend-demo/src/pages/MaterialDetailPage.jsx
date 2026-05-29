import { CheckCircle2, Download, Play, Reply } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext.jsx';
import { readCachedMaterials, resolveStudentHash, trackStudentClick } from '../api/gateway.js';
import { materials, customCourseMaterials } from '../data/mockData.js';

// ─── Constant: ID khóa học tùy chỉnh ────────────────────────────────────────
const CUSTOM_COURSE_ID = 'big-data-course';

export default function MaterialDetailPage() {
  const { courseId, materialId } = useParams();
  const { currentUser } = useAuth();
  const [studentHash, setStudentHash] = useState('');

  const isCustomCourse = courseId === CUSTOM_COURSE_ID;

  /**
   * activeMaterials – chọn nguồn dữ liệu phù hợp:
   *  - Khóa tùy chỉnh → customCourseMaterials (Lecture_Bank)
   *  - Khóa thông thường → recommendations từ cache hoặc fallback local
   */
  const activeMaterials = useMemo(() => {
    if (isCustomCourse) {
      return customCourseMaterials;
    }
    const cached = readCachedMaterials();
    return cached.length > 0 ? cached : materials;
  }, [isCustomCourse]);

  const material = activeMaterials.find((item) => item.id === materialId) ?? activeMaterials[0];

  useEffect(() => {
    let isMounted = true;
    resolveStudentHash(currentUser)
      .then((hash) => {
        if (isMounted) {
          setStudentHash(hash);
        }
      })
      .catch((error) => {
        console.log('detail hash fallback:', error);
      });

    return () => {
      isMounted = false;
    };
  }, [currentUser]);

  /**
   * handleMaterialClick – OULAD Mapping Layer
   *
   * Ưu tiên id_site_mapping (OULAD ID thực) → id_site → id nội bộ.
   * Đảm bảo event gửi về /track-click luôn chứa mã OULAD hợp lệ
   * để Kafka ingestion pipeline nhận đúng chuẩn schema.
   */
  const handleMaterialClick = async (item) => {
    const rawId = item.id_site_mapping || item.id_site || item.id;
    const cleanedSiteId = String(rawId).replace(/\D/g, '');
    await trackStudentClick(studentHash, cleanedSiteId);
  };

  return (
    <div className="learning-layout">
      <section className="player-column">
        <Link className="back-link" to={`/courses/${courseId}/materials`}><Reply size={17} />Trở về tài liệu</Link>
        <div className="video-player">
          <Play size={58} />
        </div>
        <div className="card learning-card">
          <div>
            <span className="pill">{isCustomCourse ? 'Big Data' : 'Bài học'}</span>
            <h1>{material.title}</h1>
            <p>Hiểu nội dung cốt lõi, ghi chú lại điểm quan trọng và đánh dấu hoàn thành khi đã sẵn sàng.</p>
            {isCustomCourse && material.id_site_mapping && (
              <small style={{ opacity: 0.55, fontSize: '11px' }}>
                🔗 OULAD ID: {material.id_site_mapping} · {material._bank_source}
              </small>
            )}
          </div>
          <button
            className="button primary"
            onClick={() => {
              try {
                void handleMaterialClick(material);
              } catch (e) {
                // silent
              }
            }}
          ><CheckCircle2 size={19} />Đánh dấu hoàn thành</button>
        </div>
        <div className="card">
          <div className="tabs-line">
            <button className="active">Tổng quan</button>
            <button>Bản ghi</button>
            <button>Ghi chú cá nhân</button>
          </div>
          <h3>Mục tiêu bài học</h3>
          <ul className="check-list">
            {isCustomCourse ? (
              <>
                <li>Nắm vững khái niệm cốt lõi và thuật ngữ chuyên ngành trong bài.</li>
                <li>Phân biệt được các thành phần và cơ chế hoạt động chính.</li>
                <li>Áp dụng kiến thức vào phân tích tình huống thực tế trong Big Data.</li>
              </>
            ) : (
              <>
                <li>Nắm vững khái niệm Overfitting và Underfitting.</li>
                <li>Thực hành kỹ thuật Cross-Validation cơ bản.</li>
                <li>Sử dụng Grid Search để tìm kiếm bộ tham số tối ưu.</li>
              </>
            )}
          </ul>
        </div>
      </section>
      <aside className="side-stack">
        <div className="card progress-card">
          <div className="progress-row"><strong>Tiến độ chương</strong><strong>66%</strong></div>
          <div className="progress-track"><span style={{ width: '66%' }} /></div>
          <p>Đã hoàn thành 2/3 bài học bắt buộc</p>
        </div>
        <div className="card">
          <h2>Nội dung học tập</h2>
          {activeMaterials.map((item) => (
            <Link
              key={item.id}
              className={`lesson-row ${item.id === material.id ? 'active' : ''}`}
              to={`/courses/${courseId}/materials/${item.id}`}
              onClick={() => {
                void handleMaterialClick(item);
              }}
            >
              <span>{item.status === 'Đã hoàn thành' ? <CheckCircle2 size={18} /> : <Play size={18} />}</span>
              <div><strong>{item.title}</strong><small>{item.type} • {item.duration}</small></div>
            </Link>
          ))}
        </div>
        <div className="blue-panel soft">
          <Download />
          <h3>Tài liệu đính kèm</h3>
          <p>Slide bài giảng PDF và dataset thực hành.</p>
        </div>
      </aside>
    </div>
  );
}
