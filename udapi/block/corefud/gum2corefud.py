import re
import logging
from collections import defaultdict
from udapi.core.block import Block

class Gum2CorefUD(Block):

    def process_tree(self, tree):
        docname = tree.bundle.document.meta['docname'] + '_'

        def entity2cluster_id(name):
            return docname + name.strip('()').replace(',','').replace('+','')

        clusters = tree.bundle.document.coref_clusters
        unfinished_mentions = defaultdict(list)
        for node in tree.descendants:
            entity = node.misc['Entity']
            if not entity:
                continue
            parts = [x for x in re.split('(\([^())]+\)?|[^())]+\))', entity) if x]
            for part in parts:
                # GUM entity name could be e.g.
                # abstract-173 or place-1-Coron,_Palawan or place-77-Sub-Saharan_Africa.
                # Note that the wikification part of the name may contain commas and dashes.
                # Let's take the whole name as cluster_id, which will be normalized later on.
                # We just need to remove commas and plus signs which are forbidden in cluster_id
                # because they are used as separators in Bridging and SplitAnte, respectively.
                # Let's store the type in cluster.cluster_type and Wikification in mention.misc.
                name = entity2cluster_id(part)
                if part[0] == '(':
                    cluster = clusters.get(name)
                    if cluster is None:
                        chunks = part.strip('()').split('-', maxsplit=2)
                        if len(chunks) == 3:
                            ctype, _, wiki = chunks
                        elif len(chunks) == 2:
                            ctype, _, wiki = chunks[0], None, None
                        else:
                            raise ValueError(f"Unexpected entity {part} at {node}")
                        cluster = node.create_coref_cluster(cluster_id=name, cluster_type=ctype)
                        mention = cluster.mentions[0]
                        if wiki:
                            mention.misc = 'Wikification:' + wiki.replace(',', '%2C')
                    else:
                        mention = cluster.create_mention(head=node)
                    if part[-1] == ')':
                        mention.words = [node]
                    else:
                        unfinished_mentions[name].append(mention)
                elif part[-1] == ')':
                    if not unfinished_mentions[name]:
                        logging.warning(f"Mention {name} closed at {node}, but not opened in the same tree.")
                    else:
                        mention = unfinished_mentions[name].pop()
                        mention.span = f'{mention.head.ord}-{node.ord}'
            del node.misc['Entity']

            misc_bridge = node.misc['Bridge']
            if misc_bridge:
                # E.g. Entity=event-23|Bridge=time-23<event-28
                trg_str, src_str = (entity2cluster_id(x) for x in misc_bridge.split('<'))
                try:
                    trg_cluster = clusters[trg_str]
                    src_cluster = clusters[src_str]
                except KeyError as err:
                    logging.warning(f"{node}: Cannot find cluster {err}")
                else:
                    mention = src_cluster.mentions[-1]
                    # TODO: what relation should we choose for Bridging?
                    # relation = f"{src_str.split('-')[0]}-{trg_str.split('-')[0]}"
                    relation = '_'
                    mention.bridging.append((trg_cluster, relation))
                del node.misc['Bridge']

            misc_split = node.misc['Split']
            if misc_split:
                # E.g. Entity=(person-54)|Split=person-4<person-54,person-9<person-54
                src_str = entity2cluster_id(misc_split.split('<')[-1])
                ante_clusters = []
                for x in misc_split.split(','):
                    ante_str, this_str = (entity2cluster_id(y) for y in x.split('<'))
                    if this_str != src_str:
                        logging.warning(f'{node} invalid Split: {this_str} != {src_str}')
                        # There are just three such cases in GUM and all are bugs,
                        # so let's ignore them entirely (the `else` clause will be skipped if exiting `for` w/ `break`).
                        break
                    ante_clusters.append(clusters[ante_str])
                else:
                    clusters[src_str].split_ante = ante_clusters
                del node.misc['Split']

        for cluster_name, mentions in unfinished_mentions.items():
            for mention in mentions:
                logging.warning(f"Mention {name} opened at {mention.head}, but not closed in the same tree. Deleting.")
                cluster = mention.cluster
                mention.words = []
                cluster._mentions.remove(mention)
                if not cluster._mentions:
                    del clusters[name]
