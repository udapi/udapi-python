#!/usr/bin/env python

import codecs
import re

from udapi.core.node import Node
from udapi.core.root import Root
from udapi.core.bundle import Bundle

from udapi.block.read.conllu import Conllu as ConlluReader

class Document(object):

    """Document is a container for Universal Dependency trees"""

    attrnames = ["ord", "form", "lemma", "upostag", "xpostag", "feats", "head", "deprel", "deps", "misc"]
    # ZZ: TODO: poresit tolerovani jeho absence misc
    # MP: Proc, kdyz je to povinny atribut dle http://universaldependencies.org/format.html ?
    # "If the MISC field is not used, it should contain an underscore."

    bundles = []

    def __init__(self):
        self.bundles = []

    def __iter__(self):
        return iter(self.bundles)

    def create_bundle(self):
        bundle = Bundle()
        self.bundles.append(bundle)
        bundle.number = len(self.bundles)
        return bundle

    def load_conllu(self,filename):
        reader = ConlluReader({'filename':filename})
        reader.process_document(self)

    def storex(self,args):

        try:
            fh = args['filehandle']
        except:
            filename = args['filename']
            fh = codecs.open(filename,'w','utf-8')

        for bundle in self:
            for root in bundle:
                # Skip empty sentences (no nodes, just a comment). They are not allowed in CoNLL-U.
                if root.descendants():
                    fh.write(root._aux['comment'])

                    for node in root.descendants():

                        values = [ getattr(node,attrname) for attrname in Document.attrnames ]
                        values[0] = str(values[0]) # ord

                        try:
                            values[6] = str(node.parent.ord)
                        except:
                            values[6] = '0'

                        for index in range(0,len(values)):
                            if values[index] == None:
                                values[index] = ''

                        fh.write('\t'.join([value for value in values] ))
                        fh.write('\n')

                    fh.write("\n")

        fh.close()

    def store(self,args = {}):  # TODO: to je otazka, jestli by ten ukladaci kod nemel byt spis v Document, at nema core zavislost na blocich

        from udapi.block.write.conllu import Conllu
        writer = Conllu()
        writer.process_document(self)
