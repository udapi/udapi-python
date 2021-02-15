"""Block tokenize.OnWhitespace"""
import re
from udapi.core.block import Block


class OnWhitespace(Block):
    """"Base tokenizer, splits on whitespaces, fills SpaceAfter=No."""

    def __init__(self, tokenizer_params={}, **kwargs):
        super().__init__(**kwargs)
        self.tokenizer_params = tokenizer_params

    @staticmethod
    def tokenize_sentence(string):
        """A method to be overriden in subclasses."""
        return string.split()

    def process_tree(self, root):
        if root.children:
            raise ValueError('Tree %s is already tokenized.' % root)
        #sentence = ' '.join(root.text.split())
        sentence = root.text
        tokens = self.tokenize_sentence(sentence, **self.tokenizer_params)

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

            # create a new node
            node = root.create_child(form=token)
            node.ord = i

            if i == 1 and len(spaces_before) > 0:
                node.misc["SpacesBefore"] = spaces_before
            if not len(spaces_after):
                node.misc["SpaceAfter"] = 'No'
            elif spaces_after != ' ':
                node.misc["SpacesAfter"] = spaces_after
