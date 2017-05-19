"""Block udpipe.Base for tagging and parsing using UDPipe."""
from udapi.core.block import Block
from udapi.tool.udpipe import UDPipe

KNOWN_MODELS = {
    'grc': 'models/udpipe/2.0/ancient_greek-proiel-ud-2.0-conll17-170315.udpipe',
    'grc_proiel': 'models/udpipe/2.0/ancient_greek-ud-2.0-conll17-170315.udpipe',
    'ar': 'models/udpipe/2.0/arabic-ud-2.0-conll17-170315.udpipe',
    'eu': 'models/udpipe/2.0/basque-ud-2.0-conll17-170315.udpipe',
    'bg': 'models/udpipe/2.0/bulgarian-ud-2.0-conll17-170315.udpipe',
    'ca': 'models/udpipe/2.0/catalan-ud-2.0-conll17-170315.udpipe',
    'zh': 'models/udpipe/2.0/chinese-ud-2.0-conll17-170315.udpipe',
    'hr': 'models/udpipe/2.0/croatian-ud-2.0-conll17-170315.udpipe',
    'cs_cac': 'models/udpipe/2.0/czech-cac-ud-2.0-conll17-170315.udpipe',
    'cs_cltt': 'models/udpipe/2.0/czech-cltt-ud-2.0-conll17-170315.udpipe',
    'cs': 'models/udpipe/2.0/czech-ud-2.0-conll17-170315.udpipe',
    'da': 'models/udpipe/2.0/danish-ud-2.0-conll17-170315.udpipe',
    'nl_lassysmall': 'models/udpipe/2.0/dutch-lassysmall-ud-2.0-conll17-170315.udpipe',
    'nl': 'models/udpipe/2.0/dutch-ud-2.0-conll17-170315.udpipe',
    'en_lines': 'models/udpipe/2.0/english-lines-ud-2.0-conll17-170315.udpipe',
    'en_partut': 'models/udpipe/2.0/english-partut-ud-2.0-conll17-170315.udpipe',
    'en': 'models/udpipe/2.0/english-ud-2.0-conll17-170315.udpipe',
    'et': 'models/udpipe/2.0/estonian-ud-2.0-conll17-170315.udpipe',
    'fi_ftb': 'models/udpipe/2.0/finnish-ftb-ud-2.0-conll17-170315.udpipe',
    'fi': 'models/udpipe/2.0/finnish-ud-2.0-conll17-170315.udpipe',
    'fr_partut': 'models/udpipe/2.0/french-partut-ud-2.0-conll17-170315.udpipe',
    'fr_sequoia': 'models/udpipe/2.0/french-sequoia-ud-2.0-conll17-170315.udpipe',
    'fr': 'models/udpipe/2.0/french-ud-2.0-conll17-170315.udpipe',
    'gl_treegal': 'models/udpipe/2.0/galician-treegal-ud-2.0-conll17-170315.udpipe',
    'gl': 'models/udpipe/2.0/galician-ud-2.0-conll17-170315.udpipe',
    'de': 'models/udpipe/2.0/german-ud-2.0-conll17-170315.udpipe',
    'got': 'models/udpipe/2.0/gothic-ud-2.0-conll17-170315.udpipe',
    'el': 'models/udpipe/2.0/greek-ud-2.0-conll17-170315.udpipe',
    'he': 'models/udpipe/2.0/hebrew-ud-2.0-conll17-170315.udpipe',
    'hi': 'models/udpipe/2.0/hindi-ud-2.0-conll17-170315.udpipe',
    'hu': 'models/udpipe/2.0/hungarian-ud-2.0-conll17-170315.udpipe',
    'id': 'models/udpipe/2.0/indonesian-ud-2.0-conll17-170315.udpipe',
    'ga': 'models/udpipe/2.0/irish-ud-2.0-conll17-170315.udpipe',
    'it_partut': 'models/udpipe/2.0/italian-partut-ud-2.0-conll17-170315.udpipe',
    'it': 'models/udpipe/2.0/italian-ud-2.0-conll17-170315.udpipe',
    'ja': 'models/udpipe/2.0/japanese-ud-2.0-conll17-170315.udpipe',
    'kk': 'models/udpipe/2.0/kazakh-ud-2.0-conll17-170315.udpipe',
    'ko': 'models/udpipe/2.0/korean-ud-2.0-conll17-170315.udpipe',
    'la_ittb': 'models/udpipe/2.0/latin-ittb-ud-2.0-conll17-170315.udpipe',
    'la_proiel': 'models/udpipe/2.0/latin-proiel-ud-2.0-conll17-170315.udpipe',
    'la': 'models/udpipe/2.0/latin-ud-2.0-conll17-170315.udpipe',
    'lv': 'models/udpipe/2.0/latvian-ud-2.0-conll17-170315.udpipe',
    'no_bokmaal': 'models/udpipe/2.0/norwegian-bokmaal-ud-2.0-conll17-170315.udpipe',
    'no_nynorsk': 'models/udpipe/2.0/norwegian-nynorsk-ud-2.0-conll17-170315.udpipe',
    'cu': 'models/udpipe/2.0/old_church_slavonic-ud-2.0-conll17-170315.udpipe',
    'fa': 'models/udpipe/2.0/persian-ud-2.0-conll17-170315.udpipe',
    'pl': 'models/udpipe/2.0/polish-ud-2.0-conll17-170315.udpipe',
    'pt_br': 'models/udpipe/2.0/portuguese-br-ud-2.0-conll17-170315.udpipe',
    'pt': 'models/udpipe/2.0/portuguese-ud-2.0-conll17-170315.udpipe',
    'ro': 'models/udpipe/2.0/romanian-ud-2.0-conll17-170315.udpipe',
    'ru_syntagrus': 'models/udpipe/2.0/russian-syntagrus-ud-2.0-conll17-170315.udpipe',
    'ru': 'models/udpipe/2.0/russian-ud-2.0-conll17-170315.udpipe',
    'sk': 'models/udpipe/2.0/slovak-ud-2.0-conll17-170315.udpipe',
    'sl_sst': 'models/udpipe/2.0/slovenian-sst-ud-2.0-conll17-170315.udpipe',
    'sl': 'models/udpipe/2.0/slovenian-ud-2.0-conll17-170315.udpipe',
    'es_ancora': 'models/udpipe/2.0/spanish-ancora-ud-2.0-conll17-170315.udpipe',
    'es': 'models/udpipe/2.0/spanish-ud-2.0-conll17-170315.udpipe',
    'sv_lines': 'models/udpipe/2.0/swedish-lines-ud-2.0-conll17-170315.udpipe',
    'sv': 'models/udpipe/2.0/swedish-ud-2.0-conll17-170315.udpipe',
    'tr': 'models/udpipe/2.0/turkish-ud-2.0-conll17-170315.udpipe',
    'uk': 'models/udpipe/2.0/ukrainian-ud-2.0-conll17-170315.udpipe',
    'ur': 'models/udpipe/2.0/urdu-ud-2.0-conll17-170315.udpipe',
    'ug': 'models/udpipe/2.0/uyghur-ud-2.0-conll17-170315.udpipe',
    'vi': 'models/udpipe/2.0/vietnamese-ud-2.0-conll17-170315.udpipe',
}


