"""Block tokenize.OnWhitespace"""
import re
from udapi.core.block import Block


class OnWhitespace(Block):
    """Base tokenizer, splits on whitespaces, fills SpaceAfter=No.

    Use the parameter `keep_spaces=True` to preserve all whitespaces in the sentence
    in the UDPipe way, i.e. using the `SpacesAfter` and `SpacesBefore` features in the MISC field.
    It is backward compatible with CoNLL-U v2 `SpaceAfter=No` feature. That is, no following
    whitespace is marked by `SpaceAfter=No` and a single following space results in no
    whitespace-related markup.
    If loading the text using `read.Sentences` and all whitespaces need to be preserved
    (in order to be able to reconstruct the original document), the `read.Sentences` block
    must be called with `rstrip=''`, `rstrip=\n` or `rstrip=\r\n` to prevent stripping the
    trailing whitespace, e.g.::
        $> echo -e "Hello \t world " | udapy read.Sentences $'rstrip=\r\n' tokenize.OnWhitespace keep_spaces=1 write.Conllu

        # sent_id = 1
        # text = Hello   world
        1       Hello   _       _       _       _       0       _       _       SpacesAfter=\s\t\s
        2       world   _       _       _       _       0       _       _       _
    Note that the attribute `SpaceAfter=No` is missing for the token `world`, since it is
    followed by a single space.

    Parameters
    ----------
    keep_spaces : bool
        preserve whitespaces by filling MISC attributes `SpacesAfter` and `SpacesBefore` (by default False)
    """

    escape_whitespace_table = str.maketrans({' ':r'\s', '\t':r'\t', '\r':r'\r', '\n':r'\n'})

    def __init__(self, keep_spaces=False, **kwargs):
        super().__init__(**kwargs)
        self.keep_spaces = keep_spaces

    @staticmethod
    def tokenize_sentence(string):
        """A method to be overriden in subclasses."""
        return string.split()

    def process_tree(self, root):
        if root.children:
            raise ValueError('Tree %s is already tokenized.' % root)
        #sentence = ' '.join(root.text.split())
        sentence = root.text
        tokens = self.tokenize_sentence(sentence)

        # Check if there are any spaces before the first token
        spaces_before = ""
        m = re.match(r'\s+', sentence)
        if m:
            spaces_before = m.group(0)
            sentence = sentence[len(spaces_before):]

        for i, token in enumerate(tokens, 1):
            spaces_after = ""

            # The token (returned from tokenization) does not match the start of sentence.
            # E.g. '. . . word' is tokenized as  '... word'.
            if not sentence.startswith(token):
                # Let's delete the start of sentence anyway,
                # using a non-greedy regex and the expected next token
                # returned from the tokenization.
                # my $next_token = $tokens[$i+1];
                # my ($first, $rest) = ($sentence =~ /^(.*?)(\Q$next_token\E.*)$/);
                # $no_space_after = 1 if (defined $first && $first !~ /\s$/);
                # $sentence = $rest if (defined $rest);
                raise ValueError('tokenization does not match: "%s" vs "%s"' % (token, sentence))

            # Delete the token from the begining of the sentence.
            sentence = sentence[len(token):]

            # Set the SpaceAfter and SpacesAfter properly
            m = re.match(r'\s+', sentence)
            if m is not None:
                spaces_after = m.group(0)
                sentence = sentence[len(spaces_after):]

            # normalize whitespace
            if not self.keep_spaces:
                spaces_before = ""
                # spaces_after = "" <=> SpaceAfter=No is never set for the last token <=> len(sentence) = 0
                spaces_after = "" if not len(spaces_after) and len(sentence) else " "

            # create a new node
            node = root.create_child(form=token)
            node.ord = i

            if i == 1 and spaces_before:
                node.misc["SpacesBefore"] = spaces_before.translate(self.escape_whitespace_table)
            if not spaces_after:
                node.misc["SpaceAfter"] = 'No'
            elif spaces_after != " ":
                node.misc["SpacesAfter"] = spaces_after.translate(self.escape_whitespace_table)
