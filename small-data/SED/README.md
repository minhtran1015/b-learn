SED Real Tiny Demo

What this demo contains
- A very small subset of the real SED data (header + first N rows).
- Files sampled: `Student_activity_summary.csv` (200 rows), `Student_grade_aggregated.csv` (200 rows), `Student_grade_detailed.csv` (200 rows), `Student_log.csv` (500 rows).

Why this is useful
- Preserves real data rows and formats while keeping IO and size small for testing.

How it was created
- The first N rows (after header) were copied from the original SED files in `large-data/SED`.

Guidelines to extract another subset safely
1) Decide sample strategy: by user, by course, or by time window. For Student_log, sampling by `userid` or `courseid` keeps coherence; filtering first N rows can break temporal continuity.
2) For reproducibility, prefer to extract by explicit `userid` list and copy all rows matching them across `Student_log` and the other tables.
3) Use streaming filters (e.g., `awk` or Python `csv` streaming) to avoid loading the whole `Student_log.csv` into memory.

Example commands (by userid list):

# Create a file `uids.txt` containing userids, one per line
# Then run a streaming filter to extract log rows
awk 'NR==FNR{u[$1]=1;next} ($5 in u){print}' uids.txt large-data/SED/Student_log.csv > selected_log.csv

Safety notes
- `Student_log.csv` is large (~800MB) — avoid copying it entirely unless you need the full dataset.
- When extracting by `userid`, ensure the `userid` values exist in other SED tables to preserve joinability.