class Base(Block):
    """Base class for all UDPipe blocks."""

    # pylint: disable=too-many-arguments
    def __init__(self, model=None, model_alias=None,
                 tokenize=True, tag=True, parse=True, **kwargs):
        """Create the udpipe.En block object."""
        super().__init__(**kwargs)
        self.model, self.model_alias = model, model_alias
        self._tool = None
        self.tokenize, self.tag, self.parse = tokenize, tag, parse

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

    def process_tree(self, root):
        tok, tag, par = self.tokenize, self.tag, self.parse
        if tok and tag and par:
            return self.tool.tokenize_tag_parse_tree(root)
        if not tok and tag and par:
            return self.tool.tag_parse_tree(root)
        # TODO
        # return $self->tool->tokenize_tag_parse_tree($root) if  $tok &&  $tag &&  $par;
        # return $self->tool->tokenize_tag_tree($root)       if  $tok &&  $tag && !$par;
        # return $self->tool->tokenize_tree($root)           if  $tok && !$tag && !$par;
        # return $self->tool->tag_parse_tree($root)          if !$tok &&  $tag &&  $par;
        # return $self->tool->tag_tree($root)                if !$tok &&  $tag && !$par;
        # return $self->tool->parse_tree($root)              if !$tok && !$tag &&  $par;
        raise ValueError("Unimplemented tokenize=%s tag=%s parse=%s" % (tok, tag, par))

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
