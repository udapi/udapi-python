"""Classes for handling coreference."""
import re
import functools
import collections
import collections.abc
import copy
import logging

@functools.total_ordering
class CorefMention(object):
    """Class for representing a mention (instance of an entity)."""
    __slots__ = ['_head', '_cluster', '_bridging', '_words', '_other']

    def __init__(self, head, cluster=None):
        self._head = head
        self._cluster = cluster
        if cluster is not None:
            cluster._mentions.append(self)
        self._bridging = None
        self._words = []
        self._other = None

    def __lt__(self, another):
        """Does this mention precedes (word-order wise) `another` mention?

        This method defines a total ordering of all mentions
        (within one cluster or across different clusters).
        The position is primarily defined by the first word in each mention
        (or by the head if mention.words are missing).
        If two mentions start at the same word,
        their order is defined by the last word in their span
        -- the shorter mention precedes the longer one.
        """
        node1 = self._words[0] if self._words else self._head
        node2 = another._words[0] if another._words else another._head
        if node1 is node2:
            node1 = self._words[-1] if self._words else self._head
            node2 = another._words[-1] if another._words else another._head
            if node1 is node2:
                return len(self._words) < len(another._words)
        return node1.precedes(node2)

    @property
    def other(self):
        if self._other is None:
            self._other = OtherDualDict()
        return self._other

    @other.setter
    def other(self, value):
        if self._other is None:
            self._other = OtherDualDict(value)
        else:
            self._other.set_mapping(value)

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

    def __lt__(self, another):
        """Does this CorefCluster precedes (word-order wise) `another` cluster?

        This method defines a total ordering of all clusters
        by the first mention of each cluster (see `CorefMention.__lt__`).
        If one of the clusters has no mentions (which should not happen normally),
        there is a backup solution (see the source code).
        If cluster IDs are not important, it is recommended to use block
        `corefud.IndexClusters` to re-name cluster IDs in accordance with this cluster ordering.
        """
        if not self._mentions or not another._mentions:
            # Clusters without mentions should go first, so the ordering is total.
            # If both clusters are missing mentions, let's use cluster_id, so the ordering is stable.
            if not self._mentions and not another._mentions:
                return self._cluster_id < another._cluster_id
            return not self._mentions
        return self._mentions[0] < another._mentions[0]

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
    def __init__(self, src_mention, value=None, clusters=None, strict=True):
        self.src_mention = src_mention
        self._data = []
        self.strict = strict
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
                        _error("Bridging cannot self-reference the same cluster: " + v[0].cluster_id, strict)
                    self._data.append(BridgingLink(v[0], v[1]))
        super().__init__()

    def __getitem__(self, key):
        return self._data[key]

    def __len__(self):
        return len(self._data)

    # TODO delete backlinks of old links, dtto for SplitAnte
    def __setitem__(self, key, new_value):
        if new_value[0] is self.src_mention._cluster:
            _error("Bridging cannot self-reference the same cluster: " + new_value[0].cluster_id, self.strict)
        self._data[key] = BridgingLink(new_value[0], new_value[1])

    def __delitem__(self, key):
        del self._data[key]

    def insert(self, key, new_value):
        if new_value[0] is self.src_mention._cluster:
            _error("Bridging cannot self-reference the same cluster: " + new_value[0].cluster_id, self.strict)
        self._data.insert(key, BridgingLink(new_value[0], new_value[1]))

    def __str__(self):
        return ','.join(f'{l.target._cluster_id}:{l.relation}' for l in sorted(self._data))

    def _from_string(self, string, clusters):
        self._data.clear()
        for link_str in string.split(','):
            target, relation = link_str.split(':')
            if target == self.src_mention._cluster._cluster_id:
                _error("Bridging cannot self-reference the same cluster: " + target, self.strict)
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

def _error(msg, strict):
    if strict:
        raise ValueError(msg)
    logging.error(msg)


RE_DISCONTINUOUS = re.compile(r'^([^[]+)\[(\d+)/(\d+)\]')

