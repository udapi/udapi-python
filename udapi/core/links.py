"""Links is a class for storing a set of links with the same source node."""
import collections.abc
import logging
import re

Link = collections.namedtuple('Link', 'node relation')

class Links(list):
    """Links class serves as a `list` with additional methods.

    >>> enhdeps = EnhDeps('4:nsubj|11:nsubj')
    >>> for enhdep in enhdeps:
    >>>   str(enhdep)
    '4:nsubj'
    '11:nsubj'
    >>> enhdeps[0].parent = node_with_ord5
    >>> enhdeps[0].deprel = 'obj'
    >>> str(enhdeps)
    '5:obj|11:nsubj'

    This class provides access to both
    * a structured (list of named tuples) representation and
    * a string (serialized) representation of the enhanced depndencies.

    Implementation details:
    Unlike `DualDict`
    * the structured internal storage is list, not dict
    * the string representation is always computed on the fly, it is not stored.
    """

    def __init__(self, src_node, string=None):
        self.src_node = src_node
        items = []
        if string is not None:
            all_nodes = src_node.root.descendants(add_self=1)
            for edge_str in string.split('|'):
                try:
                    trg_node_id, relation = edge_str.split(':')
                except ValueError as exception:
                    logging.error("<%s> contains <%s> which does not contain one ':' symbol.",
                                  string, edge_str)
                    raise exception
                # TODO allow `trg_node_id`s like 5.1, /zone#1, bundle/zone#1, bundle#1
                trg_node = all_nodes[int(trg_node_id)]
                link = Link(node=trg_node, relation=relation)
                items.append(link)
        super().__init__(self, items)

    def __str__(self):
        serialized = []
        for link in self:
            # TODO allow `trg_node_id`s like /zone#1, bundle/zone#1, bundle#1
            serialized.append('%s:%s' % (link.node.ord, link.relation))
        return '|'.join(serialized) if serialized else '_'

    def set_links(self, value):
        """Set the edges from a list of tuples or string.

        If the `value` is None or an empty string, it is converted to storing empty list of edges.
        If the `value` is a string, it is parsed as in `__init__`.
        If the `value` is a list of `Edge` namedtuples its copy is stored.
        Other types of `value` raise an `ValueError` exception.
        """
        if value is None:
            self.clear()
        elif isinstance(value, str):
            self.clear()
            self.__init__(value)
        elif isinstance(value, collections.abc.Sequence):
            self.clear()
            super().__init__(value)
        else:
            raise ValueError("Unsupported value type " + str(value))

    def __call__(self, following_only=False, preceding_only=False, relations=None):
        """Return a subset of links contained in this list as specified by the args.

        TODO: document args
        """
        if not following_only and not preceding_only and relations is None:
            return self
        links = list(self)
        if preceding_only:
            links = [l for l in links if l.node.precedes(self.src_node)]
        if following_only:
            links = [l for l in links if self.src_node.precedes(l.node)]
        if relations:
            links = [l for l in links if re.match(relations, l.relation)]
        return Links(self.src_node, links)

    @property
    def nodes(self):
        """Return a list of the target nodes (without relations)."""
        return [link.node for link in self]

    # TODO make sure backlinks are created and updated
    def TODO__setitem__(self, index, new_value):
        old_value = self[index]
        old_value.node._enh_children = [l for l in old_value.node._enh_children if l != old_value]
        if new_value.node._enh_children is None:
            new_value.node._enh_children = Links(new_value.node, None)
        super().__setitem__(self, index, new_value)
