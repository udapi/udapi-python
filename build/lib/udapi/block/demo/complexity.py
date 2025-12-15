"""demo.Complexity prints statistics on syntactic complexity.
"""
from udapi.core.basewriter import BaseWriter
from collections import deque


def non_punct(nodes):
    return [n for n in nodes if n.upos != 'PUNCT']


def is_np(node):
    return node.upos in ("NOUN", "PROPN") or (node.upos == "PRON" and node.feats["PronType"] == "Prs" and not node.feats["Poss"])


def is_vp(node):
    """E.g. prosili, naléhali a žadonili => 1 coordinated verb phrase, head “prosili”.

    [POS == “VERB”, [deprel == “conj”, POS == “VERB”]], unique coordination heads
    TODO: zahrnout i non-VERB?
    - vznikla a byla přijata(conj,ADJ,parent=vznikla)
    - je(cop,AUX) nešťastný(ADJ) a nechá(conj,VERB,parent=nešťastný) se nalákat
    - "podařilo se to a dokladem(ClauseHead,NOUN,conj,parent=podařilo) je(cop,AUX,parent=dokladem)"
    - omezit se jen na (či využít) ClauseHead, nebo zahrnout i non-finite verbs (koordinace infinitivů či příčestí)?
    "stihl(ClauseHead) napsat(VerbForm=Inf) a publikovat(VerbForm=Inf)" ... napsat ani publikovat nejsou ClauseHead
    "rozhodl se ukončit a ukazuje(ClauseHead,parent=ukončit)" správně by mělo být parent=rozhodl, ale parser dělá chyby.
    - Parsing vůbec dělá mnoho chyb v koordinacích, takže je vhodné podmínky velmi omezit.
    """
    return node.upos == "VERB" or node.misc["ClauseHead"]


def is_relcl(node):
    """Is a given node a head of a relative clause?

    Unfortunatelly, UDPipe 2.4 produces just acl instead of acl:relcl.
    """
    if node.deprel == 'acl:relcl':
        return True
    return node.udeprel == 'acl' and any('Rel' in c.feats['PronType'] for c in node.children)


def is_postponed_nom_mod(node):
    """Is a given node a postponed nominal modifier?

    Silvie: [(POS in {“NOUN”, “PROPN”} | POS == “PRON” & feats:PronType == “Prs” & !(feats:Poss==”Yes”)), child with higher word order than parent
    [deprel != “conj”, POS in {“NOUN”, “PROPN”} | POS == “PRON” & feats:PronType == “Prs” & !(feats:Poss==”Yes”)]

    TODO: Tohle hledá v češtině zcela běžné jevy jako "vznik díla". Nechceme hledat něco jiného?
    """
    return node.udeprel != 'conj' and is_np(node) and node.parent.precedes(node) and is_np(node.parent)


def is_postponed_adj_mod(node):
    # TODO můžeme rozlišovat holý přívlastek ("písní ruských") a rozvitý ("milenec známý z pozdějšího zpracování")
    return node.parent.precedes(node) and is_np(node.parent) and node.upos == 'ADJ' #and not node.children


def is_complex_nominal(node):
    """[(POS in {“NOUN”, “PROPN”} | POS == “PRON” & feats:PronType == “Prs” & !(feats:Poss==”Yes”)) 2x descendant [deprel != “conj”]]
    TODO: punct, case, cc a dep taky ignorovat?
    TODO: opravdu descendants a ne children? (descendants snadno roste nad všechny meze, je-li tam třeba vedlejší věta)
    TODO: beztak bude chtít odfiltrovat copuly: "Jádrem tvorby jsou sbírky." - Jádrem má 3 děti.
    TODO: a nezvýšit ten limit z 2x aspoň na 3x?
    """
    return is_np(node) and len([n for n in node.descendants if n.deprel not in ('conj', 'punct', 'case', 'cc', 'dep', 'cop')]) > 1


