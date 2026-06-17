import lectureBank from './Lecture_Bank.json';

const OULAD_VLE_IDS = [
  546614, 546644, 546645, 546648, 546649, 546651, 546652, 546653, 546654, 546655, 546656, 546657, 546658, 546659, 546660, 546661, 546662, 546664, 546665, 546666, 546667, 546668, 546669, 546670, 546671, 546672, 546674, 546675, 546676, 546677, 546678, 546679, 546680, 546682, 546683, 546685, 546686, 546687, 546688, 546689, 546690, 546691, 546692, 546693, 546694, 546695, 546696, 546697, 546699, 546700, 546701, 546702, 546703, 546704, 546705, 546706, 546707, 546708, 546709, 546711, 546712, 546713, 546714, 546716, 546717, 546719, 546721, 546723, 546725, 546726, 546728, 546731, 546732, 546733, 546734, 546735, 546736, 546737, 546738, 546739, 546740, 546871, 546872, 546873, 546874, 546876, 546879, 546883, 546884, 546885, 546887, 546888, 546889, 546890, 546891, 546894, 546896, 546897, 546898, 546899, 546901, 546903, 546905, 546906, 546907, 546909, 546910, 546911, 546913, 546914, 546915, 546916, 546917, 546918, 546919, 546920, 546921, 546922, 546923, 546924, 546925, 546927, 546928, 546930, 546933, 546935, 546942, 546943, 546947, 546948, 546952, 546954, 546955, 546960, 546961, 546965, 546966, 546968, 546970, 546971, 546972, 546974, 546975, 546982, 546983, 546984, 546985, 546986, 546987, 546988, 546989, 546990, 546991, 546992, 546994, 546995, 546996, 546997, 546998, 547000, 547001, 547003, 547004, 547005, 547006, 547007, 547008, 547009, 547011, 547012, 547013, 547014, 547015, 547017, 547018, 547019, 547020, 547021, 547022, 547023, 547024, 547025, 547026, 547027, 547028, 547030, 547031, 547032, 547034, 547035, 547036, 547037, 547040, 547042, 547047, 547048, 547049, 547050, 547066, 547067,
];

const LECTURES = lectureBank.Chapters.flatMap((chapter) =>
  chapter.Lectures.map((lecture) => ({
    chapterId: chapter.ChapterID,
    title: `${lecture.LecID}: ${lecture.Name}`,
    type: lecture.Type || 'Markdown',
    chapter: `Chương ${chapter.Order}: ${chapter.Name}`,
  }))
);

export function mapOuladIdToDemoLectureTitle(rawId) {
  const numericId = Number(String(rawId || '').replace(/\D/g, ''));
  if (!Number.isFinite(numericId)) {
    return '';
  }

  const index = OULAD_VLE_IDS.indexOf(numericId);
  if (index < 0 || LECTURES.length === 0) {
    return '';
  }

  const mappedLecture = LECTURES[index % LECTURES.length];
  return mappedLecture?.title || '';
}

export function resolveDemoLectureTitle(item) {
  const rawTitle = String(item?.title || '').trim();
  const rawId = item?.id_site_mapping || item?.id_site || item?.id || '';
  const mappedTitle = mapOuladIdToDemoLectureTitle(rawId);
  if (mappedTitle) {
    return mappedTitle;
  }

  return rawTitle || 'Học liệu';
}
