"""Block corefud.IndexClusters"""
from udapi.core.block import Block


class IndexClusters(Block):
    """Re-index the coreference cluster IDs. The final cluster IDs are of the "c<ID>" form,
       where <ID> are ordinal numbers starting from the one specified by the `start` parameter.
       
       Parameters:
       -----------
       start : int
            the starting index (by default 1)
    """

    def __init__(self, start=1):
        self.start = start

    def process_document(self, doc):
        clusters = doc.coref_clusters
        new_clusters = {}
        for idx, cid in enumerate(clusters, self.start):
            cluster = clusters[cid]
            new_cid = "c" + str(idx)
            # need to change private variable
            cluster._cluster_id = new_cid 
            new_clusters[new_cid] = cluster
