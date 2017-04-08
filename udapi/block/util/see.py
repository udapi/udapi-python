"""Block util.See prints statistics about the nodes matching a given condition.

Example usage from the command line::

udapy util.See node='node.is_nonprojective()' n=3 \
 stats=dir,children,c_upos,p_lemma,deprel,feats_split < in.conllu

Example output::

node.is_nonprojective()
matches 245 out of 35766 nodes (0.7%) in 174 out of 1478 trees (11.8%)
=== dir (2 values) ===
          right   193  78% delta=+37%
           left    52  21% delta=-33%
=== children (9 values) ===
              0    64  26% delta=-38%
              2    58  23% delta=+14%
              3    38  15% delta= +7%
=== c_upos (15 values) ===
           NOUN   118  23% delta= +4%
            DET    61  12% delta= -3%
          PROPN    47   9% delta= +1%
=== p_lemma (187 values) ===
             il     5   2% delta= +1%
       fonction     4   1% delta= +1%
         écrire     4   1% delta= +1%
=== deprel (22 values) ===
          appos    41  16% delta=+15%
           conj    41  16% delta=+13%
          punct    36  14% delta= +4%
=== feats_split (20 values) ===
    Number=Sing   114  21% delta= +2%
    Gender=Masc    81  15% delta= +3%
              _    76  14% delta= -6%

In addition to absolute counts for each value, the percentage within matching nodes is printed
and a delta relative to percentage within all nodes.
This helps to highlight what is special about the matching nodes.
"""
from collections import Counter
import re  # may be useful in eval, thus pylint: disable=unused-import

from udapi.core.block import Block

STATS = 'dir,edge,depth,children,siblings,p_upos,p_lemma,c_upos,form,lemma,upos,deprel,feats_split'

# We need eval in this block
# pylint: disable=eval-used


class See(Block):
    """Print statistics about the nodes specified by the parameter `node`."""

    def __init__(self, node, n=5, stats=STATS, **kwargs):
        """Args:
        `node`: Python expression to be evaluated for each node and if True,
            the node will be considered "matching".
        `n`: Top n values will be printed for each statistic.
        `stats`: a list of comma-separated statistics to be printed.
            A statistic can be an attribute (`form`, `lemma`) or a pseudo-attribute
            (`depth` = depth of a node in dependency tree,
            `children` = number of children nodes,
            `p_lemma` = lemma of a parent node, etc).
            See `udapi.core.Node.get_attrs` for a full list of statistics.
        """
        super().__init__(**kwargs)
        self.node = node
        self.n_limit = n
        self.stats = stats.split(',')
        self.match = dict()
        self.every = dict()
        for stat in self.stats:
            self.match[stat] = Counter()
            self.every[stat] = Counter()
        self.overall = Counter()

    def process_tree(self, root):
        self.overall['trees'] += 1
        tree_match = False
        for node in root.descendants:
            matching = self.process_node(node)
            self.overall['nodes'] += 1
            if matching:
                self.overall['matching_nodes'] += 1
                if not tree_match:
                    self.overall['matching_trees'] += 1
                    tree_match = True

    def process_node(self, node):
        matching = eval(self.node)
        for stat in self.stats:
            for value in node.get_attrs([stat], undefs=''):
                self.every[stat][value] += 1
                self.every[stat]['T O T A L'] += 1
                if matching:
                    self.match[stat][value] += 1
                    self.match[stat]['T O T A L'] += 1
        return matching

    def process_end(self):
        print(self.node)
        print("matches %d out of %d nodes (%.1f%%) in %d out of %d trees (%.1f%%)"
              % (self.overall['matching_nodes'],
                 self.overall['nodes'],
                 self.overall['matching_nodes'] * 100 / self.overall['nodes'],
                 self.overall['matching_trees'],
                 self.overall['trees'],
                 self.overall['matching_trees'] * 100 / self.overall['trees']))
        for stat in self.stats:
            vals = len(self.match[stat].keys()) - 1
            print("=== %s (%d value%s) ===" % (stat, vals, 's' if vals > 1 else ''))
            match_total = self.match[stat]['T O T A L'] or 1
            every_total = self.every[stat]['T O T A L'] or 1
            for value, match_count in self.match[stat].most_common(self.n_limit + 1):
                if value == 'T O T A L':
                    continue
                every_count = self.every[stat][value]
                match_perc = 100 * match_count / match_total
                every_perc = 100 * every_count / every_total
                print("%15s %5d %3d%% delta=%+3d%%"
                      % (value, match_count, match_perc, match_perc - every_perc))
