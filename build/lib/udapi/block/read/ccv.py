"""Ccv class is a reader for Corpus of Czech Verse json files."""
from udapi.core.basereader import BaseReader
from udapi.core.root import Root
from udapi.block.ud.setspaceafterfromtext import SetSpaceAfterFromText
import json

class Ccv(BaseReader):
    r"""A reader for Corpus of Czech Verse json files.

    See https://github.com/versotym/corpusCzechVerse
    Each verse (line) is stored as one tree (although it is quite often not a whole sentence).
    Start of each stanza is marked with `newpar`.
    Start of each poem is marked with `newdoc = [poem_id]`.

    Args:
    tokenize: create nodes
    """
    def __init__(self, tokenize=True, **kwargs):
        self.tokenize = tokenize
        self._cache = None
        super().__init__(**kwargs)

    @staticmethod
    def is_multizone_reader():
        """Can this reader read bundles which contain more zones?.

        This implementation returns always False.
        """
        return False

    def read_tree(self):
        if self._cache:
            return self._cache.pop()
        else:
            trees = self.read_trees()
            if not trees:
                return None
            self._cache = list(reversed(trees[1:]))
            return trees[0]

    def read_trees(self):
        if self.filehandle is None:
            return None
        poems = json.load(self.filehandle)
        all_trees = []
        for poem in poems:
            poem_trees = []
            for stanza in poem["body"]:
                stanza_trees = []
                for line in stanza:
                    root = Root()
                    root.text = line["text"]
                    root.json["rhyme"] = line["rhyme"]
                    root.json["metre"] = line["metre"]
                    root.json["stress"] = line["stress"]
                    stanza_trees.append(root)
                    if self.tokenize:
                        words = [[]] + [[w] for w in line["words"]]
                        for index, puncts in line["punct"].items():
                            for punct in puncts:
                                words[int(index)].append({"token": punct, "lemma": punct})
                        for word in words:
                            for w in word:
                                node = root.create_child(form=w["token"], lemma=w["lemma"])
                                if "morph" in w:
                                    node.xpos = w["morph"]
                                    node.misc["xsampa"] = w["xsampa"]
                                    node.misc["phoebe"] = w["phoebe"]
                        SetSpaceAfterFromText.process_tree(None, root)
                stanza_trees[0].newpar = True
                poem_trees.extend(stanza_trees)
            root = poem_trees[0]
            root.newdoc = poem["poem_id"]
            root.json["p_author"] = poem["p_author"]
            root.json["b_author"] = poem["b_author"]
            root.json["biblio"] = poem["biblio"] 
            all_trees.extend(poem_trees)
        return all_trees
