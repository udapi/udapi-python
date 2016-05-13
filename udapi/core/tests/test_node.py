#!/usr/bin/env python

import unittest

from udapi.core.node import Node

class TestDocument(unittest.TestCase):

    def test_init(self):
        node = Node()

    def test_parent(self):
        parent = Node()
        child = Node({"lemma":"prasopes"})
    
        self.assertEqual(child.lemma,"prasopes")

    def test_remove(self):
        pass


#    def test_iterator(self):
#        doc = Document();
#        doc.bundles = ['a','b','c']
#        for bundle in doc:
##            print bundle



if __name__ == "__main__":
    unittest.main() 
