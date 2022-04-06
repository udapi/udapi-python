import re
import logging
from collections import defaultdict
from udapi.core.block import Block

class Gum2CorefUD(Block):

    def process_tree(self, tree):
        docname = tree.bundle.document.meta['docname'] + '_'

        eid_to_entity = tree.bundle.document._eid_to_entity
        unfinished_mentions = defaultdict(list)
        for node in tree.descendants:
            misc_entity = node.misc['Entity']
            if not misc_entity:
                continue
            # Attribute Entity may contain multiple entities, e.g.
            # Entity=(abstract-7-new-2-coref(abstract-3-giv:act-1-coref)
            # means a start of entity id=7 and start&end (i.e. single-word mention) of entity id=3.
            # The following re.split line splits this into
            # entities = ["(abstract-7-new-2-coref", "(abstract-3-giv:act-1-coref)"]
            entities = [x for x in re.split('(\([^()]+\)?|[^()]+\))', misc_entity) if x]
            for entity in entities:
                # GUM 2.9 uses global.Entity = entity-GRP-infstat-MIN-coref_type-identity
                # but the closing tag is shortent just to GRP.
                opening, closing = (entity[0] == '(', entity[-1] == ')')
                entity = entity.strip('()')
                if not opening and not closing:
                    logging.warning(f"Entity {entity} at {node} has no opening nor closing bracket.")
                elif not opening and closing:
                    name = docname + entity
                    if not unfinished_mentions[name]:
                        raise ValueError(f"Mention {name} closed at {node}, but not opened in the same tree.")
                    else:
                        mention = unfinished_mentions[name].pop()
                        mention.span = f'{mention.head.ord}-{node.ord}'
                else:
                    attrs = entity.split('-')
                    if len(attrs) == 6:
                        etype, grp, infstat, minspan, ctype, wiki = attrs
                    elif len(attrs) == 5:
                        wiki = None
                        etype, grp, infstat, minspan, ctype = attrs
                    elif len(attrs) > 6:
                        logging.warning(f"Entity {entity} at {node} has more than 6 attributes.")
                        etype, grp, infstat, minspan, ctype, wiki = entity.split('-', maxsplit=5)
                    else:
                        raise ValueError(f"Less than 5 attributes in {entity} at {node}")
                    name = docname + grp
                    entity = eid_to_entity.get(name)
                    if entity is None:
                        entity = node.create_coref_entity(eid=name, etype=etype)
                        mention = entity.mentions[0]
                        mention.misc = f"Infstat:{infstat},MinSpan:{minspan},CorefType:{ctype}"
                        if wiki:
                            mention.misc += ',Wikification:' + wiki  #.replace(',', '%2C')
                    else:
                        mention = entity.create_mention(head=node)
                    if closing:
                        mention.words = [node]
                    else:
                        unfinished_mentions[name].append(mention)
            del node.misc['Entity']

            misc_bridges = node.misc['Bridge']
            if misc_bridges:
                # E.g. Entity=event-12|Bridge=12<124,12<125
                for misc_bridge in misc_bridges.split(','):
                    try:
                        trg_str, src_str = [docname + grp for grp in misc_bridge.split('<')]
                    except ValueError as err:
                        raise ValueError(f"{node}: {misc_bridge} {err}")
                    try:
                        trg_entity = eid_to_entity[trg_str]
                        src_entity = eid_to_entity[src_str]
                    except KeyError as err:
                        logging.warning(f"{node}: Cannot find entity {err}")
                    else:
                        mention = src_entity.mentions[-1]
                        # TODO: what relation should we choose for Bridging?
                        # relation = f"{src_str.split('-')[0]}-{trg_str.split('-')[0]}"
                        relation = '_'
                        mention.bridging.append((trg_entity, relation))
                del node.misc['Bridge']

            misc_split = node.misc['Split']
            if misc_split:
                # E.g. Entity=(person-54)|Split=4<54,9<54
                src_str = docname + misc_split.split('<')[-1]
                ante_entities = []
                for x in misc_split.split(','):
                    ante_str, this_str = [docname + grp for grp in x.split('<')]
                    if this_str != src_str:
                        raise ValueError(f'{node} invalid Split: {this_str} != {src_str}')
                        # logging.warning
                        # There are just three such cases in GUM and all are bugs,
                        # so let's ignore them entirely (the `else` clause will be skipped if exiting `for` w/ `break`).
                        # break
                    ante_entities.append(eid_to_entity[ante_str])
                else:
                    eid_to_entity[src_str].split_ante = ante_entities
                del node.misc['Split']

        for entity_name, mentions in unfinished_mentions.items():
            for mention in mentions:
                logging.warning(f"Mention {name} opened at {mention.head}, but not closed in the same tree. Deleting.")
                entity = mention.entity
                mention.words = []
                entity._mentions.remove(mention)
                if not entity._mentions:
                    del eid_to_entity[name]
