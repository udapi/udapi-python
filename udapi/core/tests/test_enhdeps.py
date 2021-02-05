import unittest
import os
import udapi

from udapi.core.root import Root
from udapi.core.node import Node, find_minimal_common_treelet
from udapi.core.document import Document
from udapi.block.read.conllu import Conllu as ConlluReader
from udapi.block.write.conllu import Conllu as ConlluWriter


class TestEnhDeps(unittest.TestCase):
    """Unit tests for udapi.core.node and enhanced dependecies.
    Tests the behaviour with empty nodes (with decimal ord, such as 0.1, 2.3 etc.) as well"""

    @classmethod
    def setUpClass(cls):
        cls.doc = Document()
        cls.data = os.path.join(os.path.dirname(udapi.__file__), "core", "tests", "data", "enh_deps.conllu")
        cls.doc.load_conllu(cls.data)
        cls.tree = cls.doc.bundles[0].get_tree()
        cls.nodes = cls.tree.descendants
        cls.add_empty_node(cls.tree, 3)

    @staticmethod
    def add_empty_node(tree, ord_before, decimal=1):
        """Add an empty node to tree after the node with index `ord_before`.
        Empty node will receive ord=`ord_before`.`decimal`"""
        e = tree.create_empty_child()
        e.ord = float('{}.{}'.format(ord_before, decimal))
        e.form = "E{}".format(e.ord)

    def test_datapath(self):
        self.assertTrue(os.path.isfile(self.data))

    def test_nodes(self):
        self.assertEqual(6, len(self.nodes))

    def test_ord_type(self):
        self.assertIsNot(str, type(self.nodes[0].ord))

    def test_create_empty(self):
        writer = ConlluWriter()
        writer.apply_on_document(self.doc)
        # self.tree.draw()
        self.assertGreater(len(self.tree.empty_nodes), 0)

    def test_regular_deps(self):

        n = self.nodes[0]
        self.assertEqual("0:root|2:amod", n.raw_deps)

    def test_create_deps2empty(self):
        e = self.tree.empty_nodes[0]
        h = self.nodes[1]
        d = self.nodes[5]
        e.deps.append({'parent': h, 'deprel':'dep:e2h'})
        d.deps.append({'parent': e, 'deprel': 'dep:d2e'})
        self.assertEqual("2:dep:e2h", e.raw_deps, )
        self.assertEqual("5:conj|3.1:dep:d2e", d.raw_deps)
        self.assertEqual(self.tree.descendants_and_empty, self.nodes[:3] + [e] + self.nodes[3:])


