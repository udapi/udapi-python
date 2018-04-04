"""Block ud.Google2ud for converting Google Universal Dependency Treebank into UD.

Usage:
udapy -s ud.Google2ud < google.conllu > ud2.conllu
"""
import re
from udapi.block.ud.convert1to2 import Convert1to2
from udapi.block.ud.complywithtext import ComplyWithText
from udapi.block.ud.fixchain import FixChain
from udapi.block.ud.fixrightheaded import FixRightheaded
from udapi.block.ud.fixpunct import FixPunct
from udapi.block.ud.de.addmwt import AddMwt as de_AddMwt
from udapi.block.ud.es.addmwt import AddMwt as es_AddMwt
from udapi.block.ud.fr.addmwt import AddMwt as fr_AddMwt
from udapi.block.ud.pt.addmwt import AddMwt as pt_AddMwt
from udapi.block.ud.joinasmwt import JoinAsMwt

DEPREL_CHANGE = {
    "ROOT": "root",
    "prep": "case",
    "ncomp": "case:loc",  # only in Chinese; Herman proposes case:loc
    "p": "punct",
    "poss": "nmod:poss",
    "ps": "case",
    "num": "nummod",
    "number": "nummod",  # TODO ?
    "tmod": "nmod:tmod",
    "vmod": "acl",
    "rcmod": "acl:relcl",
    "npadvmod": "advmod",
    "preconj": "cc:preconj",
    "predet": "det:predet",
    "gobj": "obj",
    "postneg": "neg",  # will be changed to advmod + Polarity=Neg in ud.Convert1to2
    "pronl": "obj",  # TODO: or expl? UD_French seems to use a mix of both
    "oblcomp": "obl",
    "mes": "clf",  # TODO: structural transformation needed
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
    "narg": "nmod:arg",  # Turkish only
}

FEATS_CHANGE = {
    "proper=false": "",
    "Proper=false": "",
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
    "mood=sub1": "Mood=Sub|Tense=Pres",  # de
    "mood=sub2": "Mood=Sub|Tense=Past",  # de
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
    "formality=fml": "Polite=Form",
    "Evidentiality=Nfh": "Evident=Nfh",
    "Evidentiality=Fh": "Evident=Fh",
}

