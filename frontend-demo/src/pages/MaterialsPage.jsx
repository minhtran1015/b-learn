import { FileText, Filter, PlaySquare } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext.jsx';
import PageHeader from '../components/PageHeader.jsx';
import { ensureGatewaySession, fetchRecommendations, resolveStudentHash, trackStudentClick } from '../api/gateway.js';
import { materials as localMaterials } from '../data/mockData.js';

export default function MaterialsPage() {
  const { courseId } = useParams();
  const { currentUser } = useAuth();
  const [materials, setMaterials] = useState(() => localMaterials);
  const [isLoading, setIsLoading] = useState(true);
  const [studentHash, setStudentHash] = useState('');

  useEffect(() => {
    let isMounted = true;

    async function loadMaterials() {
      setIsLoading(true);
      try {
        const resolvedHash = await resolveStudentHash(currentUser);
        if (isMounted) {
          setStudentHash(resolvedHash);
        }
        const { studentHash } = await ensureGatewaySession(currentUser);
        const payload = await fetchRecommendations(studentHash);
        if (isMounted) {
          setMaterials(Array.isArray(payload?.recommendations) ? payload.recommendations : []);
        }
      } catch (loadError) {
        console.log('materials fallback:', loadError);
        if (isMounted) {
          setMaterials(localMaterials);
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

  const handleMaterialClick = async (item) => {
    const rawId = item.id_site || item.id;
    const cleanedSiteId = String(rawId).replace(/\D/g, '');
    await trackStudentClick(studentHash, cleanedSiteId);
  };

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
        {!isLoading && !hasMaterials && <p>Chưa có tài liệu để hiển thị.</p>}
        {materials.map((item) => (
          <Link
            key={item.id}
            to={`/courses/${courseId}/materials/${item.id}`}
            className="material-card"
            onClick={() => {
              void handleMaterialClick(item);
            }}
          >
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
