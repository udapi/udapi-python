"""Block to fix case-enhanced dependency relations in Czech."""
from udapi.core.block import Block
import logging
import re

class FixEdeprels(Block):

    def process_node(self, node):
        """
        Occasionally the edeprels automatically derived from the Czech basic
        trees do not match the whitelist. For example, the noun is an
        abbreviation and its morphological case is unknown.
        """
        for edep in node.deps:
            if re.match(r'^(acl|advcl):', edep['deprel']):
                # We do not include 'i' in the list of redundant prefixes because we want to preserve 'i když' (but we want to discard the other combinations).
                edep['deprel'] = re.sub(r'^(acl|advcl):(?:a|alespoň|až|jen|hlavně|například|protože|teprve|zejména)_(aby|až|jestliže|když|pokud)$', r'\1:\2', edep['deprel'])
                edep['deprel'] = re.sub(r'^(acl|advcl):(aby|až|jestliže|když|pokud)_(?:ale|tedy|totiž|už|však)$', r'\1:\2', edep['deprel'])
                edep['deprel'] = re.sub(r'^(advcl):abi$', r'\1:aby', edep['deprel'])
                edep['deprel'] = re.sub(r'^(advcl):ačkoliv$', r'\1:ačkoli', edep['deprel'])
                edep['deprel'] = re.sub(r'^(acl|advcl):co_když$', r'\1', edep['deprel'])
                edep['deprel'] = re.sub(r'^(advcl):jak_aby$', r'\1:jak', edep['deprel'])
                edep['deprel'] = re.sub(r'^(advcl):jak_ad$', r'\1:jak', edep['deprel'])
                edep['deprel'] = re.sub(r'^(advcl):jakkoliv$', r'\1:jakkoli', edep['deprel'])
                edep['deprel'] = re.sub(r'^(acl|advcl):jakoby$', r'\1:jako', edep['deprel']) # these instances in FicTree should be spelled 'jako by'
                edep['deprel'] = re.sub(r'^(advcl):jelikož_do$', r'\1:jelikož', edep['deprel'])
                edep['deprel'] = re.sub(r'^(advcl):jestli_že$', r'\1:jestliže', edep['deprel'])
                edep['deprel'] = re.sub(r'^(acl):k$', r'\1', edep['deprel'])
                edep['deprel'] = re.sub(r'^(advcl):kdykoliv$', r'\1:kdykoli', edep['deprel'])
                edep['deprel'] = re.sub(r'^advcl:místo$', r'obl:místo:gen', edep['deprel']) # 'v poslední době se množí bysem místo bych'
                edep['deprel'] = re.sub(r'^(advcl):neboť$', r'\1', edep['deprel']) # 'neboť' is coordinating
                edep['deprel'] = re.sub(r'^(advcl):nechť$', r'\1', edep['deprel'])
                edep['deprel'] = re.sub(r'^(acl):od$', r'nmod:od:gen', edep['deprel'])
                edep['deprel'] = re.sub(r'^(advcl):podle$', r'obl:podle:gen', edep['deprel'])
                edep['deprel'] = re.sub(r'^(advcl):pro$', r'obl:pro:acc', edep['deprel'])
                edep['deprel'] = re.sub(r'^(acl):v$', r'nmod:v:loc', edep['deprel'])
                edep['deprel'] = re.sub(r'^(acl|advcl):v_případ_že$', r'\1:v_případě_že', edep['deprel'])
                edep['deprel'] = re.sub(r'^(advcl):v_duch$', r'obl:v_duchu:gen', edep['deprel'])
                edep['deprel'] = re.sub(r'^(advcl):že_ať$', r'\1:ať', edep['deprel'])
                edep['deprel'] = re.sub(r'^(advcl):že_jako$', r'\1:že', edep['deprel'])
                if edep['deprel'] == 'acl:v' and node.form == 'patře':
                    edep['deprel'] = 'nmod:v:loc'
                    node.deprel = 'nmod'
                    node.lemma = 'patro'
                    node.upos = 'NOUN'
                    node.xpos = 'NNNS6-----A----'
                    node.feats['Aspect'] = ''
                    node.feats['Gender'] = 'Neut'
                    node.feats['Tense'] = ''
                    node.feats['VerbForm'] = ''
                    node.feats['Voice'] = ''
                edep['deprel'] = re.sub(r'^advcl:(od|do)$', r'obl:\1:gen', edep['deprel'])
            elif re.match(r'^(nmod|obl):', edep['deprel']):
                if edep['deprel'] == 'nmod:loc' and node.parent.feats['Case'] == 'Loc' or edep['deprel'] == 'nmod:voc' and node.parent.feats['Case'] == 'Voc':
                    # This is a same-case noun-noun modifier, which just happens to be in the locative.
                    # For example, 'v Ostravě-Porubě', 'Porubě' is attached to 'Ostravě', 'Ostravě' has
                    # nmod:v:loc, which is OK, but for 'Porubě' the case does not say anything significant.
                    edep['deprel'] = 'nmod'
                elif edep['deprel'] == 'obl:loc':
                    # Annotation error. The first occurrence in PDT dev:
                    # 'V Rapaportu, ceníku Antverpské burzy i Diamantberichtu jsou uvedeny ceny...'
                    # The preposition 'V' should modify coordination 'Rapaportu i Diamantberichtu'.
                    # However, 'Rapaportu' is attached as 'obl' to 'Diamantberichtu'.
                    edep['deprel'] = 'obl:v:loc'
                elif edep['deprel'] == 'obl:arg:loc':
                    # Annotation error. The first occurrence in PDT dev:
                    edep['deprel'] = 'obl:arg:na:loc'
                elif edep['deprel'] == 'nmod:loc':
                    # 'působil v kanadském Edmontonu Oilers', 'Edmontonu' attached to 'Oilers' and not vice versa.
                    edep['deprel'] = 'nmod:nom'
                elif edep['deprel'] == 'obl:nom' or edep['deprel'] == 'obl:voc':
                    # Possibly an annotation error, nominative should be accusative, and the nominal should be direct object?
                    # However, there seems to be a great variability in the causes, some are subjects and many are really obliques, so let's go just with 'obl' for now.
                    edep['deprel'] = 'obl'
                elif edep['deprel'] == 'nmod:voc':
                    # 'v 8. čísle tiskoviny Ty rudá krávo'
                    edep['deprel'] = 'nmod:nom'
                elif re.match(r'^(nmod|obl(:arg)?):během$', edep['deprel']):
                    edep['deprel'] += ':gen'
                elif re.match(r'^(nmod|obl(:arg)?):bez$', edep['deprel']):
                    edep['deprel'] += ':gen'
                elif edep['deprel'] == 'nmod:co:nom':
                    # Annotation error: 'kompatibilní znamená tolik co slučitelný'
                    # 'co' should be relative pronoun rather than subordinating conjunction.
                    edep['deprel'] = 'acl:relcl'
                    node.deprel = 'acl:relcl'
                elif re.match(r'^(nmod|obl(:arg)?):díky$', edep['deprel']):
                    edep['deprel'] += ':dat'
                elif re.match(r'^(nmod|obl(:arg)?):dle$', edep['deprel']):
                    edep['deprel'] += ':gen'
                elif re.match(r'^(nmod|obl(:arg)?):do$', edep['deprel']):
                    edep['deprel'] += ':gen'
                elif re.match(r'^(nmod|obl(:arg)?):k(:nom)?$', edep['deprel']):
                    edep['deprel'] = re.sub(r':nom$', '', edep['deprel']) + ':dat'
                elif re.match(r'^(nmod|obl(:arg)?):kolem$', edep['deprel']):
                    edep['deprel'] += ':gen'
                elif re.match(r'^(nmod|obl(:arg)?):kromě$', edep['deprel']):
                    edep['deprel'] += ':gen'
                elif re.match(r'^(obl(:arg)?):li$', edep['deprel']):
                    edep['deprel'] = 'advcl:li'
                elif re.match(r'^(nmod|obl(:arg)?):mezi$', edep['deprel']):
                    if len([x for x in node.children if x.deprel == 'nummod:gov']) > 0:
                        edep['deprel'] += ':acc'
                    else:
                        edep['deprel'] += ':ins'
                elif re.match(r'^(nmod|obl(:arg)?):mimo$', edep['deprel']):
                    edep['deprel'] += ':acc'
                elif re.match(r'^(nmod|obl(:arg)?):místo$', edep['deprel']):
                    edep['deprel'] += ':gen'
                elif re.match(r'^obl:místo_za:acc$', edep['deprel']):
                    # 'chytají krávu místo za rohy spíše za ocas'
                    # This should be treated as coordination; 'místo' and 'spíše' are adverbs (???); 'case' for 'místo' does not seem to be the optimal solution.
                    for c in node.children:
                        if c.form == 'místo':
                            c.upos = 'ADV'
                            c.deprel = 'cc'
                    edep['deprel'] = 'obl:za:acc'
                elif re.match(r'^(nmod|obl(:arg)?):místo[_:].+$', edep['deprel']) and not re.match(r'^(nmod|obl(:arg)?):místo_aby$', edep['deprel']):
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):místo[_:].+$', r'\1:místo:gen', edep['deprel'])
                elif re.match(r'^(nmod|obl(:arg)?):na$', edep['deprel']):
                    # The case is unknown. We need 'acc' or 'loc'.
                    # The locative is probably more frequent but it is not so likely with every noun.
                    # If there is an nummod:gov child, it must be accusative and not locative.
                    # (The case would be taken from the number but if it is expressed as digits, it does not have the case feature.)
                    if len([x for x in node.children if x.deprel == 'nummod:gov']) > 0:
                        edep['deprel'] += ':acc'
                    elif re.match(r'^(adresát|AIDS|DEM|frank|h|ha|hodina|Honolulu|jméno|koruna|litr|metr|míle|miliarda|milión|mm|MUDr|NATO|obyvatel|OSN|počet|procento|příklad|rok|SSSR|vůz)$', node.lemma):
                        edep['deprel'] += ':acc'
                    else:
                        edep['deprel'] += ':loc'
                elif re.match(r'^obl:arg:na_konec$', edep['deprel']):
                    # Annotation error. It should have been two prepositional phrases: 'snížil na 225 tisíc koncem minulého roku'
                    edep['deprel'] = 'obl:arg:na:acc'
                elif re.match(r'^(nmod|obl(:arg)?):nad$', edep['deprel']):
                    if re.match(r'[0-9]', node.lemma) or len([x for x in node.children if x.deprel == 'nummod:gov']) > 0:
                        edep['deprel'] += ':acc'
                    else:
                        edep['deprel'] += ':ins'
                elif re.match(r'^(nmod|obl(:arg)?):namísto$', edep['deprel']):
                    edep['deprel'] += ':gen'
                elif re.match(r'^(nmod|obl(:arg)?):navzdory$', edep['deprel']):
                    edep['deprel'] += ':dat'
                elif re.match(r'^(nmod|obl(:arg)?):o$', edep['deprel']):
                    if re.match(r'[0-9]', node.lemma) or len([x for x in node.children if x.deprel == 'nummod:gov']) > 0:
                        edep['deprel'] += ':acc'
                    else:
                        edep['deprel'] += ':loc'
                elif re.match(r'^(nmod|obl(:arg)?):od$', edep['deprel']):
                    edep['deprel'] += ':gen'
                elif re.match(r'^(nmod|obl(:arg)?):ohled_na:ins$', edep['deprel']):
                    # Annotation error.
                    if node.form == 's':
                        ohled = node.next_node
                        na = ohled.next_node
                        noun = na.next_node
                        self.set_basic_and_enhanced(noun, node.parent, 'obl', 'obl:s_ohledem_na:acc')
                        self.set_basic_and_enhanced(ohled, node, 'fixed', 'fixed')
                        self.set_basic_and_enhanced(na, node, 'fixed', 'fixed')
                        self.set_basic_and_enhanced(node, noun, 'case', 'case')
                elif re.match(r'^(nmod|obl(:arg)?):okolo$', edep['deprel']):
                    edep['deprel'] += ':gen'
                elif re.match(r'^(nmod|obl(:arg)?):oproti$', edep['deprel']):
                    edep['deprel'] += ':dat'
                elif re.match(r'^nmod:pára:nom$', edep['deprel']):
                    # Annotation error: 'par excellence'.
                    edep['deprel'] = 'nmod'
                    for c in node.children:
                        if c.udeprel == 'case' and c.form.lower() == 'par':
                            c.lemma = 'par'
                            c.upos = 'ADP'
                            c.xpos = 'RR--X----------'
                            c.feats['Case'] = ''
                            c.feats['Gender'] = ''
                            c.feats['Number'] = ''
                            c.feats['Polarity'] = ''
                            c.feats['AdpType'] = 'Prep'
                elif re.match(r'^(nmod|obl(:arg)?):po$', edep['deprel']):
                    ###!!! Taky bychom se mohli dívat do XPOS předložky, protože tam bude pád uveden!
                    if len([x for x in node.children if x.deprel == 'nummod:gov']) > 0:
                        edep['deprel'] += ':acc'
                    else:
                        edep['deprel'] += ':loc'
                elif re.match(r'^(nmod|obl(:arg)?):poblíž$', edep['deprel']):
                    edep['deprel'] += ':gen'
                elif re.match(r'^(nmod|obl(:arg)?):pod$', edep['deprel']):
                    if re.match(r'[0-9]', node.lemma) or len([x for x in node.children if x.deprel == 'nummod:gov']) > 0:
                        edep['deprel'] += ':acc'
                    else:
                        edep['deprel'] += ':ins'
                elif re.match(r'^(nmod|obl(:arg)?):podle$', edep['deprel']):
                    edep['deprel'] += ':gen'
                elif re.match(r'^(nmod|obl(:arg)?):pro$', edep['deprel']):
                    edep['deprel'] += ':acc'
                elif re.match(r'^(nmod|obl(:arg)?):proti$', edep['deprel']):
                    edep['deprel'] += ':dat'
                elif re.match(r'^(nmod|obl(:arg)?):před$', edep['deprel']):
                    # Accusative would be possible but unlikely.
                    edep['deprel'] += ':ins'
                elif re.match(r'^(nmod|obl(:arg)?):přes$', edep['deprel']):
                    edep['deprel'] += ':acc'
                elif re.match(r'^(nmod|obl(:arg)?):při$', edep['deprel']):
                    edep['deprel'] += ':loc'
                elif re.match(r'^(nmod|obl(:arg)?):s$', edep['deprel']):
                    # Genitive would be possible but unlikely.
                    edep['deprel'] += ':ins'
                elif re.match(r'^(nmod|obl(:arg)?):skrz$', edep['deprel']):
                    edep['deprel'] += ':acc'
                elif re.match(r'^(nmod|obl(:arg)?):u$', edep['deprel']):
                    edep['deprel'] += ':gen'
                elif re.match(r'^(nmod|obl(:arg)?):uprostřed$', edep['deprel']):
                    edep['deprel'] += ':gen'
                elif re.match(r'^(nmod|obl(:arg)?):uvnitř$', edep['deprel']):
                    edep['deprel'] += ':gen'
                elif re.match(r'^(nmod|obl(:arg)?):v_s(:loc)?$', edep['deprel']) and node.form == 'spolupráci':
                    # Annotation error. 'Ve spolupráci s' should be analyzed as a multi-word preposition.
                    # Find the content nominal.
                    cnouns = [x for x in node.children if x.ord > node.ord and re.match(r'^(nmod|obl)', x.udeprel)]
                    vs = [x for x in node.children if x.ord < node.ord and x.lemma == 'v']
                    if len(cnouns) > 0 and len(vs) > 0:
                        logging.info('I am here.')
                        cnoun = cnouns[0]
                        v = vs[0]
                        self.set_basic_and_enhanced(cnoun, node.parent, 'obl', 'obl:ve_spolupráci_s:ins')
                        self.set_basic_and_enhanced(v, cnoun, 'case', 'case')
                        self.set_basic_and_enhanced(node, v, 'fixed', 'fixed')
                elif re.match(r'^(nmod|obl(:arg)?):v(:nom)?$', edep['deprel']):
                    # ':nom' occurs in 'karneval v Rio de Janeiro'
                    edep['deprel'] = re.sub(r':nom$', '', edep['deprel'])
                    if len([x for x in node.children if x.deprel == 'nummod:gov']) > 0:
                        edep['deprel'] += ':acc'
                    else:
                        edep['deprel'] += ':loc'
                elif re.match(r'^obl:v_čel[eo]_s:ins$', edep['deprel']):
                    # There is just one occurrence and it is an error:
                    # 'Předloňský kůň roku Law Soziri šel již v Lahovickém oblouku v čele s Raddelliosem a tato dvojice také nakonec zahanbila ostatní soupeře...'
                    # There should be two independent oblique modifiers, 'v čele' and 's Raddelliosem'.
                    edep['deprel'] = 'obl:s:ins'
                elif re.match(r'^(nmod|obl(:arg)?):včetně$', edep['deprel']):
                    edep['deprel'] += ':gen'
                elif re.match(r'^(nmod|obl(:arg)?):vedle$', edep['deprel']):
                    edep['deprel'] += ':gen'
                elif re.match(r'^(nmod|obl(:arg)?):vůči$', edep['deprel']):
                    edep['deprel'] += ':dat'
                elif re.match(r'^(nmod|obl(:arg)?):z$', edep['deprel']):
                    edep['deprel'] += ':gen'
                elif re.match(r'^(nmod|obl(:arg)?):za$', edep['deprel']):
                    # Instrumental would be possible but unlikely.
                    edep['deprel'] += ':acc'
                else:
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):a([_:].+)?$', r'\1', edep['deprel']) # ala vršovický dloubák
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):a_l[ae]([_:].+)?$', r'\1', edep['deprel']) # a la bondovky
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):aby_na:loc$', r'\1:na:loc', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):ač([_:].+)?$', r'\1:ač', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):ačkoliv?([_:].+)?$', r'\1:ačkoli', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):(jak_)?ad([_:].+)?$', r'\1', edep['deprel']) # ad infinitum
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):ať_v(:loc)?$', r'\1:v:loc', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):ať_z(:gen)?$', r'\1:z:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):ať:.+$', r'\1:ať', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(?::arg)?):až_(.+):(gen|dat|acc|loc|ins)', r'\1:\2:\3', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):beyond([_:].+)?$', r'\1', edep['deprel']) # Beyond the Limits
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):bez_ohled_na(:acc)?$', r'\1:bez_ohledu_na:acc', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):bez_zřetel_k(:dat)?$', r'\1:bez_zřetele_k:dat', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):blíž(:dat)?$', r'\1:blízko:dat', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):byť[_:].+$', r'\1:byť', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):cesta:ins$', r'\1:ins', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):cesta(:gen)?$', r'\1:cestou:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):co(:nom)?$', r'advmod', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):daleko(:nom)?$', r'\1:nedaleko:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):daleko_od(:gen)?$', r'\1:od:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):de([_:].+)?$', r'\1', edep['deprel']) # de facto
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):di([_:].+)?$', r'\1', edep['deprel']) # Lido di Jesolo
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):dík(:dat)?$', r'\1:díky:dat', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):do:(nom|dat)$', r'\1:do:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):do_k:dat$', r'\1:k:dat', edep['deprel']) # do maloobchodní sítě (nebo k dalšímu zpracování)
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):do_rozpor_s(:ins)?$', r'\1:do_rozporu_s:ins', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):do_soulad_s(:ins)?$', r'\1:do_souladu_s:ins', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):en([_:].+)?$', r'\1', edep['deprel']) # bienvenue en France
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):(ať_)?forma(:gen)?$', r'\1:formou:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):i_když[_:].+$', r'\1:i_když', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):in([_:].+)?$', r'\1', edep['deprel']) # made in NHL
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):into([_:].+)?$', r'\1', edep['deprel']) # made in NHL
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):jak[_:].+$', r'\1:jak', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):jakkoliv?[_:].+$', r'\1:jakkoli', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):jako[_:].+$', r'\1:jako', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):jakoby[_:].+$', r'\1:jako', edep['deprel']) # these instances in FicTree should be spelled 'jako by'
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):jakoby_pod:ins$', r'\1:pod:ins', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):jméno:nom$', r'\1:jménem:nom', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):jméno(:gen)?$', r'\1:jménem:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):k_konec(:gen)?$', r'\1:ke_konci:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):kol(em)?(:gen)?$', r'\1:kolem:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):konec(:gen)?$', r'\1:koncem:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):mezi:(nom|dat)$', r'\1:mezi:ins', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):mezi_uvnitř:gen$', r'\1:uvnitř:gen', edep['deprel']) # 'nejdou mezi, ale uvnitř odvětví a oborů'
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):na(:gen|:nom)$', r'\1:na:acc', edep['deprel']) # 'odložit na 1. září'
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):na_čelo(:gen)?$', r'\1:na_čele:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):na_mimo:loc$', r'\1:na:loc', edep['deprel']) # 'na kurtě i mimo něj'
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):na_než:acc$', r'\1:na:acc', edep['deprel']) # 'na víc než čtyři a půl kilometru'
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):na_podklad(:gen)?$', r'\1:na_podkladě:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):na_?rozdíl_od(:gen)?$', r'\1:na_rozdíl_od:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):na_úroveň(:gen)?$', r'\1:na_úrovni:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):na_základ(:gen)?$', r'\1:na_základě:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):na_závěr(:gen)?$', r'\1:na_závěr:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):namísto_do(:gen)?$', r'\1:do:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):následek(:gen)?$', r'\1:následkem:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):(ne)?daleko(:gen)?$', r'\1:nedaleko:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):než[_:].+$', r'\1:než', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):nežli[_:].+$', r'\1:nežli', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):o:(nom|gen|dat)$', r'\1:o:acc', edep['deprel']) # 'zájem o obaly'
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):o_jako[_:].+$', r'\1:jako', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):o_o:acc$', r'\1:o:acc', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):od:(nom|dat)$', r'\1:od:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):of([_:].+)?$', r'\1', edep['deprel']) # University of North Carolina
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):ohledně(:gen)?$', r'\1:ohledně:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):per([_:].+)?$', r'\1', edep['deprel']) # per rollam
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):po:nom$', r'\1:po:acc', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):po_doba(:gen)?$', r'\1:po_dobu:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):po_vzor(:gen)?$', r'\1:po_vzoru:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):počátek(:gen)?$', r'\1:počátkem:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):počínat(:ins)?$', r'\1:počínaje:ins', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):pod_vliv(:gen)?$', r'\1:pod_vlivem:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):pomocí?(:gen)?$', r'\1:pomocí:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):postup(:gen)?$', r'\1:postupem:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):pro:(nom|dat)$', r'\1:pro:acc', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):prostřednictvím?(:gen|:ins)?$', r'\1:prostřednictvím:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):proti:nom$', r'\1:proti:dat', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):protože[_:].+$', r'\1:protože', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):před:gen$', r'\1:před:ins', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):před_během:gen$', r'\1:během:gen', edep['deprel']) # 'před a během utkání'
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):před_po:loc$', r'\1:po:loc', edep['deprel']) # 'před a po vyloučení Schindlera'
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):přestože[_:].+$', r'\1:přestože', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):při_příležitost(:gen)?$', r'\1:při_příležitosti:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):se?:(nom|acc|ins)$', r'\1:s:ins', edep['deprel']) # accusative: 'být s to' should be a fixed expression and it should be the predicate!
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):s_ohled_k(:dat)?$', r'\1:s_ohledem_k:dat', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):s_ohled_na(:acc)?$', r'\1:s_ohledem_na:acc', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):s_pomoc(:gen)?$', r'\1:s_pomocí:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):s_přihlédnutí_k(:dat)?$', r'\1:s_přihlédnutím_k:dat', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):s_přihlédnutí_na(:acc)?$', r'\1:s_přihlédnutím_na:acc', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):s_výjimka(:gen)?$', r'\1:s_výjimkou:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):s_vyloučení(:gen)?$', r'\1:s_vyloučením:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):s_zřetel_k(:dat)?$', r'\1:se_zřetelem_k:dat', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):s_zřetel_na(:acc)?$', r'\1:se_zřetelem_na:acc', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):severně_od(:gen)?$', r'\1:od:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):shoda(:gen)?$', r'\1', edep['deprel']) # 'shodou okolností' is not a prepositional phrase
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):směr_do(:gen)?$', r'\1:směrem_do:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):směr_k(:dat)?$', r'\1:směrem_k:dat', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):směr_na(:acc)?$', r'\1:směrem_na:acc', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):směr_od(:gen)?$', r'\1:směrem_od:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):společně_s(:ins)?$', r'\1:společně_s:ins', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):spolu(_s)?(:ins|:dat)?$', r'\1:spolu_s:ins', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):stranou(:gen|:dat)?$', r'\1:stranou:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):třebaže[_:].+$', r'\1:třebaže', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):u_příležitost(:gen)?$', r'\1:u_příležitosti:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v:gen$', r'\1:v:loc', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_analogie_s(:ins)?$', r'\1:v_analogii_s:ins', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_čelo(:gen)?$', r'\1:v_čele:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_čelo_s(:ins)?$', r'\1:v_čele_s:ins', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_dohoda_s(:ins)?$', r'\1:v_dohodě_s:ins', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_duch(:gen)?$', r'\1:v_duchu:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_důsledek(:gen)?$', r'\1:v_důsledku:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_forma(:gen)?$', r'\1:ve_formě:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_jméno(:gen)?$', r'\1:ve_jménu:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_konfrontace_s(:ins)?$', r'\1:v_konfrontaci_s:ins', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_oblast(:gen)?$', r'\1:v_oblasti:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_oblast_s(:ins)?$', r'\1:s:ins', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_obor(:gen)?$', r'\1:v_oboru:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_otázka(:gen)?$', r'\1:v_otázce:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_podoba(:gen)?$', r'\1:v_podobě:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_poměr_k(:dat)?$', r'\1:v_poměru_k:dat', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_proces(:gen)?$', r'\1:v_procesu:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_prospěch(:gen)?$', r'\1:ve_prospěch:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_protiklad_k(:dat)?$', r'\1:v_protikladu_k:dat', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_průběh(:gen)?$', r'\1:v_průběhu:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_případ(:gen)?$', r'\1:v_případě:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_rámec(:gen)?$', r'\1:v_rámci:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_rozpor_s(:ins)?$', r'\1:v_rozporu_s:ins', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_řada(:gen)?$', r'\1:v_řadě:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_shoda_s(:ins)?$', r'\1:ve_shodě_s:ins', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_služba(:gen)?$', r'\1:ve_službách:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_smysl(:gen)?$', r'\1:ve_smyslu:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_součinnost_s(:ins|:nom)?$', r'\1:v_součinnosti_s:ins', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_souhlas_s(:ins|:nom)?$', r'\1:v_souhlasu_s:ins', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_soulad_s(:ins|:nom)?$', r'\1:v_souladu_s:ins', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_souvislost_s(:ins)?$', r'\1:v_souvislosti_s:ins', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_spojení_s(:ins)?$', r'\1:ve_spojení_s:ins', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_spojený_s(:ins)?$', r'\1:ve_spojení_s:ins', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_spojitost_s(:ins)?$', r'\1:ve_spojitosti_s:ins', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_spolupráce_s(:ins)?$', r'\1:ve_spolupráci_s:ins', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_srovnání_s(:ins)?$', r'\1:ve_srovnání_s:ins', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_světlo(:gen)?$', r'\1:ve_světle:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_věc(:gen)?$', r'\1:ve_věci:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_vztah_k(:dat)?$', r'\1:ve_vztahu_k:dat', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_zájem(:gen|:loc)?$', r'\1:v_zájmu:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_záležitost(:gen)?$', r'\1:v_záležitosti:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_závěr(:gen)?$', r'\1:v_závěru:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_závislost_na(:loc)?$', r'\1:v_závislosti_na:loc', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v_znamení(:gen)?$', r'\1:ve_znamení:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):vina(:gen)?$', r'\1:vinou:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):vliv(:gen)?$', r'\1:vlivem:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):vo:acc$', r'\1:o:acc', edep['deprel']) # colloquial: vo všecko
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):von([_:].+)?$', r'\1', edep['deprel']) # von Neumannem
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):voor([_:].+)?$', r'\1', edep['deprel']) # Hoge Raad voor Diamant
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):vzhledem(_k)?(:dat)?$', r'\1:vzhledem_k:dat', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):z:nom$', r'\1:z:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):z_důvod(:gen)?$', r'\1:z_důvodu:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):z_hledisko(:gen)?$', r'\1:z_hlediska:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):z_oblast(:gen)?$', r'\1:z_oblasti:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):z_řada(:gen)?$', r'\1:z_řad:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):(ať_)?z_strana(:gen)?$', r'\1:ze_strany:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):z_titul(:gen)?$', r'\1:z_titulu:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):za:nom$', r'\1:za:acc', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):za_pomoc(:gen)?$', r'\1:za_pomoci:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):za_účast(:gen)?$', r'\1:za_účasti:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):za_účel(:gen)?$', r'\1:za_účelem:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):začátek(:gen)?$', r'\1:začátkem:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):zásluha(:gen)?$', r'\1:zásluhou:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):závěr(:gen)?$', r'\1:závěrem:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):závisle_na(:loc)?$', r'\1:nezávisle_na:loc', edep['deprel'])
                    edep['deprel'] = re.sub(r'^nmod:že:gen$', 'acl:že', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):že_za:gen$', r'\1:za:gen', edep['deprel'])

    def set_basic_and_enhanced(self, node, parent, deprel, edeprel):
        '''
        Modifies the incoming relation of a node both in the basic tree and in
        the enhanced graph. If the node does not yet depend in the enhanced
        graph on the current basic parent, the new relation will be added without
        removing any old one. If the node already depends multiple times on the
        current basic parent in the enhanced graph, all such enhanced relations
        will be removed before adding the new one.
        '''
        old_parent = node.parent
        node.parent = parent
        node.deprel = deprel
        node.deps = [x for x in node.deps if x['parent'] != old_parent]
        new_edep = {}
        new_edep['parent'] = parent
        new_edep['deprel'] = edeprel
        node.deps.append(new_edep)
