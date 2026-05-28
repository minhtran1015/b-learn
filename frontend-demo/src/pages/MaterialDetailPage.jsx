import { CheckCircle2, Download, Play, Reply } from 'lucide-react';
import { useMemo } from 'react';
import { Link, useParams } from 'react-router-dom';
import { readCachedMaterials } from '../api/gateway.js';
import { materials } from '../data/mockData.js';

export default function MaterialDetailPage() {
  const { courseId, materialId } = useParams();
  const activeMaterials = useMemo(() => {
    const cached = readCachedMaterials();
    return cached.length > 0 ? cached : materials;
  }, []);
  const material = activeMaterials.find((item) => item.id === materialId) ?? activeMaterials[0];

  return (
    <div className="learning-layout">
      <section className="player-column">
        <Link className="back-link" to={`/courses/${courseId}/materials`}><Reply size={17} />Trở về tài liệu</Link>
        <div className="video-player">
          <Play size={58} />
        </div>
        <div className="card learning-card">
          <div>
            <span className="pill">Bài học</span>
            <h1>{material.title}</h1>
            <p>Hiểu nội dung cốt lõi, ghi chú lại điểm quan trọng và đánh dấu hoàn thành khi đã sẵn sàng.</p>
          </div>
          <button className="button primary"><CheckCircle2 size={19} />Đánh dấu hoàn thành</button>
        </div>
        <div className="card">
          <div className="tabs-line">
            <button className="active">Tổng quan</button>
            <button>Bản ghi</button>
            <button>Ghi chú cá nhân</button>
          </div>
          <h3>Mục tiêu bài học</h3>
          <ul className="check-list">
            <li>Nắm vững khái niệm Overfitting và Underfitting.</li>
            <li>Thực hành kỹ thuật Cross-Validation cơ bản.</li>
            <li>Sử dụng Grid Search để tìm kiếm bộ tham số tối ưu.</li>
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
            <Link key={item.id} className={`lesson-row ${item.id === material.id ? 'active' : ''}`} to={`/courses/${courseId}/materials/${item.id}`}>
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
