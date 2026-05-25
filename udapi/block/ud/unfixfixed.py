"""
Block UnfixFixed restructures selected fixed expressions. Currently focuses
on Spanish and Catalan AnCora, and Spanish GSD.

Author: Dan Zeman
"""
from udapi.core.block import Block

class UnfixFixed(Block):
    """
    Looks for selected fixed multiword expressions and transforms them to
    a consistent annotation (typically avoiding the fixed relation).
    """

    verb_adp = [
        'acabar de',
        'acostumbrar a',
        'cesar de',
        'comenzar a',
        'decidir a',
        'dedicar a',
        'dejar de',
        'empezar a',
        'entrar a',
        'haber que',
        'ir a',
        'llegar a',
        'pasar a',
        'tener que',
        'venir a',
        'volver a'
    ]

    def is_verb_adp(self, node, fixed_children):
        """
        Current node is the verb, its fixed child is the preposition.
        """
        if len(fixed_children) != 1:
            return False
        for va in self.verb_adp:
            # It would be more efficient to precompute this but this block will
            # be used for one-time cleanup, so I don't care so much.
            (verb, adp) = va.split(' ', maxsplit=2)
            if node.lemma == verb and fixed_children[0].lemma == adp:
                return True
        return False

    adp_noun = [
        'a bofetadas',
        'a borbotones',
        'a caballo',
        'a cambio',
        'a centenares',
        'a ciegas',
        'a conciencia',
        'a continuación',
        'a contrapié',
        'a dedo',
        'a diario',
        'a distancia',
        'a domicilio',
        'a flote',
        'a fondo',
        'a granel',
        'a gritos',
        'a gusto',
        'a mano',
        'a medias',
        'a pie',
        'a propósito',
        'a prueba',
        'a pulso',
        'a punto',
        'a sabiendas',
        'a salvo',
        'a secas',
        'a solas',
        'a tiempo',
        'a tiros',
        'a tope',
        'a ultranza',
        'con frecuencia',
        'de acuerdo',
        'de antemano',
        'de arrastre',
        'de bruces',
        'de calle',
        'de costumbre',
        'de espaldas',
        'de facto',
        'de fondo',
        'de frente',
        'de guardia',
        'de hecho',
        'de churro',
        'de inmediato',
        'de lado',
        'de largo',
        'de lleno',
        'de moda',
        'de momento',
        'de oficio',
        'de paso',
        'de pega',
        'de pie',
        'de plano',
        'de pronto',
        'de recibo',
        'de repente',
        'de rodillas',
        'de seguro',
        'de sobra',
        'de sobras',
        'de súbito',
        'de veras',
        'de verdad',
        'de vuelta',
        'en alza',
        'en armas',
        'en broma',
        'en cabeza',
        'en cambio',
        'en candelero',
        'en condiciones',
        'en consecuencia',
        'en diagonal',
        'en diferido',
        'en efectivo',
        'en efecto',
        'en entredicho',
        'en esencia',
        'en evidencia',
        'en exclusiva',
        'en falso',
        'en fin',
        'en forma',
        'en línea',
        'en marcha',
        'en masa',
        'en parte',
        'en pedazos',
        'en picado',
        'en plantilla',
        'en principio',
        'en privado',
        'en profundidad',
        'en público',
        'en realidad',
        'en regla',
        'en retirada',
        'en seco',
        'en secreto',
        'en seguida',
        'en serio',
        'en silencio',
        'en solitario',
        'en suspenso',
        'en teoría',
        'en tromba',
        'en vano',
        'en vilo',
        'en vivo',
        'en zigzag',
        'in extremis',
        'para colmo',
        'per cápita',
        'por añadidura',
        'por casualidad',
        'por completo',
        'por desgracia',
        'por ejemplo',
        'por ende',
        'por favor',
        'por fin',
        'por fortuna',
        'por separado',
        'por sorpresa',
        'por supuesto',
        'por unanimidad',
        'sin duda',
        # Catalan
        'a bord',
        'a cappella',
        'a cavall',
        'a continuació',
        'a favor',
        'a fons',
        'a granel',
        'a part',
        'a penes',
        'a peu',
        'a punt',
        'a soles',
        'a ull',
        'a ultrança',
        'a vegades',
        'contra natura',
        "d' acord",
        'de bracet',
        'de butxaca',
        'de cop',
        'de debò',
        'de fet',
        'de genolls',
        'de llarg',
        'de moment',
        "d' entrada",
        "d' època",
        'de seguida',
        'de segur',
        'de sobres',
        'de sobte',
        'de vegades',
        'en acabat',
        'en breu',
        'en canvi',
        'en comú',
        'en comunitat',
        'en concret',
        'en consciència',
        'en contacte',
        'en contra',
        'en contrast',
        'en curs',
        'en curt',
        'en definitiva',
        'en dubte',
        'en efecte',
        'en efectiu',
        'en fals',
        'en general',
        'en massa',
        'en miniatura',
        'en paral·lel',
        'en part',
        'en particular',
        'en picat',
        'en positiu',
        'en principi',
        'en privat',
        'en realitat',
        'en solitari',
        'en suspens',
        'en teoria',
        'en vida',
        'en vigílies',
        'en vigor',
        'en viu',
        'per ara',
        'per cert',
        'per contra',
        'per exemple',
        'per favor',
        'per sota',
        'per unanimitat'
    ]

    def is_adp_noun(self, node, fixed_children):
        """
        Current node is the preposition, its fixed child is the noun.
        """
        if len(fixed_children) != 1:
            return False
        for an in self.adp_noun:
            # It would be more efficient to precompute this but this block will
            # be used for one-time cleanup, so I don't care so much.
            (adp, noun) = an.split(' ', maxsplit=2)
            if node.lemma == adp and fixed_children[0].form.lower() == noun:
                return True
        return False

    # The following are sometimes tagged ADP NOUN NOUN, sometimes ADP ADJ NOUN.
    # The latter is correct, although less frequent. In some cases, the ADJ
    # slot is in fact a DET: todo, toda, cualquier, una; tota, totes, una.
    adp_adj_noun = [
        'a buenas horas',
        'a buen seguro',
        'a corto plazo',
        'a largo plazo',
        'a medio plazo',
        'a primera vista',
        'a toda costa',
        'a toda prisa',
        'a todo pasto',
        'con toda normalidad',
        'de buena voluntad',
        'de buen grado',
        'de cualquier forma',
        'de igual modo',
        'de mala fe',
        'de mala manera',
        'de ninguna manera',
        'de nuevo cuño',
        'de otro lado',
        'de poca monta',
        'de puta madre',
        'de segunda mano',
        'de todas formas',
        'de todas maneras',
        'de todos modos',
        'de una vez',
        'en gran medida',
        'en gran parte',
        'por otra parte',
        'por otro lado',
        # Catalan
        'a grans trets',
        'amb prou feines',
        'de tota manera',
        'de totes maneres',
        "d' una banda",
        'en certa manera',
        'en gran mesura'
    ]

    def is_adp_adj_noun(self, node, fixed_children):
        """
        Current node is the preposition, its fixed children are the adjective
        and the noun.
        """
        if len(fixed_children) != 2:
            return False
        for aan in self.adp_adj_noun:
            # It would be more efficient to precompute this but this block will
            # be used for one-time cleanup, so I don't care so much.
            (adp, adj, noun) = aan.split(' ', maxsplit=3)
            if node.lemma == adp and fixed_children[0].form.lower() == adj and fixed_children[1].form.lower() == noun:
                return True
        return False

    # Similar to ADP ADJ NOUN, but here the adjective follows the noun.
    adp_noun_adj = [
        'a puerta cerrada',
        'a tiro limpio',
        'de capa caída',
        'en líneas generales',
        # Catalan
        'en línia recta',
        'pel cap baix'
    ]

    def is_adp_noun_adj(self, node, fixed_children):
        """
        Current node is the preposition, its fixed children are the adjective
        and the noun.
        """
        if len(fixed_children) != 2:
            return False
        for ana in self.adp_noun_adj:
            # It would be more efficient to precompute this but this block will
            # be used for one-time cleanup, so I don't care so much.
            (adp, noun, adj) = ana.split(' ', maxsplit=3)
            if node.lemma == adp and fixed_children[0].form.lower() == noun and fixed_children[1].form.lower() == adj:
                return True
        return False

    def reattach(self, child, parent, deprel):
        """
        Takes care of both basic and enhanced dependency, assuming that they
        are always identical (which is true for non-empty nodes in AnCora).
        """
        child.parent = parent
        child.deprel = deprel
        if child.deps:
            child.deps[0]['parent'] = parent
            child.deps[0]['deprel'] = deprel

    def process_node(self, node):
        fixed_children = [x for x in node.children if x.udeprel == 'fixed']
        if len(fixed_children) > 0:
            if self.is_verb_adp(node, fixed_children):
                # Does the verb have another verb as its dependent? If so,
                # reattach the preposition as mark of that other verb.
                verbs_right = [x for x in node.children if x.udeprel != 'fixed' and (x.upos == 'VERB' or x.udeprel == 'xcomp') and x.ord > node.ord]
                if len(verbs_right) > 0:
                    self.reattach(fixed_children[0], verbs_right[0], 'mark')
                else:
                    self.reattach(fixed_children[0], node, 'xcomp')
                node.feats['ExtPos'] = ''
            elif node.lemma == 'a' and node.udeprel == 'obj' and len(fixed_children) == 1:
                # Occasionally the annotator decided that an animate direct object with "a" must be fixed: "a barberos". That's wrong.
                self.reattach(fixed_children[0], node.parent, 'obj')
                self.reattach(node, fixed_children[0], 'case')
                node.feats['ExtPos'] = ''
            elif self.is_adp_noun(node, fixed_children):
                deprel = 'obl' if node.udeprel == 'advmod' else node.deprel
                if deprel == 'obl' and node.parent.upos in ['NOUN', 'PRON', 'PROPN'] and node.parent.udeprel in ['nsubj', 'obj', 'iobj', 'obl', 'vocative', 'dislocated', 'expl', 'nmod']:
                    deprel = 'nmod'
                self.reattach(fixed_children[0], node.parent, deprel)
                self.reattach(node, fixed_children[0], 'case')
                node.feats['ExtPos'] = ''
            elif self.is_adp_adj_noun(node, fixed_children):
                deprel = 'obl' if node.udeprel == 'advmod' else node.deprel
                if deprel == 'obl' and node.parent.upos in ['NOUN', 'PRON', 'PROPN'] and node.parent.udeprel in ['nsubj', 'obj', 'iobj', 'obl', 'vocative', 'dislocated', 'expl', 'nmod']:
                    deprel = 'nmod'
                self.reattach(fixed_children[1], node.parent, deprel)
                self.reattach(node, fixed_children[1], 'case')
                if fixed_children[0].form.lower() in ['todo', 'todos', 'toda', 'todas', 'ninguna', 'cualquier', 'una', 'tota', 'totes']:
                    fixed_children[0].upos = 'DET'
                    self.reattach(fixed_children[0], fixed_children[1], 'det')
                else:
                    fixed_children[0].upos = 'ADJ'
                    self.reattach(fixed_children[0], fixed_children[1], 'amod')
                node.feats['ExtPos'] = ''
            elif self.is_adp_noun_adj(node, fixed_children):
                deprel = 'obl' if node.udeprel == 'advmod' else node.deprel
                if deprel == 'obl' and node.parent.upos in ['NOUN', 'PRON', 'PROPN'] and node.parent.udeprel in ['nsubj', 'obj', 'iobj', 'obl', 'vocative', 'dislocated', 'expl', 'nmod']:
                    deprel = 'nmod'
                self.reattach(fixed_children[0], node.parent, deprel)
                self.reattach(node, fixed_children[0], 'case')
                fixed_children[1].upos = 'ADJ'
                self.reattach(fixed_children[1], fixed_children[0], 'amod')
                node.feats['ExtPos'] = ''
