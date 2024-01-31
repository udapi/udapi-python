from udapi.core.block import Block

class Link2Cluster(Block):
    """Block corefud.Link2Cluster converts link-based coreference annotation to the (cluster-based) CorefUD format."""

    def __init__(self, id_attr='external-id', ante_attr='antecedent-id', **kwargs):
        super().__init__(**kwargs)
        self.id_attr = id_attr
        self.ante_id = ante_attr

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

        # sorted(...,reverse=True) converts both cataphora and anaphora to a pair (this, ante) where ante < this.
        node_links = [sorted([id2node[link[0]], id2node[link[1]]], reverse=True) for link in links]
        
        # sort() makes sure the links are sorted by the "this" node (i.e. the anaphor, not the antecendent).
        node_links.sort()
        
        # Thanks to this sorting, we can assert that this_node is not part of any mention/entity when iterating
        # and we can prevent the need for merging two entities.
        for this_node, ante_node in node_links:
            assert not this_node.mentions
            if ante_node.mentions:
                ante_node.entities[0].create_mention(head=this_node, words=[this_node])
            else:
                entity = this_node.root.document.create_coref_entity()
                entity.create_mention(head=ante_node, words=[ante_node])
                entity.create_mention(head=this_node, words=[this_node])
