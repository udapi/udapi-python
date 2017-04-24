"""Block ud.Google2ud for converting Google Universal Dependency Treebank into UD.

Usage:
udapy -s ud.Google2ud < google.conllu > ud2.conllu
"""
from udapi.block.ud.convert1to2 import Convert1to2
from udapi.block.ud.complywithtext import ComplyWithText
from udapi.block.ud.fixchain import FixChain
from udapi.block.ud.fixrightheaded import FixRightheaded
from udapi.block.ud.de.addmwt import AddMwt as de_AddMwt
from udapi.block.ud.pt.addmwt import AddMwt as pt_AddMwt

DEPREL_CHANGE = {
    "ROOT": "root",
    "prep": "case",
    "ncomp": "case",  # TODO ?
    "p": "punct",
    "poss": "nmod:poss",
    "ps": "case",
    "num": "nummod",
    "number": "nummod",  # TODO ?
    "tmod": "nmod:tmod",
    "vmod": "acl",
    "rcmod": "acl:relcl",
    "npadvmod": "advmod",
    "prt": "compound:prt",
    "preconj": "cc:preconj",
    "predet": "det:predet",
    "gobj": "obj",
    "postneg": "neg",  # will be changed to advmod + Polarity=Neg in ud.Convert1to2
    "pronl": "obj",  # TODO: or expl? UD_French seems to use a mix of both
    "redup": "compound:plur",
    "oblcomp": "obl",
    "mes": "dep",  # TODO ?
    "mwn": "compound:n",  # nominal multi-word
    "mwa": "compound:a",  # adjectival multi-word
    "mwv": "compound:v",  # verbal multi-word
    "asp": "aux",         # aspectual particle
    "rcmodrel": "mark:relcl",
    "auxcaus": "aux",     # redundant with Voice=Cau
    "topic": "dep",
    "possessive": "case",
    "quantmod": "det",  # TODO UD_Hindi uses "dep" for the same words
    "agent": "obl:agent",
    # TODO: "ref" - in basic dependencies it should be rehanged and relabelled
    "conjv": "compound:conjv",
    "advphmod": "advmod",
    "clas": "clf",
}

FEATS_CHANGE = {
    "proper=false": "",
    "case=prep": "",
    "case=unsp_c": "",
    "gender=unsp_g": "",
    "gender_antecedent=unsp_g": "",
    "voice=unsp_v": "",
    "number=unsp_n": "",
    "number_antecedent=unsp_n": "",
    "tense=unsp_t": "",
    "mood=unsp_m": "",
    "animacy=unsp_r": "",
    "aspect=unsp_a": "",
    "case=rel": "",  # redundant with rcmodrel (mark:relcl)
    "reciprocity=non-rcp": "",
    "reciprocity=rcp": "PronType=Rcp",
    "aspect=imperf": "Aspect=Imp",
    "form=long": "Variant=Long",
    "form=short": "Variant=Short",
    "person=reflex": "Reflex=Yes",
    "case=reflex": "Reflex=Yes",
    "case=dir": "Case=Nom",
    "gender=pl_tantum": "Number=Ptan",
    "gender_antecedent=fem_a": "Gender[psor]=Fem",
    "gender_antecedent=masc_a": "Gender[psor]=Masc",
    "gender_antecedent=neut_a": "Gender[psor]=Neut",
    "number_antecedent=sing_a": "Number[psor]=Sing",
    "number_antecedent=plur_a": "Number[psor]=Plur",
    "person_antecedent=1_a": "Person[psor]=1",
    "person_antecedent=2_a": "Person[psor]=2",
    "person_antecedent=3_a": "Person[psor]=3",
    "definiteness=def": "Definite=Def",
    "definiteness=indef": "Definite=Ind",
    "mood=sub1": "Mood=Sub",  # TODO: what is the difference between sub1 and sub2 in German?
    "mood=sub2": "Mood=Sub",
    "mood=inter": "PronType=Int",  # TODO or keep Mood=Inter (it is used in UD_Chinese)
    "tense=cnd": "Mood=Cnd",
    "degree=sup_a": "Degree=Abs",
    "degree=sup_r": "Degree=Sup",
    "case=obl": "Case=Acc",
    "tense=impf": "Tense=Imp",
    "animacy=rat": "Animacy=Hum",
    "animacy=irrat": "Animacy=Nhum",
    "honorific=hon": "Polite=Form",
    "mood=psm": "Tense=Fut",  # TODO ?
    "form=fin": "VerbForm=Fin",
    "form=ger": "VerbForm=Ger",
    # "form=irr": "VerbForm=?",
    # "form=adn": "VerbForm=?",
    "formality=fml": "Polite=Form",
    "Evidentiality=Nfh": "Evident=Nfh",
    "Evidentiality=Fh": "Evident=Fh",
}


