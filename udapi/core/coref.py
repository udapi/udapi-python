"""Classes for handling coreference."""
import re
import functools
import collections
import logging

@functools.total_ordering
class CorefMention(object):
    """Class for representing a mention (instance of an entity)."""
    __slots__ = ['_head', '_cluster', '_bridging', '_words', 'misc']

    def __init__(self, head, cluster=None):
        self._head = head
        self._cluster = cluster
        if cluster is not None:
            cluster._mentions.append(self)
        self._bridging = None
        self._words = []
        self.misc = None

    def __lt__(self, other):
        """Does this mention precedes (word-order wise) the `other` mention?

        This method defines a total ordering of all mentions
        (within one cluster or across different clusters).
        The position is primarily defined by the first word in each mention
        (or by the head if mention.words are missing).
        If two mentions start at the same word,
        their order is defined by the last word in their span
        -- the shorter mention precedes the longer one.
        """
        node1 = self._words[0] if self._words else self._head
        node2 = other._words[0] if other._words else other._head
        if node1 is node2:
            node1 = self._words[-1] if self._words else self._head
            node2 = other._words[-1] if other._words else other._head
            if node1 is node2:
                return len(self._words) < len(other._words)
        return node1.precedes(node2)

    @property
    def head(self):
        return self._head

    @head.setter
    def head(self, new_head):
        if self._words and new_head not in self._words:
            raise ValueError(f"New head {new_head} not in mention words")
        self._head = new_head

    @property
    def cluster(self):
        return self._cluster

    @cluster.setter
    def cluster(self, new_cluster):
        if self._cluster is not None:
            raise NotImplementedError('changing the cluster of a mention not supported yet')
        self._cluster = new_cluster
        new_cluster._mentions.append(new_cluster)

    @property
    def bridging(self):
        if not self._bridging:
            self._bridging = BridgingLinks(self)
        return self._bridging

    # TODO add/edit bridging

    @property
    def words(self):
        return self._words

    @words.setter
    def words(self, new_words):
        if new_words and self.head not in new_words:
            raise ValueError(f"Head {self.head} not in new_words {new_words}")
        kept_words = []
        for old_word in self._words:
            if old_word in new_words:
                kept_words.append(old_word)
            else:
                old_word._mentions.remove(self)
        new_words.sort()
        self._words = new_words
        for new_word in new_words:
            if new_word not in kept_words:
                if not new_word._mentions or self > new_word._mentions[-1]:
                    new_word._mentions.append(self)
                else:
                    new_word._mentions.append(self)
                    new_word._mentions.sort()

    @property
    def span(self):
        return nodes_to_span(self._words)

    @span.setter
    def span(self, new_span):
        self.words = span_to_nodes(self._head.root, new_span)


@functools.total_ordering
class CorefCluster(object):
    """Class for representing all mentions of a given entity."""
    __slots__ = ['_cluster_id', '_mentions', 'cluster_type', 'split_ante']

    def __init__(self, cluster_id, cluster_type=None):
        self._cluster_id = cluster_id
        self._mentions = []
        self.cluster_type = cluster_type
        self.split_ante = []

    def __lt__(self, other):
        """Does this CorefCluster precedes (word-order wise) the `other` cluster?

        This method defines a total ordering of all clusters
        by the first mention of each cluster (see `CorefMention.__lt__`).
        If one of the clusters has no mentions (which should not happen normally),
        there is a backup solution (see the source code).
        If cluster IDs are not important, it is recommended to use block
        `corefud.IndexClusters` to re-name cluster IDs in accordance with this cluster ordering.
        """
        if not self._mentions or not other._mentions:
            # Clusters without mentions should go first, so the ordering is total.
            # If both clusters are missing mentions, let's use cluster_id, so the ordering is stable.
            if not self._mentions and not other._mentions:
                return self._cluster_id < other._cluster_id
            return not self._mentions
        return self._mentions[0] < other._mentions[0]

    @property
    def cluster_id(self):
        return self._cluster_id

    @property
    def mentions(self):
        return self._mentions

    def create_mention(self, head=None, mention_words=None, mention_span=None):
        """Create a new CoreferenceMention object within this CorefCluster.

        Args:
        head: a node where the annotation about this CorefMention will be stored in MISC.
            The head is supposed to be the linguistic head of the mention,
            i.e. the highest node in the dependency tree,
            but if such information is not available (yet),
            it can be any node within the mention_words.
            If no head is specified, the first word from mention_words will be used instead.
        mention_words: a list of nodes of the mention.
            This argument is optional, but if provided, it must contain the head.
            The nodes can be both normal nodes or empty nodes.
        mention_span: an alternative way how to specify mention_words
            using a string such as "3-5,6,7.1-7.2".
            (which means, there is an empty node 5.1 and normal node 7,
            which are not part of the mention).
            At most one of the args mention_words and mention_span can be specified.
        """
        if mention_words and mention_span:
            raise ValueError("Cannot specify both mention_words and mention_span")
        if head and mention_words and head not in mention_words:
            raise ValueError(f"Head {head} is not among the specified mention_words")
        if head is None and mention_words is None:
            raise ValueError("Either head or mention_words must be specified")
        if head is None:
            head = mention_words[0]

        mention = CorefMention(head, self)
        if mention_words:
            mention.words = mention_words
        if mention_span:
            mention.span = mention_span
        self._mentions.sort()
        return mention

    # TODO or should we create a BridgingLinks instance with a fake src_mention?
    def all_bridging(self):
        for m in self._mentions:
            if m._bridging:
                for b in m._bridging:
                    yield b


