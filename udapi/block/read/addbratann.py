"""Add Brat coreference annotation from *.ann files.

So far, tested on French LitBank data only.

T12	HIST 362 366	qui
T13	HIST 349 362	une aventure
R1431	Coreference Arg1:T12 Arg2:T13

"""

from udapi.core.block import Block
from udapi.core.files import Files
import logging
from bisect import bisect_left
import networkx as nx

def _m(range_s, range_e, offset):
    return f"{range_s}-{offset}:{range_e}-{offset}" if offset else f"{range_s}:{range_e}"

class AddBratAnn(Block):

    def __init__(self, files,  zone='', offset=0, detect_bom=True, keep_mention_id=True,
                 coref_attr="R", no_type_value='_Unsorted_',
                 **kwargs):
        """Args:
        files: file names with the coreference annotations (*.ann)
        offset: what number to substract from the chatacter indices in the ann files
        detect_bom: if True and the current txt file starts with BOM (byte-order mark), add 1 to the offset
        """
        super().__init__(**kwargs)
        self.zone = zone
        self.files = Files(filenames=files)
        self.offset = offset
        self.detect_bom = detect_bom
        self.keep_mention_id = keep_mention_id
        self.coref_attr = coref_attr
        self.no_type_value = no_type_value

    def process_document(self, document):

        # Read all the important info from the *.ann file.
        mentions, attrs, split_ante, clusters = {}, [], [], []
        ann_filehandle = self.files.next_filehandle()
        offset = self.offset
        if self.detect_bom:
            txt_filename = self.files.filename.replace("ann", "txt")
            with open(txt_filename, 'rb') as txt_fh:
                raw_bytes = txt_fh.read(3)
                if raw_bytes == b'\xef\xbb\xbf':
                    offset += 1

        for line in ann_filehandle:
            line = line.rstrip('\n')
            if not "\t" in line:
                logging.warning(f"Unexpected line without tabs: {line}")
            elif line.startswith("T"):
                # T13	HIST 349 362	une aventure
                try:
                    mention_id, type_and_range, form = line.split("\t")
                    # Usually range are two numbers, but can be more, e.g. type_and_range="Abstract  605 653;654 703"
                    # Let's take the first and last number only.´
                    parts = type_and_range.split()
                    ne_type, range_s, range_e = parts[0], int(parts[1]), int(parts[-1])

                    # If form ends with spaces, remove them and adjust range_e
                    stripped_form = form.rstrip(" ")
                    if form != stripped_form:
                        num_spaces = len(form) - len(stripped_form)
                        logging.debug(f"Stripping {num_spaces} space{'s' if num_spaces>1 else ''} from {mention_id} '{form}' ({_m(range_s,range_e,offset)}->{range_e-num_spaces})")
                        form = stripped_form
                        range_e = range_e - num_spaces


                    mentions[mention_id] = [ne_type, range_s, range_e, form]
                    if self.keep_mention_id:
                        attrs.append(["mention_id", mention_id, mention_id])
                except Exception as e:
                    logging.warning(f"Unexpected mention line: {line}\n{e}")
            elif line.startswith(self.coref_attr):
                cor_attr, mention_ids = line.split("\t")
                parts = mention_ids.split()
                assert(parts[0] == "Coreference")
                clusters.append([p.split(":")[1] for p in parts[1:]])
            elif line.startswith("#"):
                pass # Let's ignore annotators' comments
            else:
                logging.warning(f"Unexpected line in {self.files.filename}:\n{line}")

        # Some Brat ann files use link-based representation, e.g.
        # R123	Coreference Arg1:T11 Arg2:T13
        # R124	Coreference Arg1:T12 Arg2:T14
        # R125	Coreference Arg1:T13 Arg2:T14
        # This actually means that all four mentions T11, T12, T13 and T14 are in the same cluster (entity).
        # However, clusters = [["T11", "T13"], ["T12", "T14"], ["T13", "T14"]]
        # and we need to convert it to clusters = [["T11", "T12", "T13", "T14"]]
        # Note that if creating entities for link, in their original order,
        # R123 and R125 would result in creating two entities and when hitting R125
        # we would need to merge them, i.e. delete one of them and move their mentions to the other.
        # This is the solution of corefud.Link2Cluster, but here it seems easier to find connected components.
        coref_graph = nx.Graph()
        for mention_ids in clusters:
            coref_graph.add_node(mention_ids[0])
            for mention_id in mention_ids[1:]:
                coref_graph.add_node(mention_id)
                coref_graph.add_edge(mention_id, mention_ids[0])
        clusters = [list(component) for component in nx.connected_components(coref_graph)]

        # Create entity objects for non-singletons.
        entity_map = {}
        for mention_ids in clusters:
            etype, etype_index = None, 0
            for index, m_id in enumerate(mention_ids):
                if mentions[m_id][0] == self.no_type_value:
                    pass
                elif etype is None:
                    etype, etype_index = mentions[m_id][0], index
                elif etype != mentions[m_id][0]:
                    logging.warning(f"Mention type mismatch {mention_ids[etype_index]}:{etype} != {m_id}:{mentions[m_id][0]}. Using the former.")
            if etype is None:
                etype = "other"
            entity = document.create_coref_entity(etype=etype)
            for m_id in mention_ids:
                if m_id in entity_map:
                    logging.warning(f"Mention {m_id} already in Entity {entity_map[m_id].eid}, not adding to {entity.eid}")
                else:
                    entity_map[m_id] = entity

        # Collect TokenRange (as pre-filled by UDPipe) for each token.
        tokens, starts, ends = [], [], []
        for tree in document.trees:
            for token in tree.token_descendants:
                tokens.append(token)
                range_s, range_e = token.misc["TokenRange"].split(":")
                starts.append(int(range_s))
                ends.append(int(range_e))

        # Create mention objects.
        mention_map = {}
        for mention_id, mention_values in mentions.items():

            # Find Udapi tokens for each mention.
            ne_type, range_s, range_e, form = mention_values
            index_s = bisect_left(starts, range_s - offset)
            if starts[index_s] != range_s - offset and index_s > 0:
                index_s -= 1
            index_e = bisect_left(ends, range_e - offset)
            mtokens = tokens[index_s : index_e+1]
            token_s, token_e = tokens[index_s], tokens[index_e]

            # Solve cases when the character range crosses Udapi (UDPipe-predicted) token boundaries.
            # If the start token is a multi-word token (MWT),
            # we can still try to find the proper word within the MWT.
            ok_s, ok_e = True, True
            if starts[index_s] != range_s - offset:
                ok_s = False
                if token_s.is_mwt():
                    mtokens.pop(0)
                    first_form = form.split()[0]
                    new_start = ends[index_s]
                    for w in reversed(token_s.words):
                        mtokens = [w] + mtokens
                        new_start -= len(w.form)
                        if w.form == first_form or new_start < range_s - offset:
                            ok_s = True
                            break

            # similarly for the end token
            if ends[index_e] != range_e - offset:
                ok_e = False
                if token_e.is_mwt():
                    mtokens.pop()
                    last_form = form.split()[-1]
                    new_end = starts[index_e]
                    for w in token_e.words:
                        mtokens.append(w)
                        new_end += len(w.form)
                        if w.form == last_form or new_end > range_e - offset:
                            ok_e = True
                            break

            if not ok_s or not ok_e:
                logging.warning(f"Mention {mention_id} range {_m(range_s, range_e, offset)} ({form})"
                                f" crosses token boundaries: {token_s.misc} ({token_s.form}) "
                                f".. {token_e.misc} ({token_e.form})")

            # Project tokens (including MWTs) to words and check forms match.
            words, udapi_form = [], ""
            for token in mtokens:
                words += token.words
                udapi_form += token.form
                if not token.no_space_after:
                    udapi_form += " "
            udapi_form = udapi_form.rstrip()
            if form != udapi_form:
                logging.warning(f"Mention {mention_id}: ann form '{form}' != Udapi form '{udapi_form}'")

            # Make sure all words of the mention are in the same sentence.
            root = words[0].root
            mwords = [words[0]]
            for word in words[1:]:
                if word.root is root:
                    mwords.append(word)
                else:
                    logging.warning(f"Cross-sentence mention. Word {word} not in {root}, thus omitting from the mention.")

            # Create entities for singletons
            if mention_id not in entity_map:
                entity_map[mention_id] = document.create_coref_entity(etype=ne_type)

            # Create the Udapi mention object
            mention = entity_map[mention_id].create_mention(words=mwords)
            mention_map[mention_id] = mention

        # Fill-in the additional mention attributes.
        for attr_name, mention_id, attr_value in attrs:
            if mention_id in mention_map:
                mention_map[mention_id].other[attr_name] = attr_value

        # Fill-in split antecedents
        for arg1, arg2 in split_ante:
            if arg1 in entity_map and arg2 in entity_map:
                if entity_map[arg1] in entity_map[arg2].split_ante:
                    logging.warning(f"Repeated SplitAnte: {arg1=} ({entity_map[arg1].eid}) {arg2=} ({entity_map[arg2].eid})")
                else:
                    entity_map[arg2].split_ante.append(entity_map[arg1])
            else:
                logging.warning(f"{arg1} or {arg2} not indexed in entity_map")
