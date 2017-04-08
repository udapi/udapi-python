"""Block GoeswithFromText for splitting nodes and attaching via goeswith according to the text.

Usage:
udapy -s ud.GoeswithFromText < in.conllu > fixed.conllu

Author: Martin Popel
"""
import logging

from udapi.core.block import Block


class GoeswithFromText(Block):
    """Block for splitting nodes and attaching via goeswith according to the the sentence text.

    For example::
    # text = Never the less, I agree.
    1 Nevertheless nevertheless ADV   _ _ 4 advmod _ SpaceAfter=No
    2 ,            ,            PUNCT _ _ 4 punct  _ _
    3 I            I            PRON  _ _ 4 nsubj  _ _
    4 agree        agree        VERB  _ _ 0 root   _ SpaceAfter=No
    5 .            .            PUNCT _ _ 4 punct  _ _

    is changed to::
    # text = Never the less, I agree.
    1 Never  never ADV   _ _ 6 advmod   _ _
    2 the    the   ADV   _ _ 1 goeswith _ _
    3 less   less  ADV   _ _ 1 goeswith _ SpaceAfter=No
    4 ,      ,     PUNCT _ _ 6 punct    _ _
    5 I      I     PRON  _ _ 6 nsubj    _ _
    6 agree  agree VERB  _ _ 0 root     _ SpaceAfter=No
    7 .      .     PUNCT _ _ 6 punct    _ _

    If used with parameter `keep_lemma=1`, the result is::
    # text = Never the less, I agree.
    1 Never  nevertheless ADV   _ _ 6 advmod   _ _
    2 the    _            ADV   _ _ 1 goeswith _ _
    3 less   _            ADV   _ _ 1 goeswith _ SpaceAfter=No
    4 ,      ,            PUNCT _ _ 6 punct    _ _
    5 I      I            PRON  _ _ 6 nsubj    _ _
    6 agree  agree        VERB  _ _ 0 root     _ SpaceAfter=No
    7 .      .            PUNCT _ _ 6 punct    _ _
    """

    def __init__(self, keep_lemma=False, **kwargs):
        super().__init__(**kwargs)
        self.keep_lemma = keep_lemma

    # pylint: disable=too-many-branches
    def process_tree(self, root):
        text = root.text
        computed = root.compute_text()
        if text == computed:
            return

        nospace_text = text.replace(' ', '')
        if nospace_text != computed.replace(' ', ''):
            logging.warning('Mismatch of the stored and computed text cannot be solved with '
                            ' ud.AddGoeswithFromText:\n<<%s>>\n<<%s>>', text, computed)
            return

        # Normalize the stored text (double space -> single space)
        text = ' '.join(text.split())

        for node in root.token_descendants:
            nospace_form = node.form.replace(' ', '')
            if text.startswith(node.form):
                text = text[len(node.form):]
                nospace_text = nospace_text[len(nospace_form):]
                if not text or text[0].isspace():
                    del node.misc['SpaceAfter']
                    text = text.lstrip()
                else:
                    node.misc['SpaceAfter'] = 'No'
            elif nospace_text.startswith(nospace_form):
                nospace_text = nospace_text[len(nospace_form):]
                len_raw_form = len(nospace_form)
                while text[:len_raw_form].replace(' ', '') != nospace_form:
                    len_raw_form += 1
                    assert len_raw_form <= len(text)
                raw_form = text[:len_raw_form]
                text = text[len_raw_form:]
                tokens = raw_form.split(' ')
                node.form = tokens[0]
                if not self.keep_lemma:
                    node.lemma = tokens[0].lower()
                del node.misc['SpaceAfter']
                last_node = node
                for token in tokens[1:]:
                    lemma = None if self.keep_lemma else token
                    child = node.create_child(form=token, lemma=lemma, upos=node.upos,
                                              xpos=node.xpos, deprel='goeswith')
                    child.shift_after_node(last_node)
                    last_node = child
                if not text or text[0].isspace():
                    text = text.lstrip()
                else:
                    last_node.misc['SpaceAfter'] = 'No'
            else:
                assert False  # we have checked the whole sentence already
        if text:
            logging.warning('Extra text "%s" in tree %s', text, root)
