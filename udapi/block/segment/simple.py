"""Block segment.Simple"""
from udapi.core.block import Block
from udapi.core.bundle import Bundle
import re

class Simple(Block):
    """"Heuristic segmenter, splits on sentence-final segmentation followed by uppercase."""

    @staticmethod
    def is_nonfinal_abbrev(token):
        """Is a given token an abbreviation (without the final period) which cannot end a sentence?"""
        if re.search('(např|e.g.)$', token):
            return True
        return False


    def is_boundary(self, first, second):
        """Is there a sentence boundary between the first and second token?"""
        if first[-1] in '"“»›)':
            first = first[:-1]
        if second[0] in '"„«¿¡‹(':
            second = second[1:]
        if not second[0].isupper() or second[0].isdigit():
            return False
        if not first[-1] in '.!?':
            return False
        if first[-1] == '.':
            if len(first) == 2 and first[0].isupper():
                return False
            if self.is_nonfinal_abbrev(first[:-1]):
                return False
        return True


    def segment_string(self, string):
        """Return a list of sentences in a given string."""
        tokens = string.split(' ')
        previous = tokens[0]
        segments = [previous]
        for token in tokens[1:]:
            if self.is_boundary(previous, token):
                segments.append(token)
            else:
                segments[-1] += ' ' + token
            previous = token
        return segments


    def process_document(self, doc):
        old_bundles = doc.bundles
        new_bundles = []
        for bundle in old_bundles:
            new_bundles.append(bundle)
            for tree in bundle:
                if self._should_process_tree(tree):
                    if tree.children:
                        raise ValueError("Segmenting already tokenized text is not supported.")
                    sentences = self.segment_string(tree.text)
                    orig_bundle_id = bundle.bundle_id
                    bundle.bundle_id = orig_bundle_id + '-1'
                    if len(sentences) > 1:
                        tree.text = sentences[0]
                        for i, sentence in enumerate(sentences[1:], 2):
                            new_bundle = Bundle(document=doc, bundle_id=orig_bundle_id + '-' + str(i))
                            new_bundle.create_tree(tree.zone).text = sentence
                            new_bundles.append(new_bundle)
        doc.bundles = new_bundles