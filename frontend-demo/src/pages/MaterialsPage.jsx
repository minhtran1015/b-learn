import { FileText, Filter, PlaySquare } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext.jsx';
import PageHeader from '../components/PageHeader.jsx';
import { ensureGatewaySession, fetchRecommendations } from '../api/gateway.js';

export default function MaterialsPage() {
  const { courseId } = useParams();
  const { currentUser } = useAuth();
  const [materials, setMaterials] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let isMounted = true;

    async function loadMaterials() {
      setIsLoading(true);
      setError('');
      try {
        const { studentHash } = await ensureGatewaySession(currentUser);
        const payload = await fetchRecommendations(studentHash);
        if (isMounted) {
          setMaterials(Array.isArray(payload?.recommendations) ? payload.recommendations : []);
        }
      } catch (loadError) {
        if (isMounted) {
          setError(loadError.message || 'Không thể tải tài liệu từ Gateway.');
          setMaterials([]);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadMaterials();
    return () => {
      isMounted = false;
    };
  }, [currentUser]);

  const hasMaterials = useMemo(() => materials.length > 0, [materials]);

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
        {isLoading && <p>Đang tải tài liệu từ FastAPI Gateway...</p>}
        {!isLoading && error && <p>{error}</p>}
        {!isLoading && !error && !hasMaterials && <p>Chưa có gợi ý tài liệu cho học viên hiện tại.</p>}
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