def is_finite_clause_head(node):
    """Is a given node a head of a finite clause?

    Silvie: [(POS == „VERB“ & feats:Verbform == „Fin“ | Verbform == „Part“} ) ] OR [(POS in {„ADJ“, „NOUN“, „PROPN“}, [child POS ==  „AUX“)]]
    - POS == „VERB“ je zbytečné, protože VerbForm=Part je nastaveno i u ADJ ("je nucen" apod.)
    - child POS == „AUX“ zase matchuje i např. na "Vidím psa(NOUN), který je(AUX,acl,parent=psa) z dávné doby."
    - adjectivized predicates (převažující(VerbForm=Part) básně) by neměly být určeny jako clause_head

    * Most finite verbs with deprel=amod are parsing errors - they should have deprel=acl,
      but for better robustness we include these as well.
    * Similarly "dep" and "orphan" are mostly parsing errors.
    * TODO: by uncommenting the nsubj/csubj line, we find few more real clause heads, but also some false positives.
    """
    # TODO appos
    if ((node.udeprel in {'root', 'conj', 'acl', 'advcl', 'ccomp', 'csubj', 'obl', 'parataxis', 'amod', 'dep', 'orphan'}
         and is_finite_verb(node))
            #or any(c.udeprel in {'nsubj', 'csubj'} for c in node.children)
            or (any(c.udeprel == 'cop' for c in node.children) and node.udeprel != 'xcomp')):
        return True
    xcomp_child = next((c for c in node.children if c.udeprel == 'xcomp'), None)
    return xcomp_child and any(c.udeprel == 'cop' for c in xcomp_child.children)


# TODO: zahrnout i: bude(aux,AUX,parent=chovat) se chovat(VERB,VerbForm=Inf)
def is_finite_verb(node):
    return (node.feats['VerbForm'] in {'Fin', 'Part'} and
            (node.upos == 'VERB' or
             node.upos == 'ADJ' and any(c.deprel == 'aux:pass' for c in node.children)))


def is_adjectivized_predicate(node):
    """E.g. kouřící komín, zbitý kluk

    Silvie: [(POS == „ADJ“ & feats:VerbForm == „Part“), parent [POS in {„NOUN“, „PROPN“}] ]
    - parent [POS in {„NOUN“, „PROPN“}] zamezí případům jako
     "kvůli nesmyslné a stupňující(parent=nesmyslné,deprel=conj) se žárlivosti"
     "Nové pronikající(parent=Nové,deprel=amod) socialistické myšlení" asi chyba parsingu, mělo být parent=myšlení?
    - dotaz naopak matchuje na "způsob, jakým jsou popsány", proto přidávám podmínku not node.misc["ClauseHead"]
    """
    return (node.feats["VerbForm"] == "Part"
        and node.upos == "ADJ"
        and (node.parent.upos in {"NOUN","PROPN"} or (node.udeprel == "conj" and node.parent.upos == "ADJ"))
        and not node.misc["ClauseHead"])


def is_controlled_predicate(node):
    """E.g. Mohli jsme odejít i zůstat.

    TODO: Chceme zahrnout i druhý a další člen koordinace, např. "stihl napsat a publikovat",
    tedy node.udeprel == "conj" and node.parent.udeprel == "xcomp"?
    """
    return node.deprel == "xcomp"