def load_coref_from_misc(doc, strict=True):
    clusters = {}
    unfinished_mentions = collections.defaultdict(list)
    global_entity = doc.meta.get('global.Entity')
    was_global_entity = True
    if not global_entity:
        was_global_entity = False
        global_entity = 'eid-etype-head-other'
        doc.meta['global.Entity'] = global_entity
    # backward compatibility
    if global_entity == 'entity-GRP-infstat-MIN-coref_type-identity':
        global_entity = 'etype-eid-infstat-minspan-link-identity'
        # Which global.Entity should be used for serialization?
        doc.meta['global.Entity'] = global_entity
        #doc.meta['global.Entity'] = 'eid-etype-head-other'
    if 'eid' not in global_entity:
        raise ValueError("No eid in global.Entity = " + global_entity)
    fields = global_entity.split('-')

    for node in doc.nodes_and_empty:
        misc_entity = node.misc["Entity"]
        if not misc_entity:
            continue

        if not was_global_entity:
            raise ValueError(f"No global.Entity header found, but Entity= annotations are presents")

        # The Entity attribute may contain multiple entities, e.g.
        # Entity=(abstract-7-new-2-coref(abstract-3-giv:act-1-coref)
        # means a start of entity id=7 and start&end (i.e. single-word mention) of entity id=3.
        # The following re.split line splits this into
        # chunks = ["(abstract-7-new-2-coref", "(abstract-3-giv:act-1-coref)"]
        chunks = [x for x in re.split('(\([^()]+\)?|[^()]+\))', misc_entity) if x]
        for chunk in chunks:
            opening, closing = (chunk[0] == '(', chunk[-1] == ')')
            chunk = chunk.strip('()')
            if not opening and not closing:
                logging.warning(f"Entity {chunk} at {node} has no opening nor closing bracket.")
            elif not opening and closing:
                if '-' in chunk:
                    # TODO delete this legacy hack once we don't need to load UD GUM v2.8 anymore
                    if not strict and global_entity.startswith('etype-eid'):
                        chunk = chunk.split('-')[1]
                    else:
                        _error("Unexpected closing eid " + chunk, strict)
                if chunk not in unfinished_mentions:
                    m = RE_DISCONTINUOUS.match(chunk)
                    if not m:
                        raise ValueError(f"Mention {chunk} closed at {node}, but not opened.")
                    eid, subspan_idx, total_subspans = m.group(1, 2, 3)
                    mention, head_idx = unfinished_mentions[eid].pop()
                    mention.words += span_to_nodes(mention.head.root, f'{mention.head.ord}-{node.ord}')
                    if subspan_idx == total_subspans and head_idx:
                        mention.head = mention.words[head_idx - 1]
                else:
                    mention, head_idx = unfinished_mentions[chunk].pop()
                    mention.span = f'{mention.head.ord}-{node.ord}'
                    if head_idx:
                        mention.head = mention.words[head_idx - 1]
            else:
                eid, etype, head_idx, other = None, None, None, OtherDualDict()
                for name, value in zip(fields, chunk.split('-')):
                    if name == 'eid':
                        eid = value
                    elif name == 'etype':
                        etype = value
                    elif name == 'head':
                        try:
                            head_idx = int(value)
                        except ValueError as err:
                            raise ValueError(f"Non-integer {value} as head index in {chunk} in {node}: {err}")
                    elif name == 'other':
                        if other:
                            new_other = OtherDualDict(value)
                            for k,v in other.values():
                                new_other[k] = v
                            other = new_other
                        else:
                            other = OtherDualDict(value)
                    else:
                        other[name] = value
                if eid is None:
                    raise ValueError("No eid in " + chunk)
                subspan_idx, total_subspans = '1', '0'
                if eid[-1] == ']':
                    m = RE_DISCONTINUOUS.match(eid)
                    if not m:
                        _error(f"eid={eid} ending with ], but not valid discontinous mention ID ", strict)
                    else:
                        eid, subspan_idx, total_subspans = m.group(1, 2, 3)

                cluster = clusters.get(eid)
                if cluster is None:
                    if subspan_idx != '1':
                        _error(f'Non-first subspan of a discontinous mention {eid} at {node} does not have any previous mention.', 1)
                    cluster = CorefCluster(eid)
                    clusters[eid] = cluster
                    cluster.cluster_type = etype
                elif etype and cluster.cluster_type and cluster.cluster_type != etype:
                    logging.warning(f"etype mismatch in {node}: {cluster.cluster_type} != {etype}")
                if subspan_idx != '1':
                    mention = cluster.mentions[-1]
                    mention.words += [node]
                    mention.head = node
                    if not closing:
                        unfinished_mentions[eid].append((mention, head_idx))
                else:
                    mention = CorefMention(node, cluster)
                    if other:
                        mention._other = other
                    if closing:
                        mention.words = [node]
                    else:
                        unfinished_mentions[eid].append((mention, head_idx))

        misc_bridges = node.misc['Bridge']
        if misc_bridges:
            # E.g. Entity=event-12|Bridge=12<124,12<125
            # or with relations Bridge=c173<c188:subset,c174<c188:part
            for misc_bridge in misc_bridges.split(','):
                try:
                    trg_str, src_str = misc_bridge.split('<')
                except ValueError as err:
                    raise ValueError(f"{node}: {misc_bridge} {err}")
                relation = '_'
                if ':' in src_str:
                    src_str, relation = src_str.split(':')
                try:
                    trg_cluster = clusters[trg_str]
                    src_cluster = clusters[src_str]
                except KeyError as err:
                    logging.warning(f"{node}: Cannot find cluster {err}")
                else:
                    mention = src_cluster.mentions[-1]
                    mention.bridging.append((trg_cluster, relation))

        misc_split = node.misc['SplitAnte']
        if not misc_split and 'Split' in node.misc:
            misc_split = node.misc.pop('Split')
        if misc_split:
            # E.g. Entity=(person-54)|Split=4<54,9<54
            src_str = misc_split.split('<')[-1]
            ante_clusters = []
            for x in misc_split.split(','):
                ante_str, this_str = x.split('<')
                if this_str != src_str:
                    raise ValueError(f'{node} invalid SplitAnte: {this_str} != {src_str}')
                ante_clusters.append(clusters[ante_str])
            clusters[src_str].split_ante = ante_clusters

    for cluster_name, mentions in unfinished_mentions.items():
        for mention in mentions:
            logging.warning(f"Mention {cluster_name} opened at {mention.head}, but not closed. Deleting.")
            cluster = mention.cluster
            mention.words = []
            cluster._mentions.remove(mention)
            if not cluster._mentions:
                del clusters[name]

    # c=doc.coref_clusters should be sorted, so that c[0] < c[1] etc.
    # In other words, the dict should be sorted by the values (according to CorefCluster.__lt__),
    # not by the keys (cluster_id).
    # In Python 3.7+ (3.6+ in CPython), dicts are guaranteed to be insertion order.
    for cluster in clusters.values():
        if not cluster._mentions:
            _error(f"Cluster {cluster.cluster_id} referenced in SplitAnte or Bridge, but not defined with Entity", strict)
        cluster._mentions.sort()
    doc._coref_clusters = {c._cluster_id: c for c in sorted(clusters.values())}


