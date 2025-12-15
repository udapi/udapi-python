"""Block corefud.IndexClusters"""
from udapi.core.block import Block


class IndexClusters(Block):
    """Re-index the coreference entity IDs (eid). The final entity IDs are of the "e<ID>" form,
       where <ID> are ordinal numbers starting from the one specified by the `start` parameter.
       This block can be applied on multiple documents within one udapy call.
       For example, to re-index eid in all conllu files in the current directory
       (keeping the IDs unique across all the files), use:
       `udapy read.Conllu files='!*.conllu' corefud.IndexClusters write.Conllu overwrite=1`

       Parameters:
       -----------
       start : int
            the starting index (default=1)
       prefix : str
            prefix of the IDs before the number (default="e")
    """

    def __init__(self, start=1, prefix='e'):
        self.start = start
        self.prefix = prefix

    def process_document(self, doc):
        entities = doc.coref_entities
        if not entities:
            return
        new_eid_to_entity = {}
        for idx, entity in enumerate(entities, self.start):
            new_eid = self.prefix + str(idx)
            entity.eid = new_eid
            new_eid_to_entity[new_eid] = entity
        self.start = idx + 1
        doc._eid_to_entity = new_eid_to_entity
