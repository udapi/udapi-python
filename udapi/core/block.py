"""Block class represents the basic Udapi processing unit."""
import logging


class Block(object):
    """The smallest processing unit for processing Universal Dependencies data."""

    def __init__(self, zones='all'):
        self.zones = zones

    def process_start(self):
        """A hook method that is executed before processing UD data"""
        pass

    def process_end(self):
        """A hook method that is executed after processing all UD data"""
        pass

    def process_node(self, _):
        """Process a UD node"""
        raise Exception("No processing activity defined in block " + str(self))

    def process_tree(self, tree):
        """Process a UD tree"""
        for node in tree.descendants:
            self.process_node(node)

    def process_bundle(self, bundle):
        """Process a UD bundle"""
        for tree in bundle:
            if self._should_process_tree(tree):
                self.process_tree(tree)

    def process_document(self, document):
        """Process a UD document"""
        for bundle_no, bundle in enumerate(document.bundles, 1):
            logging.debug('Block %s processing bundle #%d (id=%s)',
                          self.__class__.__name__, bundle_no, bundle.bundle_id)
            self.process_bundle(bundle)

    def before_process_document(self, document):
        """This method is called before each process_document."""
        pass

    def after_process_document(self, document):
        """This method is called after each process_document."""
        pass

    def _should_process_tree(self, tree):
        if self.zones == 'all':
            return True
        if self.zones == '' and tree.zone == '':
            return True
        if tree.zone in self.zones.split(','):
            return True
        return False