def store_coref_to_misc(doc):
    if not doc._coref_clusters:
        return

    global_entity = doc.meta.get('global.Entity')
    if not global_entity:
        global_entity = 'eid-etype-head-other'
        doc.meta['global.Entity'] = global_entity
    fields = global_entity.split('-')
    # GRP and entity are legacy names for eid and etype, respectively.
    other_fields = [f for f in fields if f not in ('eid etype head other GRP entity'.split(), )]

    attrs = "Entity SplitAnte Bridge".split()
    for node in doc.nodes_and_empty:
        for attr in attrs:
            del node.misc[attr]

    # TODO benchmark for node in doc.nodes_and_empty: for mention in node.coref_mentions
    # We need reversed because if two mentions start at the same node, the longer one must go first.
    for mention in reversed(doc.coref_mentions):
        cluster = mention.cluster
        values = []
        for field in fields:
            if field == 'eid' or field == 'GRP':
                values.append(cluster.cluster_id)
            elif field == 'etype' or field == 'entity':
                if cluster.cluster_type is None:
                    values.append('unk')
                else:
                    values.append(cluster.cluster_type)
            elif field == 'head':
                values.append(str(mention.words.index(mention.head) + 1))
            elif field == 'other':
                if not mention.other:
                    values.append('')
                elif not other_fields:
                    values.append(str(mention.other))
                else:
                    other_copy = OtherDualDict(mention.other)
                    for other_field in other_fields:
                        del other_copy[other_field]
                    values.append(str(other_copy))
            else:
                values.append(mention.other[field].replace('%2C', ','))
        # optional fields
        while values and values[-1] == '':
            del values[-1]
        mention_str = '(' + '-'.join(values)

        if len(mention.words) == 1:
            mention.words[0].misc['Entity'] += mention_str + ')'
        else:
            if ',' in mention.span:
                subspans = mention.span.split(',')
                root = mention.words[0].root
                for idx,subspan in enumerate(subspans, 1):
                    subspan_eid = f'{cluster.cluster_id}[{idx}/{len(subspans)}]'
                    subspan_words = span_to_nodes(root, subspan)
                    if len(subspan_words) == 1:
                        subspan_words[0].misc['Entity'] += mention_str.replace(cluster.cluster_id, subspan_eid) + ')'
                    else:
                        subspan_words[0].misc['Entity'] += mention_str.replace(cluster.cluster_id, subspan_eid)
                        subspan_words[-1].misc['Entity'] += subspan_eid + ')'
            else:
                mention.words[0].misc['Entity'] += mention_str
                mention.words[-1].misc['Entity'] += cluster.cluster_id + ')'
        if mention.bridging:
            # TODO BridgingLinks.__src__ should already return c173<c188:subset,c174<c188:part
            strs = ','.join(f'{l.target.cluster_id}<{cluster.cluster_id}{":" + l.relation if l.relation != "_" else ""}' for l in sorted(mention.bridging))
            if mention.words[0].misc['Bridge']:
                strs = mention.words[0].misc['Bridge'] + ',' + strs
            mention.words[0].misc['Bridge'] = strs

    # SplitAnte=c5<c61,c10<c61
    for cluster in doc.coref_clusters.values():
        if cluster.split_ante:
            first_word = cluster.mentions[0].words[0]
            strs = ','.join(f'{sa.cluster_id}<{cluster.cluster_id}' for sa in cluster.split_ante)
            if first_word.misc['SplitAnte']:
                strs = first_word.misc['SplitAnte'] + ',' + strs
            first_word.misc['SplitAnte'] = strs

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


