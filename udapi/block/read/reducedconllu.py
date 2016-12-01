#!/usr/bin/env python

import logging
import codecs
import re

from conllu import Conllu


class ReducedConllu(Conllu):
    """
    A reader of the reduced Conll-u files.

    """
    def __init__(self, args=None):
        Conllu.__init__(self, args)

        # Here is the reduced list of the data fields as appear in the Conllu reduced format.
        self.node_attributes = ["ord", "form", "upostag", "head", "deprel"]
