#!/usr/bin/env python3

import unittest
from udapi.core.document import Document


class TestDocument(unittest.TestCase):

    def test_init(self):
        doc = Document()

    def test_iterator(self):
        doc = Document()
        doc.bundles = ['a', 'b', 'c']
        for bundle in doc:
            print(bundle)


if __name__ == "__main__":
    unittest.main()
