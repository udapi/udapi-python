"""Wrapper for MorphoDiTa (more pythonic than ufal.morphodita)."""
from collections import namedtuple

from ufal.morphodita import Morpho, TaggedLemmasForms, TaggedLemmas  # pylint: disable=no-name-in-module
from udapi.core.resource import require_file

FormInfo = namedtuple('FormInfo', 'form lemma tag guesser')


class MorphoDiTa:
    """Wrapper for MorphoDiTa."""

    def __init__(self, model):
        """Create the MorphoDiTa tool object."""
        self.model = model
        path = require_file(model)
        self.tool = Morpho.load(path)
        if not self.tool:
            raise IOError("Cannot load model from file '%s'" % path)

    def forms_of_lemma(self, lemma, tag_wildcard='?', guesser=True):
        """Return all forms (a list of FormInfo tuples) of a given lemma matching a given tag wildcard."""
        use_guesser = 1 if guesser else 0
        lemmas_forms = TaggedLemmasForms()
        used_guesser = self.tool.generate(lemma, tag_wildcard, use_guesser, lemmas_forms)
        forms = []
        for lemma_forms in lemmas_forms:
            for form in lemma_forms.forms:
                forms.append(FormInfo(form.form, lemma_forms.lemma, form.tag, used_guesser))
        return forms

    def analyze_form(self, form, guesser=True):
        """Return all lemma-tag analyses (a list of FormInfo tuples) of a given form."""
        use_guesser = 1 if guesser else 0
        tagged_lemmas = TaggedLemmas()
        used_guesser = self.tool.analyze(form, use_guesser, tagged_lemmas)
        result = []
        for tl in tagged_lemmas:
            result.append(FormInfo(form, tl.lemma, tl.tag, used_guesser))
        return result
