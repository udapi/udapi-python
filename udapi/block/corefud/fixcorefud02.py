from udapi.core.block import Block
import udapi.core.coref
import itertools

NEW_ETYPE = {
    "misc": "other",
    "date": "time",
    "loc": "place",
    "location": "place",
    "per": "person",
    "org": "organization",
    "_": "",
    }

class FixCorefUD02(Block):
    """Fix errors in CorefUD 0.2 for release of CorefUD 1.0."""

    def process_document(self, doc):
        # For GUM
        if doc.meta['global.Entity'] == 'entity-GRP-infstat-MIN-coref_type-identity':
            doc.meta['global.Entity'] = 'eid-etype-head-other-infstat-minspan-identity'

        for entity in doc.coref_entities:
            if entity.etype:
                # Harmonize etype.
                # If gen/spec is distinguished, store it in all mentions' other['gstype'].
                etype = entity.etype.lower()
                if etype.startswith('spec') or etype.startswith('gen'):
                    gstype = 'gen' if etype.startswith('gen') else 'spec'
                    for m in entity.mentions:
                        m.other['gstype'] = gstype
                    if etype == 'spec':
                        etype = 'other'
                    etype = etype.replace('gen', '').replace('spec', '').replace('.', '')
                etype = NEW_ETYPE.get(etype, etype)
                
                # etype="APPOS" is used only in NONPUBL-CorefUD_English-OntoNotes.
                # Apposition is a mention-based rather than entity-based attribute.
                # We don't know which of the mentions it should be assigned, but let's expect all non-first.
                # UD marks appositions with deprel appos, so once someone checks it is really redunant,
                # TODO we can delete the appos mention attribute.
                if etype == 'appos':
                    etype = ''
                    for mention in entity.mentions[1:]:
                        mention.other['appos'] = '1'
                entity.etype = etype

            for mention in entity.mentions:
                # Harmonize bridge relation labels
                for bridge in mention.bridging:
                    rel = bridge.relation.lower()
                    if rel.endswith('-inv'):
                        rel = 'i' + rel.replace('-inv', '')
                    rel = rel.replace('-', '')
                    rel = rel.replace('indirect_', '')
                    bridge.relation = rel
