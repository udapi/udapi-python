"""
Block util.JoinSentence will join a given sentence with the preceding one.
"""
import logging
from udapi.core.block import Block

class JoinSentence(Block):
    """
    Joins a sentence with the preceding one. There are two ways how to indicate
    the sentences that this block should process.

    Method 1: Parameter sent_id provides the id of the sentence that should be
    merged with the preceding one. At most one sentence pair from the input will
    be merged, even if there are multiple sentences with the given id.

    Method 2: A MISC attribute can be specified that, if found, will trigger
    joining of the current sentence to the previous one. With this approach,
    multiple sentence pairs can be merged during one run.
    """

    def __init__(self, sent_id=None, misc_name=None, misc_value=None, **kwargs):
        """
        Args:
        sent_id: which sentence should be appended to the previous one
        misc_name: name of the MISC attribute that can trigger the joining (cannot be combined with sent_id and word_id)
        misc_value: value of the MISC attribute to trigger the joining; if not specified, then simple occurrence of the attribute with any value will cause the joining
            MISC attributes that have triggered sentence joining will be removed from their node.
        """
        super().__init__(**kwargs)
        if misc_name:
            if sent_id:
                logging.fatal('Cannot combine misc_value with sent_id')
        else:
            if not sent_id:
                logging.fatal('Missing parameter sent_id')
        self.sent_id = sent_id
        self.misc_name = misc_name
        self.misc_value = misc_value

    def process_document(self, document):
        previous_tree = None
        for bundle_no, bundle in enumerate(document.bundles):
            # In general, a bundle may contain multiple trees in different zones.
            # In UD data, we always expect just one zone (labeled '') per bundle.
            # This code could be extended to join all zones but we do not try to do it at present.
            if len(bundle.trees) != 1:
                logging.fatal('Cannot process bundles that have less or more than 1 zone')
            if not bundle.has_tree(zone=''):
                logging.fatal('Cannot process bundles that do not have the zone with empty zone id')
            if self.misc_name:
                root = bundle.get_tree()
                # The MISC attribute we are looking for should logically occur
                # on the first node of the sentence but we can take it from any node.
                join_commands = [n for n in root.descendants if n.misc[self.misc_name] and self.misc_value == None or n.misc[self.misc_name] == self.misc_value]
                if join_commands:
                    if not previous_tree:
                        logging.fatal('Cannot join the first sentence as there is no previous sentence')
                    previous_tree.steal_nodes(root.descendants)
                    previous_tree.text = previous_tree.compute_text()
                    # Remove from the node the MISC attribute that triggered the sentence split.
                    for n in join_commands:
                        n.misc[self.misc_name] = ''
                    # Remove the current bundle. It will also update the numbers of the remaining bundles.
                    bundle.remove()
                else:
                    previous_tree = root
            elif bundle.bundle_id == self.sent_id:
                logging.info('Found!')
                if not previous_tree:
                    logging.fatal('Cannot join the first sentence as there is no previous sentence')
                root = bundle.get_tree()
                previous_tree.steal_nodes(root.descendants)
                previous_tree.text = previous_tree.compute_text()
                # Remove the current bundle. It will also update the numbers of the remaining bundles.
                bundle.remove()
                # We have found our sentence. No need to process the rest of the document.
                break
