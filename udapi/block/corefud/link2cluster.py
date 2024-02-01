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
        for node in doc.nodes:
            this_id = node.misc[self.id_attr]
            if this_id != '':
                id2node[this_id] = node
                ante_id = node.misc[self.ante_attr]
                if ante_id != '':
                    links.append([ante_id, this_id])
                if self.delete_orig_attrs:
                    for attr in (self.id_attr, self.ante_attr):
                        del node.misc[attr]

        for link in links:
            if link[0] not in id2node:
                logging.warning(f"{link[0]} is referenced in {self.ante_attr}, but not in {self.id_attr}")               
        links = [link for link in links if link[0] in id2node]        

        # nodeA < nodeB is a shortcut for nodeA.ord < nodeB.ord
        # but here we need to sort nodes from different sentences,
        # so we need to compare first the bundle number and then node.ord.
        sort_key = lambda node: (node.root.bundle.number, node.ord)

        # sorted(...,reverse=True) converts both cataphora and anaphora to a pair (this, ante) where ante < this.
        node_links = [sorted([id2node[link[0]], id2node[link[1]]], reverse=True, key=sort_key) for link in links]
        
        # Makes sure the links are sorted by this_node (i.e. the anaphor, not the antecendent).
        node_links.sort(key=lambda link: sort_key(link[0]))
        
        # Thanks to this sorting, we can assert that this_node is not part of any mention/entity when iterating
        # and we can prevent the need for merging two entities.
        for this_node, ante_node in node_links:
            assert not this_node.coref_mentions
            if ante_node.coref_mentions:
                ante_node.coref_entities[0].create_mention(head=this_node, words=[this_node])
            else:
                entity = this_node.root.document.create_coref_entity()
                m_ante = entity.create_mention(head=ante_node, words=[ante_node])
                m_this = entity.create_mention(head=this_node, words=[this_node])
                for node, mention in ((ante_node, m_ante), (this_node, m_this)):
                    if node.misc['information-status']:
                        mention.other['infstat'] = node.misc['information-status']
                        if self.delete_orig_attrs:
                            del node.misc['information-status']
