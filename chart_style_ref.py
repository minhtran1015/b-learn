"""
gen_entity_analysis.py — Three new NER analysis charts + statistics.

Inspired by: "Generative AI for Genetic Information Extraction" (ALTA 2024)
  - High-recall/lower-precision pattern of LLMs vs. domain-specific models
  - Entity-type coverage gaps between models
  - Multi-word / compound clinical phrase capture

Charts produced (all saved to same directory as this script):
  1. plot_entity_type_coverage.png  — SpaCy entity-type breakdown + LLM word-count buckets
  2. plot_spacy_zero_llm_rescue.png — LLM rescue rate for hops where SpaCy finds 0 bio-entities
#   3. plot_entity_length_dist_spacy.png & plot_entity_length_dist_llm.png
#                                     — Word-count distribution: SpaCy vs. LLM entities
#
# Run from repo root:
#   python3 data/entity_label_analysis/gen_entity_analysis.py
"""

import json
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

# ── Style (matches existing plots exactly) ─────────────────────────────────────
sns.set_theme(style="whitegrid", font_scale=1.2, rc={"axes.labelsize": "medium"})

def fix_spines(ax):
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_edgecolor('black')
        spine.set_linewidth(1.0)

# ── Paths ──────────────────────────────────────────────────────────────────────
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..')

def load(rel):
    with open(os.path.join(ROOT, rel)) as f:
        return json.load(f)

# ── Colour palette (pastel, consistent with existing scripts) ──────────────────
C_SP   = '#afd6d7'   # teal   → SpaCy
C_LM   = '#ffb482'   # orange → LLM
C_OV   = '#8de5a1'   # green  → overlap
C_NONE = '#d3d3d3'   # grey   → neither
C_PUR  = '#d0bbff'   # purple → accent

# ── Data loading ───────────────────────────────────────────────────────────────
print("Loading NER data files...")
meta_1k      = load('data/raw/medhop/test_1000_important.json')
meta_9k      = load('data/metadata_9000q.json')
spacy_seq_1k = load('data/ner/SEQ/spacy_entity_1000q_1.json')
spacy_seq_9k = load('data/ner/SEQ/spacy_entity_9000q_1.json')
llm_seq_1k   = load('data/ner/LLM/LLM_entity_1000q_1.json')
llm_seq_9k   = load('data/ner/LLM/ner_llm_9000_seq.json')
spacy_dp_1k  = {**load('data/ner/meta_entity_WH.json'),
                **load('data/ner/meta_entity_YN.json')}
spacy_dp_9k  = load('data/ner/get_entity_9000q.json')
llm_dp_1k    = load('data/ner/get_entity_from_question_gpt.json')
llm_dp_9k    = {**load('data/ner/LLM/LLM_entity_9000q_1.json'),
                **load('data/ner/LLM/LLM_entity_9000q_2.json'),
                **load('data/ner/LLM/LLM_entity_9000q_3.json')}
spacy_par_1k     = load('data/ner/get_entity_from_question_spacy_parallel_seq.json')
llm_par_merge_1k = load('data/ner/entity_extraction_merge_parallel_seq.json')

# ── Helper functions ───────────────────────────────────────────────────────────
def spacy_bio_entities(detail):
    """Return list of (entity_string, label) for bio-type SpaCy entities."""
    out = []
    for ent, info in detail.items():
        lbl = info.get('label', '')
        if info.get('bio_type') == 'bio' and lbl not in ('new_1', 'new_2', 'gpt'):
            out.append((ent, lbl))
    return out

def spacy_all_entities(detail):
    """Return list of (entity_string, label) for ALL SpaCy entities (bio+non-bio, excl gpt/new)."""
    out = []
    for ent, info in detail.items():
        lbl = info.get('label', '')
        if lbl not in ('new_1', 'new_2', 'gpt') and lbl:
            out.append((ent, lbl))
    return out

def llm_entities(raw):
    """Return list of entity strings from LLM raw output."""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            return []
    if not isinstance(raw, list):
        return []
    return [e for e in raw if isinstance(e, str) and len(e) > 2]

