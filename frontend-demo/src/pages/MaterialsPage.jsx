import { FileText, Filter, PlaySquare } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext.jsx';
import PageHeader from '../components/PageHeader.jsx';
import { ensureGatewaySession, fetchRecommendations, resolveStudentHash, trackStudentClick } from '../api/gateway.js';
import { materials as localMaterials, customCourseMaterials } from '../data/mockData.js';
import { resolveDemoLectureTitle } from '../data/ouladLectureTitleMap.js';

const CUSTOM_COURSE_ID = 'big-data-course';

export default function MaterialsPage() {
  const { courseId } = useParams();
  const { currentUser } = useAuth();

  const isCustomCourse = courseId === CUSTOM_COURSE_ID;

  const [materials, setMaterials] = useState(() =>
    isCustomCourse ? customCourseMaterials : localMaterials
  );
  const [isLoading, setIsLoading] = useState(!isCustomCourse);
  const [studentHash, setStudentHash] = useState('');

  useEffect(() => {
    let isMounted = true;

    async function loadMaterials() {
      try {
        const resolvedHash = await resolveStudentHash(currentUser);
        if (isMounted) {
          setStudentHash(resolvedHash);
        }
      } catch {
        // silent
      }

      if (isCustomCourse) {
        if (isMounted) {
          setMaterials(customCourseMaterials);
          setIsLoading(false);
        }
        return;
      }

      setIsLoading(true);
      try {
        const { studentHash: sHash } = await ensureGatewaySession(currentUser);
        const payload = await fetchRecommendations(sHash);
        if (isMounted) {
          setMaterials(Array.isArray(payload?.recommendations) ? payload.recommendations : []);
        }
      } catch (loadError) {
        console.log('materials load error:', loadError);
        if (isMounted) {
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
  }, [currentUser, isCustomCourse]);

  const hasMaterials = useMemo(() => materials.length > 0, [materials]);

  const handleMaterialClick = async (item) => {
    const rawId = item.id_site_mapping || item.id_site || item.id;
    const cleanedSiteId = String(rawId).replace(/\D/g, '');

    await trackStudentClick(studentHash, cleanedSiteId, item);

    if (!isCustomCourse) {
      try {
        const payload = await fetchRecommendations(studentHash);
        setMaterials(Array.isArray(payload?.recommendations) ? payload.recommendations : []);
      } catch (e) {
        console.log('Reload recommendations error:', e);
      }
    }
  };

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow={isCustomCourse ? 'Big Data / Tài liệu' : 'Khóa học / Tài liệu'}
        title={isCustomCourse ? 'Tài liệu Big Data & Hệ thống Phân tán' : 'Tài liệu khóa học'}
        description={
          isCustomCourse
            ? 'Hệ thống bài giảng Big Data theo từng chương, đồng bộ với nội dung học tập hiện tại.'
            : 'Quản lý và truy cập tất cả tài nguyên học tập của khóa học hiện tại.'
        }
        action={<button className="button ghost"><Filter size={18} /> Bộ lọc</button>}
      />
      <div className="filter-tabs">
        <button className="active">Tất cả</button>
        <button>Video</button>
        <button>PDF</button>
        <button>Bài viết</button>
      </div>
      <section className="material-list">
        {isLoading && <p>Đang tải tài liệu học tập...</p>}
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
              <h3>{resolveDemoLectureTitle(item)}</h3>
              <p>{item.chapter}</p>
            </div>
            <span>{item.duration}</span>
          </Link>
        ))}
      </section>
    </div>
  );
}
