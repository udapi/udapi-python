"""Classes for handling coreference.

# CorefUD 1.0 format implementation details

## Rules for ordering "chunks" within `node.misc['Entity']`
Entity mentions are annotated using "chunks" stored in `misc['Entity']`.
Chunks are of three types:
1. opening bracket, e.g. `(e1-person`
2. closing bracket, e.g. `e1-person)`
3. single-word span (both opening and closing), e.g. `(e1-person)`

The `Entity` MISC attribute contains a sequence of chunks
without any separators, e.g. `Entity=(e1-person(e2-place)`
means opening `e1` mention and single-word `e2` mention
starting on a given node.

### Crossing mentions
Two mentions are crossing iff their spans have non-empty intersection,
but neither is a subset of the other, e.g. `e1` spanning nodes 1-3
and `e2` spanning 2-4 would be represented as:
```
1 ... Entity=(e1
2 ... Entity=(e2
3 ... Entity=e1)
4 ... Entity=e2)
```
This may be an annotation error and we may forbid such cases in future annotation guidelines,
but in CorefUD 0.2, there are thousands of such cases (see https://github.com/ufal/corefUD/issues/23).

It can even happen that one entity ends and another starts at the same node: `Entity=e1)(e2`
For this reason, we need

**Rule1**: closing brackets MUST always precede opening brackets.
Otherwise, we would get `Entity=(e2e1)`, which could not be parsed.

Note that we cannot have same-entity crossing mentions in the CorefUD 1.0 format,
so e.g. if we substitute `e2` with `e1` in the example above, we'll get
`(e1`, `e1)`, `(e1`, `e1)`, which will be interpreted as two non-overlapping mentions of the same entity.

### Nested mentions
One mention (span) can be often embedded within another mention (span).
It can happen that both these mentions correspond to the same entity (i.e. are in the same cluster),
for example, "`<the man <who> sold the world>`".
It can even happen that both mentions start at the same node, e.g. "`<<w1 w2> w3>`" (TODO: find nice real-world examples).
In such cases, we need to make sure the brackets are well-nested:

**Rule2**: when opening multiple brackets at the same node, longer mentions MUST be opened first.

This is important because
- The closing bracket has the same form for both mentions of the same entity - it includes just the entity ID (`eid`).
- The opening-bracket annotation contains other mention attributes, e.g. head index.
- The two mentions may differ in these attributes, e.g. the "`<w1 w2 w3>`" mention's head may be w3.
- When breaking Rule2, we would get
```
1 w1 ... Entity=(e1-person-1(e1-person-3
2 w2 ... Entity=e1)
3 w3 ... Entity=e1)
```
which would be interpreted as if the head of the "`<w1 w2>`" mention is its third word, which is invalid.

### Other rules

**Rule3**: when closing multiple brackets at the same node, shorter mentions SHOULD be closed first.
See Rule4 for a single exception from this rule regarding crossing mentions.
I'm not aware of any problems when breaking this rule, but it seems intuitive
(to make the annotation well-nested if possible) and we want to define some canonical ordering anyway.
The API should be able to load even files breaking Rule3.

**Rule4**: single-word chunks SHOULD follow all opening brackets and precede all closing brackets if possible.
When considering single-word chunks as a subtype of both opening and closing brackets,
this rule follows from the well-nestedness (and Rule2).
So we should have `Entity=(e1(e2)` and `Entity=(e3)e1)`,
but the API should be able to load even `Entity=(e2)(e1` and `Entity=e1)(e3)`.

In case of crossing mentions (annotated following Rule1), we cannot follow Rule4.
If we want to add a single-word mention `e2` to a node with `Entity=e1)(e3`,
it seems intuitive to prefer Rule2 over Rule3, which results in `Entity=e1)(e3(e2)`.
So the canonical ordering will be achieved by placing single-word chunks after all opening brackets.
The API should be able to load even `Entity=(e2)e1)(e3` and `Entity=e1)(e2)(e3`.

**Rule5**: ordering of same-span single-word mentions
TODO: I am not sure here. We may want to forbid such cases or define canonical ordering even for them.
E.g. `Entity=(e1)(e2)` vs. `Entity=(e2)(e1)`.

**Rule6**: ordering of same-start same-end multiword mentions
TODO: I am not sure here.
These can be either same-span multiword mentions (which may be forbidden)
or something like
```
1 w1 ... Entity=(e1(e2[1/2])
2 w2 ...
3 w3 ... Entity=(e2[2/2])e1)
```
where both `e1` and `e2` start at w1 and end at w3, but `e2` is discontinuous and does not contain w2.
If we interpret "shorter" and "longer" in Rule2 and Rule3 as `len(mention.words)`
(and not as `mention.words[-1].ord - mention.words[0].ord`),
we get the canonical ordering as in the example above.

"""
import re
import functools
import collections
import collections.abc
import copy
import logging

