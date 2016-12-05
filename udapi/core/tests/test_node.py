#!/usr/bin/env python

import unittest

from udapi.core.node import Node


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

if __name__ == "__main__":
    unittest.main() 
