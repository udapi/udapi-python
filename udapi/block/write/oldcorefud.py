"""Writer for CoNLL-U files with the old CorefUD 0.1 style of coreference annotation."""
import re
import logging
import udapi.block.write.conllu

class OldCorefUD(udapi.block.write.conllu.Conllu):

    def process_document(self, doc):
        if not doc._coref_clusters:
            logging.warning("Using write.OldCorefUD on a document without any coreference annotation")
            doc._coref_clusters = {}

        # Delete both new-style (GUM-style) and old-style (CorefUD 0.1) coreference annotations from MISC.
        attrs = "Entity Split Bridge ClusterId MentionSpan ClusterType Bridging SplitAnte MentionMisc".split()
        for node in doc.nodes_and_empty:
            for key in list(node.misc):
                if any(re.match(attr + r'(\[\d+\])?$', key) for attr in attrs):
                    del node.misc[key]

        # doc._coref_clusters is a dict, which is insertion ordered in Python 3.7+.
        # The insertion order is sorted according to CorefCluster.__lt__ (see few lines above).
        # However, new clusters could be added meanwhile or some clusters edited,
        # so we need to sort the clusters again before storing to MISC.
        # We also need to mare sure cluster.mentions are sorted in each cluster
        # because the ordering of clusters is defined by the first mention in each cluster.
        # Ordering of mentions within a cluster can be changed when e.g. changing the span
        # of a given mention or reordering words within a sentence and in such events
        # Udapi currently does not automatically update the ordering of clusters.
        for cluster in doc._coref_clusters.values():
            cluster._mentions.sort()
        for cluster in sorted(doc._coref_clusters.values()):
            for mention in cluster.mentions:
                head = mention.head
                if head.misc["ClusterId"]:
                    for a in attrs:
                        if head.misc[a]:
                            head.misc[a + "[1]"] = head.misc[a]
                            del head.misc[a]
                    index_str = "[2]"
                else:
                    index, index_str = 1, "[1]"
                    while(head.misc["ClusterId" + index_str]):
                        index += 1
                        index_str = f"[{index}]"
                    if index == 1:
                        index_str = ""
                head.misc["ClusterId" + index_str] = cluster.cluster_id
                head.misc["MentionSpan" + index_str] = mention.span
                head.misc["ClusterType" + index_str] = cluster.cluster_type
                if mention._bridging:
                    head.misc["Bridging" + index_str] = str(mention.bridging)
                if cluster.split_ante:
                    serialized = ','.join((c.cluster_id for c in sorted(cluster.split_ante)))
                    head.misc["SplitAnte" + index_str] = serialized
                if mention.misc:
                    head.misc["MentionMisc" + index_str] = mention.misc

        super().process_document(doc)