def llm_merged_entities(detail):
    """Return list of LLM entity strings from a merged SpaCy+LLM detail dict."""
    return [ent for ent, info in detail.items() if info.get('label') == 'gpt']

def word_count_bucket(entity: str) -> str:
    n = len(entity.strip().split())
    if n == 1:
        return '1 word'
    elif n == 2:
        return '2 words'
    elif n == 3:
        return '3 words'
    else:
        return '4+ words'

# ── Build per-hop rows ─────────────────────────────────────────────────────────
print("Building hop rows...")
seq_1k_qids = set(h.split('|')[0] for h in spacy_seq_1k)
seq_9k_qids = set(h.split('|')[0] for h in spacy_seq_9k)
parallel_1k_qids = {qid for qid, v in meta_1k.items() if v.get('type_q') == 'parallel'}

rows = []  # each: {hid, type_q, spacy_bio_ents, spacy_all_ents, llm_ents}

def add_row(hid, spacy_bio_ents, spacy_all_ents, llm_ents_list, type_q):
    sp_set = set(e.lower() for e, _ in spacy_bio_ents)
    ll_set = set(e.lower() for e in llm_ents_list)
    rows.append({
        'hid':         hid,
        'type_q':      type_q,
        'spacy_bio':   spacy_bio_ents,          # list of (str, label)
        'spacy_all':   spacy_all_ents,          # list of (str, label)
        'llm':         llm_ents_list,            # list of str
        'n_spacy_bio': len(sp_set),
        'n_llm':       len(ll_set),
        'n_overlap':   len(sp_set & ll_set),
        'n_llm_only':  len(ll_set - sp_set),
        'n_union':     len(sp_set | ll_set),
    })

# 1k sequence hops
for hid, e in spacy_seq_1k.items():
    detail = e.get('extracted_entities', {}).get('detail', {})
    raw    = llm_seq_1k.get(hid, {}).get('extracted_entities', [])
    tq     = meta_1k.get(hid.split('|')[0], {}).get('type_q', 'sequence')
    add_row(hid, spacy_bio_entities(detail), spacy_all_entities(detail), llm_entities(raw), tq)

# 9k sequence hops
for hid, e in spacy_seq_9k.items():
    detail = e.get('extracted_entities', {}).get('detail', {})
    raw    = llm_seq_9k.get(hid, {}).get('entities', [])
    tq     = meta_9k.get(hid.split('|')[0], {}).get('type_q', 'sequence')
    add_row(hid, spacy_bio_entities(detail), spacy_all_entities(detail), llm_entities(raw), tq)

# 1k non-sequence (parallel + direct)
for qid in meta_1k:
    if qid in seq_1k_qids:
        continue
    if qid in parallel_1k_qids:
        detail_sp = spacy_par_1k.get(qid, {}).get('entities_q', {}).get('detail', {})
        detail_mg = llm_par_merge_1k.get(qid, {}).get('entities_q', {}).get('detail', {})
        add_row(qid, spacy_bio_entities(detail_sp), spacy_all_entities(detail_sp), llm_merged_entities(detail_mg), 'parallel')
    else:
        detail = spacy_dp_1k.get(qid, {}).get('entities_q', {}).get('detail', {})
        raw    = llm_dp_1k.get(qid, {}).get('entities_q', [])
        add_row(qid, spacy_bio_entities(detail), spacy_all_entities(detail), llm_entities(raw),
                meta_1k[qid].get('type_q', 'direct'))

# 9k non-sequence hops
for qid in meta_9k:
    if qid in seq_9k_qids:
        continue
    detail = spacy_dp_9k.get(qid, {}).get('entities_q', {}).get('detail', {})
    raw    = llm_dp_9k.get(qid, {}).get('extracted_entities', [])
    add_row(qid, spacy_bio_entities(detail), spacy_all_entities(detail), llm_entities(raw),
            meta_9k[qid].get('type_q', 'direct'))

total_hops = len(rows)
print(f"Total hops: {total_hops:,}")

# ── Collect entity strings & labels for analysis ───────────────────────────────
all_spacy_ents     = []   # list of (str, label)
all_spacy_all_ents = []   # list of (str, label) (both bio and non-bio)
all_llm_ents       = []   # list of str
label_counts       = {}   # label → count

