#!/usr/bin/env python3

import os
import unittest
import logging

from udapi.core.root import Root
from udapi.core.node import Node
from udapi.core.document import Document
from udapi.block.read.conllu import Conllu

logging.basicConfig(
    format='%(asctime)-15s [%(levelname)7s] %(funcName)s - %(message)s', level=logging.DEBUG)


class TestDocument(unittest.TestCase):

    def test_feats_getter(self):
        """
        Test the deserialization of the morphological featrues.

        """
        node = Node()
        node.raw_feats = 'Mood=Ind|Negative=Pos|Number=Sing|Person=1|Tense=Pres|VerbForm=Fin|Voice=Act'
        self.assertEqual(node.feats['Mood'], 'Ind')
        self.assertEqual(node.feats['Negative'], 'Pos')
        self.assertEqual(node.feats['Number'], 'Sing')
        self.assertEqual(node.feats['Person'], '1')
        self.assertEqual(node.feats['Tense'], 'Pres')
        self.assertEqual(node.feats['VerbForm'], 'Fin')
        self.assertEqual(node.feats['Voice'], 'Act')

    def test_feats_setter(self):
        """
        Test the deserialization of the morphological featrues.

        """
        raw_feats = 'Mood=Ind|Negative=Pos|Number=Sing|Person=1|Tense=Pres|VerbForm=Fin|Voice=Act'
        expected_feats = 'Mood=Ind|Negative=Pos|Number=Sing|Person=1|Tense=Pres|VerbForm=Fin|Voice=Pas'

        node = Node()
        node.raw_feats = raw_feats
        node.feats['Voice'] = 'Pas'

        self.assertEqual(node.feats['Mood'], 'Ind')
        self.assertEqual(node.feats['Negative'], 'Pos')
        self.assertEqual(node.feats['Number'], 'Sing')
        self.assertEqual(node.feats['Person'], '1')
        self.assertEqual(node.feats['Tense'], 'Pres')
        self.assertEqual(node.feats['VerbForm'], 'Fin')
        self.assertEqual(node.feats['Voice'], 'Pas')
        self.assertEqual(node.raw_feats, expected_feats)

    def test_deps_getter(self):
        """
        Test the deserialization of the morphological featrues.

        """
        # Create a path to the test CoNLLU file.
        data_filename = os.path.join(os.path.dirname(
            __file__), 'data', 'secondary_dependencies.conllu')

        # Read a test CoNLLU file.
        document = Document()
        reader = Conllu({'filename': data_filename})
        reader.process_document(document)

        # Exactly one bundle should be loaded.
        self.assertEqual(len(document.bundles), 1)

        # Obtain the dependency tree and check its sentence ID.
        root_node = document.bundles[0].get_tree()
        self.assertEqual(root_node.sent_id, 'a-mf920901-001-p1s1A')

        # Check raw secondary dependencies for each node.
        nodes = root_node.descendants()
        self.assertEqual(nodes[0].raw_deps, '0:root|2:amod')
        self.assertEqual(nodes[1].raw_deps, '0:root')
        self.assertEqual(nodes[2].raw_deps, '0:root')
        self.assertEqual(nodes[3].raw_deps, '0:root')
        self.assertEqual(nodes[4].raw_deps, '1:amod')
        self.assertEqual(nodes[5].raw_deps, '5:conj')

        # Check deserialized dependencies.
        self.assertEqual(nodes[0].deps[0]['parent'], root_node)
        self.assertEqual(nodes[0].deps[0]['deprel'], 'root')
        self.assertEqual(nodes[5].deps[0]['parent'], nodes[4])

    def test_deps_setter(self):
        """
        Test the deserialization of the secondary dependencies.

        """
        # Create a sample dependency tree.
        root_node = Root()
        for i in range(3):
            root_node.create_child()

        nodes = root_node.descendants()
        nodes[0].deps.append({'parent': nodes[1], 'deprel': 'test'})

        self.assertEqual(nodes[0].raw_deps, '2:test')

if __name__ == "__main__":
    unittest.main()