class Google2ud(Convert1to2):
    """Convert Google Universal Dependency Treebank into UD style."""

    def __init__(self, lang='unk', non_mwt_langs='ar en ja ko zh', **kwargs):
        """Create the Google2ud block instance.

        See ``Convert1to2`` for all the args.
        """
        super().__init__(**kwargs)
        self.lang = lang
        self._addmwt_block = None
        if lang == 'de':
            self._addmwt_block = de_AddMwt()
        elif lang == 'pt':
            self._addmwt_block = pt_AddMwt()

        self._fixrigheaded_block = None
        # TODO: add 'de'
        if lang in {'ar', 'en', 'fr', 'hi', 'ru', 'th', 'tr', 'zh'}:
            self._fixrigheaded_block = FixRightheaded()

        self._fixchain_block = None
        if lang in {'pt'}:
            self._fixchain_block = FixChain()

        # UD_English v2.0 still uses "do n't" with SpaceAfter=No,
        # instead of annotating it as a multiword token.
        # In several other languages it is also common
        # that syntactic words are not separated with a space without being an MWT.
        self._comply_block = ComplyWithText(prefer_mwt=bool(lang not in non_mwt_langs.split()))

    def process_tree(self, root):
        comment_lines = root.comment.split("\n")
        root.sent_id = comment_lines[0].strip().replace(' ', '-')
        root.text = comment_lines[1].strip()
        root.comment = ''

        if self._comply_block:
            self._comply_block.process_tree(root)

        for node in root.descendants:
            self.fix_feats(node)
            self.fix_upos(node)
            self.fix_deprel(node)

        # This needs to be executed after all other deprels are converted
        for node in root.descendants:
            if node.deprel in ('acomp', 'attr'):  # TODO not sure about attr
                copula = node.parent
                node.parent = copula.parent
                node.deprel = copula.deprel
                copula.parent = node
                copula.deprel = 'cop'
                for child in copula.children:
                    child.parent = node

        # call ud.Convert1to2
        super().process_tree(root)

        # In German: "im" -> "in dem" etc.
        # This needs to be applied after prepositions are under nouns.
        if self._addmwt_block:
            self._addmwt_block.process_tree(root)

        # deprel=fixed,flat,... should be always head-initial
        if self._fixrigheaded_block:
            self._fixrigheaded_block.process_tree(root)

        # and it form a flat structure, not a chain.
        if self._fixchain_block:
            self._fixchain_block.process_tree(root)

        if self.lang in {'pt', 'it', 'ru'}:
            for node in root.descendants[2:]:
                if (node.deprel == 'goeswith' and node.prev_node.form == '-'
                    and node.parent == node.prev_node.parent
                    and node.parent == node.prev_node.prev_node):
                    node.parent.form += '-' + node.form
                    node.parent.misc['SpaceAfter'] = node.misc['SpaceAfter']
                    node.prev_node.remove(children='rehang')
                    node.remove(children='rehang')

        # This must follow fixing the hyphen-goeswith. E.g. "Primeira Dama"
        if self.lang in {'pt'}:
            for node in root.descendants:
                if node.deprel == 'goeswith':
                    node.deprel = 'compound'

    @staticmethod
    def fix_feats(node):
        """Remove language prefixes, capitalize names and values, apply FEATS_CHANGE."""
        orig_feats = dict(node.feats)
        node.feats = None
        for name, value in sorted(orig_feats.items()):
            name = name.split('/')[1]
            if name == 'inflection_type':
                node.misc['InflectionType'] = value.capitalize()
                continue
            if "antecedent" in name and node.upos == 'PRON':
                node.feats["PronType"] = "Prs"
            new = FEATS_CHANGE.get(name + '=' + value)
            if new is not None:
                if new != '':
                    new_name, new_value = new.split('=')
                    node.feats[new_name] = new_value
            elif name[0].isupper():
                node.feats[name] = value
            else:
                node.feats[name.capitalize()] = value.capitalize()

    def fix_upos(self, node):
        """PRT→PART, .→PUNCT, NOUN+Proper→PROPN, VERB+neg→AUX."""
        if node.upos == '.':
            node.upos = 'PUNCT'
        elif node.upos == 'PRT':
            node.upos = 'PART'
        if node.feats['Proper']:
            if node.upos == 'NOUN':
                node.upos = 'PROPN'
                if node.feats['Proper'] != 'True':
                    self.log(node, 'unexpected-proper', 'Proper=' + node.feats['Proper'])
            else:
                node.misc['Proper'] = node.feats['Proper']
            del node.feats['Proper']

        # Japanese uses negators with deprel=neg, which should be changed to advmod in Convert1to2.
        if node.upos == "VERB" and node.deprel == "neg":
            node.upos = "AUX"

        # Indonesian uses prefixes (me, di, ber, ke,...) and suffixes (an, kan, i,...),
        # which are written without spaces with the main word/stem (according to the raw text).
        # These could be treated as syntactic words and annotated using multi-word tokens.
        # However, there is no annotation about their dependency relations (just suff, pref)
        # and UD_Indonesian v2.0 keeps them as one word with the stem. So let's follow this style.
        # Chinese AFFIXes are more tricky to convert.
        # It seems these words are quite often tagged as PART in UD_Chinese.
        if node.upos == 'AFFIX':
            if node.deprel == 'suff':
                node.prev_node.form += node.form
                node.remove(children='rehang')
            elif node.deprel == 'pref':
                node.next_node.form = node.form + node.next_node.form
                node.remove(children='rehang')
            else:
                self.log(node, 'affix', 'upos=AFFIX deprel=' + node.deprel)
                node.upos = 'PART'

        if node.upos == 'PUNCT' and node.form in ('$', '£'):
            node.upos = 'SYM'

    def fix_deprel(self, node):
        """Convert Google dependency relations to UD deprels.

        Change topology where needed.
        """
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
            if node.parent.deprel in ('case', 'prep'):
                preposition = node.parent
                node.parent = preposition.parent
                preposition.parent = node

                # ud.Convert1to2 will change 'nmod' to 'obl' if needed
                node.deprel = 'nmod' if node.deprel == 'pobj' else 'xcomp'  # TODO check xcomp

                # Prepositions should not have any children (except for deprel=fixed/mwe), see
                # http://universaldependencies.org/u/overview/syntax.html#multiword-function-words.
                # Unfortunatelly, there are many annotation errors and it is almost always better
                # to rehang the extra children (at least to prevent spurious non-projectivities).
                # In case of PUNCTuation it is surely correct.
                # Otherwise, let's mark it as ToDo.
                for extra_prep_child in preposition.children:
                    if extra_prep_child.udeprel in ('fixed', 'mwe'):
                        continue
                    extra_prep_child.parent = node
                    if extra_prep_child.upos != 'PUNCT':
                        self.log(extra_prep_child, 'ex-adp-child', 'was an extra adposition child')
            else:
                self.log(node, node.deprel, node.deprel + ' but parent.deprel!=case')
                node.deprel = 'obj'
        elif node.deprel == 'infmod':
            node.deprel = 'xcomp'
            node.feats['VerbForm'] = 'Inf'
        elif node.deprel == 'partmod':
            node.deprel = 'ccomp'
            node.feats['VerbForm'] = 'Part'
        elif node.deprel == 'suff':
            node.misc['OrigDeprel'] = 'suff'
            node.deprel = 'dep'
        elif node.deprel == 'gmod':
            node.deprel = 'nmod' if node.feats['Case'] == 'Gen' else 'nmod:gmod'
        elif node.deprel == 'cc':
            if node.upos == 'PUNCT' and node.form == ',':
                node.deprel = 'punct'
