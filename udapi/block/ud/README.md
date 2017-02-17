# Blocks for Universal Dependencies Treebanks

Overview:
* [Convert1to2](#convert1to2) - conversion from UD v1 to UD v2
* [MarkBugs](markbugs.py) - check for suspicious/wrong constructions
* [SetSpaceAfter](setspaceafter.py) - heuristically fill `SpaceAfter=No` and `# text` if missing in the data
* [SetSpaceAfterFromText](setspaceafterfromtext.py) - `SpaceAfter=No` according to `# text`

For using these tools, you need to install Udapi for Python
as described [here](https://github.com/udapi/udapi-python/blob/master/README.md),
so you have the `udapy` execution script in your `$PATH`.

___

## Convert1to2
This Udapi block converts UD v1 files into UD v2 files.
See http://universaldependencies.org/v2/summary.html for the description of all UD v2 changes.

**IMPORTANT**: this code does only **some** of the changes and the output should be **checked**, see below.

### Usage
* Run from command line:

  ```bash
  udapy -s ud.Convert1to2 < inputUD1.conllu > outputUD2.conllu
  ```

### Tricks
* If you already have some conversion of your treebank into v2,
  you can use this script for comparing the differences, e.g.:

  ```bash
  vimdiff outputUD2.conllu previous_outputUD2.conllu
  ```
* It is difficult for humans to see the dependency structure in CoNLL-U format.
  You can use a Udapi pretty-printer `write.TextModeTrees`:

  ```bash
  udapy ud.Convert1to2 write.TextModeTrees attributes=form,lemma,upos,deprel,feats,misc < inputUD1.conllu > outputUD2.txt
  udapy write.TextModeTrees attributes=form,lemma,upos,deprel,feats,misc < previous_outputUD2.conllu > previous_outputUD2.txt
  vimdiff outputUD2.txt previous_outputUD2.txt
  ```
* `Convert1to2` marks unclear cases with a special `ToDo` attribute in the MISC column (and logging to stderr).
  You can find these nodes in colored pretty-printed trees with:

  ```bash
  udapy ud.Convert1to2 write.TextModeTrees attributes=form,lemma,upos,deprel,feats,misc color=1 < inputUD1.conllu | less -R
  ```
  and then type `/ToDo` and press `n` to jump to the next occurrence.

### Supported edits
* UPOS: CONJ→CCONJ, whatever→AUX if copula
* DEPREL: mwe→fixed, dobj→obj, *pass→*:pass, name→flat:name, foreign→flat(+Foreign=Yes)
* DEPREL: neg→advmod/det (plus distinguish interjections and negation particles)
* DEPREL: nmod→obl if parent is not nominal
* Reattach cc and punct (commas, semicolons) to the following conjunct
* FEATS: Negative→Polarity, Aspect=Pro→Prosp, VerbForm=Trans→Conv, Definite=Red→Cons
* FEATS: Polarity=Neg if DEPREL was neg and there is no PronType=Neg feature
* FEATS: warn if Tense=Nar or NumType=Gen
* ellipsis/gapped constructions using orphan deprels instead of remnant deprels
* text: make sure the `# text` comment is present and agrees with the tokens' forms

### Edits NOT supported (yet)
* Addition of enhanced dependencies.
* Changes to tokenization.
* Changes to copular constructions.
* Changes to POS tags beyond renaming CONJ to CCONJ

### Diagnostics
Unclear cases (either probable v1 annotation errors or cases where fully automatic conversion is not possible)
are marked with a special `ToDo` attribute in the MISC column and with a longer explanation printed to stderr.
`ToDo` can have these values:
* `cc-after-conj`: there is no (sibling) conjunct after a node with deprel=cc (but there are some conjunct before)
* `cc-without-conj`: node with deprel=cc follows its parent, which has no `conj` children
* `gen`: feature NumType=Gen not allowed in UD v2
* `more-remnant-children`: a node with more than one remnant child
* `nar`: feature Tense=Nar not allowed in UD v2
* `neg`: deprel=neg but upos is not any of ADV, PART, DET
* `nmod`: deprel=nmod, but parent is ambiguous nominal/predicate, so it is not clear whether the `nmod` should be changed to `obl`
* `punct-in-coord`: it is not clear whether the punctuation is part of coordination (and should be reattached to the following conjunct, which could not be found)
* `remnant`: unexpected case where either one of the remnants' grandparent (=head of head) is the root or the nearest common ancestor (governor) of all remnants in the tree is the root

### Bugs, help
This is work in progress.
Bug reports and code contributions are welcome via Github [issues](https://github.com/udapi/udapi-python/issues) and [pull requests](https://github.com/udapi/udapi-python/pulls).
Questions about Udapi or this conversion script are welcome via Github [issues](https://github.com/udapi/udapi-python/issues) or [email](popel@ufal.mff.cuni.cz).

### Author
Martin Popel (popel@ufal.mff.cuni.cz),
based on [v2-conversion](https://github.com/UniversalDependencies/tools/tree/master/v2-conversion) by Sebastian Schuster.
