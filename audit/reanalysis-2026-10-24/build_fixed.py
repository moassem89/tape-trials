"""Re-score every exported transcript with the corrected extractor; write per-item rows
with the fields the paper's analyses need, plus the failure label from the released
classifier (analysis/task/main.py::classify), applied to the corrected parse."""
import json, sys, glob, os, ast, types
sys.path.insert(0, '/home/claude/tape-trials/eval-harness/harness'); sys.path.insert(0, '/home/claude/reparse')
import score as S, parse as P, fixed_parse as F
S.parse_answer = F.parse_answer
EX = '/home/claude/export/'
# pull classify() out of the analysis job by AST, unmodified
src = open(EX + 'analysis/task/main.py').read()
mod = ast.parse(src); fn = [n for n in mod.body if isinstance(n, ast.FunctionDef) and n.name == 'classify'][0]
ns = {}; exec(compile(ast.Module(body=[fn], type_ignores=[]), 'classify', 'exec'), ns); classify = ns['classify']
def items(p): return {json.loads(l)['id']: json.loads(l) for l in open(p)}
priv = items(EX + 'storage/tape-trials/private.jsonl'); pub = items(EX + 'storage/tape-trials/public.jsonl')
c4 = items(EX + 'jobs/c4c2c79e-controls/control_c4.jsonl'); c6 = items(EX + 'jobs/c4c2c79e-controls/control_c6.jsonl')
os.makedirs('/home/claude/reparse/fixed', exist_ok=True)
for f in sorted(set(glob.glob(EX + '**/transcripts*.jsonl', recursive=True))):
    name = os.path.basename(f)[12:-6]
    if name.startswith('c8_'): continue
    srcset = c4 if 'control_c4' in name else c6 if 'control_c6' in name else priv if 'private' in name else pub
    out = open(f'/home/claude/reparse/fixed/{name}.jsonl', 'w')
    for l in open(f):
        t = json.loads(l); rid = t.get('row_id') or t.get('id'); row = srcset.get(rid)
        if row is None: continue
        text = t.get('response') or ''
        sc = S.score_row(row, text); parsed = F.parse_answer(text)
        lab = None if sc.exact_match else classify(sc, row, parsed.answer if parsed.ok else None)
        out.write(json.dumps(dict(row_id=rid, program_id=row['program_id'], tier=row['difficulty_tier'],
            category=row['category'], exec_steps=row['exec_steps'], exact_match=int(sc.exact_match),
            status=sc.status, finish_reason=t.get('finish_reason'), n_vars=sc.n_vars, n_correct=sc.n_correct,
            words=len(text.split()), failure=lab)) + '\n')
    out.close()
print(len(os.listdir('/home/claude/reparse/fixed')), 'files')
