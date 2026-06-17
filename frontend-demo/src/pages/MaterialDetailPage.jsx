import { CheckCircle2, Download, Play, Reply } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext.jsx';
import { readCachedMaterials, resolveStudentHash, trackStudentClick } from '../api/gateway.js';
import { materials, customCourseMaterials } from '../data/mockData.js';

const CUSTOM_COURSE_ID = 'big-data-course';

function MarkdownContent({ content }) {
  const lines = String(content || '').split(/\r?\n/);
  const nodes = [];
  let listItems = [];

  const flushList = () => {
    if (listItems.length === 0) return;
    nodes.push(
      <ul key={`list-${nodes.length}`} className="lesson-markdown-list">
        {listItems.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}
      </ul>
    );
    listItems = [];
  };

  lines.forEach((line, index) => {
    const trimmed = line.trim();
    if (!trimmed) {
      flushList();
      return;
    }

    const heading = trimmed.match(/^(#{1,3})\s+(.+)$/);
    if (heading) {
      flushList();
      const level = heading[1].length;
      const Tag = level === 1 ? 'h2' : level === 2 ? 'h3' : 'h4';
      nodes.push(<Tag key={`heading-${index}`}>{heading[2]}</Tag>);
      return;
    }

    const bullet = trimmed.match(/^[-*]\s+(.+)$/);
    if (bullet) {
      listItems.push(bullet[1]);
      return;
    }

    const numbered = trimmed.match(/^\d+\.\s+(.+)$/);
    if (numbered) {
      listItems.push(numbered[1]);
      return;
    }

    flushList();
    nodes.push(<p key={`paragraph-${index}`}>{trimmed}</p>);
  });

  flushList();
  return <div className="lesson-markdown">{nodes}</div>;
}

export default function MaterialDetailPage() {
  const { courseId, materialId } = useParams();
  const { currentUser } = useAuth();
  const [studentHash, setStudentHash] = useState('');
  const sessionStartRef = useRef(Date.now());
  const sessionFlushedRef = useRef(false);
  const materialRef = useRef(null);
  const studentHashRef = useRef('');

  const isCustomCourse = courseId === CUSTOM_COURSE_ID;

  const activeMaterials = useMemo(() => {
    if (isCustomCourse) {
      return customCourseMaterials;
    }
    const cached = readCachedMaterials();
    return cached.length > 0 ? cached : materials;
  }, [isCustomCourse]);

  const material = activeMaterials.find((item) => item.id === materialId) ?? activeMaterials[0];
  materialRef.current = material;
  const chapterMaterials = useMemo(() => {
    if (!material) return [];
    if (!isCustomCourse) return activeMaterials;
    return activeMaterials.filter((item) => item.chapterId === material.chapterId);
  }, [activeMaterials, isCustomCourse, material]);
  const currentChapterIndex = Math.max(0, chapterMaterials.findIndex((item) => item.id === material?.id));
  const chapterProgress = chapterMaterials.length > 0
    ? Math.round(((currentChapterIndex + 1) / chapterMaterials.length) * 100)
    : 0;

  useEffect(() => {
    sessionStartRef.current = Date.now();
    sessionFlushedRef.current = false;
  }, [materialId]);

  useEffect(() => {
    let isMounted = true;
    resolveStudentHash(currentUser)
      .then((hash) => {
        if (isMounted) {
          setStudentHash(hash);
          studentHashRef.current = hash;
        }
      })
      .catch((error) => {
        console.log('detail hash fallback:', error);
      });

    return () => {
      isMounted = false;
    };
  }, [currentUser]);

  const handleMaterialClick = async (item) => {
    const rawId = item.id_site_mapping || item.id_site || item.id;
    const cleanedSiteId = String(rawId).replace(/\D/g, '');
    await trackStudentClick(studentHashRef.current || studentHash, cleanedSiteId, item);
  };

  const flushMaterialSession = async () => {
    const activeMaterial = materialRef.current;
    if (sessionFlushedRef.current || !activeMaterial) return;
    sessionFlushedRef.current = true;
    const rawId = activeMaterial.id_site_mapping || activeMaterial.id_site || activeMaterial.id;
    const cleanedSiteId = String(rawId).replace(/\D/g, '');
    const durationSeconds = Math.max(1, Math.ceil((Date.now() - sessionStartRef.current) / 1000));
    await trackStudentClick(studentHashRef.current || studentHash, cleanedSiteId, {
      ...activeMaterial,
      duration_seconds: durationSeconds,
      event_type: 'material_view',
    });
  };

  useEffect(() => {
    return () => {
      void flushMaterialSession();
    };
  }, [materialId]);

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
          </div>
          <button
            className="button primary"
            onClick={() => {
              try {
                void flushMaterialSession();
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
        {isCustomCourse && material?.contentMarkdown && (
          <div className="card">
            <h3>Nội dung bài học</h3>
            <MarkdownContent content={material.contentMarkdown} />
          </div>
        )}
        {isCustomCourse && !material?.contentMarkdown && material?.contentExcerpt && (
          <div className="card">
            <h3>Nội dung bài học</h3>
            <MarkdownContent content={material.contentExcerpt} />
          </div>
        )}
      </section>
      <aside className="side-stack">
        <div className="card progress-card">
          <div className="progress-row"><strong>Tiến độ chương</strong><strong>{chapterProgress}%</strong></div>
          <div className="progress-track"><span style={{ width: `${chapterProgress}%` }} /></div>
          <p>Bài {currentChapterIndex + 1}/{chapterMaterials.length || activeMaterials.length} trong chương hiện tại</p>
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
          <p>{isCustomCourse ? 'Nội dung bài giảng, ghi chú chương và tài liệu thực hành.' : 'Slide bài giảng PDF và dataset thực hành.'}</p>
        </div>
      </aside>
    </div>
  );
}
