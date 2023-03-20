"""
my.SplitSentence will split a given sentence at a given token.
"""
import logging
from udapi.core.block import Block
from udapi.core.root import Root

class SplitSentence(Block):
    """
    If the sent_id of the current sentence matches the parameter, splits the
    sentence into two. The first token of the second sentence is also given as
    a parameter.
    """

    def __init__(self, sent_id=None, word_id=None, **kwargs):
        """
        Args:
        sent_id: which sentence should be split (new ids will have A and B appended)
        word_id: which word should be the first word of the second sentence (tokens and words will be renumbered)
        """
        super().__init__(**kwargs)
        if not sent_id:
            logging.fatal('Missing parameter sent_id')
        if not word_id:
            logging.fatal('Missing parameter word_id')
        self.sent_id = sent_id
        self.word_id = word_id

    def process_document(self, document):
        for bundle_no, bundle in enumerate(document.bundles):
            if bundle.bundle_id == self.sent_id:
                logging.info('Found!')
                # In general, a bundle may contain multiple trees in different zones.
                # In UD data, we always expect just one zone (labeled '') per bundle.
                # This code could be extended to split all zones but we do not try to do it at present.
                # (The zones may be translations to other languages and it is not likely that we would
                # want to split each translation at the same position.)
                if len(bundle.trees) != 1:
                    logging.fatal('Cannot process bundles that have less or more than 1 zone')
                if not bundle.has_tree(zone=''):
                    logging.fatal('Cannot process bundles that do not have the zone with empty zone id')
                root = bundle.get_tree()
                nodes_to_move = [n for n in root.descendants if n.ord >= self.word_id]
                if len(nodes_to_move) == 0:
                    logging.fatal('No nodes to move to the new sentence; word_id may be out of range')
                # Create a new bundle at the end of the current document.
                new_bundle = document.create_bundle()
                # Move the new bundle to the position right after the current bundle.
                new_bundle_no = bundle_no + 1
                document.bundles.pop()
                document.bundles.insert(new_bundle_no, new_bundle)
                updated_no = new_bundle_no
                for b in document.bundles[new_bundle_no:]:
                    b.number = updated_no
                    updated_no += 1
                new_bundle.bundle_id = bundle.bundle_id + 'B'
                bundle.bundle_id += 'A'
                new_root = Root(zone='')
                new_bundle.add_tree(new_root)
                new_root.steal_nodes(nodes_to_move)
                # The steal_nodes() method does not make sure that all nodes newly attached
                # to the artificial root have the 'root' relation. Fix it.
                for n in root.descendants:
                    if n.parent.is_root():
                        n.deprel = 'root'
                for n in new_root.descendants:
                    if n.parent.is_root():
                        n.deprel = 'root'
                # Update the sentence text attributes of the new sentences.
                root.text = root.compute_text()
                new_root.text = new_root.compute_text()
                # We have found our sentence. No need to process the rest of the document.
                break
