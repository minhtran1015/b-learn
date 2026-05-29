OULAD Real Tiny Demo

What this demo contains
- A very small subset of the real OULAD data (header + first N rows).
- Files sampled: `assessments.csv` (200 rows), `courses.csv` (200 rows), `studentAssessment.csv` (200 rows), `studentInfo.csv` (200 rows), `studentRegistration.csv` (200 rows), `studentVle.csv` (500 rows), `vle.csv` (200 rows).

Why this is useful
- Preserves real schema and realistic values for testing models and ETL code.

How it was created
- The first N rows (after header) were copied from the original OULAD files in `large-data/OULAD` to minimize IO while preserving format.

Guidelines to extract a coherent subset
1) Prefer extracting by `id_student` list or by `code_module` + `code_presentation` so related tables remain joinable.
2) Use streaming filters (Python csv reader or `awk`) to avoid loading large files (e.g., `studentVle.csv`) into memory.
3) For `studentVle.csv`, aggregate by day or sample by student to maintain temporal coherence.

Example extraction (by id_student list `uids.txt`):

awk 'NR==FNR{u[$1]=1;next} ($3 in u){print}' uids.txt large-data/OULAD/studentVle.csv > selected_studentVle.csv

Safety notes
- `studentVle.csv` is large (~450MB) — avoid copying it entirely unless necessary.
- This demo includes real rows; handle and share cautiously.
