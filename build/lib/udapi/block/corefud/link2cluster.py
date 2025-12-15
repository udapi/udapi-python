import logging
from udapi.core.block import Block

class Link2Cluster(Block):
    """Block corefud.Link2Cluster converts link-based coreference annotation to the (cluster-based) CorefUD format.

    Params:
    id_attr: name of the attribute in MISC that stores the original-format IDs of nodes
    ante_attr: name of the attribute in MISC that stores the ID of the antecedent
        of the current node (in the same format as `id_attr`).
    delete_orig_attrs: Should we delete the MISC attributes that were used for the conversion?
        (i.e. id_attr and ante_attr, plus possibly also infstat_attr, coreftype_attr,
        bridge_attr, bridge_relation_attr if these are used). Default=True.
    infstat_attr: name of the attribute in MISC that stores the information status of a given mention
        Will be stored in `mention.other['infstat']`. Use None for ignoring this.
    coreftype_attr: name of the attribute in MISC that stores the coreference type of a given mention
        Will be stored in `mention.other['coreftype']`. Use None for ignoring this.
    bridge_attr: name of the attribute in MISC that stores the ID of the bridging antecedent
        of the current node/mention (in the same format as `id_attr`).
        Default=None, i.e. ignore this parameter.
    bridge_relation_attr:  name of the attribute in MISC that stores the bridging relation type
        (e.g. "part" or "subset"). Default=None, i.e. ignore this parameter.
    eid_counter: use a global counter of entity.eid and start with a given number. Default=1.
        The main goal of this parameter is to make eid unique across multiple documents.
        If you use eid_counter=0, this feature will be turned off,
        so entities will be created using `root.document.create_coref_entity()`,
        with no eid parameter, so that the eid will start from "e1" in each document processed by this block.
    """
    def __init__(self, id_attr='proiel-id', ante_attr='antecedent-proiel-id', delete_orig_attrs=True,
                 infstat_attr='information-status', coreftype_attr='coreftype',
                 bridge_attr=None, bridge_relation_attr=None, eid_counter=1, **kwargs):
        super().__init__(**kwargs)
        self.id_attr = id_attr
        self.ante_attr = ante_attr
        self.delete_orig_attrs = delete_orig_attrs
        self.infstat_attr = infstat_attr
        self.coreftype_attr = coreftype_attr
        self.bridge_attr = bridge_attr
        self.bridge_relation_attr = bridge_relation_attr
        self.eid_counter = int(eid_counter)

    def _new_entity(self, doc):
        if not self.eid_counter:
            return doc.create_coref_entity()
        entity = doc.create_coref_entity(eid=f"e{self.eid_counter}")
        self.eid_counter += 1
        return entity

    def _new_mention(self, entity, node):
        mention = entity.create_mention(head=node, words=[node])
        if self.infstat_attr and node.misc[self.infstat_attr]:
            mention.other['infstat'] = node.misc[self.infstat_attr]
            if self.delete_orig_attrs:
                del node.misc[self.infstat_attr]
        if self.coreftype_attr and node.misc[self.coreftype_attr]:
            mention.other['coreftype'] = node.misc[self.coreftype_attr]
            if self.delete_orig_attrs:
                del node.misc[self.coreftype_attr]
        return mention

    def process_document(self, doc):
        id2node = {}
        links = []
        bridges = []
        for node in doc.nodes_and_empty:
            this_id = node.misc[self.id_attr]
            if this_id != '':
                id2node[this_id] = node
                ante_id = node.misc[self.ante_attr]
                if ante_id != '':
                    if ante_id == this_id:
                        logging.warning(f"{node} has a self-reference {self.ante_attr}={ante_id}")
                    else:
                        links.append([ante_id, this_id])
                if self.delete_orig_attrs:
                    for attr in (self.id_attr, self.ante_attr):
                        del node.misc[attr]
                if self.bridge_attr:
                    bridge_id = node.misc[self.bridge_attr]
                    if bridge_id != '':
                        if bridge_id == this_id:
                            logging.warning(f"{node} has a self-reference bridging {self.bridge_attr}={bridge_id}")
                        else:
                            bridges.append([bridge_id, this_id, node.misc[self.bridge_relation_attr]])
                        if self.delete_orig_attrs:
                            for attr in (self.bridge_attr, self.bridge_relation_attr):
                                del node.misc[attr]

        # It seems faster&simpler to process the links in any order and implement entity merging,
        # rather than trying to sort the links so that no entity merging is needed.
        for ante_id, this_id in links:
            if ante_id not in id2node:
                logging.warning(f"{ante_id} is referenced in {self.ante_attr}, but not in {self.id_attr}")
            else:
                ante_node, this_node = id2node[ante_id], id2node[this_id]
                if not this_node.coref_mentions and not ante_node.coref_mentions:
                    # None of the nodes is part of any mention/entity. Let's create them.
                    entity = self._new_entity(this_node.root.document)
                    self._new_mention(entity, ante_node)
                    self._new_mention(entity, this_node)
                elif this_node.coref_mentions and ante_node.coref_mentions:
                    # Both of the nodes are part of mentions in different entities.
                    # Let's merge the two entities (i.e. "steal" all mentions from the "ante" entity to "this" entity).
                    # While the official API supports "stealing" a single mention (m.entity = another_entity),
                    # the implementation below using _mentions and _entity is a bit faster.
                    e_ante, e_this = this_node.coref_entities[0], ante_node.coref_entities[0]
                    assert e_ante != e_this
                    for mention in e_ante.mentions:
                        mention._entity = e_this
                    e_this._mentions.extend(e_ante.mentions)
                    e_this._mentions.sort()
                    e_ante._mentions.clear()
                else:
                    # Only one of the nodes is part of an entity. Let's add the second one to this entity.
                    if ante_node.coref_mentions:
                        self._new_mention(ante_node.coref_entities[0], this_node)
                    else:
                        self._new_mention(this_node.coref_entities[0], ante_node)

        # Bridging
        for ante_id, this_id, relation in bridges:
            if ante_id not in id2node:
                logging.warning(f"{ante_id} is referenced in {self.bridge_attr}, but not in {self.id_attr}")
            else:
                ante_node, this_node = id2node[ante_id], id2node[this_id]
                if ante_node.coref_mentions:
                    m_ante = next(m for m in ante_node.coref_mentions if m.head is ante_node)
                    e_ante = m_ante.entity
                else:
                    e_ante = self._new_entity(ante_node.root.document)
                    m_ante = self._new_mention(e_ante, ante_node)
                if this_node.coref_mentions:
                    m_this = next(m for m in this_node.coref_mentions if m.head is this_node)
                else:
                    e_this = self._new_entity(this_node.root.document)
                    m_this = self._new_mention(e_this, this_node)
                m_this.bridging.append((e_ante, relation))
