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
        coref_entities = docs[-1].coref_entities
        self.assertEqual(len(coref_entities), 1)
        self.assertEqual(coref_entities[0].eid, 'e36781')

    def test_edits(self):
        data_filename = os.path.join(os.path.dirname(__file__), 'data', 'fr-democrat-dev-sample.conllu')
        doc = udapi.Document(data_filename)
        first_node = next(doc.nodes)
        second_node = first_node.next_node
        new_entity = doc.create_coref_entity(etype='person')
        self.assertEqual(new_entity.etype, 'person')
        self.assertEqual(len(new_entity.mentions), 0)
        m1 = new_entity.create_mention(words=[first_node]) # head will be automatically set to words[0]
        self.assertEqual(len(new_entity.mentions), 1)
        self.assertEqual(m1, new_entity.mentions[0])
        self.assertEqual(m1.entity, new_entity)
        self.assertEqual(m1.head, first_node)
        self.assertEqual(m1.words, [first_node])
        self.assertEqual(m1.span, '1')
        m1.words = [second_node, first_node, first_node] # intentional duplicates and wrong order
        self.assertEqual(m1.words, [first_node, second_node])
        self.assertEqual(m1.span, '1-2')
        m1.head = second_node
        self.assertEqual(m1.head, second_node)
        m2 = new_entity.create_mention(head=second_node, span='1-3') # mention.words will be filled according to the span
        self.assertEqual(len(new_entity.mentions), 2)
        self.assertEqual(new_entity.mentions[0], m2) # 1-3 should go before 1-2
        self.assertEqual(new_entity.mentions[1], m1)
        self.assertTrue(m2 < m1)
        self.assertEqual(m2.words, [first_node, second_node, second_node.next_node])


if __name__ == "__main__":
    unittest.main()
