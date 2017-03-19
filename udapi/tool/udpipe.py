'''Wrapper for UDPipe (more pythonic than ufal.udpipe).'''
import io
import os

from ufal.udpipe import Model, Pipeline, ProcessingError # pylint: disable=no-name-in-module
from udapi.block.read.conllu import Conllu as ConlluReader

class UDPipe:
    '''Wrapper for UDPipe (more pythonic than ufal.udpipe).'''

    def __init__(self, model):
        """Create the UDPipe tool object."""
        self.model = model
        path = self.model_path()
        self.tool = Model.load(path)
        if not self.tool:
            raise IOError("Cannot load model from file '%s'" % path)
        self.error = ProcessingError()
        self.conllu_reader = ConlluReader()

    def model_path(self):
        """Return absolute path to the model file to be loaded."""
        if self.model.startswith('/') or self.model.startswith('.'):
            return self.model
        elif os.environ.get('UDAPI_DATA'):
            return os.environ['UDAPI_DATA'] + '/' + self.model
        else:
            return os.environ.get('HOME') + '/' + self.model

    def tag_parse_tree(self, root):
        """Tag (+lemmatize, fill FEATS) and parse a tree (already tokenized)."""
        pipeline = Pipeline(self.tool, 'horizontal', Pipeline.DEFAULT, Pipeline.DEFAULT, 'conllu')
        in_data = " ".join([n.form for n in root.descendants])
        out_data = pipeline.process(in_data, self.error)
        if self.error.occurred():
            raise IOError("UDPipe error " + self.error.message)
        self.conllu_reader.files.filehandle = io.StringIO(out_data)
        parsed_root = self.conllu_reader.read_tree()
        nodes = [root] + root.descendants
        for parsed_node in parsed_root.descendants:
            node = nodes[parsed_node.ord]
            node.parent = nodes[parsed_node.parent.ord]
            for attr in 'upos xpos lemma feats'.split():
                setattr(node, attr, getattr(parsed_node, attr))

        # TODO: benchmark which solution is the fastest one. E.g. we could also do
        #for node, parsed_node in zip(root.descendants, parsed_root.descendants):
        #    parsed_node.misc = node.misc
        ## pylint: disable=protected-access
        #root._children, root._descendants = parsed_root._children, parsed_root._descendants
