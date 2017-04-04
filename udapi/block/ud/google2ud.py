"""Block ud.google2ud for converting Google Universal Dependency Treebank into UD.

Usage:
udapy -s ud.Google2ud ud.SetSpaceAfterFromText ud.Convert1to2 < google.conllu > ud2.conllu
"""
from udapi.block.ud.convert1to2 import Convert1to2

DEPREL_CHANGE = {
    "ROOT": "root",
    "prep": "case",
    "p": "punct",
    "poss": "nmod:poss",
    "ps": "case",
    "num": "nummod", # TODO ??
    "number": "nummod", # TODO ??
    "tmod": "nmod:tmod",
    "vmod": "acl",
    "rcmod": "acl:relcl",
    "npadvmod": "advmod",
    "prt": "compound:prt",
    "preconj": "cc:preconj",
    "predet": "det:predet",
    "gmod": "amod",
    "gobj": "obj",
}


class Google2ud(Convert1to2):
    """Convert Google Universal Dependency Treebank into UD style."""

    def process_tree(self, root):
        comment_lines = root.comment.split("\n")
        root.sent_id = comment_lines[0].strip()
        root.text = comment_lines[1].strip()
        root.comment = ''

        for node in root.descendants:
            self.process_node(node)

        # This needs to be executed after all other deprels are converted
        for node in root.descendants:
            if node.deprel in ('acomp', 'attr'): # TODO not sure about attr
                copula = node.parent
                node.parent = copula.parent
                node.deprel = copula.deprel
                copula.parent = node
                copula.deprel = 'cop'
                for child in copula.children:
                    child.parent = node

    def process_node(self, node):
        orig_feats = dict(node.feats)
        node.feats = None
        for name, value in orig_feats.items():
            if value != 'false':
                name = name.split('/')[1].capitalize()
                node.misc[name] = value.capitalize()

        if node.misc['Proper'] and node.upos == 'NOUN':
            node.upos = 'PROPN'
            del node.misc['Proper']

        try:
            node.deprel = DEPREL_CHANGE[node.deprel]
        except KeyError:
            pass

        if node.deprel == 'nn':
            if node.upos == 'PROPN' and node.parent.upos == 'PROPN':
                node.deprel = 'flat'
            else:
                node.deprel = 'compound'
        elif node.deprel in ('pobj', 'pcomp'):
            if node.parent.deprel == 'case':
                preposition = node.parent
                node.parent = preposition.parent
                preposition.parent = node
                node.deprel = 'nmod' if node.deprel == 'pobj' else 'xcomp' # TODO check xcomp
                # ud.Convert1to2 will change 'nmod' to 'obl' if needed
            else:
                self.log(node, node.deprel, node.deprel + ' but parent.deprel!=case')
                node.deprel = 'obj'
        elif node.deprel == 'infmod':
            node.deprel = 'xcomp'
            node.feats['VerbForm'] = 'Inf'
        elif node.deprel == 'partmod':
            node.deprel = 'ccomp'
            node.feats['VerbForm'] = 'Part'

        if node.upos == '.':
            node.upos = 'PUNCT'
        elif node.upos == 'PRT':
            node.upos = 'PART'
