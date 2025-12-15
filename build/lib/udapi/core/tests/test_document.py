#!/usr/bin/env python3

import unittest
from udapi.core.document import Document


class TestDocument(unittest.TestCase):

    def test_init(self):
        doc = Document()

    def test_ids(self):
        doc = Document()
        bundle1 = doc.create_bundle()
        bundle2 = doc.create_bundle()
        self.assertEqual(bundle1.address(), "1")
        self.assertEqual(bundle2.address(), "2")
        self.assertEqual([b.bundle_id for b in doc], ["1", "2"])
        tree1 = bundle1.create_tree()
        self.assertEqual(tree1.address(), "1")

if __name__ == "__main__":
    unittest.main()
