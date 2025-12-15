"""Block ud.ca.AddMwt for heuristic detection of Catalan contractions.

According to the UD guidelines, contractions such as "del" = "de el"
should be annotated using multi-word tokens.

Note that this block should be used only for converting legacy conllu files.
Ideally a tokenizer should have already split the MWTs.
"""
import re
import udapi.block.ud.addmwt

MWTS = {
    'al':      {'form': 'a el',    'lemma': 'a el',   'feats': '_ Definite=Def|Gender=Masc|Number=Sing|PronType=Art'},
    'als':     {'form': 'a els',   'lemma': 'a el',   'feats': '_ Definite=Def|Gender=Masc|Number=Plur|PronType=Art'},
    'del':     {'form': 'de el',   'lemma': 'de el',  'feats': '_ Definite=Def|Gender=Masc|Number=Sing|PronType=Art'},
    'dels':    {'form': 'de els',  'lemma': 'de el',  'feats': '_ Definite=Def|Gender=Masc|Number=Plur|PronType=Art'},
    'pel':     {'form': 'per el',  'lemma': 'per el', 'feats': '_ Definite=Def|Gender=Masc|Number=Sing|PronType=Art'},
    'pels':    {'form': 'per els', 'lemma': 'per el', 'feats': '_ Definite=Def|Gender=Masc|Number=Plur|PronType=Art'},
}

# shared values for all entries in MWTS
for v in MWTS.values():
    v['lemma'] = v['form']
    v['upos'] = 'ADP DET'
    v['deprel'] = '* det'
    # The following are the default values
    # v['main'] = 0 # which of the two words will inherit the original children (if any)
    # v['shape'] = 'siblings', # the newly created nodes will be siblings


