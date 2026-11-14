"""Staged ingestion, dev evaluation, freeze and test; no synthetic fallback."""
import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '.runtime/python'))
from dotenv import load_dotenv
from .chunking import fixed_size, by_paragraph
from .embeddings import MyEmbedder
from .evaluation import evaluate_query, summarize
from .models import DocumentPage
from .store import PgVectorStore

RESULTS = ROOT / 'results'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def stamp():
    return datetime.now(timezone.utc).isoformat()


def fingerprint():
    paths = [ROOT / 'starter/experiment.json', ROOT / 'benchmark/questions.json',
             ROOT / 'data/processed/pages.jsonl'] + sorted((ROOT / 'starter/src').glob('*.py'))
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def embedder(config):
    return MyEmbedder(config['model'], config['revision'], str(ROOT / '.runtime/huggingface'), config['batch_size'])


def ingest(config, store):
    if (RESULTS / 'selection.json').exists():
        raise RuntimeError('Already frozen; archive results before a new experiment')
    start = time.perf_counter()
    pages = [DocumentPage(**json.loads(line)) for line in (ROOT / 'data/processed/pages.jsonl').read_text(encoding='utf-8').splitlines()]
    if len(pages) < 30 or not all(p.text.strip() for p in pages):
        raise ValueError('Need at least 30 nonempty content pages')
    model = embedder(config)
    store.create_schema()
    all_chunks, stats, samples = {}, {}, []
    for name, params in config['strategies'].items():
        clock = time.perf_counter()
        if name == 'C':
            chunks, vectors = all_chunks['B'], b_vectors
            embedding_seconds = stats['B']['embedding_seconds']
            chunking_seconds = stats['B']['chunking_seconds']
        else:
            chunks = [c for page in pages for c in (fixed_size(page, params['size'], params['overlap'])
                       if params['chunking'] == 'fixed' else by_paragraph(page, params['max_size']))]
            chunking_seconds = time.perf_counter() - clock
            tick = time.perf_counter()
            vectors = model.embed_documents([c.text for c in chunks])
            embedding_seconds = time.perf_counter() - tick
            if name == 'B':
                b_vectors = vectors
        all_chunks[name] = chunks
        tick = time.perf_counter()
        store.upsert(name, chunks, vectors)
        store_seconds = time.perf_counter() - tick
        before = store.snapshot(name)
        store.upsert(name, chunks, vectors)
        after = store.snapshot(name)
        if before != after or len(after) != len(chunks):
            raise RuntimeError(f'Idempotence failed for {name}')
        lengths = sorted(len(c.text) for c in chunks)
        stats[name] = {'chunk_count': len(chunks), 'characters': sum(lengths),
                       'min_chars': min(lengths), 'median_chars': lengths[len(lengths)//2],
                       'max_chars': max(lengths), 'embedding_seconds': embedding_seconds,
                       'chunking_seconds': chunking_seconds, 'store_seconds': store_seconds,
                       'ingest_seconds': chunking_seconds + embedding_seconds + store_seconds,
                       'idempotence': {'passed': True, 'before': len(before), 'after': len(after), 'content_and_vector_hashes_equal': True},
                       'paid_api_cost_usd': 0, 'electricity_cost': 'not measured',
                       'embedding_reused_from': 'B' if name == 'C' else None}
        path = RESULTS / f'chunks/{name}.jsonl'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(''.join(json.dumps(asdict(c), ensure_ascii=False)+'\n' for c in chunks), encoding='utf-8')
        for page in pages:
            if page.page not in config['coherence_sample']['pages']:
                continue
            position = page.text.index('\n') + 1 if '\n' in page.text else 0
            chunk = next(c for c in chunks if c.page == page.page and c.metadata['char_start'] <= position < c.metadata['char_end'])
            samples.append({'strategy': name, 'page': page.page, 'position': position,
                            'chunk_id': chunk.chunk_id, 'text': chunk.text,
                            'score': None, 'reason': '', 'reviewer': None})
    assert [c.chunk_id for c in all_chunks['B']] == [c.chunk_id for c in all_chunks['C']]
    save(RESULTS / 'audit/coherence_samples.json', samples)
    versions = {p: importlib.metadata.version(p) for p in ['torch', 'sentence-transformers', 'transformers', 'pypdf', 'psycopg', 'numpy']}
    save(RESULTS / 'ingestion.json', {'created_at': stamp(), 'fingerprint': fingerprint(),
        'config': config, 'strategies': stats, 'database': store.versions(),
        'python': platform.python_version(), 'libraries': versions, 'device': 'cpu', 'threads': 4,
        'model_dimensions': model.dimensions, 'max_observed_input_tokens': model.max_observed_tokens,
        'total_wall_seconds_including_model_load_and_reingest': time.perf_counter()-start})
    print(json.dumps(stats, indent=2), flush=True)


def check_fingerprint(record):
    if record['fingerprint'] != fingerprint():
        raise RuntimeError('Inputs/code changed since ingestion/freeze; cannot report as the same experiment')


def evaluate(split, config, store):
    ingestion = read(RESULTS / 'ingestion.json')
    check_fingerprint(ingestion)
    if split == 'dev' and (RESULTS / 'selection.json').exists():
        raise RuntimeError('Dev run frozen; do not overwrite')
    if split == 'test':
        selection = read(RESULTS / 'selection.json')
        check_fingerprint(selection)
        if hashlib.sha256((RESULTS / 'dev_metrics.json').read_bytes()).hexdigest() != selection['dev_metrics_sha256']:
            raise RuntimeError('Dev metrics changed after freeze')
    if (RESULTS / f'{split}_traces.json').exists():
        raise RuntimeError(f'Refusing to overwrite {split} traces')
    qs = [q for q in read(ROOT / 'benchmark/questions.json') if q['split'] == split]
    model = embedder(config)
    traces = []
    for q in qs:
        tick = time.perf_counter()
        vector = model.embed_query(q['question'])
        query_seconds = time.perf_counter()-tick
        for strategy, params in config['strategies'].items():
            filters = q.get('filter') if params['filter'] else None
            tick = time.perf_counter()
            hits = store.search(strategy, vector, filters=filters)
            elapsed = time.perf_counter()-tick
            traces.append({**evaluate_query(q, hits), 'strategy': strategy,
                           'applied_filter': filters, 'query_embedding_seconds': query_seconds,
                           'retrieval_seconds': elapsed, 'evaluated_at': stamp()})
    save(RESULTS / f'{split}_traces.json', traces)
    save(RESULTS / f'{split}_metrics.json', summarize(traces))
    print(json.dumps(summarize(traces), indent=2), flush=True)


def freeze(config):
    if (RESULTS / 'selection.json').exists() or (RESULTS / 'test_traces.json').exists():
        raise RuntimeError('Already frozen or test already evaluated')
    ingestion = read(RESULTS / 'ingestion.json')
    check_fingerprint(ingestion)
    metrics = read(RESULTS / 'dev_metrics.json')
    ordered = sorted(metrics, key=lambda x: (-x['hit3'], -x['hit1'],
        ingestion['strategies'][x['strategy']]['ingest_seconds']+x['retrieval_seconds'], x['strategy']))
    save(RESULTS / 'selection.json', {'frozen_at': stamp(), 'fingerprint': fingerprint(),
         'criterion': config['selection_order'], 'selected_strategy': ordered[0]['strategy'],
         'ranking_on_dev': ordered, 'test_results_seen': False,
         'dev_metrics_sha256': hashlib.sha256((RESULTS / 'dev_metrics.json').read_bytes()).hexdigest()})
    print('Frozen selection based only on dev:', ordered[0]['strategy'], flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['ingest', 'dev', 'freeze', 'test'])
    args = parser.parse_args()
    load_dotenv(ROOT / 'starter/.env')
    config = read(ROOT / 'starter/experiment.json')
    url = os.environ.get('DATABASE_URL', 'postgresql://day6@127.0.0.1:55433/day6_lab')
    store = PgVectorStore(url, config['dimensions'])
    try:
        if args.stage == 'ingest':
            ingest(config, store)
        elif args.stage == 'freeze':
            freeze(config)
        else:
            evaluate(args.stage, config, store)
    except Exception as exc:
        save(RESULTS / f'{args.stage}_failure.json', {'at': stamp(), 'type': type(exc).__name__,
             'message': str(exc).replace(url, '[DATABASE_URL]')})
        raise


if __name__ == '__main__':
    main()
