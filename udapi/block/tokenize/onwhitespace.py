"""Block tokenize.OnWhitespace"""
from udapi.core.block import Block


class OnWhitespace(Block):
    """"Base tokenizer, splits on whitespaces, fills SpaceAfter=No."""

    @staticmethod
    def tokenize_sentence(string):
        """A method to be overriden in subclasses."""
        return string.split()

    def process_tree(self, root):
        if root.children:
            raise ValueError('Tree %s is already tokenized.' % root)
        sentence = ' '.join(root.text.split())
        tokens = self.tokenize_sentence(sentence)
        for i, token in enumerate(tokens, 1):
            space_after = False

            # Delete the token from the begining of the sentence.
            if sentence.startswith(token):
                sentence = sentence[len(token):]
                # This is the expected case. The sentence starts with the token.
                # If it is followed by a space, delete the space and set space_after=True.
                if not len(sentence):
                    space_after = True
                elif sentence.startswith(' '):
                    space_after = True
                    sentence = sentence[1:]
            else:
                # The token (returned from tokenization) does not match the start of sentence.
                # E.g. '. . . word' is tokenized as  '... word'.
                # Let's delete the start of sentence anyway,
                # using a non-greedy regex and the expected next token
                # returned from the tokenization.
                # my $next_token = $tokens[$i+1];
                # my ($first, $rest) = ($sentence =~ /^(.*?)(\Q$next_token\E.*)$/);
                # $no_space_after = 1 if (defined $first && $first !~ /\s$/);
                # $sentence = $rest if (defined $rest);
                raise ValueError('tokenization does not match: "%s" vs "%s"' % (token, sentence))

            # create a new node
            node = root.create_child(form=token)
            node.ord = i
            if not space_after:
                node.misc = 'SpaceAfter=No'
