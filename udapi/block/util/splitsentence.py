"""
Block util.SplitSentence will split a given sentence at a given token.
"""
import logging
from udapi.core.block import Block
from udapi.core.root import Root

class SplitSentence(Block):
    """
    If the sent_id of the current sentence matches the parameter, splits the
    sentence into two. The first token of the second sentence is also given as
    a parameter.

    Alternatively, a MISC attribute can be specified that triggers sentence
    splitting at the given token. With this approach, multiple sentence splits
    can be performed during one run.
    """

    def __init__(self, sent_id=None, word_id=None, misc_name=None, misc_value=None, **kwargs):
        """
        Args:
        sent_id: which sentence should be split (new ids will have A and B appended)
        word_id: which word should be the first word of the second sentence (tokens and words will be renumbered)
        misc_name: name of the MISC attribute that can trigger the split (cannot be combined with sent_id and word_id)
        misc_value: value of the MISC attribute to trigger the split; if not specified, then simple occurrence of the attribute with any value will cause the split
            MISC attributes that have triggered sentence split will be removed from their node.
        """
        super().__init__(**kwargs)
        if misc_name:
            if sent_id or word_id:
                logging.fatal('Cannot combine misc_value with sent_id or word_id')
        else:
            if not sent_id:
                logging.fatal('Missing parameter sent_id')
            if not word_id:
                logging.fatal('Missing parameter word_id')
        self.sent_id = sent_id
        self.word_id = word_id
        self.misc_name = misc_name
        self.misc_value = misc_value

    def process_document(self, document):
        for bundle_no, bundle in enumerate(document.bundles):
            # In general, a bundle may contain multiple trees in different zones.
            # In UD data, we always expect just one zone (labeled '') per bundle.
            # This code could be extended to split all zones but we do not try to do it at present.
            # (The zones may be translations to other languages and it is not likely that we would
            # want to split each translation at the same position.)
            if len(bundle.trees) != 1:
                logging.fatal('Cannot process bundles that have less or more than 1 zone')
            if not bundle.has_tree(zone=''):
                logging.fatal('Cannot process bundles that do not have the zone with empty zone id')
            if self.misc_name:
                root = bundle.get_tree()
                split_points = [n for n in root.descendants if n.ord > 1 and n.misc[self.misc_name] and self.misc_value == None or n.misc[self.misc_name] == self.misc_value]
                if split_points:
                    # Create as many new bundles as there are split points.
                    n_new = len(split_points)
                    current_bid = bundle.bundle_id
                    idletter = 'B' # a letter will be added to bundle ids to distinguish them
                    for i in range(n_new):
                        new_bundle = document.create_bundle()
                        new_bundle.bundle_id = current_bid + idletter
                        new_root = Root(zone='')
                        new_bundle.add_tree(new_root)
                        # Identify nodes to move to the new bundle.
                        first_node_id = split_points[i].ord
                        if i < n_new - 1:
                            next_first_node_id = split_points[i+1].ord
                            nodes_to_move = [n for n in root.descendants if n.ord >= first_node_id and n.ord < next_first_node_id]
                        else:
                            nodes_to_move = [n for n in root.descendants if n.ord >= first_node_id]
                        new_root.steal_nodes(nodes_to_move)
                        self.make_zeros_roots(new_root)
                        new_root.text = new_root.compute_text()
                        # The new bundle was created at the end of the document.
                        # Move it to the position right after the current bundle.
                        document.bundles.pop()
                        document.bundles.insert(bundle_no + i + 1, new_bundle)
                        idletter = chr(ord(idletter) + 1)
                        # Remove from the node the MISC attribute that triggered the sentence split.
                        split_points[i].misc[self.misc_name] = ''
                    # Update the id of the current bundle, fix its zero-dependents and recompute sentence text.
                    bundle.bundle_id += 'A'
                    self.make_zeros_roots(root)
                    root.text = root.compute_text()
                    # Update the bundle numbers of the new bundles and all bundles after them.
                    updated_no = bundle_no + 1
                    for b in document.bundles[(bundle_no+1):]:
                        b.number = updated_no
                        updated_no += 1
            elif bundle.bundle_id == self.sent_id:
                logging.info('Found!')
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
                self.make_zeros_roots(root)
                self.make_zeros_roots(new_root)
                # Update the sentence text attributes of the new sentences.
                root.text = root.compute_text()
                new_root.text = new_root.compute_text()
                # We have found our sentence. No need to process the rest of the document.
                break

    def make_zeros_roots(self, root):
        """
        The steal_nodes() method does not make sure that all nodes newly attached
        to the artificial root have the 'root' relation. Fix it.
        """
        n_root = 0
        for n in root.descendants:
            if n.parent.is_root():
                n.deprel = 'root'
                n_root += 1
        if n_root > 1:
            logging.warning('More than one 0:root relation in newly segmented sentence %s.' % root.bundle.bundle_id)
