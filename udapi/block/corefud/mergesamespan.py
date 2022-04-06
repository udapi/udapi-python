from udapi.core.block import Block
import udapi.core.coref
import itertools
import logging

class MergeSameSpan(Block):
    """
    Multiple same-span mentions are considered invalid in CoNLL-U, whether they
    belong to the same entity or not. If they occur, merge them into one.
    Note: We currently do not have mentions across sentence boundaries in the
    CorefUD data, so this block processes one sentence at a time.
    """

    def __init__(self, same_entity_only=False, **kwargs):
        super().__init__(**kwargs)
        self.same_entity_only = same_entity_only

    def process_tree(self, tree):
        mentions = set()
        for node in tree.descendants_and_empty:
            for m in node.coref_mentions:
                mentions.add(m)

        for mA, mB in itertools.combinations(mentions, 2):
            if self.same_entity_only and mA.entity != mB.entity:
                continue
            # Reduce non-determinism in which mention is removed:
            # If the mentions belong to different entities, sort them by entity (entity) ids.
            if mA.entity.eid > mB.entity.eid:
                mA, mB = mB, mA

            sA, sB = set(mA.words), set(mB.words)
            if sA != sB:
                continue

            # If the mentions belong to different entities, we should merge the
            # entities first, i.e., pick one entity as the survivor, move the
            # mentions from the other entity to this entity, and remove the
            # other entity.
            if mA.entity != mB.entity:
                logging.warning(f"Merging same-span mentions that belong to different entities: {mA.entity.eid} vs. {mB.entity.eid}")
                ###!!! TODO: As of now, changing the entity of a mention is not supported in the API.
                #for m in mB.entity.mentions:
                #    m.entity = mA.entity
            # Remove mention B. It may have been removed earlier because of
            # another duplicate, that is the purpose of try-except.
            ###!!! TODO: If we remove a singleton, we are destroying the entity. Then we must also handle possible bridging and split antecedents pointing to that entity!
            mB.words = []
            try:
                mB.entity.mentions.remove(mB)
            except ValueError:
                pass
