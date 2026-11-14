"""Opt-in real pgvector test; uses only a dedicated test strategy."""
import os
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / '.runtime/python'))
from src.models import Chunk
from src.store import PgVectorStore


@unittest.skipUnless(os.environ.get('RUN_PGVECTOR_TESTS') == '1', 'Set RUN_PGVECTOR_TESTS=1 for a real local database')
class StoreIntegrationTests(unittest.TestCase):
    def test_changed_snapshot_filter_and_rollback(self):
        store = PgVectorStore(os.environ.get('DATABASE_URL', 'postgresql://day6@127.0.0.1:55433/day6_lab'), 384)
        name = '__integration_test__'
        v = [1.0] + [0.0] * 383
        a = Chunk('old', 'test', 'test.pdf', 1, 'Old text', {'section': 'old'})
        b = Chunk('new', 'test', 'test.pdf', 2, 'New text', {'section': 'new'})
        try:
            store.upsert(name, [a], [v])
            store.upsert(name, [b], [v])
            self.assertEqual([r['chunk_id'] for r in store.snapshot(name)], ['new'])
            self.assertEqual(store.search(name, v, filters={'section': 'old'}), [])
            self.assertEqual(store.search(name, v, filters={'section': 'new'})[0]['chunk_id'], 'new')
            with self.assertRaises(ValueError):
                store.upsert(name, [a], [[1.0]])
            self.assertEqual([r['chunk_id'] for r in store.snapshot(name)], ['new'])
            with self.assertRaises(ValueError):
                store.search(name, v, filters={'unsafe_field': 'value'})
            self.assertEqual(PgVectorStore(store.database_url, 384).snapshot(name), store.snapshot(name))
        finally:
            with store.connect() as conn:
                conn.execute('DELETE FROM day6_chunks WHERE strategy=%s', (name,))