for r in rows:
    all_spacy_ents.extend(r['spacy_bio'])
    all_spacy_all_ents.extend(r['spacy_all'])
    all_llm_ents.extend(r['llm'])
    for _, lbl in r['spacy_bio']:
        label_counts[lbl] = label_counts.get(lbl, 0) + 1

# Word counts
spacy_word_counts = [len(e.strip().split()) for e, _ in all_spacy_ents]
spacy_all_word_counts = [len(e.strip().split()) for e, _ in all_spacy_all_ents]
llm_word_counts   = [len(e.strip().split()) for e in all_llm_ents]

# Multi-word stats
spacy_multi_pct = 100 * sum(1 for w in spacy_word_counts if w >= 2) / max(len(spacy_word_counts), 1)
spacy_all_multi_pct = 100 * sum(1 for w in spacy_all_word_counts if w >= 2) / max(len(spacy_all_word_counts), 1)
llm_multi_pct   = 100 * sum(1 for w in llm_word_counts   if w >= 2) / max(len(llm_word_counts), 1)
spacy_avg_len   = np.mean(spacy_word_counts) if spacy_word_counts else 0
spacy_all_avg_len = np.mean(spacy_all_word_counts) if spacy_all_word_counts else 0
llm_avg_len     = np.mean(llm_word_counts)   if llm_word_counts   else 0

# LLM rescue stats
spacy_zero_rows  = [r for r in rows if r['n_spacy_bio'] == 0]
rescue_rows      = [r for r in spacy_zero_rows if r['n_llm'] > 0]
still_empty_rows = [r for r in spacy_zero_rows if r['n_llm'] == 0]
rescue_rate      = 100 * len(rescue_rows) / max(len(spacy_zero_rows), 1)

print("\n=== Key Statistics ===")
print(f"Total hops              : {total_hops:,}")
print(f"SpaCy bio entities total: {len(all_spacy_ents):,}")
print(f"SpaCy all entities total: {len(all_spacy_all_ents):,}")
print(f"LLM entities total      : {len(all_llm_ents):,}")
print(f"SpaCy bio multi-word %  : {spacy_multi_pct:.1f}%  (avg {spacy_avg_len:.2f} words)")
print(f"SpaCy all multi-word %  : {spacy_all_multi_pct:.1f}%  (avg {spacy_all_avg_len:.2f} words)")
print(f"LLM multi-word %        : {llm_multi_pct:.1f}%  (avg {llm_avg_len:.2f} words)")
print(f"Hops where SpaCy bio=0  : {len(spacy_zero_rows):,}  ({100*len(spacy_zero_rows)/total_hops:.1f}%)")
print(f"  LLM rescues (≥1 ent)  : {len(rescue_rows):,}  ({rescue_rate:.1f}% of SpaCy-zero hops)")
print(f"  Still empty           : {len(still_empty_rows):,}  ({100*len(still_empty_rows)/total_hops:.1f}% of ALL hops)")
print(f"SpaCy label breakdown   : {dict(sorted(label_counts.items(), key=lambda x: -x[1]))}")



# ══════════════════════════════════════════════════════════════════════════════
# CHART 1: Entity Type Coverage
# ══════════════════════════════════════════════════════════════════════════════
print("\nGenerating Chart 1: Entity Type Coverage...")

# SpaCy bio-type labels (sorted by frequency)
sp_labels_sorted = sorted(label_counts.items(), key=lambda x: -x[1])

# LLM word-count bucket breakdown
llm_bucket_counts = {}
for e in all_llm_ents:
    b = word_count_bucket(e)
    llm_bucket_counts[b] = llm_bucket_counts.get(b, 0) + 1

bucket_order  = ['1 word', '2 words', '3 words', '4+ words']
bucket_colors = ['#ffd6a5', '#ffb482', '#ff8c42', '#cc6622']

fig, axes = plt.subplots(1, 2, figsize=(16, 5.5))

# Left: SpaCy bio entity types
ax = axes[0]
sp_names = [x[0] for x in sp_labels_sorted]
sp_vals  = [x[1] for x in sp_labels_sorted]
sp_cols  = [C_SP] * len(sp_names)

