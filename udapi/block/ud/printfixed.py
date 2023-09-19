"""
Block PrintFixed prints occurrences of fixed multiword expressions in UD. It
can be run twice in a row, first collecting known fixed expressions and then
also reporting other occurrences of these expressions where they are not
annotated as fixed.

Usage:
udapy ud.PrintFixed only_forms=1 < in.conllu | sort -u > fixed_expressions.txt
udapy ud.PrintFixed known_expressions=fixed_expressions.txt < in.conllu | sort | uniq -c | less

Author: Dan Zeman
"""
from udapi.core.block import Block
import re
import logging

class PrintFixed(Block):
    """
    Print fixed multiword expressions.
    """

    def __init__(self, only_forms=False, known_expressions=None, **kwargs):
        """
        Create the PrintFixed block.

        Parameters:
        only_forms=1: print the word forms but not tags and other info;
            This can be used to create the list of known forms that we want to
            identify even if they are not annotated as fixed.
        known_expressions: the name of the text file with the expressions
        """
        super().__init__(**kwargs)
        self.only_forms = only_forms
        self.known_expressions = {}
        self.first_words = {}
        self.max_length = 2
        if known_expressions:
            fh = open(known_expressions, 'r', encoding='utf-8')
            n = 0
            for expression in fh.readlines():
                expression = expression.replace('\n', '')
                if expression in self.known_expressions:
                    self.known_expressions[expression] += 1
                else:
                    self.known_expressions[expression] = 1
                    logging.info("Read known fixed expression '%s'" % expression)
                    n += 1
                words = expression.split(' ')
                first_word = words[0]
                self.first_words[first_word] = 1
                length = len(words)
                if length > self.max_length:
                    self.max_length = length
            logging.info('Read %d known fixed expressions.' % n)

    def process_node(self, node):
        fixed_children = [x for x in node.children if x.udeprel == 'fixed']
        if len(fixed_children) > 0:
            # Fixed children are always to the right of of the parent. But there
            # may be other nodes in between that are not fixed children (for
            # example, there may be punctuation that is attached to one of the
            # fixed nodes).
            n = node
            list_of_forms = [node.form.lower()]
            list_of_tags = [node.upos]
            while n != fixed_children[-1]:
                n = n.next_node
                if n.parent == node and n.udeprel == 'fixed':
                    list_of_forms.append(n.form.lower())
                    list_of_tags.append(n.upos)
                else:
                    list_of_forms.append('X')
                    list_of_tags.append('X')
            forms = ' '.join(list_of_forms)
            tags = ' '.join(list_of_tags)
            if self.only_forms:
                print(forms)
            else:
                print("%s / %s / %s" % (forms, tags, node.deprel))
        else:
            # If this is not the first word of a fixed expression, check whether
            # something that looks like a known fixed expression starts here.
            # Note that it is also possible that a known expression starts here
            # but only a subset is actually marked as such; we currently do not
            # account for this.
            if node.form.lower() in self.first_words:
                n = node
                list_of_forms = [node.form.lower()]
                list_of_tags = [node.upos]
                for i in range(self.max_length - 1):
                    n = n.next_node
                    if not n:
                        break
                    ###!!! At present we cannot identify known expressions with gaps ('X').
                    list_of_forms.append(n.form.lower())
                    list_of_tags.append(n.upos)
                    forms = ' '.join(list_of_forms)
                    if forms in self.known_expressions:
                        if self.only_forms:
                            print(forms)
                        else:
                            tags = ' '.join(list_of_tags)
                            print("%s / %s / NOT FIXED" % (forms, tags))
                        break
