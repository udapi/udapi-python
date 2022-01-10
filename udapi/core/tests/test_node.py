#!/usr/bin/env python3
"""Unit tests for udapi.core.node."""
import io
import logging
import os
import sys
import unittest

from udapi.core.root import Root
from udapi.core.node import Node, find_minimal_common_treelet
from udapi.core.document import Document
from udapi.block.read.conllu import Conllu

logging.basicConfig(
    format='%(asctime)-15s [%(levelname)7s] %(funcName)s - %(message)s', level=logging.DEBUG)


class TestDocument(unittest.TestCase):
    """Unit tests for udapi.core.node."""

    def test_topology(self):
        """Test methods/properties descendants, children, prev_node, next_node, ord."""
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
        self.assertEqual(nodes[2].siblings, [nodes[0], nodes[3]])
        self.assertEqual(nodes[2].siblings(following_only=True), [nodes[3]])

        self.assertEqual(nodes[0].next_node, nodes[1])
        self.assertEqual(nodes[2].prev_node, nodes[1])
        self.assertEqual(nodes[5].next_node, None)
        self.assertEqual(root.prev_node, None)

        (common_ancestor, added_nodes) = find_minimal_common_treelet(nodes[0], nodes[1])
        self.assertEqual(common_ancestor, nodes[1])
        self.assertEqual(list(added_nodes), [])
        input_nodes = [nodes[2], nodes[4], nodes[5]]
        (common_ancestor, added_nodes) = find_minimal_common_treelet(*input_nodes)
        self.assertEqual(common_ancestor, nodes[1])
        self.assertEqual(list(added_nodes), [nodes[1], nodes[3]])

        # ords and reorderings
        self.assertEqual([node.ord for node in nodes], [1, 2, 3, 4, 5, 6])
        self.assertTrue(nodes[0].precedes(nodes[1]))
        self.assertTrue(nodes[0] < nodes[1])
        self.assertFalse(nodes[0] > nodes[1])
        self.assertTrue(nodes[0] <= nodes[0])
        nodes[0].shift_after_node(nodes[1])
        self.assertEqual([node.ord for node in nodes], [2, 1, 3, 4, 5, 6])
        self.assertEqual([node.ord for node in root.descendants()], [1, 2, 3, 4, 5, 6])

    def test_draw(self):
        """Test the draw() method, which uses udapi.block.write.textmodetrees."""
        doc = Document()
        data_filename = os.path.join(os.path.dirname(__file__), 'data', 'enh_deps.conllu')
        doc.load_conllu(data_filename)
        root = doc.bundles[0].get_tree()

        expected1 = ("# sent_id = a-mf920901-001-p1s1A\n"
                     "# text = Slovenská ústava: pro i proti\n"
                     "─┮\n"
                     " │ ╭─╼ Slovenská ADJ amod\n"
                     " ╰─┾ ústava NOUN root\n"
                     "   ┡─╼ : PUNCT punct\n"
                     "   ╰─┮ pro ADP appos\n"
                     "     ┡─╼ i CONJ cc\n"
                     "     ╰─╼ proti ADP conj\n"
                     "\n")
        expected2 = ("─┮\n"
                     " │ ╭─╼ Slovenská Case=Nom|Degree=Pos|Gender=Fem|Negative=Pos|Number=Sing _\n"
                     " ╰─┾ ústava Case=Nom|Gender=Fem|Negative=Pos|Number=Sing SpaceAfter=No\n"
                     "   ┡─╼ : _ _\n"
                     "   ╰─┮ pro AdpType=Prep|Case=Acc LId=pro-1\n"
                     "     ┡─╼ i _ LId=i-1\n"
                     "     ╰─╼ proti AdpType=Prep|Case=Dat LId=proti-1\n"
                     "\n")

        # test non-projective tree
        root3 = Root()
        for i in range(1, 5):
            root3.create_child(form=str(i))
        nodes = root3.descendants(add_self=1)
        nodes[1].parent = nodes[3]
        nodes[4].parent = nodes[2]
        expected3 = ("─┮\n"
                     " │ ╭─╼ 1\n"
                     " ┡─╪───┮ 2\n"
                     " ╰─┶ 3 │\n"
                     "       ╰─╼ 4\n"
                     "\n")

        try:
            sys.stdout = capture = io.StringIO()
            root.draw(color=False)
            self.assertEqual(capture.getvalue(), expected1)
            capture.seek(0)
            capture.truncate()
            root.draw(color=False, attributes='form,feats,misc',
                      print_sent_id=False, print_text=False)
            self.assertEqual(capture.getvalue(), expected2)
            capture.seek(0)
            capture.truncate()
            root3.draw(color=False, attributes='form', print_sent_id=0, print_text=0)
            self.assertEqual(capture.getvalue(), expected3)
        finally:
            sys.stdout = sys.__stdout__  # pylint: disable=redefined-variable-type

    def test_feats(self):
        """Test the morphological featrues."""
        node = Node(root=None)
        self.assertEqual(str(node.feats), '_')
        node.feats = ''
        self.assertEqual(str(node.feats), '_')
        node.feats = None
        self.assertEqual(str(node.feats), '_')
        node.feats = {}  # pylint: disable=redefined-variable-type
        self.assertEqual(str(node.feats), '_')

        node.feats = 'Mood=Ind|Person=1|Voice=Act'
        self.assertEqual(node.feats['Mood'], 'Ind')
        self.assertEqual(node.feats['Voice'], 'Act')
        self.assertEqual(node.feats['NonExistentFeature'], '')

        node.feats['Voice'] = 'Pas'
        self.assertEqual(str(node.feats), 'Mood=Ind|Person=1|Voice=Pas')
        self.assertEqual(node.feats, {'Mood': 'Ind', 'Person': '1', 'Voice': 'Pas'})
        self.assertEqual(node.feats['Voice'], 'Pas')
        self.assertEqual(node.feats['Mood'], 'Ind')
        self.assertEqual(node.feats['Person'], '1')

        node.feats = '_'
        self.assertEqual(str(node.feats), '_')
        self.assertEqual(node.feats, {})

    def test_deps_getter(self):
        """Test enhanced dependencies."""
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
        """Test the deserialization of enhanced dependencies."""
        # Create a sample dependency tree.
        root = Root()
        for _ in range(3):
            root.create_child()

        nodes = root.descendants()
        nodes[0].deps.append({'parent': nodes[1], 'deprel': 'test'})

        self.assertEqual(nodes[0].raw_deps, '2:test')

if __name__ == "__main__":
    unittest.main()