@functools.total_ordering
class CorefMention(object):
    """Class for representing a mention (instance of an entity)."""
    __slots__ = ['_head', '_entity', '_bridging', '_words', '_other']

    def __init__(self, words, head=None, entity=None, add_word_backlinks=True):
        if not words:
            raise ValueError("mention.words must be non-empty")
        self._head = head if head else words[0]
        self._entity = entity
        if entity is not None:
            entity._mentions.append(self)
        self._bridging = None
        self._other = None
        self._words = words
        if add_word_backlinks:
            for new_word in words:
                if not new_word._mentions or not entity or self > new_word._mentions[-1]:
                    new_word._mentions.append(self)
                else:
                    new_word._mentions.append(self)
                    new_word._mentions.sort()

    def __lt__(self, another):
        """Does this mention precedes (word-order wise) `another` mention?

        This method defines a total ordering of all mentions
        (within one entity or across different entities).
        The position is primarily defined by the first word in each mention.
        If two mentions start at the same word,
        their order is defined by their length (i.e. number of words)
        -- the shorter mention follows the longer one.

        In the rare case of two same-length mentions starting at the same word, but having different spans,
        their order is defined by the order of the last word in their span.
        For example <w1, w2> precedes <w1, w3>.

        The order of two same-span mentions is currently defined by their eid.
        There should be no same-span (or same-subspan) same-entity mentions.
        """
        #TODO: no mention.words should be handled already when loading
        if not self._words:
            self._words = [self._head]
        if not another._words:
            another._words = [another._head]

        if self._words[0] is another._words[0]:
            if len(self._words) > len(another._words):
                return True
            if  len(self._words) < len(another._words):
                return False
            if self._words[-1].precedes(another._words[-1]):
                return True
            if another._words[-1].precedes(self._words[-1]):
                return False
            return self._entity.eid < another._entity.eid
        return self._words[0].precedes(another._words[0])

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
    def entity(self):
        return self._entity

    @entity.setter
    def entity(self, new_entity):
        if self._entity is not None:
            raise NotImplementedError('changing the entity of a mention not supported yet')
        self._entity = new_entity
        new_entity._mentions.append(new_entity)

    @property
    def bridging(self):
        if not self._bridging:
            self._bridging = BridgingLinks(self)
        return self._bridging

    # TODO add/edit bridging

    @property
    def words(self):
        # Words in a sentence could have been reordered, so we cannot rely on sorting self._words in the setter.
        # The serialization relies on storing the opening bracket in the first word (and closing in the last),
        # so we need to make sure the words are always returned sorted.
        # TODO: benchmark updating the order of mention._words in node.shift_*() and node.remove().
        self._words.sort()
        return self._words

    @words.setter
    def words(self, new_words):
        if new_words and self.head not in new_words:
            raise ValueError(f"Head {self.head} not in new_words {new_words} for {self._entity.eid}")
        kept_words = []
        # Make sure each word is included just once and they are in the correct order.
        new_words = sorted(list(set(new_words)))
        for old_word in self._words:
            if old_word in new_words:
                kept_words.append(old_word)
            else:
                old_word._mentions.remove(self)
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