BridgingLink = collections.namedtuple('BridgingLink', 'target relation')


class BridgingLinks(collections.abc.MutableSequence):
    """BridgingLinks class serves as a list of BridgingLink tuples with additional methods.

    Example usage:
    >>> bl = BridgingLinks(src_mention)                                   # empty links
    >>> bl = BridgingLinks(src_mention, [(c12, 'Part'), (c56, 'Subset')]) # from a list of tuples
    >>> bl = BridgingLinks(src_mention, 'c12:Part,c56:Subset', clusters)  # from a string
    >>> for cluster, relation in bl:
    >>>     print(f"{bl.src_mention} ->{relation}-> {cluster.cluster_id}")
    >>> print(str(bl)) # c12:Part,c56:Subset
    >>> bl('Part').targets == [c12]
    >>> bl('Part|Subset').targets == [c12, c56]
    >>> bl.append((c89, 'Funct'))
    """
    def __init__(self, src_mention, value=None, clusters=None):
        self.src_mention = src_mention
        self._data = []
        if value is not None:
            if isinstance(value, str):
                if clusters is None:
                    raise ValueError('BridgingClusters: clusters must be provided if initializing with a string')
                try:
                    self._from_string(value, clusters)
                except Exception:
                    logging.error(f"Problem when parsing {value} in {src_mention.words[0]}:\n")
                    raise
            elif isinstance(value, collections.abc.Sequence):
                for v in value:
                    if v[0] is src_mention._cluster:
                        raise ValueError("Bridging cannot self-reference the same cluster: " + v[0].cluster_id)
                    self._data.append(BridgingLink(v[0], v[1]))
        super().__init__()

    def __getitem__(self, key):
        return self._data[key]

    def __len__(self):
        return len(self._data)

    # TODO delete backlinks of old links, dtto for SplitAnte
    def __setitem__(self, key, new_value):
        if new_value[0] is self.src_mention._cluster:
            raise ValueError("Bridging cannot self-reference the same cluster: " + new_value[0].cluster_id)
        self._data[key] = BridgingLink(new_value[0], new_value[1])

    def __delitem__(self, key):
        del self._data[key]

    def insert(self, key, new_value):
        if new_value[0] is self.src_mention._cluster:
            raise ValueError("Bridging cannot self-reference the same cluster: " + new_value[0].cluster_id)
        self._data.insert(key, BridgingLink(new_value[0], new_value[1]))

    def __str__(self):
        return ','.join(f'{l.target._cluster_id}:{l.relation}' for l in sorted(self._data))

    def _from_string(self, string, clusters):
        self._data.clear()
        for link_str in string.split(','):
            target, relation = link_str.split(':')
            if target == self.src_mention._cluster._cluster_id:
                raise ValueError("Bridging cannot self-reference the same cluster: " + target)
            if target not in clusters:
                clusters[target] = CorefCluster(target)
            self._data.append(BridgingLink(clusters[target], relation))
        self._data.sort()

    def __call__(self, relations_re=None):
        """Return a subset of links contained in this list as specified by the args.
        Args:
        relations: only links with a relation matching this regular expression will be returned
        """
        if relations_re is None:
            return self
        return Links(self.src_mention, [l for l in self._data if re.match(relations_re, l.relation)])

    @property
    def targets(self):
        """Return a list of the target clusters (without relations)."""
        return [link.target for link in self._data]


def create_coref_cluster(head, cluster_id=None, cluster_type=None, **kwargs):
    clusters = head.root.bundle.document.coref_clusters
    if not cluster_id:
        counter = 1
        while clusters.get('c%d' % counter):
            counter += 1
        cluster_id = 'c%d' % counter
    elif clusters.get(cluster_id):
        raise ValueError("Cluster with a id %s already exists", cluster_id)
    cluster = CorefCluster(cluster_id, cluster_type)
    cluster.create_mention(head, **kwargs)
    clusters[cluster_id] = cluster
    return cluster


