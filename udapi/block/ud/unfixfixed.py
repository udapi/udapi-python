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
        'a duras penas',
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

    adp_noun_adp = [
        'a base de',
        'a bordo de',
        'a caballo entre',
        'a cambio de',
        'a cargo de',
        'a causa de',
        'a comienzos de',
        'a condición de',
        'a consecuencia de',
        'a consecuencias de',
        'a costa de',
        'a cuenta de',
        'a diferencia de',
        'a efectos de',
        'a excepción de',
        'a expensas de',
        'a falta de',
        'a favor de',
        'a final de',
        'a finales de',
        'a fin de',
        'a fines de',
        'a golpe de',
        'a instancias de',
        'a juicio de',
        'a manos de',
        'a mediados de',
        'a medida que',
        'a merced de',
        'a mitad de',
        'a modo de',
        'a nombre de',
        'a petición de',
        'a principio de',
        'a principios de',
        'a propósito de',
        'a prueba de',
        'a punto de',
        'a raíz de',
        'a razón de',
        'a sabiendas de',
        'a tenor de',
        'a través de',
        'con carácter de',
        'con miras a',
        'con motivo de',
        'con objeto de',
        'con ocasión de',
        'con respecto a',
        'con tal de',
        'con vistas a',
        'de acuerdo a',
        'de acuerdo en',
        'de cara a',
        'de forma que',
        'de manera de',
        'de manera que',
        'de manos de',
        'de mediados de',
        'de modo que',
        'de parte de',
        'de principios de',
        'en alusión a',
        'en aras de',
        'en atención a',
        'en ausencia de',
        'en base a',
        'en busca de',
        'en búsqueda de',
        'en calidad de',
        'en caso de',
        'en colaboración con',
        'en compañía de',
        'en comparación con',
        'en comunión con',
        'en concepto de',
        'en condiciones de',
        'en conformidad con',
        'en contra de',
        'en contraposición a',
        'en cuestión de',
        'en desacuerdo con',
        'en detrimento de',
        'en dirección a',
        'en espera de',
        'en favor de',
        'en forma de',
        'en función de',
        'en lugar de',
        'en manos de',
        'en materia de',
        'en medio de',
        'en memoria de',
        'en mitad de',
        'en nombre de',
        'en opinión de',
        'en parte por',
        'en poder de',
        'en pos de',
        'en presencia de',
        'en previsión de',
        'en pro de',
        'en recuerdo de',
        'en referencia a',
        'en relación a',
        'en relación con',
        'en representación de',
        'en señal de',
        'en solidaridad con',
        'en sustitución de',
        'en torno a',
        'en vez de',
        'en vías de',
        'en virtud de',
        'en vista de',
        'por boca de',
        'por cuenta de',
        'por efecto de',
        'por espacio de',
        'por falta de',
        'por medio de',
        'por motivo de',
        'por parte de',
        # Catalan
        "a banda d'",
        'a banda de',
        'a base de',
        "a canvi d'",
        'a canvi de',
        'a canvi que',
        "a càrrec d'",
        'a càrrec de',
        "a causa d'",
        'a causa de',
        'a causa que',
        "a conseqüència d'",
        'a conseqüència de',
        'a cop de',
        "a costa d'",
        'a costa de',
        "a diferència d'",
        'a diferència de',
        'a excepció de',
        "a falta d'",
        'a falta de',
        'a favor de',
        "a fi d'",
        'a fi de',
        'a finals de',
        'a fi que',
        'a iniciativa de',
        'a instàncies de',
        'a mans de',
        'amb independència de',
        "amb motiu d'",
        'amb motiu de',
        'a mercè de',
        'a mesura que',
        'a mitjan de',
        'a mitjans de',
        "a part d'",
        'a part de',
        "a petició d'",
        'a petició de',
        'a primers de',
        'a propòsit de',
        'a proposta de',
        "a punt d'",
        'a punt de',
        "a raó d'",
        'a raó de',
        'a suggeriment de',
        'a tall de',
        "a través d'",
        'a través d',
        'a través de',
        'de cara a',
        'de forma que',
        'de mans de',
        'en al·lusió a',
        'en atenció a',
        'en base a',
        "en cas d'",
        'en cas de',
        'en cas que',
        'en col·laboració amb',
        "en companyia d'",
        'en companyia de',
        'en comparació a',
        "en comptes d'",
        'en comptes de',
        "en concepte d'",
        'en concepte de',
        'en confluència amb',
        'en consonància amb',
        'en contacte amb',
        'en contra de',
        'en coordinació amb',
        'en detriment de',
        'en direcció a',
        'en favor de',
        "en funció d'",
        'en funció de',
        'en honor de',
        "en lloc d'",
        'en lloc de',
        "en mans d'",
        'en mans de',
        "en matèria d'",
        'en matèria de',
        'en memòria de',
        'en motiu de',
        "en nom d'",
        'en nom de',
        'en ocasió de',
        'en pro de',
        "en qualitat d'",
        'en qüestió de',
        'en referència a',
        'en relació a',
        'en relació amb',
        'en resposta a',
        'en solidaritat amb',
        "en virtut d'",
        'en virtut de',
        'en vista de',
        'pels voltants de',
        "pels volts d'",
        'pels volts de',
        'per boca de',
        "per causa d'",
        'per compte de',
        "per culpa d'",
        'per culpa de',
        "per mitjà d'",
        'per mitjà de',
        'per molt que',
        'per obra de',
        "per part d'",
        'per part de',
        'per sota de'
    ]

    def is_adp_noun_adp(self, node, fixed_children):
        """
        Current node is the preposition, the rest are its fixed children.
        """
        if len(fixed_children) != 2:
            return False
        for ana in self.adp_noun_adp:
            # It would be more efficient to precompute this but this block will
            # be used for one-time cleanup, so I don't care so much.
            (adp1, noun, adp2) = ana.split(' ', maxsplit=3)
            if node.lemma == adp1 and fixed_children[0].form.lower() == noun and fixed_children[1].form.lower() == adp2:
                return True
        return False

    adp_det_noun_adp = [
        'a el abrigo de',
        'a el borde de',
        'a el cabo de',
        'a el comienzo de',
        'a el contrario de',
        'a el filo de',
        'a el final de',
        'a el inicio de',
        'a el lado de',
        'a el límite de',
        'a el margen de',
        'a el objeto de',
        'a el parecer de',
        'a el respecto de',
        'a el servicio de',
        'a el término de',
        'a el tiempo que',
        'a la espera de',
        'a la hora de',
        'a la mitad de',
        'a la par que',
        'a la vez que',
        'a la vista de',
        'a la vuelta de',
        'a lo largo de',
        'con el fin de',
        'con el objetivo de',
        'con el objeto de',
        'con el propósito de',
        'con la condición de',
        'en el caso de',
        'en el puesto de',
        'en la línea de',
        'en la medida en',
        'en la medida que',
        'en lo concerniente a',
        # Catalan
        'a el marge de',
        'a la vegada que',
        'a la vora de',
        "a l' entorn de",
        "a l' hora d'",
        "a l' hora de",
        "a l' ombra d'",
        "amb el propòsit d'",
        "amb la col·laboració de",
        'amb la finalitat de',
        "amb la intenció d'",
        'amb la intenció de',
        "amb l' objecte de",
        "amb l' objectiu d'",
        "amb l' objectiu de",
        'de la mà de',
        'en el camp de',
        'en el cas de',
        'en el cas que',
        "en el marc d'",
        'en el marc de',
        "en l' àmbit de",
        'en la mesura que'
    ]

    def is_adp_det_noun_adp(self, node, fixed_children):
        """
        Current node is the preposition, the rest are its fixed children.
        """
        if len(fixed_children) != 3:
            return False
        for adna in self.adp_det_noun_adp:
            # It would be more efficient to precompute this but this block will
            # be used for one-time cleanup, so I don't care so much.
            (adp1, det, noun, adp2) = adna.split(' ', maxsplit=4)
            if node.lemma == adp1 and fixed_children[0].form.lower() == det and fixed_children[1].form.lower() == noun and fixed_children[2].form.lower() == adp2:
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
            elif self.is_adp_noun_adp(node, fixed_children) and node.parent.ord > node.ord:
                parent = node.parent.parent
                if parent:
                    deprel = node.parent.deprel
                    adp1 = node
                    noun1 = fixed_children[0]
                    adp2 = fixed_children[1]
                    noun2 = node.parent
                    self.reattach(noun1, parent, deprel)
                    self.reattach(adp1, noun1, 'case')
                    self.reattach(noun2, noun1, 'acl' if adp2.lemma == 'que' or noun2.upos == 'VERB' else 'nmod')
                    self.reattach(adp2, noun2, 'mark' if adp2.lemma == 'que' or noun2.upos == 'VERB' else 'case')
                    node.feats['ExtPos'] = ''
            elif self.is_adp_det_noun_adp(node, fixed_children) and node.parent.ord > node.ord:
                parent = node.parent.parent
                if parent:
                    deprel = node.parent.deprel
                    adp1 = node
                    det = fixed_children[0]
                    noun1 = fixed_children[1]
                    adp2 = fixed_children[2]
                    noun2 = node.parent
                    self.reattach(noun1, parent, deprel)
                    self.reattach(adp1, noun1, 'case')
                    self.reattach(det, noun1, 'det')
                    self.reattach(noun2, noun1, 'acl' if adp2.lemma == 'que' or noun2.upos == 'VERB' else 'nmod')
                    self.reattach(adp2, noun2, 'mark' if adp2.lemma == 'que' or noun2.upos == 'VERB' else 'case')
                    node.feats['ExtPos'] = ''