CHARS_FORBIDDEN_IN_ID = "-=| \t()"


@functools.total_ordering
class CorefEntity(object):
    """Class for representing all mentions of a given entity."""
    __slots__ = ['_eid', '_mentions', 'etype', 'split_ante']

    def __init__(self, eid, etype=None):
        self._eid = None # prepare the _eid slot
        self.eid = eid # call the setter and check the ID is valid
        self._mentions = []
        self.etype = etype
        self.split_ante = []

    def __lt__(self, another):
        """Does this CorefEntity precedes (word-order wise) `another` entity?

        This method defines a total ordering of all entities
        by the first mention of each entity (see `CorefMention.__lt__`).
        If one of the entities has no mentions (which should not happen normally),
        there is a backup solution (see the source code).
        If entity IDs are not important, it is recommended to use block
        `corefud.IndexClusters` to re-name entity IDs in accordance with this entity ordering.
        """
        if not self._mentions or not another._mentions:
            # Entities without mentions should go first, so the ordering is total.
            # If both entities are missing mentions, let's use eid, so the ordering is stable.
            if not self._mentions and not another._mentions:
                return self._eid < another._eid
            return not self._mentions
        return self._mentions[0] < another._mentions[0]

    @property
    def eid(self):
        return self._eid

    @eid.setter
    def eid(self, new_eid):
        if any(x in new_eid for x in CHARS_FORBIDDEN_IN_ID):
            raise ValueError(f"{new_eid} contains forbidden characters [{CHARS_FORBIDDEN_IN_ID}]")
        self._eid = new_eid

    @property
    def eid_or_grp(self):
        root = self._mentions[0].head.root
        meta = root.document.meta
        if 'GRP' in meta['global.Entity'] and meta['tree2docid']:
            docid = meta['tree2docid'][root]
            if self._eid.startswith(docid):
                return self._eid.replace(docid, '', 1)
            else:
                logging.warning(f"GRP in global.Entity, but eid={self._eid} does not start with docid={docid}")
        return self._eid

    @property
    def mentions(self):
        return self._mentions

    def create_mention(self, head=None, words=None, span=None):
        """Create a new CoreferenceMention object within this CorefEntity.

        Args:
        head: a node where the annotation about this CorefMention will be stored in MISC.
            The head is supposed to be the linguistic head of the mention,
            i.e. the highest node in the dependency tree,
            but if such information is not available (yet),
            it can be any node within the `words`.
            If no head is specified, the first word from `words` will be used instead.
        words: a list of nodes of the mention.
            This argument is optional, but if provided, it must contain the head.
            The nodes can be both normal nodes or empty nodes.
        span: an alternative way how to specify `words`
            using a string such as "3-5,6,7.1-7.2".
            (which means, there is an empty node 5.1 and normal node 7,
            which are not part of the mention).
            At most one of the args `words` and `span` can be specified.
        """
        if words and span:
            raise ValueError("Cannot specify both words and span")
        if head and words and head not in words:
            raise ValueError(f"Head {head} is not among the specified words")
        if head is None and words is None:
            raise ValueError("Either head or words must be specified")
        if head is None:
            head = words[0]

        mention = CorefMention(words=[head], head=head, entity=self)
        if words:
            mention.words = words
        if span:
            mention.span = span
        self._mentions.sort()
        return mention

    # TODO or should we create a BridgingLinks instance with a fake src_mention?
    def all_bridging(self):
        for m in self._mentions:
            if m._bridging:
                for b in m._bridging:
                    yield b


# BridgingLink
# Especially the relation should be mutable, so we cannot use
#   BridgingLink = collections.namedtuple('BridgingLink', 'target relation')
# TODO once dropping support for Python 3.6, we could use
#   from dataclasses import dataclass
#   @dataclass
#   class DataClassCard:
#      target: CorefEntity
#      relation: str
class BridgingLink:
    __slots__ = ['target', 'relation']

    def __init__(self, target, relation=''):
        self.target = target
        self.relation = '' if relation is None else relation

    def __lt__(self, another):
        if self.target == another.target:
            return self.relation < another.relation
        return self.target < another.target