bars = ax.bar(sp_names, sp_vals, color=sp_cols, edgecolor='black', linewidth=0.7, zorder=3)
for b, v in zip(bars, sp_vals):
    ax.text(b.get_x() + b.get_width()/2, b.get_height() + max(sp_vals)*0.01,
            f'{v:,}', ha='center', va='bottom', fontsize=8, fontweight='bold')

ax.set_ylabel('Total entity mentions')
ax.set_title('(a) SpaCy bio entity type breakdown\n(all 12,073 hops)', fontweight='bold')
ax.set_xticklabels(sp_names, rotation=40, ha='right', fontsize=9)
ax.set_ylim(0, max(sp_vals) * 1.22)
fix_spines(ax)

# Add annotation: SpaCy covers N labeled types
ax.text(0.98, 0.96, f'{len(sp_labels_sorted)} distinct bio-type labels',
        transform=ax.transAxes, ha='right', va='top', fontsize=9,
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='black', linewidth=0.8))

# Right: LLM entity word-count breakdown
ax = axes[1]
bk_vals = [llm_bucket_counts.get(b, 0) for b in bucket_order]
bars = ax.bar(bucket_order, bk_vals, color=bucket_colors, edgecolor='black', linewidth=0.7, zorder=3)
for b, v in zip(bars, bk_vals):
    pct = 100 * v / max(sum(bk_vals), 1)
    ax.text(b.get_x() + b.get_width()/2, b.get_height() + max(bk_vals)*0.01,
            f'{v:,}\n({pct:.1f}%)', ha='center', va='bottom', fontsize=9, fontweight='bold')

ax.set_ylabel('Total LLM entity mentions')
ax.set_title('(b) LLM entity breakdown by phrase length\n'
             '(LLM has no fine-grained type schema)', fontweight='bold')
ax.set_ylim(0, max(bk_vals) * 1.25)
fix_spines(ax)

# Annotation: multi-word %
multi_total = sum(llm_bucket_counts.get(b, 0) for b in ['2 words', '3 words', '4+ words'])
multi_pct_display = 100 * multi_total / max(sum(bk_vals), 1)
ax.text(0.98, 0.96,
        f'{multi_pct_display:.1f}% of LLM entities\nare multi-word phrases',
        transform=ax.transAxes, ha='right', va='top', fontsize=9,
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='black', linewidth=0.8))

fig.suptitle('Entity Type Coverage: SpaCy (typed schema) vs. LLM (broader phrase capture)',
             fontweight='bold', fontsize=13, y=1.01)
fig.tight_layout()
out1 = os.path.join(HERE, 'plot_entity_type_coverage.png')
fig.savefig(out1, dpi=600, bbox_inches='tight', transparent=False)
plt.close()
print(f"  Saved → {out1}")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 2: LLM Rescue Rate (SpaCy-zero hops)
# ══════════════════════════════════════════════════════════════════════════════
print("\nGenerating Chart 2: LLM Rescue Rate...")

# Break down rescue by question type
type_labels = ['direct', 'sequence', 'parallel']
type_display = ['Direct', 'Sequential', 'Parallel']

rescue_by_type = {}
for tq in type_labels:
    sp_zero = [r for r in rows if r['n_spacy_bio'] == 0 and r['type_q'] == tq]
    rescued  = [r for r in sp_zero if r['n_llm'] > 0]
    rescue_by_type[tq] = {
        'total_hops':   sum(1 for r in rows if r['type_q'] == tq),
        'spacy_zero':   len(sp_zero),
        'rescued':      len(rescued),
        'still_empty':  len(sp_zero) - len(rescued),
    }

fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

# Left panel: Overall rescue pie
ax = axes[0]
sizes_overall = [len(rescue_rows), len(still_empty_rows)]
labels_overall = [
    f'LLM rescues\n{len(rescue_rows):,} hops\n({rescue_rate:.1f}%)',
    f'Still empty\n{len(still_empty_rows):,} hops\n({100-rescue_rate:.1f}%)',
]
colors_overall = [C_LM, C_NONE]
wedges, texts = ax.pie(
    sizes_overall, labels=labels_overall,
    colors=colors_overall,
    wedgeprops={'edgecolor': 'black', 'linewidth': 0.9},
    textprops={'fontsize': 11}, startangle=90,
    explode=[0.05, 0]
)
ax.set_title(f'(a) LLM rescue rate\nfor hops where SpaCy bio = 0\n'
             f'(n = {len(spacy_zero_rows):,} hops, {100*len(spacy_zero_rows)/total_hops:.1f}% of all hops)',
             fontweight='bold')

