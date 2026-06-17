import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, '..', '..');
const lectureBankPath = path.join(repoRoot, 'frontend-demo', 'src', 'data', 'Lecture_Bank.json');
const sourceRoot = path.join(repoRoot, 'small-data');
const outputPath = path.join(repoRoot, 'frontend-demo', 'src', 'data', 'bigDataLessonContent.js');
const testBankSourcePath = path.join(sourceRoot, 'Test_Bank.json');
const testBankOutputPath = path.join(repoRoot, 'frontend-demo', 'src', 'data', 'Test_Bank.json');

const lectureBank = JSON.parse(await readFile(lectureBankPath, 'utf8'));

function makeExcerpt(text) {
  const normalized = String(text || '').trim().replace(/\r\n/g, '\n');
  if (!normalized) return '';
  const lines = normalized.split('\n').map((line) => line.trim()).filter(Boolean);
  const excerptLines = [];
  for (const line of lines) {
    excerptLines.push(line);
    if (excerptLines.length >= 6) break;
  }
  return excerptLines.join('\n');
}

const contentMap = {};

for (const chapter of lectureBank.Chapters || []) {
  for (const lecture of chapter.Lectures || []) {
    const relContentPath = String(lecture.Content || '').replace(/^Data\//, 'Data/');
    const sourcePath = path.join(sourceRoot, relContentPath);
    const body = await readFile(sourcePath, 'utf8');
    contentMap[lecture.LecID] = {
      lecId: lecture.LecID,
      chapterId: chapter.ChapterID,
      chapterName: chapter.Name,
      title: lecture.Name,
      contentPath: relContentPath,
      body: body.trim(),
      excerpt: makeExcerpt(body),
    };
  }
}

const serialized = JSON.stringify(contentMap, null, 2);
const output = `export const bigDataLessonContentByLecId = ${serialized};\n`;
await writeFile(outputPath, output, 'utf8');

const testBank = await readFile(testBankSourcePath, 'utf8');
await writeFile(testBankOutputPath, testBank, 'utf8');
