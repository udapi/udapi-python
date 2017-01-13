from udapi.core.block import Block


def _merge_deprel(deprel):
    """
    Provide a merging of the closely related bags.
    In fact, simply modify deprel name according to (Vulic et al., 2016).

    :param deprel: An original deprel.
    :return: A modified deprel.
    :rtype: str

    """
    if deprel in ['dobj', 'iobj', ]:
        return 'obj'

    if deprel in ['nsubj', 'nsubjpass']:
        return 'subj'

    if deprel in ['xcomp', 'ccomp']:
        return 'comp'

    if deprel in ['advcl', 'advmod']:
        return 'adv'

    return deprel


class Baseline(Block):
    """
    A block for extraction context configurations for training verb representations using word2vecf.

    """

    def __init__(self, args=None):
        """
        Initialization.

        :param args: A dict of optional parameters.

        """
        super(Baseline, self).__init__(args)

        if args is None:
            args = {}

        self.pool = ['prep', 'acl', 'obj', 'comp', 'adv', 'conj']
        if 'pool' in args:
            self.pool = args['pool'].split(',')

        self.pos = ['VERB']
        if 'pos' in args:
            self.pos = args['pos'].split(',')

        self.lemmas = False
        if 'lemmas' in args and args['lemmas'] == '1':
            self.lemmas = True

        self.suffixed_forms = False
        if 'suffixed_form' in args and args['suffixed_forms'] == '1':
            self.suffixed_forms = True

        self.reflexive_verbs = False
        if 'reflexive_verbs' in args and args['reflexive_verbs'] == '1':
            self.reflexive_verbs = True

    def get_word(self, node):
        """
        Format the correct string representation of the given node according to the block settings.

        :param node: A input node.
        :return: A node's string representation.

        """
        # If reflexive pronoun should be append to the verb, try to find such
        # pronoun for each verb.
        word_suffix = ''
        if self.reflexive_verbs:
            for child in node.children:
                if child.deprel == 'expl':
                    word_suffix = child.lemma
                    break

        # Use the node's form or the lemma.
        word = node.form
        if self.lemmas:
            word = node.lemma

        # Append the word suffix, if found.
        if word_suffix != '':
            word = '%s_%s' % (word, word_suffix)

        # Convert to lowercase.
        word = word.lower()

        # Remove last 3 chars when the block is applied on a suffixed dataset.
        if self.suffixed_forms:
            word = word[:-3]

        return word

    def print_triple(self, target_node, context_node, relation_name):
        """
        Print to the standard output the context triple according to the block settings.

        :param target_node: A target word.
        :param context_node: A context word.
        :param relation_name: A relation name.

        """
        target_word = self.get_word(target_node)
        context_word = self.get_word(context_node)

        triple = '%s %s_%s' % (target_word, context_word, relation_name)
        print(triple.encode('utf-8'))

    def process_node(self, node):
        """
        Extract context configuration for verbs according to (Vulic et al., 2016).

        :param node: A node to be process.

        """
        # We want to extract contexts only for verbs.
        if str(node.upos) not in self.pos:
            return

        # Process node's parent.
        parent_deprel_orig = node.deprel
        parent_deprel_merged = _merge_deprel(parent_deprel_orig)

        if parent_deprel_orig in self.pool:
            self.print_triple(node, node.parent, parent_deprel_orig)

        if parent_deprel_orig != parent_deprel_merged and parent_deprel_merged in self.pool:
            relation_name = '%sI' % parent_deprel_merged
            self.print_triple(node, node.parent, relation_name)

        if parent_deprel_orig in self.pool and parent_deprel_orig == 'conj':
            self.print_triple(node, node.parent, parent_deprel_merged)

        # Process node's children.
        for child in node.children:
            child_deprel_orig = child.deprel
            child_deprel_merged = _merge_deprel(child_deprel_orig)

            if child_deprel_orig in self.pool:
                self.print_triple(node, child, child_deprel_orig)

            if child_deprel_orig != child_deprel_merged and child_deprel_merged in self.pool:
                self.print_triple(node, child, child_deprel_merged)

            if 'prep' in self.pool:
                has_preposition = False
                for sub_child in child.children:
                    if sub_child.deprel == 'case':
                        has_preposition = True
                        break

                if has_preposition:
                    self.print_triple(node, child, 'prep')
