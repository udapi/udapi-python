#!/usr/bin/env python3

from utreex.core.document import Document
import sys

doc = Document()

doc.load({'filehandle': sys.stdin})

bundle = doc.bundles[0]
tree = bundle.trees[0]
nodes = tree.descendants()
nodes[2].remove()

doc.store({'filehandle': sys.stdout})
