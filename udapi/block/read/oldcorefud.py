"""Reader for CoNLL-U files with the old CorefUD 0.1 style of coreference annotation."""
import re
import logging
import udapi.block.read.conllu
from udapi.core.coref import CorefEntity, CorefMention, BridgingLinks

class OldCorefUD(udapi.block.read.conllu.Conllu):

    def __init__(self, replace_hyphen_in_id_with='', **kwargs):
        """Create the read.OldCorefUD reader object.

        Args:
        substitute_hyphen_in_id_for: string to use as a replacement for hyphens in ClusterId
          The new format does not allow hyphens in eid (IDs of entity entities),
          so we need to replace them.
        """
        super().__init__(**kwargs)
        self.replace_hyphen_in_id_with = replace_hyphen_in_id_with
        self.orig2new = {}
        self.new2orig = {}

    def _fix_id(self, cid):
        if not cid or '-' not in cid:
            return cid
        new_cid = self.orig2new.get(cid)
        if new_cid is None:
            new_cid = cid.replace('-', self.replace_hyphen_in_id_with)
            base, counter = new_cid, 1
            while new_cid in self.new2orig:
                counter += 1
                new_cid = f"{base}{counter}"
            self.new2orig[new_cid] = cid
            self.orig2new[cid] = new_cid
        return new_cid

    def process_document(self, doc, strict=True):
        super().process_document(doc)

        eid_to_entity = {}
        for node in doc.nodes_and_empty:
            index, index_str = 0, ""
            eid = node.misc["ClusterId"]
            if not eid:
                index, index_str = 1, "[1]"
                eid = node.misc["ClusterId[1]"]
            eid = self._fix_id(eid)
            while eid:
                entity = eid_to_entity.get(eid)
                if entity is None:
                    entity = CorefEntity(eid)
                    eid_to_entity[eid] = entity
                mention = CorefMention(words=[node], entity=entity)
                if node.misc["MentionSpan" + index_str]:
                    mention.span = node.misc["MentionSpan" + index_str]
                etype = node.misc["ClusterType" + index_str]
                if etype:
                    if entity.etype is not None and etype != entity.etype:
                        logging.warning(f"etype mismatch in {node}: {entity.etype} != {etype}")
                    entity.etype = etype

                bridging_str = node.misc["Bridging" + index_str]
                if bridging_str:
                    mention._bridging = BridgingLinks(mention)
                    for link_str in bridging_str.split(','):
                        target, relation = link_str.split(':')
                        target = self._fix_id(target)
                        if target == eid:
                            _error("Bridging cannot self-reference the same entity: " + target, strict)
                        if target not in eid_to_entity:
                            eid_to_entity[target] = CorefEntity(target)
                        mention._bridging.append((eid_to_entity[target], relation))

                split_ante_str = node.misc["SplitAnte" + index_str]
                if split_ante_str:
                    split_antes = []
                    # TODO in CorefUD draft "+" was used as the separator, but it was changed to comma.
                    # We can delete `.replace('+', ',')` once there are no more data with the legacy plus separator.
                    for ante_str in split_ante_str.replace('+', ',').split(','):
                        ante_str = self._fix_id(ante_str)
                        if ante_str in eid_to_entity:
                            if ante_str == eid:
                                _error("SplitAnte cannot self-reference the same entity: " + eid, strict)
                            split_antes.append(eid_to_entity[ante_str])
                        else:
                            # split cataphora, e.g. "We, that is you and me..."
                            ante_cl = CorefEntity(ante_str)
                            eid_to_entity[ante_str] = ante_cl
                            split_antes.append(ante_cl)
                    entity.split_ante = sorted(split_antes)

                # Some CorefUD 0.2 datasets (e.g. ARRAU) separate key-value pairs with spaces instead of commas.
                # We also need to escape forbidden characters.
                mmisc = node.misc["MentionMisc" + index_str].replace(' ', ',')
                mention.other = mmisc.replace('-', '%2D').replace('(', '%28').replace(')', '%29')
                index += 1
                index_str = f"[{index}]"
                eid = self._fix_id(node.misc["ClusterId" + index_str])
        # c=doc.coref_entities should be sorted, so that c[0] < c[1] etc.
        # In other words, the dict should be sorted by the values (according to CorefEntity.__lt__),
        # not by the keys (eid).
        # In Python 3.7+ (3.6+ in CPython), dicts are guaranteed to be insertion order.
        for entity in eid_to_entity.values():
            if not entity._mentions:
                _error(f"Entity {entity.eid} referenced in SplitAnte or Bridging, but not defined with ClusterId", strict)
            entity._mentions.sort()
        doc._eid_to_entity = {c._eid: c for c in sorted(eid_to_entity.values())}

        # Delete all old-style attributes from MISC (so when converting old to new style, the old attributes are deleted).
        attrs = "ClusterId MentionSpan ClusterType Bridging SplitAnte MentionMisc".split()
        for node in doc.nodes_and_empty:
            for key in list(node.misc):
                if any(re.match(attr + r'(\[\d+\])?$', key) for attr in attrs):
                    del node.misc[key]


def _error(msg, strict):
    if strict:
        raise ValueError(msg)
    logging.error(msg)
