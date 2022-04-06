"""Block class represents the basic Udapi processing unit."""
import logging

def not_overridden(method):
  method.is_not_overridden = True
  return method

class Block(object):
    """The smallest processing unit for processing Universal Dependencies data.

    Parameters:
    zones: which zone to process (default="all")
    if_empty_tree: what to do when encountering a tree with no nodes.
        Possible values are: process (default), skip, skip_warn, fail, delete.
    """

    def __init__(self, zones='all', if_empty_tree='process'):
        self.zones = zones
        self.if_empty_tree = if_empty_tree

    def process_start(self):
        """A hook method that is executed before processing UD data"""
        pass

    def process_end(self):
        """A hook method that is executed after processing all UD data"""
        pass

    @not_overridden
    def process_node(self, _):
        """Process a UD node"""
        pass

    @not_overridden
    def process_tree(self, tree):
        """Process a UD tree"""
        # tree.descendants is slightly slower than tree._descendants (0.05s per iterating over 700k words),
        # but it seems safer to iterate over a copy of the list of nodes.
        # If a user calls parent.create_child().shift_before_node(parent) in process_node,
        # it may end up in endless cycle (because the same node is processed again - Python for cycle remembers the position).
        for node in tree.descendants:
            self.process_node(node)

    @not_overridden
    def process_bundle(self, bundle):
        """Process a UD bundle"""
        for tree in bundle:
            if self._should_process_tree(tree):
                self.process_tree(tree)

    def run(self, document):
        self.process_start()
        self.apply_on_document(document)
        self.process_end()

    def apply_on_document(self, document):
        self.before_process_document(document)
        self.process_document(document)
        self.after_process_document(document)

    def process_document(self, document):
        """Process a UD document"""
        # Calling document.coref_entities is expensive because
        # it needs to deserialize coref_entities from the MISC attributes.
        # If no block in a scenario needs to process coreference entities/mentions,
        # the deserialization does not need to be done.
        # So we need to detect if any of the methods process_coref_entity and process_coref_mention
        # has been overriden (without calling them, which could have adverse side effects).
        # Let's use method annotations for this.
        p_entity = not hasattr(self.process_coref_entity, 'is_not_overridden')
        p_mention = not hasattr(self.process_coref_mention, 'is_not_overridden')
        p_bundle = not hasattr(self.process_bundle, 'is_not_overridden')
        p_tree = not hasattr(self.process_tree, 'is_not_overridden')
        p_node = not hasattr(self.process_node, 'is_not_overridden')
        if not any((p_entity, p_mention, p_bundle, p_tree, p_node)):
            raise Exception("No processing activity defined in block " + str(self))

        if p_entity or p_mention:
            for entity in document.coref_entities:
                if p_entity:
                    self.process_coref_entity(entity)
                else:
                    for mention in entity.mentions:
                        self.process_coref_mention(mention)

        if p_bundle or p_tree or p_node:
            for bundle_no, bundle in enumerate(document.bundles, 1):
                logging.debug('Block %s processing bundle #%d (id=%s)',
                            self.__class__.__name__, bundle_no, bundle.bundle_id)
                if p_bundle:
                    self.process_bundle(bundle)
                else:
                    for tree in bundle:
                        if self._should_process_tree(tree):
                            if p_tree:
                                self.process_tree(tree)
                            else:
                                for node in tree.descendants:
                                    self.process_node(node)

    @not_overridden
    def process_coref_entity(self, entity):
        """This method is called on each coreference entity in the document."""
        for mention in entity.mentions:
            self.process_coref_mention(mention)

    @not_overridden
    def process_coref_mention(self, mention):
        """This method is called on each coreference mention in the document."""
        pass

    def before_process_document(self, document):
        """This method is called before each process_document."""
        pass

    def after_process_document(self, document):
        """This method is called after each process_document."""
        pass

    def _should_process_tree(self, tree):
        if self.if_empty_tree != 'process' and not tree.descendants:
            if self.if_empty_tree == 'skip':
                return False
            elif self.if_empty_tree == 'delete':
                tree.remove()
                return False
            elif self.if_empty_tree == 'skip_warn':
                logging.warning("Tree %s is empty", tree)
                return False
            elif self.if_empty_tree == 'fail':
                raise Exception("Tree %s is empty" % tree)
            else:
                raise ValueError("Unknown value for if_empty_tree: "
                                 + self.if_empty_tree)
        if self.zones == 'all':
            return True
        if self.zones == '' and tree.zone == '':
            return True
        if tree.zone in self.zones.split(','):
            return True
        return False
