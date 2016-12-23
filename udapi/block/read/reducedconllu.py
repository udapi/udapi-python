from udapi.block.read.conllu import Conllu


class ReducedConllu(Conllu):
    """
    A reader of the reduced Conll-u files.

    """

    def __init__(self, args=None):
        super(ReducedConllu, self).__init__(args)

        # Here is the reduced list of the data fields as appear in the Conllu
        # reduced format.
        self.node_attributes = ["ord", "form", "upostag", "head", "deprel"]
