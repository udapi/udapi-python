
import udapi.block.msf.phrase
from enum import Enum

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
        refl = [x for x in node.children if x.lemma == 'se' and x.upos == 'PRON' and x.udeprel == 'expl' and x.udeprel != 'expl:impers' and x.udeprel != 'expl:pass']
        
        if refl:
            expl='Pv'
        else:
            expl=None
   
        if cop:
            auxes = [x for x in node.children if x.udeprel == 'aux']
            if auxes:
                self.process_periphrastic_verb_forms(cop[0], auxes, refl, auxes + cop, node)
            else:
                # no auxiliaries, only cop
                self.process_copulas(node,cop,auxes,refl,expl)
            return

        if node.upos == 'VERB':
            auxes = [x for x in node.children if x.udeprel == 'aux']
            aux_pass = [x for x in node.children if x.deprel == 'aux:pass']
            auxes_without_pass = [x for x in node.children if x.udeprel == 'aux' and x.deprel != 'aux:pass']

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
            
            if not auxes:
                    phrase_ords = [node.ord] + [r.ord for r in refl]
                    phrase_ords.sort()

                    # presente -> PhraseTense=Pres, PhraseAspect=''
                    # Futuro do presente -> PhraseTense=Fut, PhraseAspect=''
                    aspect = ''
                    tense = node.feats['Tense']

                    if node.feats['Mood'] == 'Ind':

                        # pretérito imperfeito -> PhraseTense=Past, PhraseAspect=Imp
                        if node.feats['Tense'] == 'Imp':
                            tense=Tense.PAST.value
                            aspect=Aspect.IMP.value

                        # pretérito perfeito -> PhraseTense=Past, PhraseAspect=Perf
                        if node.feats['Tense'] == 'Past':
                            aspect=Aspect.PERF.value

                        # pretérito mais que perfeito simples -> PhraseTense=Past, PhraseAspect=Pqp
                        if node.feats['Tense'] == 'Pqp':
                            tense=Tense.PAST.value
                            aspect=Aspect.PQP.value
                            
                    # subjunctive presente -> PhraseTense=Pres, PhraseAspect=''
                    # subjunctive futuro -> PhraseTense=Fut, PhraseAspect=''
                    if node.feats['Mood'] == 'Sub':

                        if node.feats['Tense'] == 'Past':
                            aspect=Aspect.IMP.value

                        # subjunctive pretérito imperfeito -> PhraseTense=Past, PhraseAspect=Imp
                        if node.feats['Tense']  == 'Imp':
                            tense=Tense.PAST.value
                            aspect=Aspect.IMP.value

                    # Futuro do pretérito (cnd) -> PhraseTense=Pres, PhraseAspect='', PhraseMood=Cnd
                    if node.feats['Mood'] == 'Cnd':
                        aspect=''
                        tense=Tense.PRES.value

                    
                    self.write_node_info(node,
                        person=node.feats['Person'],
                        aspect=aspect,
                        number=node.feats['Number'],
                        mood=node.feats['Mood'],
                        form=node.feats['VerbForm'],
                        tense=tense,
                        gender=node.feats['Gender'],
                        voice=node.feats['Voice'],
                        expl=expl,
                        ords=phrase_ords
                    )


            else:
                # no passive auxiliaries
                if not aux_pass:
                    self.process_periphrastic_verb_forms(node, auxes, refl, auxes, node)

                # head verb has one passive auxiliary and no more other auxiliaries
                # TODO complete the tenses and aspects for individual verb forms
                elif not auxes_without_pass:
                    phrase_ords = [node.ord] + [x.ord for x in auxes] + [r.ord for r in refl]
                    phrase_ords.sort()

                    self.write_node_info(node,
                        person=aux_pass[0].feats['Person'],
                        number=aux_pass[0].feats['Number'],
                        mood=aux_pass[0].feats['Mood'],
                        form='Fin',
                        tense=aux_pass[0].feats['Tense'],
                        gender=node.feats['Gender'],
                        voice='Pass',
                        expl=expl,
                        ords=phrase_ords
                    )

                # head verb has passive auxiliary and also other auxiliaries
                else:
                    self.process_periphrastic_verb_forms(aux_pass[0], auxes_without_pass, refl, auxes, node)


    def process_periphrastic_verb_forms(self, node, auxes, refl, all_auxes, head_node):
        """
        Parameters
        - node: if there is no passive then the node is the head verb, if the head verb is in the passive, then the node is the passive auxiliary
        - auxes: list of all auxiliaries except the passive auxes
        - refl: list of reflexives which should be included into the periphrastic phrase
        - all_auxes: list of all auxiliaries (passive auxes are included)
        - head_node: the node which should have the Phrase* attributes, i. e. the head of the phrase

        annotates periphrastic verb forms with the Phrase* attributes
        """

        if refl:
            expl='Pv'
        else:
            expl=None

        if len(auxes)  == 1:
            # Cnd
            if ((auxes[0].lemma == 'ter' and node.feats['VerbForm'] == 'Part') or (auxes[0].lemma == 'estar' and node.feats['VerbForm'] == 'Ger')) and auxes[0].feats['Mood'] == 'Cnd':
                phrase_ords = [head_node.ord] + [x.ord for x in all_auxes] + [r.ord for r in refl] + [r.ord for r in refl]
                phrase_ords.sort()

                # aux estar cond + gerund -> PhraseTense=Pres, PhraseAspect=Prog, PhraseMood=Cnd
                if auxes[0].lemma == 'estar':
                    tense=Tense.PRES.value
                    aspect=Aspect.PROG.value

                # Futuro do pretérito composto -> PhraseTense=Past, PhraseAspect=Perf, PhraseMood=Cnd
                else:
                    tense=Tense.PAST.value
                    aspect=Aspect.PERF.value

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
                
            # Auxiliary 'estar' followed by a gerund 
            if auxes[0].lemma == 'estar' and node.feats['VerbForm'] == 'Ger':
                phrase_ords = [head_node.ord] + [x.ord for x in all_auxes] + [r.ord for r in refl]
                phrase_ords.sort()

                # pretérito imperfeito (aux estar) -> PhraseTense=Past, PhraseAspect=ImpProg
                # subjunctive pretérito imperfeito (aux estar) -> PhraseTense=Past, PhraseAspect=ImpProg, PhraseMood=Sub
                if auxes[0].feats['Tense'] == 'Imp':
                    tense=Tense.PAST.value
                    aspect=Aspect.IMPPROG.value

                # pretérito perfeito (aux estar) -> PhraseTense=Past, PhraseAspect=PerfProg
                elif auxes[0].feats['Tense'] == 'Past':
                    tense=Tense.PAST.value
                    aspect=Aspect.PERFPROG.value

                # conditional (aux estar) -> PhraseTense=Pres, PhraseAspect=Prog, PhraseMood=Cnd
                elif auxes[0].feats['Mood'] == 'Cnd':
                    tense=Tense.PRES.value
                    aspect=Aspect.PROG.value

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

            # Auxiliary 'ter' followed by a participle
            if auxes[0].lemma == 'ter' and node.feats['VerbForm'] == 'Part':
                phrase_ords = [head_node.ord] + [x.ord for x in all_auxes] + [r.ord for r in refl]
                phrase_ords.sort()

                # futuro do presente composto (aux ter) -> PhraseTense=Fut, PhraseAspect=Perf
                aspect=Aspect.PERF.value
                tense=auxes[0].feats['Tense']

                # pretérito perfeito composto (aux ter) -> PhraseTense=PastPres, PhraseAspect=Perf
                # subjonctive pretérito perfeito composto (aux ter) -> PhraseTense=PastPres, PhraseAspect=Perf, PhraseMood=Sub
                if auxes[0].feats['Tense'] == 'Pres':
                    tense=Tense.PASTPRES.value

                # pretérito mais que perfeito composto (aux ter/haver) -> PhraseTense=Past, PhraseAspect=Pqp
                # subjonctive pretérito mais-que-perfeito composto (aux ter) -> PhraseTense=Past, PhraseAspect=Pqp, PhraseMood=Sub
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

            
            # auxiliary 'ir' followed by infinitive
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
                
        elif len(auxes) == 2:
            # auxiliry 'ir' followed by auxiliary 'estar' in infinitive and a gerund
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
                
            
                
            # Cnd (only ter), Sub and Past,Pres,Fut tenses: 2 auxes - ter + estar
            if auxes[0].lemma in ['ter', 'haver'] and auxes[1].lemma == 'estar' and node.feats['VerbForm'] == 'Ger':
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
