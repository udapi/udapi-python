from udapi.core.block import Block

import sys
import codecs
#sys.stdout = codecs.getwriter('utf-8')(sys.stdout, 'strict')

class Conllu(Block):

    attrnames = ["ord", "form", "lemma", "upostag", "xpostag", "feats", "head", "deprel", "deps", "misc"]


    def __init__( self, args = {} ):

        self.filehandle = None

        if 'filehandle' in args:
            self.filehandle = args['filehandle']

        elif 'filename' in args:
            self.filename = args['filename']

            self.filehandle = open(self.filename, 'w')

        else:
            print str(self) + " has no file to read from"

        self.filehandle = codecs.getwriter('utf8')(self.filehandle)


    def process_document( self, document ):

        fh = self.filehandle

        for bundle in document.bundles:

            tree_number = 0

            for root in bundle:
                # Skip empty sentences (no nodes, just a comment). They are not allowed in CoNLL-U.

                tree_number += 1
                if tree_number > 1:
                    fh.write("#UDAPI_BUNDLE_CONTINUES\n")

                if root.descendants():

                    try: # undefined comment allowed
                        fh.write(root._aux['comment'])
                    except:
                        pass

                    try:
                        fh.write('#UDAPI_ZONE=' + root.zone()+"\n")
                    except:
                        pass

                    for node in root.descendants():

                        values = [ getattr(node,attrname) for attrname in Conllu.attrnames ]
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
