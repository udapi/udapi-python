"""Classes for handling coreference."""

class CorefMention(object):
    """Class for representing a mention (instance of an entity)."""
    __slots__ = ['_head', '_cluster', '_bridging', '_words']

    def __init__(self, head, cluster=None):
        self._head = head
        self._cluster = cluster
        if cluster is not None:
            cluster._mentions.append(self)
        self._bridging = None
        self._words = []

    @property
    def head(self):
        return self._head

    # TODO change head - make sure it is already within the span (_words) or add it?

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
        return self._bridging

    # TODO add/edit bridging

    @property
    def words(self):
        return self._words

    @words.setter
    def words(self, new_words):
        if self.head not in new_words:
            raise ValueError(f"Head {self.head} not in new_words {new_words}")
        for old_word in self._words:
            old_word._mentions.remove(self)
        self._words = new_words # TODO sorted
        for new_word in new_words:
            new_word._mentions.append(self)

    @property
    def span(self):
        def _nums_to_ranges(nums):
            lo, hi = nums[0], nums[0]
            for num in nums[1:]:
                if num == hi + 1:
                    hi = num
                else:
                    yield (lo, hi)
                    lo, hi = num, num
            yield (lo, hi)

        if not self._words:
            return ''
        ords = sorted(n.ord for n in self._words) # TODO vypustit sorted
        if len(ords) == 1:
            return str(ords[0])
        first, last = ords[0], ords[-1]
        if ords == list(range(first, last+1)):
            return "%g-%g" % (first, last)
        return ','.join( '%g' % r[0] if r[0]==r[1] else '%g-%g' % r for r in _nums_to_ranges(ords))

    @span.setter
    def span(self, new_span):
        self.words = span_to_nodes(self._head.root, new_span)


class CorefCluster(object):
    """Class for representing all mentions of a given entity."""
    __slots__ = ['_cluster_id', '_mentions', 'cluster_type', '_split_ante']

    def __init__(self, cluster_id, cluster_type=None):
        self._cluster_id = cluster_id
        self._mentions = []
        self.cluster_type = cluster_type
        self._split_ante = None

    @property
    def cluster_id(self):
        return self._cluster_id

    @property
    def mentions(self):
        #TODO return sorted(self._mentions, key=lambda x:...
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
        return mention

    @property
    def split_ante(self):
        return self._split_ante

    # TODO add/edit split_ante

    # TODO adapt depending on how mention.bridging is implemented (callable list subclass)
    def all_bridging(self):
        for m in self._mentions:
            if m._bridging:
                for b in m._bridging:
                    yield b


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
    for node in doc.nodes:
        cluster_id = node.misc["ClusterId"]
        if cluster_id:
            cluster = clusters.get(cluster_id)
            if cluster is None:
                cluster = CorefCluster(cluster_id)
                clusters[cluster_id] = cluster
            mention = CorefMention(node, cluster)
            if node.misc["MentionSpan"]:
                mention.span = node.misc["MentionSpan"]
            cluster_type = node.misc["ClusterType"]
            if cluster_type is not None:
                if cluster.cluster_type is not None and cluster_type != cluster.cluster_type:
                    logging.warning(f"cluster_type mismatch in {node}: {cluster.cluster_type} != {cluster_type}")
                cluster.cluster_type = cluster_type
            # TODO deserialize Bridging and Split
            mention._bridging = node.misc["Bridging"]
            mention._split_ante = node.misc["Split"]
    doc._coref_clusters = clusters


def store_coref_to_misc(doc):
    if not doc._coref_clusters:
        return
    for node in doc.nodes:
        del node.misc["ClusterId"]
        del node.misc["MentionSpan"]
        del node.misc["ClusterType"]
        del node.misc["Bridging"]
        del node.misc["Split"]
    for cluster in doc._coref_clusters.values():
        for mention in cluster.mentions:
            head = mention.head
            head.misc["ClusterId"] = cluster.cluster_id
            head.misc["MentionSpan"] = mention.span
            head.misc["ClusterType"] = cluster.cluster_type
            head.misc["Bridging"] = mention.bridging
            head.misc["Split"] = cluster.split_ante


def span_to_nodes(root, span):
    ranges = []
    for span_str in span.split(','):
        if '-' not in span_str:
            lo = hi = float(span_str)
        else:
            lo, hi = (float(x) for x in span_str.split('-'))
        ranges.append((lo, hi))

    def _num_in_ranges(num):
        for (lo, hi) in ranges:
            if num > hi:
                return False
            if num >= lo:
                return True
            return False

    return [w for w in root.descendants_and_empty if _num_in_ranges(w.ord)]


def nodes_to_span(nodes):
    def _nums_to_ranges(nums):
        lo, hi = nums[0], nums[0]
        for num in nums[1:]:
            if num == hi + 1:
                hi = num
            else:
                yield (lo, hi)
                lo, hi = num, num
        yield (lo, hi)

    ords = sorted(n.ord for n in nodes) # TODO vypustit sorted
    if len(ords) == 1:
        return str(ords[0])
    first, last = ords[0], ords[-1]
    if ords == list(range(first, last+1)):
        return "%g-%g" % (first, last)
    return ','.join( '%g' % r[0] if r[0]==r[1] else '%g-%g' % r for r in _nums_to_ranges(ords))