def load_coref_from_misc(doc):
    clusters = {}
    for node in doc.nodes_and_empty:
        index, index_str = 0, ""
        cluster_id = node.misc["ClusterId"]
        if not cluster_id:
            index, index_str = 1, "[1]"
            cluster_id = node.misc["ClusterId[1]"]
        while cluster_id:
            cluster = clusters.get(cluster_id)
            if cluster is None:
                cluster = CorefCluster(cluster_id)
                clusters[cluster_id] = cluster
            mention = CorefMention(node, cluster)
            if node.misc["MentionSpan" + index_str]:
                mention.span = node.misc["MentionSpan" + index_str]
            else:
                mention.words = [node]
            cluster_type = node.misc["ClusterType" + index_str]
            if cluster_type is not None:
                if cluster.cluster_type is not None and cluster_type != cluster.cluster_type:
                    logging.warning(f"cluster_type mismatch in {node}: {cluster.cluster_type} != {cluster_type}")
                cluster.cluster_type = cluster_type

            bridging_str = node.misc["Bridging" + index_str]
            if bridging_str:
                mention._bridging = BridgingLinks(mention, bridging_str, clusters)

            split_ante_str = node.misc["SplitAnte" + index_str]
            if split_ante_str:
                split_antes = []
                # TODO in CorefUD draft "+" was used as the separator, but it was changed to comma.
                # We can delete `.replace('+', ',')` once there are no more data with the legacy plus separator.
                for ante_str in split_ante_str.replace('+', ',').split(','):
                    if ante_str in clusters:
                        if ante_str == cluster_id:
                            raise ValueError("SplitAnte cannot self-reference the same cluster: " + cluster_id)
                        split_antes.append(clusters[ante_str])
                    else:
                        # split cataphora, e.g. "We, that is you and me..."
                        ante_cl = CorefCluster(ante_str)
                        clusters[ante_str] = ante_cl
                        split_antes.append(ante_cl)
                cluster.split_ante = sorted(split_antes)

            mention.misc = node.misc["MentionMisc" + index_str]
            index += 1
            index_str = f"[{index}]"
            cluster_id = node.misc["ClusterId" + index_str]
    # c=doc.coref_clusters should be sorted, so that c[0] < c[1] etc.
    # In other words, the dict should be sorted by the values (according to CorefCluster.__lt__),
    # not by the keys (cluster_id).
    # In Python 3.7+ (3.6+ in CPython), dicts are guaranteed to be insertion order.
    for cluster in clusters.values():
        if not cluster._mentions:
            raise ValueError(f"Cluster {cluster.cluster_id} referenced in SplitAnte or Bridging, but not defined with ClusterId")
        cluster._mentions.sort()
    doc._coref_clusters = {c._cluster_id: c for c in sorted(clusters.values())}


def store_coref_to_misc(doc):
    if not doc._coref_clusters:
        return
    attrs = ("ClusterId", "MentionSpan", "ClusterType", "Bridging", "SplitAnte", "MentionMisc")
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


def span_to_nodes(root, span):
    ranges = []
    for span_str in span.split(','):
        try:
            if '-' not in span_str:
                lo = hi = float(span_str)
            else:
                lo, hi = (float(x) for x in span_str.split('-'))
        except ValueError as e:
            raise ValueError(f"Cannot parse '{span}': {e}")
        ranges.append((lo, hi))
    ranges.sort()

    def _num_in_ranges(num):
        for (lo, hi) in ranges:
            if num < lo:
                return False
            if num <= hi:
                return True
        return False

    return [w for w in root.descendants_and_empty if _num_in_ranges(w.ord)]


def nodes_to_span(nodes):
    """Converts a list of nodes into a string specifying ranges of their ords.

    For example, nodes with ords 3, 4, 5 and 7 will be converted to "3-5,7".
    The function handles also empty nodes, so e.g. 3.1, 3.2 and 3.3 will be converted to "3.1-3.3".
    Note that empty nodes may form gaps in the span, so if a given tree contains
    an empty node with ord 5.1, but only nodes with ords 3, 4, 5, 6, 7.1 and 7.2
    are provided as `nodes`, the resulting string will be "3-5,6,7.1-7.2".
    This means that the implementation needs to iterate of all nodes
    in a given tree (root.descendants_and_empty) to check for such gaps.
    """
    if not nodes:
        return ''
    all_nodes = nodes[0].root.descendants_and_empty
    i, found, ranges = -1, 0, []
    while i + 1 < len(all_nodes) and found < len(nodes):
        i += 1
        if all_nodes[i] in nodes:
            lo = all_nodes[i].ord
            while i < len(all_nodes) and all_nodes[i] in nodes:
                i, found = i + 1, found + 1
            hi = all_nodes[i - 1].ord
            ranges.append(f"{lo}-{hi}" if hi > lo else f"{lo}")
    return ','.join(ranges)
