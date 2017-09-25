from udapi.core.node import *

class Evaluation:


    def __init__(self):

        self.files = []
        self.files_neg = []
        self.files.append(open("en_nouns_001b_der_V1_ADVx__ADJx_N1.csv", 'a+'))
        self.files.append(open("en_nouns_002a_der_V1_NX__Nx_N1.csv", 'a+'))
        self.files.append(open("en_nouns_003b_der_V1_Nx__ADJ1_Nx.csv",'a+'))
        self.files.append(open("en_nouns_004a_der_V1_prepNX__N1_prepNx.csv",'a+'))
        self.files.append(open("en_nouns_005_Nx_ADJ1__Nx_neg_ADJ1.csv",'a+'))
        #self.files.append(open('en_verbs_001a_der_ADJx_N1__V1_ADVx.csv','a+'))
        #self.files.append(open('en_verbs_002b_der_Nx_N1__V1_Nx.csv','a+'))
        #self.files.append(open('en_verbs_004b_der_N1_prepNx__V1_prepNx.csv','a+'))
        #self.files.append(open('en_verbs_003a_der_ADJ1_Nx__V1_Nx.csv','a+'))

        self.files_neg.append(open("en_nouns_001b_der_V1_ADVx__ADJx_N1-neg.csv", 'a+'))
        self.files_neg.append(open("en_nouns_002a_der_V1_NX__Nx_N1-neg.csv", 'a+'))
        self.files_neg.append(open("en_nouns_003b_der_V1_Nx__ADJ1_Nx-neg.csv",'a+'))
        self.files_neg.append(open("en_nouns_004a_der_V1_prepNX__N1_prepNx-neg.csv",'a+'))
        self.files_neg.append(open("en_nouns_005_Nx_ADJ1__Nx_neg_ADJ1-neg.csv",'a+'))
        #self.files_neg.append(open('en_verbs_001a_der_ADJx_N1__V1_ADVx-neg.csv', 'a+'))
        #self.files_neg.append(open('en_verbs_002b_der_Nx_N1__V1_Nx-neg.csv', 'a+'))
        #self.files_neg.append(open('en_verbs_004b_der_N1_prepNx__V1_prepNx-neg.csv', 'a+'))
        #self.files_neg.append(open('en_verbs_003a_der_ADJ1_Nx__V1_Nx-neg.csv', 'a+'))

        self.file_real_triples=open("real_triples.csv",'a+')

        for f in self.files:
            f.write("Sentence\t"+"Name of function\t"+"Triple\t"+"1.word-derivation\t"+"2.word-derivation\t"+"1.word-upos-orig\t"+"2.word-upos-orig\t"+"1.word-upos-new\t"+"2.word-upos-new\n")
        for f in self.files_neg:
            f.write("Sentence\t"+"1.word\t"+"2.word\t"+"Comment\n")

        self.file_real_triples.write("Sentence\t"+"Name of function\t"+"Triple\t"+"1.word-upos\t"+"2.word-upos\n")

    def evaluate_triple(self,node,name_of_function,w1,rel,w2,deriv_1,deriv_2,upos_1_orig,upos_2_orig,upos_1_new,upos_2_new):
        for f in self.files:
            if f.name.split('.')[0] == name_of_function:
                f.write(node.root.get_sentence()+"\t")
                f.write(name_of_function+"\t")
                f.write(w1.lemma+" ")
                f.write(rel + " ")
                f.write(w2.lemma+"\t")
                f.write(deriv_1 + "\t")
                f.write(deriv_2 + "\t")
                f.write(upos_1_orig + "\t")
                f.write(upos_2_orig + "\t")
                f.write(upos_1_new + "\t")
                f.write(upos_2_new + "\n")

    def evaluate_neg(self,node,name_of_function,word,comment):
        for f in self.files_neg:
            if f.name.split('-')[0] == name_of_function:
                f.write(node.root.get_sentence() + "\t")
                f.write(node.lemma + "\t")
                try:
                    f.write(word.lemma + "\t")
                except:
                    f.write("None" + "\t")

                f.write(comment + "\n")

    def evaluate_real(self,node,name_of_function,w1,rel,w2):
        self.file_real_triples.write(node.root.get_sentence()+"\t")
        self.file_real_triples.write(name_of_function + "\t")
        self.file_real_triples.write(w1.lemma + " ")
        self.file_real_triples.write(rel + " ")
        self.file_real_triples.write(w2.lemma + "\t")
        self.file_real_triples.write(w1.upos + "\t")
        self.file_real_triples.write(w2.upos + "\n")












