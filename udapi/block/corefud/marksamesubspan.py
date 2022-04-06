from udapi.core.block import Block
import udapi.core.coref
import itertools

class MarkSameSubSpan(Block):
    """Find mentions with the same subspan."""

    def __init__(self, same_entity_only=False, both_discontinuous=False, print_form=False, nested_only=False,
                 log=True, mark=True, **kwargs):
        super().__init__(**kwargs)
        self.same_entity_only = same_entity_only
        self.both_discontinuous = both_discontinuous
        self.nested_only = nested_only
        self.print_form = print_form
        self.log = log
        self.mark = mark

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
        if len(mentions) > 1:
            for mA, mB in itertools.combinations(mentions, 2):
                if self.same_entity_only and mA.entity != mB.entity:
                    continue
                if self.both_discontinuous and (',' not in mA.span or ',' not in mB.span):
                    continue
                sA, sB = set(mA.words), set(mB.words)
                if self.nested_only and not (sA <= sB) and not (sB <= sA):
                    continue
                if not set(mA.span.split(',')).intersection(set(mB.span.split(','))):
                    continue
                if self.mark:
                    for w in mA.words + mB.words:
                        w.misc['Mark'] = 1
                    mA.words[0].misc['Mark'] = f"{self._print(mA)}+{self._print(mB)}"
                if self.log:
                    print(f"same-subspan mentions at {tree.sent_id}: {self._print(mA)} + {self._print(mB)}")
