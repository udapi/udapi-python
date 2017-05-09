"""tutorial.Parse block template.

Usage:
udapy read.Conllu zone=gold files=sample.conllu \
      read.Conllu zone=pred files=sample.conllu \
      transform.Flatten zones=pred \
      tutorial.Parse zones=pred \
      eval.Parsing gold_zone=gold \
      util.MarkDiff gold_zone=gold \
      write.TextModeTreesHtml marked_only=1 files=parse-diff.html
"""
from udapi.core.block import Block

class Parse(Block):
    """Dependency parsing."""

    def process_tree(self, root):
        # TODO: Your task: implement a better heuristics than "right chain"
        for node in root.descendants:
            if node.next_node:
                node.parent = node.next_node
                node.deprel = 'root'