class BridgingLinks(collections.abc.MutableSequence):
    """BridgingLinks class serves as a list of BridgingLink tuples with additional methods.

    Example usage:
    >>> bl = BridgingLinks(src_mention)                                   # empty links
    >>> bl = BridgingLinks(src_mention, [(c12, 'part'), (c56, 'subset')]) # from a list of tuples
    >>> (bl8, bl9) = BridgingLinks.from_string('c12<c8:part,c56<c8:subset,c5<c9', entities)
    >>> for entity, relation in bl:
    >>>     print(f"{bl.src_mention} ->{relation}-> {entity.eid}")
    >>> print(str(bl)) # c12<c8:part,c56<c8:subset
    >>> bl('part').targets == [c12]
    >>> bl('part|subset').targets == [c12, c56]
    >>> bl.append((c57, 'funct'))
    """

    @classmethod
    def from_string(cls, string, entities, node, strict=True, tree2docid=None):
        """Return a sequence of BridgingLink objects representing a given string serialization.
        The bridging links are also added to the mentions (`mention.bridging`) in the supplied `entities`,
        so the returned sequence can be usually ignored.
        If `tree2docid` parameter is provided (mapping trees to document IDs used as prefixes in eid),
        the entity IDs in the provided string are interpreted as "GRP", i.e. as document-wide IDs,
        which need to be prefixed by the document IDs, to get corpus-wide unique "eid".
        """
        src_str2bl = {}
        for link_str in string.split(','):
            try:
                trg_str, src_str = link_str.split('<')
            except ValueError as err:
                _error(f"invalid Bridge {link_str} {err} at {node}", strict)
                continue
            relation = ''
            if ':' in src_str:
                src_str, relation = src_str.split(':', 1)
            if trg_str == src_str:
                _error(f"Bridge cannot self-reference the same entity {trg_str} at {node}", strict)
            if tree2docid:
                src_str = tree2docid[node.root] + src_str
                trg_str = tree2docid[node.root] + trg_str
            bl = src_str2bl.get(src_str)
            if not bl:
                bl = entities[src_str].mentions[-1].bridging
                src_str2bl[src_str] = bl
            if trg_str not in entities:
                entities[trg_str] = CorefEntity(trg_str)
            bl._data.append(BridgingLink(entities[trg_str], relation))
        return src_str2bl.values()

    def __init__(self, src_mention, value=None, strict=True):
        self.src_mention = src_mention
        self._data = []
        self.strict = strict
        if value is not None:
            if isinstance(value, collections.abc.Sequence):
                for v in value:
                    if v[0] is src_mention._entity:
                        _error("Bridging cannot self-reference the same entity: " + v[0].eid, strict)
                    self._data.append(BridgingLink(v[0], v[1]))
            else:
                raise ValueError(f"Unknown value type: {type(value)}")
        self.src_mention._bridging = self
        super().__init__()

    def __getitem__(self, key):
        return self._data[key]

    def __len__(self):
        return len(self._data)

    # TODO delete backlinks of old links, dtto for SplitAnte
    def __setitem__(self, key, new_value):
        if new_value[0] is self.src_mention._entity:
            _error("Bridging cannot self-reference the same entity: " + new_value[0].eid, self.strict)
        self._data[key] = BridgingLink(new_value[0], new_value[1])

    def __delitem__(self, key):
        del self._data[key]

    def insert(self, key, new_value):
        if new_value[0] is self.src_mention._entity:
            _error("Bridging cannot self-reference the same entity: " + new_value[0].eid, self.strict)
        self._data.insert(key, BridgingLink(new_value[0], new_value[1]))

    def __str__(self):
        # TODO in future link.relation should never be None, 0 nor "_", so we could delete the <not in (None, "_", "")> below.
        return ','.join(f'{l.target.eid_or_grp}<{self.src_mention.entity.eid_or_grp}{":" + l.relation if l.relation not in (None, "_", "") else ""}' for l in sorted(self._data))

    def __call__(self, relations_re=None):
        """Return a subset of links contained in this list as specified by the args.
        Args:
        relations: only links with a relation matching this regular expression will be returned
        """
        if relations_re is None:
            return self
        return BridgingLinks(self.src_mention, [l for l in self._data if re.match(relations_re, l.relation)])

    @property
    def targets(self):
        """Return a list of the target entities (without relations)."""
        return [link.target for link in self._data]

    def _delete_targets_without_mentions(self, warn=True):
        for link in self._data:
            if not link.target.mentions:
                if warn:
                    logging.warning(f"Entity {link.target.eid} has no mentions, but is referred to in bridging of {self.src_mention.entity.eid}")
                self._data.remove(link)


