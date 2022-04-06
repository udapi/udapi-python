import random
from collections import Counter
from udapi.core.block import Block
from udapi.block.write.textmodetreeshtml import TextModeTreesHtml
from udapi.block.write.textmodetrees import TextModeTrees

class PrintMentions(Block):
    """Print mentions with various properties."""

    def __init__(self, continuous='include', almost_continuous='include', treelet='include',
                 forest='include', almost_forest='include', oneword='include', singleton='include',
                 empty='include', max_trees=0, html=False, shuffle=True, print_other_forms=5,
                 print_total=True,
                 print_sent_id=True, print_text=True, add_empty_line=True, indent=1,
                 minimize_cross=True, color=True, attributes='form,upos,deprel',
                 print_undef_as='_', print_doc_meta=True, print_comments=False,
                 mark='(Mark)', hints=True, layout='classic',
                 **kwargs):
        super().__init__(**kwargs)
        self.continuous = self._convert(continuous)
        self.almost_continuous = self._convert(almost_continuous)
        self.treelet = self._convert(treelet)
        self.forest = self._convert(forest)
        self.almost_forest = self._convert(almost_forest)
        self.oneword = self._convert(oneword)
        self.singleton = self._convert(singleton)
        self.empty = self._convert(empty)

        self.max_trees = max_trees
        self.html = html
        self.shuffle = shuffle
        if shuffle:
            random.seed(42)
        self.print_other_forms = print_other_forms
        self.print_total = print_total,
        print_class = TextModeTreesHtml if html else TextModeTrees
        self.print_block = print_class(
                print_sent_id=print_sent_id, print_text=print_text, add_empty_line=add_empty_line, indent=indent,
                minimize_cross=minimize_cross, color=color, attributes=attributes,
                print_undef_as=print_undef_as, print_doc_meta=print_doc_meta, print_comments=print_comments,
                mark=mark, hints=hints, layout=layout)

    def _convert(self, value):
        if value in {'include', 'exclude', 'only'}:
            return value
        if value == 1:
            return 'only'
        if value == 0:
            return 'exclude'
        raise ValueError('unknown value ' + value)

    def before_process_document(self, document):
        self.print_block.before_process_document(document)

    def after_process_document(self, document):
        self.print_block.after_process_document(document)

    def _ok(self, condition, value):
        if value == 'include':
            return True
        return (condition and value == 'only') or (not condition and value=='exclude')

    def _is_auxiliary_etc(self, node):
        if node.udeprel in {'case', 'cc', 'punct', 'conj', 'mark', 'appos', 'vocative'}:
            return True
        if node.udeprel == 'dep' and node.upos in {'ADP', 'SCONJ', 'CCONJ', 'PUNCT'}:
            return True
        return False

    def _is_forest(self, mention, mwords, almost):
        for w in mention.words:
            # UD unfortunatelly does not use the copula-as-head style for copula construction,
            # so e.g. in "It is my fault", "fault" is the root of the tree and all other words its children.
            # However, in the cop-as-head stule, only "my" would depend on "fault" (and should be part of the mention).
            # It is difficult to tell apart which w.children are related to w and which to the copula.
            # We thus ignore these cases completely (we expect any child is potentially related to the copula).
            if any(ch.udeprel == 'cop' for ch in w.children):
                continue
            for ch in w.children:
                if ch not in mwords:
                    if not almost:
                        return False
                    if not (w.parent and w.parent not in mwords and self._is_auxiliary_etc(ch)):
                        return False
        return True

    def _is_almost_continuous(self, mention):
        if ',' not in mention.span:
            return True
        nonempty = [w for w in mention.words if not w.is_empty()]
        if not nonempty:
            return True
        mwords = set(mention.words)
        gap_nodes = [w for w in mention.head.root.descendants if w > nonempty[0] and w < nonempty[-1] and not w in mwords]
        for gap_node in gap_nodes:
            if not gap_node.is_empty():
                return False
        return True

    def process_document(self, doc):
        mentions = []
        for entity in doc.coref_entities:
            if self._ok(len(entity.mentions) == 1, self.singleton):
                mentions.extend(entity.mentions)
        if self.shuffle:
            random.shuffle(mentions)
        else:
            mentions.sort()

        seen_trees = 0
        for mention in mentions:
            if not self._ok(len(mention.words) == 1, self.oneword):
                continue
            if not self._ok(',' not in mention.span, self.continuous):
                continue
            if self.almost_continuous != 'include' and not self._ok(self._is_almost_continuous(mention), self.almost_continuous):
                continue

            empty_mwords = [w for w in mention.words if w.is_empty()]
            if not self._ok(len(empty_mwords) > 0, self.empty):
                continue

            heads, mwords = 0, set(mention.words)
            for w in mention.words:
                if w.parent:
                    heads += 0 if w.parent in mwords else 1
                else:
                    heads += 0 if any(d['parent'] in mwords for d in w.deps) else 1
            if not self._ok(heads <= 1, self.treelet):
                continue
            if self.forest != 'include' and not self._ok(self._is_forest(mention, mwords, False), self.forest):
                continue
            if self.almost_forest != 'include' and not self._ok(self._is_forest(mention, mwords, True), self.almost_forest):
                continue

            for w in mention.words:
                w.misc['Mark'] = 1

            seen_trees += 1
            if self.max_trees and seen_trees > self.max_trees:
                if not self.print_total:
                    print(f'######## Only first {self.max_trees} matching mentions printed. Use max_trees=0 to see all.')
                    return
            else:
                this_form = ' '.join([w.form for w in mention.words])
                print("# Mention = " + this_form)
                if self.print_other_forms:
                    counter = Counter()
                    for m in mention.entity.mentions:
                        forms = ' '.join([w.form for w in m.words])
                        if forms != this_form:
                            counter[forms] += 1
                    if counter:
                        print(f"# {min(len(counter), self.print_other_forms)} other forms:", end='')
                        for form, count in counter.most_common(self.print_other_forms):
                            print(f' "{form}"({count})', end='')
                        print()
                self.print_block.process_tree(mention.head.root)
                for w in mention.words:
                    del w.misc['Mark']

        if self.print_total:
            if self.max_trees and seen_trees > self.max_trees:
                print(f'######## Only first {self.max_trees} matching mentions printed. Use max_trees=0 to see all.')
            print(f'######## Total matching/all mentions = {seen_trees} / {len(mentions)}')

