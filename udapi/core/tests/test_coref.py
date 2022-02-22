#!/usr/bin/env python3

import os
import unittest
import udapi
from udapi.block.read.conllu import Conllu as ConlluReader


class TestCoref(unittest.TestCase):

    def test_load(self):
        data_filename = os.path.join(os.path.dirname(__file__), 'data', 'fr-democrat-dev-sample.conllu')
        reader = ConlluReader(files=data_filename, split_docs=True)
        docs = reader.read_documents()
        self.assertEqual(len(docs), 2)
        docs[-1].draw()
        coref_entities = list(docs[-1].coref_clusters.values())
        self.assertEqual(len(coref_entities), 1)
        self.assertEqual(coref_entities[0].cluster_id, 'e36781')


if __name__ == "__main__":
    unittest.main()
