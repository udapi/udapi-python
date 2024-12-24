"""
Morphosyntactic features (UniDive):
Create abstract nodes representing dropped arguments of predicates (if verbal
morphology signals that the subject is third person singular, and there is no
subject node, create an abstract node and copy the features there).
"""
from udapi.core.block import Block
import re

class MsfCreateAbstract(Block):

    def process_node(self, node):
        """
        If a node has MSFVerbForm=Fin and at least one of the agreement features
        MSFNumber, MSFPerson, MSFGender, MSFAnimacy, MSFPolite, assume that these
        features characterize the subject (this block is not suitable for languages
        with polypersonal agreement). Check that the subject is present. If not,
        create an abstract node to represent it.
        """
        if node.misc['MSFVerbForm'] == 'Fin' and any([node.misc[x] for x in ['MSFNumber', 'MSFPerson', 'MSFGender', 'MSFAnimacy', 'MSFPolite']]):
            # Current node is a finite predicate. Does it have a subject? If not, create an abstract one.
            if not any([x.udeprel in ['nsubj', 'csubj'] for x in node.children]):
                # There could already be an abstract subject. We have to look for it in the enhanced graph.
                if not any([re.match(r"^[nc]subj", edep['deprel']) for edep in node.deps]):
                    # Create an abstract subject.
                    subject = node.create_empty_child('nsubj')
                    subject.upos = 'PRON'
                    subject.feats['PronType'] = 'Prs'
                    subject.misc['MSFPronType'] = 'Prs'
                    subject.feats['Case'] = 'Nom'
                    subject.misc['MSFCase'] = 'Nom'
                    for f in ['Number', 'Person', 'Gender', 'Animacy', 'Polite']:
                        msf = 'MSF' + f
                        if node.misc[msf]:
                            subject.feats[f] = node.misc[msf]
                            subject.misc[msf] = node.misc[msf]
                    subject.misc['MSFFunc'] = 'No'
