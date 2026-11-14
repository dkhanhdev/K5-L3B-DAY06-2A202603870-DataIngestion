"""Replay saved retrievals with separately approved alternative evidence.

No model/database calls; original benchmark, metrics, traces and selection stay intact.
"""
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'starter'))
from src.evaluation import canonical, evaluate_query, summarize


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    audit_dir = ROOT / 'results/audit'
    approvals = load(audit_dir / 'alternative_evidence_approval.json')
    pages = {p['page']: p for p in map(json.loads, (ROOT / 'data/processed/pages.jsonl').read_text(encoding='utf-8').splitlines())}
    for alt in approvals['alternatives']:
        page = pages[alt['gold']['page']]
        assert page['document_id'] == alt['gold']['source_id']
        assert canonical(alt['gold']['evidence_quote']) in canonical(page['text'])
    traces, changes = [], []
    for split in ['dev', 'test']:
        for original in load(ROOT / f'results/{split}_traces.json'):
            question = copy.deepcopy(original)
            alternatives = [a['gold'] for a in approvals['alternatives'] if a['question_id'] == question['id']]
            question['alternative_gold'] = question.get('alternative_gold', []) + alternatives
            evaluated = evaluate_query(question, copy.deepcopy(original['hits']))
            evaluated.update(original_hit1=original['hit1'], original_hit3=original['hit3'],
                             evaluation_stage='post_run_audit_with_student_approved_alternative_evidence')
            traces.append(evaluated)
            if (evaluated['hit1'], evaluated['hit3']) != (original['hit1'], original['hit3']):
                changes.append({'strategy': original['strategy'], 'split': split, 'question_id': original['id'],
                                'original_hit1': original['hit1'], 'audited_hit1': evaluated['hit1'],
                                'original_hit3': original['hit3'], 'audited_hit3': evaluated['hit3']})
    selection = load(ROOT / 'results/selection.json')
    metrics = {'evaluation_stage': 'post_run_audit', 'approval_file': 'results/audit/alternative_evidence_approval.json',
               'original_selection_preserved': selection['selected_strategy'],
               'method': 'Original gold OR approved alternative; same source/page plus full quote; identical saved top-3 for A/B/C. No new retrieval or tuning. Retrieval seconds are copied from the original run, not measured again.',
               'metrics': summarize(traces), 'changed_queries': changes,
               'original_files_sha256': {f'results/{n}': hashlib.sha256((ROOT / 'results' / n).read_bytes()).hexdigest()
                   for n in ['dev_traces.json', 'test_traces.json', 'dev_metrics.json', 'test_metrics.json', 'selection.json']}}
    for name, data in [('retrieval_audited_traces.json', traces), ('retrieval_audited_metrics.json', metrics)]:
        (audit_dir / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'changed_queries': changes, 'metrics': metrics['metrics']}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
