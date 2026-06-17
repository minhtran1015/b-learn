import { customCourseAssignments } from '../data/mockData.js';

export const CUSTOM_COURSE_ID = 'big-data-course';
export const COMPETENCY_PROGRESS_KEY = 'blearn.competency_progress';
export const PASSING_SCORE = 60;

export function readCompetencyProgress() {
  try {
    return JSON.parse(localStorage.getItem(COMPETENCY_PROGRESS_KEY) || '{}');
  } catch {
    return {};
  }
}

export function writeCompetencyProgress(chapterId, progressItem) {
  if (!chapterId) return;
  const current = readCompetencyProgress();
  current[chapterId] = {
    score: Number(progressItem.score || 0),
    submissions: Number(progressItem.submissions || 1),
    correct_count: Number(progressItem.correct_count || 0),
    question_count: Number(progressItem.question_count || 0),
    updated_at: progressItem.updated_at || new Date().toISOString(),
  };
  localStorage.setItem(COMPETENCY_PROGRESS_KEY, JSON.stringify(current));
  window.dispatchEvent(new CustomEvent('blearn-progress-updated'));
}

export function mergeCompetencyProgress(remoteProgress = {}) {
  const current = readCompetencyProgress();
  const merged = { ...current };
  Object.entries(remoteProgress || {}).forEach(([chapterId, item]) => {
    const localItem = merged[chapterId] || {};
    const remoteSubmissions = Number(item?.submissions || (Number(item?.score || 0) > 0 ? 1 : 0));
    const localSubmissions = Number(localItem?.submissions || 0);
    const remoteTime = Date.parse(item?.updated_at || '') || 0;
    const localTime = Date.parse(localItem?.updated_at || '') || 0;
    const shouldUseRemote = remoteSubmissions > localSubmissions || (remoteSubmissions === localSubmissions && remoteTime >= localTime);

    if (shouldUseRemote) {
      merged[chapterId] = {
        ...localItem,
        ...item,
        submissions: remoteSubmissions,
      };
    }
  });
  localStorage.setItem(COMPETENCY_PROGRESS_KEY, JSON.stringify(merged));
  window.dispatchEvent(new CustomEvent('blearn-progress-updated'));
  return merged;
}

export function getCourseProgressPercent(courseId) {
  if (courseId !== CUSTOM_COURSE_ID) return null;
  const progress = readCompetencyProgress();
  const passedCount = customCourseAssignments.filter((assignment) => {
    const item = progress[assignment.chapterId];
    return Number(item?.submissions || 0) > 0 && Number(item?.score || 0) >= PASSING_SCORE;
  }).length;
  return Math.round((passedCount / customCourseAssignments.length) * 100);
}
