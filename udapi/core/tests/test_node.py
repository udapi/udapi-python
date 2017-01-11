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

    def test_topology(self):
        doc = Document()
        data_filename = os.path.join(os.path.dirname(__file__), 'data', 'enh_deps.conllu')
        doc.load_conllu(data_filename)
        self.assertEqual(len(doc.bundles), 1)
        root = doc.bundles[0].get_tree()
        nodes = root.descendants
        nodes2 = root.descendants()
        # descendants() and descendants should return the same sequence of nodes
        self.assertEqual(nodes, nodes2)
        self.assertEqual(len(nodes), 6)
        self.assertEqual(nodes[1].parent, root)
        self.assertEqual(nodes[2].root, root)
        self.assertEqual(len(nodes[1].descendants), 5)
        self.assertEqual(len(nodes[1].children), 3)
        self.assertEqual(len(nodes[1].children(add_self=True)), 4)
        self.assertEqual(len(nodes[1].children(add_self=1, following_only=1)), 3)

        self.assertEqual(nodes[0].next_node, nodes[1])
        # TODO fix
        #self.assertEqual(nodes[2].prev_node, nodes[1])
        self.assertEqual(nodes[5].next_node, None)
        self.assertEqual(root.prev_node, None)


        # ords and reorderings
        self.assertEqual([node.ord for node in nodes], [1, 2, 3, 4, 5, 6])
        # TODO: fix
        #nodes[0].shift_after_node(nodes[1])
        #self.assertEqual([node.ord for node in nodes], [2, 1, 3, 4, 5, 6])
        #self.assertEqual([node.ord for node in root.descendants()], [1, 2, 3, 4, 5, 6])

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
        data_filename = os.path.join(os.path.dirname(__file__), 'data', 'enh_deps.conllu')

        # Read a test CoNLLU file.
        document = Document()
        reader = Conllu(files=data_filename)
        reader.process_document(document)

        # Exactly one bundle should be loaded.
        self.assertEqual(len(document.bundles), 1)

        # Obtain the dependency tree and check its sentence ID.
        root = document.bundles[0].get_tree()
        self.assertEqual(root.bundle.bundle_id, 'a-mf920901-001-p1s1A')

        # Check raw secondary dependencies for each node.
        nodes = root.descendants()
        self.assertEqual(nodes[0].raw_deps, '0:root|2:amod')
        self.assertEqual(nodes[1].raw_deps, '0:root')
        self.assertEqual(nodes[2].raw_deps, '0:root')
        self.assertEqual(nodes[3].raw_deps, '0:root')
        self.assertEqual(nodes[4].raw_deps, '1:amod')
        self.assertEqual(nodes[5].raw_deps, '5:conj')

        # Check deserialized dependencies.
        self.assertEqual(nodes[0].deps[0]['parent'], root)
        self.assertEqual(nodes[0].deps[0]['deprel'], 'root')
        self.assertEqual(nodes[5].deps[0]['parent'], nodes[4])

    def test_deps_setter(self):
        """
        Test the deserialization of the secondary dependencies.

        """
        # Create a sample dependency tree.
        root = Root()
        for i in range(3):
            root.create_child()

        nodes = root.descendants()
        nodes[0].deps.append({'parent': nodes[1], 'deprel': 'test'})

        self.assertEqual(nodes[0].raw_deps, '2:test')

if __name__ == "__main__":
    unittest.main()
