"""Writer for CoNLL-U files with the old CorefUD 0.1 style of coreference annotation."""
import re
import logging
import udapi.block.write.conllu

class OldCorefUD(udapi.block.write.conllu.Conllu):

    def process_document(self, doc):
        if not doc.coref_entities:
            logging.warning("Using write.OldCorefUD on a document without any coreference annotation")

        # Delete both new-style (GUM-style) and old-style (CorefUD 0.1) coreference annotations from MISC.
        attrs = "Entity Split Bridge ClusterId MentionSpan ClusterType Bridging SplitAnte MentionMisc".split()
        for node in doc.nodes_and_empty:
            for key in list(node.misc):
                if any(re.match(attr + r'(\[\d+\])?$', key) for attr in attrs):
                    del node.misc[key]
        del doc.meta['global.Entity']

        # doc._eid_to_entity is a dict, which is insertion ordered in Python 3.7+.
        # The insertion order is sorted according to CorefEntity.__lt__ (see few lines above).
        # However, new entities could be added meanwhile or some entities edited,
        # so we need to sort the entities again before storing to MISC.
        # We also need to mare sure entity.mentions are sorted in each entity
        # because the ordering of entities is defined by the first mention in each entity.
        # Ordering of mentions within a entity can be changed when e.g. changing the span
        # of a given mention or reordering words within a sentence and in such events
        # Udapi currently does not automatically update the ordering of entities.
        for entity in doc.coref_entities:
            entity._mentions.sort()
        for entity in sorted(doc.coref_entities):
            for mention in entity.mentions:
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
                head.misc["ClusterId" + index_str] = entity.eid
                head.misc["MentionSpan" + index_str] = mention.span
                head.misc["ClusterType" + index_str] = entity.etype
                if mention._bridging:
                    head.misc["Bridging" + index_str] = ','.join(f'{l.target.eid}:{l.relation}' for l in sorted(mention.bridging))
                if entity.split_ante:
                    serialized = ','.join((c.eid for c in sorted(entity.split_ante)))
                    head.misc["SplitAnte" + index_str] = serialized
                if mention.other:
                    head.misc["MentionMisc" + index_str] = str(mention.other).replace('%2D', '-')

        super().process_document(doc)
