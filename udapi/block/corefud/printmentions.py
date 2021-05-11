from udapi.core.block import Block
import udapi.core.coref

class PrintMentions(Block):
    """Print mentions with various properties."""

    def __init__(self, continuous='include', treelet='include',
                 oneword='include', singleton='include', **kwargs):
        super().__init__(**kwargs)
        self.continuous = self._convert(continuous)
        self.treelet = self._convert(treelet)
        self.oneword = self._convert(oneword)
        self.singleton = self._convert(singleton)


    def _convert(self, value):
        if value in {'include', 'exclude', 'only'}:
            return value
        if value == 1:
            return 'only'
        if value == 0:
            return 'exclude'
        raise ValueError('unknown value ' + value)

    def _ok(self, condition, value):
        if value == 'include':
            return True
        return (condition and value == 'only') or (not condition and value=='exclude')

    def process_document(self, doc):
        for cluster in doc.coref_clusters.values():
            if not self._ok(len(cluster.mentions) == 1, self.singleton):
                continue

            for mention in cluster.mentions:
                if not self._ok(len(mention.words) == 1, self.oneword):
                    continue
                if not self._ok(',' not in mention.span, self.continuous):
                    continue

                heads, mwords = 0, set(mention.words)
                for w in mention.words:
                    if w.parent:
                        heads += 0 if w.parent in mwords else 1
                    else:
                        heads += 0 if any(d['parent'] in mwords for d in w.deps) else 1
                if not self._ok(heads <= 1, self.treelet):
                    continue

                for w in mention.words:
                    w.misc['Mark'] = 1
                mention.head.root.draw()
                for w in mention.words:
                    del w.misc['Mark']

