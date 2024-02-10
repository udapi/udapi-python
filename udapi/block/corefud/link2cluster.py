import logging
from udapi.core.block import Block

class Link2Cluster(Block):
    """Block corefud.Link2Cluster converts link-based coreference annotation to the (cluster-based) CorefUD format."""

    def __init__(self, id_attr='proiel-id', ante_attr='antecedent-proiel-id', delete_orig_attrs=True, **kwargs):
        super().__init__(**kwargs)
        self.id_attr = id_attr
        self.ante_attr = ante_attr
        self.delete_orig_attrs = delete_orig_attrs

    def process_document(self, doc):
        id2node = {}
        links = []
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

        # It seems faster&simpler to process the links in any order and implement entity merging,
        # rather than trying to sort the links so that no entity merging is needed.
        for ante_id, this_id in links:
            if ante_id not in id2node:
                logging.warning(f"{ante_id} is referenced in {self.ante_attr}, but not in {self.id_attr}")
            else:
                ante_node, this_node = id2node[ante_id], id2node[this_id]
                if not this_node.coref_mentions and not ante_node.coref_mentions:
                    # None of the nodes is part of any mention/entity. Let's create them.
                    entity = this_node.root.document.create_coref_entity()
                    m_ante = entity.create_mention(head=ante_node, words=[ante_node])
                    m_this = entity.create_mention(head=this_node, words=[this_node])
                    for node, mention in ((ante_node, m_ante), (this_node, m_this)):
                        if node.misc['information-status']:
                            mention.other['infstat'] = node.misc['information-status']
                            if self.delete_orig_attrs:
                                del node.misc['information-status']
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
                        ante_node.coref_entities[0].create_mention(head=this_node, words=[this_node])
                    else:
                        this_node.coref_entities[0].create_mention(head=ante_node, words=[ante_node])
