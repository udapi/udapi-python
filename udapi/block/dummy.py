from udapi.core.block import Block

class Dummy(Block):
    def process_tree(self,root):
        for node in root.descendants():
            # print node.lemma
            pass