class AddMwt(udapi.block.ud.addmwt.AddMwt):
    """Detect and mark MWTs (split them into words and add the words to the tree)."""

    def __init__(self, verbpron=False, **kwargs):
        super().__init__(**kwargs)
        self.verbpron = verbpron

    def multiword_analysis(self, node):
        """Return a dict with MWT info or None if `node` does not represent a multiword token."""
        analysis = MWTS.get(node.form.lower(), None)

        if analysis is not None:
            # Modify the default attachment of the new syntactic words in special situations.
            if re.match(r'^(root|conj|reparandum)$', node.udeprel):
                # Copy the dictionary so that we do not modify the original and do not affect subsequent usages.
                analysis = analysis.copy()
                analysis['shape'] = 'subtree'
            return analysis
        return None

    def fix_personal_pronoun(self, node):
        # There is a mess in lemmas and features of personal pronouns.
        if node.upos == 'PRON':
            if re.match("^jo$", node.form, re.IGNORECASE):
                node.lemma = 'jo'
                node.feats = 'Case=Nom|Number=Sing|Person=1|PronType=Prs'
            if re.match("^(em|m'|-me|'m|me|m)$", node.form, re.IGNORECASE):
                node.lemma = 'jo'
                node.feats = 'Case=Acc,Dat|Number=Sing|Person=1|PrepCase=Npr|PronType=Prs'
            if re.match("^mi$", node.form, re.IGNORECASE):
                node.lemma = 'jo'
                node.feats = 'Case=Acc|Number=Sing|Person=1|PrepCase=Pre|PronType=Prs'
            if re.match("^tu$", node.form, re.IGNORECASE):
                node.lemma = 'tu'
                node.feats = 'Case=Nom|Number=Sing|Person=2|Polite=Infm|PronType=Prs'
            if re.match("^(et|t'|-te|'t|te|t)$", node.form, re.IGNORECASE):
                node.lemma = 'tu'
                node.feats = 'Case=Acc,Dat|Number=Sing|Person=2|Polite=Infm|PrepCase=Npr|PronType=Prs'
            if re.match("^ti$", node.form, re.IGNORECASE):
                node.lemma = 'tu'
                node.feats = 'Case=Acc|Number=Sing|Person=2|Polite=Infm|PrepCase=Pre|PronType=Prs'
            # Strong forms of third person pronouns can be used as subjects or after preposition.
            # Do not mark them as nominative (because of the prepositions).
            if re.match("^ell$", node.form, re.IGNORECASE):
                node.lemma = 'ell'
                node.feats = 'Gender=Masc|Number=Sing|Person=3|PronType=Prs'
            if re.match("^ella$", node.form, re.IGNORECASE):
                node.lemma = 'ell'
                node.feats = 'Gender=Fem|Number=Sing|Person=3|PronType=Prs'
            if re.match("^(el|-lo|'l|lo)$", node.form, re.IGNORECASE):
                node.lemma = 'ell'
                node.feats = 'Case=Acc|Gender=Masc|Number=Sing|Person=3|PronType=Prs'
            if re.match("^(la|-la)$", node.form, re.IGNORECASE):
                node.lemma = 'ell'
                node.feats = 'Case=Acc|Gender=Fem|Number=Sing|Person=3|PronType=Prs'
            if re.match("^(l')$", node.form, re.IGNORECASE):
                node.lemma = 'ell'
                node.feats = 'Case=Acc|Gender=Fem,Masc|Number=Sing|Person=3|PronType=Prs'
            if re.match("^(ho|-ho)$", node.form, re.IGNORECASE):
                node.lemma = 'ell'
                node.feats = 'Case=Acc|Gender=Neut|Number=Sing|Person=3|PronType=Prs'
            if re.match("^(li|-li)$", node.form, re.IGNORECASE):
                node.lemma = 'ell'
                node.feats = 'Case=Dat|Number=Sing|Person=3|PronType=Prs'
            if re.match("^(es|s'|-se|'s|se|s)$", node.form, re.IGNORECASE):
                node.lemma = 'ell'
                node.feats = 'Case=Acc,Dat|Person=3|PrepCase=Npr|PronType=Prs|Reflex=Yes'
            if re.match("^si$", node.form, re.IGNORECASE):
                node.lemma = 'ell'
                node.feats = 'Case=Acc|Person=3|PrepCase=Pre|PronType=Prs|Reflex=Yes'
            # If nosaltres can be used after a preposition, we should not tag it as nominative.
            if re.match("^nosaltres$", node.form, re.IGNORECASE):
                node.lemma = 'jo'
                node.feats = 'Number=Plur|Person=1|PronType=Prs'
            # Nós is the majestic first person singular. In accusative and dative, it is identical to first person plural.
            if re.match("^nós$", node.form, re.IGNORECASE):
                node.lemma = 'jo'
                node.feats = 'Number=Sing|Person=1|Polite=Form|PronType=Prs'
            if re.match("^(ens|-nos|'ns|nos|ns)$", node.form, re.IGNORECASE):
                node.lemma = 'jo'
                node.feats = 'Case=Acc,Dat|Number=Plur|Person=1|PronType=Prs'
            if re.match("^vosaltres$", node.form, re.IGNORECASE):
                node.lemma = 'tu'
                node.feats = 'Number=Plur|Person=2|PronType=Prs'
            # Vós is the formal second person singular. In accusative and dative, it is identical to second person plural.
            # Vostè is even more formal than vós. In accusative and dative, it is identical to third person singular.
            if re.match("^(vós|vostè)$", node.form, re.IGNORECASE):
                node.lemma = 'tu'
                node.feats = 'Number=Sing|Person=2|Polite=Form|PronType=Prs'
            if re.match("^vostès$", node.form, re.IGNORECASE):
                node.lemma = 'tu'
                node.feats = 'Number=Plur|Person=2|Polite=Form|PronType=Prs'
            if re.match("^(us|-vos|-us|vos)$", node.form, re.IGNORECASE):
                node.lemma = 'tu'
                node.feats = 'Case=Acc,Dat|Number=Plur|Person=2|PronType=Prs'
            # Strong forms of third person pronouns can be used as subjects or after preposition.
            # Do not mark them as nominative (because of the prepositions).
            if re.match("^ells$", node.form, re.IGNORECASE):
                node.lemma = 'ell'
                node.feats = 'Gender=Masc|Number=Plur|Person=3|PronType=Prs'
            if re.match("^elles$", node.form, re.IGNORECASE):
                node.lemma = 'ell'
                node.feats = 'Gender=Fem|Number=Plur|Person=3|PronType=Prs'
            # Els is masculine accusative, or dative in any gender.
            if re.match("^(els|-los|'ls|los|ls)$", node.form, re.IGNORECASE):
                node.lemma = 'ell'
                node.feats = 'Case=Acc,Dat|Number=Plur|Person=3|PronType=Prs'
            if re.match("^(les|-les)$", node.form, re.IGNORECASE):
                node.lemma = 'ell'
                node.feats = 'Case=Acc|Gender=Fem|Number=Plur|Person=3|PronType=Prs'
            # There are also "adverbial" pronominal clitics that can occur at direct object positions.
            if re.match("^(en|n'|'n|-ne|n|ne)$", node.form, re.IGNORECASE):
                node.lemma = 'en'
                node.feats = 'Case=Gen|Person=3|PronType=Prs'
            if re.match("^(hi|-hi)$", node.form, re.IGNORECASE):
                node.lemma = 'hi'
                node.feats = 'Case=Loc|Person=3|PronType=Prs'

    def report_suspicious_lemmas(self, node):
        # There are offset issues of splitted multi_word_expressions.
        # Sometimes a word gets the lemma of the neighboring word.
        if node.form.lower()[:1] != node.lemma.lower()[:1]:
            # Exclude legitimate cases where the lemma starts with a different letter.
            hit = True
            if node.lemma == 'jo' and re.match("(em|ens|m'|me|mi|nos|nosaltres|'ns)", node.form, re.IGNORECASE):
                hit = False
            if node.lemma == 'tu' and re.match("(et|'t|us|vosaltres|vostè)", node.form, re.IGNORECASE):
                hit = False
            if node.lemma == 'el' and re.match("(la|l|l'|les)", node.form, re.IGNORECASE):
                hit = False
            if node.lemma == 'ell' and re.match("(hi|ho|'l|l'|la|-la|les|li|lo|-lo|los|'ls|'s|s'|se|-se|si)", node.form, re.IGNORECASE):
                hit = False
            if node.lemma == 'es' and re.match("(s|se)", node.form, re.IGNORECASE):
                hit = False
            if node.lemma == 'em' and re.match("('m|m|m')", node.form, re.IGNORECASE):
                hit = False
            if node.lemma == 'en' and re.match("('n|n'|ne|-ne)", node.form, re.IGNORECASE):
                hit = False
            if node.lemma == 'anar' and re.match("(va|van|vàrem)", node.form, re.IGNORECASE):
                hit = False
            if node.lemma == 'ser' and re.match("(és|era|eren|eres|érem|essent|estat|ets|foren|fos|fossin|fou)", node.form, re.IGNORECASE):
                hit = False
            if node.lemma == 'estar' and re.match("(sigut)", node.form, re.IGNORECASE):
                hit = False
            if node.lemma == 'caure' and re.match("(queia|queies|quèiem|quèieu|queien)", node.form, re.IGNORECASE):
                hit = False
            if node.lemma == 'ampli' and re.match("(àmplia|àmplies)", node.form, re.IGNORECASE):
                hit = False
            if node.lemma == 'indi' and re.match("(índies)", node.form, re.IGNORECASE):
                hit = False
            if node.lemma == 'obvi' and re.match("(òbvia)", node.form, re.IGNORECASE):
                hit = False
            if node.lemma == 'ossi' and re.match("(òssies)", node.form, re.IGNORECASE):
                hit = False
            if node.lemma == 'ús' and re.match("(usos)", node.form, re.IGNORECASE):
                hit = False
            # Form = '2001/37/CE', lemma = 'CE'
            # Form = 'nº5', lemma = '5'
            # Form = 'kg.', lemma = 'quilogram'
            # Form = 'un', lemma = '1'
            if node.lemma == 'CE' or re.match("nº", node.form, re.IGNORECASE) or re.match("^quil[oò]", node.lemma, re.IGNORECASE) or re.match("^[0-9]+$", node.lemma):
                hit = False
            if hit:
                print("Form = '%s', lemma = '%s', address = %s" % (node.form, node.lemma, node.address()))
