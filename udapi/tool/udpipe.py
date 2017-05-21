"""Wrapper for UDPipe (more pythonic than ufal.udpipe)."""
import io

from ufal.udpipe import Model, Pipeline, ProcessingError, Sentence  # pylint: disable=no-name-in-module
from udapi.core.resource import require_file
from udapi.block.read.conllu import Conllu as ConlluReader


class UDPipe:
    """Wrapper for UDPipe (more pythonic than ufal.udpipe)."""

    def __init__(self, model):
        """Create the UDPipe tool object."""
        self.model = model
        path = require_file(model)
        self.tool = Model.load(path)
        if not self.tool:
            raise IOError("Cannot load model from file '%s'" % path)
        self.error = ProcessingError()
        self.conllu_reader = ConlluReader()
        self.tokenizer = self.tool.newTokenizer(Model.DEFAULT)

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
        # for node, parsed_node in zip(root.descendants, parsed_root.descendants):
        #    parsed_node.misc = node.misc
        # pylint: disable=protected-access
        #root._children, root._descendants = parsed_root._children, parsed_root._descendants

    def tokenize_tag_parse_tree(self, root):
        """Tokenize, tag (+lemmatize, fill FEATS) and parse the text stored in `root.text`."""
        if root.children:
            raise ValueError('Tree already contained nodes before tokenization')

        # tokenization (I cannot turn off segmenter, so I need to join the segments)
        self.tokenizer.setText(root.text)
        u_sentence = Sentence()
        is_another = self.tokenizer.nextSentence(u_sentence)
        u_words = u_sentence.words
        n_words = u_words.size() - 1
        if is_another:
            u_sent_cont = Sentence()
            while self.tokenizer.nextSentence(u_sent_cont):
                n_cont = u_sent_cont.words.size() - 1
                for i in range(1, n_cont + 1):
                    u_w = u_sent_cont.words[i]
                    n_words += 1
                    u_w.id = n_words
                    u_words.append(u_w)

        # tagging and parsing
        self.tool.tag(u_sentence, Model.DEFAULT)
        self.tool.parse(u_sentence, Model.DEFAULT)

        # converting UDPipe nodes to Udapi nodes
        heads, nodes = [], [root]
        for i in range(1, u_words.size()):
            u_w = u_words[i]
            node = root.create_child(
                form=u_w.form, lemma=u_w.lemma, upos=u_w.upostag,
                xpos=u_w.xpostag, feats=u_w.feats, deprel=u_w.deprel,
            )
            node.misc = u_w.misc
            heads.append(u_w.head)
            nodes.append(node)
        for node in nodes[1:]:
            head = heads.pop(0)
            node.parent = nodes[head]
