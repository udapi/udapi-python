"""Reader for CoNLL-U files with the old CorefUD 0.1 style of coreference annotation."""
import re
import logging
import udapi.block.read.conllu
from udapi.core.coref import CorefCluster, CorefMention, BridgingLinks

class OldCorefUD(udapi.block.read.conllu.Conllu):

    def __init__(self, replace_hyphen_in_id_with='', **kwargs):
        """Create the read.OldCorefUD reader object.

        Args:
        substitute_hyphen_in_id_for: string to use as a replacement for hyphens in ClusterId
          The new format does not allow hyphens in eid (IDs of entity clusters),
          so we need to replace them.
        """
        super().__init__(**kwargs)
        self.replace_hyphen_in_id_with = replace_hyphen_in_id_with
        self.orig2new = {}
        self.new2orig = {}

    def _fix_id(self, cid):
        if not cid or '-' not in cid:
            return cid
        new_cid = self.orig2new.get(cid)
        if new_cid is None:
            new_cid = cid.replace('-', self.replace_hyphen_in_id_with)
            base, counter = new_cid, 1
            while new_cid in self.new2orig:
                counter += 1
                new_cid = f"{base}{counter}"
            self.new2orig[new_cid] = cid
            self.orig2new[cid] = new_cid
        return new_cid

    def process_document(self, doc, strict=True):
        super().process_document(doc)

        clusters = {}
        for node in doc.nodes_and_empty:
            index, index_str = 0, ""
            cluster_id = node.misc["ClusterId"]
            if not cluster_id:
                index, index_str = 1, "[1]"
                cluster_id = node.misc["ClusterId[1]"]
            cluster_id = self._fix_id(cluster_id)
            while cluster_id:
                cluster = clusters.get(cluster_id)
                if cluster is None:
                    cluster = CorefCluster(cluster_id)
                    clusters[cluster_id] = cluster
                mention = CorefMention(words=[node], cluster=cluster)
                if node.misc["MentionSpan" + index_str]:
                    mention.span = node.misc["MentionSpan" + index_str]
                cluster_type = node.misc["ClusterType" + index_str]
                if cluster_type:
                    if cluster.cluster_type is not None and cluster_type != cluster.cluster_type:
                        logging.warning(f"cluster_type mismatch in {node}: {cluster.cluster_type} != {cluster_type}")
                    cluster.cluster_type = cluster_type

                bridging_str = node.misc["Bridging" + index_str]
                if bridging_str:
                    mention._bridging = BridgingLinks(mention)
                    for link_str in bridging_str.split(','):
                        target, relation = link_str.split(':')
                        target = self._fix_id(target)
                        if target == cluster_id:
                            _error("Bridging cannot self-reference the same cluster: " + target, strict)
                        if target not in clusters:
                            clusters[target] = CorefCluster(target)
                        mention._bridging.append((clusters[target], relation))

                split_ante_str = node.misc["SplitAnte" + index_str]
                if split_ante_str:
                    split_antes = []
                    # TODO in CorefUD draft "+" was used as the separator, but it was changed to comma.
                    # We can delete `.replace('+', ',')` once there are no more data with the legacy plus separator.
                    for ante_str in split_ante_str.replace('+', ',').split(','):
                        ante_str = self._fix_id(ante_str)
                        if ante_str in clusters:
                            if ante_str == cluster_id:
                                _error("SplitAnte cannot self-reference the same cluster: " + cluster_id, strict)
                            split_antes.append(clusters[ante_str])
                        else:
                            # split cataphora, e.g. "We, that is you and me..."
                            ante_cl = CorefCluster(ante_str)
                            clusters[ante_str] = ante_cl
                            split_antes.append(ante_cl)
                    cluster.split_ante = sorted(split_antes)

                # Some CorefUD 0.2 datasets (e.g. ARRAU) separate key-value pairs with spaces instead of commas.
                # We also need to escape forbidden characters.
                mmisc = node.misc["MentionMisc" + index_str].replace(' ', ',')
                mention.other = mmisc.replace('-', '%2D').replace('(', '%28').replace(')', '%29')
                index += 1
                index_str = f"[{index}]"
                cluster_id = self._fix_id(node.misc["ClusterId" + index_str])
        # c=doc.coref_clusters should be sorted, so that c[0] < c[1] etc.
        # In other words, the dict should be sorted by the values (according to CorefCluster.__lt__),
        # not by the keys (cluster_id).
        # In Python 3.7+ (3.6+ in CPython), dicts are guaranteed to be insertion order.
        for cluster in clusters.values():
            if not cluster._mentions:
                _error(f"Cluster {cluster.cluster_id} referenced in SplitAnte or Bridging, but not defined with ClusterId", strict)
            cluster._mentions.sort()
        doc._coref_clusters = {c._cluster_id: c for c in sorted(clusters.values())}

        # Delete all old-style attributes from MISC (so when converting old to new style, the old attributes are deleted).
        attrs = "ClusterId MentionSpan ClusterType Bridging SplitAnte MentionMisc".split()
        for node in doc.nodes_and_empty:
            for key in list(node.misc):
                if any(re.match(attr + r'(\[\d+\])?$', key) for attr in attrs):
                    del node.misc[key]


def _error(msg, strict):
    if strict:
        raise ValueError(msg)
    logging.error(msg)