class Complexity(BaseWriter):

    def __init__(self, matches=False, **kwargs):
        super().__init__(**kwargs)
        self.matches = matches


    def report(self, category, groups, expand_type='no'):
        if self.matches:
            for group in groups:
                self.print_match(category, group, expand_type)
        else:
            print("\t" + str(len(groups)), end='')


    def expand_subtree(self, nodes, expand_type):
        if expand_type == 'no':
            return nodes
        if len(nodes) > 1:
            raise Exception("expanding more than one node not implemented yet")
        if expand_type == 'subtree':
            return nodes[0].descendants(add_self=True)
        #if expand_type == 'subtree_except_conj':
            #result = nodes
            #for child in group.children:
                #if child.udeprel != 'conj':
                    #result.extend(child.descendants(add_self=True))
            #return = sorted(result)
        if expand_type == 'subtree_within_clause':
            stack = [n for n in nodes[0].children if n.udeprel != 'conj']
            while stack:
                node = stack.pop()
                if not node.misc["ClauseHead"]:
                    nodes.append(node)
                    stack.extend(node.children())
            return sorted(nodes)
        raise ValueError("unknown expand value " + expand_type)


    def print_match(self, category, group, expand_type='no'):
        nodes = self.expand_subtree(group, expand_type)
        lemmas = " ".join(n.lemma for n in nodes)
        tags = " ".join(n.upos for n in nodes)
        n_tokens = str(len(non_punct(nodes)))
        print("\t".join([category, nodes[0].root.sent_id, lemmas, tags, n_tokens]))


    def get_main_clauses(self, root):
        main_heads = []
        for main_head in root.children:
            main_heads.append(main_head)
            main_heads.extend(n for n in main_head.children if n.udeprel == 'conj')
        return [[n] for n in main_heads]


    def get_coord_phrase(self, root, phrase_type_function):
        results = []
        for node in root.descendants:
            if phrase_type_function(node):
                conjuncts = [n for n in node.children if n.udeprel == 'conj' and phrase_type_function(n)]
                if conjuncts:
                    conjunctions = []
                    for conj in conjuncts:
                        # TODO multiword conjunctions (udeprel=flat)?
                        conjunctions.extend([n for n in conj.children if n.udeprel == 'cc'])
                    results.append(sorted([node] + conjuncts + conjunctions))
        return results

    # TODO koordinace hlavních i vedlejších vět
    def get_t_units(self, main_heads):
        results = []
        for main_head in main_heads:
            main_clause = [main_head]
            dep_heads = []
            stack = main_head.children
            while stack:
                node = stack.pop()
                if node.misc["ClauseHead"]:
                    dep_heads.append(node)
                else:
                    main_clause.append(node)
                    stack.extend(node.children)
            main_clause = sorted(main_clause)

            for dep_clause_head in dep_heads:
                results.append(main_clause + self.expand_subtree([dep_clause_head], 'subtree'))
        return results

    # TODO complex t-unit má jinou definici: 3 klauze
    def get_complex_t_units(self, root):
        results = []
        for node in root.descendants:
            if node.deprel != 'root' and node.misc["ClauseHead"]: # TODO: exclude the main clause?
                results += self.get_t_units([node])
        return results


    def process_tree(self, root):
        print("# " + root.text)

        allnodes = root.descendants
        depth, clause_depth = {0: 0}, {0: 0}
        queue = deque(root.children)
        clause_heads = []
        while queue:
            node = queue.popleft()
            depth[node.ord] = depth[node.parent.ord] + 1
            clause_depth[node.ord] = clause_depth[node.parent.ord]
            if is_finite_clause_head(node):
                node.misc['ClauseHead'] = 1
                clause_heads.append(node)
                clause_depth[node.ord] += 1
            queue.extend(node.children)
        max_depth = sorted(depth.values())[-1]
        max_clause_depth = sorted(clause_depth.values())[-1]

        t_units = self.get_t_units([n for n in root.children if n.deprel == 'root'])
        total_t_units_length = sum(len(t_unit) for t_unit in t_units)
        mean_t_unit_length = total_t_units_length / (len(t_units) or 1) # TODO co reportovat, když věta nemá žádné t-units?

        if not self.matches:
            print("\t".join(str(x) for x in [root.sent_id, len(non_punct(allnodes)), max_depth, max_clause_depth, mean_t_unit_length]), end='')

        self.report("clauses", [[n] for n in clause_heads], 'subtree')
        self.report("adjectivized_predicates", [[n] for n in allnodes if is_adjectivized_predicate(n)])
        self.report("controlled_predicates", [[n] for n in allnodes if is_controlled_predicate(n)])
        self.report("main_clauses", self.get_main_clauses(root), 'subtree_within_clause')
        self.report("coordinated_verb_phrases", self.get_coord_phrase(root, is_vp))
        self.report("coordinated_noun_phrases", self.get_coord_phrase(root, is_np))
        self.report("coordinated_adjective_phrases", self.get_coord_phrase(root, lambda n: n.upos in ("ADJ", "DET")))
        self.report("coordinated_adverb_phrases", self.get_coord_phrase(root, lambda n: n.upos == "ADV"))
        self.report("t-units", t_units)
        self.report("complex_t-units", self.get_complex_t_units(root))
        # TODO: najde "básně a písně" a "rychtář a rychtářka" UDPipe kdovíproč určil jako ADV a ADV. Zkontrolovat, máme-li nejlepší možný UDPipe model.
        self.report("relative_clauses", [[n] for n in allnodes if is_relcl(n)], 'subtree_within_clause')
        self.report("postponed_nominal_modifiers", [[n] for n in allnodes if is_postponed_nom_mod(n)])
        self.report("postponed_adjective_modifiers", [[n] for n in allnodes if is_postponed_adj_mod(n)])
        self.report("complex_nominals", [[n] for n in allnodes if is_complex_nominal(n)])

        if not self.matches:
            # TODO: pro total koordinace asi nemá smysl reportovat matches, jen total count?
            self.report("coordinated_phrases_total", self.get_coord_phrase(root, lambda _: True))

            nonpunct_upos = [n.upos for n in non_punct(allnodes)] + ['NONE', 'NONE']
            brackets = str(len([n for n in allnodes if n.form == '(']))
            dashes = str(len([n for n in allnodes if n.form in '-–—―'])) # hyphen, en-dash, em-dash, horizonatal bar
            colons = str(len([n for n in allnodes if n.form == ':']))
            semicolons = str(len([n for n in allnodes if n.form == ';']))
            print("\t", "\t".join([nonpunct_upos[0], nonpunct_upos[1], brackets, dashes, colons, semicolons]))
