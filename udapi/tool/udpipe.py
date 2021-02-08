"""Wrapper for UDPipe (more pythonic than ufal.udpipe)."""
import io
import sys

from ufal.udpipe import Model, Pipeline, ProcessingError, Sentence  # pylint: disable=no-name-in-module
from udapi.core.resource import require_file
from udapi.block.read.conllu import Conllu as ConlluReader
from udapi.core.root import Root


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
        descendants = root.descendants
        if not descendants:
            return
        pipeline = Pipeline(self.tool, 'horizontal', Pipeline.DEFAULT, Pipeline.DEFAULT, 'conllu')
        in_data = " ".join([n.form for n in descendants])
        out_data = pipeline.process(in_data, self.error)
        if self.error.occurred():
            raise IOError("UDPipe error " + self.error.message)
        self.conllu_reader.files.filehandle = io.StringIO(out_data)
        parsed_root = self.conllu_reader.read_tree()
        nodes = [root] + descendants
        for parsed_node in parsed_root.descendants:
            node = nodes[parsed_node.ord]
            node.parent = nodes[parsed_node.parent.ord]
            for attr in 'upos xpos lemma feats deprel'.split():
                setattr(node, attr, getattr(parsed_node, attr))

        # TODO: benchmark which solution is the fastest one. E.g. we could also do
        # for node, parsed_node in zip(root.descendants, parsed_root.descendants):
        #    parsed_node.misc = node.misc
        # pylint: disable=protected-access
        #root._children, root._descendants = parsed_root._children, parsed_root._descendants

    def tokenize_tag_parse_tree(self, root, resegment=False, tag=True, parse=True):
        """Tokenize, tag (+lemmatize, fill FEATS) and parse the text stored in `root.text`.

        If resegment=True, the returned list of Udapi trees may contain multiple trees.
        """
        if root.children:
            raise ValueError('Tree already contained nodes before tokenization')

        # Tokenize and segment the text (segmentation cannot be turned off in older UDPipe versions).
        self.tokenizer.setText(root.text)
        is_another = True
        u_sentences = []
        while is_another:
            u_sentence = Sentence()
            is_another = self.tokenizer.nextSentence(u_sentence)
            if is_another:
                u_sentences.append(u_sentence)

        # If resegmentation was not required, we need to join the segments.
        if not resegment and len(u_sentences) > 1:
            first_sent = u_sentences[0]
            n_words = first_sent.words.size() - 1
            for other_sent in u_sentences[1:]:
                other_words = other_sent.words.size() - 1
                for i in range(1, other_words + 1):
                    u_w = other_sent.words[i]
                    n_words += 1
                    u_w.id = n_words
                    first_sent.words.append(u_w)
            u_sentences = [first_sent]

        # tagging and parsing
        if tag:
            for u_sentence in u_sentences:
                self.tool.tag(u_sentence, Model.DEFAULT)
                if parse:
                    self.tool.parse(u_sentence, Model.DEFAULT)
        elif parse:
            raise ValueError('Combination parse=True tag=False is not allowed.')

        # converting UDPipe nodes to Udapi nodes
        new_root = root
        trees = []
        for u_sentence in u_sentences:
            if not new_root:
                new_root = Root()
            new_root.text = u_sentence.getText() if resegment else root.text
            heads, nodes = [], [new_root]
            u_words = u_sentence.words
            for i in range(1, u_words.size()):
                u_w = u_words[i]
                node = new_root.create_child(
                    form=u_w.form, lemma=u_w.lemma, upos=u_w.upostag,
                    xpos=u_w.xpostag, feats=u_w.feats, deprel=u_w.deprel, misc=u_w.misc,
                )
                if parse:
                    heads.append(u_w.head)
                    nodes.append(node)
            if parse:
                for node in nodes[1:]:
                    head = heads.pop(0)
                    node.parent = nodes[head]
            trees.append(new_root)
            new_root = None
        return trees

    def segment_text(self, text):
        """Segment the provided text into sentences."""
        self.tokenizer.setText(text)
        is_another = True
        sentences = []
        while is_another:
            u_sentence = Sentence()
            is_another = self.tokenizer.nextSentence(u_sentence)
            if is_another:
                sentences.append(u_sentence.getText())
        return sentences
