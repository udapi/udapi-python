#!/usr/bin/env python3

import unittest

from udapi.core.root import Root
from udapi.core.node import Node


class TestEffectives(unittest.TestCase):
    def test_eparents(self):
        tree = Root()


if __name__ == "__main__":
    unittest.main()