# TODO fix code duplication with udapi.core.dualdict after making sure benchmarks are not slower
class OtherDualDict(collections.abc.MutableMapping):
    """OtherDualDict class serves as dict with lazily synchronized string representation.

    >>> ddict = OtherDualDict('anacata:anaphoric,antetype:entity,nptype:np')
    >>> ddict['mention'] = 'np'
    >>> str(ddict)
    'anacata:anaphoric,antetype:entity,mention:np,nptype:np'
    >>> ddict['NonExistent']
    ''

    This class provides access to both
    * a structured (dict-based, deserialized) representation,
      e.g. {'anacata': 'anaphoric', 'antetype': 'entity'}, and
    * a string (serialized) representation of the mapping, e.g. `anacata:anaphoric,antetype:entity`.
    There is a clever mechanism that makes sure that users can read and write
    both of the representations which are always kept synchronized.
    Moreover, the synchronization is lazy, so the serialization and deserialization
    is done only when needed. This speeds up scenarios where access to dict is not needed.

    A value can be deleted with any of the following three ways:
    >>> del ddict['nptype']
    >>> ddict['nptype'] = None
    >>> ddict['nptype'] = ''
    and it works even if the value was already missing.
    """
    __slots__ = ['_string', '_dict']

    def __init__(self, value=None, **kwargs):
        if value is not None and kwargs:
            raise ValueError('If value is specified, no other kwarg is allowed ' + str(kwargs))
        self._dict = dict(**kwargs)
        self._string = None
        if value is not None:
            self.set_mapping(value)

    def __str__(self):
        if self._string is None:
            serialized = []
            for name, value in sorted(self._dict.items(), key=lambda s: s[0].lower()):
                if value is True:
                    serialized.append(name)
                else:
                    serialized.append('%s:%s' % (name, value))
            self._string = ','.join(serialized) if serialized else ''
        return self._string

    def _deserialize_if_empty(self):
        if not self._dict and self._string is not None and self._string != '':
            for raw_feature in self._string.split(','):
                namevalue = raw_feature.split(':', 1)
                if len(namevalue) == 2:
                    name, value = namevalue
                else:
                    name, value = namevalue[0], True
                self._dict[name] = value

    def __getitem__(self, key):
        self._deserialize_if_empty()
        return self._dict.get(key, '')

    def __setitem__(self, key, value):
        self._deserialize_if_empty()
        self._string = None
        if value is None or value == '':
            self.__delitem__(key)
        else:
            value = value.replace(',', '%2C') # TODO report a warning? Escape also '|' and '-'?
            self._dict[key] = value

    def __delitem__(self, key):
        self._deserialize_if_empty()
        try:
            del self._dict[key]
            self._string = None
        except KeyError:
            pass

    def __iter__(self):
        self._deserialize_if_empty()
        return self._dict.__iter__()

    def __len__(self):
        self._deserialize_if_empty()
        return len(self._dict)

    def __contains__(self, key):
        self._deserialize_if_empty()
        return self._dict.__contains__(key)

    def clear(self):
        self._string = '_'
        self._dict.clear()

    def copy(self):
        """Return a deep copy of this instance."""
        return copy.deepcopy(self)

    def set_mapping(self, value):
        """Set the mapping from a dict or string.

        If the `value` is None, it is converted to storing an empty string.
        If the `value` is a string, it is stored as is.
        If the `value` is a dict (or any instance of `collections.abc.Mapping`),
        its copy is stored.
        Other types of `value` raise an `ValueError` exception.
        """
        if value is None:
            self.clear()
        elif isinstance(value, str):
            self._dict.clear()
            self._string = value
        elif isinstance(value, collections.abc.Mapping):
            self._string = None
            self._dict = dict(value)
        else:
            raise ValueError("Unsupported value type " + str(value))
