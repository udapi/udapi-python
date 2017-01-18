"""Eval is a special block for evaluating code given by parameters."""
from udapi.core.block import Block

# We need exec in this block and the variables this etc. are not unused but provided for the exec
# pylint: disable=exec-used,unused-variable
class Eval(Block):
    """Special block for evaluating code given by parameters."""

    # So many arguments is the design of this block (consistent with Perl Udapi).
    # pylint: disable=too-many-arguments,too-many-instance-attributes
    def __init__(self, doc=None, bundle=None, tree=None, node=None, start=None, end=None,
                 before_doc=None, after_doc=None, before_bundle=None, after_bundle=None,
                 expand_code=True, **kwargs):
        super().__init__(**kwargs)
        self.doc = doc
        self.bundle = bundle
        self.tree = tree
        self.node = node
        self.start = start
        self.end = end
        self.before_doc = before_doc
        self.after_doc = after_doc
        self.before_bundle = before_bundle
        self.after_bundle = after_bundle
        self.expand_code = expand_code

    def expand_eval_code(self, to_eval):
        """Expand '$.' to 'this.', useful for oneliners."""
        return to_eval.replace('$.', 'this.') if self.expand_code else to_eval

    def before_process_document(self, document):
        if self.before_doc:
            this = doc = document
            exec(self.expand_eval_code(self.before_doc))

    def after_process_document(self, document):
        if self.after_doc:
            this = doc = document
            exec(self.expand_eval_code(self.after_doc))

    def process_document(self, document):
        this = doc = document
        if self.doc:
            exec(self.expand_eval_code(self.doc))

        if self.bundle or self.before_bundle or self.after_bundle or self.tree or self.node:
            for bundle in doc.bundles:
                #TODO if self._should_process_bundle(bundle):
                self.process_bundle(bundle)

    def process_bundle(self, bundle):
        # Extract variables, so they can be used in eval code
        document = doc = bundle.document
        this = bundle

        if self.before_bundle:
            exec(self.expand_eval_code(self.before_bundle))

        if self.bundle:
            exec(self.expand_eval_code(self.bundle))

        if self.tree or self.node:
            trees = bundle.trees
            for tree in trees:
                #TODO if not self._should_process_tree(tree): continue
                self.process_tree(tree)

        if self.after_bundle:
            exec(self.expand_eval_code(self.after_bundle))

    def process_tree(self, tree):
        # Extract variables $bundle, so they can be used in eval code
        bundle = tree.bundle
        doc = document = bundle.document
        this = tree

        if self.tree:
            exec(self.expand_eval_code(self.tree))

        if self.node:
            for node in tree.descendants():
                this = node
                exec(self.expand_eval_code(self.node))

    def process_start(self):
        if self.start:
            exec(self.expand_eval_code(self.start))

    def process_end(self):
        if self.end:
            exec(self.expand_eval_code(self.end))
