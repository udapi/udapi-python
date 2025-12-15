from udapi.core.block import Block
import udapi.core.coref

class Load(Block):
    """Load coreference-related MISC attributes into memory. Allow lenient mode by strict=0."""

    def __init__(self, strict=True):
        self.strict = strict

    def process_document(self, doc):
        if doc._eid_to_entity is None:
            udapi.core.coref.load_coref_from_misc(doc, self.strict)
