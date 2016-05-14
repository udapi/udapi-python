#!/usr/bin/env python

import codecs
import re

from udapi.core.node import Node
from udapi.core.root import Root
from udapi.core.bundle import Bundle

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

    def load(self,args):

        fh = None

        try:
            fh = args['filehandle']
        except:
            filename = args['filename']
            fh = open(filename, 'r')

        fh = codecs.getreader('utf8')(fh)

        nodes = []
        comment = ''

        for line in fh:

            if re.search('^#',line):
                comment = comment + line

            elif re.search('^\d+\-',line):  # HACK: multiword tokens temporarily avoided
                pass

            elif line.strip():

                if not nodes:
                    bundle = Bundle()
                    self.bundles.append(bundle)
                    root = Root() # TODO: nahradit bundle.create_tree, az bude odladene
                    root._aux['comment'] = comment # TODO: ulozit nekam poradne
                    nodes = [root]
                    bundle.trees.append(root)

                columns = line.strip().split('\t')

                node = Node()
                nodes.append(node)

                for index in xrange(0,len(Document.attrnames)):
                    setattr( node, Document.attrnames[index], columns[index] )

                try:  # TODO: kde se v tomhle sloupecku berou podtrzitka
                    node.head = int(node.head)
                except ValueError:
                    node.head = 0

                try:   # TODO: poresit multitokeny
                    node.ord = int(node.ord)
                except ValueError:
                    node.ord = 0


            else: # an empty line is guaranteed even after the last sentence in a conll-u file

                nodes[0]._aux['descendants'] = nodes[1:]

                for node in nodes[1:]:

                    node.set_parent( nodes[node.head] )

                nodes = []
                comment = ''


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
