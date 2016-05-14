#!/usr/bin/env python

import unittest
from udapi.core.document import Document

class TestDocument(unittest.TestCase):

    def test_init(self):
        doc = Document()

    def test_iterator(self):
        doc = Document()
        doc.bundles = ['a','b','c']
        for bundle in doc:
            print bundle

    def test_load_and_store(self):
        doc = Document()
        doc.load_conllu('UD_Czech_sample.conllu')
        doc.store({'filename':'temp_copy.connlu'})
        



if __name__ == "__main__":
    unittest.main() 
