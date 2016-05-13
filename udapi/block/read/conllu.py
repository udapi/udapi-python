from udapi.core.basereader import BaseReader
from udapi.core.document import Document
from udapi.core.bundle import Bundle
from udapi.core.node import Node
from udapi.core.root import Root
import codecs
import re

class Conllu(BaseReader):

    def __init__( self, args = {} ):

        self.finished = False # TODO: this should be invoked from the parent class

        self.bundles_per_document = float("inf")

        if 'bundles_per_document' in args:
            self.bundles_per_document = int(args['bundles_per_document'])

        self.filehandle = None

        if 'filehandle' in args:
            self.filehandle = args['filehandle']

        elif 'filename' in args:
            self.filename = args['filename']
            self.filehandle = open(self.filename, 'r')

        else:
            print str(self) + " has no file to read from"

        self.filehandle = codecs.getreader('utf8')(self.filehandle)


    def process_document( self, document ):

        number_of_loaded_bundles = 0

        nodes = []
        comment = ''

        while number_of_loaded_bundles < self.bundles_per_document:

            # TODO: more or less cut'n'paste from document.py (in which it should be deleted)

            line = self.filehandle.readline()
            if line == '': # EOF
                self.finished = True
                return
                # TODO: the last processed bundle should be finished at this point (because of the guaranteed empty line), but it should be checked


            if re.search('^#',line):
                comment = comment + line

            elif re.search('^\d+\-',line):  # HACK: multiword tokens temporarily avoided                                                                                         
                pass

            elif line.strip():

                if not nodes:
                    bundle = Bundle()
                    document.bundles.append(bundle)
                    root = Root()

                    root._aux['comment'] = comment # TODO: ulozit nekam poradne
                    nodes = [root]
                    bundle.trees.append(root)
                    root._bundle = bundle

                columns = line.strip().split('\t')

                node = Node()
                nodes.append(node)

                columns.append(None)  # TODO: why was the last column missing in some files?

                for index in xrange(0,len(Document.attrnames)):
                    setattr( node, Document.attrnames[index], columns[index] )


                try:  # TODO: kde se v tomhle sloupecku berou podtrzitka
                    node.head = int(node.head)
                except ValueError:
                    node.head = 0

                try:   # TODO: poresit multitokeny
                    node.ord = int(node.ord)
                except ValueError:
                    pass # node.ord = 0                        


            else: # an empty line is guaranteed even after the last sentence in a conll-u file

                if len(nodes) == 0:
                    print "Warning: this is weird: probably two empty lines following each other" # TODO: resolve
                else:
#                    print "QQQ A tree completed, tree number "+str(number_of_loaded_bundles)
                    number_of_loaded_bundles += 1
                    nodes[0]._aux['descendants'] = nodes[1:]
                    for node in nodes[1:]:
                        node.set_parent( nodes[node.head] )
                    nodes = []
                    comment = ''

        return document
