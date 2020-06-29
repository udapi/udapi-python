"""Block udpipe.Base for tagging and parsing using UDPipe."""
from udapi.core.block import Block
from udapi.tool.udpipe import UDPipe
from udapi.core.bundle import Bundle

KNOWN_MODELS = {
    'af': 'models/udpipe/2.4/afrikaans-afribooms-ud-2.4-190531.udpipe',
    'af_afribooms': 'models/udpipe/2.4/afrikaans-afribooms-ud-2.4-190531.udpipe',
    'grc': 'models/udpipe/2.4/ancient_greek-perseus-ud-2.4-190531.udpipe',
    'grc_perseus': 'models/udpipe/2.4/ancient_greek-perseus-ud-2.4-190531.udpipe',
    'grc_proiel': 'models/udpipe/2.4/ancient_greek-proiel-ud-2.4-190531.udpipe',
    'ar': 'models/udpipe/2.4/arabic-padt-ud-2.4-190531.udpipe',
    'ar_padt': 'models/udpipe/2.4/arabic-padt-ud-2.4-190531.udpipe',
    'hy': 'models/udpipe/2.4/armenian-armtdp-ud-2.4-190531.udpipe',
    'hy_armtdp': 'models/udpipe/2.4/armenian-armtdp-ud-2.4-190531.udpipe',
    'eu': 'models/udpipe/2.4/basque-bdt-ud-2.4-190531.udpipe',
    'eu_bdt': 'models/udpipe/2.4/basque-bdt-ud-2.4-190531.udpipe',
    'be': 'models/udpipe/2.4/belarusian-hse-ud-2.4-190531.udpipe',
    'be_hse': 'models/udpipe/2.4/belarusian-hse-ud-2.4-190531.udpipe',
    'bg': 'models/udpipe/2.4/bulgarian-btb-ud-2.4-190531.udpipe',
    'bg_btb': 'models/udpipe/2.4/bulgarian-btb-ud-2.4-190531.udpipe',
    'ca': 'models/udpipe/2.4/catalan-ancora-ud-2.4-190531.udpipe',
    'ca_ancora': 'models/udpipe/2.4/catalan-ancora-ud-2.4-190531.udpipe',
    'zh': 'models/udpipe/2.4/chinese-gsd-ud-2.4-190531.udpipe',
    'zh_gsd': 'models/udpipe/2.4/chinese-gsd-ud-2.4-190531.udpipe',
    'lzh': 'models/udpipe/2.4/classical_chinese-kyoto-ud-2.4-190531.udpipe',
    'lzh_kyoto': 'models/udpipe/2.4/classical_chinese-kyoto-ud-2.4-190531.udpipe',
    'cop': 'models/udpipe/2.4/coptic-scriptorium-ud-2.4-190531.udpipe',
    'cop_scriptotium': 'models/udpipe/2.4/coptic-scriptorium-ud-2.4-190531.udpipe',
    'hr': 'models/udpipe/2.4/croatian-set-ud-2.4-190531.udpipe',
    'hr_set': 'models/udpipe/2.4/croatian-set-ud-2.4-190531.udpipe',
    'cs': 'models/udpipe/2.4/czech-pdt-ud-2.4-190531.udpipe',
    'cs_pdt': 'models/udpipe/2.4/czech-pdt-ud-2.4-190531.udpipe',
    'cs_cac': 'models/udpipe/2.4/czech-cac-ud-2.4-190531.udpipe',
    'cs_cltt': 'models/udpipe/2.4/czech-cltt-ud-2.4-190531.udpipe',
    'cs_fictree': 'models/udpipe/2.4/czech-fictree-ud-2.4-190531.udpipe',
    'da': 'models/udpipe/2.4/danish-ddt-ud-2.4-190531.udpipe',
    'da_ddt': 'models/udpipe/2.4/danish-ddt-ud-2.4-190531.udpipe',
    'nl': 'models/udpipe/2.4/dutch-alpino-ud-2.4-190531.udpipe',
    'nl_alpino': 'models/udpipe/2.4/dutch-alpino-ud-2.4-190531.udpipe',
    'nl_lassysmall': 'models/udpipe/2.4/dutch-lassysmall-ud-2.4-190531.udpipe',
    'en': 'models/udpipe/2.4/english-ewt-ud-2.4-190531.udpipe',
    'en_ewt': 'models/udpipe/2.4/english-ewt-ud-2.4-190531.udpipe',
    'en_gum': 'models/udpipe/2.4/english-gum-ud-2.4-190531.udpipe',
    'en_lines': 'models/udpipe/2.4/english-lines-ud-2.4-190531.udpipe',
    'en_partut': 'models/udpipe/2.4/english-partut-ud-2.4-190531.udpipe',
    'et_edt': 'models/udpipe/2.4/estonian-edt-ud-2.4-190531.udpipe',
    'et_ewt': 'models/udpipe/2.4/estonian-ewt-ud-2.4-190531.udpipe',
    'fi': 'models/udpipe/2.4/finnish-tdt-ud-2.4-190531.udpipe',
    'fi_tdt': 'models/udpipe/2.4/finnish-tdt-ud-2.4-190531.udpipe',
    'fi_ftb': 'models/udpipe/2.4/finnish-ftb-ud-2.4-190531.udpipe',
    'fr_gsd': 'models/udpipe/2.4/french-gsd-ud-2.4-190531.udpipe',
    'fr_partut': 'models/udpipe/2.4/french-partut-ud-2.4-190531.udpipe',
    'fr_sequoia': 'models/udpipe/2.4/french-sequoia-ud-2.4-190531.udpipe',
    'fr_spoken': 'models/udpipe/2.4/french-spoken-ud-2.4-190531.udpipe',
    'gl_ctg': 'models/udpipe/2.4/galician-ctg-ud-2.4-190531.udpipe',
    'gl_treegal': 'models/udpipe/2.4/galician-treegal-ud-2.4-190531.udpipe',
    'de': 'models/udpipe/2.4/german-gsd-ud-2.4-190531.udpipe',
    'got': 'models/udpipe/2.4/gothic-proiel-ud-2.4-190531.udpipe',
    'el': 'models/udpipe/2.4/greek-gdt-ud-2.4-190531.udpipe',
    'he': 'models/udpipe/2.4/hebrew-htb-ud-2.4-190531.udpipe',
    'hi': 'models/udpipe/2.4/hindi-hdtb-ud-2.4-190531.udpipe',
    'hu': 'models/udpipe/2.4/hungarian-szeged-ud-2.4-190531.udpipe',
    'id': 'models/udpipe/2.4/indonesian-gsd-ud-2.4-190531.udpipe',
    'ga': 'models/udpipe/2.4/irish-idt-ud-2.4-190531.udpipe',
    'it_isdt': 'models/udpipe/2.4/italian-isdt-ud-2.4-190531.udpipe',
    'it_partut': 'models/udpipe/2.4/italian-partut-ud-2.4-190531.udpipe',
    'it_postwita': 'models/udpipe/2.4/italian-postwita-ud-2.4-190531.udpipe',
    'it_vit': 'models/udpipe/2.4/italian-vit-ud-2.4-190531.udpipe',
    'ja': 'models/udpipe/2.4/japanese-gsd-ud-2.4-190531.udpipe',
    'ko_gsd': 'models/udpipe/2.4/korean-gsd-ud-2.4-190531.udpipe',
    'ko_kaist': 'models/udpipe/2.4/korean-kaist-ud-2.4-190531.udpipe',
    'la_ittb': 'models/udpipe/2.4/latin-ittb-ud-2.4-190531.udpipe',
    'la_perseus': 'models/udpipe/2.4/latin-perseus-ud-2.4-190531.udpipe',
    'la_proiel': 'models/udpipe/2.4/latin-proiel-ud-2.4-190531.udpipe',
    'lv': 'models/udpipe/2.4/latvian-lvtb-ud-2.4-190531.udpipe',
    'lt_alksnis': 'models/udpipe/2.4/lithuanian-alksnis-ud-2.4-190531.udpipe',
    'lt_hse': 'models/udpipe/2.4/lithuanian-hse-ud-2.4-190531.udpipe',
    'mt': 'models/udpipe/2.4/maltese-mudt-ud-2.4-190531.udpipe',
    'mr': 'models/udpipe/2.4/marathi-ufal-ud-2.4-190531.udpipe',
    'sme': 'models/udpipe/2.4/north_sami-giella-ud-2.4-190531.udpipe',
    'no_bokmaal': 'models/udpipe/2.4/norwegian-bokmaal-ud-2.4-190531.udpipe',
    'no_nynorsklia': 'models/udpipe/2.4/norwegian-nynorsklia-ud-2.4-190531.udpipe',
    'no_nynorsk': 'models/udpipe/2.4/norwegian-nynorsk-ud-2.4-190531.udpipe',
    'cu': 'models/udpipe/2.4/old_church_slavonic-proiel-ud-2.4-190531.udpipe',
    'fro': 'models/udpipe/2.4/old_french-srcmf-ud-2.4-190531.udpipe',
    'orv': 'models/udpipe/2.4/old_russian-torot-ud-2.4-190531.udpipe',
    'fa': 'models/udpipe/2.4/persian-seraji-ud-2.4-190531.udpipe',
    'pl_lfg': 'models/udpipe/2.4/polish-lfg-ud-2.4-190531.udpipe',
    'pl_pdb': 'models/udpipe/2.4/polish-pdb-ud-2.4-190531.udpipe',
    'pt_bosque': 'models/udpipe/2.4/portuguese-bosque-ud-2.4-190531.udpipe',
    'pt_gsd': 'models/udpipe/2.4/portuguese-gsd-ud-2.4-190531.udpipe',
    'ro_nonstandard': 'models/udpipe/2.4/romanian-nonstandard-ud-2.4-190531.udpipe',
    'ro_rrt': 'models/udpipe/2.4/romanian-rrt-ud-2.4-190531.udpipe',
    'ru_gsd': 'models/udpipe/2.4/russian-gsd-ud-2.4-190531.udpipe',
    'ru_syntagrus': 'models/udpipe/2.4/russian-syntagrus-ud-2.4-190531.udpipe',
    'ru_taiga': 'models/udpipe/2.4/russian-taiga-ud-2.4-190531.udpipe',
    'sr': 'models/udpipe/2.4/serbian-set-ud-2.4-190531.udpipe',
    'sk': 'models/udpipe/2.4/slovak-snk-ud-2.4-190531.udpipe',
    'sl_ssj': 'models/udpipe/2.4/slovenian-ssj-ud-2.4-190531.udpipe',
    'sl_sst': 'models/udpipe/2.4/slovenian-sst-ud-2.4-190531.udpipe',
    'es_ancora': 'models/udpipe/2.4/spanish-ancora-ud-2.4-190531.udpipe',
    'es_gsd': 'models/udpipe/2.4/spanish-gsd-ud-2.4-190531.udpipe',
    'sv_lines': 'models/udpipe/2.4/swedish-lines-ud-2.4-190531.udpipe',
    'sv_talbanken': 'models/udpipe/2.4/swedish-talbanken-ud-2.4-190531.udpipe',
    'ta': 'models/udpipe/2.4/tamil-ttb-ud-2.4-190531.udpipe',
    'te': 'models/udpipe/2.4/telugu-mtg-ud-2.4-190531.udpipe',
    'tr': 'models/udpipe/2.4/turkish-imst-ud-2.4-190531.udpipe',
    'uk': 'models/udpipe/2.4/ukrainian-iu-ud-2.4-190531.udpipe',
    'ur': 'models/udpipe/2.4/urdu-udtb-ud-2.4-190531.udpipe',
    'ug': 'models/udpipe/2.4/uyghur-udt-ud-2.4-190531.udpipe',
    'vi': 'models/udpipe/2.4/vietnamese-vtb-ud-2.4-190531.udpipe',
    'wo': 'models/udpipe/2.4/wolof-wtb-ud-2.4-190531.udpipe',
}


