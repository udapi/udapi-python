import udapi.block.msf.phrase
from enum import Enum

AUXES_HAVE = ['ter', 'haber', 'avere']
AUXES_BE = ['estar', 'essere']
MODALS = ['poder', 'deber', 'querer', 'saber', # Spanish + Portuguese
          'potere', 'dovere', 'volere', 'sapere'] # Italian

class Aspect(str, Enum):
    IMP = 'Imp'
    IMPPROG = 'ImpProg'
    PERF = 'Perf'
    PERFPROG = 'PerfProg'
    PROG = 'Prog'
    PQP = 'Pqp'

class Tense(str, Enum):
    FUT = 'Fut'
    FUTFUT = 'FutFut'
    PAST = 'Past'
    PASTFUT = 'PastFut'
    PASTPRES = 'PastPres'
    PRES = 'Pres'

class Romance(udapi.block.msf.phrase.Phrase):

    def process_node(self, node):

        cop = [x for x in node.children if x.udeprel == 'cop']
        
        # only expl or expl:pv, no expl:impers or expl:pass
        refl = [x for x in node.children if x.lemma == 'se' and x.upos == 'PRON' and x.udeprel == 'expl' and x.deprel != 'expl:impers' and x.deprel != 'expl:pass']
        
        if refl:
            expl='Pv'
        else:
            expl=None
   
        if cop:
            # find auxiliary verbs, modal verbs, and auxiliary verbs related to modal verbs among the children of the content verb and separate them from each other 
            auxes, modals, modal_auxes = self.find_auxes(node)

            if modals:
                # we consider modals themselves to be separate verb forms
                self.process_modal_verbs(modals, modal_auxes)

            if auxes:
                self.process_periphrastic_verb_forms(cop[0], auxes, refl, auxes + cop, node)
            else:
                # no auxiliaries, only cop
                self.process_copulas(node,cop,auxes,refl,expl)
            return

        if node.upos == 'VERB': #TODO maybe add "or node.feats['VerbForm'] == 'Part'"?

            # find auxiliary verbs, modal verbs, and auxiliary verbs related to modals among the children of the content verb and separate them from each other 
            auxes, modals, modal_auxes = self.find_auxes(node)
            aux_pass = [x for x in auxes if x.deprel == 'aux:pass']
            auxes_without_pass = [x for x in auxes if x.deprel != 'aux:pass']

            # infinitive with a subject is a subjunctive
            subj = [x for x in node.children if x.udeprel == 'subj']
            if node.feats['VerbForm'] == 'Inf' and subj:
                self.write_node_info(node,
                        person=node.feats['Person'],
                        number=node.feats['Number'],
                        mood='Sub',
                        form='Fin',
                        tense=Tense.FUT.value,
                        gender=node.feats['Gender'],
                        voice=node.feats['Voice'],
                        expl=expl,
                        ords=[node.ord]
                    )
                return
            
            if modals:
                # we consider modals themselves to be separate verb forms
                self.process_modal_verbs(modals, modal_auxes)
            
            if not auxes:
                phrase_ords = [node.ord] + [r.ord for r in refl]
                phrase_ords.sort()

                self.process_simple_verb_forms(node, expl, phrase_ords, node)


            else:
                # no passive auxiliaries
                if not aux_pass:
                    self.process_periphrastic_verb_forms(node, auxes, refl, auxes, node)

                # head verb has only passive auxiliary and no more other auxiliaries
                elif not auxes_without_pass:
                    phrase_ords = [node.ord] + [x.ord for x in auxes] + [r.ord for r in refl]
                    phrase_ords.sort()

                    # TODO phrase-level features are currently determined based on the first passive auxiliary, but it can happen that there are more than one passive auxiliary
                    self.process_simple_verb_forms(auxes[0], expl, phrase_ords, node)

                # head verb has passive auxiliary and also other auxiliaries
                else:
                    self.process_periphrastic_verb_forms(aux_pass[0], auxes_without_pass, refl, auxes, node)

    def find_auxes(self, node):
        """
        Find all auxiliaries among node.children and classifies them.

        Parameters:
            node (udapi.core.node.Node): head word, look for auxiliaries in its children

        Returns:
            tuple: a classification of auxiliaries consisting of:
                - auxiliaries directly modifying the node,
                - modal verbs,
                - auxiliaries modifying a modal verb.
        """

        node_auxes = []
        modals = []
        modal_auxes = []

        for child in node.children:
            if child.udeprel == 'aux':
                if child.lemma in MODALS:
                    modals.append(child)
                    modal_auxes = node_auxes # auxiliaries found so far are assumed to modify the modal verb (they come before it)
                    node_auxes = []
                else:
                    node_auxes.append(child)

        return node_auxes, modals, modal_auxes
    
    def process_modal_verbs(self, modals, modal_auxes):
        """
        Annotates modal verb forms with the Phrase* attributes.
        The modal verbs are kept as a single verb form, without including the infinitive of the content word.

        Parameters:
            modals (list): all modal verbs among the children of the head content verb (currently assumes there is only one.)
            modal_auxes (list): auxiliaries of the modal verb(s)
        
        """

        if not modal_auxes:
            self.process_simple_verb_forms(modals[0], '', [modals[0].ord], modals[0]) 

        else:
            self.process_periphrastic_verb_forms(modals[0], modal_auxes, [], modal_auxes, modals[0])


    def process_simple_verb_forms(self, node, expl, phrase_ords, head_node):
        """
        Annotate simple verb forms or passive verb forms that contain only a passive auxiliary.

        Parameters
            node (udapi.core.node.Node): The relevant node. If there is no passive construction, this is the head verb. If the head verb is passive, this is the passive auxiliary.
            expl (str): The value of the PhraseExpl attribute.
            phrase_ords (list[int]): The ord values of all member words of the verb form.
            head_node (udapi.core.node.Node): The node that should receive the Phrase* attributes, i.e., the head of the phrase.
        """

        # Portuguese
        # presente -> PhraseTense=Pres, PhraseAspect=''
        # Futuro do presente -> PhraseTense=Fut, PhraseAspect=''

        # Spanish
        # presente -> PhraseTense=Pres, PhraseAspect=''
        # futuro simple -> PhraseTense=Fut, PhraseAspect=''

        # Italian
        # presente -> PhraseTense=Pres, PhraseAspect=''
        # futuro semplice -> PhraseTense=Fut, PhraseAspect=''

        aspect = ''
        tense = node.feats['Tense']

        if node.feats['Mood'] == 'Ind':
            
            # Portuguese
            # pretérito imperfeito -> PhraseTense=Past, PhraseAspect=Imp

            # Spanish
            # pretérito imperfecto -> PhraseTense=Past, PhraseAspect=Imp

            # Italian
            # imperfetto -> PhraseTense=Past, PhraseAspect=Imp
            if node.feats['Tense'] == 'Imp':
                tense=Tense.PAST.value
                aspect=Aspect.IMP.value

            # Portuguese
            # pretérito perfeito -> PhraseTense=Past, PhraseAspect=Perf

            # Spanish
            # pretérito perfecto -> PhraseTense=Past, PhraseAspect=Perf

            # Italian
            # pass remoto -> PhraseTense=Past, PhraseAspect=Perf
            if node.feats['Tense'] == 'Past':
                aspect=Aspect.PERF.value

            # Portuguese
            # pretérito mais que perfeito simples -> PhraseTense=Past, PhraseAspect=Pqp
            if node.feats['Tense'] == 'Pqp':
                tense=Tense.PAST.value
                aspect=Aspect.PQP.value
                
        # Portuguese
        # subjunctive presente -> PhraseTense=Pres, PhraseAspect=''
        # subjunctive futuro -> PhraseTense=Fut, PhraseAspect=''

        # Spanish
        # subjunctive presente -> PhraseTense=Pres, PhraseAspect=''
        # subjunctive futuro -> PhraseTense=Fut, PhraseAspect='' TODO not annotated in treebanks?

        # Italian
        # Congiuntivo presente -> PhraseTense=Pres, PhraseAspect=''
        if node.feats['Mood'] == 'Sub':

            if node.feats['Tense'] == 'Past':
                aspect=Aspect.IMP.value

            # Portuguese
            # subjunctive pretérito imperfeito -> PhraseTense=Past, PhraseAspect=Imp

            # Spanish
            # Pretérito imperfecto -> PhraseTense=Past, PhraseAspect=Imp

            # Italian
            # Congiuntivo imperfetto -> PhraseTense=Past, PhraseAspect=Imp
            if node.feats['Tense']  == 'Imp':
                tense=Tense.PAST.value
                aspect=Aspect.IMP.value

        # Portuguese
        # Futuro do pretérito (cnd) -> PhraseTense=Pres, PhraseAspect='', PhraseMood=Cnd

        # Spanish
        # pospretérito (cnd) -> PhraseTense=Pres, PhraseAspect='', PhraseMood=Cnd

        # Italian
        # Condizionale presente -> PhraseTense=Pres, PhraseAspect='', PhraseMood=Cnd
        if node.feats['Mood'] == 'Cnd':
            aspect=''
            tense=Tense.PRES.value

        
        self.write_node_info(head_node,
            person=node.feats['Person'],
            aspect=aspect,
            number=node.feats['Number'],
            mood=node.feats['Mood'],
            form=node.feats['VerbForm'],
            tense=tense,
            gender=head_node.feats['Gender'],
            voice=head_node.feats['Voice'],
            expl=expl,
            ords=phrase_ords
        )


    def process_periphrastic_verb_forms(self, node, auxes, refl, all_auxes, head_node):
        """
        Annotate periphrastic verb forms with the Phrase* attributes.

        Parameters
            node (udapi.core.node.Node): The relevant node. If there is no passive construction, this is the head verb. If the head verb is passive, this is the passive auxiliary.
            auxes (list[udapi.core.node.Node]): All auxiliaries except the passive auxiliaries.
            refl (list[udapi.core.node.Node]): Reflexives that should be included in the periphrastic phrase.
            all_auxes (list[udapi.core.node.Node]): All auxiliaries, including the passive auxiliaries.
            head_node (udapi.core.node.Node): The node that should receive the Phrase* attributes, i.e., the head of the phrase.
        """

        if refl:
            expl='Pv'
        else:
            expl=None

        if len(auxes)  == 1:
            # Cnd
            if auxes[0].feats['Mood'] == 'Cnd' and (node.feats['VerbForm'] == 'Part' or node.feats['VerbForm'] == 'Ger'):
                phrase_ords = [head_node.ord] + [x.ord for x in all_auxes] + [r.ord for r in refl]
                phrase_ords.sort()

                # Portuguese
                # aux estar cond + gerund -> PhraseTense=Pres, PhraseAspect=Prog, PhraseMood=Cnd
                if auxes[0].lemma == 'estar':
                    tense=Tense.PRES.value
                    aspect=Aspect.PROG.value

                # Portuguese
                # Futuro do pretérito composto -> PhraseTense=Past, PhraseAspect='', PhraseMood=Cnd

                # Spanish
                # Antepospretérito -> PhraseTense=Past, PhraseAspect='', PhraseMood=Cnd

                # Italian
                # Condizionale passato -> PhraseTense=Past, PhraseAspect='', PhraseMood=Cnd
                else:
                    tense=Tense.PAST.value
                    aspect=''

                self.write_node_info(head_node,
                    tense=tense,
                    number=auxes[0].feats['Number'],
                    person=auxes[0].feats['Person'],
                    aspect=aspect,
                    mood='Cnd',
                    form='Fin',
                    expl=expl,
                    voice=head_node.feats['Voice'],
                    ords=phrase_ords)
                return
            
            if auxes[0].lemma == 'vir' and auxes[0].feats['Tense'] in ['Pres', 'Imp', 'Past'] and node.feats['VerbForm'] == 'Ger':
                phrase_ords = [head_node.ord] + [x.ord for x in all_auxes] + [r.ord for r in refl]
                phrase_ords.sort()

                # aux Pres (vir) + gerund -> PhraseTense=PastPres, PraseAspect=Prog
                if auxes[0].feats['Tense'] == 'Pres':
                    tense=Tense.PASTPRES.value


                elif auxes[0].feats['Tense'] in ['Imp', 'Past']: 
                    tense=Tense.PAST.value

                self.write_node_info(head_node,
                    tense=tense,
                    number=auxes[0].feats['Number'],
                    person=auxes[0].feats['Person'],
                    mood=auxes[0].feats['Mood'],
                    form='Fin',
                    aspect=Aspect.PROG.value,
                    voice=head_node.feats['Voice'],
                    expl=expl,
                    ords=phrase_ords)      
                return
            
            if auxes[0].lemma == 'ir' and node.feats['VerbForm'] == 'Ger':
                phrase_ords = [head_node.ord] + [x.ord for x in all_auxes] + [r.ord for r in refl]
                phrase_ords.sort()

                # aux Pres (ir) + gerund -> PhraseTense=Pres, PhraseAspect=Prog
                tense = auxes[0].feats['Tense']
                aspect = Aspect.PROG.value

                # aux Imp (ir) + gerund -> PhraseTense=Past, PhraseAspect=Prog
                if auxes[0].feats['Tense'] == 'Imp':
                    tense=Tense.PAST.value
                    aspect=Aspect.PROG.value

                self.write_node_info(head_node,
                    tense=tense,
                    number=auxes[0].feats['Number'],
                    person=auxes[0].feats['Person'],
                    mood=auxes[0].feats['Mood'],
                    aspect=aspect,
                    form='Fin',
                    voice=head_node.feats['Voice'],
                    expl=expl,
                    ords=phrase_ords)
                return
            
            # Portuguese
            # pretérito mais que perfeito composto (aux haver) -> PhraseTense=Past, PhraseAspect=Perf
            if auxes[0].lemma == 'haver' and auxes[0].feats['Tense'] == 'Imp' and node.feats['VerbForm'] == 'Part':
                phrase_ords = [head_node.ord] + [x.ord for x in all_auxes] + [r.ord for r in refl]
                phrase_ords.sort()

                self.write_node_info(head_node,
                    tense=Tense.PAST.value,
                    aspect=Aspect.PERF.value,
                    number=auxes[0].feats['Number'],
                    person=auxes[0].feats['Person'],
                    mood=auxes[0].feats['Mood'],
                    form='Fin',
                    voice=head_node.feats['Voice'],
                    expl=expl,
                    ords=phrase_ords)
                return
                
            # Auxiliary 'estar' followed by a gerund 
            if node.feats['VerbForm'] == 'Ger':
                phrase_ords = [head_node.ord] + [x.ord for x in all_auxes] + [r.ord for r in refl]
                phrase_ords.sort()

                # Portuguese + Spanish
                # pretérito imperfeito (aux estar) -> PhraseTense=Past, PhraseAspect=ImpProg
                # subjunctive pretérito imperfeito (aux estar) -> PhraseTense=Past, PhraseAspect=ImpProg, PhraseMood=Sub
                if auxes[0].feats['Tense'] == 'Imp':
                    tense=Tense.PAST.value
                    aspect=Aspect.IMPPROG.value

                # Portuguese + Spanish
                # pretérito perfeito (aux estar) -> PhraseTense=Past, PhraseAspect=PerfProg
                elif auxes[0].feats['Tense'] == 'Past':
                    tense=Tense.PAST.value
                    aspect=Aspect.PERFPROG.value

                # Portuguese + Spanish
                # presente (aux estar) -> PhraseTense=Pres, PhraseAspect=Prog
                # futuro do presente (aux estar) -> PhraseTense=Fut, PhraseAspect=Prog
                # subjunctive presente (aux estar) -> PhraseTense=Pres, PhraseAspect=Prog, PhraseMood=Sub
                # subjunctive futuro (aux estar) -> PhraseTense=Fut, PhraseAspect=Prog, PhraseMood=Sub
                else:
                    tense=auxes[0].feats['Tense']
                    aspect=Aspect.PROG.value

                self.write_node_info(head_node,
                    tense=tense,
                    number=auxes[0].feats['Number'],
                    person=auxes[0].feats['Person'],
                    mood=auxes[0].feats['Mood'],
                    form='Fin',
                    voice=head_node.feats['Voice'],
                    aspect=aspect,
                    expl=expl,
                    ords=phrase_ords)
                
                return

            # Auxiliary 'ter' / 'haber' / 'avere' / 'essere' followed by a participle
            if node.feats['VerbForm'] == 'Part':
                phrase_ords = [head_node.ord] + [x.ord for x in all_auxes] + [r.ord for r in refl]
                phrase_ords.sort()

                # Portuguese
                # futuro do presente composto (aux ter) -> PhraseTense=Fut, PhraseAspect=Perf

                # Spanish
                # Futuro compuesto antefuturo -> PhraseTense=Fut, PhraseAspect=Perf

                # Italian
                # Futuro anteriore -> PhraseTense=Fut, PhraseAspect=Perf
                aspect=Aspect.PERF.value
                tense=auxes[0].feats['Tense']

                # Spanish
                # Pretérito perfecto compuesto ante presente -> PhraseTense=Past, PhraseAspect=Perf

                # Italian
                # Passato prossimo (aux avere/essere) -> PhraseTense=Past, PhraseAspect=Perf
                if auxes[0].feats['Tense'] == 'Pres':

                    # Portuguese
                    # pretérito perfeito composto (aux ter) -> PhraseTense=PastPres, PhraseAspect=Perf
                    # subjonctive pretérito perfeito composto (aux ter) -> PhraseTense=PastPres, PhraseAspect=Perf, PhraseMood=Sub
                    if auxes[0].lemma == 'ter' or auxes[0].feats['Mood'] == 'Sub':
                        tense = Tense.PASTPRES.value
                    else:
                        tense=Tense.PAST.value

                # Portuguese
                # pretérito mais que perfeito composto (aux ter) -> PhraseTense=Past, PhraseAspect=Pqp
                # subjonctive pretérito mais-que-perfeito composto (aux ter) -> PhraseTense=Past, PhraseAspect=Pqp, PhraseMood=Sub

                # Spanish
                # pretérito pluscuamperfecto -> PhraseTense=Past, PhraseAspect=Pqp

                # Italian
                # Trapassato prossimo -> PhraseTense=Past, PhraseAspect=Pqp
                elif auxes[0].feats['Tense'] in ['Imp', 'Past']: # TODO prej neni v Past, jenom Imp
                    tense=Tense.PAST.value
                    aspect=Aspect.PQP.value

                self.write_node_info(head_node,
                    tense=tense,
                    number=auxes[0].feats['Number'],
                    person=auxes[0].feats['Person'],
                    mood=auxes[0].feats['Mood'],
                    aspect=aspect,
                    form='Fin',
                    voice=head_node.feats['Voice'],
                    expl=expl,
                    ords=phrase_ords)
                return
                
            # auxiliary 'ir' followed by infinitive
            # TODO solve these verb forms for Spanish (VERB 'ir' + ADP 'a' + infinitive)
            if auxes[0].lemma == 'ir' and node.feats['VerbForm'] == 'Inf':
                phrase_ords = [head_node.ord] + [x.ord for x in all_auxes] + [r.ord for r in refl]
                phrase_ords.sort()

                tense=node.feats['Tense']
                aspect=''

                # Futuro perifrástico -> PhraseTense=Fut, PhraseAspect=''
                if auxes[0].feats['Tense'] == 'Pres': 
                    tense=Tense.FUT.value
                    aspect=''

                # Futuro perifrástico passado imp -> PhraseTense=PastFut, PhraseAspect=Imp
                elif auxes[0].feats['Tense'] == 'Imp':
                    tense=Tense.PASTFUT.value
                    aspect=Aspect.IMP.value

                # Futuro perifrástico in the future -> PhraseTense=FutFut, PhraseAspect=''
                elif auxes[0].feats['Tense'] == 'Fut':
                    tense=Tense.FUTFUT.value
                    aspect=''

                # Futuro perifrástico passado perf -> PhraseTense=PastFut, PhraseAspect=Perf
                elif auxes[0].feats['Tense'] == 'Past':
                    tense=Tense.PASTFUT.value
                    aspect=Aspect.PERF.value                

                self.write_node_info(head_node,
                    tense=tense,
                    aspect=aspect,
                    number=auxes[0].feats['Number'],
                    person=auxes[0].feats['Person'],
                    mood=auxes[0].feats['Mood'],
                    form='Fin',
                    voice=head_node.feats['Voice'],
                    expl=expl,
                    ords=phrase_ords)
                
                
        elif len(auxes) == 2:
            # Portuguese
            # auxiliry 'ir' followed by auxiliary 'estar' in infinitive and a gerund

            # TODO Spanish
            # VERB 'ir' + ADP 'a' + AUX 'estar'.Inf + gerund
            if auxes[0].lemma == 'ir' and auxes[1].lemma == 'estar' and node.feats['VerbForm'] == 'Ger':
                phrase_ords = [head_node.ord] + [x.ord for x in all_auxes] + [r.ord for r in refl]
                phrase_ords.sort()

                # Futuro perifrástico -> PhraseTense=Fut, PhraseAspect=Prog
                if auxes[0].feats['Tense'] == 'Pres':
                    tense=Tense.FUT.value
                    aspect=Aspect.PROG.value

                # Futuro perifrástico passado imp -> PhraseTense=PastFut, PhraseAspect=ImpProg
                if auxes[0].feats['Tense'] == 'Imp':
                    tense=Tense.PASTFUT.value
                    aspect=Aspect.IMPPROG.value

                # Futuro perifrástico in the future -> PhraseTense=FutFut, PhraseAspect=Prog
                if auxes[0].feats['Tense'] == 'Fut':
                    tense=Tense.FUTFUT.value
                    aspect=Aspect.PROG.value

                if auxes[0].feats['Tense'] == 'Past':
                    tense=Tense.PASTFUT.value
                    aspect=Aspect.PERFPROG.value

                self.write_node_info(head_node,
                    tense=tense,
                    number=auxes[0].feats['Number'],
                    person=auxes[0].feats['Person'],
                    mood=auxes[0].feats['Mood'],
                    form='Fin',
                    aspect=aspect,
                    voice=head_node.feats['Voice'],
                    expl=expl,
                    ords=phrase_ords)

            # auxiliriy 'ir' in present or future tense followed by auxiliary 'ter' in infinitive and a participle
            if auxes[0].lemma == 'ir' and (auxes[0].feats['Tense'] in ['Pres', 'Fut']) and auxes[1].lemma == 'ter' and node.feats['VerbForm'] == 'Part':
                phrase_ords = [head_node.ord] + [x.ord for x in all_auxes] + [r.ord for r in refl]
                phrase_ords.sort()

                # Futuro perifrástico -> PhraseTense=FutFut, PhraseAspect=Perf
                if auxes[0].feats['Tense'] == 'Fut':
                    tense=Tense.FUTFUT.value
                    aspect=Aspect.PERF.value

                # aux Pres (ir) + aux ter inf + pp -> PhraseTense=Fut, PhraseAspect=Perf
                if auxes[0].feats['Tense'] == 'Pres':
                    tense=Tense.FUT.value
                    aspect=Aspect.PERF.value

                self.write_node_info(head_node,
                    tense=tense,
                    number=auxes[0].feats['Number'],
                    person=auxes[0].feats['Person'],
                    mood=auxes[0].feats['Mood'],
                    aspect=aspect,
                    form='Fin',
                    voice=head_node.feats['Voice'],
                    expl=expl,
                    ords=phrase_ords)    
                
            
                
            # Cnd (only ter/haber), Sub and Past,Pres,Fut tenses: 2 auxes - ter/haber + estar
            if auxes[0].lemma in AUXES_HAVE and auxes[1].lemma == 'estar' and node.feats['VerbForm'] == 'Ger':
                phrase_ords = [head_node.ord] + [x.ord for x in all_auxes] + [r.ord for r in refl]
                phrase_ords.sort()

                tense = auxes[0].feats['Tense']
                aspect = Aspect.PERFPROG.value

                # aux ter cond + estar pp + gerund -> PhraseTense=Past, PhraseAspect=Prog, PhraseMood=Cnd
                if auxes[0].feats['Mood'] == 'Cnd':
                    tense=Tense.PAST.value
                    aspect=Aspect.PROG.value

                # Pretérito perfeito composto -> PhraseTense=PastPres, PhraseAspect=PerfProg
                # subjonctive Pretérito perfeito composto -> PhraseTense=PastPres, PhraseAspect=PerfProg, PhraseMood=Sub
                elif auxes[0].feats['Tense'] == 'Pres':
                    tense=Tense.PASTPRES.value

                # Pretérito mais que perfeito composto -> PhraseTense=Past, PhraseAspect=ImpProg
                # subjonctive Pretérito mais que perfeito composto -> PhraseTense=Past, PhraseAspect=ImpProg, PhraseMood=Sub
                elif auxes[0].feats['Tense'] in ['Imp', 'Past']:
                    tense=Tense.PAST.value
                    aspect=Aspect.IMPPROG.value

                # Futuro do presente composto -> PhraseTense=Fut, PhraseAspect=PerfProg
                elif auxes[0].feats['Tense'] == 'Fut' and auxes[0].lemma == 'ter':
                    tense=Tense.FUT.value

                self.write_node_info(head_node,
                    tense=tense,
                    number=auxes[0].feats['Number'],
                    person=auxes[0].feats['Person'],
                    mood=auxes[0].feats['Mood'],
                    form='Fin',
                    aspect=aspect,
                    voice=head_node.feats['Voice'],
                    expl=expl,
                    ords=phrase_ords,
                )
                return
                
    def process_copulas(self, node, cop, auxes, refl, expl):

        aspect = ''
        
        if not auxes:
            tense = cop[0].feats['Tense']
            number=cop[0].feats['Number']
            person=cop[0].feats['Person']
            mood=cop[0].feats['Mood']

            if cop[0].feats['Tense'] in ['Pres', 'Fut']:
                if cop[0].lemma == 'ser':
                    aspect=Aspect.PERF.value
                elif cop[0].lemma == 'estar':
                    aspect=Aspect.IMP.value
            
            elif cop[0].feats['Tense'] == 'Imp':
                tense=Tense.PAST.value
                aspect=Aspect.IMP.value
            
            elif cop[0].feats['Tense'] == 'Past':
                aspect=Aspect.PERF.value
            else:
                # i.e. copulas in infinitive
                aspect=''

        else: 
            tense = auxes[0].feats['Tense']
            number=auxes[0].feats['Number']
            person=auxes[0].feats['Person']
            mood=auxes[0].feats['Mood']
            aspect=''

            
            if auxes[0].lemma == 'estar': 
                aspect=Aspect.IMPPROG.value

        phrase_ords = [node.ord] + [x.ord for x in cop] + [x.ord for x in auxes] + [r.ord for r in refl]
        phrase_ords.sort()
      
        self.write_node_info(node,
                    tense=tense,
                    number=number,
                    person=person,
                    mood=mood,
                    form='Fin',
                    aspect=aspect,
                    voice=node.feats['Voice'],
                    expl=expl,
                    ords=phrase_ords,
                )
