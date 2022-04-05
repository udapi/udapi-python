"""Block corefud.IndexClusters"""
from udapi.core.block import Block


class IndexClusters(Block):
    """Re-index the coreference cluster IDs. The final cluster IDs are of the "e<ID>" form,
       where <ID> are ordinal numbers starting from the one specified by the `start` parameter.
       This block can be applied on multiple documents within one udapy call.
       For example, to re-index ClusterId in all conllu files in the current directory
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
        clusters = doc.coref_clusters
        if not clusters:
            return
        new_clusters = {}
        for idx, cid in enumerate(clusters, self.start):
            cluster = clusters[cid]
            new_cid = self.prefix + str(idx)
            cluster.eid = new_cid
            new_clusters[new_cid] = cluster
        self.start = idx + 1
        doc._coref_clusters = new_clusters