class Base(Block):
    """Base class for all UDPipe blocks."""

    # pylint: disable=too-many-arguments
    def __init__(self, model=None, model_alias=None,
                 tokenize=True, tag=True, parse=True, resegment=False, **kwargs):
        """Create the udpipe.En block object."""
        super().__init__(**kwargs)
        self.model, self.model_alias = model, model_alias
        self._tool = None
        self.tokenize, self.tag, self.parse, self.resegment = tokenize, tag, parse, resegment

    @property
    def tool(self):
        """Return the tool (UDPipe in this case), created lazily."""
        if self._tool:
            return self._tool
        if not self.model:
            if not self.model_alias:
                raise ValueError('model (path/to/model) or model_alias (e.g. en) must be set!')
            self.model = KNOWN_MODELS[self.model_alias]
        self._tool = UDPipe(model=self.model)
        return self._tool

    def process_document(self, doc):
        tok, tag, par = self.tokenize, self.tag, self.parse
        old_bundles = doc.bundles
        new_bundles = []
        for bundle in old_bundles:
            for tree in bundle:
                new_bundles.append(bundle)
                if self._should_process_tree(tree):
                    if tok:
                        new_trees = self.tool.tokenize_tag_parse_tree(tree, resegment=self.resegment,
                                                                      tag=self.tag, parse=self.parse)
                        if self.resegment and len(new_trees) > 1:
                            orig_bundle_id = bundle.bundle_id
                            bundle.bundle_id = orig_bundle_id + '-1'
                            for i, new_tree in enumerate(new_trees[1:], 2):
                                new_bundle = Bundle(document=doc, bundle_id=orig_bundle_id + '-' + str(i))
                                new_tree.zone = tree.zone
                                new_bundle.add_tree(new_tree)
                                new_bundles.append(new_bundle)
                    elif not tok and tag and par:
                        self.tool.tag_parse_tree(tree)
                    elif not tok and not tag and not par and self.resegment:
                        sentences = self.tool.segment_text(tree.text)
                        if len(sentences) > 1:
                            orig_bundle_id = bundle.bundle_id
                            bundle.bundle_id = orig_bundle_id + '-1'
                            tree.text = sentences[0]
                            for i, sentence in enumerate(sentences[1:], 2):
                                new_bundle = Bundle(document=doc, bundle_id=orig_bundle_id + '-' + str(i))
                                new_tree = new_bundle.create_tree(zone=tree.zone)
                                new_tree.text = sentence
                                new_bundles.append(new_bundle)
                    else:
                        raise ValueError("Unimplemented tokenize=%s tag=%s parse=%s" % (tok, tag, par))
        doc.bundles = new_bundles

