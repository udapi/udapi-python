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
# nickname = xy123
# TODO: make up a unique nickname and edit the previous line
# if you want your results to be listed on the NPFL070 web (under that nickname).
# Delete the line if you don't want to listed on the web.
from udapi.core.block import Block

class Parse(Block):
    """Dependency parsing."""

    def __init__(self, language='en', **kwargs):
        super().__init__(**kwargs)
        self.language = language

    def process_tree(self, root):
        # TODO: Your task: implement a better heuristics than "right chain"
        for node in root.descendants:
            if node.next_node:
                node.parent = node.next_node
                node.deprel = 'root'
