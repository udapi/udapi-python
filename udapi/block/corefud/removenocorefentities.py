from udapi.core.block import Block
import udapi.core.coref
import re
import logging

class RemoveNoCorefEntities(Block):
    """
    Some corpora (e.g., AnCora) include annotation of named entities that are
    not annotated for coreference. To distinguish them, their cluster ID starts
    with 'NOCOREF' (optionally followed by entity type, so that one cluster
    still has just one type). We may want to remove such entities from datasets
    that are used to train coreference resolves, to prevent the resolvers from
    thinking that all members of a NOCOREF cluster are coreferential. That is
    what this block does.
    """

    def process_document(self, doc):
        entities = doc.coref_entities
        if not entities:
            return
        doc._eid_to_entity = {e._eid: e for e in entities if not re.match(r'^NOCOREF', e.eid)}
