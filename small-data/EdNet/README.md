EdNet Real Tiny Demo

What this demo contains
- A very small subset of the real EdNet data (copied files, not synthetic).
- User shards: `u1.csv`, `u10.csv`, `u100.csv` copied from the real dataset across KT1, KT2, KT3, KT4.
- Real `contents` CSVs copied from `large-data/EdNet_2/contents`.
- Real `Question_Bank.json` and `Lecture_Bank.json` copied from `large-data` root.

Why this is useful
- Preserves real row formats and example values for testing models and code that expect realistic logs.
- Small size avoids heavy IO and preserves privacy by limiting user count to 3.

How it was created
- Files were copied directly from the original dataset for the three user shard files `u1,u10,u100`.

How to extract a similar tiny real subset yourself
1) Pick a small list of user shard names (e.g., `u1,u10,u100`).
2) Copy the matching `u{N}.csv` from each of the KT folders you need (KT1/KT2/KT3/KT4) into your demo folder.
3) Copy the `contents/*.csv` files that provide metadata for `question_id`/`lecture_id` resolution.
4) Optionally copy `Question_Bank.json` and `Lecture_Bank.json` for richer content examples.

Quick copy commands (example)

cp large-data/EdNet_2/KT1/u1.csv large-data/Ednet_demo_real_small/KT1/
cp large-data/EdNet/KT2/u1.csv large-data/Ednet_demo_real_small/KT2/
cp large-data/EdNet_2/KT3/u1.csv large-data/Ednet_demo_real_small/KT3/
cp large-data/EdNet/KT4/u1.csv large-data/Ednet_demo_real_small/KT4/

Safety and privacy notes
- This copies a very small number of real user records. Do not share the copied data publicly unless you have the right to do so.
- For larger extractions, prefer scripted, batched copying and verify disk usage.

If you want, I can now:
- Package the tiny demo into a ZIP for easy sharing.
- Or write a small Python script `extract_ednet_subset.py` that takes a list of user IDs and copies matching files across KT folders automatically and validates references.