# Right panel: Rescue breakdown by question type (grouped bar)
ax = axes[1]
x = np.arange(len(type_labels))
width = 0.28

spacy_zero_counts = [rescue_by_type[t]['spacy_zero']  for t in type_labels]
rescued_counts    = [rescue_by_type[t]['rescued']      for t in type_labels]
still_empty_counts= [rescue_by_type[t]['still_empty'] for t in type_labels]

b1 = ax.bar(x - width, spacy_zero_counts, width, label='SpaCy bio = 0 (total)',
            color=C_SP, edgecolor='black', linewidth=0.7, zorder=3)
b2 = ax.bar(x,          rescued_counts,    width, label='LLM rescues (≥1 entity)',
            color=C_LM, edgecolor='black', linewidth=0.7, zorder=3)
b3 = ax.bar(x + width,  still_empty_counts,width, label='Still empty (neither)',
            color=C_NONE, edgecolor='black', linewidth=0.7, zorder=3)

for bars, vals in [(b1, spacy_zero_counts), (b2, rescued_counts), (b3, still_empty_counts)]:
    for b, v in zip(bars, vals):
        if v > 0:
            ax.text(b.get_x() + b.get_width()/2, b.get_height() + 2,
                    f'{v:,}', ha='center', va='bottom', fontsize=9, fontweight='bold')

ax.set_xticks(x)
ax.set_xticklabels(type_display, fontsize=11)
ax.set_ylabel('Number of hops')
ax.set_title('(b) LLM rescue breakdown by question type', fontweight='bold')
ax.legend(fontsize=9, loc='upper right')
fix_spines(ax)

fig.suptitle('LLM NER "Rescue Rate": Hops Where SpaCy Finds Zero Bio-Entities',
             fontweight='bold', fontsize=13, y=1.01)
fig.tight_layout()
out2 = os.path.join(HERE, 'plot_spacy_zero_llm_rescue.png')
fig.savefig(out2, dpi=600, bbox_inches='tight', transparent=False)
plt.close()
print(f"  Saved → {out2}")

print("\n  By-type breakdown:")
for tq, td in zip(type_labels, type_display):
    d = rescue_by_type[tq]
    rr = 100 * d['rescued'] / max(d['spacy_zero'], 1)
    print(f"    {td:12s}: total={d['total_hops']:,}  SpaCy-zero={d['spacy_zero']:,}"
          f"  rescued={d['rescued']:,}  rescue_rate={rr:.1f}%")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 3: Entity Word-Count Length Distribution
# ══════════════════════════════════════════════════════════════════════════════
print("\nGenerating Chart 3: Entity Length Distribution...")

# Bucket counts for histograms
buckets = ['1 word', '2 words', '3 words', '4 words', '5+ words']

def bucket_counts(word_counts_list):
    counts = {'1 word': 0, '2 words': 0, '3 words': 0, '4 words': 0, '5+ words': 0}
    for w in word_counts_list:
        if w == 1:
            counts['1 word'] += 1
        elif w == 2:
            counts['2 words'] += 1
        elif w == 3:
            counts['3 words'] += 1
        elif w == 4:
            counts['4 words'] += 1
        else:
            counts['5+ words'] += 1
    return counts

spacy_unique_set = set(e.lower() for e, _ in all_spacy_all_ents)
llm_unique_set = set(e.lower() for e in all_llm_ents)

sp_all_unique_word_counts = [len(e.strip().split()) for e in spacy_unique_set]
llm_unique_word_counts = [len(e.strip().split()) for e in llm_unique_set]

sp_all_buckets = bucket_counts(sp_all_unique_word_counts)
ll_buckets = bucket_counts(llm_unique_word_counts)

