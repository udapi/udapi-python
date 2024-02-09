from udapi.core.block import Block
import udapi.core.coref
import logging

class FixEntityAcrossNewdoc(Block):
    """
    Fix the error reported by validate.py --coref:
    "[L6 Coref entity-across-newdoc] Same entity id should not occur in multiple documents"
    by making the entity IDs (eid) unique in each newdoc document.

    This block uses Udapi's support for loading GUM-like GRP document-wide IDs
    (so the implementation is simple, although unnecessarily slow).
    After applying this block, IDs of all entities are prefixed with document numbers,
    e.g. "e45" in the 12th document changes to "d12.e45".
    If you prefer simple eid, use corefud.IndexClusters afterwards.
    """

    def process_document(self, doc):
        if not doc.eid_to_entity:
            logging.warning(f"No entities in document {doc.meta}")
        udapi.core.coref.store_coref_to_misc(doc)
        assert doc.meta["global.Entity"].startswith("eid")
        doc.meta["global.Entity"] = "GRP" + doc.meta["global.Entity"][3:]
        udapi.core.coref.load_coref_from_misc(doc)
        doc.meta["global.Entity"] = "eid" + doc.meta["global.Entity"][3:]
