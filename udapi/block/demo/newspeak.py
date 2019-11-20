"""demo.Newspeak block for 1984-like newspeak-ization of Czech.

This is just a demo/draft.

Usage:
  $ echo 'Nejhorší žena je lepší než nejlepší muž.' | \
         udapy -q read.Sentences udpipe.Cs demo.Newspeak write.Sentences
  Převelenedobrá žena je veledobrá než převeledobrý muž.
"""
from udapi.core.block import Block
from udapi.tool.morphodita import MorphoDiTa

ANTONYMS = {
    'špatný': 'dobrý',
    'pomalý': 'rychlý',
    # 'muž': 'žena',  this does not work because xpos contains gender,
    # we would also need to exploit the parsing and change gender of all congruent adj children.
}


class Newspeak(Block):
    """Change all comparatives to vele-x and superlatives to převele-x."""

    def __init__(self, morphodita_path='models/morphodita/cs/',
                 morphodita_model='czech-morfflex-131112.dict',
                 **kwargs):
        """Create the PreVele block object."""
        super().__init__(**kwargs)
        self.morphodita = MorphoDiTa(model=morphodita_path + morphodita_model)

    def process_tree(self, tree):

        # apply process_node on all nodes
        super().process_tree(tree)

        # Capitalize if needed
        first_node = tree.descendants[0]
        if tree.text[0].isupper() and not first_node.form[0].isupper():
            first_node.form = first_node.form[0].upper() + first_node.form[1:]

        # Recompute the sentence string
        tree.text = tree.compute_text()

    def process_node(self, node):
        antonym = ANTONYMS.get(node.lemma)
        if antonym is not None:
            if node.xpos[11] == 'N':
                if node.form.lower().startswith('ne'):
                    node.lemma = antonym
                    node.xpos = node.xpos[:10] + 'A' + node.xpos[11:]
                    node.form = node.form[2:]
            else:
                forms = self.morphodita.forms_of_lemma(antonym, node.xpos)
                if forms:
                    node.lemma = antonym
                    node.xpos = node.xpos[:10] + 'N' + node.xpos[11:]
                    node.form = 'ne' + forms[0].form

        degree = node.feats["Degree"]
        if degree in ("Sup", "Cmp"):
            new_xpos = node.xpos[:9] + '1' + node.xpos[10:]
            forms = self.morphodita.forms_of_lemma(node.lemma, new_xpos)
            if forms:
                new_form = "vele" if degree == "Cmp" else "převele"
                new_form += forms[0].form
                node.form = new_form
