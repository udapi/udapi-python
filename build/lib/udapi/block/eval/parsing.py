"""Block eval.Parsing for evaluating UAS and LAS - gold and pred must have the same tokens."""
from udapi.core.basewriter import BaseWriter


class Parsing(BaseWriter):
    """Evaluate labeled and unlabeled attachment score (LAS and UAS)."""

    def __init__(self, gold_zone, **kwargs):
        """Create the eval.Parsing block object."""
        super().__init__(**kwargs)
        self.gold_zone = gold_zone
        self.correct_las, self.correct_ulas, self.correct_uas, self.total = 0, 0, 0, 0

    def process_tree(self, tree):
        gold_tree = tree.bundle.get_tree(self.gold_zone)
        if tree == gold_tree:
            return
        pred_nodes = tree.descendants
        gold_nodes = gold_tree.descendants
        if len(pred_nodes) != len(gold_nodes):
            raise ValueError('The sentences do not match (%d vs. %d nodes)'
                             % (len(pred_nodes), len(gold_nodes)))

        self.total += len(pred_nodes)
        for pred_node, gold_node in zip(pred_nodes, gold_nodes):
            if pred_node.parent.ord == gold_node.parent.ord:
                self.correct_uas += 1
                if pred_node.deprel == gold_node.deprel:
                    self.correct_las += 1
                if pred_node.udeprel == gold_node.udeprel:
                    self.correct_ulas += 1


    def process_end(self):
        # Redirect the default filehandle to the file specified by self.files
        self.before_process_document(None)
        print('nodes = %d' % self.total)
        print('UAS           = %6.2f' % (100 * self.correct_uas / self.total))
        print('LAS (deprel)  = %6.2f' % (100 * self.correct_las / self.total))
        print('LAS (udeprel) = %6.2f' % (100 * self.correct_ulas / self.total))