def _error(msg, strict):
    if strict:
        raise ValueError(msg)
    logging.error(msg)


RE_DISCONTINUOUS = re.compile(r'^([^[]+)\[(\d+)/(\d+)\]')
# When converting doc-level GRP IDs to corpus-level eid IDs,
# we need to assign each document a short ID/number (document names are too long).
# These document numbers must be unique even when loading multiple files,
# so we need to store the highest number generated so far here, at the Python module level.
highest_doc_n = 0

def load_coref_from_misc(doc, strict=True):
    global highest_doc_n
    entities = {}
    unfinished_mentions = collections.defaultdict(list)
    discontinuous_mentions = collections.defaultdict(list)
    global_entity = doc.meta.get('global.Entity')
    was_global_entity = True
    if not global_entity:
        was_global_entity = False
        global_entity = 'eid-etype-head-other'
        doc.meta['global.Entity'] = global_entity
    tree2docid = None
    if 'GRP' in global_entity:
        tree2docid, docid = {}, ""
        for bundle in doc:
            for tree in bundle:
                if tree.newdoc or docid == "":
                    highest_doc_n += 1
                    docid = f"d{highest_doc_n}."
                tree2docid[tree] = docid
        doc.meta['tree2docid'] = tree2docid
    elif 'eid' not in global_entity:
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
        chunks = [x for x in re.split(r'(\([^()]+\)?|[^()]+\))', misc_entity) if x]
        for chunk in chunks:
            opening, closing = (chunk[0] == '(', chunk[-1] == ')')
            chunk = chunk.strip('()')
            # 1. invalid
            if not opening and not closing:
                logging.warning(f"Entity {chunk} at {node} has no opening nor closing bracket.")
            # 2. closing bracket
            elif not opening and closing:
                # closing brackets should include just the ID, but GRP needs to be converted to eid
                if tree2docid:
                    # TODO delete this legacy hack once we don't need to load UD GUM v2.8 anymore
                    if '-' in chunk:
                        if not strict and global_entity.startswith('entity-GRP'):
                            chunk = chunk.split('-')[1]
                        else:
                            _error("Unexpected closing eid " + chunk, strict)
                    chunk = tree2docid[node.root] + chunk

                # closing discontinuous mentions
                eid, subspan_idx = chunk, None
                if chunk not in unfinished_mentions:
                    m = RE_DISCONTINUOUS.match(chunk)
                    if not m:
                        raise ValueError(f"Mention {chunk} closed at {node}, but not opened.")
                    eid, subspan_idx, total_subspans = m.group(1, 2, 3)

                try:
                    mention, head_idx = unfinished_mentions[eid].pop()
                except IndexError as err:
                    raise ValueError(f"Mention {chunk} closed at {node}, but not opened.")
                last_word = mention.words[-1]
                if node.root is not last_word.root:
                    # TODO cross-sentence mentions
                    raise ValueError(f"Cross-sentence mentions not supported yet: {chunk} at {node}")
                for w in node.root.descendants_and_empty:
                    if last_word.precedes(w):
                        mention._words.append(w)
                        w._mentions.append(mention)
                        if w is node:
                            break
                if head_idx and (subspan_idx is None or subspan_idx == total_subspans):
                    try:
                        mention.head = mention.words[head_idx - 1]
                    except IndexError as err:
                        _error(f"Invalid head_idx={head_idx} for {mention.entity.eid} "
                                f"closed at {node} with words={mention.words}", 1)
                if subspan_idx and subspan_idx == total_subspans:
                    m = discontinuous_mentions[eid].pop()
                    if m is not mention:
                        _error(f"Closing mention {mention.entity.eid} at {node}, but it has unfinished nested mentions ({m.words})", 1)

            # 3. opening or single-word
            else:
                eid, etype, head_idx, other = None, None, None, OtherDualDict()
                for name, value in zip(fields, chunk.split('-')):
                    if name == 'eid':
                        eid = value
                    elif name == 'GRP':
                        eid = tree2docid[node.root] + value
                    elif name == 'etype' or name == 'entity': # entity is an old name for etype used in UD GUM 2.8 and 2.9
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
                subspan_idx, total_subspans = None, '0'
                if eid[-1] == ']':
                    m = RE_DISCONTINUOUS.match(eid)
                    if not m:
                        _error(f"eid={eid} ending with ], but not valid discontinuous mention ID ", strict)
                    else:
                        eid, subspan_idx, total_subspans = m.group(1, 2, 3)

                entity = entities.get(eid)
                if entity is None:
                    if subspan_idx and subspan_idx != '1':
                        _error(f'Non-first subspan of a discontinuous mention {eid} at {node} does not have any previous mention.', 1)
                    entity = CorefEntity(eid)
                    entities[eid] = entity
                    entity.etype = etype
                elif etype and entity.etype and entity.etype != etype:
                    logging.warning(f"etype mismatch in {node}: {entity.etype} != {etype}")
                # CorefEntity could be created first with "Bridge=" without any type
                elif etype and entity.etype is None:
                    entity.etype = etype

                if subspan_idx and subspan_idx != '1':
                    opened = [pair[0] for pair in unfinished_mentions[eid]]
                    mention = next(m for m in discontinuous_mentions[eid] if m not in opened)
                    mention._words.append(node)
                    if closing and subspan_idx == total_subspans:
                        m = discontinuous_mentions[eid].pop()
                        if m is not mention:
                            _error(f"{node}: closing mention {mention.entity.eid} ({mention.words}), but it has an unfinished nested mention ({m.words})", 1)
                        try:
                            mention.head = mention._words[head_idx - 1]
                        except IndexError as err:
                            _error(f"Invalid head_idx={head_idx} for {mention.entity.eid} "
                                    f"closed at {node} with words={mention._words}", 1)
                else:
                    mention = CorefMention(words=[node], entity=entity)
                    if other:
                        mention._other = other
                    if subspan_idx:
                        discontinuous_mentions[eid].append(mention)
                node._mentions.append(mention)

                if not closing:
                    unfinished_mentions[eid].append((mention, head_idx))


        # Bridge, e.g. Entity=(e12-event|Bridge=e12<e124,e12<e125
        # or with relations Bridge=e173<c188:subset,e174<e188:part
        misc_bridge = node.misc['Bridge']
        if misc_bridge:
            BridgingLinks.from_string(misc_bridge, entities, node, strict, tree2docid)

        # SplitAnte, e.g. Entity=(e11-person(e12-person)|SplitAnte=e3<e11,e4<e11,e6<e12,e7<e12
        # which means that both e11 and e12 have split antecedents (e11=e3+e4, e12=e6+e7).
        misc_split = node.misc['SplitAnte']
        if not misc_split and 'Split' in node.misc:
            misc_split = node.misc.pop('Split')
        if misc_split:
            ante_entities = []
            for x in misc_split.split(','):
                ante_str, this_str = x.split('<')
                if ante_str == this_str:
                    _error("SplitAnte cannot self-reference the same entity: " + this_str, strict)
                if tree2docid:
                    ante_str = tree2docid[node.root] + ante_str
                    this_str = tree2docid[node.root] + this_str
                # split cataphora, e.g. "We, that is you and me..."
                if ante_str not in entities:
                    entities[ante_str] = CorefEntity(ante_str)
                entities[this_str].split_ante.append(entities[ante_str])

    for entity_name, mentions in unfinished_mentions.items():
        for mention in mentions:
            logging.warning(f"Mention {entity_name} opened at {mention.head}, but not closed. Deleting.")
            entity = mention.entity
            mention.words = []
            entity._mentions.remove(mention)
            if not entity._mentions:
                del entities[name]

    # c=doc.coref_entities should be sorted, so that c[0] < c[1] etc.
    # In other words, the dict should be sorted by the values (according to CorefEntity.__lt__),
    # not by the keys (eid).
    # In Python 3.7+ (3.6+ in CPython), dicts are guaranteed to be insertion order.
    for entity in entities.values():
        if not entity._mentions:
            _error(f"Entity {entity.eid} referenced in SplitAnte or Bridge, but not defined with Entity", strict)
        entity._mentions.sort()
        for mention in entity._mentions:
            for node in mention._words:
                node._mentions.sort()
    doc._eid_to_entity = {c._eid: c for c in sorted(entities.values())}


