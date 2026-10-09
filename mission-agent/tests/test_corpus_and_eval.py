"""Local checks. Run: python3 -m unittest discover mission-agent/tests"""
import csv
import pathlib
import re
import unittest

D = pathlib.Path(__file__).resolve().parent.parent / "data"


def rows(name):
    with open(D / name, newline="") as f:
        return list(csv.DictReader(f))


class CorpusTests(unittest.TestCase):
    def setUp(self):
        self.c = rows("nist_chunks.csv")

    def test_ids_unique_and_shaped(self):
        ids = [x["chunk_id"] for x in self.c]
        self.assertEqual(len(ids), len(set(ids)))
        for x in self.c:
            self.assertRegex(x["chunk_id"], r"^[A-Za-z0-9.\-]+-p\d+-\d+$")

    def test_three_documents_with_pages(self):
        self.assertEqual({x["doc_id"] for x in self.c}, {"CSF2", "SP800-61r3", "SP800-37r2"})
        for x in self.c:
            self.assertGreater(int(x["page"]), 0)
            self.assertGreaterEqual(len(x["text"].split()), 40)


class EvalSetTests(unittest.TestCase):
    def test_shape(self):
        q = rows("eval_questions.csv")
        self.assertEqual(len(q), 32)
        cats = [x["category"] for x in q]
        self.assertEqual((cats.count("in_scope"), cats.count("out_of_scope"), cats.count("adversarial")), (24, 6, 2))
        docs = {x["doc_id"] for x in rows("nist_chunks.csv")}
        for x in q:
            if x["category"] == "in_scope":
                self.assertIn(x["gold_doc"], docs)
                self.assertTrue(x["must_contain"])

    def test_citation_pattern_matches_chunk_ids(self):
        pat = re.compile(r"\[([A-Za-z0-9.\-]+-p\d+-\d+)\]")
        cid = rows("nist_chunks.csv")[0]["chunk_id"]
        self.assertEqual(pat.findall(f"Claim [{cid}] and [not-a-citation]."), [cid])


if __name__ == "__main__":
    unittest.main()