FR_DAYS_MONTHS = ('lundi mardi mercredi jeudi vendredi samedi dimanche '
                  'janvier février mars avril mai juin juillet août '
                  'septembre octobre novembre décembre'.split())


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
        elif lang == 'es':
            self._addmwt_block = es_AddMwt()
        elif lang == 'fr':
            self._addmwt_block = fr_AddMwt()
        elif lang == 'pt':
            self._addmwt_block = pt_AddMwt()
        self._joinasmwt_block = JoinAsMwt() if lang in {'es', 'tr'} else None

        self._fixrigheaded_block = None
        if lang in {'ar', 'de', 'en', 'fr', 'hi', 'ru', 'th', 'zh'}:
            self._fixrigheaded_block = FixRightheaded()
        elif lang == 'tr':
            self._fixrigheaded_block = FixRightheaded(deprels='conj,flat,fixed,appos,goeswith,list')

        # Normalize the attachment of punctuation for all languages.
        self._fixpunct_block = FixPunct()

        self._fixchain_block = None
        if lang in {'pt', 'ru'}:
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
        # The third line of comments contains the English translation.
        root.comment = '' if self.lang == "en" or len(comment_lines) < 3 else comment_lines[2]

        # ud.ComplyWithText is the very first step because it may change the tokenization
        # and also it fills SpaceAfter=No, which is used in further steps.
        if self._comply_block:
            self._comply_block.process_tree(root)

        # `deprel=goeswith` must be fixed now because it also changes the number of nodes.
        # Unlike UDv2, Google style uses `goeswith` mostly to fix "wrong" tokenization,
        # e.g. "e-mail" written correctly without spaces, but tokenized into three words.
        # Moreover, the hyphen is not always marked with `goeswith`.
        if self.lang in {'de', 'fr', 'it', 'pt', 'ru', 'tr'}:
            for node in root.descendants:
                if node.form == '-' and node.no_space_after and node.prev_node.no_space_after:
                    if 'goeswith' in (node.prev_node.deprel, node.next_node.deprel):
                        node.deprel = 'goeswith'
                    if self.lang == 'fr':
                        node.deprel = 'goeswith'
                        node.parent = node.next_node
            for node in root.descendants:
                self.fix_goeswith(node)

        # Google Turkish annotation of coordination is very different from both UDv1 and UDv2.
        # Also some of the deprel=ig nodes should be merged with their parents.
        if self.lang == 'tr':
            for node in root.descendants:
                conjs = [n for n in node.children if n.deprel == 'conj']
                if conjs:
                    conjs[0].parent = node.parent
                    conjs[0].deprel = node.deprel
                    node.deprel = 'conj'
                    for nonfirst_conj in conjs[1:] + [node]:
                        nonfirst_conj.parent = conjs[0]
            for node in root.descendants:
                if node.deprel == 'ig' and re.match('leş|laş', node.parent.form.lower()):
                    self._merge_with(node.parent, node)

        # Multi-word prepositions must be solved before fix_deprel() fixes pobj+pcomp.
        for node in root.descendants:
            self.fix_multiword_prep(node)

        # Fixing feats, upos and deprel in separate steps (the order is important).
        for node in root.descendants:
            self.fix_feats(node)
        for node in root.descendants:
            self.fix_upos(node)
        for node in root.descendants:
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

        for block in (
                self._addmwt_block,        # e.g. "im" -> "in dem" in de. Must follow Convert1to2.
                self._joinasmwt_block,     # no pair of alphabetical words with SpaceAfter=No
                self._fixrigheaded_block,  # deprel=fixed,flat,... should be always head-initial
                self._fixchain_block,      # and form a flat structure, not a chain.
                self._fixpunct_block):     # commas should depend on the subord unit.
            if block:
                block.process_tree(root)

        if self.lang == 'tr':
            root.children[0].deprel = 'root'
            for node in root.descendants:
                if node.deprel in {'obl:poss', 'obl:arg'}:
                    node.udeprel = 'nmod'

    def fix_goeswith(self, node):
        """Solve deprel=goeswith which is almost always wrong in the Google annotation."""
        if node.deprel != 'goeswith':
            return

        # It has been decided German should use "compound" and keep e.g. "E-mail" as three words.
        # The only two cases we want to merge are:
        # * dots marking ordinal numbers (21. Oktober) should be merged with the number
        #   keeping the upos of the number (Google has the dot as parent, don't ask me why).
        #   There are still bugs in the output ("Oktober" depends on "21.") which I give up.
        # * apostrophes in foreign words "don't" or "Smith'" (the original English was "Smith's").
        if self.lang == 'de':
            if (node.precedes(node.parent) and node.misc['SpaceAfter'] == 'No'
                    and node.next_node.form in ".'"):
                node.next_node.upos = node.upos
                self._merge_with(node.next_node, node)
            elif (node.parent.precedes(node) and node.prev_node.misc['SpaceAfter'] == 'No'
                  and node.prev_node.form in ".'"):
                node.prev_node.upos = node.upos
                self._merge_with(node.prev_node, node)
            else:
                node.deprel = 'compound'

        # Other languages use goeswith for marking Google-tokenization errors.
        # In Portuguese, there are in addition cases like "Primeira Dama".
        elif self.lang in {'fr', 'it', 'pt', 'ru', 'tr'}:
            if node.precedes(node.parent) and node.misc['SpaceAfter'] == 'No':
                self._merge_with(node.next_node, node)
            elif node.parent.precedes(node) and node.prev_node.misc['SpaceAfter'] == 'No':
                self._merge_with(node.prev_node, node)
            elif self.lang in {'pt'}:
                node.deprel = 'compound'

    @staticmethod
    def _merge_with(node, delete_node):
        """Concat forms, merge feats, remove `delete_node`, and keep SpaceAfter of the right node.

        Should be called only on neighboring nodes.
        """
        if node.precedes(delete_node):
            node.form += delete_node.form
            node.misc['SpaceAfter'] = delete_node.misc['SpaceAfter']
        else:
            node.form = delete_node.form + node.form
        if node.parent == delete_node:
            node.parent = delete_node.parent
        for child in delete_node.children:
            child.parent = node
        delete_node.feats.update(node.feats)
        node.feats = delete_node.feats
        # node.misc['Merge'] = 1
        delete_node.remove()

    def fix_multiword_prep(self, node):
        """Solve pobj/pcomp depending on pobj/pcomp.

         Only some of these cases are multi-word prepositions (which should get deprel=fixed).
         """
        if node.deprel in ('pobj', 'pcomp') and node.parent.deprel in ('pobj', 'pcomp'):
            lo_prep = node.parent
            hi_prep = node.parent.parent
            if hi_prep.deprel != 'prep':
                return
            # E.g. in "from A to B", the Google style attaches "to"/pcomp under "from"/prep.
            # Let's use this heuristics: if the prepositions are not next to each other,
            # they should be siblings (as in "from A to B").
            if abs(lo_prep.ord - hi_prep.ord) != 1:
                lo_prep.parent = hi_prep.parent
                lo_prep.deprel = 'prep'
            # Some languages (e.g. pt) in UDv2 do not use multi-word prepositions at all.
            elif self.lang in {'pt'}:
                node.parent = hi_prep
                lo_prep.parent = node
                lo_prep.deprel = 'case'
            elif self.lang == 'es' and lo_prep.form in {'entre', 'en', 'a'}:
                node.parent = hi_prep
                lo_prep.parent = node
                lo_prep.deprel = 'case'
            elif self.lang == 'es' and lo_prep.form == 'para':
                node.parent, node.deprel = hi_prep.parent, 'obj'
                lo_prep.deprel, hi_prep.deprel = 'mark', 'mark'
                lo_prep.parent, hi_prep.parent = node, node
            # Otherwise, they are probably multi-word prepositions, e.g. "according to",
            # but they can also be sibling prepositions, e.g. "out of".
            # The Google style does not distinguish those and I don't see any heuristics,
            # so let's mark these cases as ToDo.
            else:
                first_prep, second_prep = hi_prep, lo_prep
                if lo_prep.precedes(hi_prep):
                    first_prep, second_prep = lo_prep, hi_prep
                    first_prep.parent = hi_prep.parent
                    second_prep.parent = first_prep
                for prep_child in second_prep.children:
                    prep_child.parent = first_prep
                second_prep.deprel = 'fixed'
                if self.lang == 'es' and lo_prep.form == 'par':
                    pass
                else:
                    self.log(second_prep, 'unsure-multi-prep', 'deprel=fixed, but may be siblings')

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
                    for new_pair in new.split('|'):
                        new_name, new_value = new_pair.split('=')
                        node.feats[new_name] = new_value
            elif name[0].isupper():
                node.feats[name] = value
            else:
                node.feats[name.capitalize()] = value.capitalize()

        # Don't loose info about proper names which will not have upos=PROPN.
        if node.feats['Proper'] == 'True':
            if node.xpos not in {'NNP', 'NNPS'}:
                node.misc['Proper'] = 'True'
            del node.feats['Proper']

    def fix_upos(self, node):
        """PRT→PART, .→PUNCT, NOUN+Proper→PROPN, VERB+neg→AUX etc."""
        if node.xpos == 'SYM':  # These are almost always tagged as upos=X which is wrong.
            node.upos = 'SYM'
            if node.deprel in {'punct', 'p'}:
                if node.form in "_-.؟”'":
                    node.upos = 'PUNCT'
                else:
                    node.deprel = 'dep'  # This is another way how to say deprel=todo.
        elif node.upos == '.':
            node.upos = 'PUNCT'
        elif node.upos == 'PRT':
            node.upos = 'PART'
        elif node.upos == 'NOUN':
            if node.xpos in {'NNP', 'NNPS'}:
                node.upos = 'PROPN'

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

        if node.upos == "NUM" and node.deprel == "det" and not node.form.isnumeric():
            node.upos = "DET"

        if self.lang == 'de' and node.upos == 'CONJ' and node.form.lower() == 'zu':
            node.deprel = 'mark'
            node.upos = 'PART'
            node.xpos = 'RP'
            if node.parent.deprel == 'aux':
                node.parent = node.parent.parent

        if node.upos == 'CONJ' and node.deprel == 'mark':
            node.upos = 'SCONJ'

        if self.lang == 'fr':
            if node.upos == 'PROPN' and node.form.lower() in FR_DAYS_MONTHS:
                node.upos = 'NOUN'
            if node.form == 'États-Unis':
                node.upos = 'PROPN'

    def fix_deprel(self, node):
        """Convert Google dependency relations to UD deprels.

        Change topology where needed.
        """
        try:
            node.deprel = DEPREL_CHANGE[node.deprel]
        except KeyError:
            pass

        if node.deprel in ('nn', 'compound'):
            if node.upos == 'PROPN' and node.parent.upos == 'PROPN':
                node.deprel = 'flat:name'
            else:
                node.deprel = 'compound'
        elif node.deprel in ('pobj', 'pcomp'):
            if node.parent.deprel in ('case', 'prep', 'conj'):
                preposition = node.parent
                node.parent = preposition.parent
                preposition.parent = node

                # ud.Convert1to2 will change 'nmod' to 'obl' if needed
                if preposition.deprel == 'conj':
                    node.deprel = 'conj'
                    preposition.deprel = 'case'
                elif node.deprel == 'pobj':
                    node.deprel = 'nmod'
                else:
                    node.deprel = 'xcomp'  # TODO check if pcomp -> xcomp is correct

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
        elif node.deprel == 'parataxis':
            if node.children:
                cc_node = node.descendants[0].prev_node
                if cc_node.udeprel == 'cc' and cc_node.parent == node.parent:
                    node.deprel = 'conj'
        elif node.deprel == 'dislocated':
            if self.lang == 'fr':
                nsubj = next((n for n in node.parent.children if n.udeprel == 'nsubj'), None)
                if nsubj is not None:
                    node.deprel = 'nsubj'
                    nsubj.deprel = 'expl' if nsubj.upos == 'PRON' else 'dislocated'
        elif node.deprel == 'appos':
            if self.lang == 'fr' and node.parent.form in {'M.', 'Mme', 'Dr'}:
                node.deprel = 'flat:name'
        elif node.deprel == 'prt':
            if self.lang in {'en', 'de', 'nl', 'sv', 'da', 'no', 'th'}:
                node.deprel = 'compound:prt'
            elif self.lang == 'tr':
                node.deprel = 'advmod:emph'
            else:
                node.deprel = 'dep:prt'
        elif node.deprel == 'redup':
            node.deprel = 'compound:plur' if self.lang == 'id' else 'compound:redup'
        elif node.deprel == 'ig':
            if node.parent.form == 'ki' and node.parent.deprel not in {'prep', 'pobj'}:
                ki = node.parent
                node.deprel = ki.deprel
                ki.upos = 'ADP'
                ki.deprel = 'case'
                node.parent = ki.parent
                ki.parent = node
            elif node.upos == 'AUX' or node.form == 'ler':  # dır, dir, ydi, dı, ydı, tu, değil,...
                node.deprel = 'cop'
            elif node.parent.upos == 'AUX':  # yaşlıyken, gençken,...
                copula = node.parent
                node.parent = copula.parent
                copula.parent = node
                node.deprel = copula.deprel
                copula.deprel = 'cop'
            elif node.upos == 'PUNCT':
                node.deprel = 'punct'
            else:
                node.deprel = 'dep:ig'