def store_coref_to_misc(doc):
    if not doc._eid_to_entity:
        return

    tree2docid = doc.meta.get('tree2docid')
    global_entity = doc.meta.get('global.Entity')
    if not global_entity:
        global_entity = 'eid-etype-head-other'
        doc.meta['global.Entity'] = global_entity

    # global.Entity won't be written without newdoc
    if not doc[0].trees[0].newdoc:
        doc[0].trees[0].newdoc = True

    fields = global_entity.split('-')
    # GRP and entity are legacy names for eid and etype, respectively.
    other_fields = [f for f in fields if f not in ('eid etype head other GRP entity'.split(), )]

    attrs = "Entity SplitAnte Bridge".split()
    for node in doc.nodes_and_empty:
        for attr in attrs:
            del node.misc[attr]

    # Convert each subspan of each discontinuous mention into a fake CorefMention instance,
    # so that we can sort both real and fake mentions and process them in the correct order.
    doc_mentions = []
    for mention in doc.coref_mentions:
        if ',' not in mention.span:
            doc_mentions.append(mention)
        else:
            entity = mention.entity
            head_str = str(mention.words.index(mention.head) + 1)
            subspans = mention.span.split(',')
            root = mention.words[0].root
            for idx,subspan in enumerate(subspans, 1):
                eid = entity.eid
                if tree2docid and 'GRP' in fields:
                    eid = re.sub(r'^d\d+\.', '', eid) # TODO or "eid = entity.eid_or_grp"?
                subspan_eid = f'{eid}[{idx}/{len(subspans)}]'
                subspan_words = span_to_nodes(root, subspan)
                fake_entity = CorefEntity(subspan_eid, entity.etype)
                fake_mention = CorefMention(subspan_words, head_str, fake_entity, add_word_backlinks=False)
                if mention._other:
                    fake_mention._other = mention._other
                if mention._bridging and idx == 1:
                    fake_mention._bridging = mention._bridging
                doc_mentions.append(fake_mention)
    doc_mentions.sort()

    for mention in doc_mentions:
        entity = mention.entity
        values = []
        for field in fields:
            if field == 'eid' or field == 'GRP':
                eid = entity.eid
                if field == 'GRP':
                    eid = re.sub(r'^d\d+\.', '', eid)
                if any(x in eid for x in CHARS_FORBIDDEN_IN_ID):
                    _error(f"{eid} contains forbidden characters [{CHARS_FORBIDDEN_IN_ID}]", strict)
                    for c in CHARS_FORBIDDEN_IN_ID:
                        eid = eid.replace(c, '')
                values.append(eid)
            elif field == 'etype' or field == 'entity':
                if not entity.etype:
                    values.append('')
                else:
                    values.append(entity.etype)
            elif field == 'head':
                if isinstance(mention.head, str):
                    values.append(mention.head) # fake mention for discontinuous spans
                else:
                    values.append(str(mention.words.index(mention.head) + 1))
            elif field == 'other':
                if not mention._other:
                    values.append('')
                elif not other_fields:
                    values.append(str(mention.other))
                else:
                    other_copy = OtherDualDict(mention.other)
                    for other_field in other_fields:
                        del other_copy[other_field]
                    values.append(str(other_copy))
            elif field == 'identity':
                values.append(mention.other[field]) # don't replace('%2C', ',') in wikification
            else:
                values.append(mention.other[field].replace('%2C', ',')) # but de-escape commas e.g. in minspan
        # optional fields
        while values and values[-1] == '':
            del values[-1]
        mention_str = '(' + '-'.join(values)

        # First, handle single-word mentions.
        # If there are no opening brackets (except for single-word),
        # single-word mentions should precede all closing brackets, e.g. `Entity=(e10)(e9)e4)e3)`.
        # Otherwise, single-word mentions should follow all opening brackets,
        # e.g. `Entity=(e1(e2(e9)(e10)` or `Entity=e4)e3)(e1(e2(e9)(e10)`.
        firstword = mention.words[0]
        if len(mention.words) == 1:
            orig_entity = firstword.misc['Entity']
            # empty     --> (e10)
            # (e1(e2    --> (e1(e2(e10)
            # e3)(e1(e2 --> e3)(e1(e2(e10)
            if not orig_entity or orig_entity[-1] != ')':
                firstword.misc['Entity'] += mention_str + ')'
            # e4)e3)    --> (e10)e4)e3)
            elif '(' not in orig_entity:
                firstword.misc['Entity'] = mention_str + ')' + orig_entity
            # (e9)e4)e3) --> (e10)(e9)e4)e3)
            elif any(c and c[0] == '(' and c[-1] != ')' for c in re.split(r'(\([^()]+\)?|[^()]+\))', orig_entity)):
                firstword.misc['Entity'] += mention_str + ')'
            # (e1(e2(e9)   --> (e1(e2(e9)(e10)
            # e3)(e1(e2(e9)--> e3)(e1(e2(e9)(e10)
            else:
                firstword.misc['Entity'] = mention_str + ')' + orig_entity
        # Second, multi-word mentions. Opening brackets should follow closing brackets.
        else:
            firstword.misc['Entity'] += mention_str
            eid = entity.eid
            if tree2docid and 'GRP' in fields:
                eid = re.sub(r'^d\d+\.', '', eid)
            mention.words[-1].misc['Entity'] = eid + ')' + mention.words[-1].misc['Entity']

        # Bridge=e1<e5:subset,e2<e6:subset|Entity=(e5(e6
        if mention._bridging:
            mention._bridging._delete_targets_without_mentions()
            str_bridge = str(mention._bridging)
            if firstword.misc['Bridge']:
                str_bridge = firstword.misc['Bridge'] + ',' + str_bridge
            firstword.misc['Bridge'] = str_bridge

    # SplitAnte=e5<e61,e10<e61
    for entity in doc.coref_entities:
        if entity.split_ante:
            for ante_entity in entity.split_ante:
                if not ante_entity.mentions:
                    logging.warning(f"Entity {ante_entity.eid} has no mentions, but is referred to in SplitAnte of {entity.eid}")
                    entity.split_ante.remove(ante_entity)
            if not entity.split_ante or len(entity.split_ante) < 2:
                logging.warning(f"SplitAnte of {entity.eid} has less than two antecedents, omitting")
                continue
            first_word = entity.mentions[0].words[0]
            if tree2docid:
                strs = ','.join(f'{sa.eid_or_grp}<{entity.eid_or_grp}' for sa in entity.split_ante)
            else:
                strs = ','.join(f'{sa.eid}<{entity.eid}' for sa in entity.split_ante)
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
                    serialized.append(f"{name}:{value}")
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
