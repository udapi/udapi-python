"""Block segment.Simple"""
from udapi.core.block import Block
from udapi.core.bundle import Bundle
import re

# We don't want to introduce the extra "regex" dependency for \p{Lu} support.
# import sys
# pLu = '[{}]'.format("".join([chr(i) for i in range(sys.maxunicode) if chr(i).isupper()]))
# p = re.compile(pLu)


class Simple(Block):
    """"Base segmenter, splits on sentence-final segmentation followed by uppercase."""

    @staticmethod
    def segment_string(string):
        """A method to be overriden in subclasses."""
        return re.sub(r'([.!?])(["“»›]?) (["„«¿¡‹(]?)(\d|[ČĎŇÓŘŠŤÚŽA-Z])', r'\1\2\n\3\4', string).split('\n')


    def process_document(self, doc):
        old_bundles = doc.bundles
        new_bundles = []
        for bundle in old_bundles:
            for tree in bundle:
                new_bundles.append(bundle)
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