sp_all_total = sum(sp_all_buckets.values())
ll_total = sum(ll_buckets.values())

sp_all_pcts = [100 * sp_all_buckets[b] / max(sp_all_total, 1) for b in buckets]
ll_pcts = [100 * ll_buckets[b] / max(ll_total, 1) for b in buckets]

fig_sp, ax_sp = plt.subplots(figsize=(6, 6))
ax_sp.set_box_aspect(1)
x = np.arange(len(buckets))
sp_all_raw = [sp_all_buckets[b] for b in buckets]

b_sp = ax_sp.bar(x, sp_all_raw, color=C_SP, edgecolor='black', linewidth=1.0, width=1.0, zorder=3)

for bar, count, pct in zip(b_sp, sp_all_raw, sp_all_pcts):
    ax_sp.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 75,
            f'{count:,}\n({pct:.1f}%)', ha='center', va='bottom', fontsize=9.5, fontweight='bold')

ax_sp.set_xticks(x)
ax_sp.set_xticklabels(buckets, fontsize=10.5)
ax_sp.set_ylabel('Total unique entities')
ax_sp.set_ylim(0, 5000)
ax_sp.set_title('SpaCy Entity Phrase-Length Distribution', fontweight='bold', fontsize=12)
fix_spines(ax_sp)

fig_sp.tight_layout()
out3_spacy = os.path.join(HERE, 'plot_entity_length_dist_spacy.png')
fig_sp.savefig(out3_spacy, dpi=600, bbox_inches='tight', transparent=False)
plt.close(fig_sp)
print(f"  Saved → {out3_spacy}")

# Right Subplot: LLM
fig_ll, ax_ll = plt.subplots(figsize=(6, 6))
ax_ll.set_box_aspect(1)
ll_raw = [ll_buckets[b] for b in buckets]

b_ll = ax_ll.bar(x, ll_raw, color=C_LM, edgecolor='black', linewidth=1.0, width=1.0, zorder=3)

for bar, count, pct in zip(b_ll, ll_raw, ll_pcts):
    ax_ll.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 75,
            f'{count:,}\n({pct:.1f}%)', ha='center', va='bottom', fontsize=9.5, fontweight='bold')

ax_ll.set_xticks(x)
ax_ll.set_xticklabels(buckets, fontsize=10.5)
ax_ll.set_ylabel('Total unique entities')
ax_ll.set_ylim(0, 5000)
ax_ll.set_title('LLM Entity Phrase-Length Distribution', fontweight='bold', fontsize=12)
fix_spines(ax_ll)

fig_ll.tight_layout()
out3_llm = os.path.join(HERE, 'plot_entity_length_dist_llm.png')
fig_ll.savefig(out3_llm, dpi=600, bbox_inches='tight', transparent=False)
plt.close(fig_ll)
print(f"  Saved → {out3_llm}")

# ── Final stats summary for README ────────────────────────────────────────────
print("\n" + "="*60)
print("STATS SUMMARY (for README)")
print("="*60)
print(f"SpaCy bio entity total            : {len(all_spacy_ents):,}")
print(f"LLM entity total                  : {len(all_llm_ents):,}")
print(f"SpaCy bio-type labels             : {len(label_counts)} distinct labels")
print(f"SpaCy avg entity length           : {spacy_avg_len:.2f} words")
print(f"LLM avg entity length             : {llm_avg_len:.2f} words")
print(f"SpaCy multi-word (≥2 words) %     : {spacy_multi_pct:.1f}%")
print(f"LLM multi-word (≥2 words) %       : {llm_multi_pct:.1f}%")
print(f"Hops where SpaCy bio = 0          : {len(spacy_zero_rows):,} ({100*len(spacy_zero_rows)/total_hops:.1f}%)")
print(f"  → LLM rescues (≥1 entity found) : {len(rescue_rows):,} ({rescue_rate:.1f}% of SpaCy-zero hops)")
print(f"  → LLM rescue as % of ALL hops   : {100*len(rescue_rows)/total_hops:.1f}%")
print(f"  → Still empty (neither)         : {len(still_empty_rows):,} ({100*len(still_empty_rows)/total_hops:.1f}%)")
print()
print("Done. All 3 charts saved.")
