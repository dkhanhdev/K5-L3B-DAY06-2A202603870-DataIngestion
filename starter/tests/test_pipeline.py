"""Contract tests for evidence scoring and source-preserving chunk boundaries."""
import unittest
from src.chunking import fixed_size, by_paragraph
from src.evaluation import evaluate_query
from src.models import DocumentPage


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.page = DocumentPage('d', 'file.pdf', 75,
            'Heading\nA sentence that must remain traceable.\nAnother longer sentence.\n\n• A bullet with context.',
            {'section': 's'})

    def test_all_source_characters_retained_with_offsets_and_metadata(self):
        for chunks in [fixed_size(self.page, 25, 5), by_paragraph(self.page, 35)]:
            covered = set()
            for c in chunks:
                start, end = c.metadata['char_start'], c.metadata['char_end']
                self.assertEqual(c.text, self.page.text[start:end])
                self.assertEqual((c.page, c.metadata['section']), (75, 's'))
                covered.update(range(start, end))
            self.assertEqual(covered, set(range(len(self.page.text))))
        self.assertEqual(fixed_size(self.page, 25, 5), fixed_size(self.page, 25, 5))

    def test_invalid_overlap_rejected(self):
        with self.assertRaises(ValueError):
            fixed_size(self.page, 20, 20)

    def test_same_page_without_full_evidence_is_not_a_hit(self):
        q = {'gold_source_id': 'd', 'gold_page': 75, 'evidence_quote': 'Full evidence including a condition.'}
        hit = {'document_id': 'd', 'page': 75, 'text': 'Full evidence'}
        self.assertFalse(evaluate_query(q, [hit])['hit3'])
        hit['text'] = 'Full evidence\nincluding a condition.'
        self.assertTrue(evaluate_query(q, [hit])['hit1'])
        hit['page'] = 76
        self.assertFalse(evaluate_query(q, [hit])['hit3'])

    def test_documented_alternative_evidence_accepted(self):
        q = {'gold_source_id': 'd', 'gold_page': 75, 'evidence_quote': 'Original evidence',
             'alternative_gold': [{'source_id': 'd', 'page': 77, 'evidence_quote': 'Equivalent evidence'}]}
        self.assertTrue(evaluate_query(q, [{'document_id': 'd', 'page': 77, 'text': 'Equivalent evidence'}])['hit3'])


if __name__ == '__main__':
    unittest.main()
