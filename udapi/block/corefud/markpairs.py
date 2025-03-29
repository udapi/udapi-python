from udapi.core.block import Block
import udapi.core.coref
import itertools
from collections import Counter
import logging

class MarkPairs(Block):
    """Find pairs of coreference mentions within the same sentence with given properties.
    Mark these pairs of mentions (using `misc["Mark"]`), so they can be further
    processed or printed.

    Usage:
    # Find pairs of mentions of the same entity within the same sentence:
    cat my.conllu | udapy -TM corefud.MarkPairs same_entity=1 | less -R

    Properties:
    same_entity - both mentions belong to the same entity (cluster)
    both_continuous - both mentions have continuous spans
    both_discontinuous - both mentions have discontinuous spans
    nested - span of one mention is nested (a subset of) in the span of the other mention
    crossing - spans are crossing (i.e. intersecting, but neither is subset of the other)
    interleaved - spans are interleaved (i.e. not intersecting, but neither span precedes the other)
    same_head - the same node is a head of both mentions
    same_span - both mentions have the same span (which is invalid according to UD's validate.py)
    same_subspan - at least one of the mentions is discontinuous and one of its subspans
                   is also a subspan (or span) of the other mention


    You can combine any number of properties.
    Each property can have one of the three values:
    include - this is the default value: include pairs with this property, i.e. ignore the property
    exclude - exclude (from the marking) pairs of mentions with this property
    only - pairs of mentions without this property will be excluded

    As a shortcut, you can use -1 and 1 instead of exclude and only, so e.g.
     nested=only same_head=exclude
    can be written as
     nested=1 same_head=-1
    """

    def __init__(self, same_entity=0, both_continuous=0, both_discontinuous=0,
                 nested=0, crossing=0, interleaved=0,
                 same_head=0, same_span=0, same_subspan=0,
                 print_form=False, print_total=True, log=True, mark=True, **kwargs):
        super().__init__(**kwargs)


        self.same_entity = self._convert(same_entity)
        self.both_continuous = self._convert(both_continuous)
        self.both_discontinuous = self._convert(both_discontinuous)
        self.nested = self._convert(nested)
        self.crossing = self._convert(crossing)
        self.interleaved = self._convert(interleaved)
        self.same_head = self._convert(same_head)
        self.same_span = self._convert(same_span)
        self.same_subspan = self._convert(same_subspan)

        self.print_form = print_form
        self.print_total = print_total
        self.log = log
        self.mark = mark
        self.counter = Counter()

    def _convert(self, value):
        if value in {-1, 0, 1}:
            return value
        if value == 'include':
            return 0
        if value == 'only':
            return 1
        if value == 'exclude':
            return -1
        raise ValueError('unknown value ' + value)

    def _ok(self, condition, value):
        if value == 0:
            return True
        return (condition and value == 1) or (not condition and value==-1)

    def _print(self, mention):
        if self.print_form:
            return mention.entity.eid + ':' + ' '.join([w.form for w in mention.words])
        else:
            return mention.entity.eid + ':' + mention.span

    def process_tree(self, tree):
        mentions = set()
        for node in tree.descendants_and_empty:
            for m in node.coref_mentions:
                mentions.add(m)
        self.counter['mentions'] += len(mentions)

        for mA, mB in itertools.combinations(mentions, 2):
            self.counter['pairs'] += 1
            if not self._ok(mA.entity == mB.entity, self.same_entity):
                continue
            if not self._ok(mA.head == mB.head, self.same_head):
                continue

            if self.both_continuous or self.both_discontinuous or self.same_span or self.same_subspan:
                sA, sB = mA.span, mB.span
                cA, cB = ',' not in sA, ',' not in sB
                if not self._ok(cA and cB, self.both_continuous):
                    continue
                if not self._ok(not cA and not cB, self.both_discontinuous):
                    continue
                if not self._ok(sA == sB, self.same_span):
                    continue
                if not self._ok(set(sA.split(',')).intersection(set(sB.split(','))), self.same_subspan):
                    continue

            if self.nested or self.crossing or self.interleaved:
                wA, wB = set(mA.words), set(mB.words)
                if not self._ok(wA <= wB or wB <= wA, self.nested):
                    continue
                if not self._ok(wA.intersection(wB) and not wA <= wB and not wB <= wA, self.crossing):
                    continue
                if self.interleaved:
                    a_precedes_b = mA.words[0] < mB.words[0] and mA.words[-1] < mB.words[0]
                    b_precedes_a = mB.words[0] < mA.words[0] and mB.words[-1] < mA.words[0]
                    if not self._ok(not wA.intersection(wB) and not a_precedes_b and not b_precedes_a, self.interleaved):
                        continue

            self.counter['matching'] += 1
            if self.mark:
                for w in mA.words + mB.words:
                    w.misc['Mark'] = 1
                mA.words[0].misc['Mark'] = f"{self._print(mA)}+{self._print(mB)}"
            if self.log:
                logging.info(f"Found mentions at {tree.sent_id}: {self._print(mA)} + {self._print(mB)}")

    def after_process_document(self, doc):
        if self.print_total:
            #if self.max_trees and seen_trees > self.max_trees:
            #    print(f'######## Only first {self.max_trees} matching mentions printed. Use max_trees=0 to see all.')
            msg = f'######## Mentions = {self.counter["mentions"]}, matching/all pairs = {self.counter["matching"]} / {self.counter["pairs"]}'
            logging.info(msg)
            doc.meta["corefud.MarkPairs"] = msg
