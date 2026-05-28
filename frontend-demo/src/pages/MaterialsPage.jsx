import { FileText, Filter, PlaySquare } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import PageHeader from '../components/PageHeader.jsx';
import { materials } from '../data/mockData.js';

export default function MaterialsPage() {
  const { courseId } = useParams();

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Khóa học / Tài liệu"
        title="Tài liệu khóa học"
        description="Quản lý và truy cập tất cả tài nguyên học tập của khóa học hiện tại."
        action={<button className="button ghost"><Filter size={18} /> Bộ lọc</button>}
      />
      <div className="filter-tabs">
        <button className="active">Tất cả</button>
        <button>Video</button>
        <button>PDF</button>
        <button>Bài viết</button>
      </div>
      <section className="material-list">
        {materials.map((item) => (
          <Link key={item.id} to={`/courses/${courseId}/materials/${item.id}`} className="material-card">
            <div className="material-icon">{item.type.toLowerCase().includes('pdf') ? <FileText /> : <PlaySquare />}</div>
            <div>
              <small>{item.type}</small>
              <h3>{item.title}</h3>
              <p>{item.chapter}</p>
            </div>
            <span>{item.duration}</span>
          </Link>
        ))}
      </section>
    </div>
  );
}