'''
Udapi::Block::UDPipe::Base - tokenize, tag and parse into UD

=head1 SYNOPSIS

 # from the command line
 echo John loves Mary | udapi.pl Read::Sentences UDPipe::Base model_alias=en Write::TextModeTrees

 # in scenario
 UDPipe::Base model=/home/me/english-ud-1.2-160523.udpipe
 UDPipe::Base model_alias=en
 UDPipe::EN # shortcut for the above
 UDPipe::EN tokenize=1 tag=1 parse=0

=head1 DESCRIPTION

This block loads L<Udapi::Tool::UDPipe> (a wrapper for the UDPipe C++ tool) with
the given C<model> for analysis into the Universal Dependencies (UD) style.
UDPipe can do tokenization, tagging (plus lemmatization and universal features)
and parsing (with deprel labels) and users of this block can select which of the
substasks should be done using parameters C<tokenize>, C<tag> and C<parse>.
The default is to do all three.

=head1 TODO

UDPipe can do also sentence segmentation, but L<Udapi::Tool::UDPipe> does not supported it yet.

Similarly with multi-word tokens.

=head1 PARAMETERS

=head2 C<model>

Path to the model file within Udapi share
(or relative path starting with "./" or absolute path starting with "/").
This parameter is required if C<model_alias> is not supplied.

=head2 C<model_alias>

The C<model> parameter can be omitted if this parameter is supplied.
Currently available model aliases are:

B<grc_proiel, grc, ar, eu, bg, hr, cs, da, nl, en, et, fi, fi_ftb, fr, got, de,
el, he, hi, hu, id, ga, it, la_itt, la_proiel, la, no, cu, fa, po, ro, pt, sl,
es, ta, sv>.

They correspond to paths where the language code in the alias is substituted
with the respective language name, e.g. B<grc_proiel> expands to
C<models/udpipe/ancient-greek-ud-1.2-160523.udpipe>.

=head1 tokenize

Do tokenization, i.e. create new nodes with attributes
C<form>, C<misc> (if SpaceAfter=No) and C<ord>.
The sentence string is taken from the root's attribute C<text>.

=head1 tag

Fill node attributes: C<lemma>, C<upos>, C<xpos> and C<feats>.
On the input, just the attribute C<form> is expected.

=head1 parse

Fill node attributes: C<deprel> and rehang the nodes to their parent.
On the input, attributes C<lemma>, C<upos>, C<xpos> and C<feats> are expected.

=head1 SEE ALSO

L<http://ufal.mff.cuni.cz/udpipe>

L<Udapi::Tool::UDPipe>
'''
