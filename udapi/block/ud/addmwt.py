"""Abstract base class ud.AddMwt for heuristic detection of multi-word tokens."""
from udapi.core.block import Block
import logging


class AddMwt(Block):
    """Detect and mark MWTs (split them into words and add the words to the tree)."""

    def process_node(self, node):
        analysis = self.multiword_analysis(node)
        if analysis is None:
            return
        orig_attr = {}
        for attr in 'form lemma upos xpos deprel'.split():
            orig_attr[attr] = getattr(node, attr)
        orig_attr['feats'] = node.feats.copy()
        orig_attr['misc'] = node.misc.copy()
        # Defaults for the newly created MWT
        mwt_misc = node.misc.copy()
        mwt_form = node.form

        forms = analysis['form'].split()
        main = analysis.get('main', 0)
        parent = node if analysis.get('shape', '') == 'subtree' else node.parent
        nodes = []
        for form in forms[0:main]:
            new_node = parent.create_child(form=form)
            new_node.shift_before_node(node)
            nodes.append(new_node)
        node.form = forms[main]
        nodes.append(node)
        for form in forms[main + 1:]:
            new_node = parent.create_child(form=form)
            new_node.shift_after_node(nodes[-1])
            nodes.append(new_node)

        if orig_attr['form'].isupper():
            for new_node in nodes:
                new_node.form = new_node.form.upper()
        elif orig_attr['form'][0].isupper():
            nodes[0].form = nodes[0].form.title()

        node.misc = None
        for attr in 'lemma upos xpos feats deprel misc'.split():
            if attr in analysis:
                values = analysis[attr].split()
                for i, new_node in enumerate(nodes):
                    if len(values) <= i:
                        logging.warning("Attribute '%s' not supplied for word no. %d" % (attr, i))
                        for attr in 'form lemma upos xpos feats deprel misc'.split():
                            logging.warning("%s = %s" % (attr, analysis.get(attr, '')))
                    if values[i] == '*':
                        setattr(new_node, attr, orig_attr[attr])
                        # No MISC attribute should be duplicated on the word level and token level,
                        # so if copying MISC to a new_node, delete mwt_misc.
                        # However, SpaceAfter should be annotated only on the token level,
                        # so make sure it is not accidentally copied on the word level.
                        if attr == 'misc':
                            orig_attr['misc'].clear()
                            for a in 'SpaceAfter SpacesAfter SpacesBefore'.split():
                                if new_node.misc[a]:
                                    orig_attr['misc'][a] = new_node.misc[a]
                                    del new_node.misc[a]

                    elif attr == 'feats' and '*' in values[i]:
                        new_node.feats = values[i]
                        for feat_name, feat_value in list(new_node.feats.items()):
                            if feat_value == '*':
                                new_node.feats[feat_name] = orig_attr['feats'][feat_name]
                    else:
                        setattr(new_node, attr, values[i])

        # Entity (coreference) annotation should be only on the word level,
        # so make sure it does not stay on the token level.
        if mwt_misc['Entity']:
            nodes[0].misc['Entity'] = mwt_misc['Entity']
            del mwt_misc['Entity']

        # If node is already part of an MWT, we need to delete the old MWT and extend the new MWT.
        if node.multiword_token:
            mwt_words = node.multiword_token.words
            mwt_form = node.multiword_token.form
            if node.multiword_token.misc:
                mwt_misc.update(node.multiword_token.misc)
            node.multiword_token.remove()
            mwt_words[mwt_words.index(node):mwt_words.index(node)+1] = nodes
            nodes = mwt_words

        mwt = node.root.create_multiword_token(nodes, mwt_form, mwt_misc)
        self.postprocess_mwt(mwt)

    def multiword_analysis(self, node):
        """Return a dict with MWT info or None if `node` does not represent a multiword token.

        An example return value is::

        {
            'form': 'aby bych',
            'lemma': 'aby být',
            'upos': 'SCONJ AUX',
            'xpos': 'J,------------- Vc-S---1-------',
            'feats': '_ Mood=Cnd|Number=Sing|Person=1|VerbForm=Fin', # _ means empty FEATS
            'deprel': '* aux', # * means keep the original deprel
            'main': 0, # which of the two words will inherit the original children (if any)
            'shape': 'siblings', # the newly created nodes will be siblings or alternatively
            #'shape': 'subtree', # the main-indexed node will be the head
        }
        """
        raise NotImplementedError('multiword_analysis must be overriden in subclasses')

    def postprocess_mwt(self, mwt):
        """Optional postprocessing of newly created MWTs."""
        pass
