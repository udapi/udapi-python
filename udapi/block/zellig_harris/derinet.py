class Derivation(object):
    def __init__(self, sub_word, part, depth):
        self.sub_word = sub_word
        self.part = part
        self.depth = depth


class Word(object):
    def __init__(self, lemma,sub_words,derivation):
        self.lemma = lemma
        self.sub_words = sub_words
        self.derivation = derivation


class WtypeOfD(object):
    def __init__(self, lemma,type_of_deriv):
        self.lemma = lemma
        self.type_of_deriv = type_of_deriv

    def set_type_of_deriv(self, value):
        self.type_of_deriv = value



class Derinet(object):

    words=[]
    dict_noun_key_verb_value= {}
    dict_verb_key_noun_value = {}
    dict_adj_key_adv_value = {}
    dict_adv_key_adj_value = {}
    dict_adj_key_verb_value = {}
    dict_verb_key_adj_value = {}
    dict_noun_key_adj_value = {}
    dict_adj_key_noun_value = {}
    dict_adj_key_adj_value = {}
    dict_verb_key_verb_value = {}
    dict_noun_key_noun_value = {}


    #7\aback\59\C\\1\N\N\N\N\Y\a+back\xN\AS\N\N\N\#\N\N\AS\((a)[B|.N],(back)[N])[B]\N\N\N
    #24099\irritant\5\C\\1\N\N\N\N\Y\irritate+ant\2x\SA\N\Y\N\-ate#\N\N\SA\((irritate)[V],(ant)[A|V.])[A]\N\Y\N
    #24087\irreverently\7\C\\1\N\N\N\N\Y\irreverent+ly\Ax\SA\N\N\N\#\N\N\ASAA\(((ir)[A|.A],((revere)[V],(ent)[A|V.])[A])[A],(ly)[B|A.])[B]\N\N\N

    def __init__(self):
        f1 = open("derivations.txt",'w')
        with open("eml.cd") as f:
            for line in f:
                arr = line.split('\\')
                lemma = arr[1]
                ws = lemma.split(' ')
                if ws.__len__() == 1:
                    derword = arr[11]
                    sub_words = derword.split('+')
                    deriving = arr[21]
                    depth = 0
                    deriv = []
                    type = False
                    if deriving.__len__() > 0:
                        f1.write("\n")
                        for z in deriving:
                            if (z == '('):
                                s = []
                                depth = depth + 1
                            elif (z == '['):
                                t = []
                                type = True
                            elif (z == ']'):
                                type = False
                                d = Derivation(''.join(s), ''.join(t), depth)
                                f1.write(''.join(s)+" ")
                                f1.write(''.join(t)+" ")
                                f1.write(str(depth)+"  ")
                                s = []
                                deriv.append(d)
                            elif ((z >= 'a') and (z <= 'z')) or ((z >= 'A') and (z <= 'Z') or (z == '.') or (z == '|')):
                                if not type:
                                    l = z
                                    s.append(l)
                                else:
                                    l = z
                                    t.append(l)
                            elif z == ')':
                                depth = depth - 1
                        w = Word(lemma, sub_words, deriv)
                        self.words.append(w)
        f.close()
        f1.close()

        for w in self.words:
            wc=w.derivation[-1].part
            if len(w.sub_words) == 1:
                if len(w.derivation)>=2 and ((w.derivation[-2].sub_word) == '' or (w.derivation[-2].sub_word == w.sub_words[0])):
                    derived_word=w.sub_words[0]
                    if (w.derivation[-2].part == 'V') and (wc == 'N'):
                        self.add_word_to_dictionary(self.dict_noun_key_verb_value, self.dict_verb_key_noun_value, w.lemma, derived_word, 'pos_conversion')

                    elif (w.derivation[-2].part == 'N') and (wc == 'V'):
                        self.add_word_to_dictionary(self.dict_verb_key_noun_value, self.dict_noun_key_verb_value, w.lemma, derived_word, 'pos_conversion')

                    elif (w.derivation[-2].part == 'A') and (wc == 'B'):
                        self.add_word_to_dictionary(self.dict_adv_key_adj_value, self.dict_adj_key_adv_value, w.lemma, derived_word, 'pos_conversion')

                    elif (w.derivation[-2].part == 'N') and (wc == 'A'):
                        self.add_word_to_dictionary(self.dict_adj_key_noun_value, self.dict_noun_key_adj_value, w.lemma, derived_word, 'pos_conversion')

                    elif (w.derivation[-2].part == 'V') and (wc == 'A'):
                        self.add_word_to_dictionary(self.dict_adj_key_verb_value, self.dict_verb_key_adj_value, w.lemma, derived_word, 'pos_conversion')


            for d in w.derivation:
                if w.sub_words[-1] == d.sub_word:
                    dp = d.part.split('|')
                    if len(dp) > 1:
                        derived_word = ''.join(w.sub_words[:-1])
                        if dp[1] == 'A.' and wc =='V':
                            self.add_word_to_dictionary(self.dict_verb_key_adj_value, self.dict_adj_key_verb_value, w.lemma, derived_word, 'suffix')

                        if dp[1] == 'V.' and wc == 'N':
                            self.add_word_to_dictionary(self.dict_noun_key_verb_value, self.dict_verb_key_noun_value, w.lemma, derived_word, 'suffix')

                        elif dp[1] == 'N.' and wc == 'V':
                            self.add_word_to_dictionary(self.dict_verb_key_noun_value, self.dict_noun_key_verb_value, w.lemma, derived_word, 'suffix')

                        elif dp[1] == 'A.' and wc == 'B':
                           self.add_word_to_dictionary(self.dict_adv_key_adj_value, self.dict_adj_key_adv_value, w.lemma, derived_word, 'suffix')

                        elif dp[1] == 'N.' and wc == 'A':
                            self.add_word_to_dictionary(self.dict_adj_key_noun_value, self.dict_noun_key_adj_value, w.lemma, derived_word, 'suffix')

                        elif dp[1] == 'V.' and wc == 'A':
                            self.add_word_to_dictionary(self.dict_adj_key_verb_value, self.dict_verb_key_adj_value, w.lemma, derived_word, 'suffix')

                if (w.sub_words[0] == d.sub_word) and (w.sub_words[0] in [ 'in', 'un', 'non', 'de', 'dis', 'a', 'anti', 'im', 'il','ir','mis']):
                    dp = d.part.split('|')
                    if len(dp) > 1:
                        derived_word = ''.join(w.sub_words[1:])
                        if dp[1] == '.A' and wc == 'A':
                            self.add_word_to_dictionary(self.dict_adj_key_adj_value, self.dict_adj_key_adj_value, w.lemma, derived_word, 'neg_prefix')

                if (w.sub_words[0] == d.sub_word) and (w.sub_words[0] in ['in', 'un', 'non', 'de', 'dis','anti', 'im', 'il', 'ir', 'mis']):
                    dp = d.part.split('|')
                    if len(dp) > 1:
                        derived_word = ''.join(w.sub_words[1:])
                        if dp[1] == '.V' and wc == 'V':
                            self.add_word_to_dictionary(self.dict_verb_key_verb_value, self.dict_verb_key_verb_value, w.lemma, derived_word,'neg_prefix')

                if (w.sub_words[0] == d.sub_word) and (w.sub_words[0] in ['in', 'un', 'non', 'de', 'dis','anti', 'im', 'il', 'ir', 'mis']):
                    dp = d.part.split('|')
                    if len(dp) > 1:
                        derived_word = ''.join(w.sub_words[1:])
                        if dp[1] == '.N' and wc == 'N':
                            self.add_word_to_dictionary(self.dict_noun_key_noun_value, self.dict_noun_key_noun_value, w.lemma, derived_word,'neg_prefix')





    def add_word_to_dictionary(self, dictionary_lemma_key, dictionary_derived_word_key, lemma, derived_word, type):
        wtdl = WtypeOfD(lemma,type)
        wtdd = WtypeOfD(derived_word,type)
        try:
            if derived_word in dictionary_lemma_key[lemma]:
                dictionary_lemma_key[lemma].append(wtdd)
        except:
            dictionary_lemma_key[lemma] = []
            dictionary_lemma_key[lemma].append(wtdd)
        try:
            if lemma not in dictionary_derived_word_key[derived_word]:
                dictionary_derived_word_key[derived_word].append(wtdl)
        except:
            dictionary_derived_word_key[derived_word] = []
            dictionary_derived_word_key[derived_word].append(wtdl)


    def get_verb_from_noun(self,noun,type):
        verb = []
        try:
            for v in self.dict_noun_key_verb_value[noun]:
                if v.type_of_deriv in type:
                    verb.append(v)
                if 'neg_prefix' in type:
                    try:
                        neg_verbs = self.dict_verb_key_verb_value(v.lemma)
                    except:
                        neg_verbs = []
                    verb.extend(neg_verbs)

        except:
            verb = []
        return verb


    def get_noun_from_verb(self,verb,type):
        neg_nouns = []
        noun = []
        types=[]
        lemmas=[]
        try:
            for n in self.dict_verb_key_noun_value[verb]:
                if n.type_of_deriv in type:
                    noun.append(n)
                    types.append(n.type_of_deriv)
                if 'neg_prefix' in type:
                    try:
                        neg_verbs = self.dict_verb_key_verb_value[verb]
                        for neg_verb in neg_verbs:
                            if neg_verb.type_of_deriv == 'neg_prefix':
                                try:
                                    neg_nouns_part=self.dict_verb_key_noun_value[neg_verb.lemma]
                                    for neg_noun in neg_nouns_part:
                                        if neg_noun.type_of_deriv in types:
                                            if neg_noun.lemma not in lemmas:
                                                neg_noun_new= WtypeOfD(neg_noun.lemma,'neg_prefix')
                                                neg_nouns.append(neg_noun_new)
                                                lemmas.append(neg_noun.lemma)

                                except:
                                    neg_nouns=[]
                    except:
                        neg_nouns = []
            noun.extend(neg_nouns)

        except:
            noun = []
        return noun


    def get_adv_from_adj(self, adj,type):
        adv = []
        lemmas = []
        try:
            for av in self.dict_adj_key_adv_value[adj]:
                if av.type_of_deriv in type:
                    adv.append(av)
            if 'neg_prefix' in type:
                try:
                    neg_adjs=self.dict_adj_key_adj_value[adj]
                    for neg_adj in neg_adjs:
                        try:
                            neg_advs=self.dict_adj_key_adv_value[neg_adj.lemma]
                        except:
                            neg_advs=[]
                        for neg_adv in neg_advs:
                            if neg_adv.lemma not in lemmas:
                                neg_adv_new= WtypeOfD(neg_adv.lemma,'neg_prefix')
                                adv.append(neg_adv_new)
                                lemmas.append(neg_adv.lemma)

                except:
                    neg_adjs=[]
        except:
            adv = []
        return adv


    def get_adj_from_adv(self, adv, type):
        adj = []
        try:
            for aj in self.dict_adv_key_adj_value[adv]:
                if aj.type_of_deriv in type:
                    adj.append(aj)
                if 'neg_prefix' in type:
                    try:
                        neg_adjs = self.dict_adj_key_adj_value[aj.lemma]
                    except:
                        neg_adjs = []
                    adj.extend(neg_adjs)
        except:
            adj = []
        return adj


    def get_adj_from_verb(self, verb,type):
        adj = []
        lemmas = []
        try:
            try:
                adjs=self.dict_verb_key_adj_value[verb]
            except:
                adjs=[]
            for aj in adjs:
                if aj.lemma not in lemmas:
                    lemmas.append(aj.lemma)
            try:
                nouns = self.dict_verb_key_noun_value[verb]
            except:
                nouns = []

            for noun in nouns:
                try:
                    adj_from_noun = self.dict_noun_key_adj_value[noun.lemma]
                except:
                    adj_from_noun = []

                for afn in adj_from_noun:
                    if afn.lemma not in lemmas:
                        lemmas.append(afn.lemma)
                        adjs.append(afn)

            for aj in adjs:
                if aj.type_of_deriv in type:
                    adj.append(aj)
                if 'neg_prefix' in type:
                    try:
                        neg_adjs = self.dict_adj_key_adj_value[aj.lemma]
                    except:
                        neg_adjs = []
                    for n_a in neg_adjs:
                        if n_a.lemma not in lemmas:
                            lemmas.append(n_a.lemma)
                            adjs.append(n_a)
        except:
            adj = []
        return adj


    def get_verb_from_adj(self, adj,type):
        verb=[]
        verbs = []
        lemmas = []
        try:
            try:
                verbs = self.dict_adj_key_verb_value[adj]
            except:
                verbs = []

            for v in verbs:
                if v.lemma not in lemmas:
                    lemmas.append(v.lemma)
            try:
                nouns = self.dict_adj_key_noun_value[adj]
            except:
                nouns=[]

            for noun in nouns:
                try:
                    verb_from_noun = self.dict_noun_key_verb_value[noun.lemma]
                except:
                    verb_from_noun = []

                for vfn in verb_from_noun:
                    if vfn.lemma not in lemmas:
                        lemmas.append(vfn.lemma)
                        verbs.append(vfn)

            for v in verbs:
                if ((v.type_of_deriv in type) and (v.lemma not in verb)):
                    verb.append(v)
                if 'neg_prefix' in type:
                    try:
                        neg_verbs = self.dict_verb_key_verb_value[v.lemma]
                    except:
                        neg_verbs = []
                    for n_v in neg_verbs:
                        if n_v.lemma not in lemmas:
                            lemmas.append(v.lemma)
                            verb.append(v)
        except:
            verb = []
        return verb


    def get_neg_adj_from_adj(self, adj, type):
        adjs = []
        try:
            for aj in self.dict_adj_key_adj_value[adj]:
                if ((aj.type_of_deriv in type) and (aj not in adjs)):
                    adjs.append(aj)
        except:
           adjs=[]
        return adjs










