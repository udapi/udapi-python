from udapi.core.block import Block
from collections import Counter

class Stats(Block):
    """Block corefud.Stats prints various coreference-related statistics."""

    def __init__(self, m_len_max=5, c_len_max=5, report_mentions=True, report_entities=True,
                 report_details=True, selected_upos='NOUN PRON PROPN DET ADJ VERB ADV NUM',
                 exclude_singletons=False, exclude_nonsingletons=False, style='human', **kwargs):
        super().__init__(**kwargs)
        self.m_len_max = m_len_max
        self.c_len_max = c_len_max
        self.report_mentions = report_mentions
        self.report_entities = report_entities
        self.report_details = report_details
        self.exclude_singletons = exclude_singletons
        self.exclude_nonsingletons = exclude_nonsingletons
        self.style = style
        if style not in 'tex human'.split():
            raise ValueError(f'Unknown style f{style}')

        self.counter = Counter()
        self.mentions = 0
        self.entities = 0
        self.total_nodes = 0
        self.longest_mention = 0
        self.longest_entity = 0
        self.m_words = 0
        self.selected_upos = None if selected_upos == 'all' else selected_upos.split()

    def process_document(self, doc):
        self.total_nodes += len(list(doc.nodes))
        for entity in doc.coref_entities:
            len_mentions = len(entity.mentions)
            if len_mentions == 1 and self.exclude_singletons:
                continue
            elif len_mentions > 1 and self.exclude_nonsingletons:
                continue
            self.longest_entity = max(len_mentions, self.longest_entity)
            self.counter['c_total_len'] += len_mentions
            self.counter[f"c_len_{min(len_mentions, self.c_len_max)}"] += 1

            self.entities += 1
            if not self.report_mentions and not self.report_details:
                continue
            for mention in entity.mentions:
                self.mentions += 1
                all_words = len(mention.words)
                non_empty = len([w for w in mention.words if not w.is_empty()])
                self.m_words += all_words
                self.longest_mention = max(non_empty, self.longest_mention)
                self.counter['m_total_len'] += non_empty
                self.counter[f"m_len_{min(non_empty, self.m_len_max)}"] += 1
                if self.report_details:
                    upos = 'other'
                    if not self.selected_upos or mention.head.upos in self.selected_upos:
                        upos = mention.head.upos
                    self.counter['m_head_upos_' + upos] += 1
                    self.counter['m_with_empty'] += 1 if all_words > non_empty else 0
                    self.counter['m_with_gaps'] += 1 if ',' in mention.span else 0
                    heads, mwords = 0, set(mention.words)
                    for w in mention.words:
                        if w.parent:
                            heads += 0 if w.parent in mwords else 1
                        else:
                            heads += 0 if any(d['parent'] in mwords for d in w.deps) else 1
                    self.counter['m_nontreelet'] += 1 if heads > 1 else 0

    def process_end(self):
        mentions_nonzero = 1 if self.mentions == 0 else self.mentions
        entities_nonzero = 1 if self.entities == 0 else self.entities
        total_nodes_nonzero = 1 if self.total_nodes == 0 else self.total_nodes

        columns =[ ]
        if self.report_entities:
            columns += [('entities', f"{self.entities:7,}"),
                        ('entities_per1k', f"{1000 * self.entities / total_nodes_nonzero:6.0f}"),
                        ('longest_entity', f"{self.longest_entity:6}"),
                        ('avg_entity', f"{self.counter['c_total_len'] / entities_nonzero:5.1f}")]
            for i in range(1, self.c_len_max + 1):
                percent = 100 * self.counter[f"c_len_{i}"] / entities_nonzero
                columns.append((f"c_len_{i}{'' if i < self.c_len_max else '+'}", f"{percent:5.1f}"))
        if self.report_mentions:
            columns += [('mentions', f"{self.mentions:7,}"),
                        ('mentions_per1k', f"{1000 * self.mentions / total_nodes_nonzero:6.0f}"),
                        ('longest_mention', f"{self.longest_mention:6}"),
                        ('avg_mention', f"{self.counter['m_total_len'] / mentions_nonzero:5.1f}")]
            for i in range(0, self.m_len_max + 1):
                percent = 100 * self.counter[f"m_len_{i}"] / mentions_nonzero
                columns.append((f"m_len_{i}{'' if i < self.m_len_max else '+'}", f"{percent:5.1f}"))
        if self.report_details:
            columns += [('with_empty', f"{100 * self.counter['m_with_empty'] / mentions_nonzero:5.1f}"),
                        ('with_gaps', f"{100 * self.counter['m_with_gaps'] / mentions_nonzero:5.1f}"),
                        ('nontreelet', f"{100 * self.counter['m_nontreelet'] / mentions_nonzero:5.1f}"),]
            if self.selected_upos:
                upos_list = self.selected_upos + ['other']
            else:
                upos_list = [x[12:] for x in self.counter if x.startswith('m_head_upos_')]
            for upos in upos_list:
                columns.append(('head_upos=' + upos, f"{100 * self.counter['m_head_upos_' + upos] / mentions_nonzero:5.1f}"))

        if self.style == 'tex':
            print(" & ".join(c[1] for c in columns))
        elif self.style == 'human':
            for c in columns:
                print(f"{c[0]:>15} = {c[1].strip():>10}")
